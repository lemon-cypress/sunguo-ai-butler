from __future__ import annotations


SUPPORTED_WEATHER_PROVIDERS = {
    "open_meteo": "Open-Meteo",
}

SUPPORTED_MARKET_PROVIDERS = {
    "yahoo": "Yahoo Finance chart",
    "alphavantage": "Alpha Vantage",
    "finnhub": "Finnhub",
    "polygon": "Polygon / Massive",
}

SUPPORTED_NEWS_PROVIDERS = {
    "rss": "RSS",
    "marketaux": "Marketaux",
    "newsapi": "NewsAPI",
    "finnhub": "Finnhub",
    "gdelt": "GDELT",
    "combined": "Marketaux + NewsAPI + Finnhub + X leads + GDELT + RSS",
}

SUPPORTED_ECONOMIC_CALENDAR_PROVIDERS = {
    "nasdaq": "Nasdaq economic calendar",
}

SUPPORTED_CHINA_MARKET_PROVIDERS = {
    "eastmoney": "Eastmoney public quote",
}

SUPPORTED_STRUCTURED_MARKET_PROVIDERS = {
    "touzid": "Touzid open API",
}

SUPPORTED_THEME_PROVIDERS = {
    "yahoo": "Yahoo Finance chart",
    "alphavantage": "Alpha Vantage",
}

SUPPORTED_COMPANY_PROVIDERS = {
    "watchlist": "Watchlist + Yahoo + Google News RSS + SEC",
    "marketaux": "Marketaux",
    "finnhub": "Finnhub",
}


def unsupported_provider_message(kind: str, provider: str, supported: dict[str, str]) -> str:
    supported_names = ", ".join(sorted(supported))
    return f"{kind} provider '{provider}' is not available. Supported values: {supported_names}."
