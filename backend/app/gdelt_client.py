from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone


GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
DEFAULT_QUERY = "(earnings OR revenue OR guidance OR capex OR order OR central bank OR inflation OR tariff OR sanctions OR export controls OR semiconductor OR data center OR shipping OR oil OR supply chain)"

# A single broad GDELT query tends to over-return loosely related headlines.
# Separate editorial beats make the raw pool wider while preserving enough
# topical intent for the later fact-card filter.
EDITORIAL_QUERIES = [
    ("macro", "(inflation OR central bank OR interest rate OR tariff OR trade OR GDP OR PMI OR fiscal policy)"),
    ("company", "(earnings OR revenue OR profit OR guidance OR order OR backlog OR capex OR merger OR acquisition OR SEC filing)"),
    ("industry", "(semiconductor OR AI OR data center OR supply chain OR energy OR oil OR shipping OR capacity OR inventory)"),
    ("global", "(sanction OR export controls OR geopolitics OR Iran OR Ukraine OR Israel OR military OR Hormuz OR trade policy)"),
]


class GdeltClientError(RuntimeError):
    pass


def fetch_gdelt_news(
    max_records: int = 20,
    query: str | None = None,
    published_after_hours: int = 24,
    timeout_seconds: int = 10,
) -> dict:
    # The public GDELT endpoint rate-limits shared IP addresses aggressively.
    # Use one strong editorial query by default; callers can still request a
    # focused custom query. This is more reliable than losing later groups to
    # a 429 during the daily generation window.
    query_groups = [("custom", query)] if query else [("editorial", DEFAULT_QUERY)]
    per_group_records = max(6, min(20, max_records // max(1, len(query_groups))))
    categories = []
    errors = []
    seen_titles: set[str] = set()
    last_request_at = 0.0

    for category, search_query in query_groups:
        # GDELT's public endpoint asks callers to stay under one request per
        # five seconds. Without this pause, later editorial beats disappear
        # behind a 429 and the pool becomes accidentally one-dimensional.
        wait_seconds = 5.2 - (time.monotonic() - last_request_at)
        if last_request_at and wait_seconds > 0:
            time.sleep(wait_seconds)
        try:
            articles = fetch_gdelt_query(
                query=search_query,
                max_records=per_group_records,
                published_after_hours=published_after_hours,
                timeout_seconds=timeout_seconds,
            )
            last_request_at = time.monotonic()
        except GdeltClientError as error:
            errors.append(f"{category}: {error}")
            last_request_at = time.monotonic()
            continue
        unique_articles = []
        for article in articles:
            key = " ".join(str(article.get("title", "")).lower().split())[:180]
            if not key or key in seen_titles:
                continue
            seen_titles.add(key)
            unique_articles.append(article)
        if unique_articles:
            categories.append(
                {
                    "category": category,
                    "label": f"GDELT {category}",
                    "url": GDELT_DOC_URL,
                    "articles": unique_articles,
                }
            )

    if not categories:
        raise GdeltClientError("; ".join(errors) or "GDELT returned no articles.")

    return {
        "source": "GDELT",
        "categories": categories,
        "errors": errors,
        "note": "GDELT is split into macro, company, industry and global raw pools before local fact-card filtering.",
        "provider_meta": {
            "query_groups": [name for name, _ in query_groups],
            "published_after_hours": published_after_hours,
        },
    }


def fetch_gdelt_query(
    query: str,
    max_records: int,
    published_after_hours: int,
    timeout_seconds: int = 10,
) -> list[dict]:
    start = datetime.now(timezone.utc) - timedelta(hours=max(1, published_after_hours))
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": str(max(1, min(max_records, 250))),
        "sort": "hybridrel",
        "startdatetime": start.strftime("%Y%m%d%H%M%S"),
    }
    url = f"{GDELT_DOC_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "sunguo-ai-butler/0.1"})
    try:
        payload = request_gdelt_json(request, timeout_seconds=timeout_seconds)
    except urllib.error.HTTPError as error:
        if error.code == 429:
            # GDELT is an optional discovery source. Retrying after a 429 can
            # stall the daily refresh while the RSS and API pool is already ready.
            body = error.read().decode("utf-8", errors="replace")
            raise GdeltClientError(f"GDELT HTTP 429: {body[:800]}") from error
        else:
            body = error.read().decode("utf-8", errors="replace")
            raise GdeltClientError(f"GDELT HTTP {error.code}: {body[:800]}") from error
    except TimeoutError as error:
        raise GdeltClientError(f"GDELT timeout: {error}") from error
    except OSError as error:
        raise GdeltClientError(f"GDELT network error: {error}") from error
    except urllib.error.URLError as error:
        raise GdeltClientError(f"GDELT network error: {error}") from error
    except json.JSONDecodeError as error:
        raise GdeltClientError("GDELT returned invalid JSON.") from error

    raw_items = payload.get("articles", []) or []
    articles = [normalize_gdelt_article(item) for item in raw_items if item.get("title")]
    if not articles:
        raise GdeltClientError("GDELT returned no articles.")
    return articles


def request_gdelt_json(request: urllib.request.Request, timeout_seconds: int = 10) -> dict:
    with urllib.request.urlopen(request, timeout=max(3, timeout_seconds)) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def normalize_gdelt_article(item: dict) -> dict:
    return {
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "published": item.get("seendate", ""),
        "description": item.get("snippet", "") or item.get("title", ""),
        "source_name": item.get("sourceCommonName", "") or item.get("domain", ""),
        "source_domain": item.get("domain", ""),
        "language": item.get("language", ""),
        "country": item.get("sourceCountry", ""),
    }
