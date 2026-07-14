from __future__ import annotations

import argparse
import json
import re
import sys

from brief_writer import save_daily_brief, save_output_bundle, write_latest_index
from butler_persona import build_butler_brief
from avatar_3d_builder import build_avatar_3d_package
from company_client import CompanyClientError, build_mock_company_snapshot, fetch_company_snapshot, load_company_watchlist
from china_market_client import ChinaMarketError, build_mock_china_market_snapshot, fetch_china_market_snapshot
from config import get_settings
from data_source_registry import (
    SUPPORTED_CHINA_MARKET_PROVIDERS,
    SUPPORTED_COMPANY_PROVIDERS,
    SUPPORTED_ECONOMIC_CALENDAR_PROVIDERS,
    SUPPORTED_MARKET_PROVIDERS,
    SUPPORTED_NEWS_PROVIDERS,
    SUPPORTED_STRUCTURED_MARKET_PROVIDERS,
    SUPPORTED_THEME_PROVIDERS,
    SUPPORTED_WEATHER_PROVIDERS,
    unsupported_provider_message,
)
from deepseek_client import DeepSeekClientError, DeepSeekQuotaError, create_chat_completion
from economic_calendar_client import EconomicCalendarError, build_mock_economic_calendar, fetch_economic_calendar
from event_timeline_builder import build_event_timeline
from financial_reasoning import build_finance_reasoning
from insight_builder import build_insights
from local_memory import load_user_profile, summarize_profile
from local_schedule import load_local_schedule, summarize_local_tasks
from market_client import MarketClientError, build_mock_market_snapshot, fetch_market_snapshot, load_symbols
from marketaux_client import MarketauxClientError, fetch_marketaux_news
from gdelt_client import GdeltClientError, fetch_gdelt_news
from newsapi_client import NewsApiClientError, fetch_newsapi_news
from finnhub_news_client import FinnhubNewsClientError, fetch_finnhub_news
from x_client import XClientError, fetch_x_lead_snapshot
from mock_data import build_mock_brief
from news_enrichment import enrich_company_snapshot, enrich_news_snapshot
from news_digest_builder import build_news_digest
from news_client import NewsClientError, build_mock_news_snapshot, fetch_news_snapshot, load_news_feeds, merge_news_snapshots
from openai_client import OpenAIClientError, OpenAIQuotaError, create_response
from output_builder import build_output_bundle
from outlook_graph import get_today_outlook_or_error
from outlook_mock import build_mock_outlook_day, summarize_outlook_tasks
from pathlib import Path
from quality_builder import build_brief_analysis
from reminder_builder import build_reminder_plan
from theme_client import ThemeClientError, build_mock_theme_snapshot, fetch_theme_snapshot, load_theme_symbols
from touzid_client import TouzidClientError, fetch_touzid_market_snapshot, load_a_share_watchlist, parse_symbol_list
from weather_client import WeatherClientError, fetch_weather


def configure_output() -> None:
    """Prefer UTF-8 output for Windows terminals."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def build_prompt(brief: dict) -> str:
    brief_json = json.dumps(brief, ensure_ascii=False, indent=2)
    return f"""
你是“松果”，一个温柔、阳光、聪明的 18 岁女生 AI 私人管家。

请根据下面的结构化信息，生成一份中文早安汇报。

要求：
- 语气温柔、自然、可靠。
- 先讲今天最重要的 3 件事。
- 优先使用 `insights` 里的判断材料组织语言，不要机械罗列所有原始数据。
- 财经内容必须区分事实、可能原因和后续关注点。
- 投资相关内容只做信息整理和线索提示，不直接建议买卖。
- 新闻标题和指数数据只是线索，不能把未经核验的标题当成最终事实。
- 日程目前优先来自本地文件；如果 source 不是 Microsoft Graph，请不要说已经真实读取 Outlook。
- 如果有 calendar write proposal，只能说“建议创建”，不能说已经创建。
- 控制在 900-1300 字之间。
- 结尾给出今天松果项目的下一步行动。

结构化信息：

{brief_json}
""".strip()


def render_template_brief(brief: dict) -> str:
    lines: list[str] = []
    analysis = brief.get("brief_analysis", {})
    if analysis:
        lines.append("松果解读")
        lines.append(analysis.get("today_overview", ""))
        lines.append("")
        lines.append("今天最重要的三件事：")
        for story_item in analysis.get("top_stories", [])[:3]:
            lines.append(f"- {story_item.get('title', '')}")
            if story_item.get("why_it_matters"):
                lines.append(f"  为什么重要：{story_item['why_it_matters']}")
            if story_item.get("confidence"):
                lines.append(f"  可信度：{story_item['confidence']}｜来源：{story_item.get('source', 'unknown')}")
            if story_item.get("follow_up"):
                lines.append(f"  后续核验：{story_item['follow_up'][0]}")
        lines.append("")
    lines.append(f"早上好，我是松果。今天是 {brief['date']}，我先为你整理 {brief['city']} 的早报。")
    lines.append("")
    lines.append("今天最重要的三件事是：维护本地日程、确认早报保存正常、开始推进财经/新闻真实数据源。")
    lines.append("")
    lines.append("一、天气和穿衣建议")
    weather = brief["weather"]
    lines.append(f"今天 {brief['city']} {weather['condition']}，气温 {weather['temperature']}，{weather['rain']}。")
    lines.append(weather["outfit"])
    lines.append("")
    lines.append("二、全球市场和宏观")
    insights = brief.get("insights", {})
    market_insights = insights.get("market", {})
    if market_insights:
        lines.append(f"- 市场情绪：{market_insights.get('tone', '待判断')}")
        for item in market_insights.get("watch_points", [])[:3]:
            lines.append(f"- 后续关注：{item}")
    for event in brief["markets"]:
        lines.append(f"- {event['region']}：{event['summary']} 可能驱动因素：{event['possible_driver']}")
    market_data = brief.get("market_data", {})
    indices = market_data.get("indices", [])
    if indices:
        lines.append("")
        lines.append(f"主要指数数据源：{market_data.get('source', 'unknown')}")
        for index in indices[:8]:
            change = index.get("change_percent_from_open")
            if change is None:
                change = index.get("change_percent_from_previous_close")
            change_text = "变化待确认" if change is None else f"较前收盘约 {change}%"
            close = index.get("close")
            if close is None:
                close = index.get("regular_market_price")
            close_text = "点位待确认" if close is None else f"{close}"
            lines.append(f"- {index.get('region', '')}｜{index.get('name', '')}：{close_text}，{change_text}")
    lines.append("")
    lines.append("三、行业、板块和公司线索")
    theme_insights = insights.get("themes", {})
    if theme_insights:
        for item in theme_insights.get("opportunity_watch", [])[:5]:
            lines.append(f"- 价格/主题线索：{item}")
    company_insights = insights.get("companies", {})
    if company_insights:
        for item in company_insights.get("watch_points", [])[:6]:
            lines.append(f"- 公司观察池：{item}")
    for item in brief["industry"]:
        lines.append(f"- {item}")
    theme_data = brief.get("theme_data", {})
    theme_items = theme_data.get("items", [])
    if theme_items:
        lines.append("")
        lines.append(f"主题价格数据源：{theme_data.get('source', 'unknown')}")
        for item in theme_items[:8]:
            change = item.get("change_percent_from_previous_close")
            change_text = "变化待确认" if change is None else f"较前收盘约 {change}%"
            price = item.get("regular_market_price")
            price_text = "价格待确认" if price is None else f"{price}"
            lines.append(f"- {item.get('theme', '')}｜{item.get('name', '')}：{price_text}，{change_text}")
    company_data = brief.get("company_data", {})
    company_items = company_data.get("items", [])
    if company_items:
        lines.append("")
        lines.append(f"公司观察池数据源：{company_data.get('source', 'unknown')}")
        for item in company_items[:8]:
            quote = item.get("quote") or {}
            change = quote.get("change_percent_from_previous_close")
            change_text = "变化待确认" if change is None else f"较前收盘约 {change}%"
            price = quote.get("regular_market_price")
            price_text = "价格待确认" if price is None else f"{price}"
            headline = ""
            articles = item.get("articles", [])
            if articles:
                headline = f"｜新闻线索：{articles[0].get('title', '')}"
            lines.append(f"- {item.get('sector', '')}｜{item.get('name', '')}：{price_text}，{change_text}{headline}")
    lines.append("")
    lines.append("四、政治、军事和社会新闻")
    news_insights = insights.get("news", {})
    if news_insights:
        topics = news_insights.get("possible_topics", [])
        if topics:
            lines.append(f"- 新闻主题线索：{'、'.join(topics)}")
        for item in news_insights.get("watch_points", [])[:3]:
            lines.append(f"- 后续关注：{item}")
    for item in brief["politics_and_society"]:
        lines.append(f"- {item}")
    news_data = brief.get("news_data", {})
    categories = news_data.get("categories", [])
    if categories:
        lines.append("")
        lines.append(f"新闻线索数据源：{news_data.get('source', 'unknown')}")
        for category in categories[:5]:
            articles = category.get("articles", [])
            if not articles:
                continue
            lines.append(f"- {category.get('label', category.get('category', '新闻'))}：{articles[0].get('title', '')}")
    lines.append("")
    lines.append("五、松果项目今天要做什么")
    for item in insights.get("priorities", [])[:3]:
        lines.append(f"- {item}")
    for item in brief["sunguo_project"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("六、今天的待办")
    for task in brief["outlook_tasks"]:
        lines.append(f"- {task['time']}｜{task['title']}｜优先级：{task['priority']}")
    schedule = brief.get("schedule", {})
    proposals = schedule.get("write_proposals", [])
    next_section_number = 7
    if proposals:
        lines.append("")
        lines.append("七、建议加入日程的事项（需要你确认，不会自动写入）")
        for proposal in proposals:
            lines.append(
                f"- {proposal['start']}-{proposal['end']}｜{proposal['title']}｜原因：{proposal['reason']}"
            )
        next_section_number = 8
    lines.append("")
    lines.append(f"{number_to_chinese(next_section_number)}、生活细节提醒")
    for item in brief["life_reminders"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append(f"{number_to_chinese(next_section_number + 1)}、历史故事")
    lines.append(brief["history_story"])
    lines.append("")
    lines.append(f"{number_to_chinese(next_section_number + 2)}、轻松一下")
    lines.append(brief["joke"])
    return "\n".join(lines)


def number_to_chinese(value: int) -> str:
    mapping = {
        1: "一",
        2: "二",
        3: "三",
        4: "四",
        5: "五",
        6: "六",
        7: "七",
        8: "八",
        9: "九",
        10: "十",
    }
    return mapping.get(value, str(value))


def generate_ai_brief(settings, brief: dict) -> str | None:
    if settings.ai_provider == "deepseek" and settings.deepseek_api_key:
        try:
            prompt = build_prompt(brief)
            generated = create_chat_completion(settings.deepseek_api_key, settings.deepseek_model, prompt)
            return generated
        except DeepSeekQuotaError as error:
            print("DeepSeek 已连通，但账号额度/余额/限流暂时不可用，先回退到模板版早报。")
            print(f"处理建议：{error}")
            print("请打开 https://platform.deepseek.com/usage 和 https://platform.deepseek.com/top_up 检查。")
            print("")
        except DeepSeekClientError as error:
            print("DeepSeek 生成失败，先回退到模板版早报。")
            print(f"错误信息：{error}")
            print("")

    if settings.ai_provider == "openai" and settings.openai_api_key:
        try:
            prompt = build_prompt(brief)
            generated = create_response(settings.openai_api_key, settings.openai_model, prompt)
            return generated
        except OpenAIQuotaError as error:
            print("OpenAI 已连通，但账号额度/账单暂时不可用，先回退到模板版早报。")
            print(f"处理建议：{error}")
            print("请打开 https://platform.openai.com/usage 和 https://platform.openai.com/settings/organization/billing/overview 检查。")
            print("")
        except OpenAIClientError as error:
            print("OpenAI 生成失败，先回退到模板版早报。")
            print(f"错误信息：{error}")
            print("")

    if settings.ai_provider not in {"deepseek", "openai"}:
        print(f"未知 AI_PROVIDER：{settings.ai_provider}，先回退到模板版早报。")
        print("")

    return None


def build_news_digest_prompt(brief: dict) -> str:
    digest_input = {
        "date": brief.get("date"),
        "city": brief.get("city"),
        "market_data": brief.get("market_data", {}),
        "china_market_data": brief.get("china_market_data", {}),
        "structured_market_data": brief.get("structured_market_data", {}),
        "theme_data": brief.get("theme_data", {}),
        "company_data": brief.get("company_data", {}),
        "news_data": brief.get("news_data", {}),
        "economic_calendar": brief.get("economic_calendar", {}),
        "finance_reasoning": brief.get("finance_reasoning", {}),
        "brief_analysis": brief.get("brief_analysis", {}),
        "event_timeline": brief.get("event_timeline", {}),
        "today_tasks": brief.get("outlook_tasks", []),
        "project_priorities": (brief.get("insights") or {}).get("priorities", []),
    }
    payload = json.dumps(digest_input, ensure_ascii=False, indent=2)
    return f"""
