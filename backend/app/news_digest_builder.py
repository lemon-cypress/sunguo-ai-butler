from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha1
from typing import Any
import re


BEIJING_TZ = timezone(timedelta(hours=8))


def zh(text: str) -> str:
    return text.encode("ascii").decode("unicode_escape")


MACRO = zh("\\u5b8f\\u89c2\\u7ecf\\u6d4e")
PROPERTY = zh("\\u5730\\u4ea7\\u52a8\\u6001")
MARKET = zh("\\u80a1\\u5e02\\u76d8\\u70b9")
INDUSTRY = zh("\\u884c\\u4e1a\\u89c2\\u5bdf")
COMPANY = zh("\\u516c\\u53f8\\u8981\\u95fb")
GLOBAL = zh("\\u73af\\u7403\\u89c6\\u91ce")
FINANCE = zh("\\u91d1\\u878d\\u6570\\u636e")

SECTION_ORDER = [MACRO, PROPERTY, MARKET, INDUSTRY, COMPANY, GLOBAL, FINANCE]

SECTION_KEYWORDS = {
    MACRO: [
        "cpi", "ppi", "inflation", "rate", "fed", "central bank", "treasury", "yield",
        "gdp", "pmi", "tariff", "imf", "world bank", "budget", "deficit", "jobs",
        "unemployment", "trade balance", "trade deficit", "export", "import", "tax", "customs",
    ],
    PROPERTY: [
        "real estate", "property", "housing", "mortgage", "home sales", "developer",
        "land sale", "rent", "office vacancy", "reit",
    ],
    MARKET: [
        "stock", "stocks", "market", "index", "s&p", "nasdaq", "dow", "dax", "nikkei",
        "kospi", "hang seng", "shares", "etf", "ipo", "equity", "rally", "selloff",
    ],
    INDUSTRY: [
        "ai", "semiconductor", "chip", "robot", "data center", "cloud", "ev", "battery",
        "energy", "solar", "pharma", "biotech", "shipping", "oil", "gas", "copper",
        "manufacturing", "supply chain", "rare earth", "export controls",
    ],
    COMPANY: [
        "earnings", "revenue", "profit", "guidance", "buyback", "merger", "acquisition",
        "sec", "filing", "lawsuit", "investigation", "appointment", "resignation",
        "dividend", "forecast", "shares surge", "shares fall",
    ],
    GLOBAL: [
        "war", "military", "sanction", "election", "ukraine", "israel", "iran", "russia",
        "shipping lane", "strait", "geopolitics", "policy", "minister", "president",
        "export controls", "customs", "security",
    ],
    FINANCE: [
        "oil", "gold", "copper", "dollar", "bond", "treasury", "yield", "shibor",
        "currency", "fx", "renminbi", "yuan", "rate", "commodity",
    ],
}

HIGH_SIGNAL_KEYWORDS = set().union(*[set(v) for v in SECTION_KEYWORDS.values()])

LOW_VALUE_PATTERNS = [
    "best states to live", "worst states to live", "portable shower", "funflation",
    "weight loss", "celebrity", "sports", "lottery", "dating", "recipe", "travel tips",
    "what to watch", "streaming", "movie", "netflix", "hulu", "disney", "weather forecast",
    "assassin's creed", "game", "dinosaur", "tiny repairs", "shower", "filthy enough",
    "crime drama", "season finale", "box office", "music festival",
    "ice are heavily armed", "opinion", "commentary", "worth the", "how to", "why i prefer",
    "could yield big returns", "undervalued", "safe double-digit dividend", "stock:", "warrants upgrade",
    "appeared company news clue", "subpoenas new york times journalists", "journalists subpoenaed",
    "air force one reporting", "electric pickup truck is like in person",
    "ahead of market", "things that will decide", "what happened before",
    "how aldi is taking", "ex-lawmaker", "detained by armed settlers",
    "fair value", "simplywall", "zacks", "stock analysis", "price target",
    "rosen, a globally respected law firm", "class action investigation", "24/7 wall st.",
    "ea worldview", "drawing crowds", "here's why the world is watching",
    # Social-media arguments and personality disputes are weak morning-brief
    # material unless accompanied by an official filing or a measurable
    # business event. They were previously slipping through via "lawsuit".
    "on x", "x platform", "twitter feud", "argue on x", "argument on x",
    "spar on x", "clash on x", "social media spat", "war of words",
    "dies aged", "died aged", "has died", "death of", "obituary",
]

PREVIEW_PATTERNS = [
    "ahead of market", "things that will decide", "what to watch", "will now track",
    "investors will now track", "preview", "look ahead",
]

SECTION_REQUIRED_PATTERNS = {
    MACRO: [
        "cpi", "ppi", "inflation", "fed", "central bank", "treasury", "yield",
        "gdp", "pmi", "tariff", "trade deficit", "trade balance", "jobs",
        "unemployment", "budget", "deficit", "customs", "imf", "world bank",
    ],
    PROPERTY: [
        "real estate", "property", "housing", "mortgage", "home sales", "developer",
        "land sale", "rent", "office vacancy", "reit",
    ],
    MARKET: [
        "stock", "stocks", "market", "index", "s&p", "nasdaq", "dow", "dax", "nikkei",
        "kospi", "hang seng", "shares", "etf", "ipo", "equity", "rally", "selloff",
        "berkshire", "retail traders",
    ],
    INDUSTRY: [
        "ai", "semiconductor", "chip", "robot", "data center", "cloud", "ev", "battery",
        "energy", "solar", "pharma", "biotech", "shipping", "oil", "gas", "copper",
        "manufacturing", "supply chain", "rare earth", "export controls", "memory supply",
    ],
    COMPANY: [
        "earnings", "revenue", "profit", "guidance", "buyback", "merger", "acquisition",
        "sec", "filing", "lawsuit", "investigation", "appointment", "resignation",
        "dividend", "forecast", "trade secret", "sues", "layoffs",
    ],
    GLOBAL: [
        "war", "military", "sanction", "election", "ukraine", "israel", "iran", "russia",
        "shipping lane", "strait", "geopolitics", "policy", "minister", "president",
        "export controls", "customs", "security", "blacklist", "china-us",
    ],
    FINANCE: [
        "oil", "gold", "copper", "dollar", "bond", "treasury", "yield", "shibor",
        "currency", "fx", "renminbi", "yuan", "rate", "commodity",
    ],
}

FORCE_COMPANY_PATTERNS = ["trade secret", "lawsuit", "sues", "earnings", "revenue", "profit", "guidance"]
FORCE_GLOBAL_PATTERNS = [
    "sanction", "blacklist", "export controls", "iran", "ukraine", "israel", "russia",
    "china-us", "airstrike", "military", "hormuz", "container ship", "west bank",
]

TRUSTED_DOMAINS = [
    "reuters.com", "bloomberg.com", "wsj.com", "ft.com", "cnbc.com", "apnews.com",
    "bbc.co.uk", "nytimes.com", "lemonde.fr", "scmp.com", "theverge.com",
    "sec.gov", "hkexnews.hk", "sse.com.cn", "szse.cn", "pbc.gov.cn", "mof.gov.cn",
    "stats.gov.cn", "ndrc.gov.cn", "csrc.gov.cn", "mofcom.gov.cn", "customs.gov.cn",
    "gov.cn", "cninfo.com.cn", "hkex.com.hk", "cs.com.cn", "stcn.com", "cls.cn",
    "caixin.com", "yicai.com", "cnstock.com", "21jingji.com", "nbd.com.cn",
    "thepaper.cn", "eeo.com.cn", "xinhuanet.com", "chinanews.com.cn", "people.com.cn",
    "eastmoney.com", "jrj.com.cn", "10jqka.com.cn", "bjnews.com.cn", "36kr.com",
    "jiemian.com", "ofweek.com", "c114.com.cn", "tmtpost.com",
    "federalreserve.gov", "ecb.europa.eu",
]

# Recognised public-interest and business newsrooms.  These stories are useful
# reading even when a syndication feed only retains a title, so they should not
# be discarded merely because a short RSS description contains no figures.
MAJOR_MEDIA_MARKERS = [
    "reuters", "bloomberg", "wsj", "financial times", "ft.com", "cnbc", "ap news", "bbc",
    "new york times", "nytimes", "caixin", "财新", "yicai", "第一财经", "证券时报",
    "中国证券报", "上海证券报", "21世纪", "经济观察", "澎湃", "新华社", "中国新闻网",
    "人民日报", "新京报", "界面新闻", "东方财富", "36氪", "财联社", "thepaper",
]

# The pool can contain a lot of useful clues, but an editorial brief must lead
# with primary disclosures and reports that contain concrete, checkable facts.
SOURCE_CONFIDENCE_SCORES = {
    "high": 5,
    "medium": 3,
    "normal": 1,
    "lead": 0,
    "": 0,
}

