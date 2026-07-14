from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request


EASTMONEY_ULIST_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"
EASTMONEY_CLIST_URL = "https://push2.eastmoney.com/api/qt/clist/get"
SINA_QUOTE_URL = "https://hq.sinajs.cn/list={symbols}"


class ChinaMarketError(RuntimeError):
    pass


CHINA_INDEX_SYMBOLS = [
    {"secid": "1.000001", "sina": "sh000001", "symbol": "000001", "name": "\u4e0a\u8bc1\u6307\u6570", "region": "\u4e2d\u56fdA\u80a1"},
    {"secid": "0.399001", "sina": "sz399001", "symbol": "399001", "name": "\u6df1\u8bc1\u6210\u6307", "region": "\u4e2d\u56fdA\u80a1"},
    {"secid": "1.000300", "sina": "sh000300", "symbol": "000300", "name": "\u6caa\u6df1300", "region": "\u4e2d\u56fdA\u80a1"},
    {"secid": "0.399006", "sina": "sz399006", "symbol": "399006", "name": "\u521b\u4e1a\u677f\u6307", "region": "\u4e2d\u56fdA\u80a1"},
    {"secid": "1.000688", "sina": "sh000688", "symbol": "000688", "name": "\u79d1\u521b50", "region": "\u4e2d\u56fdA\u80a1"},
]

INDEX_BY_SECID = {item["secid"]: item for item in CHINA_INDEX_SYMBOLS}
INDEX_BY_SINA = {item["sina"]: item for item in CHINA_INDEX_SYMBOLS}


def fetch_china_market_snapshot(
    timeout_seconds: int = 20,
    sector_max_count: int = 10,
) -> dict:
    errors: list[str] = []
    indices: list[dict] = []
    sectors: list[dict] = []

    try:
        indices = fetch_eastmoney_indices(timeout_seconds=timeout_seconds)
    except ChinaMarketError as error:
        errors.append(f"indices/eastmoney: {error}")
        try:
            indices = fetch_sina_indices(timeout_seconds=timeout_seconds)
        except ChinaMarketError as fallback_error:
            errors.append(f"indices/sina: {fallback_error}")

    try:
        sectors = fetch_eastmoney_sectors(
            timeout_seconds=timeout_seconds,
            max_count=sector_max_count,
        )
    except ChinaMarketError as error:
        errors.append(f"sectors: {error}")

    if not indices and not sectors and errors:
        raise ChinaMarketError("; ".join(errors))

    return {
        "source": "Eastmoney public quote",
        "provider": "eastmoney+sina",
        "indices": indices,
        "sectors": sectors,
        "errors": errors,
        "note": (
            "Eastmoney public quote is used as a domestic market clue source. "
            "For final investment judgment, reconcile it with exchange data, company filings and paid data feeds."
        ),
    }


def fetch_eastmoney_indices(timeout_seconds: int = 20) -> list[dict]:
    params = {
        "fltt": "2",
        "invt": "2",
        "fields": "f12,f14,f2,f3,f4,f5,f6,f17,f18",
        "secids": ",".join(item["secid"] for item in CHINA_INDEX_SYMBOLS),
    }
    payload = request_eastmoney(EASTMONEY_ULIST_URL, params, timeout_seconds)
    rows = (payload.get("data") or {}).get("diff") or []
    if not rows:
        raise ChinaMarketError("Eastmoney index response has no rows.")

    items = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = clean_text(row.get("f12"))
        meta = find_index_meta(symbol)
        if not meta:
            continue
        items.append(
            {
                "symbol": meta["symbol"],
                "name": meta["name"],
                "region": meta["region"],
                "price": as_number(row.get("f2")),
                "change": as_number(row.get("f4")),
                "change_percent": as_number(row.get("f3")),
                "open": as_number(row.get("f17")),
                "previous_close": as_number(row.get("f18")),
                "volume": as_number(row.get("f5")),
                "turnover": as_number(row.get("f6")),
            }
        )
    return items


