from __future__ import annotations

import re


def build_output_bundle(brief: dict, rendered_text: str) -> dict:
    return {
        "version": "output-v1",
        "project": "松果",
        "date": brief.get("date", ""),
        "city": brief.get("city", ""),
        "brief_text": rendered_text,
        "brief_analysis": brief.get("brief_analysis", {}),
        "memory_summary": brief.get("memory_summary", {}),
        "finance_reasoning": brief.get("finance_reasoning", {}),
        "reminder_plan": brief.get("reminder_plan", {}),
        "butler_brief": brief.get("butler_brief", {}),
        "screen_cards": build_screen_cards(brief),
        "speech_script": build_speech_script(brief, rendered_text),
        "avatar_timeline": build_avatar_timeline(brief),
        "avatar_3d": brief.get("avatar_3d", {}),
        "source_summary": build_source_summary(brief),
    }


def build_screen_cards(brief: dict) -> list[dict]:
    weather = brief.get("weather", {})
    insights = brief.get("insights", {})
    schedule = brief.get("schedule", {})
    analysis = brief.get("brief_analysis", {})
    memory_summary = brief.get("memory_summary", {})
    finance_reasoning = brief.get("finance_reasoning", {})
    reminder_plan = brief.get("reminder_plan", {})
    butler = brief.get("butler_brief", {})

    cards = build_butler_cards(butler) + build_reminder_cards(reminder_plan) + build_quality_cards(analysis) + build_memory_cards(memory_summary) + build_finance_cards(finance_reasoning) + build_filing_cards(finance_reasoning) + [
        {
            "id": "weather",
            "type": "weather",
            "title": "天气和穿衣",
            "priority": "high",
            "summary": f"{brief.get('city', '')} {weather.get('condition', '')}，气温 {weather.get('temperature', '')}",
            "details": [weather.get("rain", ""), weather.get("outfit", "")],
            "source": weather.get("source", "unknown"),
        },
        {
            "id": "top-priorities",
            "type": "priorities",
            "title": "今天先关注",
            "priority": "high",
            "summary": "松果为你挑出的 3 个优先事项",
            "details": insights.get("priorities", [])[:3],
            "source": "insight_builder",
        },
        {
            "id": "market",
            "type": "market",
            "title": "市场和宏观",
            "priority": "high",
            "summary": insights.get("market", {}).get("tone", "市场方向待确认"),
            "details": insights.get("market", {}).get("watch_points", [])[:4],
            "source": brief.get("market_data", {}).get("source", "unknown"),
        },
        {
            "id": "themes",
            "type": "themes",
            "title": "价格和行业线索",
            "priority": "normal",
            "summary": "能源、金属、半导体和航运等主题变化",
            "details": insights.get("themes", {}).get("opportunity_watch", [])[:5],
            "source": brief.get("theme_data", {}).get("source", "unknown"),
        },
        {
            "id": "companies",
            "type": "companies",
            "title": "公司观察池",
            "priority": "normal",
            "summary": "重点公司价格变化和新闻线索",
            "details": insights.get("companies", {}).get("watch_points", [])[:6],
            "source": brief.get("company_data", {}).get("source", "unknown"),
        },
        {
            "id": "schedule",
            "type": "schedule",
            "title": "今天待办",
            "priority": "high",
            "summary": schedule.get("safety_note", "当前使用本地日程。"),
            "details": format_schedule_items(schedule.get("events", [])),
            "source": schedule.get("source", "local"),
        },
        {
            "id": "life",
            "type": "life",
            "title": "生活提醒",
            "priority": "normal",
            "summary": "照顾好今天的精力和节奏",
            "details": brief.get("life_reminders", [])[:5],
            "source": "local_rules",
        },
    ]
    return [card for card in cards if card.get("details") or card.get("summary")]