你是“松果”的高质量每日早报编辑。你的任务不是复述标题，而是把过去 24 小时的市场、宏观、政策、产业、公司和供应链线索整理成网页可展示的中文早报。

只输出 JSON，不要输出 Markdown，不要解释，不要在 JSON 外加任何文字。

JSON 结构必须是：
{{
  "version": "news-digest-ai-v3",
  "date": "...",
  "city": "...",
  "overview": ["一句话总览1", "一句话总览2", "一句话总览3"],
  "sections": [
    {{
      "title": "宏观经济",
      "items": [
        {{
          "time": "07-09 09:30",
          "thesis": "美债利率回落正在减轻科技股估值压力",
          "summary": "解释发生了什么、为什么重要、可能影响哪些资产/行业/公司、后续观察什么。"
        }}
      ]
    }}
  ]
}}

只使用这些栏目标题，并尽量按顺序输出：
1. 宏观经济
2. 全球市场
3. 中国市场
4. 地缘政治与政策监管
5. 科技与产业
6. 大宗商品与供应链
7. 公司与资本运作
8. 今日重点观察

不要输出这些栏目：财秘关注、财秘追踪、财富聚焦。

写作规则：
- 每条 item 的 thesis 直接写判断或事件，不要写“观点：”“新闻1”“新闻2”“要点1”。
- 每条 summary 必须包含信息增量，至少回答四件事中的两件：发生了什么、为什么重要、影响谁、下一步看什么。
- 优先使用 event_timeline 里的高分事件；有可靠时间就写 time，没有可靠时间就省略 time。
- 不要在正文展示信息来源，不要写“信息来源：”。
- 不要编造事实。数据不足时写“暂不下结论”，并说明还需要核验什么。
- 财经内容只做信息整理，不给买卖建议，不写“买入/卖出/推荐”。
- 总条数控制在 18-28 条；每个栏目 1-5 条。
- 语言要像一个专业但温和的私人管家：清晰、克制、具体，不要空话。
- 如果只有价格变化，必须提示回到公告、财报、政策、供需或新闻事实核验，不能直接把涨跌写成基本面结论。
- 对宏观和地缘事件，要写清可能传导到利率、汇率、能源、航运、军工、科技或消费中的哪条链路。
- 今日重点观察要输出 3-6 条“今天具体盯什么”，不要写泛泛而谈的项目口号。

