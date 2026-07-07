from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

BEIJING_TZ = timezone(timedelta(hours=8))


def build_news_digest(brief: dict) -> dict:
    sections = [
        build_overview_section(brief),
        build_china_market_section(brief),
        build_global_macro_section(brief),
        build_policy_section(brief),
        build_technology_section(brief),
        build_company_section(brief),
        build_commodity_section(brief),
        build_focus_section(brief),
    ]
    sections = [section for section in sections if section.get("items")]
    overview = [
        item["thesis"]
        for section in sections[:3]
        for item in section.get("items", [])[:1]
        if item.get("thesis")
    ]
    return {
        "version": "news-digest-v3",
        "date": brief.get("date", ""),
        "city": brief.get("city", ""),
        "overview": overview[:3],
        "sections": sections,
    }


def build_overview_section(brief: dict) -> dict:
    analysis = brief.get("brief_analysis", {}) or {}
    stories = analysis.get("top_stories", []) or []
    items: list[dict] = []
    for story in stories[:3]:
        title = clean_text(story.get("title"))
        why = clean_text(story.get("why_it_matters"))
        follow = first_text(story.get("follow_up"))
        if not title:
            continue
        summary = why or "先把这件事放进今日观察清单，后续用数据和公告核验。"
        if follow:
            summary = f"{summary} 后续重点看：{follow}"
        items.append(news_item(title, summary))
    if not items:
        items.append(news_item("今天早报先把事实、解释和待核验事项分开，避免把标题直接当结论", "信息源不足时不硬下判断；优先保留会影响宏观、行业、公司和今日行动的线索。"))
    return {"title": "今日总览", "items": items[:3]}


def build_china_market_section(brief: dict) -> dict:
    market = brief.get("market_data", {}) or {}
    indices = [
        item for item in market.get("indices", [])
        if text_contains_any(item.get("region"), ["中国", "China", "香港", "A股"])
        or text_contains_any(item.get("name"), ["上证", "深证", "沪深", "恒生", "China"])
    ]
    themes = (brief.get("theme_data", {}) or {}).get("items", [])
    items: list[dict] = []
    if indices:
        main_index = strongest_move(indices)
        items.append(news_item(
            f"中国市场先看指数方向和成交量是否共振，{name_of(main_index, '主要指数')}{direction_word(main_index)}",
            f"最新点位 {format_number(price_of(main_index))}，较前收盘 {format_percent(change_of(main_index))}。如果只是单个指数变化，暂不直接推导市场风格；下一步重点看政策预期、人民币、地产链、消费和科技成长是否同向。",
            market_time(main_index),
        ))
    else:
        items.append(news_item("中国市场暂不从单日价格下结论，先等待指数、汇率和政策信号互相验证", "指数数据不足时，重点观察地产链、消费复苏、科技自主可控和高股息资产有没有共同方向。"))
    semi_theme = find_theme(themes, ["半导体", "芯片", "semiconductor"])
    if semi_theme:
        items.append(news_item(
            f"半导体链是中国科技线的核心温度计，{name_of(semi_theme, '半导体主题')}{direction_word(semi_theme)}",
            f"较前收盘 {format_percent(change_of(semi_theme))}。不能只看单个标的；后续要同时核验设备、材料、设计、制造和封测是否一起走强。",
            market_time(semi_theme),
        ))
    return {"title": "中国市场", "items": items[:4]}


def build_global_macro_section(brief: dict) -> dict:
    indices = (brief.get("market_data", {}) or {}).get("indices", [])
    regions = ["美国", "日本", "韩国", "欧洲"]
    items: list[dict] = []
    for region in regions:
        candidates = [
            item for item in indices
            if text_contains_any(item.get("region"), [region])
            or text_contains_any(item.get("name"), [region, region_alias(region)])
        ]
        if not candidates:
            continue
        index = strongest_move(candidates)
        items.append(news_item(
            f"{region}市场的关键不是涨跌本身，而是风险偏好是否扩散，{name_of(index, '主要指数')}{direction_word(index)}",
            f"最新点位 {format_number(price_of(index))}，较前收盘 {format_percent(change_of(index))}。下一步看同一区域内科技、银行、能源和消费是否同步，否则更像局部交易。",
            market_time(index),
        ))
    if not items:
        items.append(news_item("全球市场先用利率、美元、能源和科技股四条线组织信息", "没有稳定价格数据时，不做方向判断；先确认美债收益率、美元指数、AI龙头和原油价格是否同向变化。"))
    return {"title": "全球市场与宏观", "items": items[:5]}


