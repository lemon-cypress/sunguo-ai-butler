from __future__ import annotations

import json
from pathlib import Path


DEFAULT_PROFILE = {
    "owner_name": "小主人",
    "city": "北京-朝阳",
    "project_name": "松果",
    "persona": {
        "name": "松果",
        "style": "温柔、阳光、聪明、可靠",
        "avatar": "18岁左右的女生形象",
    },
    "focus": {
        "regions": ["中国", "日本", "韩国", "美国", "欧洲"],
        "markets": ["主要指数", "股市板块", "宏观政策", "利率", "汇率"],
        "industries": ["AI算力", "半导体", "机器人", "创新药", "新能源", "消费电子", "能源", "航运"],
        "companies": ["英伟达", "AMD", "台积电", "ASML", "微软"],
        "news_topics": ["经济", "政治", "军事", "社会新闻", "科技应用"],
    },
    "output_preferences": {
        "tone": "先讲结论，再讲证据，语气温柔自然",
        "morning_brief_order": ["松果解读", "三件重要事", "天气穿衣", "市场宏观", "行业公司", "政治社会", "今日待办", "生活提醒"],
        "risk_style": "财经内容只做线索整理，不直接给买卖建议",
        "detail_level": "中等详细，重要信息解释为什么值得关注",
    },
    "life_reminders": [
        "刷牙",
        "喝水",
        "出门前检查钥匙和手机",
        "久坐时拉伸",
        "晚上简单整理桌面",
    ],
    "project_memory": {
        "current_stage": "早报原型、追问能力和输出层",
        "current_priority": "提升早报质量、追问能力、本地记忆、语音和数字人输出",
        "paused_items": ["Outlook 公司日历接入，等待管理员授权"],
    },
}


def load_user_profile(path: Path) -> dict:
    if not path.exists():
        save_user_profile(path, DEFAULT_PROFILE)
        return json.loads(json.dumps(DEFAULT_PROFILE, ensure_ascii=False))
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_user_profile(path: Path, profile: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def summarize_profile(profile: dict) -> dict:
    focus = profile.get("focus", {})
    return {
        "owner_name": profile.get("owner_name", "小主人"),
        "city": profile.get("city", ""),
        "project_name": profile.get("project_name", "松果"),
        "regions": focus.get("regions", []),
        "industries": focus.get("industries", []),
        "companies": focus.get("companies", []),
        "life_reminders": profile.get("life_reminders", []),
        "current_priority": profile.get("project_memory", {}).get("current_priority", ""),
        "tone": profile.get("output_preferences", {}).get("tone", ""),
    }


def add_list_item(profile: dict, section: str, item: str) -> dict:
    if section in {"regions", "industries", "companies", "markets", "news_topics"}:
        focus = profile.setdefault("focus", {})
        values = focus.setdefault(section, [])
    elif section == "life_reminders":
        values = profile.setdefault("life_reminders", [])
    else:
        raise ValueError(f"Unsupported memory section: {section}")

    if item and item not in values:
        values.append(item)
    return profile


def remove_list_item(profile: dict, section: str, item: str) -> dict:
    if section in {"regions", "industries", "companies", "markets", "news_topics"}:
        values = profile.setdefault("focus", {}).setdefault(section, [])
    elif section == "life_reminders":
        values = profile.setdefault("life_reminders", [])
    else:
        raise ValueError(f"Unsupported memory section: {section}")

    kept_values = [value for value in values if value != item]
    if section in {"regions", "industries", "companies", "markets", "news_topics"}:
        profile["focus"][section] = kept_values
    else:
        profile[section] = kept_values
    return profile
