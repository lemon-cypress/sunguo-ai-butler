from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date


@dataclass(frozen=True)
class OutlookEvent:
    start: str
    end: str
    title: str
    location: str
    importance: str
    preparation: str


@dataclass(frozen=True)
class CalendarWriteProposal:
    action: str
    title: str
    start: str
    end: str
    reason: str
    requires_confirmation: bool = True


def build_mock_outlook_day(day: date) -> dict:
    """Build simulated Outlook data until Microsoft Graph auth is connected."""
    events = [
        OutlookEvent(
            start="09:30",
            end="10:00",
            title="检查今日日程和项目优先级",
            location="本地",
            importance="high",
            preparation="打开松果项目目录，确认今天要完成的最小交付物。",
        ),
        OutlookEvent(
            start="14:00",
            end="15:00",
            title="整理松果早报固定栏目",
            location="本地",
            importance="normal",
            preparation="看一遍昨天保存的早报，标记哪些栏目需要真实数据。",
        ),
        OutlookEvent(
            start="20:30",
            end="20:50",
            title="复盘学习和项目进度",
            location="本地",
            importance="normal",
            preparation="记录今天学到了什么、代码跑通了什么、明天接什么能力。",
        ),
    ]
    proposals = [
        CalendarWriteProposal(
            action="create",
            title="松果项目：Outlook 日历接入设计",
            start="19:30",
            end="20:10",
            reason="下一步要接真实 Outlook，先把读写权限、确认流程和失败回退设计清楚。",
        )
    ]
    return {
        "source": "mock",
        "date": day.isoformat(),
        "events": [asdict(event) for event in events],
        "write_proposals": [asdict(proposal) for proposal in proposals],
        "safety_note": "当前为模拟 Outlook 数据。真实接入后，创建/修改/删除日历事件前仍必须由用户确认。",
    }


def summarize_outlook_tasks(outlook_day: dict) -> list[dict]:
    tasks: list[dict] = []
    for event in outlook_day.get("events", []):
        priority = "高" if event.get("importance") == "high" else "中"
        tasks.append(
            {
                "time": event.get("start", ""),
                "title": event.get("title", ""),
                "priority": priority,
            }
        )
    return tasks

