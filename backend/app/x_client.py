from __future__ import annotations

"""Read-only X discovery feed.

X posts are intentionally returned as low-confidence leads. The editorial
filter excludes them from the visible fact briefing unless another trusted
newsroom, filing, or official notice independently supports the event.
"""

import json
import urllib.error
import urllib.parse
import urllib.request


X_RECENT_SEARCH_URL = "https://api.x.com/2/tweets/search/recent"
DEFAULT_X_LEAD_QUERY = (
    '(earnings OR guidance OR orders OR backlog OR capex OR capacity OR shipment '
    'OR "export controls" OR tariff OR regulator OR semiconductor OR "data center") '
    'lang:en -is:retweet'
)


class XClientError(RuntimeError):
    pass


def fetch_x_lead_snapshot(bearer_token: str, max_records: int = 20) -> dict:
    if not bearer_token:
        raise XClientError("X_BEARER_TOKEN is empty.")

    params = {
        "query": DEFAULT_X_LEAD_QUERY,
        "max_results": str(max(10, min(max_records, 100))),
        "sort_order": "recency",
        "tweet.fields": "created_at,author_id,public_metrics,entities",
        "expansions": "author_id",
        "user.fields": "username,name,verified",
    }
    request = urllib.request.Request(
        f"{X_RECENT_SEARCH_URL}?{urllib.parse.urlencode(params)}",
        headers={
            "Authorization": f"Bearer {bearer_token}",
            "User-Agent": "sunguo-ai-butler/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise XClientError(f"X API HTTP {error.code}: {body[:800]}") from error
    except urllib.error.URLError as error:
        raise XClientError(f"X API network error: {error}") from error
    except json.JSONDecodeError as error:
        raise XClientError("X API returned invalid JSON.") from error

    if payload.get("errors") and not payload.get("data"):
        raise XClientError(str(payload["errors"])[:800])

    users = {
        str(item.get("id")): item
        for item in (payload.get("includes", {}) or {}).get("users", [])
        if item.get("id")
    }
    articles = [
        normalize_x_post(item, users.get(str(item.get("author_id")), {}))
        for item in payload.get("data", []) or []
        if item.get("text")
    ]
    if not articles:
        raise XClientError("X API returned no matching public posts.")

    return {
        "source": "X public posts (lead signals)",
        "categories": [{
            "category": "social_leads",
            "label": "X public lead signals - verification required",
            "url": X_RECENT_SEARCH_URL,
            "articles": articles,
        }],
        "errors": [],
        "note": "X is a discovery-only lead pool and is excluded from visible facts without independent corroboration.",
    }


def normalize_x_post(item: dict, author: dict) -> dict:
    post_id = str(item.get("id") or "")
    username = str(author.get("username") or "")
    author_label = f"@{username}" if username else str(author.get("name") or "X public post")
    return {
        "title": str(item.get("text") or "").replace("\n", " "),
        "url": f"https://x.com/{username}/status/{post_id}" if username and post_id else "",
        "published": str(item.get("created_at") or ""),
        "description": str(item.get("text") or "").replace("\n", " "),
        "source_name": author_label,
        "source_domain": "x.com",
        "source_type": "social",
        "confidence": "lead",
    }
