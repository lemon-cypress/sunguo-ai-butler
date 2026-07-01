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
    "gdelt": "GDELT",
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
