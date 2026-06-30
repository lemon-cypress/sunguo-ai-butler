from __future__ import annotations


COMPANY_SOURCE_OVERRIDES = {
    "NVDA": {
        "cik": "1045810",
        "ir": "https://investor.nvidia.com/",
        "sec": "https://www.sec.gov/edgar/browse/?CIK=1045810",
    },
    "AMD": {
        "cik": "2488",
        "ir": "https://ir.amd.com/",
        "sec": "https://www.sec.gov/edgar/browse/?CIK=2488",
    },
    "TSM": {
        "cik": "1046179",
        "ir": "https://investor.tsmc.com/english",
        "sec": "https://www.sec.gov/edgar/browse/?CIK=1046179",
    },
    "ASML": {
        "cik": "937966",
        "ir": "https://www.asml.com/en/investors",
        "sec": "https://www.sec.gov/edgar/browse/?CIK=937966",
    },
    "MSFT": {
        "cik": "789019",
        "ir": "https://www.microsoft.com/en-us/Investor",
        "sec": "https://www.sec.gov/edgar/browse/?CIK=789019",
    },
    "GOOGL": {
        "cik": "1652044",
        "ir": "https://abc.xyz/investor/",
        "sec": "https://www.sec.gov/edgar/browse/?CIK=1652044",
    },
    "XOM": {
        "cik": "34088",
        "ir": "https://investor.exxonmobil.com/",
        "sec": "https://www.sec.gov/edgar/browse/?CIK=34088",
    },
    "SHEL": {
        "cik": "1306965",
        "ir": "https://www.shell.com/investors.html",
        "sec": "https://www.sec.gov/edgar/browse/?CIK=1306965",
    },
    "ZIM": {
        "cik": "1654126",
        "ir": "https://investors.zim.com/",
        "sec": "https://www.sec.gov/edgar/browse/?CIK=1654126",
    },
}


def build_company_verification_sources(company: dict) -> list[dict]:
    symbol = str(company.get("symbol", "")).upper()
    name = company.get("name", symbol)
    overrides = COMPANY_SOURCE_OVERRIDES.get(symbol, {})
    sources = []

    if overrides.get("ir"):
        sources.append(
            {
                "label": f"{name} Investor Relations",
                "type": "company_ir",
                "priority": "high",
                "url": overrides["ir"],
                "use_for": "核对财报、电话会材料、新闻稿和投资者演示。",
            }
        )

    if overrides.get("sec"):
        sources.append(
            {
                "label": f"{symbol} SEC filings",
                "type": "regulatory_filing",
                "priority": "high",
                "url": overrides["sec"],
                "use_for": "核对10-K、10-Q、8-K、20-F等监管披露。",
            }
        )

    if symbol:
        sources.append(
            {
                "label": f"{symbol} Yahoo Finance",
                "type": "market_quote",
                "priority": "medium",
                "url": f"https://finance.yahoo.com/quote/{symbol}",
                "use_for": "核对价格、成交和市场摘要，不能替代公告原文。",
            }
        )

    return sources


def get_company_cik(company: dict) -> str:
    symbol = str(company.get("symbol", "")).upper()
    return str(COMPANY_SOURCE_OVERRIDES.get(symbol, {}).get("cik", ""))