HARD_EVENT_PATTERNS = [
    "earnings", "revenue", "profit", "guidance", "forecast", "order", "orders", "backlog",
    "capex", "capacity", "shipment", "inventory", "production", "factory", "plant", "data center",
    "investment", "funding", "fundraise", "valuation",
    "cpi", "ppi", "gdp", "pmi", "inflation", "rate", "yield", "tariff", "sanction",
    "export control", "blacklist", "merger", "acquisition", "buyback", "dividend",
    "sec", "filing", "regulator", "lawsuit", "sues", "recall", "layoff",
    "oil", "gold", "copper", "shipping", "container", "hormuz", "strike",
    "earthquake", "wildfire", "typhoon", "airstrike", "military",
    "政策", "发布", "出台", "数据", "统计", "监管", "公告", "财报", "业绩", "利润",
    "营收", "订单", "投资", "融资", "收购", "并购", "回购", "减持", "增持", "产能",
    "出口", "关税", "制裁", "芯片", "半导体", "人工智能", "算力", "新能源", "汽车",
]

TITLE_EVENT_VERBS = [
    "announces", "announced", "reports", "reported", "files", "filed", "raises", "raised",
    "cuts", "cut", "approves", "approved", "signs", "signed", "imposes", "imposed",
    "launches", "launched", "strikes", "struck", "attacks", "attacked", "withdraws",
    "withdrawn", "reaches", "reached", "agrees", "agreed", "buys", "acquires",
    "merger", "acquisition", "sanctions", "sanctioned", "sues", "lawsuit",
    "发布", "公布", "出台", "通过", "启动", "签署", "收购", "并购", "投资", "融资",
    "增持", "减持", "回购", "上调", "下调", "扩产", "投产", "落地", "回应",
]

NUMERIC_RE = re.compile(r"[-+]?\d+(?:\.\d+)?\s*(?:%|bp|bps|bn|billion|m|million|trillion|x|\\$)?", re.I)


def build_news_digest(brief: dict) -> dict:
    pool = build_news_pool(brief)
    ranked_pool = rank_news_pool(pool)
    # A news event often arrives through several wires with slightly different
    # section labels.  Cluster before the editorial gate so the reader sees a
    # single, best-supported event rather than the same Hormuz/earnings story
    # repeated across macro, market and global sections.
    clustered_pool = cluster_news_candidates(ranked_pool)
    editorial_pool = build_editorial_pool(clustered_pool)
    pool_audit = build_news_pool_audit(pool, ranked_pool, editorial_pool, len(clustered_pool))
    # The deterministic fallback uses the same editorial pool as the AI. This
    # prevents a temporary model/API outage from turning the page back into a
    # long list of ticker movements.
    sections = [section for section in build_sections(editorial_pool, brief) if section.get("items")]
    return {
        "version": "news-pool-digest-v3",
        "date": brief.get("date", ""),
        "city": brief.get("city", ""),
        "overview": build_overview(sections),
        "sections": sections,
        "news_pool": {
            "version": "news-pool-v3",
            "window_hours": 24,
            "total_candidates": len(pool),
            "ranked_candidates": len(ranked_pool),
            "clustered_candidates": len(clustered_pool),
            "editorial_candidates": len(editorial_pool),
            "source_counts": pool_audit["source_counts"],
            "stage_counts": pool_audit["stage_counts"],
            "rejection_reasons": pool_audit["rejection_reasons"],
            "editorial_rejection_reasons": pool_audit["editorial_rejection_reasons"],
            "diagnostics": pool_audit["diagnostics"],
            "top_candidates": [
                serialize_fact_card(item)
                for item in editorial_pool[:60]
            ],
            # Reader-selectable title list.  It deliberately keeps recognised
            # newsroom coverage that is relevant but too short for the main
            # fact-card digest, and always retains its original click-through.
            "media_candidates": [
                serialize_fact_card(item)
                for item in clustered_pool
                if is_major_media(item) and clean_text(item.get("url"))
            ][:100],
            # Kept for diagnostics and future review panels. The AI is not fed
            # these lower-confidence market-only clues as lead stories.
            "context_candidates": [serialize_fact_card(item) for item in ranked_pool[:20]],
        },
    }


def build_news_pool_audit(pool: list[dict], ranked_pool: list[dict], editorial_pool: list[dict], clustered_count: int | None = None) -> dict:
    """Explain in Chinese why the visible news count is high or low."""
    ranked_ids = {item.get("id") for item in ranked_pool}
    editorial_ids = {item.get("id") for item in editorial_pool}
    source_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    section_counts: dict[str, int] = {}
    confidence_counts: dict[str, int] = {}
    rejection_reasons: dict[str, int] = {}
    editorial_rejection_reasons: dict[str, int] = {}

    for item in pool:
        increment(source_counts, clean_text(item.get("source")) or "unknown")
        increment(kind_counts, clean_text(item.get("kind")) or "unknown")
        increment(section_counts, clean_text(item.get("section")) or "unknown")
        increment(confidence_counts, clean_text(item.get("source_confidence")) or "unknown")
        if item.get("id") not in ranked_ids:
            increment(rejection_reasons, relevance_rejection_reason(item))

    for item in ranked_pool:
        if item.get("id") not in editorial_ids:
            increment(editorial_rejection_reasons, editorial_rejection_reason(item))

    diagnostics = [
        f"原始候选 {len(pool)} 条，进入相关性排序 {len(ranked_pool)} 条，进入网页早报 {len(editorial_pool)} 条。",
        "网页只展示可信来源、硬事实和足够证据的条目；社媒、泛资讯、纯价格波动和缺少摘要的内容会留在候选池，不直接展示。",
    ]
    if source_counts:
        top_sources = sorted(source_counts.items(), key=lambda row: row[1], reverse=True)[:8]
        diagnostics.append("主要来源：" + "；".join(f"{name} {count}条" for name, count in top_sources))
    if rejection_reasons:
        top_reasons = sorted(rejection_reasons.items(), key=lambda row: row[1], reverse=True)[:5]
        diagnostics.append("相关性阶段主要过滤原因：" + "；".join(f"{reason} {count}条" for reason, count in top_reasons))
    if editorial_rejection_reasons:
        top_editorial_reasons = sorted(editorial_rejection_reasons.items(), key=lambda row: row[1], reverse=True)[:5]
        diagnostics.append("编辑精选阶段主要过滤原因：" + "；".join(f"{reason} {count}条" for reason, count in top_editorial_reasons))

    return {
        "source_counts": sorted_count_dict(source_counts),
        "kind_counts": sorted_count_dict(kind_counts),
        "section_counts": sorted_count_dict(section_counts),
        "confidence_counts": sorted_count_dict(confidence_counts),
        "stage_counts": {
            "raw": len(pool),
            "ranked": len(ranked_pool),
            "clustered": clustered_count if clustered_count is not None else len(ranked_pool),
            "editorial": len(editorial_pool),
        },
        "rejection_reasons": sorted_count_dict(rejection_reasons),
        "editorial_rejection_reasons": sorted_count_dict(editorial_rejection_reasons),
        "diagnostics": diagnostics,
    }


def relevance_rejection_reason(item: dict) -> str:
    text = " ".join([clean_text(item.get("title")), clean_text(item.get("summary")), clean_text(item.get("source"))]).lower()
    dt = parse_candidate_time(item)
    cutoff = datetime.now(BEIJING_TZ) - timedelta(hours=30)
    if dt and dt < cutoff:
        return "超过30小时窗口"
    if any(pattern in text for pattern in LOW_VALUE_PATTERNS):
        return "低价值或泛资讯"
    if is_non_material_global_event(text):
        return "地缘/冲突缺少经济传导"
    if item.get("kind") in {"article", "timeline", "company_news"} and any(pattern in text for pattern in PREVIEW_PATTERNS):
        return "预告类内容"
    natural_disaster_terms = ["typhoon", "wildfire", "earthquake", "flood", "evacuated"]
    material_link_terms = ["shipping", "oil", "energy", "factory", "supply chain", "export", "sanction", "hormuz"]
    if any(term in text for term in natural_disaster_terms) and not any(term in text for term in material_link_terms):
        return "灾害新闻缺少市场传导"
    if "military" in text and not any(term in text for term in ["sanction", "strike", "airstrike", "shipping", "hormuz", "oil", "export control"]):
        return "军事新闻缺少经济传导"
    raw_text = " ".join([clean_text(item.get("title")), clean_text(item.get("summary"))])
    if any(pattern in raw_text for pattern in [zh("\\u51fa\\u73b0\\u516c\\u53f8\\u65b0\\u95fb\\u7ebf\\u7d22"), zh("\\u8fd9\\u7c7b\\u7ebf\\u7d22\\u8981\\u5224\\u65ad")]):
        return "模板占位内容"
    headline_only_media = is_major_media(item) and has_material_headline(item)
    if item.get("kind") in {"article", "timeline", "company_news"} and not has_factual_signal(text) and not headline_only_media:
        return "缺少硬事实信号"
    if item.get("kind") in {"article", "timeline", "company_news"} and not has_enough_evidence(item) and not headline_only_media:
        return "证据不足或摘要过短"
    item = dict(item)
    item["section"] = corrected_section(item)
    if score_candidate(item) < 6:
        return "综合分低于阈值"
    return "其他相关性过滤"


