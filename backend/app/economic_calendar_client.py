from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta


NASDAQ_ECONOMIC_CALENDAR_URL = "https://api.nasdaq.com/api/calendar/economicevents"


class EconomicCalendarError(RuntimeError):
    pass


def fetch_economic_calendar(
    start_day: date | None = None,
    days: int = 2,
    timeout_seconds: int = 20,
) -> dict:
    start_day = start_day or date.today()
    days = max(1, min(days, 7))
    events: list[dict] = []
    errors: list[str] = []

    for offset in range(days):
        target_day = start_day + timedelta(days=offset)
        try:
            payload = request_nasdaq_calendar(target_day, timeout_seconds)
            events.extend(normalize_nasdaq_rows(payload, target_day))
        except EconomicCalendarError as error:
            errors.append(str(error))

    if not events and errors:
        raise EconomicCalendarError("; ".join(errors))

    return {
        "source": "Nasdaq economic calendar",
        "provider": "nasdaq",
        "events": events,
        "errors": errors,
        "note": "Economic calendar events are timing clues for macro data and policy catalysts. They should be combined with actual data releases before final judgment.",
    }


def request_nasdaq_calendar(target_day: date, timeout_seconds: int) -> dict:
    params = urllib.parse.urlencode({"date": target_day.isoformat()})
    url = f"{NASDAQ_ECONOMIC_CALENDAR_URL}?{params}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
            "Origin": "https://www.nasdaq.com",
            "Referer": "https://www.nasdaq.com/",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise EconomicCalendarError(f"Nasdaq calendar HTTP {error.code}: {body[:500]}") from error
    except urllib.error.URLError as error:
        raise EconomicCalendarError(f"Nasdaq calendar network error: {error}") from error
    except json.JSONDecodeError as error:
        raise EconomicCalendarError("Nasdaq calendar returned invalid JSON.") from error


def normalize_nasdaq_rows(payload: dict, target_day: date) -> list[dict]:
    data = payload.get("data") or {}
    rows = data.get("rows") or []
    events = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        event_name = clean_text(row.get("eventName", ""))
        if not event_name:
            continue
        time_text = clean_text(row.get("gmt", ""))
        events.append(
            {
                "date": target_day.isoformat(),
                "time": time_text,
                "country": clean_text(row.get("country", "")),
                "event": event_name,
                "actual": clean_text(row.get("actual", "")),
                "consensus": clean_text(row.get("consensus", "")),
                "previous": clean_text(row.get("previous", "")),
                "description": clean_text(row.get("description", "")),
                "importance": infer_importance(event_name),
                "category": infer_category(event_name),
                "time_sort": build_time_sort(target_day, time_text),
            }
        )
    return events


def build_time_sort(target_day: date, time_text: str) -> str:
    match = re.search(r"(\d{1,2}):(\d{2})", time_text or "")
    if not match:
        return target_day.isoformat()
    hour = int(match.group(1))
    minute = int(match.group(2))
    return datetime(target_day.year, target_day.month, target_day.day, hour, minute).isoformat()


def infer_importance(event_name: str) -> str:
    text = event_name.lower()
    high_keywords = [
        "cpi",
        "ppi",
        "inflation",
        "payroll",
        "unemployment",
        "pmi",
        "gdp",
        "fed",
        "interest rate",
        "rate decision",
        "retail sales",
        "industrial production",
    ]
    medium_keywords = ["confidence", "sentiment", "trade", "budget", "housing", "claims", "inventory"]
    if any(keyword in text for keyword in high_keywords):
        return "high"
    if any(keyword in text for keyword in medium_keywords):
        return "medium"
    return "normal"


def infer_category(event_name: str) -> str:
    text = event_name.lower()
    if any(keyword in text for keyword in ["cpi", "ppi", "inflation", "price"]):
        return "inflation"
    if any(keyword in text for keyword in ["pmi", "industrial", "manufacturing", "services"]):
        return "activity"
    if any(keyword in text for keyword in ["payroll", "unemployment", "employment", "claims"]):
        return "jobs"
    if any(keyword in text for keyword in ["fed", "rate", "central bank"]):
        return "central_bank"
    if any(keyword in text for keyword in ["gdp"]):
        return "growth"
    if any(keyword in text for keyword in ["retail", "consumer"]):
        return "consumption"
    return "macro"


def clean_text(value) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def build_mock_economic_calendar() -> dict:
    return {
        "source": "mock",
        "provider": "mock",
        "events": [],
        "errors": [],
        "note": "Economic calendar is empty because the real provider was skipped or unavailable.",
    }