原始数据：
{payload}
""".strip()

def generate_ai_news_digest(settings, brief: dict) -> dict | None:
    if settings.ai_provider != "deepseek" or not settings.deepseek_api_key:
        return None

    try:
        digest_model = "deepseek-chat" if "v4" in settings.deepseek_model.lower() or "reason" in settings.deepseek_model.lower() else settings.deepseek_model
        raw = create_chat_completion(
            settings.deepseek_api_key,
            digest_model,
            build_news_digest_prompt(brief),
            json_mode=True,
        )
        payload = parse_json_object(raw)
        repair_news_digest_payload(payload, brief, min_items=minimum_digest_items(brief))
        validate_news_digest(payload)
        validate_news_digest_grounding(payload, brief)
        # DeepSeek is more reliable on short translation batches. Repeat the
        # grounded append pass until the requested editorial coverage is met.
        for _ in range(8):
            if count_digest_items(payload) >= minimum_digest_items(brief):
                break
            append_missing_fact_cards(settings, payload, brief)
        repair_news_digest_payload(payload, brief, min_items=minimum_digest_items(brief))
        localize_news_digest_items(settings, payload, brief)
        refresh_digest_overview(payload)
        validate_news_digest(payload)
        return payload
    except (DeepSeekClientError, ValueError, json.JSONDecodeError) as error:
        print("AI 新闻汇总生成失败，改用分批事实提炼。")
        print(f"错误信息：{error}")
        print("")
        return build_localized_rule_digest(settings, brief)


def build_localized_rule_digest(settings, brief: dict) -> dict | None:
    """Reliable fallback: translate/summarise small fact-card batches, not raw titles."""
    rule_digest = get_rule_digest_with_pool(brief)
    sections = json.loads(json.dumps(rule_digest.get("sections") or [], ensure_ascii=False))
    payload = {
        "version": "news-digest-ai-v4",
        "date": brief.get("date", ""),
        "city": brief.get("city", ""),
        "overview": [],
        "sections": sections,
        "_force_refine": True,
    }
    localize_news_digest_items(settings, payload, brief)
    payload.pop("_force_refine", None)
    refresh_digest_overview(payload)
    try:
        validate_news_digest(payload)
    except ValueError:
        return None
    return payload


def parse_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("AI response did not contain a JSON object.")
    return json.loads(text[start : end + 1])


def minimum_digest_items(brief: dict) -> int:
    """Quality gate: do not manufacture weak stories on a quiet news day."""
    rule_digest = get_rule_digest_with_pool(brief)
    cards = (rule_digest.get("news_pool") or {}).get("top_candidates", []) or []
    return min(30, max(1, len(cards)))


def validate_news_digest(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("news digest is not an object")
    version = payload.get("version", "")
    if version not in {"news-digest-ai-v1", "news-digest-ai-v2", "news-digest-ai-v3", "news-digest-v4", "news-digest-v5"}:
        payload["version"] = "news-digest-ai-v2"
    if not isinstance(payload.get("overview"), list):
        payload["overview"] = []
    if not isinstance(payload.get("sections"), list) or not payload["sections"]:
        raise ValueError("news digest sections is empty")

    total_items = 0
    banned_prefixes = ("观点：", "观点:", "新闻1", "新闻2", "新闻3", "要点1", "要点2")
    for section in payload["sections"]:
        if not isinstance(section, dict) or not clean_digest_text(section.get("title")):
            raise ValueError("news digest section missing title")
        section["title"] = clean_digest_text(section.get("title"))
        if not isinstance(section.get("items"), list) or not section["items"]:
            raise ValueError(f"news digest section has no items: {section.get('title')}")
        for item in section["items"]:
            if not isinstance(item, dict):
                raise ValueError(f"news digest item is not object: {section.get('title')}")
            thesis = clean_digest_text(item.get("thesis"))
            summary = clean_digest_text(item.get("summary"))
            if not thesis:
                raise ValueError(f"news digest item missing thesis: {section.get('title')}")
            if thesis.startswith(banned_prefixes):
                raise ValueError(f"news digest item uses weak label: {thesis}")
            if "信息来源" in thesis or "信息来源" in summary:
                raise ValueError("news digest should not expose source labels in body")
            item["thesis"] = thesis
            item["summary"] = summary
            if item.get("time"):
                item["time"] = clean_digest_text(item.get("time"))
            total_items += 1
    if total_items < 8:
        raise ValueError("news digest has too few items")


def clean_digest_text(value) -> str:
    return " ".join(str(value or "").replace("\n", " ").split())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成松果早安汇报")
    parser.add_argument("--save", action="store_true", help="保存结构化输入和早报文本到 demos 目录")
    parser.add_argument("--no-ai", action="store_true", help="不调用模型，强制使用模板版早报")
    parser.add_argument("--mock-weather", action="store_true", help="不调用真实天气，使用内置假天气")
    parser.add_argument("--mock-market", action="store_true", help="不调用真实市场数据，使用内置占位市场数据")
    parser.add_argument("--mock-news", action="store_true", help="不调用真实新闻数据，使用内置占位新闻数据")
    parser.add_argument("--mock-themes", action="store_true", help="不调用真实主题/商品数据，使用内置占位主题数据")
    parser.add_argument("--mock-companies", action="store_true", help="不调用真实公司观察池数据，使用内置占位公司数据")
    parser.add_argument("--mock-structured", action="store_true", help="不调用真实 A 股结构化数据，使用空的本地结构化数据")
    parser.add_argument("--show-json", action="store_true", help="输出结构化早报输入 JSON")
    return parser.parse_args()


def build_brief(
    settings,
    use_mock_weather: bool,
    use_mock_market: bool,
    use_mock_news: bool,
    use_mock_themes: bool,
    use_mock_companies: bool,
    use_mock_structured: bool = False,
) -> dict:
    weather = None
    if settings.use_real_weather and not use_mock_weather:
        try:
            weather = build_weather_data(settings)
        except WeatherClientError as error:
            print("真实天气获取失败，先使用内置假天气。")
            print(f"错误信息：{error}")
            print("你可以稍后重试，或临时加 --mock-weather 跳过真实天气。")
            print("")

    market_data = build_market_data(settings, use_mock_market)
    china_market_data = build_china_market_data(settings)
    structured_market_data = build_structured_market_data(settings, use_mock_structured)
    news_data = enrich_news_snapshot(build_news_data(settings, use_mock_news))
    economic_calendar = build_economic_calendar_data(settings)
    theme_data = build_theme_data(settings, use_mock_themes)
    company_data = enrich_company_snapshot(build_company_data(settings, use_mock_companies))
    user_profile = load_user_profile(settings.user_profile_path)

    from datetime import date

    schedule = None
    if settings.outlook_feature_enabled and settings.use_real_outlook:
        schedule, outlook_error = get_today_outlook_or_error(settings)
        if outlook_error:
            print("真实 Outlook 日程获取失败，先使用本地日程文件。")
            print(f"错误信息：{outlook_error}")
            print("公司 Outlook 授权可暂缓；当前阶段使用 backend/data/local_schedule.json。")
            print("")

    if not schedule:
        schedule = load_local_schedule(settings.local_schedule_path, date.today())

    brief = build_mock_brief(
        settings.default_city,
        weather=weather,
        schedule=schedule,
        market_data=market_data,
        news_data=news_data,
        theme_data=theme_data,
        company_data=company_data,
    )
    brief["economic_calendar"] = economic_calendar
    brief["china_market_data"] = china_market_data
    brief["structured_market_data"] = structured_market_data
    # Keep a normalized alias for older modules while the digest reads the
    # richer structured_market_data object directly.
    brief["a_share_company_data"] = {
        "companies": (structured_market_data or {}).get("a_share_companies", []),
    }
    brief["user_profile"] = user_profile
    brief["memory_summary"] = summarize_profile(user_profile)
    if schedule.get("source") == "Microsoft Graph":
        brief["outlook_tasks"] = summarize_outlook_tasks(schedule)
    else:
        brief["outlook_tasks"] = summarize_local_tasks(schedule)
    brief["insights"] = build_insights(brief)
    brief["finance_reasoning"] = build_finance_reasoning(brief)
    brief["event_timeline"] = build_event_timeline(brief)
    brief["brief_analysis"] = build_brief_analysis(brief)
    brief["news_digest"] = build_news_digest(brief)
    brief["reminder_plan"] = build_reminder_plan(brief)
    brief["butler_brief"] = build_butler_brief(brief)
    brief["avatar_3d"] = build_avatar_3d_package(brief)
    return brief


def build_weather_data(settings) -> dict:
    if settings.weather_provider == "open_meteo":
        return fetch_weather(
            latitude=settings.weather_latitude,
            longitude=settings.weather_longitude,
            timezone=settings.timezone,
            city=settings.default_city,
            timeout_seconds=settings.weather_timeout_seconds,
            retries=settings.weather_retries,
        )
    raise WeatherClientError(
        unsupported_provider_message("Weather", settings.weather_provider, SUPPORTED_WEATHER_PROVIDERS)
    )


def build_market_data(settings, use_mock_market: bool) -> dict:
    if settings.use_real_markets and not use_mock_market:
        try:
            if settings.market_provider == "yahoo":
                symbols = load_symbols(settings.market_symbols_path)
                return fetch_market_snapshot(symbols)
            if settings.market_provider in {"alphavantage", "finnhub", "polygon"}:
                raise MarketClientError(
                    f"{settings.market_provider} market provider is planned but not wired yet. "
                    "The provider switch is ready; next step is to add the actual API client."
                )
            raise MarketClientError(
                unsupported_provider_message("Market", settings.market_provider, SUPPORTED_MARKET_PROVIDERS)
            )
        except MarketClientError as error:
            print("真实市场数据获取失败，先使用内置占位市场数据。")
            print(f"错误信息：{error}")
            print("你可以稍后重试，或临时加 --mock-market 跳过真实市场数据。")
            print("")
    return build_mock_market_snapshot()


def build_news_data(settings, use_mock_news: bool) -> dict:
    if settings.use_real_news and not use_mock_news:
        try:
            if settings.news_provider == "rss":
                feeds = load_news_feeds(settings.news_feeds_path)
                return fetch_news_snapshot(feeds, max_records_per_feed=settings.news_max_records_per_query)
            if settings.news_provider == "marketaux":
                return fetch_marketaux_news(
                    api_key=settings.marketaux_api_key,
                    max_records=settings.news_max_records_per_query,
                )
            if settings.news_provider == "gdelt":
                return fetch_gdelt_news(max_records=settings.news_max_records_per_query)
            if settings.news_provider == "newsapi":
                return fetch_newsapi_news(
                    api_key=settings.newsapi_api_key,
                    max_records=max(10, settings.news_max_records_per_query * 2),
                )
            if settings.news_provider == "finnhub":
                return fetch_finnhub_news(
                    api_key=settings.finnhub_api_key,
                    max_records=max(10, settings.news_max_records_per_query * 2),
                )
            if settings.news_provider == "combined":
                return build_combined_news_data(settings)
            raise NewsClientError(
                unsupported_provider_message("News", settings.news_provider, SUPPORTED_NEWS_PROVIDERS)
            )
        except (MarketauxClientError, GdeltClientError, NewsApiClientError, FinnhubNewsClientError) as error:
            print("真实新闻数据获取失败，先使用内置占位新闻数据。")
            print(f"错误信息：{error}")
            print("你可以稍后重试，或先改回 NEWS_PROVIDER=rss。")
            print("")
        except NewsClientError as error:
            print("真实新闻数据获取失败，先使用内置占位新闻数据。")
            print(f"错误信息：{error}")
            print("你可以稍后重试，或临时加 --mock-news 跳过真实新闻数据。")
            print("")
    return build_mock_news_snapshot()


def build_combined_news_data(settings) -> dict:
    snapshots = []
    errors = []

    if settings.marketaux_api_key:
        try:
            snapshots.append(fetch_marketaux_news(
                api_key=settings.marketaux_api_key,
                max_records=settings.news_max_records_per_query,
            ))
        except MarketauxClientError as error:
            errors.append(f"Marketaux: {error}")

    if settings.newsapi_api_key:
        try:
            snapshots.append(fetch_newsapi_news(
                api_key=settings.newsapi_api_key,
                max_records=max(10, settings.news_max_records_per_query * 2),
            ))
        except NewsApiClientError as error:
            errors.append(f"NewsAPI: {error}")

    if settings.finnhub_api_key:
        try:
            snapshots.append(fetch_finnhub_news(
                api_key=settings.finnhub_api_key,
                max_records=max(10, settings.news_max_records_per_query * 2),
            ))
        except FinnhubNewsClientError as error:
            errors.append(f"Finnhub: {error}")

    # X is deliberately discovery-only. Its posts carry confidence=lead and
    # the editorial fact-card filter will not display them without independent
    # corroboration from a filing, official notice, or trusted newsroom.
    if settings.x_bearer_token:
        try:
            snapshots.append(fetch_x_lead_snapshot(
                bearer_token=settings.x_bearer_token,
                max_records=max(10, settings.news_max_records_per_query),
            ))
        except XClientError as error:
            errors.append(f"X leads: {error}")

    try:
        feeds = load_news_feeds(settings.news_feeds_path)
        snapshots.append(fetch_news_snapshot(feeds, max_records_per_feed=settings.news_max_records_per_query))
    except NewsClientError as error:
        errors.append(f"RSS: {error}")

    # GDELT is discovery-only. Keep its failure isolated so a shared-IP rate
    # limit cannot hold up the usable RSS, official and paid-provider pool.
    try:
        snapshots.append(
            fetch_gdelt_news(
                max_records=max(30, settings.news_max_records_per_query * 3),
                timeout_seconds=10,
            )
        )
    except GdeltClientError as error:
        errors.append(f"GDELT: {error}")

    merged = merge_news_snapshots(snapshots)
    merged["errors"] = (merged.get("errors") or []) + errors
    return merged


def build_economic_calendar_data(settings) -> dict:
    if settings.use_real_economic_calendar:
        try:
            if settings.economic_calendar_provider == "nasdaq":
                return fetch_economic_calendar(days=settings.economic_calendar_days)
            raise EconomicCalendarError(
                unsupported_provider_message(
                    "Economic calendar",
                    settings.economic_calendar_provider,
                    SUPPORTED_ECONOMIC_CALENDAR_PROVIDERS,
                )
            )
        except EconomicCalendarError as error:
            print("真实财经日历获取失败，先使用空财经日历。")
            print(f"错误信息：{error}")
            print("你可以稍后重试，或临时设置 USE_REAL_ECONOMIC_CALENDAR=false。")
            print("")
    return build_mock_economic_calendar()


def build_china_market_data(settings) -> dict:
    if settings.use_real_china_markets:
        try:
            if settings.china_market_provider == "eastmoney":
                return fetch_china_market_snapshot(
                    sector_max_count=settings.china_sector_max_count,
                )
            raise ChinaMarketError(
                unsupported_provider_message(
                    "China market",
                    settings.china_market_provider,
                    SUPPORTED_CHINA_MARKET_PROVIDERS,
                )
            )
        except ChinaMarketError as error:
            print("真实 A 股市场数据获取失败，先保留空的中国市场数据。")
            print(f"错误信息：{error}")
            print("你可以稍后重试，或临时设置 USE_REAL_CHINA_MARKETS=false。")
            print("")
    return build_mock_china_market_snapshot()


def build_structured_market_data(settings, use_mock_structured: bool = False) -> dict:
    if settings.use_real_structured_market and not use_mock_structured:
        try:
            if settings.structured_market_provider == "touzid":
                return fetch_touzid_market_snapshot(
                    token=settings.touzid_token,
                    token_path=settings.touzid_token_path,
                    timeout_seconds=settings.touzid_timeout_seconds,
                    industry_max_count=settings.touzid_industry_max_count,
                    index_symbols=parse_symbol_list(settings.touzid_index_symbols),
                    a_share_watchlist=load_a_share_watchlist(settings.a_share_watchlist_path),
                    stock_max_count=settings.touzid_stock_max_count,
                    announcement_days=settings.touzid_announcement_days,
                    finreport_fields=parse_symbol_list(settings.touzid_finreport_fields),
                    fundamental_limit=settings.touzid_fundamental_limit,
                )
            raise TouzidClientError(
                unsupported_provider_message(
                    "Structured market",
                    settings.structured_market_provider,
                    SUPPORTED_STRUCTURED_MARKET_PROVIDERS,
                )
            )
        except TouzidClientError as error:
            print("Structured market data fetch failed; continuing with an empty structured market dataset.")
            print(f"Error: {error}")
            print("")
    return build_mock_structured_market_snapshot()


def build_mock_structured_market_snapshot() -> dict:
    return {
        "source": "mock",
        "provider": "mock",
        "industries": [],
        "index_valuation": [],
        "errors": [],
        "note": "Structured market data is empty because the real provider was skipped or unavailable.",
    }


def build_theme_data(settings, use_mock_themes: bool) -> dict:
    if settings.use_real_themes and not use_mock_themes:
        try:
            if settings.theme_provider == "yahoo":
                symbols = load_theme_symbols(settings.theme_symbols_path)
                return fetch_theme_snapshot(symbols)
            if settings.theme_provider == "alphavantage":
                raise ThemeClientError(
                    "alphavantage theme provider is planned but not wired yet. "
                    "The provider switch is ready; next step is to add the actual API client."
                )
            raise ThemeClientError(
                unsupported_provider_message("Theme", settings.theme_provider, SUPPORTED_THEME_PROVIDERS)
            )
        except ThemeClientError as error:
            print("真实主题/商品数据获取失败，先使用内置占位主题数据。")
            print(f"错误信息：{error}")
            print("你可以稍后重试，或临时加 --mock-themes 跳过真实主题/商品数据。")
            print("")
    return build_mock_theme_snapshot()


def build_company_data(settings, use_mock_companies: bool) -> dict:
    if settings.use_real_companies and not use_mock_companies:
        try:
            if settings.company_provider == "watchlist":
                companies = load_company_watchlist(settings.company_watchlist_path)
                return fetch_company_snapshot(
                    companies,
                    timeout_seconds=settings.company_timeout_seconds,
                    max_articles_per_company=settings.company_news_max_records,
                    max_companies=settings.company_max_count,
                )
            if settings.company_provider in {"marketaux", "finnhub"}:
                raise CompanyClientError(
                    f"{settings.company_provider} company provider is planned but not wired yet. "
                    "The provider switch is ready; next step is to add the actual API client."
                )
            raise CompanyClientError(
                unsupported_provider_message("Company", settings.company_provider, SUPPORTED_COMPANY_PROVIDERS)
            )
        except CompanyClientError as error:
            print("真实公司观察池数据获取失败，先使用内置占位公司数据。")
            print(f"错误信息：{error}")
            print("你可以稍后重试，或临时加 --mock-companies 跳过真实公司数据。")
            print("")
    return build_mock_company_snapshot()


def uses_mock_data(brief: dict) -> bool:
    source_paths = [
        ("weather", "source"),
        ("market_data", "source"),
        ("news_data", "source"),
        ("theme_data", "source"),
        ("company_data", "source"),
    ]
    for section, field in source_paths:
        if str(brief.get(section, {}).get(field, "")).lower() == "mock":
            return True
    return False


def build_news_digest_prompt(brief: dict) -> str:
    """Build the stricter v4 prompt used by the AI news digest layer."""
    rule_digest = get_rule_digest_with_pool(brief)
    news_pool = (rule_digest.get("news_pool") or {}).get("top_candidates", [])

    def compact_text(value, limit=180):
        text = clean_digest_text(value)
        return text[:limit]

    def compact_item(item: dict, limit=180) -> dict:
        if not isinstance(item, dict):
            return {}
        return {
            "time": compact_text(item.get("time") or item.get("published_at"), 32),
            "section": compact_text(item.get("section"), 24),
            "title": compact_text(item.get("title") or item.get("thesis"), 120),
            "summary": compact_text(item.get("summary") or item.get("description"), limit),
            "facts": [compact_text(fact, 24) for fact in (item.get("facts") or [])[:5]],
            "source": compact_text(item.get("source") or item.get("source_name"), 48),
            "url": compact_text(item.get("url") or item.get("source_url"), 120),
            "score": item.get("score"),
        }

    def compact_index(item: dict) -> dict:
        if not isinstance(item, dict):
            return {}
        return {
            "name": compact_text(item.get("name") or item.get("label"), 40),
            "price": item.get("price") or item.get("last") or item.get("value"),
            "change_pct": item.get("change_pct") or item.get("change_percent") or item.get("pct_change"),
            "note": compact_text(item.get("note") or item.get("summary"), 90),
        }

    digest_input = {
        "date": brief.get("date"),
        "city": brief.get("city"),
        "rule_digest_overview": [compact_text(item, 120) for item in rule_digest.get("overview", [])[:5]],
        "fact_cards": [compact_item(item, 140) for item in news_pool[:16]],
        "market_indices": [compact_index(item) for item in market_indices[:4]],
        "china_market_indices": [compact_index(item) for item in china_indices[:4]],
        "economic_calendar": [compact_item(item, 60) for item in (brief.get("economic_calendar") or {}).get("events", [])[:3]],
        "event_timeline": [compact_item(item, 70) for item in timeline[:6]],
    }
    payload = json.dumps(digest_input, ensure_ascii=False, indent=2)
    return f"""
