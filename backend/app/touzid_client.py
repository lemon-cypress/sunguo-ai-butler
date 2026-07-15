from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import gzip
import zlib
from datetime import date, timedelta
from pathlib import Path


TOUZID_BASE_URL = "https://open.touzid.com/api"
DEFAULT_TOKEN_FILE = Path.home() / ".codex" / "skills" / "\u6295\u8d44\u6570\u636e\u7f51-\u63a5\u53e3\u6570\u636e\u67e5\u8be2" / "token.json"


class TouzidClientError(RuntimeError):
    pass


def fetch_touzid_market_snapshot(
    token: str = "",
    token_path: Path | None = None,
    timeout_seconds: int = 20,
    industry_max_count: int = 12,
    index_symbols: list[str] | None = None,
    a_share_watchlist: list[dict] | None = None,
    stock_max_count: int = 5,
    announcement_days: int = 14,
    finreport_fields: list[str] | None = None,
    fundamental_limit: int = 1,
) -> dict:
    api_token = resolve_token(token, token_path)
    errors: list[str] = []

    industries: list[dict] = []
    index_valuation: list[dict] = []
    a_share_companies: list[dict] = []

    try:
        industries = fetch_industry_snapshot(
            api_token,
            timeout_seconds=timeout_seconds,
            max_count=industry_max_count,
        )
    except TouzidClientError as error:
        errors.append(f"industry: {error}")

    try:
        symbols = index_symbols or ["sh000001", "sz399001", "sh000300", "sz399006", "sh000688"]
        index_valuation = fetch_index_valuation(
            symbols,
            api_token,
            timeout_seconds=timeout_seconds,
        )
    except TouzidClientError as error:
        errors.append(f"index_valuation: {error}")

    try:
        a_share_companies = fetch_a_share_company_snapshot(
            a_share_watchlist or [],
            api_token,
            timeout_seconds=timeout_seconds,
            max_count=stock_max_count,
            announcement_days=announcement_days,
            finreport_fields=finreport_fields,
            fundamental_limit=fundamental_limit,
        )
    except TouzidClientError as error:
        errors.append(f"a_share_companies: {error}")

    if not industries and not index_valuation and not a_share_companies and errors:
        raise TouzidClientError("; ".join(errors))

    return {
        "source": "Touzid open API",
        "provider": "touzid",
        "industries": industries,
        "index_valuation": index_valuation,
        "a_share_companies": a_share_companies,
        "errors": errors,
        "note": (
            "Touzid structured data is used for A-share industry, index, company valuation, financial report and announcement clues. "
            "Important conclusions still need exchange filings, official announcements and paid data reconciliation."
        ),
    }


def fetch_industry_snapshot(token: str, timeout_seconds: int = 20, max_count: int = 12) -> list[dict]:
    base_rows = fetch_industry_baseinfo(token, timeout_seconds=timeout_seconds)
    broad_level = [
        row for row in base_rows
        if as_int(row.get("idx_type")) == 0 and as_int(row.get("type")) == 1 and clean_text(row.get("symbol"))
    ]
    mid_level = [
        row for row in base_rows
        if as_int(row.get("idx_type")) == 0 and as_int(row.get("type")) == 2 and clean_text(row.get("symbol"))
    ]
    detail_level = [
        row for row in base_rows
        if as_int(row.get("idx_type")) == 0 and as_int(row.get("type")) == 3 and clean_text(row.get("symbol"))
    ]
    if len(detail_level) >= max(3, max_count):
        first_level = detail_level
    elif len(mid_level) >= 3:
        first_level = mid_level
    else:
        first_level = broad_level

    selected = first_level[: max(1, max_count)]
    symbols = [clean_text(row.get("symbol")) for row in selected]
    if not symbols:
        return []

    prof_rows = fetch_industry_profinfo(symbols, token, timeout_seconds=timeout_seconds)
    trps_rows = fetch_industry_trpsinfo(symbols, token, timeout_seconds=timeout_seconds)
    prof_by_symbol = {clean_text(row.get("symbol")): row for row in prof_rows}
    trps_by_symbol = {clean_text(row.get("symbol")): row for row in trps_rows}

    items: list[dict] = []
    for row in selected:
        symbol = clean_text(row.get("symbol"))
        prof = prof_by_symbol.get(symbol, {})
        trps = trps_by_symbol.get(symbol, {})
        items.append(
            {
                "symbol": symbol,
                "name": clean_text(row.get("name")),
                "level": as_int(row.get("type")),
                "stock_count": as_int(row.get("num")),
                "profit_1d": as_number(prof.get("d_typrofit_rt")),
                "profit_1y": as_number(prof.get("d_1yprofit_rt")),
                "profit_3y": as_number(prof.get("d_3yprofit_rt")),
                "rps_5d": as_number(trps.get("rps5_rt")),
                "rps_20d": as_number(trps.get("rps20_rt")),
                "rps_50d": as_number(trps.get("rps50_rt")),
                "turnover_1d": as_number(trps.get("tr1_rt")),
                "turnover_30d": as_number(trps.get("tr30_rt")),
                "trade_date": clean_text(prof.get("date") or trps.get("date")),
            }
        )

    return sorted(
        items,
        key=lambda item: (
            item.get("rps_20d") is not None,
            item.get("rps_20d") or -999999,
            item.get("profit_1d") or -999999,
        ),
        reverse=True,
    )


