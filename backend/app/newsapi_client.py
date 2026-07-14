from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone


NEWSAPI_EVERYTHING_URL = "https://newsapi.org/v2/everything"
DEFAULT_QUERY = '"central bank" OR inflation OR tariff OR earnings OR guidance OR "data center" OR semiconductor OR oil OR shipping'


class NewsApiClientError(RuntimeError):
    pass


def fetch_newsapi_news(api_key: str, max_records: int = 20, published_after_hours: int = 30) -> dict:
    if not api_key:
        raise NewsApiClientError("NEWSAPI_API_KEY is empty.")

    published_after = datetime.now(timezone.utc) - timedelta(hours=max(1, published_after_hours))
    params = {
        "q": DEFAULT_QUERY,
        "from": published_after.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": str(max(1, min(max_records, 100))),
        "apiKey": api_key,
    }
    request = urllib.request.Request(
        f"{NEWSAPI_EVERYTHING_URL}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": "sunguo-ai-butler/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise NewsApiClientError(f"NewsAPI HTTP {error.code}: {body[:800]}") from error
    except urllib.error.URLError as error:
        raise NewsApiClientError(f"NewsAPI network error: {error}") from error
    except json.JSONDecodeError as error:
        raise NewsApiClientError("NewsAPI returned invalid JSON.") from error

    if payload.get("status") != "ok":
        raise NewsApiClientError(str(payload.get("message") or payload))

    articles = [normalize_newsapi_article(item) for item in payload.get("articles", []) if item.get("title")]
    if not articles:
        raise NewsApiClientError("NewsAPI returned no articles.")
    return {
        "source": "NewsAPI",
        "categories": [{
            "category": "editorial_news",
            "label": "NewsAPI 24h",
            "url": NEWSAPI_EVERYTHING_URL,
            "articles": articles,
        }],
        "errors": [],
        "note": "NewsAPI provides a second paid/global editorial news pool for fact-card filtering.",
    }


def normalize_newsapi_article(item: dict) -> dict:
    source = item.get("source") or {}
    return {
        "title": str(item.get("title") or ""),
        "url": str(item.get("url") or ""),
        "published": str(item.get("publishedAt") or ""),
        "description": str(item.get("description") or ""),
        "source_name": str(source.get("name") or ""),
        "source_domain": str(source.get("id") or ""),
    }