你是“松果”的财经早报总编辑。你的目标是做一份接近专业财经早报的中文稿，不是堆标题，也不是投资建议。

只输出 JSON，不要输出 Markdown，不要在 JSON 外写任何解释。

JSON 结构必须是：
{{
  "version": "news-digest-ai-v4",
  "date": "...",
  "city": "...",
  "overview": ["今天最重要的事实1", "今天最重要的事实2", "今天最重要的事实3"],
  "sections": [
    {{
      "title": "宏观经济",
      "items": [
        {{
          "time": "07-12 08:30",
          "thesis": "一句完整的事实型标题，不写“观点：”",
          "summary": "用两到三句话讲清事实、关键数字、相关主体、为什么值得进入早报。"
        }}
      ]
    }}
  ]
}}

栏目只能使用以下标题，并按这个顺序输出；没有足够高质量事实的栏目可以少写，但不要乱造：
1. 宏观经济
2. 地产动态
3. 股市盘点
4. 行业观察
5. 公司要闻
6. 环球视野
7. 金融数据

输入说明：
- fact_cards 是已经被本地规则筛过的候选事实卡片。优先使用 fact_cards，不要绕开它自行扩写。
- 每张卡片只有 title、summary、facts、time、source、url 这些字段；输出只能基于这些字段。
- 如果某张卡片 summary 为空或太短，只能引用标题层面的事实，不能补写背景细节。

选题标准：
- 只选过去 24 小时内对全球宏观、政策、股市、产业链、公司经营、供需价格有真实信息增量的事件。
- 优先选择带时间、主体、数字、公告、财报、政策、订单、产能、供给、价格、利率、汇率、库存、航运、监管动作的事实。
- 不要选择娱乐、生活方式、软文、泛评论、个人观点、无明确主体和数字的文章。
- 如果输入里只有标题、没有摘要或数字，除非事件本身非常重大，否则不要写入早报；不要在正文里写“只有标题层面信息”这类占位话。
- 不能补写输入里没有的细节。禁止自行添加政策工具、金额、司法进展、公司关系、交易细节、财报数字、订单规模、产能变化。
- 对标题看起来很戏剧化但缺少细节支撑的内容，要降权或跳过；不要把新闻标题扩写成确定事实。
- 如果只是指数涨跌，必须写清“哪个市场、涨跌幅、成交/资金/板块、可能相关事实”，不能直接推导成基本面结论。
- 如果涉及公司，优先写订单、财报、公告、监管、产品、供应链、资本开支、产能、裁员、诉讼等硬事实。
- 如果涉及产业，优先写供需、价格、产能、库存、政策补贴、出口管制、资本开支、关键公司动作。