def build_policy_section(brief: dict) -> dict:
    articles = flatten_articles(brief.get("news_data", {}) or {})
    keywords = ["fed", "rate", "inflation", "tariff", "sanction", "election", "war", "military", "ceasefire", "policy", "监管", "利率", "通胀", "关税", "制裁", "选举", "军事", "冲突"]
    items: list[dict] = []
    for article in articles:
        title = clean_text(article.get("title"))
        if not title or not text_contains_any(title, keywords):
            continue
        items.append(news_item(
            f"{compress(title)}需要放进政策和地缘框架里判断",
            "这类事件要看它影响的是利率、汇率、能源、军工、航运还是跨境贸易；如果传导链不清晰，先列为待核验。",
            iso_time(article.get("published")),
        ))
        if len(items) >= 4:
            break
    if not items:
        items.append(news_item("政策、监管与地缘暂未形成高置信度主线", "这一栏先保持观察，不用低质量标题填充；后续优先补充全球宏观、央行、地缘和监管数据源。"))
    return {"title": "政策、监管与地缘", "items": items}


def build_technology_section(brief: dict) -> dict:
    themes = (brief.get("theme_data", {}) or {}).get("items", [])
    company_items = (brief.get("company_data", {}) or {}).get("items", [])
    theme_specs = [
        ("AI算力", ["AI", "算力", "人工智能"]),
        ("半导体", ["半导体", "芯片", "semiconductor"]),
        ("机器人", ["机器人", "robot"]),
        ("创新药", ["创新药", "biotech"]),
        ("新能源", ["新能源", "solar", "battery"]),
    ]
    items: list[dict] = []
    for label, keywords in theme_specs:
        theme = find_theme(themes, keywords)
        if not theme:
            continue
        items.append(news_item(
            f"{label}不能只看一个标的，要看产业链是否同向，{name_of(theme, label)}{direction_word(theme)}",
            f"较前收盘 {format_percent(change_of(theme))}。如果主题上涨但公告、订单、库存和财报没有跟上，只能当交易线索；多环节共同验证时，才更接近产业趋势。",
            market_time(theme),
        ))
        if len(items) >= 3:
            break
    company = find_company(company_items, {"NVDA", "AMD", "TSM", "ASML", "MSFT"})
    if company:
        quote = company.get("quote") or {}
        items.append(news_item(
            f"{company.get('name', '重点科技公司')}是观察科技风险偏好的前哨，股价{direction_from_value(change_of(quote))}",
            f"较前收盘 {format_percent(change_of(quote))}。个股变化需要回到财报、管理层指引和订单验证，单日涨跌不能替代基本面判断。",
            market_time(quote),
        ))
    if not items:
        items.append(news_item("科技与产业先看AI、半导体和机器人三条线是否共振", "后续要接入公司公告、财报日历和产业新闻，避免只靠普通新闻标题判断产业变化。"))
    return {"title": "科技与产业", "items": items[:4]}


def build_company_section(brief: dict) -> dict:
    company_items = (brief.get("company_data", {}) or {}).get("items", [])
    ranked = sorted(company_items, key=lambda item: abs(change_of(item.get("quote") or {}) or 0), reverse=True)
    items: list[dict] = []
    for company in ranked[:4]:
        quote = company.get("quote") or {}
        articles = company.get("articles") or []
        headline = clean_text((articles[0] or {}).get("title")) if articles else ""
        summary = f"股价较前收盘 {format_percent(change_of(quote))}。"
        if headline:
            summary += f" 相关线索是：{compress(headline)}。"
        summary += "重点是核验公告、财报、电话会和管理层口径是否支持这次变化。"
        items.append(news_item(
            f"{company.get('name', '重点公司')}的变化要放回行业链条里看",
            summary,
            market_time(quote) or iso_time((articles[0] or {}).get("published") if articles else ""),
        ))
    if not items:
        items.append(news_item("公司与资本运作先保留观察池，不把低置信标题写成结论", "下一步要接入公告、财报日历、交易所文件和公司IR，才能判断事件对公司价值的影响。"))
    return {"title": "公司与资本运作", "items": items}


