from __future__ import annotations

"""Persistence and search helpers for the dashboard's user-selected A shares."""

import json
from pathlib import Path

from touzid_client import TouzidClientError, fetch_stock_baseinfo, resolve_token


def load_stock_watchlist(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"无法读取自选股文件：{error}") from error
    items = payload.get("items", []) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ValueError("自选股文件格式不正确")
    return [normalize_stock(item) for item in items if isinstance(item, dict) and normalize_stock(item)]


def save_stock_watchlist(path: Path, items: list[dict]) -> list[dict]:
    payload = {"version": "stock-watchlist-v1", "items": items}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return items


def normalize_stock(item: dict) -> dict:
    symbol = str(item.get("symbol") or "").strip().lower()
    name = " ".join(str(item.get("name") or "").split())
    sector = " ".join(str(item.get("sector") or "").split())
    if not symbol:
        return {}
    return {"symbol": symbol, "name": name, "sector": sector}


def normalize_a_share_code(value: str) -> list[str]:
    raw = str(value or "").strip().lower()
    if raw.startswith(("sh", "sz", "bj")) and len(raw) == 8 and raw[2:].isdigit():
        return [raw]
    if len(raw) != 6 or not raw.isdigit():
        return []
    if raw.startswith("6"):
        return [f"sh{raw}"]
    if raw.startswith(("8", "4")):
        return [f"bj{raw}"]
    return [f"sz{raw}"]


def search_stock(query: str, watchlist: list[dict], token: str = "", token_path: Path | None = None) -> list[dict]:
    text = " ".join(str(query or "").split())
    if not text:
        return []
    lower = text.lower()
    local_matches = [
        item for item in watchlist
        if lower in item.get("symbol", "").lower() or lower in item.get("name", "").lower()
    ]
    symbols = normalize_a_share_code(text)
    if not symbols:
        # The open API's base-info route is code-based rather than a fuzzy-name
        # search service.  Keep useful matches from the selected list and give
        # a clear code-input fallback for any other A share.
        return local_matches[:12]
    try:
        records = fetch_stock_baseinfo(symbols, resolve_token(token, token_path))
    except TouzidClientError:
        return local_matches[:12]
    return [
        normalize_stock({"symbol": row.get("symbol"), "name": row.get("name"), "sector": ""})
        for row in records
    ] or local_matches[:12]


def add_stock(path: Path, stock: dict) -> list[dict]:
    item = normalize_stock(stock)
    if not item:
        raise ValueError("股票代码不能为空")
    items = load_stock_watchlist(path)
    if any(row["symbol"] == item["symbol"] for row in items):
        return items
    items.append(item)
    return save_stock_watchlist(path, items)


def remove_stock(path: Path, symbol: str) -> list[dict]:
    clean = str(symbol or "").strip().lower()
    items = [item for item in load_stock_watchlist(path) if item["symbol"] != clean]
    return save_stock_watchlist(path, items)
