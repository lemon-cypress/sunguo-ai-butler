from __future__ import annotations

import json
import http.client
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


FINNHUB_GENERAL_NEWS_URL = "https://finnhub.io/api/v1/news"


class FinnhubNewsClientError(RuntimeError):
    pass


def fetch_finnhub_news(api_key: str, max_records: int = 20) -> dict:
    if not api_key:
        raise FinnhubNewsClientError("FINNHUB_API_KEY is empty.")
    params = {"category": "general", "token": api_key}
    request = urllib.request.Request(
        f"{FINNHUB_GENERAL_NEWS_URL}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": "sunguo-ai-butler/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise FinnhubNewsClientError(f"Finnhub HTTP {error.code}: {body[:800]}") from error
    except (urllib.error.URLError, http.client.HTTPException, OSError) as error:
        raise FinnhubNewsClientError(f"Finnhub network error: {error}") from error
    except json.JSONDecodeError as error:
        raise FinnhubNewsClientError("Finnhub returned invalid JSON.") from error

    if not isinstance(payload, list):
        raise FinnhubNewsClientError(str(payload)[:800])
    articles = [normalize_finnhub_article(item) for item in payload[: max(1, min(max_records, 50))] if item.get("headline")]
    if not articles:
        raise FinnhubNewsClientError("Finnhub returned no articles.")
    return {
        "source": "Finnhub",
        "categories": [{
            "category": "finance",
            "label": "Finnhub general news",
            "url": FINNHUB_GENERAL_NEWS_URL,
            "articles": articles,
        }],
        "errors": [],
        "note": "Finnhub provides additional U.S. market and company-event leads for the fact-card pool.",
    }


def normalize_finnhub_article(item: dict) -> dict:
    published = item.get("datetime")
    if isinstance(published, (int, float)):
        published_text = datetime.fromtimestamp(published, tz=timezone.utc).isoformat()
    else:
        published_text = ""
    return {
        "title": str(item.get("headline") or ""),
        "url": str(item.get("url") or ""),
        "published": published_text,
        "description": str(item.get("summary") or ""),
        "source_name": str(item.get("source") or "Finnhub"),
        "source_domain": str(item.get("source") or ""),
    }
