from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = PROJECT_ROOT / "backend" / "data" / "reminders.json"


def load_rules() -> dict:
    if not RULES_PATH.exists():
        return {"version": "reminder-rules-v1", "fixed_reminders": [], "weather_rules": {}}
    return json.loads(RULES_PATH.read_text(encoding="utf-8-sig"))


def save_rules(rules: dict) -> None:
    RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    RULES_PATH.write_text(json.dumps(rules, ensure_ascii=True, indent=2) + "\n", encoding="ascii")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="\u7ba1\u7406\u677e\u679c\u672c\u5730\u63d0\u9192")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="\u5217\u51fa\u6240\u6709\u56fa\u5b9a\u63d0\u9192")

    add = sub.add_parser("add", help="\u65b0\u589e\u56fa\u5b9a\u63d0\u9192")
    add.add_argument("--time", required=True, help="\u65f6\u95f4\uff0c\u4f8b\u5982 08:40")
    add.add_argument("--title", required=True, help="\u63d0\u9192\u6807\u9898")
    add.add_argument("--message", required=True, help="\u63d0\u9192\u8bdd\u672f")
    add.add_argument("--type", default="life", help="\u7c7b\u578b\uff0c\u4f8b\u5982 life\u3001health\u3001medicine")
    add.add_argument("--priority", default="normal", choices=["normal", "high"], help="\u4f18\u5148\u7ea7")

    toggle = sub.add_parser("enable", help="\u542f\u7528\u67d0\u6761\u63d0\u9192")
    toggle.add_argument("title", help="\u63d0\u9192\u6807\u9898\uff0c\u652f\u6301\u90e8\u5206\u5339\u914d")

    toggle = sub.add_parser("disable", help="\u5173\u95ed\u67d0\u6761\u63d0\u9192")
    toggle.add_argument("title", help="\u63d0\u9192\u6807\u9898\uff0c\u652f\u6301\u90e8\u5206\u5339\u914d")

    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    rules = load_rules()
    reminders = rules.setdefault("fixed_reminders", [])

    if args.command == "list":
        for index, item in enumerate(reminders, start=1):
            enabled = "\u542f\u7528" if item.get("enabled", True) else "\u5173\u95ed"
            print(f"{index}. {enabled}\uff5c{item.get('time', '')}\uff5c{item.get('type', 'life')}\uff5c{item.get('title', '')}\uff5c{item.get('message', '')}")
        return

    if args.command == "add":
        reminders.append(
            {
                "enabled": True,
                "time": args.time,
                "type": args.type,
                "priority": args.priority,
                "title": args.title,
                "message": args.message,
                "voice_style": "careful" if args.type == "medicine" else "warm",
                "avatar_expression": "focused" if args.priority == "high" else "warm",
                "avatar_gesture": "small_nod",
            }
        )
        save_rules(rules)
        print(f"\u5df2\u65b0\u589e\u63d0\u9192\uff1a{args.time}\uff5c{args.title}")
        return

    enabled = args.command == "enable"
    matched = [item for item in reminders if args.title in item.get("title", "")]
    if not matched:
        raise SystemExit(f"\u6ca1\u6709\u627e\u5230\u6807\u9898\u5305\u542b\u300c{args.title}\u300d\u7684\u63d0\u9192\u3002")
    for item in matched:
        item["enabled"] = enabled
    save_rules(rules)
    state = "\u542f\u7528" if enabled else "\u5173\u95ed"
    print(f"\u5df2{state} {len(matched)} \u6761\u63d0\u9192\u3002")


if __name__ == "__main__":
    main()
