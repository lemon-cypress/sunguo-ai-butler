from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
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


def fetch_news_snapshot(feeds: list[dict], timeout_seconds: int = 30, max_records_per_feed: int = 5) -> dict:
    categories_by_position: dict[int, dict] = {}
    errors = []

    worker_count = min(6, max(1, len(feeds)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(fetch_rss_articles, feed["url"], timeout_seconds, max_records_per_feed): (position, feed)
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
                errors.append(f"Unexpected RSS error for {feed['url']}: {error}")
                articles = []
            categories_by_position[position] = {
                "category": feed["category"],
                "label": feed["label"],
                "url": feed["url"],
                "articles": articles,
            }

    categories = [categories_by_position[position] for position in sorted(categories_by_position)]

    if not any(category["articles"] for category in categories):
        raise NewsClientError("; ".join(errors) or "No RSS articles returned.")

    return {
        "source": "RSS",
        "categories": categories,
        "errors": errors,
        "note": "RSS 标题用于早报线索；松果会把它作为待核验新闻材料，而非最终事实结论。",
    }


def fetch_rss_articles(url: str, timeout_seconds: int, max_records: int) -> list[dict]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            xml_text = response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as error:
        raise NewsClientError(f"RSS network error for {url}: {error}") from error

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as error:
        raise NewsClientError(f"RSS returned invalid XML for {url}.") from error

    articles = []
    channel = root.find("channel")
    if channel is None:
        return articles

    for item in channel.findall("item")[:max_records]:
        articles.append(
            {
                "title": text_or_empty(item.find("title")),
                "url": text_or_empty(item.find("link")),
                "published": text_or_empty(item.find("pubDate")),
                "description": text_or_empty(item.find("description")),
            }
        )
    return articles


def text_or_empty(element) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


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
