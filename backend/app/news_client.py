from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
import http.client
import html
import json
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


class NewsClientError(RuntimeError):
    pass


def load_news_feeds(path: Path) -> list[dict]:
    if not path.exists():
        raise NewsClientError(f"News feeds file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_news_snapshot(
    feeds: list[dict],
    timeout_seconds: int = 30,
    max_records_per_feed: int = 5,
) -> dict:
    categories_by_position: dict[int, dict] = {}
    errors: list[str] = []

    # A number of publishers intermittently close TLS handshakes when too many
    # feeds are opened at once from one address. Fewer workers plus a bounded
    # retry is slower by a few seconds, but keeps official feeds usable.
    worker_count = min(4, max(1, len(feeds)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(fetch_feed_articles, feed["url"], timeout_seconds, max_records_per_feed): (position, feed)
            for position, feed in enumerate(feeds)
        }
        for future in as_completed(future_map):
            position, feed = future_map[future]
            try:
                articles = future.result()
            except NewsClientError as error:
                errors.append(str(error))
                articles = []
            except Exception as error:
                errors.append(f"Unexpected feed error for {feed['url']}: {error}")
                articles = []

            source_name = feed.get("label", "")
            for article in articles:
                article.setdefault("source_name", source_name)
                article.setdefault("source_domain", feed.get("url", ""))
                article.setdefault("feed_category", feed.get("category", ""))
                article.setdefault("feed_region", feed.get("region", ""))
                article.setdefault("feed_topics", feed.get("topics", []))

            categories_by_position[position] = {
                "category": feed.get("category", ""),
                "label": source_name,
                "region": feed.get("region", ""),
                "topics": feed.get("topics", []),
                "url": feed["url"],
                "source_name": source_name,
                "articles": articles,
            }

    categories = [categories_by_position[position] for position in sorted(categories_by_position)]

    if not any(category["articles"] for category in categories):
        raise NewsClientError("; ".join(errors) or "No RSS/Atom articles returned.")

    return {
        "source": "RSS/Atom",
        "categories": categories,
        "errors": errors,
        "note": "RSS and Atom feeds are used as raw briefing clues. They should be deduped, grouped, and verified before final wording.",
    }


def fetch_feed_articles(url: str, timeout_seconds: int, max_records: int) -> list[dict]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    last_error: Exception | None = None
    xml_text = ""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                xml_text = response.read().decode("utf-8", errors="replace")
                break
        except http.client.IncompleteRead as error:
            xml_text = error.partial.decode("utf-8", errors="replace")
            break
        except urllib.error.URLError as error:
            last_error = error
            if attempt < 2:
                time.sleep(1.2 * (attempt + 1))
    if not xml_text:
        raise NewsClientError(f"RSS/Atom network error for {url}: {last_error}") from last_error

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as error:
        raise NewsClientError(f"RSS/Atom returned invalid XML for {url}.") from error

    channel = root.find("channel")
    if channel is not None:
        return parse_rss_channel(channel, max_records)

    return parse_atom_feed(root, max_records)


def fetch_rss_articles(url: str, timeout_seconds: int, max_records: int) -> list[dict]:
    return fetch_feed_articles(url, timeout_seconds, max_records)


def parse_rss_channel(channel: ET.Element, max_records: int) -> list[dict]:
    articles = []
    for item in channel.findall("item")[:max_records]:
        source_element = item.find("source")
        source_url = source_element.attrib.get("url", "") if source_element is not None else ""
        source_name = clean_article_text(text_or_empty(source_element))
        article = {
            "title": clean_article_text(text_or_empty(item.find("title"))),
            "url": clean_article_text(text_or_empty(item.find("link"))),
            "published": normalize_published(text_or_empty(item.find("pubDate"))),
            "description": clean_article_text(text_or_empty(item.find("description"))),
        }
        # Google News RSS keeps the original publisher in <source>. Preserve it
        # so downstream scoring can distinguish Reuters/AP from an aggregator.
        if source_name:
            article["source_name"] = source_name
        if source_url:
            article["source_domain"] = source_url
        articles.append(article)
    return articles


def parse_atom_feed(root: ET.Element, max_records: int) -> list[dict]:
    articles = []
    namespace = ""
    if root.tag.startswith("{") and "}" in root.tag:
        namespace = root.tag[1:].split("}", 1)[0]

    def atom_name(name: str) -> str:
        return f"{{{namespace}}}{name}" if namespace else name

    for entry in root.findall(atom_name("entry"))[:max_records]:
        url = ""
        for link in entry.findall(atom_name("link")):
            href = link.attrib.get("href", "")
            rel = link.attrib.get("rel", "alternate")
            if href and rel in {"alternate", ""}:
                url = href
                break
        if not url:
            url = text_or_empty(entry.find(atom_name("link")))

        summary = text_or_empty(entry.find(atom_name("summary"))) or text_or_empty(entry.find(atom_name("content")))
        published = (
            text_or_empty(entry.find(atom_name("published")))
            or text_or_empty(entry.find(atom_name("updated")))
        )
        articles.append(
            {
                "title": clean_article_text(text_or_empty(entry.find(atom_name("title")))),
                "url": clean_article_text(url),
                "published": normalize_published(published),
                "description": clean_article_text(summary),
            }
        )
    return articles


def text_or_empty(element) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def clean_article_text(value: str) -> str:
    text = html.unescape(value or "")
    fragments: list[str] = []
    in_tag = False
    for char in text:
        if char == "<":
            in_tag = True
            fragments.append(" ")
            continue
        if char == ">":
            in_tag = False
            fragments.append(" ")
            continue
        if not in_tag:
            fragments.append(char)
    return " ".join("".join(fragments).split())


def normalize_published(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    try:
        return parsedate_to_datetime(raw).isoformat()
    except (TypeError, ValueError, IndexError):
        return raw


def build_mock_news_snapshot() -> dict:
    return {
        "source": "mock",
        "categories": [
            {
                "category": "world",
                "label": "国际新闻",
                "articles": [],
            },
            {
                "category": "business",
                "label": "商业财经",
                "articles": [],
            },
        ],
        "note": "新闻数据暂时使用占位符，真实接口失败时回退。",
    }


def merge_news_snapshots(snapshots: list[dict]) -> dict:
    categories: list[dict] = []
    errors: list[str] = []
    seen: set[str] = set()
    sources: list[str] = []

    for snapshot in snapshots:
        if not snapshot:
            continue
        source = str(snapshot.get("source", "unknown"))
        if source and source not in sources:
            sources.append(source)
        errors.extend(snapshot.get("errors", []) or [])
        for category in snapshot.get("categories", []) or []:
            articles = []
            for article in category.get("articles", []) or []:
                key = article_key(article)
                if not key or key in seen:
                    continue
                seen.add(key)
                articles.append(article)
            if articles:
                merged_category = dict(category)
                merged_category["articles"] = articles
                merged_category["source"] = source
                categories.append(merged_category)

    if not categories:
        raise NewsClientError("No combined news articles returned.")

    return {
        "source": " + ".join(sources) if sources else "combined",
        "categories": categories,
        "errors": errors,
        "note": "Combined news snapshot: Marketaux/RSS/GDELT are used as raw clues; final wording should be deduped, categorized, and verified by the briefing layer.",
    }


def article_key(article: dict) -> str:
    url = str(article.get("url", "")).strip().lower()
    if url:
        return url
    return " ".join(str(article.get("title", "")).lower().split())[:120]
