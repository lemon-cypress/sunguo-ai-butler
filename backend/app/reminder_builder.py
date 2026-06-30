from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES_PATH = PROJECT_ROOT / "backend" / "data" / "reminders.json"

DEFAULT_RULES = {
    "version": "reminder-rules-v1",
    "fixed_reminders": [
        {
            "enabled": True,
            "time": "08:30",
            "type": "life",
            "priority": "normal",
            "title": "出门前检查",
            "message": "出门前看一眼钥匙、手机和水杯。今天先让自己轻一点。",
            "voice_style": "gentle",
            "avatar_expression": "gentle",
            "avatar_gesture": "present_left"
        },
        {
            "enabled": True,
            "time": "11:00",
            "type": "health",
            "priority": "normal",
            "title": "补水和伸展",
            "message": "喝几口水，站起来活动 3 分钟。肩颈会感谢你的。",
            "voice_style": "warm",
            "avatar_expression": "smile",
            "avatar_gesture": "small_nod"
        },
        {
            "enabled": True,
            "time": "21:30",
            "type": "life",
            "priority": "normal",
            "title": "晚间收尾",
            "message": "睡前简单整理桌面，给明天留一个轻松的开始。",
            "voice_style": "warm",
            "avatar_expression": "warm",
            "avatar_gesture": "small_nod"
        },
        {
            "enabled": False,
            "time": "08:40",
            "type": "medicine",
            "priority": "high",
            "title": "吃药提醒",
            "message": "到吃药时间了。先喝点温水，按你配置的药品和剂量来。",
            "voice_style": "careful",
            "avatar_expression": "focused",
            "avatar_gesture": "small_nod"
        }
    ],
    "weather_rules": {
        "rain": {
            "enabled": True,
            "time": "08:35",
            "priority": "high",
            "title": "雨具提醒",
            "message": "今天可能有雨，出门前把伞带上，鞋子也尽量选不怕湿的。"
        }
    }
}


def build_reminder_plan(brief: dict, rules_path: Path | None = None) -> dict:
    schedule = brief.get("schedule", {})
    rules = load_reminder_rules(rules_path or DEFAULT_RULES_PATH)
    items = []

    for event in schedule.get("events", [])[:8]:
        reminder = build_schedule_reminder(event)
        if reminder:
            items.append(reminder)

    items.extend(build_weather_reminders(brief, rules))
    items.extend(build_configured_reminders(rules))
    items = sorted(items, key=lambda item: item.get("time", "99:99"))

    medicine_configured = any(item.get("type") == "medicine" for item in items)
    return {
        "version": "reminder-plan-v2",
        "rules_version": rules.get("version", "reminder-rules-v1"),
        "source": f"{schedule.get('source', 'local') or 'local'} + reminders.json",
        "summary": build_summary(items),
        "medicine_configured": medicine_configured,
        "items": assign_ids(items),
    }


def load_reminder_rules(path: Path) -> dict:
    if not path.exists():
        save_reminder_rules(path, DEFAULT_RULES)
        return dict(DEFAULT_RULES)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_reminder_rules(path: Path, rules: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(rules, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def build_schedule_reminder(event: dict) -> dict | None:
    start = event.get("start", "")
    title = event.get("title", "").strip()
    if not start or not title:
        return None

    reminder_time = subtract_minutes(start, 10)
    priority = "high" if event.get("importance") == "high" else "normal"
    preparation = event.get("preparation", "").strip()
    detail = f"准备：{preparation}" if preparation else "先打开相关材料，把下一步想清楚。"

    return {
        "time": reminder_time,
        "type": "schedule",
        "priority": priority,
        "title": f"{title} 即将开始",
        "message": f"小主人，10 分钟后是「{title}」。{detail}",
        "trigger": {"kind": "relative", "minutes_before": 10, "event_time": start},
        "voice": {"style": "encouraging" if priority == "high" else "gentle", "pause_after_ms": 650},
        "avatar": {"expression": "encouraging", "gesture": "checklist"},
    }


def build_weather_reminders(brief: dict, rules: dict) -> list[dict]:
    weather = brief.get("weather", {})
    rain_rule = rules.get("weather_rules", {}).get("rain", {})
    if not rain_rule.get("enabled", True):
        return []
    if not (has_rain(weather.get("condition", "")) or has_rain(weather.get("rain", ""))):
        return []
    return [
        {
            "time": rain_rule.get("time", "08:35"),
            "type": "weather",
            "priority": rain_rule.get("priority", "high"),
            "title": rain_rule.get("title", "雨具提醒"),
            "message": rain_rule.get("message", "今天可能有雨，出门前把伞带上。"),
            "trigger": {"kind": "weather_rule", "condition": "rain"},
            "voice": {"style": "careful", "pause_after_ms": 700},
            "avatar": {"expression": "focused", "gesture": "point_screen"},
        }
    ]


def build_configured_reminders(rules: dict) -> list[dict]:
    reminders = []
    for rule in rules.get("fixed_reminders", []):
        if not rule.get("enabled", True):
            continue
        if not rule.get("time") or not rule.get("title"):
            continue
        reminders.append(
            {
                "time": rule.get("time", ""),
                "type": rule.get("type", "life"),
                "priority": rule.get("priority", "normal"),
                "title": rule.get("title", "提醒"),
                "message": rule.get("message", "这是一条提醒。"),
                "trigger": {"kind": "fixed_time"},
                "voice": {"style": rule.get("voice_style", "warm"), "pause_after_ms": int(rule.get("pause_after_ms", 600))},
                "avatar": {
                    "expression": rule.get("avatar_expression", "warm"),
                    "gesture": rule.get("avatar_gesture", "small_nod"),
                },
            }
        )
    return reminders


def build_summary(items: list[dict]) -> str:
    high_count = sum(1 for item in items if item.get("priority") == "high")
    if not items:
        return "今天暂时没有需要主动提醒的事项。"
    if high_count:
        return f"今天我会安排 {len(items)} 条提醒，其中 {high_count} 条是高优先级。"
    return f"今天我会安排 {len(items)} 条轻量提醒，帮你照看节奏。"


def assign_ids(items: list[dict]) -> list[dict]:
    result = []
    for index, item in enumerate(items, start=1):
        enriched = dict(item)
        enriched["id"] = f"reminder-{index:02d}"
        result.append(enriched)
    return result


def subtract_minutes(time_text: str, minutes: int) -> str:
    try:
        parsed = datetime.strptime(time_text, "%H:%M")
    except ValueError:
        return time_text
    return (parsed - timedelta(minutes=minutes)).strftime("%H:%M")


def has_rain(text: str) -> bool:
    return any(word in text for word in ["雨", "雷", "雪", "冰雹", "阵雨"])