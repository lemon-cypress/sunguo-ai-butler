from __future__ import annotations


def build_butler_brief(brief: dict) -> dict:
    memory = brief.get("memory_summary", {})
    owner = memory.get("owner_name", "小主人")
    persona = (brief.get("user_profile", {}).get("persona", {}) or {})
    name = persona.get("name", "松果")

    opening = build_opening(brief, owner, name)
    care = build_care_note(brief)
    agenda = build_agenda_note(brief)
    finance = build_finance_note(brief)
    closing = build_closing(brief, owner)

    return {
        "version": "butler-persona-v2",
        "name": name,
        "owner": owner,
        "style": persona.get("style", "温柔、阳光、聪明、可靠"),
        "opening": opening,
        "care_note": care,
        "agenda_note": agenda,
        "finance_note": finance,
        "closing": closing,
        "speech_script": build_butler_speech(opening, care, agenda, finance, closing),
    }


def build_opening(brief: dict, owner: str, name: str) -> str:
    weather = brief.get("weather", {})
    city = brief.get("city", "北京-朝阳")
    condition = weather.get("condition", "天气待确认")
    temperature = weather.get("temperature", "")
    mood = weather_mood(condition)
    return f"???{owner}???{name}?{city}??{condition}???{temperature}?{mood}??????????????????"


def build_care_note(brief: dict) -> str:
    weather = brief.get("weather", {})
    condition = weather.get("condition", "")
    outfit = weather.get("outfit", "")
    reminders = brief.get("life_reminders", [])[:2]
    if has_rain(condition) or has_rain(weather.get("rain", "")):
        lead = "今天外面不太省心，出门前把伞、钥匙和手机都看一眼。"
    elif is_hot(weather.get("temperature", "")):
        lead = "今天温度偏高，衣服尽量轻一点，水也记得带上。"
    else:
        lead = "今天节奏可以稳一点，不用一开始就把自己绷太紧。"
    tail = f"穿衣上，{outfit}" if outfit else "穿衣我会继续帮你留意天气变化。"
    life = "；".join(reminders)
    return f"{lead}{tail}" + (f" 另外，{life}。" if life else "")


def build_agenda_note(brief: dict) -> str:
    tasks = brief.get("outlook_tasks", [])[:4]
    if not tasks:
        return "今天暂时没有明确日程。我们先给松果项目留一个安静的推进时间，把最小版本继续做顺。"
    high = [task for task in tasks if task.get("priority") == "高"]
    first = high[0] if high else tasks[0]
    later = [task for task in tasks if task is not first][:2]
    later_text = "；".join(f"{task.get('time', '')} {task.get('title', '')}" for task in later)
    if later_text:
        return f"今天先抓住 {first.get('time', '')} 的「{first.get('title', '')}」。后面我会再提醒你：{later_text}。"
    return f"今天先抓住 {first.get('time', '')} 的「{first.get('title', '')}」。先做这一件，就已经是在往前走。"


def build_finance_note(brief: dict) -> str:
    analysis = brief.get("brief_analysis", {})
    stories = analysis.get("top_stories", [])
    if not stories:
        return "财经和新闻我先保持观察，只把事实、可能原因和核验入口分开，不替你做仓促判断。"
    first = stories[0].get("title", "市场线索")
    second = stories[1].get("title", "公司和行业线索") if len(stories) > 1 else "后续核验点"
    return f"财经部分我会谨慎一点。今天先看两个重点：{first}；以及{second}。这些先当线索，我会把核验入口放在旁边。"


def build_closing(brief: dict, owner: str) -> str:
    priority = brief.get("memory_summary", {}).get("current_priority", "把今天最重要的一步做扎实")
    return f"{owner}，今天不用一下子把所有事做完。我们先把最重要的一步推进好：{priority}。我会在旁边帮你看着节奏，慢慢来。"


def build_butler_speech(opening: str, care: str, agenda: str, finance: str, closing: str) -> list[dict]:
    sections = [
        ("opening", opening, "warm", 750),
        ("care", care, "gentle", 700),
        ("agenda", agenda, "encouraging", 650),
        ("finance", finance, "careful", 800),
        ("closing", closing, "warm", 950),
    ]
    return [
        {
            "id": f"butler-{index:02d}",
            "section": section,
            "text": text,
            "voice": {"style": style, "speed": "normal", "pause_after_ms": pause},
        }
        for index, (section, text, style, pause) in enumerate(sections, start=1)
        if text
    ]


def weather_mood(condition: str) -> str:
    if has_rain(condition):
        return "外面可能会有点湿乱，今天我会多提醒你几句。"
    if "晴" in condition:
        return "天气看起来还不错，适合把节奏打开一点。"
    return "天气没有完全确定，我们稳稳安排就好。"


def has_rain(text: str) -> bool:
    return any(word in text for word in ["雨", "雷", "雪", "冰雹", "阵雨"])


def is_hot(temperature: str) -> bool:
    digits = [int(part) for part in temperature.replace("°C", "").replace("℃", "").replace("-", " ").split() if part.isdigit()]
    return bool(digits and max(digits) >= 32)
