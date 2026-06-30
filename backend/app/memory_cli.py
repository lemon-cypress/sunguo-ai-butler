from __future__ import annotations

import argparse
import json
import sys

from config import get_settings
from local_memory import add_list_item, load_user_profile, remove_list_item, save_user_profile, summarize_profile


SECTIONS = ["regions", "industries", "companies", "markets", "news_topics", "life_reminders"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="管理松果本地记忆")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("show", help="查看当前记忆摘要")

    add_parser = subparsers.add_parser("add", help="添加一个关注项")
    add_parser.add_argument("section", choices=SECTIONS)
    add_parser.add_argument("item")

    remove_parser = subparsers.add_parser("remove", help="删除一个关注项")
    remove_parser.add_argument("section", choices=SECTIONS)
    remove_parser.add_argument("item")

    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    settings = get_settings()
    profile = load_user_profile(settings.user_profile_path)

    if args.command == "show":
        print(json.dumps(summarize_profile(profile), ensure_ascii=False, indent=2))
        return

    if args.command == "add":
        profile = add_list_item(profile, args.section, args.item)
        save_user_profile(settings.user_profile_path, profile)
        print(f"已记住：{args.section} -> {args.item}")
        return

    if args.command == "remove":
        profile = remove_list_item(profile, args.section, args.item)
        save_user_profile(settings.user_profile_path, profile)
        print(f"已删除：{args.section} -> {args.item}")


if __name__ == "__main__":
    main()
