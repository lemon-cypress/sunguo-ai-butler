from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

BEIJING_TZ = timezone(timedelta(hours=8))

CATEGORY_KEYWORDS = [
    ("中国市场", ["china", "chinese", "hong kong", "上证", "深证", "沪深", "恒生", "中国", "香港", "a股"]),
    ("全球市场与宏观", ["fed", "rate", "inflation", "treasury", "dollar", "nasdaq", "s&p", "dow", "央行", "利率", "通胀", "美元", "美债", "指数"]),
    ("政策、监管与地缘", ["tariff", "sanction", "election", "war", "military", "ceasefire", "policy", "regulator", "关税", "制裁", "选举", "军事", "冲突", "监管", "政策"]),
    ("科技与产业", ["ai", "chip", "semiconductor", "nvidia", "amd", "tsmc", "asml", "robot", "data center", "芯片", "半导体", "人工智能", "算力", "机器人"]),
    ("公司与资本运作", ["earnings", "revenue", "profit", "guidance", "merger", "acquisition", "ipo", "财报", "收入", "利润", "并购", "上市", "回购"]),
    ("大宗商品、能源与供应链", ["oil", "copper", "gold", "gas", "opec", "shipping", "原油", "黄金", "铜", "天然气", "航运", "能源"]),
]

HIGH_IMPACT_KEYWORDS = [
    "fed", "rate", "inflation", "tariff", "sanction", "war", "military", "election",
    "earnings", "guidance", "revenue", "profit", "ai", "chip", "semiconductor",
    "oil", "copper", "gold", "央行", "利率", "通胀", "关税", "制裁", "军事", "冲突",
    "财报", "业绩", "收入", "利润", "指引", "人工智能", "芯片", "半导体", "原油", "黄金",
]

TRUSTED_SOURCE_MARKERS = [
    "sec.gov", "reuters.com", "bloomberg.com", "wsj.com", "ft.com", "cnbc.com",
    "prnewswire.com", "businesswire.com", "globenewswire.com",
]


def build_event_timeline(brief: dict, hours: int = 24, max_events: int = 24) -> dict:
    events = collect_events(brief)
    cutoff = datetime.now(BEIJING_TZ) - timedelta(hours=hours)
    scored = []
    for event in events:
        event_time = event_datetime(event)
        if event_time and event_time < cutoff:
            continue
        score = score_event(event)
        if score <= 0:
            continue
        scored.append({**event, "score": score})

    scored.sort(key=lambda item: (item.get("score", 0), event_datetime(item) or datetime.min.replace(tzinfo=BEIJING_TZ)), reverse=True)
    selected = sorted(scored[:max_events], key=lambda item: event_datetime(item) or datetime.max.replace(tzinfo=BEIJING_TZ), reverse=True)
    if not selected:
        selected = build_fallback_events(brief)[:max_events]

    return {
        "version": "event-timeline-v1",
        "window_hours": hours,
        "events": [normalize_event(event) for event in selected],
        "category_counts": count_categories(selected),
    }


def build_fallback_events(brief: dict) -> list[dict]:
    market = brief.get("market_data", {}) or {}
    indices = market.get("indices", []) or []
    news_data = brief.get("news_data", {}) or {}
    categories = news_data.get("categories", []) or []

    events: list[dict] = []
    if indices:
        mover = max(indices, key=lambda item: abs(percent_value(item.get("change_percent_from_previous_close")) or 0))
        name = mover.get("name") or mover.get("symbol") or "主要指数"
        region = mover.get("region") or "市场"
        change = percent_value(mover.get("change_percent_from_previous_close"))
        direction_text = direction(change) if change is not None else "有变化"
        events.append({
            "title": f"{region}{name}{direction_text}，先核验是否代表整体风险偏好变化",
            "time": timestamp_time(mover.get("market_time")),
            "time_sort": timestamp_datetime(mover.get("market_time")),
            "category": classify_category(f"{region} {name}"),
            "subject": f"{region}市场",
            "summary": "当前可用信息更像价格线索，下一步要把指数、利率、汇率和行业表现放在一起看。",
            "impact": "指数、行业风格、风险偏好",
            "verification": "核验主要指数是否同向，成交量是否放大，以及政策或宏观变量是否支持。",
            "confidence": "线索",
            "kind": "fallback-market",
            "score": 1,
        })

    for category in categories[:2]:
        articles = category.get("articles", []) or []
        article = next((item for item in articles if clean_text(item.get("title"))), None)
        if not article:
            continue
        title = clean_text(article.get("title"))
        events.append({
            "title": f"{compress(title)}需要先进入观察清单",
            "time": iso_time(article.get("published")),
            "time_sort": iso_datetime(article.get("published")),
            "category": classify_category(title, category.get("label") or category.get("category") or ""),
            "subject": category.get("label") or category.get("category") or "新闻",
            "summary": "这条信息暂时只作为线索，不能直接当成结论；需要看是否有主流报道或官方披露交叉验证。",
            "impact": infer_impact(title),
            "verification": "回到原始报道、官方披露或后续价格反应核验。",
            "confidence": article.get("confidence") or "线索",
            "source_url": article.get("url", ""),
            "kind": "fallback-news",
            "score": 1,
        })

    return dedupe_events(events)


