from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


def env_text(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def load_env_file(path: Path = ENV_FILE) -> None:
    """Load simple KEY=VALUE pairs from .env without third-party packages."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    ai_provider: str
    openai_api_key: str
    openai_model: str
    deepseek_api_key: str
    deepseek_model: str
    alphavantage_api_key: str
    marketaux_api_key: str
    finnhub_api_key: str
    polygon_api_key: str
    newsapi_api_key: str
    default_city: str
    weather_latitude: float
    weather_longitude: float
    weather_timeout_seconds: int
    weather_retries: int
    use_real_weather: bool
    weather_provider: str
    outlook_feature_enabled: bool
    use_real_outlook: bool
    microsoft_client_id: str
    microsoft_tenant: str
    microsoft_scopes: str
    microsoft_token_path: Path
    local_schedule_path: Path
    use_real_markets: bool
    market_provider: str
    market_symbols_path: Path
    use_real_news: bool
    news_provider: str
    news_feeds_path: Path
    news_max_records_per_query: int
    use_real_themes: bool
    theme_provider: str
    theme_symbols_path: Path
    use_real_companies: bool
    company_provider: str
    company_watchlist_path: Path
    company_news_max_records: int
    company_max_count: int
    company_timeout_seconds: int
    user_profile_path: Path
    timezone: str


def get_settings() -> Settings:
    load_env_file()
    return Settings(
        ai_provider=env_text("AI_PROVIDER", "deepseek").lower(),
        openai_api_key=env_text("OPENAI_API_KEY"),
        openai_model=env_text("OPENAI_MODEL", "gpt-5.5"),
        deepseek_api_key=env_text("DEEPSEEK_API_KEY"),
        deepseek_model=env_text("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        alphavantage_api_key=env_text("ALPHAVANTAGE_API_KEY"),
        marketaux_api_key=env_text("MARKETAUX_API_KEY"),
        finnhub_api_key=env_text("FINNHUB_API_KEY"),
        polygon_api_key=env_text("POLYGON_API_KEY"),
        newsapi_api_key=env_text("NEWSAPI_API_KEY"),
        default_city=env_text("DEFAULT_CITY", "北京-朝阳"),
        weather_latitude=float(env_text("WEATHER_LATITUDE", "39.9219")),
        weather_longitude=float(env_text("WEATHER_LONGITUDE", "116.4433")),
        weather_timeout_seconds=int(env_text("WEATHER_TIMEOUT_SECONDS", "30")),
        weather_retries=int(env_text("WEATHER_RETRIES", "2")),
        use_real_weather=env_text("USE_REAL_WEATHER", "true").lower() in {"1", "true", "yes", "on"},
        weather_provider=env_text("WEATHER_PROVIDER", "open_meteo").lower(),
        outlook_feature_enabled=env_text("OUTLOOK_FEATURE_ENABLED", "false").lower() in {"1", "true", "yes", "on"},
        use_real_outlook=env_text("USE_REAL_OUTLOOK", "false").lower() in {"1", "true", "yes", "on"},
        microsoft_client_id=env_text("MICROSOFT_CLIENT_ID"),
        microsoft_tenant=env_text("MICROSOFT_TENANT", "common"),
        microsoft_scopes=env_text(
            "MICROSOFT_SCOPES",
            "offline_access User.Read Calendars.ReadWrite",
        ),
        microsoft_token_path=PROJECT_ROOT / env_text(
            "MICROSOFT_TOKEN_PATH",
            "backend/data/ms_graph_token.json",
        ),
        local_schedule_path=PROJECT_ROOT / env_text(
            "LOCAL_SCHEDULE_PATH",
            "backend/data/local_schedule.json",
        ),
        use_real_markets=env_text("USE_REAL_MARKETS", "true").lower() in {"1", "true", "yes", "on"},
        market_provider=env_text("MARKET_PROVIDER", "yahoo").lower(),
        market_symbols_path=PROJECT_ROOT / env_text(
            "MARKET_SYMBOLS_PATH",
            "backend/data/market_symbols.json",
        ),
        use_real_news=env_text("USE_REAL_NEWS", "true").lower() in {"1", "true", "yes", "on"},
        news_provider=env_text("NEWS_PROVIDER", "rss").lower(),
        news_feeds_path=PROJECT_ROOT / env_text(
            "NEWS_FEEDS_PATH",
            "backend/data/news_feeds.json",
        ),
        news_max_records_per_query=int(env_text("NEWS_MAX_RECORDS_PER_QUERY", "5")),
        use_real_themes=env_text("USE_REAL_THEMES", "true").lower() in {"1", "true", "yes", "on"},
        theme_provider=env_text("THEME_PROVIDER", "yahoo").lower(),
        theme_symbols_path=PROJECT_ROOT / env_text(
            "THEME_SYMBOLS_PATH",
            "backend/data/theme_symbols.json",
        ),
        use_real_companies=env_text("USE_REAL_COMPANIES", "true").lower() in {"1", "true", "yes", "on"},
        company_provider=env_text("COMPANY_PROVIDER", "watchlist").lower(),
        company_watchlist_path=PROJECT_ROOT / env_text(
            "COMPANY_WATCHLIST_PATH",
            "backend/data/company_watchlist.json",
        ),
        company_news_max_records=int(env_text("COMPANY_NEWS_MAX_RECORDS", "2")),
        company_max_count=int(env_text("COMPANY_MAX_COUNT", "5")),
        company_timeout_seconds=int(env_text("COMPANY_TIMEOUT_SECONDS", "10")),
        user_profile_path=PROJECT_ROOT / env_text(
            "USER_PROFILE_PATH",
            "backend/data/user_profile.json",
        ),
        timezone=env_text("TIMEZONE", "Asia/Shanghai"),
    )