def editorial_rejection_reason(item: dict) -> str:
    kind = item.get("kind")
    if kind in {"market", "china_market", "company_price"}:
        return "纯行情或价格波动"
    if kind in {"article", "timeline", "company_news"} and not is_trusted(item):
        return "非可信来源，仅作线索"
    text = " ".join([clean_text(item.get("title")), clean_text(item.get("summary"))]).lower()
    if is_non_material_global_event(text):
        return "地缘事件缺少经济传导"
    if not any(pattern in text for pattern in HARD_EVENT_PATTERNS):
        return "缺少公告/财报/政策/供需等硬事件"
    if item.get("section") == COMPANY and not is_material_company_event(item, text):
        return "公司新闻缺少经营事实"
    facts = item.get("facts") or []
    if len(facts) < 2 and len(clean_text(item.get("summary"))) < 120:
        return "事实数量或摘要长度不足"
    return "编辑精选过滤"


def increment(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def sorted_count_dict(counter: dict[str, int]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda row: row[1], reverse=True))


def serialize_fact_card(item: dict) -> dict:
    return {
        "id": item["id"],
        "event_key": item.get("event_key", ""),
        "time": item.get("time", ""),
        "section": item.get("section", ""),
        "title": item.get("title", ""),
        "summary": item.get("summary", ""),
        "facts": item.get("facts", []),
        "source": item.get("source", ""),
        "source_confidence": item.get("source_confidence", ""),
        "url": item.get("url", ""),
        "score": item.get("score", 0),
        "importance_score": item.get("importance_score", item.get("score", 0)),
        "cluster_id": item.get("cluster_id", ""),
        "cluster_size": item.get("cluster_size", 1),
        "cluster_sources": item.get("cluster_sources", []),
        "kind": item.get("kind", ""),
    }


def build_editorial_pool(ranked_pool: list[dict]) -> list[dict]:
    """Return only reader-worthy facts; quiet days should stay short."""
    return [item for item in ranked_pool if is_editorial_fact_card(item)]


def is_editorial_fact_card(item: dict) -> bool:
    kind = item.get("kind")
    if kind in {"economic_calendar", "a_share_announcement", "a_share_financial", "a_share_supervision", "a_share_industry", "a_share_index_valuation", "company_filing"}:
        return True
    if kind in {"market", "china_market", "company_price"}:
        return False
    if kind in {"article", "timeline", "company_news"} and not is_trusted(item):
        # Discovery feeds may point to a useful story, but visible facts must
        # come from a recognised newsroom or an official disclosure.
        return False
    text = " ".join([clean_text(item.get("title")), clean_text(item.get("summary"))]).lower()
    facts = item.get("facts") or []
    if is_disallowed_visible_story(item, text):
        return False
    if is_non_material_global_event(text):
        return False
    headline_only_media = is_major_media(item) and has_material_headline(item)
    if not any(pattern in text for pattern in HARD_EVENT_PATTERNS) and not headline_only_media:
        return False
    if item.get("section") == COMPANY and not is_material_company_event(item, text) and not headline_only_media:
        return False
    if len(facts) >= 2 or len(clean_text(item.get("summary"))) >= 90:
        return True
    if headline_only_media:
        return True
    return (
        is_trusted(item)
        and clean_text(item.get("source_confidence")).lower() in {"high", "medium"}
        and len(clean_text(item.get("title"))) >= 28
        and (
            any(verb in clean_text(item.get("title")).lower() for verb in TITLE_EVENT_VERBS)
            or any(pattern in text for pattern in HARD_EVENT_PATTERNS)
        )
    )


def is_major_media(item: dict) -> bool:
    text = " ".join([
        clean_text(item.get("source")),
        clean_text(item.get("source_domain")),
        clean_text(item.get("url")),
    ]).lower()
    return any(marker in text for marker in MAJOR_MEDIA_MARKERS) or is_trusted(item)


def has_material_headline(item: dict) -> bool:
    """A credible title can be a valid optional-reading clue without numbers."""
    title = clean_text(item.get("title"))
    text = f"{title} {clean_text(item.get('summary'))}".lower()
    if len(title) < 12:
        return False
    return (
        any(pattern in text for pattern in HARD_EVENT_PATTERNS)
        or any(verb in title.lower() for verb in TITLE_EVENT_VERBS)
        or any(keyword in text for keyword in HIGH_SIGNAL_KEYWORDS)
    )


def is_non_material_global_event(text: str) -> bool:
    """Keep conflict coverage only when it has a real economic transmission."""
    conflict_terms = ["iran", "israel", "ukraine", "russia", "airstrike", "military", "ceasefire", "strike"]
    transmission_terms = [
        "sanction", "tariff", "shipping", "container", "hormuz", "strait", "oil",
        "energy", "gas", "export", "blacklist", "supply chain", "port",
        "trade policy", "trade route", "trade restriction", "trade blockade",
    ]
    return any(term in text for term in conflict_terms) and not any(term in text for term in transmission_terms)


def is_material_company_event(item: dict, text: str) -> bool:
    """Company rows need a business fact, not a personality or legal headline."""
    business_terms = [
        "earnings", "revenue", "profit", "guidance", "forecast", "order", "backlog",
        "capex", "capacity", "shipment", "inventory", "production", "factory", "plant",
        "merger", "acquisition", "buyback", "dividend", "filing", "sec", "recall",
        "layoff", "regulator", "antitrust",
    ]
    if not any(term in text for term in business_terms):
        return False
    if item.get("kind") == "company_filing":
        return True
    return (
        len(item.get("facts") or []) >= 2
        or len(clean_text(item.get("summary"))) >= 80
        or (
            is_trusted(item)
            and clean_text(item.get("source_confidence")).lower() in {"high", "medium"}
            and len(clean_text(item.get("summary"))) >= 45
        )
    )


def is_disallowed_visible_story(item: dict, text: str) -> bool:
    """Block noisy or suspicious stories from the public brief."""
    source = clean_text(item.get("source")).lower()
    title = clean_text(item.get("title")).lower()
    summary = clean_text(item.get("summary")).lower()
    combined = f"{title} {summary} {source}"

    social_spat_terms = [
        "musk", "altman", "sam altman", "elon musk", "openai", "x platform",
        "x post", "twitter", "spar", "feud", "argue", "responds",
    ]
    if sum(1 for term in social_spat_terms if term in combined) >= 3:
        return True

    private_company_market_claims = [
        ("spacex", "ipo"),
        ("spacex", "stock"),
        ("openai", "ipo"),
        ("anthropic", "stock"),
        ("xai", "ipo"),
    ]
    if any(a in combined and b in combined for a, b in private_company_market_claims):
        return True

    entertainment_media_terms = ["paramount", "warner bros", "wbd", "disney", "netflix"]
    if any(term in combined for term in entertainment_media_terms) and any(
        term in combined for term in ["lawsuit", "sues", "merger", "acquisition", "block merger"]
    ):
        return True

    # Conflict alone is not enough, but a named economic event (inflation,
    # shipping, energy or a formal policy action) is still reader-worthy.
    war_narrative_terms = ["war volatility", "edge toward war"]
    if any(term in combined for term in war_narrative_terms):
        return True

    if "military" in combined and not any(
        term in combined for term in ["sanction", "export control", "shipping", "oil", "hormuz", "trade"]
    ):
        return True

    if item.get("section") == COMPANY and "lawsuit" in combined and not any(
        term in combined for term in ["sec", "regulator", "antitrust", "fine", "settlement", "probe"]
    ):
        return True

    return False


def build_news_pool(brief: dict) -> list[dict]:
    candidates: list[dict] = []
    candidates.extend(collect_article_candidates(brief))
    candidates.extend(collect_timeline_candidates(brief))
    candidates.extend(collect_economic_calendar_candidates(brief))
    candidates.extend(collect_market_candidates(brief))
    candidates.extend(collect_china_market_candidates(brief))
    candidates.extend(collect_theme_candidates(brief))
    candidates.extend(collect_global_company_candidates(brief))
    candidates.extend(collect_a_share_company_candidates(brief))
    candidates.extend(collect_structured_a_share_candidates(brief))
    candidates.extend(collect_structured_industry_candidates(brief))
    candidates.extend(collect_structured_index_valuation_candidates(brief))
    return dedupe_candidates(candidates)