写作格式：
- thesis 直接写结论式事实，例如“美国科技股估值压力继续受利率预期牵制”，不要写“观点：”“新闻1”“要点1”。
- summary 必须包含事实细节，不要空话；每条 70-160 个中文字符。
- summary 只能改写输入中已经出现的信息；如果输入没有足够细节，就写“目前只有标题层面信息，需等待公告或原文核验”，或直接不选这条。
- 所有数字、百分比、金额、指数点位必须原样来自输入；不要自行换算，也不要补写输入里没有的“美元指数、美债收益率、北向资金、补贴、税收优惠、黄金、日元”等词。
- 可以在 summary 中写“后续看什么”，但必须具体到数据、政策、公告、公司或市场，不要写泛泛的“继续关注”。
- 不要在正文展示“信息来源”“source”“来自某某 API”。
- 不写买卖建议，不写“推荐、买入、卖出、看多、看空”。
- 全文总条数控制在 6-10 条；每个栏目 1-2 条。必须至少输出 6 条；如果宏观和公司事件不够，就从股市盘点、环球视野、金融数据里选择事实更完整的卡片补足。
- 可补足的事实卡包括：主要指数涨跌、Berkshire 与 S&P 500 的相对表现、印度股市与 Q1 财报/油价观察、台风导致的交通扰动、台湾志愿兵人数变化、西班牙野火伤亡等；但仍然只能使用输入中已有事实。
- 中文表达要像专业早报：克制、具体、事实优先。英文专有名词保留英文。

输入数据：
{payload}
""".strip()


def is_editorially_complete_digest_item(thesis: str, summary: str) -> bool:
    """Reject public rows that are vague, duplicated, or lack a market period."""
    compact_thesis = re.sub(r"[\s，。；：、,.!！?？-]", "", thesis).lower()
    compact_summary = re.sub(r"[\s，。；：、,.!！?？-]", "", summary).lower()
    # Keep concise, evidence-rich details (for example a multi-day fund-flow
    # window) instead of discarding them merely because they are short.
    if len(compact_summary) < 8:
        return False
    if len(compact_thesis) >= 12 and (
        compact_thesis in compact_summary or compact_summary in compact_thesis
    ):
        return False

    vague_subjects = (
        "某头部企业", "又一头部企业", "这只股票", "该股", "该公司", "上述公司",
        "相关公司", "相关股票", "一家企业", "一只股票",
    )
    if any(term in f"{thesis}{summary}" for term in vague_subjects):
        return False
    if "更名" in thesis and not any(marker in summary for marker in ("更名为", "改名为", "原名", "新名称")):
        return False
    if any(term in thesis for term in ("答案", "解决方案")) and any(
        term in summary for term in ("已有答案", "给出答案", "答案是", "有了答案")
    ):
        return False

    market_move_terms = ("上涨", "下跌", "涨", "跌", "熔断", "反弹", "回落", "净流入", "净流出")
    if any(term in f"{thesis}{summary}" for term in market_move_terms):
        # A bare publication date (or merely the character "日") is not a
        # usable market window.  The rendered sentence needs to say when the
        # move happened or over which trading period it accumulated.
        explicit_window = re.compile(
            r"(?:\d{1,2}月\d{1,2}[日号]|\d{1,2}-\d{1,2}(?:至\d{1,2}-\d{1,2})?|"
            r"今日|昨日|当天|当日|盘中|收盘|截至(?:收盘|\d{1,2}月\d{1,2}[日号])|"
            r"本周|本月|过去\d+[个]?(?:交易)?日|连续\d+[个]?(?:交易)?日|近\d+[个]?(?:交易)?日)"
        )
        if not explicit_window.search(f"{thesis}{summary}"):
            return False
    return True


def validate_news_digest(payload: dict) -> None:
    """Validate and normalize the stricter AI news digest payload."""
    if not isinstance(payload, dict):
        raise ValueError("news digest is not an object")
    payload["version"] = "news-digest-ai-v4"
    if not isinstance(payload.get("overview"), list):
        payload["overview"] = []
    if not isinstance(payload.get("sections"), list) or not payload["sections"]:
        raise ValueError("news digest sections is empty")

    allowed_titles = {
        "宏观经济",
        "地产动态",
        "股市盘点",
        "行业观察",
        "公司要闻",
        "环球视野",
        "金融数据",
    }
    banned_prefixes = ("观点：", "观点:", "新闻1", "新闻2", "新闻3", "要点1", "要点2", "信息来源")
    banned_terms = ("信息来源", "source:", "Source:", "买入", "卖出", "推荐")
    total_items = 0

    normalized_sections = []
    for section in payload["sections"]:
        if not isinstance(section, dict):
            continue
        title = clean_digest_text(section.get("title"))
        if title not in allowed_titles:
            continue
        items = []
        for item in section.get("items") or []:
            if not isinstance(item, dict):
                continue
            thesis = clean_digest_text(item.get("thesis"))
            summary = clean_digest_text(item.get("summary"))
            if not thesis or not summary:
                continue
            if thesis.startswith(banned_prefixes):
                raise ValueError(f"news digest item uses weak label: {thesis}")
            if any(term in thesis or term in summary for term in banned_terms):
                raise ValueError("news digest contains banned wording")
            cleaned_item = {"thesis": thesis, "summary": summary}
            if item.get("time"):
                cleaned_item["time"] = clean_digest_text(item.get("time"))
            items.append(cleaned_item)
            total_items += 1
        if items:
            normalized_sections.append({"title": title, "items": items[:5]})

    if total_items < 5:
        raise ValueError("news digest has too few usable items")
    payload["sections"] = normalized_sections


def validate_news_digest_grounding(payload: dict, brief: dict) -> None:
    """Reject AI digests that add obvious unsupported facts beyond the input pool."""
    rule_digest = get_rule_digest_with_pool(brief)
    fact_cards = (rule_digest.get("news_pool") or {}).get("top_candidates", []) or []
    fact_card_by_id = {
        clean_digest_text(card.get("id")): card
        for card in fact_cards
        if isinstance(card, dict) and clean_digest_text(card.get("id"))
    }
    evidence_blob = json.dumps(
        {
            "rule_digest": rule_digest,
            "market_data": brief.get("market_data", {}),
            "china_market_data": brief.get("china_market_data", {}),
            "economic_calendar": brief.get("economic_calendar", {}),
        },
        ensure_ascii=False,
    )

    unsupported_terms = [
        "税收优惠",
        "首付",
        "机构投资者",
        "单户住宅",
        "美元指数",
        "美债收益率",
        "北向资金",
        "净流出",
        "黄金",
        "日元",
        "约20%",
        "20%",
    ]
    grounded_sections = []
    total_grounded = 0
    for section in payload.get("sections", []):
        grounded_items = []
        for item in section.get("items", []):
            text = f"{item.get('thesis', '')} {item.get('summary', '')}"
            card_id = clean_digest_text(item.get("card_id"))
            card = fact_card_by_id.get(card_id)
            # The final author must be able to point back to a single fact card.
            # This keeps the prose honest when a model is tempted to complete a
            # familiar market narrative from general knowledge.
            if fact_card_by_id and not card:
                continue
            evidence_for_item = json.dumps(card, ensure_ascii=False) if card else evidence_blob
            is_grounded = True
            for term in unsupported_terms:
                if term in text and term not in evidence_for_item:
                    is_grounded = False
                    break
            if not is_grounded:
                continue
            for number in re.findall(r"\d+(?:\.\d+)?%?", text):
                if len(number) <= 1:
                    continue
                if number not in evidence_for_item and number.replace("%", "") not in evidence_for_item:
                    is_grounded = False
                    break
            if is_grounded:
                grounded_items.append(item)
                total_grounded += 1
        if grounded_items:
            section["items"] = grounded_items
            grounded_sections.append(section)
    # A quiet day may contain only one fact the model chooses to rewrite. The
    # remaining verified cards are deterministically restored afterwards, so
    # requiring every card here turns a valid AI result into an unnecessary
    # fallback.
    required_grounded = 1 if fact_card_by_id else 0
    if total_grounded < required_grounded:
        raise ValueError(f"news digest has too few grounded items: {total_grounded}")
    payload["sections"] = grounded_sections
    # The overview is not an AI free-form area. Generate it from the same
    # validated items so the headline layer cannot smuggle in outside context.
    payload["overview"] = [
        clean_digest_text(item.get("thesis"))
        for section in grounded_sections
        for item in section.get("items", [])
        if clean_digest_text(item.get("thesis"))
    ][:3]


def build_news_digest_prompt(brief: dict) -> str:
    """Build the final fact-card grounded prompt for the AI news digest layer."""
    rule_digest = get_rule_digest_with_pool(brief)
    news_pool = (rule_digest.get("news_pool") or {}).get("top_candidates", [])
    timeline = (brief.get("event_timeline") or {}).get("events", [])
    market_indices = (brief.get("market_data") or {}).get("indices", [])
    china_indices = (brief.get("china_market_data") or {}).get("indices", [])

    def compact_text(value, limit=180):
        text = clean_digest_text(value)
        return text[:limit]

    def compact_item(item: dict, limit=180) -> dict:
        if not isinstance(item, dict):
            return {}
        return {
            "time": compact_text(item.get("time") or item.get("published_at"), 32),
            "section": compact_text(item.get("section"), 24),
            "title": compact_text(item.get("title") or item.get("thesis"), 120),
            "summary": compact_text(item.get("summary") or item.get("description"), limit),
            "facts": [compact_text(fact, 24) for fact in (item.get("facts") or [])[:5]],
            "source": compact_text(item.get("source") or item.get("source_name"), 48),
            "url": compact_text(item.get("url") or item.get("source_url"), 120),
            "score": item.get("score"),
        }

    def compact_index(item: dict) -> dict:
        if not isinstance(item, dict):
            return {}
        return {
            "name": compact_text(item.get("name") or item.get("label"), 40),
            "price": item.get("price") or item.get("last") or item.get("value") or item.get("close"),
            "change_pct": item.get("change_pct") or item.get("change_percent") or item.get("pct_change") or item.get("change_percent_from_previous_close"),
            "note": compact_text(item.get("note") or item.get("summary"), 90),
        }

    digest_input = {
        "date": brief.get("date"),
        "city": brief.get("city"),
        "rule_digest_overview": [compact_text(item, 120) for item in rule_digest.get("overview", [])[:5]],
        "fact_cards": [compact_item(item, 180) for item in news_pool[:18]],
        "market_indices": [compact_index(item) for item in market_indices[:5]],
        "china_market_indices": [compact_index(item) for item in china_indices[:5]],
        "economic_calendar": [compact_item(item, 90) for item in (brief.get("economic_calendar") or {}).get("events", [])[:4]],
    }
    payload = json.dumps(digest_input, ensure_ascii=False, indent=2)
    return f"""
