from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


Answer = dict[str, Any]


KEYWORDS = {
    "summary": ["总结", "总览", "最重要", "重点", "今天看什么", "三件"],
    "sources": ["来源", "数据源", "可靠吗", "可信", "可靠", "证据充分"],
    "schedule": ["待办", "日程", "今天做什么", "项目", "任务"],
    "reminders": ["提醒", "叫我", "到点", "吃药", "主动提醒", "几点提醒"],
    "memory": ["记住", "偏好", "关注", "我关心", "你知道我"],
    "finance": ["财经", "市场", "股市", "指数", "行业", "板块", "公司", "上涨", "下跌", "原因", "影响", "机会", "入口", "链接", "官方", "去哪", "哪里", "披露", "SEC", "8-K", "10-Q", "10-K", "20-F", "6-K"],
    "evidence": ["证据", "依据", "从哪", "来源"],
    "impact": ["影响", "行业", "对象", "谁", "利好", "利空"],
    "followup": ["下一步", "核验", "看什么", "关注", "怎么确认"],
    "reason": ["原因", "为什么", "背后"],
    "filing": ["披露", "SEC", "8-K", "10-Q", "10-K", "20-F", "6-K", "公告", "财报"],
}


COMPANY_ALIASES = {
    "微软": ["微软", "MSFT", "Microsoft"],
    "英伟达": ["英伟达", "NVDA", "NVIDIA"],
    "AMD": ["AMD"],
    "台积电": ["台积电", "TSM", "TSMC"],
    "ASML": ["ASML"],
    "谷歌": ["Alphabet", "GOOGL", "谷歌", "Google"],
}


SUGGESTIONS = [
    "今天最重要的三件事是什么？",
    "第一件事为什么重要？",
    "有哪些证据？",
    "下一步需要核验什么？",
    "数据可靠吗？",
    "公司核验入口在哪里？",
    "今天松果项目该做什么？",
]


def load_latest_bundle(demos_dir: Path) -> dict:
    latest_path = demos_dir / "latest.json"
    if not latest_path.exists():
        raise FileNotFoundError(f"latest.json not found: {latest_path}")
    latest = json.loads(latest_path.read_text(encoding="utf-8-sig"))
    bundle_path = demos_dir / latest["bundle_path"]
    if not bundle_path.exists():
        raise FileNotFoundError(f"output bundle not found: {bundle_path}")
    return json.loads(bundle_path.read_text(encoding="utf-8-sig"))


def answer_question(bundle: dict, question: str) -> Answer:
    question = normalize_question(question)
    analysis = extract_analysis(bundle)
    stories = analysis.get("top_stories", [])

    if not question:
        return build_answer(
            "你可以继续问我：为什么重要、证据是什么、影响谁、下一步看什么、今天会提醒我什么。",
            [],
            "local",
            suggestions=SUGGESTIONS,
        )

    if has_keyword(question, KEYWORDS["reminders"]):
        return build_reminder_answer(bundle)
    if has_keyword(question, KEYWORDS["summary"]):
        return build_summary_answer(analysis)
    if has_keyword(question, KEYWORDS["finance"]):
        return build_finance_answer(bundle, question)
    if has_keyword(question, KEYWORDS["sources"]):
        return build_sources_answer(bundle)
    if has_keyword(question, KEYWORDS["schedule"]):
        return build_schedule_answer(bundle)
    if has_keyword(question, KEYWORDS["memory"]):
        return build_memory_answer(bundle)

    story = find_story(stories, question)
    if story:
        return build_story_answer(story, question)

    return build_answer(
        "我先基于今天早报回答。现在最值得追问的是三件重要事、数据来源和下一步核验点。",
        [story.get("title", "") for story in stories[:3]],
        "brief_analysis",
        suggestions=SUGGESTIONS,
    )


def normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", (question or "").strip())


def extract_analysis(bundle: dict) -> dict:
    if bundle.get("brief_analysis"):
        return bundle["brief_analysis"]
    stories = []
    for card in bundle.get("screen_cards", []):
        if card.get("type") == "top-story":
            stories.append({
                "title": card.get("title", ""),
                "why_it_matters": card.get("summary", ""),
                "evidence": card.get("details", []),
                "impact": [],
                "confidence": "待确认",
                "source": card.get("source", "unknown"),
                "follow_up": [],
            })
    return {
        "today_overview": first_line(bundle.get("brief_text", "")),
        "top_stories": stories,
    }


def first_line(value: str) -> str:
    return next((line.strip() for line in value.splitlines() if line.strip()), "")


