from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import urllib.parse
from pathlib import Path

from market_client import MarketClientError, fetch_yahoo_chart
from news_client import NewsClientError, fetch_rss_articles
from sec_client import SecClientError, fetch_recent_sec_filings
from verification_sources import build_company_verification_sources


class CompanyClientError(RuntimeError):
    pass


def load_company_watchlist(path: Path) -> list[dict]:
    if not path.exists():
        raise CompanyClientError(f"Company watchlist file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_company_snapshot(
    companies: list[dict],
    timeout_seconds: int = 10,
    max_articles_per_company: int = 2,
    max_companies: int = 5,
) -> dict:
    selected_companies = companies[:max_companies]
    items_by_position: dict[int, dict] = {}
    errors = []

    worker_count = min(8, max(1, len(selected_companies)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(
                fetch_one_company,
                company,
                timeout_seconds,
                max_articles_per_company,
            ): position
            for position, company in enumerate(selected_companies)
        }
        for future in as_completed(future_map):
            position = future_map[future]
            try:
                item, item_errors = future.result()
                items_by_position[position] = item
                errors.extend(item_errors)
            except Exception as error:
                company = selected_companies[position]
                errors.append(f"Unexpected company data error for {company.get('symbol', '')}: {error}")

    items = [items_by_position[position] for position in sorted(items_by_position)]

    if not items:
        raise CompanyClientError("; ".join(errors) or "No company data returned.")

    return {
        "source": "Yahoo Finance chart + Google News RSS",
        "items": items,
        "errors": errors,
        "coverage": {
            "requested_companies": len(companies),
            "fetched_companies": len(items),
            "max_companies": max_companies,
        },
        "note": "公司数据为观察池线索，新闻标题不等于已核验公告；正式投研需进一步核对交易所公告和公司 IR。",
    }


def fetch_one_company(
    company: dict,
    timeout_seconds: int,
    max_articles_per_company: int,
) -> tuple[dict, list[str]]:
    errors = []
    item = {
        "symbol": company.get("symbol", ""),
        "name": company.get("name", company.get("symbol", "")),
        "sector": company.get("sector", ""),
        "quote": None,
        "articles": [],
        "verification_sources": build_company_verification_sources(company),
        "official_filings": [],
    }

    try:
        item["quote"] = fetch_yahoo_chart(company, timeout_seconds)
    except MarketClientError as error:
        errors.append(str(error))

    try:
        item["official_filings"] = fetch_recent_sec_filings(company, timeout_seconds)
    except SecClientError as error:
        errors.append(str(error))

    try:
        query = build_company_news_query(company)
        item["articles"] = compact_articles(
            fetch_google_news_rss(query, timeout_seconds, max_articles_per_company)
        )
    except NewsClientError as error:
        errors.append(str(error))

    return item, errors


def build_company_news_query(company: dict) -> str:
    name = company.get("name", "")
    symbol = company.get("symbol", "")
    keywords = company.get("keywords", [])
    keyword_text = " OR ".join(keywords[:4])
    if keyword_text:
        return f'"{name}" OR {symbol} ({keyword_text})'
    return f'"{name}" OR {symbol} earnings announcement'


def fetch_google_news_rss(query: str, timeout_seconds: int, max_records: int) -> list[dict]:
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    return fetch_rss_articles(url, timeout_seconds, max_records)


def compact_articles(articles: list[dict]) -> list[dict]:
    return [
        {
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "published": article.get("published", ""),
        }
        for article in articles
    ]


def build_mock_company_snapshot() -> dict:
    return {
        "source": "mock",
        "items": [
            {
                "symbol": "NVDA",
                "name": "英伟达",
                "sector": "AI算力/半导体",
                "quote": {"regular_market_price": None, "change_percent_from_previous_close": None},
                "articles": [],
            },
            {
                "symbol": "TSM",
                "name": "台积电",
                "sector": "半导体制造",
                "quote": {"regular_market_price": None, "change_percent_from_previous_close": None},
                "articles": [],
            },
        ],
        "note": "公司观察池暂时使用占位符，真实接口失败时回退。",
    }


