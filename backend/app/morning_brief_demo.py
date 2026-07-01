from __future__ import annotations

import argparse
import json
import sys

from brief_writer import save_daily_brief, save_output_bundle, write_latest_index
from butler_persona import build_butler_brief
from avatar_3d_builder import build_avatar_3d_package
from company_client import CompanyClientError, build_mock_company_snapshot, fetch_company_snapshot, load_company_watchlist
from config import get_settings
from data_source_registry import (
    SUPPORTED_COMPANY_PROVIDERS,
    SUPPORTED_MARKET_PROVIDERS,
    SUPPORTED_NEWS_PROVIDERS,
    SUPPORTED_THEME_PROVIDERS,
    SUPPORTED_WEATHER_PROVIDERS,
    unsupported_provider_message,
)
from deepseek_client import DeepSeekClientError, DeepSeekQuotaError, create_chat_completion
from financial_reasoning import build_finance_reasoning
from insight_builder import build_insights
from local_memory import load_user_profile, summarize_profile
from local_schedule import load_local_schedule, summarize_local_tasks
from market_client import MarketClientError, build_mock_market_snapshot, fetch_market_snapshot, load_symbols
from marketaux_client import MarketauxClientError, fetch_marketaux_news
from mock_data import build_mock_brief
from news_enrichment import enrich_company_snapshot, enrich_news_snapshot
from news_client import NewsClientError, build_mock_news_snapshot, fetch_news_snapshot, load_news_feeds
from openai_client import OpenAIClientError, OpenAIQuotaError, create_response
from output_builder import build_output_bundle
from outlook_graph import get_today_outlook_or_error
from outlook_mock import build_mock_outlook_day, summarize_outlook_tasks
from pathlib import Path
from quality_builder import build_brief_analysis
from reminder_builder import build_reminder_plan
from theme_client import ThemeClientError, build_mock_theme_snapshot, fetch_theme_snapshot, load_theme_symbols
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成松果早安汇报")
    parser.add_argument("--save", action="store_true", help="保存结构化输入和早报文本到 demos 目录")
    parser.add_argument("--no-ai", action="store_true", help="不调用模型，强制使用模板版早报")
    parser.add_argument("--mock-weather", action="store_true", help="不调用真实天气，使用内置假天气")
    parser.add_argument("--mock-market", action="store_true", help="不调用真实市场数据，使用内置占位市场数据")
    parser.add_argument("--mock-news", action="store_true", help="不调用真实新闻数据，使用内置占位新闻数据")
    parser.add_argument("--mock-themes", action="store_true", help="不调用真实主题/商品数据，使用内置占位主题数据")
    parser.add_argument("--mock-companies", action="store_true", help="不调用真实公司观察池数据，使用内置占位公司数据")
    parser.add_argument("--show-json", action="store_true", help="输出结构化早报输入 JSON")
    return parser.parse_args()


def build_brief(
    settings,
    use_mock_weather: bool,
    use_mock_market: bool,
    use_mock_news: bool,
    use_mock_themes: bool,
    use_mock_companies: bool,
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
    news_data = enrich_news_snapshot(build_news_data(settings, use_mock_news))
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
    brief["user_profile"] = user_profile
    brief["memory_summary"] = summarize_profile(user_profile)
    if schedule.get("source") == "Microsoft Graph":
        brief["outlook_tasks"] = summarize_outlook_tasks(schedule)
    else:
        brief["outlook_tasks"] = summarize_local_tasks(schedule)
    brief["insights"] = build_insights(brief)
    brief["finance_reasoning"] = build_finance_reasoning(brief)
    brief["brief_analysis"] = build_brief_analysis(brief)
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
            if settings.news_provider in {"newsapi", "gdelt"}:
                raise NewsClientError(
                    f"{settings.news_provider} news provider is planned but not wired yet. "
                    "The provider switch is ready; next step is to add the actual API client."
                )
            raise NewsClientError(
                unsupported_provider_message("News", settings.news_provider, SUPPORTED_NEWS_PROVIDERS)
            )
        except MarketauxClientError as error:
            print("Marketaux 新闻获取失败，先使用内置占位新闻数据。")
            print(f"错误信息：{error}")
            print("你可以稍后重试，或先改回 NEWS_PROVIDER=rss。")
            print("")
        except NewsClientError as error:
            print("真实新闻数据获取失败，先使用内置占位新闻数据。")
            print(f"错误信息：{error}")
            print("你可以稍后重试，或临时加 --mock-news 跳过真实新闻数据。")
            print("")
    return build_mock_news_snapshot()


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
    )

    if args.show_json:
        print(json.dumps(brief, ensure_ascii=False, indent=2))
        return

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