def build_butler_cards(butler: dict) -> list[dict]:
    if not butler:
        return []
    return [
        {
            "id": "butler-voice",
            "type": "butler",
            "title": "松果管家语气",
            "priority": "high",
            "summary": butler.get("opening", "早安，我是松果。"),
            "details": [butler.get("care_note", ""), butler.get("agenda_note", ""), butler.get("closing", "")],
            "source": butler.get("version", "butler-persona-v1"),
        }
    ]

def build_reminder_cards(reminder_plan: dict) -> list[dict]:
    if not reminder_plan:
        return []

    details = []
    for item in reminder_plan.get("items", [])[:8]:
        details.append(f"{item.get('time', '')}｜{item.get('title', '')}｜{item.get('message', '')}")

    return [
        {
            "id": "reminder-plan",
            "type": "reminders",
            "title": "主动提醒",
            "priority": "high",
            "summary": reminder_plan.get("summary", "今天我会帮你照看节奏。"),
            "details": details,
            "source": reminder_plan.get("version", "reminder-plan-v1"),
        }
    ]


def build_memory_cards(memory_summary: dict) -> list[dict]:
    if not memory_summary:
        return []

    details = []
    if memory_summary.get("regions"):
        details.append(f"关注国家/地区：{'、'.join(memory_summary['regions'])}")
    if memory_summary.get("industries"):
        details.append(f"关注行业：{'、'.join(memory_summary['industries'])}")
    if memory_summary.get("companies"):
        details.append(f"关注公司：{'、'.join(memory_summary['companies'])}")
    if memory_summary.get("current_priority"):
        details.append(f"当前项目重点：{memory_summary['current_priority']}")

    return [
        {
            "id": "memory",
            "type": "memory",
            "title": "松果记住了",
            "priority": "normal",
            "summary": f"我会按 {memory_summary.get('owner_name', '小主人')} 的关注偏好整理早报。",
            "details": details,
            "source": "user_profile",
        }
    ]


def build_finance_cards(finance_reasoning: dict) -> list[dict]:
    if not finance_reasoning:
        return []

    details = []
    for section in ["market", "themes", "companies"]:
        for item in finance_reasoning.get(section, [])[:2]:
            details.append(
                f"{item.get('title', '财经线索')}｜事实：{item.get('fact', '')}｜可能原因：{item.get('possible_reason', '')}｜后续：{'；'.join(item.get('follow_up', [])[:2])}"
            )

    if not details:
        details = finance_reasoning.get("rules", [])[:3]

    return [
        {
            "id": "finance-reasoning",
            "type": "finance-reasoning",
            "title": "财经解读框架",
            "priority": "high",
            "summary": finance_reasoning.get("summary", "按事实、原因、影响和核验整理财经线索。"),
            "details": details[:6],
            "source": "financial_reasoning",
        }
    ]

def build_filing_cards(finance_reasoning: dict) -> list[dict]:
    companies = finance_reasoning.get("companies", []) if finance_reasoning else []
    details = []
    for item in companies:
        filings = item.get("official_filings", [])
        if not filings:
            continue
        filing = filings[0]
        details.append(
            f"{item.get('title', '公司线索')}｜{filing.get('form', '')}｜提交日 {filing.get('filing_date', '')}｜{format_filing_summary(filing)}｜{filing.get('url', '')}"
        )
    if not details:
        return []
    return [
        {
            "id": "filing-evidence",
            "type": "filing-evidence",
            "title": "官方披露证据",
            "priority": "high",
            "summary": "最近 SEC/监管披露入口，用来回到原文核验公司线索。",
            "details": details[:6],
            "source": "SEC submissions",
        }
    ]

def format_filing_summary(filing: dict) -> str:
    summary = filing.get("document_summary", {}) or {}
    items = summary.get("items", [])
    if items:
        return "；".join(items[:3])
    if summary.get("title"):
        return summary["title"]
    return filing.get("use_for", "回到原文核验")