def collect_events(brief: dict) -> list[dict]:
    events: list[dict] = []
    events.extend(collect_news_events(brief.get("news_data", {}) or {}))
    events.extend(collect_company_events(brief.get("company_data", {}) or {}))
    events.extend(collect_market_events(brief.get("market_data", {}) or {}))
    events.extend(collect_theme_events(brief.get("theme_data", {}) or {}))
    return dedupe_events(events)


def collect_news_events(news_data: dict) -> list[dict]:
    events = []
    for category in news_data.get("categories", []) or []:
        label = category.get("label") or category.get("category") or "新闻"
        for article in category.get("articles", []) or []:
            title = clean_text(article.get("title"))
            if not title:
                continue
            events.append({
                "title": title,
                "time": iso_time(article.get("published")),
                "time_sort": iso_datetime(article.get("published")),
                "category": classify_category(title, label),
                "subject": label,
                "summary": build_article_summary(article),
                "impact": infer_impact(title),
                "verification": article.get("verification_hint") or "先回到原始报道或官方披露核验，不把标题直接当作结论。",
                "confidence": article.get("confidence") or source_confidence(article.get("url", "")),
                "source_url": article.get("url", ""),
                "kind": "news",
            })
    return events


def collect_company_events(company_data: dict) -> list[dict]:
    events = []
    for item in company_data.get("items", []) or []:
        company = item.get("name") or item.get("symbol") or "重点公司"
        quote = item.get("quote") or {}
        change = percent_value(quote.get("change_percent_from_previous_close"))
        if change is not None and abs(change) >= 2:
            events.append({
                "title": f"{company}股价{direction(change)}，需要核验公司层面的原因",
                "time": timestamp_time(quote.get("market_time")),
                "time_sort": timestamp_datetime(quote.get("market_time")),
                "category": "公司与资本运作",
                "subject": company,
                "summary": f"较前收盘 {change:.2f}%。单日价格变化只是线索，不能直接等同于基本面变化。",
                "impact": item.get("sector") or "公司观察池",
                "verification": "回到公告、财报、电话会和管理层指引核验。",
                "confidence": "线索",
                "kind": "company-price",
            })
        for article in item.get("articles", []) or []:
            title = clean_text(article.get("title"))
            if not title:
                continue
            events.append({
                "title": f"{company}出现公司新闻线索：{compress(title)}",
                "time": iso_time(article.get("published")),
                "time_sort": iso_datetime(article.get("published")),
                "category": "公司与资本运作",
                "subject": company,
                "summary": "这类线索要判断是否影响收入、利润率、订单、资本开支或估值预期。",
                "impact": item.get("sector") or "公司观察池",
                "verification": article.get("verification_hint") or "回到公司公告、监管披露或IR原文核验。",
                "confidence": article.get("confidence") or source_confidence(article.get("url", "")),
                "source_url": article.get("url", ""),
                "kind": "company-news",
            })
    return events


def collect_market_events(market_data: dict) -> list[dict]:
    events = []
    for item in market_data.get("indices", []) or []:
        change = percent_value(item.get("change_percent_from_previous_close") or item.get("change_percent_from_open"))
        if change is None or abs(change) < 0.8:
            continue
        region = item.get("region") or "市场"
        name = item.get("name") or item.get("symbol") or "主要指数"
        events.append({
            "title": f"{region}{name}{direction(change)}，观察风险偏好是否扩散",
            "time": timestamp_time(item.get("market_time")),
            "time_sort": timestamp_datetime(item.get("market_time")),
            "category": classify_category(f"{region} {name}"),
            "subject": f"{region}市场",
            "summary": f"较前收盘 {change:.2f}%。指数变化需要和利率、汇率、行业表现一起看。",
            "impact": "指数、行业风格、风险偏好",
            "verification": "核验同一区域的行业分化、成交量和宏观变量是否同向。",
            "confidence": "中",
            "kind": "market-price",
        })
    return events