def find_story(stories: list[dict], question: str) -> dict | None:
    ordinal_map = [
        (["第一", "第1", "1"], 0),
        (["第二", "第2", "2"], 1),
        (["第三", "第3", "3"], 2),
    ]
    for keys, index in ordinal_map:
        if any(key in question for key in keys) and index < len(stories):
            return stories[index]

    normalized = question.lower()
    best = None
    best_score = 0
    for story in stories:
        title = str(story.get("title", ""))
        tokens = split_tokens(title)
        score = sum(1 for token in tokens if token and token.lower() in normalized)
        if score > best_score:
            best = story
            best_score = score
    return best or (stories[0] if stories else None)


def split_tokens(value: str) -> list[str]:
    clean = re.sub(r"[，。；：、|｜/\\()（）\[\]【】]+", " ", value)
    return [token for token in clean.split() if len(token) >= 2]


def build_summary_answer(analysis: dict) -> Answer:
    stories = analysis.get("top_stories", [])[:3]
    details = [f"{index}. {story.get('title', '重要事项')}" for index, story in enumerate(stories, start=1)]
    return build_answer(
        analysis.get("today_overview") or "今天的重点已经整理在三件重要事里。",
        details,
        "brief_analysis",
        suggestions=["第一件事为什么重要？", "有哪些证据？", "下一步需要核验什么？"],
    )


def build_sources_answer(bundle: dict) -> Answer:
    summary = bundle.get("source_summary", {})
    details = [
        f"天气：{summary.get('weather', 'unknown')}",
        f"市场：{summary.get('market', 'unknown')}",
        f"新闻：{summary.get('news', 'unknown')}",
        f"主题：{summary.get('themes', 'unknown')}",
        f"公司：{summary.get('companies', 'unknown')}",
        f"日程：{summary.get('schedule', 'unknown')}",
    ]
    return build_answer(
        summary.get("reliability_note") or "重要结论需要回到原始来源核验，我会把事实、推测和待确认分开说。",
        details,
        "source_summary",
        suggestions=["下一步需要核验什么？", "有哪些证据？"],
    )


def build_schedule_answer(bundle: dict) -> Answer:
    card = next((card for card in bundle.get("screen_cards", []) if card.get("id") == "schedule"), None)
    if not card:
        return build_answer("我暂时没有读到今天的日程卡片。", [], "schedule")
    return build_answer(card.get("summary", "今天待办已整理。"), card.get("details", []), card.get("source", "schedule"))


def build_reminder_answer(bundle: dict) -> Answer:
    plan = bundle.get("reminder_plan", {})
    if not plan:
        return build_answer("我还没有生成今天的主动提醒计划。", [], "reminder_plan")
    details = [f"{item.get('time', '')}｜{item.get('title', '')}｜{item.get('message', '')}" for item in plan.get("items", [])[:12]]
    lead = plan.get("summary", "今天的提醒已经整理好了。")
    if not plan.get("medicine_configured"):
        lead += " 目前还没有启用固定吃药提醒。"
    return build_answer(lead, details, plan.get("version", "reminder_plan"), suggestions=["几点提醒我？", "今天松果项目该做什么？"])


def build_memory_answer(bundle: dict) -> Answer:
    memory = bundle.get("memory_summary", {})
    if not memory:
        return build_answer("我暂时没有读到本地记忆。", [], "user_profile")
    details = []
    if memory.get("regions"):
        details.append(f"关注国家/地区：{'、'.join(memory['regions'])}")
    if memory.get("industries"):
        details.append(f"关注行业：{'、'.join(memory['industries'])}")
    if memory.get("companies"):
        details.append(f"关注公司：{'、'.join(memory['companies'])}")
    if memory.get("life_reminders"):
        details.append(f"生活提醒：{'、'.join(memory['life_reminders'])}")
    if memory.get("current_priority"):
        details.append(f"当前项目重点：{memory['current_priority']}")
    return build_answer("我会按这些本地记忆来组织早报和追问回答。", details, "user_profile")


def build_story_answer(story: dict, question: str) -> Answer:
    if has_keyword(question, KEYWORDS["evidence"]):
        lead = "这条判断目前主要基于这些证据："
        details = story.get("evidence", [])
        suggestions = ["这件事影响谁？", "下一步需要核验什么？"]
    elif has_keyword(question, KEYWORDS["impact"]):
        lead = "它主要影响这些对象："
        details = story.get("impact", [])
        suggestions = ["有哪些证据？", "下一步看什么？"]
    elif has_keyword(question, KEYWORDS["followup"]):
        lead = "下一步建议这样核验："
        details = story.get("follow_up", [])
        suggestions = ["有哪些证据？", "数据可靠吗？"]
    else:
        lead = story.get("why_it_matters") or "这条值得关注，因为它会影响今天的信息判断顺序。"
        details = story.get("evidence", [])[:2] + story.get("follow_up", [])[:2]
        suggestions = ["有哪些证据？", "影响哪些行业？", "下一步需要核验什么？"]
    if story.get("confidence"):
        details = list(details) + [f"可信度：{story.get('confidence')}｜来源：{story.get('source', 'unknown')}"]
    return build_answer(lead, details, story.get("source", "brief_analysis"), suggestions=suggestions)