def fetch_sina_indices(timeout_seconds: int = 20) -> list[dict]:
    symbols = ",".join(item["sina"] for item in CHINA_INDEX_SYMBOLS)
    url = SINA_QUOTE_URL.format(symbols=urllib.parse.quote(symbols, safe=","))
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Referer": "https://finance.sina.com.cn/",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            text = response.read().decode("gb18030", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ChinaMarketError(f"Sina quote network error: {error}") from error

    items = []
    for line in text.splitlines():
        if "hq_str_" not in line or '="' not in line:
            continue
        code = line.split("hq_str_", 1)[1].split("=", 1)[0]
        meta = INDEX_BY_SINA.get(code)
        if not meta:
            continue
        values = line.split('="', 1)[1].rsplit('";', 1)[0].split(",")
        if len(values) < 11:
            continue
        current = as_number(values[3])
        previous_close = as_number(values[2])
        change = None
        change_percent = None
        if current is not None and previous_close not in (None, 0):
            change = round(current - previous_close, 4)
            change_percent = round((change / previous_close) * 100, 4)
        items.append(
            {
                "symbol": meta["symbol"],
                "name": meta["name"],
                "region": meta["region"],
                "price": current,
                "change": change,
                "change_percent": change_percent,
                "open": as_number(values[1]),
                "previous_close": previous_close,
                "high": as_number(values[4]),
                "low": as_number(values[5]),
                "volume": as_number(values[8]),
                "turnover": as_number(values[9]),
                "trade_date": clean_text(values[30]) if len(values) > 30 else "",
                "trade_time": clean_text(values[31]) if len(values) > 31 else "",
                "quote_source": "Sina quote",
            }
        )
    if not items:
        raise ChinaMarketError("Sina quote response has no usable index rows.")
    return items


def find_index_meta(symbol: str) -> dict | None:
    for item in CHINA_INDEX_SYMBOLS:
        if item["symbol"] == symbol:
            return item
    return None


def fetch_eastmoney_sectors(timeout_seconds: int = 20, max_count: int = 10) -> list[dict]:
    params = {
        "pn": "1",
        "pz": str(max(1, min(max_count, 50))),
        "po": "1",
        "np": "1",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:90+t:2",
        "fields": "f12,f14,f2,f3,f4,f5,f6,f104,f105,f128,f140",
    }
    payload = request_eastmoney(EASTMONEY_CLIST_URL, params, timeout_seconds)
    rows = (payload.get("data") or {}).get("diff") or []
    if not rows:
        raise ChinaMarketError("Eastmoney sector response has no rows.")

    items = []
    for row in rows[:max_count]:
        if not isinstance(row, dict):
            continue
        items.append(
            {
                "code": clean_text(row.get("f12")),
                "name": clean_text(row.get("f14")),
                "price": as_number(row.get("f2")),
                "change": as_number(row.get("f4")),
                "change_percent": as_number(row.get("f3")),
                "volume": as_number(row.get("f5")),
                "turnover": as_number(row.get("f6")),
                "rising_count": as_number(row.get("f104")),
                "falling_count": as_number(row.get("f105")),
                "leader_code": clean_text(row.get("f140")),
                "leader_name": clean_text(row.get("f128")),
            }
        )
    return items


def request_eastmoney(url: str, params: dict[str, str], timeout_seconds: int) -> dict:
    query = urllib.parse.urlencode(params)
    full_url = f"{url}?{query}"
    last_error: Exception | None = None
    for attempt in range(3):
        request = urllib.request.Request(
            full_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json,text/plain,*/*",
                "Referer": "https://quote.eastmoney.com/",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read()
            return json.loads(decode_json_bytes(raw))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise ChinaMarketError(f"Eastmoney HTTP {error.code}: {body[:300]}") from error
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
            last_error = error
            time.sleep(0.8 * (attempt + 1))
    raise ChinaMarketError(f"Eastmoney network or parse error: {last_error}")


def decode_json_bytes(raw: bytes) -> str:
    for encoding in ("utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def as_number(value):
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clean_text(value) -> str:
    return " ".join(str(value or "").split())


def build_mock_china_market_snapshot() -> dict:
    return {
        "source": "mock",
        "provider": "mock",
        "indices": [],
        "sectors": [],
        "errors": [],
        "note": "China market data is empty because the real provider was skipped or unavailable.",
    }
