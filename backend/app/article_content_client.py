from __future__ import annotations

"""Small, dependency-free extractor for publicly readable news articles.

It is deliberately conservative: only a short allowlist of recognised media
and official domains is requested, no login/paywall is bypassed, and failures
leave the original RSS/API description untouched.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import time
from urllib.parse import urlparse
import re
import urllib.error
import urllib.request


ALLOWED_DOMAINS = (
    "reuters.com", "apnews.com", "bbc.co.uk", "bbc.com", "cnbc.com", "ft.com", "wsj.com",
    "nytimes.com", "scmp.com", "theverge.com", "lemonde.fr", "caixin.com", "yicai.com",
    "21jingji.com", "stcn.com", "cs.com.cn", "cnstock.com", "cls.cn", "jiemian.com",
    "thepaper.cn", "eeo.com.cn", "xinhuanet.com", "chinanews.com", "people.com.cn",
    "gov.cn", "pbc.gov.cn", "mof.gov.cn", "stats.gov.cn", "customs.gov.cn", "sec.gov",
    "federalreserve.gov", "ecb.europa.eu",
)

# The refresh endpoint is also invoked by the browser.  Caching public pages
# keeps a second F5 from issuing the same publisher requests again while still
# allowing the next scheduled/news-cycle refresh to obtain newer reporting.
CACHE_DIR = Path(__file__).resolve().parents[2] / "demos" / ".article_content_cache"
CACHE_TTL_SECONDS = 6 * 60 * 60


class _PublicArticleParser(HTMLParser):
    """Extract paragraph-like public text without executing or interpreting HTML."""

    TEXT_TAGS = {"p", "h1", "h2", "li"}
    SKIP_TAGS = {"script", "style", "svg", "noscript", "iframe", "nav", "footer", "form"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._active_tag = ""
        self._parts: list[str] = []
        self.description = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        if self._skip_depth:
            return
        if tag == "meta":
            values = {str(key).lower(): str(value or "") for key, value in attrs}
            marker = values.get("name", "").lower() or values.get("property", "").lower()
            if marker in {"description", "og:description", "twitter:description"} and not self.description:
                self.description = values.get("content", "")
        elif tag in self.TEXT_TAGS:
            self._active_tag = tag

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        if tag == self._active_tag:
            self._active_tag = ""

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and self._active_tag:
            cleaned = normalize_text(data)
            if cleaned:
                self._parts.append(cleaned)

    def text(self) -> str:
        # Repeated site chrome becomes obvious when adjacent paragraphs are
        # identical; keep unique, substantial paragraphs only.
        unique: list[str] = []
        seen: set[str] = set()
        for part in self._parts:
            key = re.sub(r"\W+", "", part).lower()
            if len(part) < 24 or key in seen:
                continue
            seen.add(key)
            unique.append(part)
            if len(" ".join(unique)) >= 3600:
                break
        return normalize_text(" ".join(unique))[:3600]


def normalize_text(value: str) -> str:
    return " ".join(unescape(value or "").split())


def public_article_allowed(url: str) -> bool:
    parsed = urlparse(url or "")
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not host:
        return False
    if host in {"localhost", "127.0.0.1", "0.0.0.0"} or host.endswith(".local"):
        return False
    return any(host == domain or host.endswith(f".{domain}") for domain in ALLOWED_DOMAINS)


def fetch_public_article_text(url: str, timeout_seconds: int = 7) -> dict:
    if not public_article_allowed(url):
        return {}
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; SunguoBrief/0.1; public-summary-extractor)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            content_type = str(response.headers.get("Content-Type", "")).lower()
            if "html" not in content_type:
                return {}
            html_text = response.read(1_500_000).decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, ValueError):
        return {}
    parser = _PublicArticleParser()
    try:
        parser.feed(html_text)
        parser.close()
    except Exception:
        return {}
    body = parser.text()
    description = normalize_text(parser.description)
    if len(body) < 180 and len(description) < 80:
        return {}
    return {"body_text": body, "public_description": description}


def cache_path_for_url(url: str) -> Path:
    return CACHE_DIR / f"{sha256(url.encode('utf-8')).hexdigest()}.json"


def read_cached_article(url: str) -> dict:
    path = cache_path_for_url(url)
    try:
        if not path.exists() or time.time() - path.stat().st_mtime > CACHE_TTL_SECONDS:
            return {}
        cached = json.loads(path.read_text(encoding="utf-8"))
        return cached if isinstance(cached, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write_cached_article(url: str, content: dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path_for_url(url).write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    except OSError:
        # Cache failures must never make a publisher request fail.
        return


def enrich_news_with_public_content(news_data: dict, max_articles: int = 24) -> dict:
    """Attach public body text to a bounded set of direct trusted articles."""
    categories = news_data.get("categories", []) or []
    targets: list[tuple[int, int, str]] = []
    seen_urls: set[str] = set()
    for category_index, category in enumerate(categories):
        for article_index, article in enumerate(category.get("articles", []) or []):
            url = str(article.get("url", "")).strip()
            if url and url not in seen_urls and public_article_allowed(url):
                targets.append((category_index, article_index, url))
                seen_urls.add(url)
            if len(targets) >= max_articles:
                break
        if len(targets) >= max_articles:
            break

    extracted = 0
    cached = 0
    failures = 0
    pending: list[tuple[int, int, str]] = []
    for category_index, article_index, url in targets:
        content = read_cached_article(url)
        if content:
            article = categories[category_index]["articles"][article_index]
            article.update(content)
            article["content_source"] = "public_html_cache"
            cached += 1
        else:
            pending.append((category_index, article_index, url))

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(fetch_public_article_text, url, timeout_seconds=5): (category_index, article_index, url)
            for category_index, article_index, url in pending
        }
        for future in as_completed(futures):
            category_index, article_index, url = futures[future]
            try:
                content = future.result()
            except Exception:
                failures += 1
                continue
            if not content:
                failures += 1
                continue
            article = categories[category_index]["articles"][article_index]
            article.update(content)
            article["content_source"] = "public_html"
            write_cached_article(url, content)
            extracted += 1

    return {
        **news_data,
        "categories": categories,
        "content_extraction": {
            "attempted": len(targets),
            "extracted": extracted,
            "cached": cached,
            "unavailable": failures,
            "policy": "trusted-public-html-only",
        },
    }
