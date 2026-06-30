from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from ms_graph_auth import MicrosoftAuthError, get_access_token


GRAPH_BASE = "https://graph.microsoft.com/v1.0"
MICROSOFT_OUTLOOK_TIMEZONE = "China Standard Time"


class OutlookGraphError(RuntimeError):
    pass


def fetch_calendar_view(access_token: str, start_datetime: datetime, end_datetime: datetime) -> dict:
    params = urllib.parse.urlencode(
        {
            "startDateTime": start_datetime.isoformat(),
            "endDateTime": end_datetime.isoformat(),
            "$orderby": "start/dateTime",
            "$select": "id,subject,start,end,location,importance,isAllDay,webLink",
        }
    )
    url = f"{GRAPH_BASE}/me/calendar/calendarView?{params}"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Prefer": f'outlook.timezone="{MICROSOFT_OUTLOOK_TIMEZONE}"',
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise OutlookGraphError(f"Microsoft Graph HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise OutlookGraphError(f"Microsoft Graph network error: {error}") from error


def fetch_today_outlook(settings) -> dict:
    access_token = get_access_token(
        settings.microsoft_client_id,
        settings.microsoft_tenant,
        settings.microsoft_scopes,
        settings.microsoft_token_path,
    )
    tz = ZoneInfo(settings.timezone)
    today = date.today()
    start_datetime = datetime.combine(today, time.min, tzinfo=tz)
    end_datetime = datetime.combine(today, time.max, tzinfo=tz)
    payload = fetch_calendar_view(access_token, start_datetime, end_datetime)
    return normalize_calendar_view(payload, today)


def normalize_calendar_view(payload: dict, day: date) -> dict:
    events = []
    for item in payload.get("value", []):
        events.append(
            {
                "id": item.get("id", ""),
                "start": extract_time(item.get("start", {})),
                "end": extract_time(item.get("end", {})),
                "title": item.get("subject", "(无标题)"),
                "location": (item.get("location") or {}).get("displayName", ""),
                "importance": item.get("importance", "normal"),
                "preparation": "真实 Outlook 日程，松果后续会学习如何为它生成准备建议。",
                "web_link": item.get("webLink", ""),
            }
        )

    return {
        "source": "Microsoft Graph",
        "date": day.isoformat(),
        "events": events,
        "write_proposals": [],
        "safety_note": "当前只读取 Outlook 日历，不写入。写入功能必须由用户确认后执行。",
    }


def extract_time(value: dict) -> str:
    raw = value.get("dateTime")
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%H:%M")
    except ValueError:
        return raw


def get_today_outlook_or_error(settings) -> tuple[dict | None, str | None]:
    try:
        return fetch_today_outlook(settings), None
    except (MicrosoftAuthError, OutlookGraphError) as error:
        return None, str(error)