def build_quality_cards(analysis: dict) -> list[dict]:
    if not analysis:
        return []

    cards = [
        {
            "id": "quality-overview",
            "type": "analysis",
            "title": "松果解读",
            "priority": "high",
            "summary": analysis.get("today_overview", ""),
            "details": analysis.get("quality_rules", [])[:3],
            "source": analysis.get("version", "brief-analysis-v1"),
        }
    ]

    for index, story_item in enumerate(analysis.get("top_stories", [])[:3], start=1):
        details = []
        if story_item.get("why_it_matters"):
            details.append(f"为什么重要：{story_item['why_it_matters']}")
        if story_item.get("impact"):
            details.append(f"影响对象：{'、'.join(story_item['impact'])}")
        if story_item.get("evidence"):
            details.append(f"证据：{'；'.join(story_item['evidence'][:2])}")
        if story_item.get("follow_up"):
            details.append(f"后续核验：{'；'.join(story_item['follow_up'][:2])}")
        details.append(f"可信度：{story_item.get('confidence', '待确认')}")

        cards.append(
            {
                "id": f"top-story-{index}",
                "type": "top-story",
                "title": f"{index}. {story_item.get('title', '重要事项')}",
                "priority": "high",
                "summary": story_item.get("why_it_matters", ""),
                "details": details,
                "source": story_item.get("source", "unknown"),
            }
        )

    return cards


def build_speech_script(brief: dict, rendered_text: str) -> list[dict]:
    butler_script = brief.get("butler_brief", {}).get("speech_script", [])
    if butler_script:
        return butler_script
    paragraphs = split_for_speech(rendered_text)
    if not paragraphs:
        return []

    script = []
    for index, paragraph in enumerate(paragraphs[:12], start=1):
        script.append(
            {
                "id": f"speech-{index:02d}",
                "text": paragraph,
                "voice": {
                    "style": choose_voice_style(paragraph),
                    "speed": "normal",
                    "pause_after_ms": 500 if index < len(paragraphs) else 900,
                },
            }
        )
    return script


def build_avatar_timeline(brief: dict) -> list[dict]:
    butler = brief.get("butler_brief", {})
    reminder_plan = brief.get("reminder_plan", {})
    reminder_caption = reminder_plan.get("summary", "??????????????")
    speech_script = butler.get("speech_script", [])
    if speech_script:
        return build_speech_avatar_timeline(speech_script, reminder_caption, brief)
    return [
        {
            "id": "hello",
            "section": "opening",
            "expression": "smile",
            "gesture": "wave",
            "camera": "medium",
            "mouth": "open",
            "speaking": True,
            "lip_sync": "preview",
            "caption": butler.get("opening", f"?????? {brief.get('date', '')}"),
        },
        {
            "id": "care",
            "section": "care",
            "expression": "gentle",
            "gesture": "present_left",
            "camera": "medium",
            "mouth": "soft_open",
            "speaking": True,
            "lip_sync": "preview",
            "caption": butler.get("care_note", "???????????????????"),
        },
        {
            "id": "agenda",
            "section": "agenda",
            "expression": "encouraging",
            "gesture": "checklist",
            "camera": "medium",
            "mouth": "open",
            "speaking": True,
            "lip_sync": "preview",
            "caption": butler.get("agenda_note", "???????????????????"),
        },
        {
            "id": "reminders",
            "section": "reminders",
            "expression": "encouraging",
            "gesture": "checklist",
            "camera": "medium",
            "mouth": "soft_open",
            "speaking": True,
            "lip_sync": "preview",
            "caption": reminder_caption,
        },
        {
            "id": "finance",
            "section": "finance",
            "expression": "focused",
            "gesture": "point_screen",
            "camera": "medium_close",
            "mouth": "open",
            "speaking": True,
            "lip_sync": "preview",
            "caption": butler.get("finance_note", "?????????????????????"),
        },
        {
            "id": "closing",
            "section": "closing",
            "expression": "warm",
            "gesture": "small_nod",
            "camera": "medium_close",
            "mouth": "closed",
            "speaking": False,
            "lip_sync": "rest",
            "caption": butler.get("closing", "?????????????????"),
        },
    ]