def fetch_industry_baseinfo(token: str, timeout_seconds: int = 20) -> list[dict]:
    return request_touzid("industry/baseinfo", {"token": token}, timeout_seconds=timeout_seconds)


def fetch_industry_profinfo(symbols: list[str], token: str, timeout_seconds: int = 20) -> list[dict]:
    return request_touzid(
        "industry/profinfo",
        {"token": token, "symbols": symbols},
        timeout_seconds=timeout_seconds,
    )


def fetch_industry_trpsinfo(symbols: list[str], token: str, timeout_seconds: int = 20) -> list[dict]:
    return request_touzid(
        "industry/trpsinfo",
        {"token": token, "symbols": symbols},
        timeout_seconds=timeout_seconds,
    )


def fetch_index_valuation(symbols: list[str], token: str, timeout_seconds: int = 20) -> list[dict]:
    rows = request_touzid(
        "indice/valuinfo",
        {"token": token, "symbols": symbols},
        timeout_seconds=timeout_seconds,
    )
    items = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        items.append(
            {
                "symbol": clean_text(row.get("symbol")),
                "name": clean_text(row.get("name")),
                "pe": as_number(row.get("pe_aw") or row.get("pe")),
                "pb": as_number(row.get("pb_aw") or row.get("pb")),
                "ps": as_number(row.get("ps_aw") or row.get("ps")),
                "dividend_yield": as_number(row.get("div_aw") or row.get("div")),
                "trade_date": clean_text(row.get("date")),
            }
        )
    return items


def fetch_stock_announcements(
    symbol: str,
    token: str,
    start_date: str = "",
    end_date: str = "",
    timeout_seconds: int = 20,
) -> list[dict]:
    body = {"token": token, "symbol": symbol}
    if start_date:
        body["start_date"] = start_date
    if end_date:
        body["end_date"] = end_date
    rows = request_touzid("stock/announcement", body, timeout_seconds=timeout_seconds)
    items = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        items.append(
            {
                "symbol": symbol,
                "title": clean_text(row.get("announcementTitle")),
                "time": clean_text(row.get("announcementTime")),
                "category": clean_text(row.get("category")),
                "file_type": clean_text(row.get("adjunctType")),
                "url": clean_text(row.get("adjunctUrl")),
            }
        )
    return items


def fetch_a_share_company_snapshot(
    watchlist: list[dict],
    token: str,
    timeout_seconds: int = 20,
    max_count: int = 5,
    announcement_days: int = 14,
    finreport_fields: list[str] | None = None,
    fundamental_limit: int = 1,
) -> list[dict]:
    selected = [item for item in watchlist if clean_text(item.get("symbol"))][: max(0, max_count)]
    if not selected:
        return []

    symbols = [clean_text(item.get("symbol")) for item in selected]
    valuation_by_symbol: dict[str, dict] = {}
    try:
        valuation_rows = fetch_stock_valuation(symbols, token, timeout_seconds=timeout_seconds)
        valuation_by_symbol = {row.get("symbol", ""): row for row in valuation_rows}
    except TouzidClientError as error:
        valuation_error = str(error)
    else:
        valuation_error = ""

    start_date = format_date(date.today() - timedelta(days=max(1, announcement_days)))
    end_date = format_date(date.today())
    items: list[dict] = []
    for company in selected:
        symbol = clean_text(company.get("symbol"))
        errors: list[str] = []
        if valuation_error:
            errors.append(f"valuation: {valuation_error}")

        announcements: list[dict] = []
        supervision: list[dict] = []
        financials: list[dict] = []
        fundamentals: list[dict] = []

        try:
            announcements = fetch_stock_announcements(
                symbol,
                token,
                start_date=start_date,
                end_date=end_date,
                timeout_seconds=timeout_seconds,
            )[:3]
        except TouzidClientError as error:
            errors.append(f"announcements: {error}")

        try:
            supervision = fetch_stock_supervision(
                symbol,
                token,
                start_date=start_date,
                end_date=end_date,
                timeout_seconds=timeout_seconds,
            )[:3]
        except TouzidClientError as error:
            errors.append(f"supervision: {error}")

        try:
            financials = fetch_stock_finreport(
                symbol,
                token,
                fields=finreport_fields,
                timeout_seconds=timeout_seconds,
            )[:1]
        except TouzidClientError as error:
            errors.append(f"finreport: {error}")

        try:
            fundamentals = fetch_stock_fundamental(
                symbol,
                token,
                limit=fundamental_limit,
                timeout_seconds=timeout_seconds,
            )[: max(0, fundamental_limit)]
        except TouzidClientError as error:
            errors.append(f"fundamental: {error}")

        items.append(
            {
                "symbol": symbol,
                "name": clean_text(company.get("name")),
                "sector": clean_text(company.get("sector")),
                "valuation": valuation_by_symbol.get(symbol, {}),
                "announcements": announcements,
                "supervision": supervision,
                "financials": financials,
                "fundamentals": fundamentals,
                "errors": errors,
            }
        )
    return items