def rank_news_pool(candidates: list[dict]) -> list[dict]:
    scored = []
    cutoff = datetime.now(BEIJING_TZ) - timedelta(hours=30)
    for item in candidates:
        dt = parse_candidate_time(item)
        if dt and dt < cutoff:
            continue
        if not passes_relevance_gate(item):
            continue
        item = dict(item)
        item["section"] = corrected_section(item)
        item["score"] = score_candidate(item)
        if item["score"] >= 6:
            scored.append(item)

    scored.sort(
        key=lambda item: (
            item.get("score", 0),
            parse_candidate_time(item) or datetime.min.replace(tzinfo=BEIJING_TZ),
        ),
        reverse=True,
    )
    return scored


EVENT_ANCHORS = {
    "hormuz": ("hormuz", "strait of hormuz"),
    "iran_conflict": ("iran", "iranian", "tehran"),
    "tariffs": ("tariff", "tariffs", "trade probe", "section 301"),
    "tsmc": ("tsmc", "taiwan semiconductor"),
    "volkswagen": ("volkswagen", "vw", "porsche", "audi"),
    "oil_supply": ("oil", "crude", "brent", "wti"),
    "central_banks": ("federal reserve", "fed", "central bank", "interest rate"),
    "chip_supply": ("semiconductor", "chip", "chips", "memory supply"),
    "shipping": ("shipping", "container", "freight", "vessel"),
}


def cluster_news_candidates(candidates: list[dict]) -> list[dict]:
    """Merge corroborating coverage and preserve an auditable representative."""
    clusters: list[list[dict]] = []
    for item in candidates:
        placed = False
        for cluster in clusters:
            if same_news_cluster(item, cluster[0]):
                cluster.append(item)
                placed = True
                break
        if not placed:
            clusters.append([item])

    result = []
    for members in clusters:
        representative = max(members, key=candidate_preference)
        item = dict(representative)
        sources = sorted({clean_text(member.get("source")) for member in members if clean_text(member.get("source"))})
        sections = sorted({clean_text(member.get("section")) for member in members if clean_text(member.get("section"))})
        item["cluster_id"] = "cluster-" + sha1("|".join(sorted(member["id"] for member in members)).encode("utf-8")).hexdigest()[:12]
        item["cluster_size"] = len(members)
        item["cluster_sources"] = sources[:5]
        item["cluster_sections"] = sections
        item["importance_score"] = importance_score(item, members)
        # Cross-beat events belong to the section that best explains the
        # primary fact, not to every section where a wire happened to place it.
        item["section"] = preferred_cluster_section(item, members)
        result.append(item)

    result.sort(
        key=lambda item: (
            item.get("importance_score", item.get("score", 0)),
            parse_candidate_time(item) or datetime.min.replace(tzinfo=BEIJING_TZ),
        ),
        reverse=True,
    )
    return result


def same_news_cluster(left: dict, right: dict) -> bool:
    if left.get("kind") not in {"article", "timeline", "company_news"}:
        return False
    if right.get("kind") not in {"article", "timeline", "company_news"}:
        return False
    left_text = f"{clean_text(left.get('title'))} {clean_text(left.get('summary'))}".lower()
    right_text = f"{clean_text(right.get('title'))} {clean_text(right.get('summary'))}".lower()
    left_anchors = {name for name, terms in EVENT_ANCHORS.items() if any(term in left_text for term in terms)}
    right_anchors = {name for name, terms in EVENT_ANCHORS.items() if any(term in right_text for term in terms)}
    shared = left_anchors & right_anchors
    # One generic anchor (for example oil) is not enough. Hormuz+oil or a
    # company-specific marker is strong enough to treat syndicated wires as
    # the same event even when the feeds assigned different categories.
    if len(shared) >= 2:
        return True
    company_markers = {"tsmc", "volkswagen"}
    if shared & company_markers:
        return True
    left_tokens = set(clean_text(left.get("event_key")).split())
    right_tokens = set(clean_text(right.get("event_key")).split())
    overlap = left_tokens & right_tokens
    return len(overlap) >= 4 and len(overlap) / max(1, min(len(left_tokens), len(right_tokens))) >= 0.6


def importance_score(item: dict, members: list[dict]) -> int:
    """Reader-facing 0-100 importance score: impact, evidence, freshness, corroboration."""
    text = f"{clean_text(item.get('title'))} {clean_text(item.get('summary'))}".lower()
    impact = 20
    if any(term in text for term in ["earnings", "revenue", "profit", "guidance", "cpi", "inflation", "rate", "tariff", "sanction", "hormuz", "oil", "merger", "acquisition", "layoff"]):
        impact += 20
    if any(term in text for term in ["export control", "shipping", "supply chain", "capex", "order", "backlog", "regulator", "filing"]):
        impact += 10
    evidence = min(18, len(item.get("facts") or []) * 4 + SOURCE_CONFIDENCE_SCORES.get(clean_text(item.get("source_confidence")).lower(), 0) * 2)
    if is_trusted(item):
        evidence += 5
    dt = parse_candidate_time(item)
    age_hours = (datetime.now(BEIJING_TZ) - dt).total_seconds() / 3600 if dt else 30
    freshness = max(2, min(12, round(12 - age_hours / 3)))
    corroboration = min(15, max(0, len(members) - 1) * 5)
    return max(1, min(100, impact + evidence + freshness + corroboration))


def preferred_cluster_section(item: dict, members: list[dict]) -> str:
    text = f"{clean_text(item.get('title'))} {clean_text(item.get('summary'))}".lower()
    if "hormuz" in text or "shipping" in text or "sanction" in text:
        return GLOBAL
    if any(term in text for term in ["earnings", "revenue", "profit", "guidance", "layoff", "merger", "acquisition"]):
        return COMPANY
    if any(term in text for term in ["cpi", "inflation", "central bank", "interest rate", "gdp", "pmi"]):
        return MACRO
    return item.get("section") or members[0].get("section") or MARKET


def build_sections(ranked_pool: list[dict], brief: dict) -> list[dict]:
    sections = []
    used_ids: set[str] = set()
    for title in SECTION_ORDER:
        section_items = []
        for candidate in ranked_pool:
            if candidate["id"] in used_ids or candidate.get("section") != title:
                continue
            section_items.append(candidate_to_digest_item(candidate))
            used_ids.add(candidate["id"])
            if len(section_items) >= section_limit(title):
                break
        # The digest is intentionally not auto-filled with price moves or
        # generic market context. Every visible row must originate from an
        # editorial fact card in the verified pool.
        sections.append({"title": title, "items": section_items[:section_limit(title)]})
    return sections


def build_market_context_items(brief: dict, used_ids: set[str], limit: int) -> list[dict]:
    """Keep only a few large index moves as factual context in a fallback brief."""
    candidates = collect_china_market_candidates(brief) + collect_market_candidates(brief)
    ranked = []
    for item in candidates:
        if item["id"] in used_ids:
            continue
        change = number_from_text(item.get("title"))
        ranked.append((abs(change or 0), item))
    result = []
    for _, item in sorted(ranked, key=lambda row: row[0], reverse=True):
        used_ids.add(item["id"])
        result.append(candidate_to_digest_item(item))
        if len(result) >= limit:
            break
    return result


def number_from_text(value: Any) -> float | None:
    match = re.search(r"([-+]?\d+(?:\.\d+)?)%", clean_text(value))
    return number(match.group(1)) if match else None


def collect_article_candidates(brief: dict) -> list[dict]:
    news_data = brief.get("news_data", {}) or {}
    items = []
    for category in news_data.get("categories", []) or []:
        feed_label = clean_text(category.get("label") or category.get("category"))
        for article in category.get("articles", []) or []:
            title = clean_text(article.get("title"))
            if not title:
                continue
            summary = clean_text(article.get("description"))
            section = classify_section([title, summary, feed_label, article.get("feed_topics")])
            if article_looks_like_company_item(title, summary):
                section = COMPANY
            items.append(candidate(
                kind="article",
                section=section,
                title=title,
                summary=summary,
                time=normalize_time(article.get("published")),
                url=article.get("url", ""),
                source=article.get("source_name") or feed_label,
                # Publisher URLs are a stronger trust signal than an upstream
                # feed's generic "lead" label.
                source_confidence=best_source_confidence(
                    normalize_source_confidence(article.get("confidence")),
                    source_confidence_for(article),
                ),
                source_type=article.get("source_type", ""),
                source_domain=article.get("source_domain", ""),
                facts=extract_facts(title, summary),
            ))
    return items