def build_speech_avatar_timeline(speech_script: list[dict], reminder_caption: str, brief: dict) -> list[dict]:
    timeline = []
    for index, item in enumerate(speech_script, start=1):
        style = str((item.get("voice") or {}).get("style", "clear"))
        section = str(item.get("section", f"speech-{index}"))
        caption = str(item.get("text", ""))
        expression, gesture, camera, mouth = style_to_avatar_state(style, section)
        timeline.append(
            {
                "id": f"speech-{index:02d}",
                "section": section,
                "expression": expression,
                "gesture": gesture,
                "camera": camera,
                "mouth": mouth,
                "speaking": True,
                "lip_sync": "enabled",
                "caption": caption,
                "subtitle": caption[:60],
                "duration_ms": estimate_avatar_duration(item),
                "audio_pause_ms": int((item.get("voice") or {}).get("pause_after_ms", 0) or 0),
            }
        )
    if timeline:
        timeline.append(
            {
                "id": "wrap",
                "section": "closing",
                "expression": "warm",
                "gesture": "small_nod",
                "camera": "medium_close",
                "mouth": "closed",
                "speaking": False,
                "lip_sync": "rest",
                "caption": reminder_caption or brief.get("butler_brief", {}).get("closing", "?????????????????"),
                "subtitle": reminder_caption or "",
            }
        )
    return timeline


def style_to_avatar_state(style: str, section: str) -> tuple[str, str, str, str]:
    if style == "careful":
        return "focused", "small_nod", "medium_close", "soft_open"
    if style == "gentle":
        return "gentle", "present_left", "medium", "soft_open"
    if style == "encouraging":
        return "encouraging", "checklist", "medium", "open"
    if section in {"opening", "closing"}:
        return "smile", "wave", "medium", "open"
    return "warm", "small_nod", "medium", "open"


def estimate_avatar_duration(item: dict) -> int:
    text = str(item.get("text", ""))
    pause = int((item.get("voice") or {}).get("pause_after_ms", 0) or 0)
    speaking = min(5200, max(1400, len(text) * 48))
    return speaking + pause


def build_source_summary(brief: dict) -> dict:
    return {
        "weather": brief.get("weather", {}).get("source", "unknown"),
        "market": brief.get("market_data", {}).get("source", "unknown"),
        "news": brief.get("news_data", {}).get("source", "unknown"),
        "themes": brief.get("theme_data", {}).get("source", "unknown"),
        "companies": brief.get("company_data", {}).get("source", "unknown"),
        "schedule": brief.get("schedule", {}).get("source", "unknown"),
        "memory": "user_profile",
        "reliability_note": "财经、新闻和公司观察池先作为线索输出，重要结论需要回到原始来源核验。",
    }


def split_for_speech(text: str) -> list[str]:
    cleaned = re.sub(r"\*\*", "", text)
    raw_parts = re.split(r"\n\s*\n+", cleaned)
    parts = []
    for part in raw_parts:
        sentence = " ".join(line.strip("- ").strip() for line in part.splitlines() if line.strip())
        if len(sentence) > 260:
            sentence = sentence[:257] + "..."
        if sentence:
            parts.append(sentence)
    return parts


def choose_voice_style(text: str) -> str:
    if any(word in text for word in ["风险", "核验", "不构成投资建议", "下跌"]):
        return "careful"
    if any(word in text for word in ["早安", "早上好", "今天"]):
        return "warm"
    if any(word in text for word in ["待办", "下一步", "项目"]):
        return "encouraging"
    return "clear"


def format_schedule_items(events: list[dict]) -> list[str]:
    items = []
    for event in events[:8]:
        start = event.get("start", "")
        end = event.get("end", "")
        title = event.get("title", "")
        preparation = event.get("preparation", "")
        if preparation:
            items.append(f"{start}-{end} {title}。准备：{preparation}")
        else:
            items.append(f"{start}-{end} {title}")
    return items












