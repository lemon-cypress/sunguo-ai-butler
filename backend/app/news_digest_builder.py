from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

BEIJING_TZ = timezone(timedelta(hours=8))

SECTION_SPECS = [
    {
        "key": "china_market",
        "title": "中国市场",
        "categories": ["中国市场"],
        "keywords": ["中国", "香港", "A股", "上证", "深证", "沪深", "恒生", "人民币", "地产", "消费", "政策"],
        "fallback": "中国市场先看政策预期、人民币、成交量和科技成长是否同向，暂不把单日价格波动当成趋势。",
    },
    {
        "key": "global_macro",
        "title": "全球市场与宏观",
        "categories": ["全球市场与宏观"],
        "keywords": ["美国", "日本", "韩国", "欧洲", "Fed", "利率", "通胀", "美元", "美债", "NASDAQ", "S&P", "DAX", "KOSPI", "日经"],
        "fallback": "全球宏观先看利率、美元、能源和科技股四条线是否共振，暂不从单一区域指数下结论。",
    },
    {
        "key": "policy",
        "title": "政治、政策与监管",
        "categories": ["政策、监管与地缘"],
        "keywords": ["政策", "监管", "央行", "利率", "通胀", "关税", "制裁", "选举", "财政", "税", "SEC", "regulator"],
        "fallback": "政策监管线暂未形成高置信度主线，优先等待官方文件、央行表态和监管口径。",
    },
    {
        "key": "geopolitics",
        "title": "地缘政治、军事与安全",
        "categories": ["政策、监管与地缘"],
        "keywords": ["战争", "军事", "冲突", "停火", "军工", "航运", "安全", "边境", "war", "military", "ceasefire"],
        "fallback": "地缘安全线先观察能源、航运、军工和汇率传导，不把单条标题直接当作市场结论。",
    },
    {
        "key": "technology",
        "title": "科技与产业",
        "categories": ["科技与产业"],
        "keywords": ["AI", "算力", "半导体", "芯片", "机器人", "数据中心", "英伟达", "AMD", "台积电", "ASML", "微软", "Nvidia", "semiconductor"],
        "fallback": "科技产业重点看AI、半导体和机器人是否出现产业链共振，单个公司涨跌只能作为线索。",
    },
    {
        "key": "commodities",
        "title": "大宗商品、能源与供应链",
        "categories": ["大宗商品、能源与供应链"],
        "keywords": ["原油", "黄金", "铜", "天然气", "能源", "航运", "OPEC", "oil", "gold", "copper", "shipping"],
        "fallback": "大宗商品先看能源、贵金属、工业金属和航运是否连续变化，连续性比单日波动更重要。",
    },
    {
        "key": "companies",
        "title": "公司与资本运作",
        "categories": ["公司与资本运作"],
        "keywords": ["财报", "业绩", "收入", "利润", "指引", "并购", "回购", "IPO", "公告", "earnings", "guidance"],
        "fallback": "公司线优先回到公告、财报、电话会和管理层指引，避免把股价波动直接写成基本面变化。",
    },
]


def build_news_digest(brief: dict) -> dict:
    events = brief_events(brief)
    sections = [build_overview_section(brief, events)]
    sections.append(build_timeline_section(events))
    sections.extend(build_framework_sections(brief, events))
    sections.append(build_focus_section(brief, events))
    sections = [section for section in sections if section.get("items")]
    return {
        "version": "news-digest-v4",
        "date": brief.get("date", ""),
        "city": brief.get("city", ""),
        "overview": [item["thesis"] for item in sections[0].get("items", [])[:3]] if sections else [],
        "sections": sections,
    }


def build_overview_section(brief: dict, events: list[dict]) -> dict:
    items: list[dict] = []
    for event in events[:3]:
        title = clean_text(event.get("title"))
        if not title:
            continue
        items.append(news_item(
            thesis=f"{event_label(event)}是今天最值得先看的线索",
            summary=join_sentences([
                event.get("summary"),
                event.get("impact") and f"可能影响：{event.get('impact')}",
                event.get("verification") and f"下一步：{event.get('verification')}",
            ]),
            time_text=event.get("time", ""),
        ))
    if not items:
        items.append(news_item(
            "今天早报先把事实、解释和待核验事项分开",
            "信息源不足时不硬下判断；优先保留会影响宏观、行业、公司和今日行动的线索。",
        ))
    return {"title": "总览", "items": items[:3]}


def build_timeline_section(events: list[dict]) -> dict:
    items = []
    for event in events[:8]:
        title = event_label(event)
        summary = join_sentences([
            event.get("summary"),
            event.get("impact") and f"影响范围：{event.get('impact')}",
            event.get("verification") and f"后续观察：{event.get('verification')}",
        ])
        items.append(news_item(title, summary, event.get("time", "")))
    return {"title": "过去24小时重要事件", "items": items}