def collect_timeline_candidates(brief: dict) -> list[dict]:
    timeline = brief.get("event_timeline", {}) or {}
    items = []
    for event in timeline.get("events", []) or []:
        title = clean_text(event.get("title"))
        if not title:
            continue
        summary = clean_text(event.get("summary"))
        section = normalize_section(event.get("category")) or classify_section(
            [title, summary, event.get("impact"), event.get("subject")]
        )
        items.append(candidate(
            kind="timeline",
            section=section,
            title=title,
            summary=summary,
            time=clean_text(event.get("time")),
            source="event_timeline",
            facts=extract_facts(title, summary, event.get("impact")),
            impact=clean_text(event.get("impact")),
        ))
    return items


def collect_economic_calendar_candidates(brief: dict) -> list[dict]:
    calendar = brief.get("economic_calendar", {}) or {}
    items = []
    for event in calendar.get("events", []) or []:
        importance = clean_text(event.get("importance")).lower()
        if importance and importance not in {"high", "medium"}:
            continue
        country = clean_text(event.get("country"))
        name = clean_text(event.get("event"))
        if not name:
            continue
        actual = clean_text(event.get("actual")) or zh("\\u5f85\\u516c\\u5e03")
        consensus = clean_text(event.get("consensus")) or zh("\\u672a\\u7ed9\\u51fa")
        previous = clean_text(event.get("previous")) or zh("\\u672a\\u7ed9\\u51fa")
        title = f"{country} {name}{zh('\\u516c\\u5e03\\u503c\\u4e3a')}{actual}"
        summary = zh("\\u5e02\\u573a\\u9884\\u671f\\u4e3a") + f"{consensus}" + zh("\\uff0c\\u524d\\u503c\\u4e3a") + f"{previous}" + zh("\\uff1b\\u8fd9\\u7c7b\\u6570\\u636e\\u4f1a\\u5f71\\u54cd\\u5229\\u7387\\u3001\\u6c47\\u7387\\u548c\\u80a1\\u503a\\u5546\\u54c1\\u7684\\u98ce\\u9669\\u504f\\u597d\\u3002")
        items.append(candidate(
            kind="economic_calendar",
            section=MACRO,
            title=title,
            summary=summary,
            time=join_time(event.get("date"), event.get("time")),
            source="economic_calendar",
            facts=extract_facts(title, summary),
        ))
    return items


def collect_market_candidates(brief: dict) -> list[dict]:
    market = brief.get("market_data", {}) or {}
    items = []
    for row in market.get("indices", []) or []:
        change = number(row.get("change_percent_from_previous_close") or row.get("change_percent_from_open"))
        if change is None or abs(change) < 0.4:
            continue
        region = clean_text(row.get("region"))
        name = clean_text(row.get("name") or row.get("symbol"))
        price = format_number(row.get("regular_market_price") or row.get("close"))
        title = f"{region} {name}{direction(change)}{abs(change):.2f}%"
        summary = zh("\\u6700\\u65b0\\u70b9\\u4f4d\\u4e3a") + f"{price}" + zh("\\uff1b\\u8be5\\u53d8\\u5316\\u7528\\u4e8e\\u5224\\u65ad\\u5168\\u7403\\u98ce\\u9669\\u504f\\u597d\\u548c\\u533a\\u57df\\u5e02\\u573a\\u5f3a\\u5f31\\u3002")
        items.append(candidate(
            kind="market",
            section=MARKET,
            title=title,
            summary=summary,
            time=market_time(row),
            source="market_data",
            facts=extract_facts(title, summary),
        ))
    return items


def collect_china_market_candidates(brief: dict) -> list[dict]:
    china = brief.get("china_market_data", {}) or {}
    items = []
    for row in china.get("indices", []) or []:
        change = number(row.get("change_percent"))
        if change is None or abs(change) < 0.5:
            continue
        name = clean_text(row.get("name") or row.get("symbol"))
        price = format_number(row.get("price") or row.get("close"))
        title = f"{name}{direction(change)}{abs(change):.2f}%"
        summary = zh("\\u6700\\u65b0\\u70b9\\u4f4d\\u4e3a") + f"{price}" + zh("\\uff1bA\\u80a1\\u53d8\\u5316\\u8981\\u548c\\u677f\\u5757\\u3001\\u6210\\u4ea4\\u989d\\u548c\\u653f\\u7b56\\u4fe1\\u53f7\\u4e00\\u8d77\\u770b\\u3002")
        items.append(candidate(
            kind="china_market",
            section=MARKET,
            title=title,
            summary=summary,
            time=market_time(row),
            source="china_market_data",
            facts=extract_facts(title, summary),
        ))
    return items


def collect_theme_candidates(brief: dict) -> list[dict]:
    theme_data = brief.get("theme_data", {}) or {}
    items = []
    for group_name, rows in flatten_theme_groups(theme_data):
        for row in rows:
            change = number(row.get("change_percent_from_previous_close") or row.get("change_percent_from_open"))
            if change is None or abs(change) < 0.8:
                continue
            name = clean_text(row.get("name") or row.get("symbol") or group_name)
            price = format_number(row.get("regular_market_price") or row.get("close"))
            title = f"{group_name} {name}{direction(change)}{abs(change):.2f}%"
            summary = zh("\\u6700\\u65b0\\u4ef7\\u683c\\u4e3a") + f"{price}" + zh("\\uff1b\\u4e3b\\u9898\\u8d44\\u4ea7\\u7684\\u53d8\\u5316\\u7528\\u6765\\u89c2\\u5bdf\\u884c\\u4e1a\\u666f\\u6c14\\u3001\\u6210\\u672c\\u548c\\u9700\\u6c42\\u3002")
            items.append(candidate(
                kind="theme",
                section=INDUSTRY if group_name != zh("\\u80fd\\u6e90\\u4ef7\\u683c") else FINANCE,
                title=title,
                summary=summary,
                time=market_time(row),
                source="theme_data",
                facts=extract_facts(title, summary),
            ))
    return items


def collect_global_company_candidates(brief: dict) -> list[dict]:
    company_data = brief.get("company_watchlist_data", {}) or {}
    items = []
    for company in company_data.get("items") or company_data.get("companies", []) or []:
        name = clean_text(company.get("name") or company.get("symbol"))
        quote = company.get("quote", {}) or {}
        change = number(quote.get("change_percent_from_previous_close") or quote.get("change_percent_from_open"))
        if change is not None and abs(change) >= 1.5:
            price = format_number(quote.get("regular_market_price") or quote.get("close"))
            title = f"{name}{zh('\\u80a1\\u4ef7')}{direction(change)}{abs(change):.2f}%"
            summary = zh("\\u6700\\u65b0\\u4ef7\\u683c\\u4e3a") + f"{price}" + zh("\\uff1b\\u516c\\u53f8\\u80a1\\u4ef7\\u5f02\\u52a8\\u9700\\u8981\\u4e0e\\u8d22\\u62a5\\u3001\\u6307\\u5f15\\u3001\\u8ba2\\u5355\\u6216\\u884c\\u4e1a\\u65b0\\u95fb\\u5408\\u5e76\\u5224\\u65ad\\u3002")
            items.append(candidate("company_price", COMPANY, title, summary, market_time(quote), "company_watchlist", facts=extract_facts(title, summary)))
        for article in company.get("articles") or company.get("news", []) or []:
            title = clean_text(article.get("title"))
            if not title:
                continue
            summary = clean_text(article.get("description"))
            section = classify_section([name, title, summary])
            if section not in {COMPANY, INDUSTRY, MARKET, GLOBAL}:
                section = COMPANY
            items.append(candidate(
                kind="company_news",
                section=section,
                title=f"{name}: {title}",
                summary=summary,
                time=normalize_time(article.get("published")),
                url=article.get("url", ""),
                source=article.get("source_name") or "company_news",
                source_confidence=normalize_source_confidence(article.get("confidence")) or source_confidence_for(article),
                source_type=article.get("source_type", ""),
                source_domain=article.get("source_domain", ""),
                facts=extract_facts(title, summary),
            ))
        for filing in company.get("official_filings", []) or []:
            form = clean_text(filing.get("form"))
            filing_date = clean_text(filing.get("filing_date"))
            if not form or not filing_date:
                continue
            document_summary = filing.get("document_summary") or {}
            document_title = clean_text(document_summary.get("title"))
            document_items = [clean_text(value) for value in (document_summary.get("items") or []) if clean_text(value)]
            details = "；".join(document_items[:3])
            summary = f"{name}于{filing_date}向美国证券交易委员会提交{form}。"
            if document_title:
                summary += f" 文件标题：{document_title[:160]}。"
            if details:
                summary += f" 披露条目：{details[:220]}。"
            items.append(candidate(
                kind="company_filing",
                section=COMPANY,
                title=f"{name}提交SEC {form}披露",
                summary=summary,
                time=filing_date,
                source="SEC EDGAR",
                url=clean_text(filing.get("url")),
                source_confidence="high",
                source_domain="sec.gov",
                facts=extract_facts(form, filing_date, document_title, details),
            ))
    return items


