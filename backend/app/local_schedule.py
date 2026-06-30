from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class LocalEvent:
    start: str
    end: str
    title: str
    location: str
    importance: str
    preparation: str


DEFAULT_EVENTS = [
    LocalEvent(
        start="09:30",
        end="10:00",
        title="检查今日日程和项目优先级",
        location="本地",
        importance="high",
        preparation="打开松果项目目录，确认今天要完成的最小交付物。",
    ),
    LocalEvent(
        start="14:00",
        end="15:00",
        title="整理松果早报固定栏目",
        location="本地",
        importance="normal",
        preparation="看一遍昨天保存的早报，标记哪些栏目需要真实数据。",
    ),
    LocalEvent(
        start="16:00",
        end="16:30",
        title="整理松果下一步任务",
        location="本地",
        importance="high",
        preparation="把今天遇到的问题写成 3 条。",
    ),
    LocalEvent(
        start="20:30",
        end="20:50",
        title="复盘学习和项目进度",
        location="本地",
        importance="normal",
        preparation="记录今天学到了什么、代码跑通了什么、明天接什么能力。",
    ),
]


def load_local_schedule(path: Path, day: date) -> dict:
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        events = payload.get("events", [])
    else:
        events = [asdict(event) for event in DEFAULT_EVENTS]

    return {
        "source": "local",
        "date": day.isoformat(),
        "events": events,
        "write_proposals": [],
        "safety_note": "当前使用本地日程文件，不依赖公司 Outlook 授权。",
    }


def summarize_local_tasks(schedule: dict) -> list[dict]:
    tasks: list[dict] = []
    for event in schedule.get("events", []):
        priority = "高" if event.get("importance") == "high" else "中"
        tasks.append(
            {
                "time": event.get("start", ""),
                "title": event.get("title", ""),
                "priority": priority,
            }
        )
    return tasks



