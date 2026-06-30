from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import http.client
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart"


class MarketClientError(RuntimeError):
    pass


def load_symbols(path: Path) -> list[dict]:
    if not path.exists():
        raise MarketClientError(f"Market symbols file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_market_snapshot(symbols: list[dict], timeout_seconds: int = 30) -> dict:
    indices_by_position: dict[int, dict] = {}
    errors = []

    worker_count = min(8, max(1, len(symbols)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(fetch_yahoo_chart, item, timeout_seconds): position
            for position, item in enumerate(symbols)
        }
        for future in as_completed(future_map):
            position = future_map[future]
            try:
                indices_by_position[position] = future.result()
            except MarketClientError as error:
                errors.append(str(error))
            except Exception as error:
                errors.append(f"Unexpected market data error: {error}")

    indices = [indices_by_position[position] for position in sorted(indices_by_position)]

    if not indices:
        raise MarketClientError("; ".join(errors) or "No market data returned.")

    return {
        "source": "Yahoo Finance chart",
        "indices": indices,
        "errors": errors,
        "note": "公开 chart 接口用于早报线索；后续可替换为更权威的行情 API。",
    }


def fetch_yahoo_chart(symbol_item: dict, timeout_seconds: int) -> dict:
    symbol = symbol_item["symbol"]
    encoded_symbol = urllib.parse.quote(symbol, safe="")
    url = f"{YAHOO_CHART_URL}/{encoded_symbol}?range=1d&interval=1d"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    payload = None
    last_error: Exception | None = None
    for attempt in range(1, 3):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except http.client.IncompleteRead as error:
            last_error = error
        except urllib.error.URLError as error:
            last_error = error
        except TimeoutError as error:
            last_error = error
        except json.JSONDecodeError as error:
            raise MarketClientError(f"Yahoo Finance returned invalid JSON for {symbol}.") from error

    if payload is None:
        raise MarketClientError(f"Yahoo Finance network error for {symbol}: {last_error}") from last_error

    result = (payload.get("chart", {}).get("result") or [None])[0]
    if not result:
        raise MarketClientError(f"Yahoo Finance returned no result for {symbol}.")

    meta = result.get("meta", {})
    regular_price = meta.get("regularMarketPrice")
    previous_close = meta.get("previousClose") or meta.get("chartPreviousClose")
    change_percent = None
    if regular_price is not None and previous_close not in {None, 0}:
        change_percent = round((regular_price - previous_close) / previous_close * 100, 2)

    return {
        "symbol": symbol,
        "name": symbol_item.get("name", symbol),
        "region": symbol_item.get("region", ""),
        "currency": meta.get("currency", ""),
        "exchange": meta.get("fullExchangeName") or meta.get("exchangeName", ""),
        "regular_market_price": regular_price,
        "previous_close": previous_close,
        "change_percent_from_previous_close": change_percent,
        "market_time": meta.get("regularMarketTime"),
    }


def build_mock_market_snapshot() -> dict:
    return {
        "source": "mock",
        "indices": [
            {"name": "上证指数", "region": "中国", "regular_market_price": None, "change_percent_from_previous_close": None},
            {"name": "纳斯达克综合", "region": "美国", "regular_market_price": None, "change_percent_from_previous_close": None},
            {"name": "日经225", "region": "日本", "regular_market_price": None, "change_percent_from_previous_close": None},
            {"name": "德国DAX", "region": "欧洲", "regular_market_price": None, "change_percent_from_previous_close": None},
        ],
        "note": "市场数据暂时使用占位符，真实接口失败时回退。",
    }