def collect_theme_events(theme_data: dict) -> list[dict]:
    events = []
    for item in theme_data.get("items", []) or []:
        change = percent_value(item.get("change_percent_from_previous_close"))
        if change is None or abs(change) < 1.5:
            continue
        theme = item.get("theme") or item.get("name") or "主题"
        name = item.get("name") or item.get("symbol") or theme
        events.append({
            "title": f"{theme}方向{name}{direction(change)}，检查产业链传导",
            "time": timestamp_time(item.get("market_time")),
            "time_sort": timestamp_datetime(item.get("market_time")),
            "category": classify_category(f"{theme} {name}"),
            "subject": theme,
            "summary": f"较前收盘 {change:.2f}%。主题价格变化要回到供需、库存、订单和政策验证。",
            "impact": ", ".join(item.get("affected_industries", []) or [theme]),
            "verification": "核验同主题多环节是否共振，避免只看单个标的。",
            "confidence": "中",
            "kind": "theme-price",
        })
    return events


def score_event(event: dict) -> int:
    text = f"{event.get('title', '')} {event.get('summary', '')} {event.get('subject', '')}".lower()
    score = 0
    if event.get("time"):
        score += 2
    if event.get("category") in {"全球市场与宏观", "政策、监管与地缘", "科技与产业", "公司与资本运作"}:
        score += 2
    if any(keyword.lower() in text for keyword in HIGH_IMPACT_KEYWORDS):
        score += 3
    if event.get("confidence") in {"高", "中"}:
        score += 1
    if any(marker in str(event.get("source_url", "")).lower() for marker in TRUSTED_SOURCE_MARKERS):
        score += 2
    if len(clean_text(event.get("title"))) < 8:
        score -= 2
    if "mock" in text:
        score -= 4
    return score


def normalize_event(event: dict) -> dict:
    return {
        "time": event.get("time", ""),
        "category": event.get("category", "今日观察"),
        "subject": event.get("subject", ""),
        "title": clean_text(event.get("title")),
        "summary": clean_text(event.get("summary")),
        "impact": clean_text(event.get("impact")),
        "verification": clean_text(event.get("verification")),
        "confidence": event.get("confidence", "线索"),
        "score": event.get("score", 0),
    }


def count_categories(events: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for event in events:
        category = event.get("category", "今日观察")
        counts[category] = counts.get(category, 0) + 1
    return counts


def dedupe_events(events: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for event in events:
        key = compress(clean_text(event.get("title", "")).lower(), 80)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(event)
    return result


def classify_category(text: Any, fallback: str = "") -> str:
    haystack = f"{text or ''} {fallback or ''}".lower()
    for category, keywords in CATEGORY_KEYWORDS:
        if any(keyword.lower() in haystack for keyword in keywords):
            return category
    return fallback if fallback in [item[0] for item in CATEGORY_KEYWORDS] else "今日观察"


def infer_impact(title: str) -> str:
    category = classify_category(title)
    mapping = {
        "中国市场": "A股、港股、人民币、政策预期",
        "全球市场与宏观": "利率、美元、股债商品、风险偏好",
        "政策、监管与地缘": "能源、航运、军工、跨境贸易、汇率",
        "科技与产业": "AI、半导体、云计算、设备材料、成长股",
        "公司与资本运作": "公司盈利、估值、行业竞争格局",
        "大宗商品、能源与供应链": "通胀、成本、资源品、制造业利润率",
    }
    return mapping.get(category, "市场情绪、行业主题或今日观察清单")


def build_article_summary(article: dict) -> str:
    labels = article.get("event_labels") or []
    if labels:
        return f"这条线索涉及{'、'.join(labels[:3])}，需要判断它是否会传导到资产价格、行业景气或公司盈利。"
    return "这条线索先进入观察清单，重点看是否能被官方信息、价格变化或公司公告交叉验证。"


def source_confidence(url: str) -> str:
    lower = str(url or "").lower()
    if "sec.gov" in lower:
        return "高"
    if any(marker in lower for marker in TRUSTED_SOURCE_MARKERS):
        return "中"
    return "线索"


def event_datetime(event: dict) -> datetime | None:
    value = event.get("time_sort")
    return value if isinstance(value, datetime) else None


def iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).astimezone(BEIJING_TZ)
    except ValueError:
        return None


def iso_time(value: str | None) -> str:
    dt = iso_datetime(value)
    return dt.strftime("%m-%d %H:%M") if dt else ""


def timestamp_datetime(value: int | float | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).astimezone(BEIJING_TZ)


def timestamp_time(value: int | float | None) -> str:
    dt = timestamp_datetime(value)
    return dt.strftime("%m-%d %H:%M") if dt else ""


def percent_value(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def direction(value: float) -> str:
    if value > 0:
        return "走强"
    if value < 0:
        return "回落"
    return "基本持平"


def compress(text: str, limit: int = 54) -> str:
    value = clean_text(text)
    if len(value) <= limit:
        return value
    return f"{value[:limit]}..."


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").replace("\n", " ").split())
