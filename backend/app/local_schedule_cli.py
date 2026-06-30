from __future__ import annotations

import argparse
import json
from pathlib import Path

from config import get_settings


def load_payload(path: Path) -> dict:
    if not path.exists():
        return {"source": "local", "events": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["source"] = "local"
    payload["events"] = sorted(payload.get("events", []), key=lambda item: item.get("start", ""))
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def list_events(path: Path) -> None:
    payload = load_payload(path)
    events = payload.get("events", [])
    if not events:
        print("今天还没有本地日程。")
        return

    for index, event in enumerate(events, start=1):
        start = event.get("start", "")
        end = event.get("end", "")
        title = event.get("title", "")
        importance = event.get("importance", "normal")
        location = event.get("location", "本地")
        preparation = event.get("preparation", "")
        print(f"{index}. {start}-{end} [{importance}] {title} @ {location}")
        if preparation:
            print(f"   准备：{preparation}")


def add_event(path: Path, args: argparse.Namespace) -> None:
    payload = load_payload(path)
    payload.setdefault("events", []).append(
        {
            "start": args.start,
            "end": args.end,
            "title": args.title,
            "location": args.location,
            "importance": args.importance,
            "preparation": args.preparation,
        }
    )
    save_payload(path, payload)
    print(f"已添加：{args.start}-{args.end} {args.title}")


def delete_event(path: Path, index: int) -> None:
    payload = load_payload(path)
    events = payload.get("events", [])
    if index < 1 or index > len(events):
        raise SystemExit(f"没有第 {index} 条日程，请先运行 list 查看编号。")

    removed = events.pop(index - 1)
    save_payload(path, payload)
    print(f"已删除：{removed.get('start', '')}-{removed.get('end', '')} {removed.get('title', '')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="管理松果本地日程。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="查看本地日程")

    add_parser = subparsers.add_parser("add", help="添加一条本地日程")
    add_parser.add_argument("--start", required=True, help="开始时间，例如 09:30")
    add_parser.add_argument("--end", required=True, help="结束时间，例如 10:00")
    add_parser.add_argument("--title", required=True, help="日程标题")
    add_parser.add_argument("--location", default="本地", help="地点，默认本地")
    add_parser.add_argument(
        "--importance",
        default="normal",
        choices=["low", "normal", "high"],
        help="重要性：low/normal/high",
    )
    add_parser.add_argument("--preparation", default="", help="松果需要提醒你提前准备什么")

    delete_parser = subparsers.add_parser("delete", help="按编号删除一条本地日程")
    delete_parser.add_argument("index", type=int, help="日程编号，可先运行 list 查看")

    return parser


def main() -> None:
    settings = get_settings()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list":
        list_events(settings.local_schedule_path)
    elif args.command == "add":
        add_event(settings.local_schedule_path, args)
    elif args.command == "delete":
        delete_event(settings.local_schedule_path, args.index)


if __name__ == "__main__":
    main()