def fetch_stock_valuation(symbols: list[str], token: str, timeout_seconds: int = 20) -> list[dict]:
    rows = request_touzid(
        "stock/valuinfo",
        {"token": token, "symbols": symbols},
        timeout_seconds=timeout_seconds,
    )
    items: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = clean_text(row.get("symbol"))
        items.append(
            {
                "symbol": symbol,
                "name": clean_text(row.get("name")),
                "date": clean_text(row.get("date")),
                "pe_ttm": as_number(row.get("pe_ttm") or row.get("pet")),
                "pe_percentile_5y": first_number(row, ["pe_ttm_per_5y", "pet_per_5y", "pe_per_5y"]),
                "pe_percentile_10y": first_number(row, ["pe_ttm_per_10y", "pet_per_10y", "pe_per_10y"]),
                "pb": as_number(row.get("pb")),
                "pb_percentile_5y": first_number(row, ["pb_per_5y", "pb_percentile_5y"]),
                "pb_percentile_10y": first_number(row, ["pb_per_10y", "pb_percentile_10y"]),
                "ps_ttm": as_number(row.get("ps_ttm") or row.get("pst")),
                "dividend_yield": first_number(row, ["dividend_r", "dividend_yield", "dyr"]),
                "raw": compact_raw(row),
            }
        )
    return items


def fetch_stock_baseinfo(symbols: list[str], token: str, timeout_seconds: int = 20) -> list[dict]:
    """Return the small identity record used by the self-selected-stock UI."""
    body: dict = {"token": token}
    if symbols:
        body["symbols"] = symbols
    rows = request_touzid("stock/baseinfo", body, timeout_seconds=timeout_seconds)
    return [
        {
            "symbol": clean_text(row.get("symbol")),
            "name": clean_text(row.get("name")),
            "exchange": clean_text(row.get("exchange")),
            "market": clean_text(row.get("market")),
            "report_date": clean_text(row.get("report_date")),
        }
        for row in rows
        if isinstance(row, dict) and clean_text(row.get("symbol"))
    ]


def fetch_stock_kline(
    symbol: str,
    token: str,
    start_date: str = "",
    end_date: str = "",
    timeout_seconds: int = 20,
) -> list[dict]:
    body: dict = {"token": token, "symbol": symbol}
    if start_date:
        body["start_date"] = start_date
    if end_date:
        body["end_date"] = end_date
    rows = request_touzid("stock/kline", body, timeout_seconds=timeout_seconds)
    items = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        close = as_number(row.get("close"))
        if close is None:
            continue
        items.append({
            "date": clean_text(row.get("date")),
            "close": close,
            "open": as_number(row.get("open")),
            "high": as_number(row.get("high")),
            "low": as_number(row.get("low")),
        })
    return sorted(items, key=lambda item: item.get("date") or "")


FINANCIAL_QUARTERS = (
    ("25Q3", "2025-09-30"),
    ("25Q4", "2025-12-31"),
    ("26Q1", "2026-03-31"),
    ("26Q2", "2026-06-30"),
)