你是“松果”的财经早报总编辑。你的目标是做一份接近专业财经早报的中文稿，不是堆标题，也不是投资建议。

只输出 JSON，不要输出 Markdown，不要在 JSON 外写任何解释。

JSON 结构必须是：
{{
  "version": "news-digest-ai-v4",
  "date": "...",
  "city": "...",
  "overview": ["今天最重要的事实", "今天最重要的事实", "今天最重要的事实"],
  "sections": [
    {{
      "title": "宏观经济",
      "items": [
        {{
          "time": "07-12 08:30",
          "thesis": "一句完整的事实型标题，不写“观点：”",
          "summary": "用两到三句话讲清事实、关键数字、相关主体、为什么值得进入早报。"
        }}
      ]
    }}
  ]
}}

栏目只能使用以下标题，并按这个顺序输出；没有足够高质量事实的栏目可以少写，但不要乱凑：
1. 宏观经济
2. 地产动态
3. 股市盘点
4. 行业观察
5. 公司要闻
6. 环球视野
7. 金融数据

输入说明：
- fact_cards 是已经被本地规则筛过的候选事实卡片。只能使用 fact_cards、market_indices、china_market_indices、economic_calendar，不要使用其他背景知识自行扩写。
- 每张卡片只有 title、summary、facts、time、source、url 这些字段；输出只能基于这些字段。
- 如果某张卡片 summary 为空或太短，只能引用标题层面的事实，不能补写背景细节。

选题标准：
- 只选过去 24 小时内对全球宏观、政策、股市、产业链、公司经营、供需价格有真实信息增量的事件。
- 优先选择带时间、主体、数字、公告、财报、政策、订单、产能、供给、价格、利率、汇率、库存、航运、监管动作的事实。
- 不要选择娱乐、生活方式、软文、泛评论、个人观点、无明确主体和数字的文章。
- 如果输入里只有标题、没有摘要或数字，除非事件本身非常重大，否则不要写入早报。
- 不能补写输入里没有的细节。禁止自行添加政策工具、金额、司法进展、公司关系、交易细节、财报数字、订单规模、产能变化。
- 对标题看起来很戏剧化但缺少细节支撑的内容，要降权或跳过；不要把新闻标题扩写成确定事实。
- 如果只是指数涨跌，必须写清“哪个市场、涨跌幅、成交/资金/板块、可能相关事实”，不能直接推导成基本面结论。
- 如果涉及公司，优先写订单、财报、公告、监管、产品、供应链、资本开支、产能、裁员、诉讼等硬事实。
- 如果涉及产业，优先写供需、价格、产能、库存、政策补贴、出口管制、资本开支、关键公司动作。

写作格式：
- 你必须从 fact_cards 的前 10 张中至少选择 6 张写入 sections；每张被选择的 fact_card 只能生成 1 条 item。
- 不要只输出 3 个栏目；至少输出 4 个不同栏目。如果某个栏目没有合适内容，可以把事实更完整的卡片放到“股市盘点”“公司要闻”“环球视野”或“金融数据”。
- thesis 直接写结论式事实，例如“韩国 KOSPI 在芯片股带动下创阶段新高”，不要写“观点：”“新闻1”“要点1”。
- summary 必须包含事实细节，不要空话；每条 70-160 个中文字符。
- summary 只能改写输入中已经出现的信息；如果输入没有足够细节，直接不选这条，不要写成占位说明。
- 所有数字、百分比、金额、指数点位必须原样来自输入；不要自行换算，也不要补写输入里没有的“美元指数、美债收益率、北向资金、补贴、税收优惠、黄金、日元”等词。
- 可以在 summary 中写“后续看什么”，但必须具体到数据、政策、公告、公司或市场，不要写泛泛的“继续关注”。
- 不要在正文展示“信息来源”“source”“来自某某 API”。
- 不写买卖建议，不写“推荐、买入、卖出、看多、看空”。
- 全文总条数控制在 8-12 条；每个栏目 1-2 条。优先保证质量，不要为了凑数写弱新闻。
- 中文表达要像专业早报：克制、具体、事实优先。英文专有名词保留英文。

输入数据：
{payload}
""".strip()


def validate_news_digest(payload: dict) -> None:
    """Validate and normalize the final AI news digest payload."""
    if not isinstance(payload, dict):
        raise ValueError("news digest is not an object")
    payload["version"] = "news-digest-ai-v4"
    if not isinstance(payload.get("overview"), list):
        payload["overview"] = []
    if not isinstance(payload.get("sections"), list) or not payload["sections"]:
        raise ValueError("news digest sections is empty")

    allowed_titles = {
        "宏观经济",
        "地产动态",
        "股市盘点",
        "行业观察",
        "公司要闻",
        "环球视野",
        "金融数据",
    }
    banned_prefixes = ("观点：", "观点:", "新闻1", "新闻2", "新闻3", "要点1", "要点2", "信息来源")
    banned_terms = (
        "信息来源",
        "source:",
        "Source:",
        "买入",
        "卖出",
        "推荐",
        "标题层面信息",
        "等待公告",
        "等待原文",
        "尚未披露",
        "暂未披露",
        "具体条款尚未公布",
    )
    total_items = 0

    normalized_sections = []
    for section in payload["sections"]:
        if not isinstance(section, dict):
            continue
        title = clean_digest_text(section.get("title"))
        if title not in allowed_titles:
            continue
        items = []
        for item in section.get("items") or []:
            if not isinstance(item, dict):
                continue
            thesis = clean_digest_text(item.get("thesis"))
            summary = clean_digest_text(item.get("summary"))
            if not thesis or not summary:
                continue
            if thesis.startswith(banned_prefixes):
                raise ValueError(f"news digest item uses weak label: {thesis}")
            if any(term in thesis or term in summary for term in banned_terms):
                continue
            cleaned_item = {"thesis": thesis, "summary": summary}
            if item.get("time"):
                cleaned_item["time"] = clean_digest_text(item.get("time"))
            items.append(cleaned_item)
            total_items += 1
        if items:
            normalized_sections.append({"title": title, "items": items[:5]})

    if total_items < 5:
        raise ValueError("news digest has too few usable items")
    payload["sections"] = normalized_sections


def repair_news_digest_payload(payload: dict, brief: dict, min_items: int = 6) -> None:
    """Fill sparse AI output with grounded local fact cards."""
    if not isinstance(payload, dict):
        return
    rule_digest = get_rule_digest_with_pool(brief)
    candidates = (rule_digest.get("news_pool") or {}).get("top_candidates", [])
    sections = payload.get("sections")
    if not isinstance(sections, list):
        sections = []
        payload["sections"] = sections

    allowed_titles = ["宏观经济", "地产动态", "股市盘点", "行业观察", "公司要闻", "环球视野", "金融数据"]
    by_title: dict[str, dict] = {}
    seen: set[str] = set()

    for section in sections:
        if not isinstance(section, dict):
            continue
        title = clean_digest_text(section.get("title"))
        if title not in allowed_titles:
            continue
        items = section.get("items")
        if not isinstance(items, list):
            items = []
            section["items"] = items
        by_title[title] = section
        for item in items:
            if isinstance(item, dict):
                seen.add(normalize_digest_key(item.get("thesis")))

    for title in allowed_titles:
        if title not in by_title:
            section = {"title": title, "items": []}
            sections.append(section)
            by_title[title] = section

    total = count_digest_items(payload)
    for card in candidates:
        if total >= min_items:
            break
        if not usable_supplement_card(card):
            continue
        title = clean_digest_text(card.get("section"))
        if title not in by_title:
            title = "股市盘点"
        thesis = clean_digest_text(card.get("title"))[:140]
        summary = clean_digest_text(card.get("summary"))[:260]
        key = normalize_digest_key(thesis)
        if not thesis or not summary or key in seen:
            continue
        item = {"thesis": thesis, "summary": summary}
        if card.get("id"):
            item["card_id"] = clean_digest_text(card.get("id"))
        if card.get("time"):
            item["time"] = clean_digest_text(card.get("time"))
        by_title[title]["items"].append(item)
        seen.add(key)
        total += 1

    payload["sections"] = [
        {"title": section["title"], "items": section.get("items", [])}
        for section in sections
        if section.get("title") in allowed_titles and section.get("items")
    ]


def usable_supplement_card(card: dict) -> bool:
    if not isinstance(card, dict):
        return False
    kind = clean_digest_text(card.get("kind"))
    source = clean_digest_text(card.get("source")).lower()
    title = clean_digest_text(card.get("title"))
    summary = clean_digest_text(card.get("summary"))
    if not title or not summary:
        return False
    if kind in {"economic_calendar", "a_share_financial", "a_share_announcement", "a_share_supervision"}:
        return True
    if source in {"economic_calendar", "a_share_financials", "a_share_announcements", "a_share_supervision"}:
        return True
    # Do not push an untranslated raw English headline onto the Chinese page
    # merely to increase the count. The AI can select and translate it on a
    # later run once there is enough factual material.
    return (
        kind in {"article", "timeline", "company_news"}
        and contains_cjk(title)
        and contains_cjk(summary)
        and len(card.get("facts") or []) >= 2
    )


def refresh_digest_overview(payload: dict) -> None:
    """Derive the overview from final verified rows, never free-form AI text."""
    if not isinstance(payload, dict):
        return
    payload["overview"] = [
        clean_digest_text(item.get("thesis"))
        for section in payload.get("sections") or []
        if isinstance(section, dict)
        for item in section.get("items") or []
        if isinstance(item, dict) and clean_digest_text(item.get("thesis"))
    ][:3]


def append_missing_fact_cards(settings, payload: dict, brief: dict) -> None:
    """Translate any editorial cards omitted by the first AI pass.

    The first pass chooses a clean structure; this narrow second pass only
    translates an already-verified card and cannot introduce a new story.
    """
    rule_digest = get_rule_digest_with_pool(brief)
    cards = (rule_digest.get("news_pool") or {}).get("top_candidates", []) or []
    if not cards:
        return

    used_ids = {
        clean_digest_text(item.get("card_id"))
        for section in payload.get("sections") or []
        if isinstance(section, dict)
        for item in section.get("items") or []
        if isinstance(item, dict) and clean_digest_text(item.get("card_id"))
    }
    missing = [card for card in cards if clean_digest_text(card.get("id")) not in used_ids]
    if not missing:
        return

    prompt_cards = [
        {
            "id": clean_digest_text(card.get("id")),
            "time": clean_digest_text(card.get("time")),
            "section": clean_digest_text(card.get("section")),
            "title": clean_digest_text(card.get("title")),
            "summary": clean_digest_text(card.get("summary")),
            "facts": card.get("facts") or [],
        }
        for card in missing[:8]
    ]
    prompt = f"""