def build_commodity_section(brief: dict) -> dict:
    themes = (brief.get("theme_data", {}) or {}).get("items", [])
    keywords = ["WTI", "原油", "天然气", "黄金", "铜", "航运", "能源"]
    items: list[dict] = []
    for keyword in keywords:
        item = find_theme(themes, [keyword])
        if not item:
            continue
        items.append(news_item(
            f"{name_of(item, keyword)}影响的是通胀、成本和产业利润分配，价格{direction_word(item)}",
            f"较前收盘 {format_percent(change_of(item))}。如果能源和工业金属连续变化，要同步看上游资源、制造业成本和下游需求。",
            market_time(item),
        ))
        if len(items) >= 3:
            break
    if not items:
        items.append(news_item("大宗商品暂未形成足够明确的单独主线", "先看能源、贵金属、工业金属和航运是否出现连续变化；连续性比单日波动更重要。"))
    return {"title": "大宗商品、能源与供应链", "items": items}


def build_focus_section(brief: dict) -> dict:
    tasks = brief.get("outlook_tasks", []) or []
    priorities = (brief.get("insights") or {}).get("priorities", []) or []
    items: list[dict] = []
    for task in tasks[:2]:
        title = clean_text(task.get("title")) or "重点事项"
        time_text = clean_text(task.get("time"))
        items.append(news_item(f"今天{(' ' + time_text) if time_text else ''}先处理：{title}", "这是把早报落到行动里的部分；信息看完以后，至少形成一个当天可执行的小结果。"))
    for priority in priorities[:2]:
        text = clean_text(priority)
        if text:
            items.append(news_item(text, "这是松果项目今天最值得推进的抓手，优先做能让产品体验明显变好的那一步。"))
    return {"title": "今日重点观察", "items": items[:4]}


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


def find_theme(items: list[dict], keywords: list[str]) -> dict | None:
    for item in items:
        haystack = " ".join([str(item.get("name", "")), str(item.get("theme", "")), str(item.get("symbol", ""))]).lower()
        if any(keyword.lower() in haystack for keyword in keywords):
            return item
    return None


def find_company(items: list[dict], symbols: set[str]) -> dict | None:
    for item in items:
        if str(item.get("symbol", "")).upper() in symbols:
            return item
    return items[0] if items else None


def strongest_move(items: list[dict]) -> dict:
    return sorted(items, key=lambda item: abs(change_of(item) or 0), reverse=True)[0]


def text_contains_any(value: Any, keywords: list[str]) -> bool:
    text = str(value or "").lower()
    return any(keyword.lower() in text for keyword in keywords)


def name_of(item: dict, fallback: str) -> str:
    return clean_text(item.get("name")) or clean_text(item.get("symbol")) or fallback


def price_of(item: dict) -> float | int | None:
    return item.get("regular_market_price") or item.get("close") or item.get("price")


def change_of(item: dict) -> float | int | None:
    return item.get("change_percent_from_previous_close") or item.get("change_percent_from_open")


def direction_word(item: dict) -> str:
    return direction_from_value(change_of(item))


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
    return f"{value:,.2f}"


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


def compress(text: str, limit: int = 46) -> str:
    value = clean_text(text)
    if len(value) <= limit:
        return value
    return f"{value[:limit]}..."


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").replace("\n", " ").split())


def first_text(value: Any) -> str:
    if isinstance(value, list) and value:
        return clean_text(value[0])
    return clean_text(value)


def region_alias(region: str) -> str:
    aliases = {"美国": "US", "日本": "Japan", "韩国": "Korea", "欧洲": "Europe"}
    return aliases.get(region, region)