def build_framework_sections(brief: dict, events: list[dict]) -> list[dict]:
    sections = []
    for spec in SECTION_SPECS:
        matched = match_events(events, spec)
        items = [event_to_item(event, spec) for event in matched[:4]]
        if not items:
            items = build_data_items_for_section(brief, spec)
        if not items:
            items = [news_item(f"{spec['title']}暂无高置信度主线", spec["fallback"])]
        sections.append({"title": spec["title"], "items": items[:5]})
    return sections


def build_data_items_for_section(brief: dict, spec: dict) -> list[dict]:
    if spec["key"] == "china_market":
        return market_items(brief, ["中国", "香港", "A股", "上证", "深证", "沪深", "恒生", "China"])
    if spec["key"] == "global_macro":
        return market_items(brief, ["美国", "日本", "韩国", "欧洲", "US", "Japan", "Korea", "Europe", "NASDAQ", "S&P", "DAX", "KOSPI"])
    if spec["key"] == "technology":
        return theme_and_company_items(brief, ["AI", "算力", "半导体", "芯片", "机器人", "semiconductor", "NVDA", "AMD", "TSM", "ASML", "MSFT"])
    if spec["key"] == "commodities":
        return theme_items(brief, ["WTI", "原油", "黄金", "铜", "天然气", "能源", "航运", "oil", "gold", "copper"])
    if spec["key"] == "companies":
        return company_items(brief)
    return news_article_items(brief, spec["keywords"])


def build_focus_section(brief: dict, events: list[dict]) -> dict:
    items: list[dict] = []
    tasks = brief.get("outlook_tasks", []) or []
    for task in tasks[:2]:
        title = clean_text(task.get("title"))
        if not title:
            continue
        time_text = clean_text(task.get("time"))
        items.append(news_item(
            thesis=f"今天{(' ' + time_text) if time_text else ''}先处理：{title}",
            summary="这是把早报落到行动里的部分；看完信息后，至少形成一个当天可执行的小结果。",
        ))
    if events:
        top = events[0]
        items.append(news_item(
            thesis=f"今日复盘重点跟踪：{event_label(top)}",
            summary="晚上回看这条线索是否被价格、公告、政策或主流报道进一步验证，避免早上看过就结束。",
        ))
    return {"title": "今日重点观察", "items": items[:4]}


def event_to_item(event: dict, spec: dict) -> dict:
    thesis = event_label(event)
    summary = join_sentences([
        event.get("summary"),
        event.get("impact") and f"影响范围：{event.get('impact')}",
        event.get("verification") and f"后续观察：{event.get('verification')}",
    ])
    return news_item(thesis, summary or spec["fallback"], event.get("time", ""))


def market_items(brief: dict, keywords: list[str]) -> list[dict]:
    indices = (brief.get("market_data", {}) or {}).get("indices", []) or []
    matched = [item for item in indices if text_contains_any([item.get("region"), item.get("name"), item.get("symbol")], keywords)]
    ranked = sorted(matched, key=lambda item: abs(number(item.get("change_percent_from_previous_close") or item.get("change_percent_from_open")) or 0), reverse=True)
    items = []
    for item in ranked[:4]:
        name = name_of(item, "主要指数")
        region = clean_text(item.get("region"))
        change = change_of(item)
        items.append(news_item(
            thesis=f"{region}{name}{direction_from_value(change)}，重点看是否代表整体风险偏好变化",
            summary=f"最新点位 {format_number(price_of(item))}，较前收盘 {format_percent(change)}。指数变化要和利率、汇率、成交量、行业分化一起看，不能只用一个涨跌判断市场。",
            time_text=market_time(item),
        ))
    return items


def theme_and_company_items(brief: dict, keywords: list[str]) -> list[dict]:
    return (theme_items(brief, keywords) + company_items(brief, keywords))[:5]


def theme_items(brief: dict, keywords: list[str]) -> list[dict]:
    themes = (brief.get("theme_data", {}) or {}).get("items", []) or []
    matched = [item for item in themes if text_contains_any([item.get("name"), item.get("theme"), item.get("symbol")], keywords)]
    ranked = sorted(matched, key=lambda item: abs(change_of(item) or 0), reverse=True)
    items = []
    for item in ranked[:4]:
        name = name_of(item, "主题资产")
        change = change_of(item)
        items.append(news_item(
            thesis=f"{name}{direction_from_value(change)}，重点检查产业链是否共振",
            summary=f"较前收盘 {format_percent(change)}。主题价格变化要回到供需、库存、订单、政策和财报验证；只有多环节同向，才更接近产业趋势。",
            time_text=market_time(item),
        ))
    return items