def build_finance_answer(bundle: dict, question: str) -> Answer:
    finance = bundle.get("finance_reasoning", {})
    if not finance:
        return build_answer("我还没有读到财经解读框架，先看早报里的三件重要事和来源信息。", [], "finance_reasoning")

    items = select_finance_items(finance, question)
    if not items:
        return build_answer(finance.get("summary", "今天财经线索不足，先保持观察。"), finance.get("rules", [])[:3], "finance_reasoning")

    if has_keyword(question, KEYWORDS["reason"]):
        details = [f"{item.get('title', '财经线索')}：{item.get('possible_reason') or '原因待核验'}" for item in items[:5]]
        return build_answer("我先按“可能原因”回答，但这些都需要继续核验。", details, "finance_reasoning", suggestions=["有哪些证据？", "下一步需要核验什么？"])

    if has_keyword(question, KEYWORDS["impact"]):
        details = [f"{item.get('title', '财经线索')}：{item.get('impact') or '影响待确认'}" for item in items[:5]]
        return build_answer("这些线索可能影响的对象主要是：", details, "finance_reasoning")

    if has_keyword(question, KEYWORDS["filing"]):
        details = []
        for item in items[:5]:
            filing = (item.get("official_filings", []) or [None])[0]
            details.append(format_filing_answer(item, filing) if filing else f"{item.get('title', '财经线索')}：暂未抓到最近 SEC 文件，先看公司 IR 和 SEC 页面。")
        return build_answer("我查到的最近官方披露是：", details, "finance_reasoning")

    if has_keyword(question, KEYWORDS["followup"]):
        details = [f"{item.get('title', '财经线索')}：{'；'.join(item.get('follow_up', [])[:2])}" for item in items[:5]]
        return build_answer("下一步建议这样核验：", details, "finance_reasoning")

    details = [f"{item.get('title', '财经线索')}｜事实：{item.get('fact') or '待确认'}｜可能原因：{item.get('possible_reason') or '待核验'}" for item in items[:5]]
    return build_answer(finance.get("summary", "我已经按事实、原因、影响、核验整理了财经线索。"), details, "finance_reasoning", suggestions=["半导体为什么下跌？", "公司核验入口在哪里？", "微软最近披露是什么？"])


def select_finance_items(finance: dict, question: str) -> list[dict]:
    if has_keyword(question, ["公司", "英伟达", "微软", "AMD", "台积电", "ASML", "公告", "财报", "披露", "SEC"]):
        return filter_company_items(finance.get("companies", []), question)
    if has_keyword(question, ["行业", "板块", "价格", "商品", "黄金", "铜", "原油", "半导体ETF", "半导体", "主题"]):
        return finance.get("themes", [])
    if has_keyword(question, ["市场", "股市", "指数", "大盘", "中国", "美国", "日本", "韩国", "欧洲"]):
        return finance.get("market", [])
    return finance.get("market", []) + finance.get("themes", []) + finance.get("companies", [])


def filter_company_items(items: list[dict], question: str) -> list[dict]:
    tokens = {token.lower() for key, group in COMPANY_ALIASES.items() if key in question for token in group}
    if not tokens:
        return items
    filtered = []
    for item in items:
        text = " ".join([str(item.get("title", "")), str(item.get("fact", "")), str(item.get("impact", ""))]).lower()
        if any(token in text for token in tokens):
            filtered.append(item)
    return filtered or items


def format_filing_answer(item: dict, filing: dict | None) -> str:
    if not filing:
        return f"{item.get('title', '财经线索')}：暂未抓到最近官方披露。"
    summary = filing.get("document_summary", {}) or {}
    items = "；".join(summary.get("items", [])[:3])
    title = summary.get("title", "")
    extra = f"，摘要：{items}" if items else (f"，标题：{title}" if title else "")
    return f"{item.get('title', '财经线索')}：{filing.get('form', '披露')}，提交日 {filing.get('filing_date', '')}{extra}，链接：{filing.get('url', '')}"


def has_keyword(question: str, keywords: list[str]) -> bool:
    lower = question.lower()
    return any(keyword.lower() in lower for keyword in keywords)


def build_answer(answer: str, details: list[str], source: str, suggestions: list[str] | None = None) -> Answer:
    return {
        "answer": answer,
        "details": [str(item) for item in details if item],
        "source": source,
        "suggested_questions": suggestions or [],
    }
