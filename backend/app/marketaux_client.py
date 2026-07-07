from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone


MARKETAUX_NEWS_URL = "https://api.marketaux.com/v1/news/all"


class MarketauxClientError(RuntimeError):
    pass


def fetch_marketaux_news(
    api_key: str,
    max_records: int = 10,
    language: str = "en",
    countries: str = "cn,us,jp,kr,gb,de,fr",
    published_after_hours: int = 24,
) -> dict:
    if not api_key:
        raise MarketauxClientError("MARKETAUX_API_KEY is empty.")

    published_after = (
        datetime.now(timezone.utc) - timedelta(hours=max(1, published_after_hours))
    ).strftime("%Y-%m-%d")

    params = {
        "api_token": api_key,
        "language": language,
        "countries": countries,
        "filter_entities": "true",
        "limit": str(max(1, min(max_records, 50))),
        "published_after": published_after,
        "sort": "published_desc",
        "group_similar": "true",
    }
    payload = fetch_marketaux_payload(params)

    if "error" in payload:
        raise MarketauxClientError(str(payload["error"]))

    raw_items = payload.get("data", [])
    articles = [normalize_marketaux_article(item) for item in raw_items if item.get("title")]
    if not articles:
        raise MarketauxClientError("Marketaux returned no articles.")

    return {
        "source": "Marketaux",
        "categories": [
            {
                "category": "finance",
                "label": "全球财经快讯",
                "url": MARKETAUX_NEWS_URL,
                "articles": articles,
            }
        ],
        "errors": [],
        "note": "Marketaux 提供全球财经新闻与实体识别，适合作为松果新闻层的正式数据源。",
        "provider_meta": {
            "language": language,
            "countries": countries,
            "published_after": published_after,
        },
    }


def fetch_marketaux_payload(params: dict[str, str]) -> dict:
    try:
        return request_marketaux(params)
    except MarketauxClientError as error:
        lower = str(error).lower()
        if "published_after" in lower and "malformed_parameters" in lower:
            fallback_params = dict(params)
            fallback_params.pop("published_after", None)
            return request_marketaux(fallback_params)
        raise


def request_marketaux(params: dict[str, str]) -> dict:
    url = f"{MARKETAUX_NEWS_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "sunguo-ai-butler/0.1"})

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise MarketauxClientError(f"Marketaux HTTP {error.code}: {body[:1000]}") from error
    except urllib.error.URLError as error:
        raise MarketauxClientError(f"Marketaux network error: {error}") from error
    except json.JSONDecodeError as error:
        raise MarketauxClientError("Marketaux returned invalid JSON.") from error


def normalize_marketaux_article(item: dict) -> dict:
    entities = item.get("entities") or []
    symbols = []
    entity_names = []
    for entity in entities:
        if isinstance(entity, dict):
            if entity.get("symbol"):
                symbols.append(entity.get("symbol", ""))
            if entity.get("name"):
                entity_names.append(entity.get("name", ""))
        elif isinstance(entity, str) and entity.strip():
            entity_names.append(entity.strip())

    source_name = ""
    source_domain = ""
    source = item.get("source")
    if isinstance(source, dict):
        source_name = str(source.get("name", "") or "")
        source_domain = str(source.get("domain", "") or "")
    elif isinstance(source, str):
        source_name = source

    return {
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "published": item.get("published_at", ""),
        "description": item.get("description", "") or item.get("snippet", ""),
        "source_name": source_name,
        "source_domain": source_domain,
        "symbols": symbols[:8],
        "entities": entity_names[:8],
        "sentiment": item.get("sentiment"),
    }