def collect_a_share_company_candidates(brief: dict) -> list[dict]:
    data = brief.get("a_share_company_data", {}) or {}
    items = []
    for company in data.get("companies", []) or []:
        name = clean_text(company.get("name") or company.get("code"))
        for ann in company.get("announcements", []) or []:
            title = clean_text(ann.get("title"))
            if not title or not is_material_a_share_title(title):
                continue
            items.append(candidate("a_share_announcement", COMPANY, f"{name}: {title}", clean_text(ann.get("summary")), clean_text(ann.get("date")), "a_share_announcements", facts=extract_facts(title, ann.get("summary"))))
        for row in company.get("financials", []) or []:
            summary = summarize_financial_row(row)
            if summary:
                items.append(candidate("a_share_financial", COMPANY, f"{name}{zh('\\u8d22\\u52a1\\u6570\\u636e\\u66f4\\u65b0')}", summary, clean_text(row.get("report_date") or row.get("date")), "a_share_financials", facts=extract_facts(summary)))
        for row in company.get("supervision", []) or []:
            title = clean_text(row.get("title") or row.get("type"))
            if title:
                items.append(candidate("a_share_supervision", COMPANY, f"{name}: {title}", clean_text(row.get("summary")), clean_text(row.get("date")), "a_share_supervision", facts=extract_facts(title, row.get("summary"))))
    return items


def collect_structured_a_share_candidates(brief: dict) -> list[dict]:
    """Turn exchange-oriented A-share data into high-confidence fact cards."""
    data = brief.get("structured_market_data", {}) or {}
    items = []
    for company in data.get("a_share_companies", []) or []:
        name = clean_text(company.get("name") or company.get("symbol"))
        if not name:
            continue
        for announcement in company.get("announcements", []) or []:
            title = clean_text(announcement.get("title"))
            if not title or not is_material_a_share_title(title):
                continue
            announced_at = clean_text(announcement.get("time"))
            category = clean_text(announcement.get("category"))
            summary = f"{name}于{announced_at or '最近'}披露{category or '公告'}：{title}。"
            items.append(candidate(
                "a_share_announcement",
                COMPANY,
                f"{name}：{title}",
                summary,
                announced_at,
                "A股公告",
                url=clean_text(announcement.get("url")),
                source_confidence="high",
                facts=extract_facts(title, summary),
            ))
        for notice in company.get("supervision", []) or []:
            title = clean_text(notice.get("title") or notice.get("type"))
            if not title:
                continue
            issued_at = clean_text(notice.get("time"))
            notice_type = clean_text(notice.get("type"))
            summary = f"{name}于{issued_at or '最近'}收到{notice_type or '监管'}文件：{title}。"
            items.append(candidate(
                "a_share_supervision",
                COMPANY,
                f"{name}：{title}",
                summary,
                issued_at,
                "A股监管披露",
                url=clean_text(notice.get("url")),
                source_confidence="high",
                facts=extract_facts(title, summary),
            ))
        for financial in company.get("financials", []) or []:
            summary = summarize_structured_financial_row(name, financial)
            if not summary:
                continue
            report_date = clean_text(financial.get("date"))
            items.append(candidate(
                "a_share_financial",
                COMPANY,
                f"{name}财务指标更新",
                summary,
                report_date,
                "A股财报披露",
                source_confidence="high",
                facts=extract_facts(summary),
            ))
    return items


def collect_structured_industry_candidates(brief: dict) -> list[dict]:
    """Expose domestic industry strength as factual, clearly-labelled context."""
    data = brief.get("structured_market_data", {}) or {}
    items = []
    for row in (data.get("industries") or [])[:30]:
        name = clean_text(row.get("name"))
        if not name:
            continue
        profit_1d = number(row.get("profit_1d"))
        rps_20d = number(row.get("rps_20d"))
        rps_50d = number(row.get("rps_50d"))
        if profit_1d is None and rps_20d is None and rps_50d is None:
            continue
        metrics = []
        if profit_1d is not None:
            metrics.append(f"单日收益率{profit_1d:.2f}%")
        if rps_20d is not None:
            metrics.append(f"20日相对强度{rps_20d:.2f}")
        if rps_50d is not None:
            metrics.append(f"50日相对强度{rps_50d:.2f}")
        if row.get("stock_count"):
            metrics.append(f"覆盖{row['stock_count']}只成分股")
        items.append(candidate(
            "a_share_industry", INDUSTRY, f"A股行业：{name}",
            "；".join(metrics) + "。数据用于观察行业相对强弱，不构成投资建议。",
            clean_text(row.get("trade_date")), "投资数据网行业数据",
            source_confidence="high", facts=extract_facts(" ".join(metrics)),
        ))
    return items


def collect_structured_index_valuation_candidates(brief: dict) -> list[dict]:
    data = brief.get("structured_market_data", {}) or {}
    items = []
    for row in (data.get("index_valuation") or [])[:12]:
        name = clean_text(row.get("name") or row.get("symbol"))
        if not name:
            continue
        metrics = []
        for label, field in [("市盈率", "pe"), ("市净率", "pb"), ("股息率", "dividend_yield")]:
            value = number(row.get(field))
            if value is not None:
                metrics.append(f"{label}{value:.2f}")
        if not metrics:
            continue
        items.append(candidate(
            "a_share_index_valuation", MARKET, f"A股指数估值：{name}", "；".join(metrics) + "。",
            clean_text(row.get("trade_date")), "投资数据网指数估值",
            source_confidence="high", facts=extract_facts(" ".join(metrics)),
        ))
    return items


def is_material_a_share_title(title: str) -> bool:
    text = clean_text(title).lower()
    markers = [
        "年度", "半年度", "季度", "业绩", "利润", "营收", "回购", "增持", "减持", "收购",
        "重大", "签署", "合同", "订单", "投资", "融资", "发行", "重组", "停牌", "复牌",
        "监管", "问询", "处罚", "立案", "诉讼", "仲裁", "担保", "关联交易",
    ]
    return any(marker in text for marker in markers)


def summarize_structured_financial_row(name: str, row: dict) -> str:
    metrics = row.get("metrics") or {}
    if not isinstance(metrics, dict) or not metrics:
        return ""
    labels = {
        "pr.toi.o": "营业总收入",
        "pr.toi.o_y": "营业总收入同比",
        "pr.np.o": "净利润",
        "pr.np.o_y": "净利润同比",
        "ca.ncffoa.o": "经营现金流",
        "me.mt_roe_rt.o": "ROE",
        "bs.ta.o": "总资产",
        "bs.tl.o": "总负债",
    }
    parts = []
    for key, label in labels.items():
        value = clean_text(metrics.get(key))
        if value:
            parts.append(f"{label}{value}")
    if not parts:
        return ""
    return f"{name}披露财务指标：" + "；".join(parts[:4]) + "。"


def candidate(kind: str, section: str, title: str, summary: str = "", time: str = "", source: str = "", **extra: Any) -> dict:
    title = clean_text(title)
    summary = clean_text(summary)
    key = "|".join([kind, section, title.lower(), clean_text(time)])
    return {
        "id": sha1(key.encode("utf-8", errors="ignore")).hexdigest()[:16],
        "kind": kind,
        "section": section,
        "title": title,
        "summary": summary,
        "time": clean_text(time),
        "source": clean_text(source),
        "event_key": event_fingerprint(title),
        **extra,
    }