把下面每一张事实卡翻译/改写为中文财经早报条目。只输出 JSON：
{{"items":[{{"card_id":"原 id","time":"原 time","section":"原 section","thesis":"中文事实标题","summary":"中文事实摘要"}}]}}

必须每张卡都输出一条；只能转述 title、summary、facts 的已有事实；不要补背景、影响、判断、来源或投资建议。

事实卡：
{json.dumps(prompt_cards, ensure_ascii=False)}
""".strip()
    try:
        model = "deepseek-chat" if "v4" in settings.deepseek_model.lower() or "reason" in settings.deepseek_model.lower() else settings.deepseek_model
        raw = create_chat_completion(settings.deepseek_api_key, model, prompt, json_mode=True)
        translated = parse_json_object(raw).get("items", [])
    except (DeepSeekClientError, ValueError, json.JSONDecodeError) as error:
        print(f"遗漏事实卡翻译跳过：{error}")
        return

    cards_by_id = {clean_digest_text(card.get("id")): card for card in missing}
    allowed_titles = {"宏观经济", "地产动态", "股市盘点", "行业观察", "公司要闻", "环球视野", "金融数据"}
    sections = payload.setdefault("sections", [])
    by_title = {clean_digest_text(section.get("title")): section for section in sections if isinstance(section, dict)}
    appended = 0
    for item in translated if isinstance(translated, list) else []:
        if not isinstance(item, dict):
            continue
        card_id = clean_digest_text(item.get("card_id"))
        card = cards_by_id.get(card_id)
        thesis = clean_digest_text(item.get("thesis"))
        summary = clean_digest_text(item.get("summary"))
        if not card or not thesis or not summary:
            continue
        title = clean_digest_text(card.get("section"))
        if title not in allowed_titles:
            title = "公司要闻"
        section = by_title.get(title)
        if not section:
            section = {"title": title, "items": []}
            sections.append(section)
            by_title[title] = section
        section.setdefault("items", []).append(
            {
                "card_id": card_id,
                "time": clean_digest_text(item.get("time")) or clean_digest_text(card.get("time")),
                "thesis": thesis,
                "summary": summary,
            }
        )
        appended += 1
    if missing and appended != len(missing):
        print(f"遗漏事实卡翻译未完整覆盖：待补 {len(missing)} 条，已补 {appended} 条。")


def localize_news_digest_items(settings, payload: dict, brief: dict | None = None) -> None:
    """Translate final visible digest rows into Chinese without adding facts."""
    if settings.ai_provider != "deepseek" or not settings.deepseek_api_key:
        remove_untranslated_news_items(payload)
        return

    card_by_id = {}
    if isinstance(brief, dict):
        rule_digest = get_rule_digest_with_pool(brief)
        card_by_id = {
            clean_digest_text(card.get("id")): card
            for card in (rule_digest.get("news_pool") or {}).get("top_candidates", [])
            if isinstance(card, dict) and clean_digest_text(card.get("id"))
        }

    targets = []
    for section_index, section in enumerate(payload.get("sections") or []):
        if not isinstance(section, dict):
            continue
        for item_index, item in enumerate(section.get("items") or []):
            if not isinstance(item, dict):
                continue
            thesis = clean_digest_text(item.get("thesis"))
            summary = clean_digest_text(item.get("summary"))
            if thesis and (
                payload.get("_force_refine")
                or not contains_cjk(thesis)
                or (summary and not contains_cjk(summary))
            ):
                card = card_by_id.get(clean_digest_text(item.get("card_id")), {})
                targets.append(
                    {
                        "index": len(targets),
                        "section_index": section_index,
                        "item_index": item_index,
                        "section": clean_digest_text(section.get("title")),
                        "time": clean_digest_text(item.get("time")),
                        "thesis": thesis,
                        "summary": summary,
                        # The original evidence is passed into the small batch,
                        # so the model can name the company/ETF and retain the
                        # period of a price move instead of paraphrasing a thin
                        # RSS headline.
                        "evidence": {
                            "title": clean_digest_text(card.get("title")),
                            "summary": clean_digest_text(card.get("summary")),
                            "facts": [clean_digest_text(fact) for fact in (card.get("facts") or [])[:8]],
                        },
                    }
                )

    if not targets:
        return

    target_by_index = {item["index"]: item for item in targets}
    model = "deepseek-chat" if "v4" in settings.deepseek_model.lower() or "reason" in settings.deepseek_model.lower() else settings.deepseek_model
    # Large JSON responses are occasionally truncated by the provider. Eight
    # cards per request keeps every result small and lets one weak batch fail
    # without discarding the rest of the morning brief.
    for start in range(0, len(targets), 8):
        batch = targets[start : start + 8]
        prompt = f"""
把下面原始新闻改写为中文财经早报事实条目。只输出 JSON：
{{"items":[{{"index":0,"thesis":"中文事实提炼标题","summary":"中文提炼摘要"}}]}}

要求：
- 不是逐字翻译或照抄原标题。thesis 只保留一个最关键、可核验的事实；summary 只补充 thesis 没有写出的细节，二者不得重复或近似改写。
- 必须写清主体：公司、ETF、股票、机构、人物、产品不能用“某头部企业”“这只股票”“该公司”等代词替代。改名新闻必须写出原名和新名；“答案/方案”类新闻必须在 summary 直接写出答案。
- 涨跌、熔断、反弹、资金流入等市场表述必须给出来源中明确的日期或时间窗口（如“7月14日盘中”“截至收盘”“过去4个交易日”）。条目里的发布时间不等于事件时间窗，不能拿发布时间替代；来源没有时间窗口时，不要保留该条。
- summary 用 1-2 句说明发生了什么及可核验的信息增量；不新增背景、判断、影响、投资建议或来源。
- 产业观察只收录供需、产能、技术、监管、供应链或关键公司动作；犯罪、失踪、消费产品或一般社会新闻不要改写。
- 公司名、人名、机构名、产品名可以保留英文；普通英文句子必须转成中文。
- 数字、百分比、金额、时间保持原样。
- thesis 不要写“观点：”“新闻1”“要点1”。
- summary 控制在 45-120 个中文字符；原文没有摘要时可输出空字符串。