def fetch_stock_financial_series(symbol: str, token: str, timeout_seconds: int = 20) -> list[dict]:
    """Return an explicitly quarterly income-statement series for the dashboard.

    Do not silently substitute cumulative or annual figures: each request uses
    the period-end date and the API's single-quarter (``.q``) field type.
    """
    fields = ["pr.toi.q", "pr.toi.q_y", "pr.oc_rt.q", "pr.np.q", "pr.np_rt.q"]
    series: list[dict] = []
    for label, report_date in FINANCIAL_QUARTERS:
        rows = fetch_stock_finreport(
            symbol,
            token,
            date=report_date,
            fields=fields,
            timeout_seconds=timeout_seconds,
        )
        row = rows[0] if rows else {}
        metrics = row.get("metrics", {}) or {}
        series.append({
            "label": label,
            "report_date": report_date,
            "available": bool(row and clean_text(row.get("date")) == report_date),
            "revenue": as_number(metrics.get("pr.toi.q")),
            "revenue_yoy": as_number(metrics.get("pr.toi.q_y")),
            "gross_margin": as_number(metrics.get("pr.oc_rt.q")),
            "net_profit": as_number(metrics.get("pr.np.q")),
            "net_margin": as_number(metrics.get("pr.np_rt.q")),
        })
    return series


def fetch_stock_watchlist_snapshot(
    watchlist: list[dict],
    token: str = "",
    token_path: Path | None = None,
    timeout_seconds: int = 20,
) -> list[dict]:
    """Build the lightweight quote/valuation/financial view for selected A shares.

    Touzid's public K-line endpoint is daily data.  The UI intentionally labels
    the value as the latest trading-day close instead of claiming an intraday
    real-time quote.
    """
    api_token = resolve_token(token, token_path)
    selected = [item for item in watchlist if clean_text(item.get("symbol"))]
    if not selected:
        return []
    symbols = [clean_text(item.get("symbol")) for item in selected]
    valuation_rows = fetch_stock_valuation(symbols, api_token, timeout_seconds=timeout_seconds)
    valuations = {clean_text(row.get("symbol")): row for row in valuation_rows}
    rows: list[dict] = []
    start = format_date(date.today() - timedelta(days=12))
    end = format_date(date.today())
    for item in selected:
        symbol = clean_text(item.get("symbol"))
        errors: list[str] = []
        try:
            prices = fetch_stock_kline(symbol, api_token, start, end, timeout_seconds=timeout_seconds)
        except TouzidClientError as error:
            prices = []
            errors.append(f"kline: {error}")
        try:
            financial_series = fetch_stock_financial_series(symbol, api_token, timeout_seconds=timeout_seconds)
        except TouzidClientError as error:
            financial_series = []
            errors.append(f"finreport: {error}")
        latest = prices[-1] if prices else {}
        previous = prices[-2] if len(prices) > 1 else {}
        latest_close = as_number(latest.get("close"))
        previous_close = as_number(previous.get("close"))
        change_percent = None
        if latest_close is not None and previous_close not in (None, 0):
            change_percent = (latest_close - previous_close) / previous_close * 100
        rows.append({
            "symbol": symbol,
            "name": clean_text(item.get("name")) or clean_text((valuations.get(symbol) or {}).get("name")),
            "sector": clean_text(item.get("sector")),
            "quote": {
                "price": latest_close,
                "date": clean_text(latest.get("date")),
                "previous_close": previous_close,
                "change_percent": change_percent,
                "data_label": "最新交易日收盘价",
            },
            "valuation": valuations.get(symbol, {}),
            "financial_series": financial_series,
            "errors": errors,
        })
    return rows


def fetch_stock_finreport(
    symbol: str,
    token: str,
    date: str = "",
    fields: list[str] | None = None,
    timeout_seconds: int = 20,
) -> list[dict]:
    body: dict = {"token": token, "symbol": symbol}
    if date:
        body["date"] = date
    if fields:
        body["fields"] = fields
    rows = request_touzid("stock/finreport", body, timeout_seconds=timeout_seconds)
    return [normalize_financial_row(symbol, row) for row in rows if isinstance(row, dict)]


def fetch_stock_fundamental(
    symbol: str,
    token: str,
    fields: list[str] | None = None,
    limit: int = 1,
    timeout_seconds: int = 20,
) -> list[dict]:
    body: dict = {"token": token, "symbol": symbol, "limit": max(1, limit)}
    if fields:
        body["fields"] = fields
    rows = request_touzid("stock/fundamental", body, timeout_seconds=timeout_seconds)
    return [normalize_financial_row(symbol, row) for row in rows if isinstance(row, dict)]


