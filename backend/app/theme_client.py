from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path

from market_client import MarketClientError, fetch_yahoo_chart


class ThemeClientError(RuntimeError):
    pass


def load_theme_symbols(path: Path) -> list[dict]:
    if not path.exists():
        raise ThemeClientError(f"Theme symbols file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_theme_snapshot(symbols: list[dict], timeout_seconds: int = 30) -> dict:
    items_by_position: dict[int, dict] = {}
    errors = []

    worker_count = min(8, max(1, len(symbols)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(fetch_yahoo_chart, symbol, timeout_seconds): (position, symbol)
            for position, symbol in enumerate(symbols)
        }
        for future in as_completed(future_map):
            position, symbol = future_map[future]
            try:
                quote = future.result()
                quote["theme"] = symbol.get("theme", "")
                quote["affected_industries"] = symbol.get("affected_industries", [])
                items_by_position[position] = quote
            except MarketClientError as error:
                errors.append(str(error))
            except Exception as error:
                errors.append(f"Unexpected theme data error for {symbol.get('symbol', '')}: {error}")

    items = [items_by_position[position] for position in sorted(items_by_position)]

    if not items:
        raise ThemeClientError("; ".join(errors) or "No theme data returned.")

    return {
        "source": "Yahoo Finance chart",
        "items": items,
        "errors": errors,
        "note": "主题和商品价格使用公开行情代理，适合作为早报线索，不构成投资建议。",
    }


def build_mock_theme_snapshot() -> dict:
    return {
        "source": "mock",
        "items": [
            {
                "name": "WTI原油",
                "theme": "能源价格",
                "regular_market_price": None,
                "change_percent_from_previous_close": None,
                "affected_industries": ["油气", "化工", "航运", "航空"],
            },
            {
                "name": "铜",
                "theme": "工业金属",
                "regular_market_price": None,
                "change_percent_from_previous_close": None,
                "affected_industries": ["电力设备", "新能源", "制造业"],
            },
            {
                "name": "半导体ETF",
                "theme": "半导体",
                "regular_market_price": None,
                "change_percent_from_previous_close": None,
                "affected_industries": ["芯片", "AI算力", "消费电子"],
            },
        ],
        "note": "主题价格暂时使用占位符，真实接口失败时回退。",
    }