def passes_relevance_gate(item: dict) -> bool:
    text = " ".join([clean_text(item.get("title")), clean_text(item.get("summary")), clean_text(item.get("source"))]).lower()
    if any(pattern in text for pattern in LOW_VALUE_PATTERNS):
        return False
    if is_non_material_global_event(text):
        return False
    if item.get("kind") in {"article", "timeline", "company_news"} and any(pattern in text for pattern in PREVIEW_PATTERNS):
        return False
    # General disaster and personnel stories are important news, but they do
    # not belong in a finance-led morning brief unless a concrete market,
    # supply-chain, energy or policy transmission is present in the same card.
    natural_disaster_terms = ["typhoon", "wildfire", "earthquake", "flood", "evacuated"]
    material_link_terms = ["shipping", "oil", "energy", "factory", "supply chain", "export", "sanction", "hormuz"]
    if any(term in text for term in natural_disaster_terms) and not any(term in text for term in material_link_terms):
        return False
    if "military" in text and not any(term in text for term in ["sanction", "strike", "airstrike", "shipping", "hormuz", "oil", "export control"]):
        return False
    raw_text = " ".join([clean_text(item.get("title")), clean_text(item.get("summary"))])
    if any(pattern in raw_text for pattern in [zh("\\u51fa\\u73b0\\u516c\\u53f8\\u65b0\\u95fb\\u7ebf\\u7d22"), zh("\\u8fd9\\u7c7b\\u7ebf\\u7d22\\u8981\\u5224\\u65ad")]):
        return False
    headline_only_media = is_major_media(item) and has_material_headline(item)
    if item.get("kind") in {"article", "timeline", "company_news"} and not has_factual_signal(text) and not headline_only_media:
        return False
    if item.get("kind") in {"article", "timeline", "company_news"} and not has_enough_evidence(item) and not headline_only_media:
        return False
    if item.get("kind") in {"market", "china_market", "theme", "economic_calendar", "company_price", "a_share_financial", "a_share_announcement", "a_share_supervision", "a_share_industry", "a_share_index_valuation"}:
        return True
    section = item.get("section")
    required = SECTION_REQUIRED_PATTERNS.get(section, [])
    if required and any(keyword in text for keyword in required):
        return True
    if is_trusted(item) and any(keyword in text for keyword in HIGH_SIGNAL_KEYWORDS):
        return True
    return False


def score_candidate(item: dict) -> int:
    text = " ".join([clean_text(item.get("title")), clean_text(item.get("summary")), clean_text(item.get("source"))]).lower()
    score = 0
    score += {"economic_calendar": 8, "a_share_announcement": 9, "a_share_financial": 8, "a_share_supervision": 8, "a_share_industry": 7, "a_share_index_valuation": 7, "theme": 7, "company_news": 6, "article": 5, "timeline": 5, "china_market": 5, "market": 4, "company_price": 4}.get(item.get("kind"), 3)
    score += min(len(NUMERIC_RE.findall(text)), 5)
    if is_trusted(item):
        score += 3
    score += SOURCE_CONFIDENCE_SCORES.get(clean_text(item.get("source_confidence")).lower(), 0)
    if item.get("section") in {MACRO, MARKET, INDUSTRY, COMPANY, FINANCE}:
        score += 2
    if item.get("time"):
        score += 1
    if any(keyword in text for keyword in ["earnings", "revenue", "profit", "guidance", "cpi", "fed", "tariff", "export control", "semiconductor", "ai", "oil", "gold"]):
        score += 2
    if any(pattern in text for pattern in LOW_VALUE_PATTERNS):
        score -= 20
    if any(pattern in text for pattern in PREVIEW_PATTERNS):
        score -= 12
    if item.get("kind") in {"article", "timeline", "company_news"} and has_factual_signal(text):
        score += 3
    if has_enough_evidence(item):
        score += 3
    if item.get("kind") in {"article", "timeline", "company_news"} and len(clean_text(item.get("summary"))) >= 140:
        score += 3
    if item.get("kind") in {"market", "china_market", "company_price"}:
        score -= 4
    if len(clean_text(item.get("summary"))) < 25 and item.get("kind") in {"article", "timeline", "company_news"}:
        score -= 6
    return score


def candidate_to_digest_item(item: dict) -> dict:
    title = clean_text(item.get("title"))
    summary = clean_text(item.get("summary"))
    facts = item.get("facts") or []
    if not summary:
        summary = zh("\\u8fd9\\u6761\\u4fe1\\u606f\\u8bb0\\u5f55\\u4e86\\u8fc7\\u53bb24\\u5c0f\\u65f6\\u7684\\u5173\\u952e\\u53d8\\u5316\\uff0c\\u9700\\u8981\\u548c\\u540c\\u677f\\u5757\\u4fe1\\u606f\\u4e00\\u8d77\\u770b\\u3002")
    if facts:
        summary = append_facts(summary, facts)
    return {
        "card_id": clean_text(item.get("id")),
        "thesis": title[:140],
        "summary": summary[:360],
        "time": clean_text(item.get("time")),
        "importance_score": item.get("importance_score", item.get("score", 0)),
        "cluster_size": item.get("cluster_size", 1),
        "source": clean_text(item.get("source")),
    }


def corrected_section(item: dict) -> str:
    text = " ".join([clean_text(item.get("title")), clean_text(item.get("summary"))]).lower()
    if any(pattern in text for pattern in [
        "cpi", "ppi", "inflation", "gdp", "pmi", "unemployment", "jobs report",
        "central bank", "interest rate", "rate decision", "trade balance",
    ]):
        return MACRO
    if any(pattern in text for pattern in FORCE_GLOBAL_PATTERNS):
        return GLOBAL
    if any(pattern in text for pattern in FORCE_COMPANY_PATTERNS):
        return COMPANY
    if "typhoon" in text or "wildfire" in text:
        return GLOBAL
    return item.get("section") or classify_section([text])


def build_overview(sections: list[dict]) -> list[str]:
    overview = []
    for section in sections:
        for item in section.get("items", []):
            thesis = clean_text(item.get("thesis"))
            if thesis:
                overview.append(thesis)
            if len(overview) >= 3:
                return overview
    return overview


def build_financial_data_items(brief: dict, used_ids: set[str]) -> list[dict]:
    items = []
    for candidate_item in collect_theme_candidates(brief) + collect_market_candidates(brief):
        if candidate_item.get("section") != FINANCE or candidate_item["id"] in used_ids:
            continue
        used_ids.add(candidate_item["id"])
        items.append(candidate_to_digest_item(candidate_item))
        if len(items) >= 3:
            break
    return items


def section_limit(title: str) -> int:
    return {MACRO: 6, PROPERTY: 5, MARKET: 6, INDUSTRY: 10, COMPANY: 8, GLOBAL: 6, FINANCE: 6}.get(title, 6)


def classify_section(parts: list[Any]) -> str:
    text = " ".join(clean_text(part) for part in parts if part).lower()
    if any(pattern in text for pattern in FORCE_GLOBAL_PATTERNS):
        return GLOBAL
    if any(pattern in text for pattern in FORCE_COMPANY_PATTERNS):
        return COMPANY
    best_section = MARKET
    best_score = -1
    for section, keywords in SECTION_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_score = score
            best_section = section
    return best_section


def article_looks_like_company_item(title: str, summary: str) -> bool:
    text = f"{title} {summary}".lower()
    return any(pattern in text for pattern in FORCE_COMPANY_PATTERNS)


def has_factual_signal(text: str) -> bool:
    if any(pattern in text for pattern in FORCE_GLOBAL_PATTERNS + FORCE_COMPANY_PATTERNS):
        return True
    if any(pattern in text for pattern in [
        "cpi", "ppi", "inflation", "fed", "central bank", "treasury", "yield", "gdp",
        "pmi", "tariff", "customs", "export control", "sanction", "blacklist",
        "earnings", "revenue", "profit", "guidance", "lawsuit", "sues", "sec filing",
        "ipo", "buyback", "merger", "acquisition", "layoffs", "jobs", "unemployment",
        "semiconductor", "chip", "ai", "data center", "memory supply", "oil", "gold",
        "copper", "hormuz", "strait", "container ship", "airstrikes",
    ]):
        return True
    numbers = NUMERIC_RE.findall(text)
    if len(numbers) >= 2 and any(pattern in text for pattern in ["stock", "shares", "index", "market", "housing", "property"]):
        return True
    return False


def has_enough_evidence(item: dict) -> bool:
    summary = clean_text(item.get("summary"))
    title = clean_text(item.get("title"))
    facts = item.get("facts") or []
    text = f"{title} {summary}".lower()
    if item.get("kind") not in {"article", "timeline", "company_news"}:
        return True
    if (
        is_trusted(item)
        and clean_text(item.get("source_confidence")).lower() in {"high", "medium"}
        and len(title) >= 42
        and any(pattern in text for pattern in HARD_EVENT_PATTERNS)
        and any(verb in title.lower() for verb in TITLE_EVENT_VERBS)
    ):
        return True
    if any(pattern in text for pattern in ["lawsuit", "sues", "investigation", "merger", "acquisition"]) and len(facts) < 2 and len(summary) < 120:
        return False
    if len(facts) >= 2 and len(summary) >= 60:
        return True
    if facts and len(summary) >= 110 and any(pattern in text for pattern in [
        "airstrike", "airstrikes", "hormuz", "tariff", "export control", "sanction",
        "lawsuit", "sues", "sec filing", "earnings", "revenue", "profit", "guidance",
        "central bank", "cpi", "inflation", "typhoon", "evacuated", "volunteers",
        "military", "container ship", "flight", "train", "cancel", "wildfire",
        "merger", "acquisition", "retention", "defence ministry",
    ]):
        return True
    if len(summary) >= 180 and is_trusted(item) and any(pattern in text for pattern in [
        "airstrike", "airstrikes", "hormuz", "tariff", "export control", "sanction",
        "lawsuit", "sues", "sec filing", "earnings", "revenue", "profit", "guidance",
        "central bank", "cpi", "inflation", "typhoon", "evacuated", "volunteers",
        "military", "container ship", "flight", "train", "cancel",
    ]):
        return True
    return False