def fetch_stock_supervision(
    symbol: str,
    token: str,
    start_date: str = "",
    end_date: str = "",
    timeout_seconds: int = 20,
) -> list[dict]:
    body = {"token": token, "symbol": symbol}
    if start_date:
        body["start_date"] = start_date
    if end_date:
        body["end_date"] = end_date
    rows = request_touzid("stock/supervision", body, timeout_seconds=timeout_seconds)
    items = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        items.append(
            {
                "symbol": symbol,
                "title": clean_text(row.get("announcementTitle")),
                "time": clean_text(row.get("announcementTime")),
                "type": clean_text(row.get("announcementType")),
                "file_type": clean_text(row.get("adjunctType")),
                "url": clean_text(row.get("adjunctUrl")),
            }
        )
    return items


def normalize_financial_row(symbol: str, row: dict) -> dict:
    date_value = clean_text(row.get("date") or row.get("report_date") or row.get("end_date"))
    metrics = {}
    for key, value in row.items():
        if key in {"symbol", "date", "report_date", "end_date"}:
            continue
        if value in (None, "", "-"):
            continue
        metrics[key] = value
    return {
        "symbol": symbol,
        "date": date_value,
        "metrics": metrics,
    }


def load_a_share_watchlist(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise TouzidClientError(f"Could not read A-share watchlist {path}: {error}") from error
    if not isinstance(payload, list):
        raise TouzidClientError(f"A-share watchlist must be a list: {path}")
    items: list[dict] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        symbol = clean_text(row.get("symbol"))
        if not symbol:
            continue
        items.append(
            {
                "symbol": symbol,
                "name": clean_text(row.get("name")),
                "sector": clean_text(row.get("sector")),
            }
        )
    return items


def request_touzid(endpoint: str, body: dict, timeout_seconds: int = 20) -> list[dict]:
    url = f"{TOUZID_BASE_URL}/{endpoint.strip('/')}/"
    raw_body = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=raw_body,
        method="POST",
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
            content_encoding = response.headers.get("Content-Encoding", "")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise TouzidClientError(f"Touzid HTTP {error.code}: {redact_token(detail, body.get('token'))}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise TouzidClientError(f"Touzid network error: {error}") from error

    try:
        payload = json.loads(decode_response_body(raw, content_encoding))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TouzidClientError(f"Touzid JSON parse error: {error}") from error

    if not isinstance(payload, dict):
        raise TouzidClientError("Touzid response is not an object.")
    errno = payload.get("errno")
    message = clean_text(payload.get("err") or payload.get("error") or payload.get("message"))
    if errno not in (0, "0", 1, "1", None) and message.lower() != "success":
        raise TouzidClientError(f"Touzid returned errno={errno}: {message}")
    rows = payload.get("rsm")
    if rows is None:
        return []
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    if isinstance(rows, dict):
        return [rows]
    raise TouzidClientError("Touzid rsm is not a list or object.")


def decode_response_body(raw: bytes, content_encoding: str) -> str:
    encoding = clean_text(content_encoding).lower()
    if "gzip" in encoding:
        raw = gzip.decompress(raw)
    elif "deflate" in encoding:
        try:
            raw = zlib.decompress(raw)
        except zlib.error:
            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
    return raw.decode("utf-8-sig")


def resolve_token(token: str = "", token_path: Path | None = None) -> str:
    direct = clean_text(token or os.getenv("TOUZID_TOKEN"))
    if direct:
        return direct

    candidates: list[Path] = []
    if token_path and str(token_path) not in {"", "."}:
        candidates.append(token_path)
    env_path = clean_text(os.getenv("TOUZID_TOKEN_PATH"))
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(DEFAULT_TOKEN_FILE)

    for path in candidates:
        try:
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
                loaded = clean_text(payload.get("token") if isinstance(payload, dict) else "")
                if loaded:
                    return loaded
        except (OSError, json.JSONDecodeError) as error:
            raise TouzidClientError(f"Could not read Touzid token file {path}: {error}") from error

    raise TouzidClientError("Missing Touzid token. Set TOUZID_TOKEN or TOUZID_TOKEN_PATH.")


def parse_symbol_list(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def first_number(row: dict, keys: list[str]):
    for key in keys:
        value = as_number(row.get(key))
        if value is not None:
            return value
    return None


def compact_raw(row: dict) -> dict:
    return {key: value for key, value in row.items() if value not in (None, "", "-")}


def format_date(value: date) -> str:
    return value.isoformat()


def redact_token(text: str, token: str | None) -> str:
    if token:
        return text.replace(str(token), "***")
    return text


def as_number(value):
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value):
    if value in (None, "", "-"):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def clean_text(value) -> str:
    return " ".join(str(value or "").split())