def company_items(brief: dict, keywords: list[str] | None = None) -> list[dict]:
    companies = (brief.get("company_data", {}) or {}).get("items", []) or []
    if keywords:
        companies = [item for item in companies if text_contains_any([item.get("name"), item.get("symbol"), item.get("sector")], keywords)]
    ranked = sorted(companies, key=lambda item: abs(change_of(item.get("quote") or {}) or 0), reverse=True)
    items = []
    for company in ranked[:4]:
        quote = company.get("quote") or {}
        articles = company.get("articles") or []
        headline = clean_text((articles[0] or {}).get("title")) if articles else ""
        summary = f"股价较前收盘 {format_percent(change_of(quote))}。"
        if headline:
            summary += f" 相关线索：{compress(headline)}。"
        summary += "后续要回到公告、财报、电话会和管理层指引核验。"
        items.append(news_item(
            thesis=f"{company.get('name') or company.get('symbol') or '重点公司'}的变化要放回行业链条里看",
            summary=summary,
            time_text=market_time(quote),
        ))
    return items


def news_article_items(brief: dict, keywords: list[str]) -> list[dict]:
    articles = flatten_articles(brief.get("news_data", {}) or {})
    items = []
    for article in articles:
        title = clean_text(article.get("title"))
        if not title or not text_contains_any([title], keywords):
            continue
        items.append(news_item(
            thesis=f"{compress(title)}需要进入今日观察清单",
            summary="这条信息要先判断它影响的是利率、汇率、能源、军工、航运、跨境贸易还是公司盈利；传导链不清楚时只标记为线索。",
            time_text=iso_time(article.get("published")),
        ))
        if len(items) >= 4:
            break
    return items


def brief_events(brief: dict) -> list[dict]:
    timeline = brief.get("event_timeline", {}) or {}
    events = timeline.get("events", []) or []
    return sorted(events, key=event_sort_key, reverse=True)


def match_events(events: list[dict], spec: dict) -> list[dict]:
    matched = []
    for event in events:
        category = clean_text(event.get("category"))
        haystack = [event.get("title"), event.get("summary"), event.get("impact"), event.get("subject"), category]
        if category in spec.get("categories", []) or text_contains_any(haystack, spec.get("keywords", [])):
            matched.append(event)
    return matched


def event_label(event: dict) -> str:
    title = clean_text(event.get("title")) or "重点事件"
    category = clean_text(event.get("category"))
    if category and not title.startswith(category):
        return f"{category}：{title}"
    return title


def news_item(thesis: str, summary: str, time_text: str = "") -> dict:
    payload = {"thesis": clean_text(thesis), "summary": clean_text(summary)}
    if time_text:
        payload["time"] = clean_text(time_text)
    return payload


def flatten_articles(news_data: dict) -> list[dict]:
    articles: list[dict] = []
    for category in news_data.get("categories", []) or []:
        articles.extend(category.get("articles", []) or [])
    return articles


def event_sort_key(event: dict) -> tuple[float, str]:
    score = number(event.get("score")) or 0
    return score, clean_text(event.get("time"))


def text_contains_any(values: Any, keywords: list[str]) -> bool:
    if not isinstance(values, list):
        values = [values]
    text = " ".join(str(value or "") for value in values).lower()
    return any(str(keyword).lower() in text for keyword in keywords)


def name_of(item: dict, fallback: str) -> str:
    return clean_text(item.get("name")) or clean_text(item.get("symbol")) or fallback


def price_of(item: dict) -> float | int | None:
    return item.get("regular_market_price") or item.get("close") or item.get("price")


def change_of(item: dict) -> float | int | None:
    return number(item.get("change_percent_from_previous_close") or item.get("change_percent_from_open"))


def number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def direction_from_value(value: float | int | None) -> str:
    if value is None:
        return "变化待确认"
    if value > 0:
        return "走强"
    if value < 0:
        return "回落"
    return "基本持平"


def format_percent(value: float | int | None) -> str:
    if value is None:
        return "待确认"
    return f"{value:.2f}%"


def format_number(value: float | int | None) -> str:
    if value is None:
        return "待确认"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "待确认"


def market_time(item: dict) -> str:
    return timestamp_time(item.get("market_time"))


def timestamp_time(value: int | float | None) -> str:
    if not value:
        return ""
    dt = datetime.fromtimestamp(value, tz=timezone.utc).astimezone(BEIJING_TZ)
    return dt.strftime("%m-%d %H:%M")


def iso_time(value: str | None) -> str:
    if not value:
        return ""
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text).astimezone(BEIJING_TZ)
    except ValueError:
        return ""
    return dt.strftime("%m-%d %H:%M")


def compress(text: str, limit: int = 54) -> str:
    value = clean_text(text)
    if len(value) <= limit:
        return value
    return f"{value[:limit]}..."


def join_sentences(parts: list[Any]) -> str:
    cleaned = [clean_text(part) for part in parts if clean_text(part)]
    return " ".join(cleaned)


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").replace("\n", " ").split())