def normalize_section(text: Any) -> str:
    raw = clean_text(text).lower()
    if not raw:
        return ""
    mapping = {
        "macro": MACRO, "economy": MACRO, "economic": MACRO,
        "property": PROPERTY, "real_estate": PROPERTY, "housing": PROPERTY,
        "market": MARKET, "markets": MARKET, "stocks": MARKET,
        "industry": INDUSTRY, "technology": INDUSTRY, "energy": INDUSTRY,
        "company": COMPANY, "companies": COMPANY, "earnings": COMPANY,
        "global": GLOBAL, "politics": GLOBAL, "geopolitics": GLOBAL,
        "finance": FINANCE, "commodity": FINANCE, "commodities": FINANCE,
    }
    return mapping.get(raw, "")


def dedupe_candidates(candidates: list[dict]) -> list[dict]:
    """Collapse reposts while retaining the most factual version of an event."""
    by_exact_title: dict[str, dict] = {}
    for item in candidates:
        key = normalize_title(item.get("title"))
        if not key:
            continue
        previous = by_exact_title.get(key)
        if previous is None or candidate_preference(item) > candidate_preference(previous):
            by_exact_title[key] = item

    unique: list[dict] = []
    for item in by_exact_title.values():
        if item.get("kind") not in {"article", "timeline", "company_news"}:
            unique.append(item)
            continue
        duplicate_position = next((index for index, kept in enumerate(unique) if is_same_event(item, kept)), None)
        if duplicate_position is None:
            unique.append(item)
        elif candidate_preference(item) > candidate_preference(unique[duplicate_position]):
            unique[duplicate_position] = item
    return unique


def candidate_preference(item: dict) -> int:
    summary = clean_text(item.get("summary"))
    confidence = SOURCE_CONFIDENCE_SCORES.get(clean_text(item.get("source_confidence")).lower(), 0)
    return confidence * 100 + min(len(summary), 320) + len(item.get("facts") or []) * 30 + (30 if is_trusted(item) else 0)


def is_same_event(left: dict, right: dict) -> bool:
    if left.get("kind") not in {"article", "timeline", "company_news"}:
        return False
    if right.get("kind") not in {"article", "timeline", "company_news"}:
        return False
    if left.get("section") != right.get("section"):
        return False
    left_key = clean_text(left.get("event_key"))
    right_key = clean_text(right.get("event_key"))
    if not left_key or not right_key:
        return False
    if left_key == right_key:
        return True
    left_tokens = set(left_key.split())
    right_tokens = set(right_key.split())
    overlap = left_tokens & right_tokens
    if len(overlap) >= 3 and len(overlap) / max(1, min(len(left_tokens), len(right_tokens))) >= 0.7:
        return True
    return False


def extract_facts(*parts: Any) -> list[str]:
    text = " ".join(clean_text(part) for part in parts if part)
    facts = []
    for match in NUMERIC_RE.findall(text):
        token = clean_text(match)
        if token and token not in facts:
            facts.append(token)
        if len(facts) >= 4:
            break
    return facts


def append_facts(summary: str, facts: list[str]) -> str:
    existing = summary
    facts = [fact for fact in facts if fact and fact not in existing]
    if not facts:
        return summary
    return summary.rstrip(" .;；。") + zh("\\uff1b\\u5173\\u952e\\u6570\\u5b57\\uff1a") + "、".join(facts[:3]) + zh("\\u3002")


def summarize_financial_row(row: dict) -> str:
    parts = []
    for key in ["revenue", "net_profit", "gross_margin", "roe", "yoy", "report_period"]:
        value = clean_text(row.get(key))
        if value:
            parts.append(f"{key}: {value}")
    if not parts:
        title = clean_text(row.get("title") or row.get("summary"))
        return title[:240]
    return zh("\\u516c\\u53f8\\u62ab\\u9732\\u8d22\\u52a1\\u6307\\u6807\\uff1a") + "；".join(parts[:5]) + zh("\\u3002")


def flatten_theme_groups(theme_data: dict) -> list[tuple[str, list[dict]]]:
    groups = []
    labels = {
        "commodities": zh("\\u5927\\u5b97\\u5546\\u54c1"),
        "commodity_prices": zh("\\u5927\\u5b97\\u5546\\u54c1"),
        "energy": zh("\\u80fd\\u6e90\\u4ef7\\u683c"),
        "energy_prices": zh("\\u80fd\\u6e90\\u4ef7\\u683c"),
        "semiconductors": zh("\\u534a\\u5bfc\\u4f53"),
        "themes": zh("\\u4e3b\\u9898\\u8d44\\u4ea7"),
    }
    for key, label in labels.items():
        value = theme_data.get(key)
        if isinstance(value, list):
            groups.append((label, value))
        elif isinstance(value, dict):
            rows = value.get("items") or value.get("indices") or value.get("quotes") or []
            if isinstance(rows, list):
                groups.append((label, rows))
    return groups


def parse_candidate_time(item: dict) -> datetime | None:
    text = clean_text(item.get("time"))
    if not text:
        return None
    now = datetime.now(BEIJING_TZ)
    text = text.replace("T", " ").replace("Z", "")
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%m-%d %H:%M"]
    for fmt in formats:
        try:
            sample = text[:len(now.strftime(fmt))]
            dt = datetime.strptime(sample, fmt)
            if fmt.startswith("%m"):
                dt = dt.replace(year=now.year)
            return dt.replace(tzinfo=BEIJING_TZ)
        except ValueError:
            continue
    return None


def normalize_time(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    text = text.replace("T", " ").replace("Z", "")
    return text[:16]


def join_time(date_value: Any, time_value: Any) -> str:
    date = clean_text(date_value)
    time = clean_text(time_value)
    if date and time:
        return f"{date} {time}"[:16]
    return date or time


def market_time(row: dict) -> str:
    return normalize_time(row.get("regular_market_time") or row.get("timestamp") or row.get("date"))


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(clean_text(item) for item in value)
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_title(value: Any) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:120]


def event_fingerprint(value: Any) -> str:
    """A small semantic key for syndicated English headlines and repeated wires."""
    text = normalize_title(value)
    stopwords = {
        "the", "a", "an", "to", "for", "of", "in", "on", "and", "with", "after", "as",
        "says", "say", "will", "may", "new", "latest", "update", "news", "market", "markets",
        "stock", "stocks", "shares", "global", "china", "us", "u s", "from", "at", "by",
    }
    tokens = [token for token in text.split() if token not in stopwords and len(token) > 1]
    return " ".join(tokens[:12])


def source_confidence_for(article: dict) -> str:
    url = " ".join([
        clean_text(article.get("url")),
        clean_text(article.get("source_domain")),
        clean_text(article.get("source_name")),
    ]).lower()
    if any(marker in url for marker in ["sec.gov", "sse.com.cn", "szse.cn", "hkexnews.hk", "pbc.gov.cn", "mof.gov.cn", "stats.gov.cn", "ndrc.gov.cn"]):
        return "high"
    if any(marker in url for marker in TRUSTED_DOMAINS):
        return "medium"
    return "normal"


def normalize_source_confidence(value: Any) -> str:
    raw = clean_text(value).lower()
    mapping = {
        "高": "high",
        "high": "high",
        "中": "medium",
        "medium": "medium",
        "线索": "normal",
        "normal": "normal",
        "lead": "normal",
    }
    return mapping.get(raw, "")


def best_source_confidence(*values: Any) -> str:
    """Keep the strongest evidence-based source tier available for an article."""
    normalized = [normalize_source_confidence(value) for value in values]
    return max(normalized, key=lambda value: SOURCE_CONFIDENCE_SCORES.get(value, 0), default="")


def is_trusted(item: dict) -> bool:
    text = " ".join([
        clean_text(item.get("url")),
        clean_text(item.get("source_domain")),
        clean_text(item.get("source")),
    ]).lower()
    return any(domain in text for domain in TRUSTED_DOMAINS)


def number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = clean_text(value).replace("%", "").replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def format_number(value: Any) -> str:
    val = number(value)
    if val is None:
        return clean_text(value) or zh("\\u5f85\\u786e\\u8ba4")
    return f"{val:.2f}".rstrip("0").rstrip(".")


def direction(change: float) -> str:
    return zh("\\u4e0a\\u6da8") if change >= 0 else zh("\\u4e0b\\u8dcc")