待处理条目：
{json.dumps([{k: v for k, v in item.items() if k in {"index", "section", "time", "thesis", "summary", "evidence"}} for item in batch], ensure_ascii=False)}
""".strip()
        try:
            raw = create_chat_completion(settings.deepseek_api_key, model, prompt, json_mode=True)
            translated = parse_json_object(raw).get("items", [])
        except (DeepSeekClientError, ValueError, json.JSONDecodeError) as error:
            print(f"第 {start // 8 + 1} 批新闻提炼失败，保留其余批次：{error}")
            continue

        for translated_item in translated if isinstance(translated, list) else []:
            if not isinstance(translated_item, dict):
                continue
            try:
                target = target_by_index[int(translated_item.get("index"))]
            except (TypeError, ValueError, KeyError):
                continue
            thesis = clean_digest_text(translated_item.get("thesis"))
            summary = clean_digest_text(translated_item.get("summary"))
            if not thesis or not contains_cjk(thesis):
                continue
            if summary and not contains_cjk(summary):
                continue
            section = payload["sections"][target["section_index"]]
            item = section["items"][target["item_index"]]
            item["thesis"] = thesis
            item["summary"] = summary

    remove_untranslated_news_items(payload)


def remove_untranslated_news_items(payload: dict) -> None:
    """Keep the public page Chinese-only even when a model response is weak."""
    sections = []
    for section in payload.get("sections") or []:
        if not isinstance(section, dict):
            continue
        items = []
        for item in section.get("items") or []:
            if not isinstance(item, dict):
                continue
            thesis = clean_digest_text(item.get("thesis"))
            summary = clean_digest_text(item.get("summary"))
            if thesis and contains_cjk(thesis) and (not summary or contains_cjk(summary)):
                items.append(item)
        if items:
            section["items"] = items
            sections.append(section)
    payload["sections"] = sections


def count_digest_items(payload: dict) -> int:
    total = 0
    for section in payload.get("sections") or []:
        if isinstance(section, dict):
            total += len([item for item in section.get("items", []) if isinstance(item, dict)])
    return total


def normalize_digest_key(value) -> str:
    return clean_digest_text(value).lower()[:80]


def contains_cjk(value) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", clean_digest_text(value)))


def get_rule_digest_with_pool(brief: dict) -> dict:
    """Reuse an existing digest only when it already carries a candidate pool."""
    existing = brief.get("news_digest")
    if isinstance(existing, dict):
        pool = (existing.get("news_pool") or {}).get("top_candidates") or []
        if pool:
            return existing
    return build_news_digest(brief)


def build_news_digest_prompt(brief: dict) -> str:
    """Final editorial prompt: collect facts first, then write a concise morning brief."""
    rule_digest = get_rule_digest_with_pool(brief)
    news_pool = (rule_digest.get("news_pool") or {}).get("top_candidates", [])
    market_indices = (brief.get("market_data") or {}).get("indices", [])
    china_indices = (brief.get("china_market_data") or {}).get("indices", [])

    def compact_text(value, limit=220):
        text = clean_digest_text(value)
        return text[:limit]

    def compact_card(item: dict, limit=260) -> dict:
        if not isinstance(item, dict):
            return {}
        return {
            "id": compact_text(item.get("id"), 32),
            "time": compact_text(item.get("time") or item.get("published_at"), 40),
            "section": compact_text(item.get("section"), 24),
            "title": compact_text(item.get("title") or item.get("thesis"), 140),
            "summary": compact_text(item.get("summary") or item.get("description"), limit),
            "facts": [compact_text(fact, 40) for fact in (item.get("facts") or [])[:8]],
            "kind": compact_text(item.get("kind"), 32),
            "confidence": compact_text(item.get("source_confidence"), 16),
            "score": item.get("score"),
            "importance_score": item.get("importance_score", item.get("score")),
            "cluster_size": item.get("cluster_size", 1),
            "cluster_sources": [compact_text(source, 40) for source in (item.get("cluster_sources") or [])[:4]],
        }

    digest_input = {
        "date": brief.get("date"),
        "city": brief.get("city"),
        "fact_cards": [compact_card(item) for item in news_pool[:60]],
    }
    payload = json.dumps(digest_input, ensure_ascii=False, indent=2)
    return f"""
你是“松果”的财经早报主编。你的任务不是做投资建议，而是把过去24小时的新闻池整理成一份事实密度高、可读性强、像专业财经早报的中文简报。

只输出 JSON，不输出 Markdown，不在 JSON 外写解释。

输出结构必须是：
{{
  "version": "news-digest-ai-v4",
  "date": "...",
  "city": "...",
  "overview": ["一句话事实摘要", "一句话事实摘要", "一句话事实摘要"],
  "sections": [
    {{
      "title": "宏观经济",
        "items": [
        {{
          "card_id": "对应 fact_cards 的 id",
          "time": "MM-DD HH:mm",
          "thesis": "直接写事实型标题，不要写观点两个字",
          "summary": "只复述该事实卡中已经出现的主体、动作、时间和数字；不写影响判断。"
        }}
      ]
    }}
  ]
}}

栏目只能使用这些标题，并按这个顺序输出：宏观经济、地产动态、股市盘点、行业观察、公司要闻、环球视野、金融数据。

选稿规则：
1. 每条新闻都必须把所用 fact_cards 的 id 写入 card_id；只能使用这张卡的 title、summary、facts 中可直接支持的事实。不得使用外部记忆，不得从常识补全背景。
2. 优先选择有明确时间、主体、数字、公告、财报、政策、订单、产能、供给、价格、利率、汇率、库存、航运、监管动作的事件。
3. 不要写“值得关注”“需要观察”“可能影响市场”“风险”“利好”“利空”“供应中断担忧”等判断或推演。只陈述发生了什么。
4. 不要显示“信息来源”“source”“新闻1/2/3”“观点：”“要点：”。thesis 直接写事实型标题，例如“韩国KOSPI在芯片股带动下上涨2.5%”。
5. summary 只写输入里能支撑的事实。没有输入支撑的金额、政策工具、公司关系、订单规模、产能变化、司法进展，一律不要补。
6. overview 不要自行创作；可以返回空数组，系统会根据最终通过验证的标题生成。
7. 公司新闻优先写财报、公告、诉讼、监管、产品、供应链、资本开支、订单、产能、裁员等硬事实。
8. 产业新闻优先写供需、价格、产能、库存、政策补贴、出口管制、资本开支和关键公司动作。
9. 每张 fact_card 已是一个去重后的事件簇；cluster_size 表示相互印证的报道数。每张卡只能生成一条，不能把同一事件换标题后重复写到其他栏目。
10. 质量优先。fact_cards 少于或等于 30 张时，必须逐条覆盖全部 fact_cards；超过 30 张时选择最重要的 24-30 条。每个栏目 1-12 条；素材不足时允许栏目较少。
11. 每条 summary 控制在 50-140 个中文字符，写成简洁事实正文；输入没有数字就不要杜撰数字。

输入数据：
{payload}
""".strip()


def validate_news_digest(payload: dict) -> None:
    """Validate and normalize the final AI news digest payload."""
    if not isinstance(payload, dict):
        raise ValueError("news digest is not an object")
    payload["version"] = "news-digest-ai-v4"
    if not isinstance(payload.get("overview"), list):
        payload["overview"] = []
    if not isinstance(payload.get("sections"), list) or not payload["sections"]:
        raise ValueError("news digest sections is empty")

    allowed_titles = ["宏观经济", "地产动态", "股市盘点", "行业观察", "公司要闻", "环球视野", "金融数据"]
    banned_prefixes = ("观点：", "观点:", "新闻1", "新闻2", "新闻3", "要点1", "要点2", "信息来源")
    banned_terms = (
        "信息来源",
        "source:",
        "Source:",
        "买入",
        "卖出",
        "推荐",
        "标题层面信息",
        "等待公告",
        "等待原文",
        "尚未披露",
        "暂未披露",
        "具体条款尚未公布",
    )
    normalized_sections = []
    total_items = 0

    for expected_title in allowed_titles:
        for section in payload.get("sections") or []:
            if not isinstance(section, dict):
                continue
            title = clean_digest_text(section.get("title"))
            if title != expected_title:
                continue
            items = []
            for item in section.get("items") or []:
                if not isinstance(item, dict):
                    continue
                thesis = clean_digest_text(item.get("thesis"))
                summary = clean_digest_text(item.get("summary"))
                if not thesis or not summary:
                    continue
                if thesis.startswith(banned_prefixes):
                    raise ValueError(f"news digest item uses weak label: {thesis}")
                if any(term in thesis or term in summary for term in banned_terms):
                    continue
                if not is_editorially_complete_digest_item(thesis, summary):
                    continue
                cleaned_item = {"thesis": thesis, "summary": summary}
                if item.get("card_id"):
                    cleaned_item["card_id"] = clean_digest_text(item.get("card_id"))
                if item.get("time"):
                    cleaned_item["time"] = clean_digest_text(item.get("time"))
                items.append(cleaned_item)
                total_items += 1
            if items:
                normalized_sections.append({"title": expected_title, "items": items[:12]})
            break

    if total_items < 1:
        raise ValueError(f"news digest has too few usable items: {total_items}")
    payload["sections"] = normalized_sections


def main() -> None:
    configure_output()
    args = parse_args()
    settings = get_settings()
    brief = build_brief(
        settings,
        use_mock_weather=args.mock_weather,
        use_mock_market=args.mock_market,
        use_mock_news=args.mock_news,
        use_mock_themes=args.mock_themes,
        use_mock_companies=args.mock_companies,
        use_mock_structured=args.mock_structured,
    )

    if args.show_json:
        print(json.dumps(brief, ensure_ascii=False, indent=2))
        return

    # Preserve the unedited evidence pool beside the finished editorial digest.
    # It is intentionally not rendered on the public page, but makes every
    # daily output auditable and lets later QA inspect why an item was selected.
    brief["news_digest_rules"] = brief.get("news_digest")
    if not args.no_ai:
        ai_news_digest = generate_ai_news_digest(settings, brief)
        if ai_news_digest:
            brief["news_digest"] = ai_news_digest

    rendered = None if args.no_ai else generate_ai_brief(settings, brief)
    if not rendered:
        rendered = render_template_brief(brief)

    print(rendered)

    if args.save:
        demos_dir = Path(__file__).resolve().parents[2] / "demos"
        is_mock_output = uses_mock_data(brief)
        output_dir = demos_dir / "mock" if is_mock_output else demos_dir
        json_path, text_path = save_daily_brief(output_dir, brief, rendered)
        output_paths = save_output_bundle(
            output_dir,
            build_output_bundle(brief, rendered),
            update_latest=True,
        )
        if is_mock_output:
            root_latest = demos_dir / "latest.json"
            write_latest_index(
                root_latest,
                str(brief.get("date", "unknown-date")),
                path_prefix="mock",
                speech_audio_name=output_paths.get("speech_audio").name if output_paths.get("speech_audio") else None,
            )
            output_paths["root_latest"] = root_latest

        print("")
        print("已保存早报：")
        print(f"- 结构化输入：{json_path}")
        print(f"- 早报文本：{text_path}")
        print(f"- 输出包：{output_paths['output_bundle']}")
        print(f"- 屏幕卡片：{output_paths['screen_cards']}")
        print(f"- 语音台词：{output_paths['speech_script']}")
        print(f"- 数字人动作：{output_paths['avatar_timeline']}")
        print(f"- avatar_3d: {output_paths['avatar_3d']}")
        if output_paths.get("latest"):
            print(f"- latest: {output_paths['latest']}")
        if output_paths.get("root_latest"):
            print(f"- root latest: {output_paths['root_latest']}")

if __name__ == "__main__":
    main()
