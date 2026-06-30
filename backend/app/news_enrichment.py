from __future__ import annotations


EVENT_RULES = [
    ("earnings", "财报/业绩", "优先核对公司财报、电话会纪要和交易所披露。"),
    ("revenue", "收入", "核对收入增速、分业务拆分和管理层指引。"),
    ("guidance", "业绩指引", "核对公司原文指引，以及分析师预期是否同步变化。"),
    ("profit", "利润", "核对利润率、成本项和一次性项目。"),
    ("margin", "利润率", "核对毛利率、经营利润率和成本变化。"),
    ("orders", "订单", "核对订单金额、交付周期、客户和是否进入正式公告。"),
    ("backlog", "在手订单", "核对订单可见度和未来收入确认节奏。"),
    ("capex", "资本开支", "核对资本开支方向、供应商和产能周期。"),
    ("tariff", "关税/贸易", "核对政策原文、生效时间和受影响商品范围。"),
    ("sanction", "制裁", "核对官方公告、涉及主体和执行细节。"),
    ("rate cut", "降息", "核对央行声明、点阵图或利率期货定价。"),
    ("interest rate", "利率", "核对央行口径、债券收益率和市场预期。"),
    ("inflation", "通胀", "核对CPI/PPI原始数据和分项。"),
    ("oil", "油价", "核对供需、库存、OPEC消息和地缘风险。"),
    ("copper", "铜", "核对库存、需求、地产链和制造业数据。"),
    ("AI", "AI", "核对具体产品、订单、客户和资本开支证据。"),
    ("chip", "芯片", "核对产业链位置、出货、库存和价格。"),
    ("cloud", "云计算", "核对云收入增速、资本开支和AI贡献。"),
    ("data center", "数据中心", "核对资本开支、供电、GPU/服务器订单。"),
    ("war", "地缘冲突", "核对官方消息和对能源、航运、军工的传导。"),
    ("military", "军事", "核对官方通报、地点、参与方和影响范围。"),
    ("election", "选举", "核对结果、政策方向和市场预期变化。"),
    ("earthquake", "自然灾害", "核对灾害规模、供应链影响和救援进展。"),
]

SOURCE_TIERS = [
    ("sec.gov", "监管披露", "高"),
    ("www.sec.gov", "监管披露", "高"),
    ("prnewswire.com", "公司新闻稿", "中"),
    ("globenewswire.com", "公司新闻稿", "中"),
    ("businesswire.com", "公司新闻稿", "中"),
    ("ir.", "公司IR", "中"),
    ("reuters.com", "权威媒体", "中"),
    ("bloomberg.com", "权威媒体", "中"),
    ("wsj.com", "权威媒体", "中"),
    ("ft.com", "权威媒体", "中"),
    ("cnbc.com", "财经媒体", "中"),
    ("yahoo.com", "聚合/转载", "线索"),
    ("finance.yahoo.com", "聚合/转载", "线索"),
    ("news.google.com", "聚合/转载", "线索"),
]


def enrich_news_snapshot(news_data: dict) -> dict:
    enriched_categories = []
    for category in news_data.get("categories", []):
        articles = [enrich_article(article, category.get("label", "")) for article in category.get("articles", [])]
        enriched_categories.append({**category, "articles": articles})
    return {
        **news_data,
        "categories": enriched_categories,
        "event_summary": summarize_events(enriched_categories),
        "enrichment_version": "news-enrichment-v1",
    }


def enrich_company_snapshot(company_data: dict) -> dict:
    enriched_items = []
    for item in company_data.get("items", []):
        articles = [enrich_article(article, item.get("name", "")) for article in item.get("articles", [])]
        enriched_items.append({**item, "articles": articles, "event_summary": summarize_company_events(articles)})
    return {
        **company_data,
        "items": enriched_items,
        "enrichment_version": "news-enrichment-v1",
    }


def enrich_article(article: dict, context: str = "") -> dict:
    title = article.get("title", "")
    url = article.get("url", "")
    labels = classify_title(title)
    source_type, confidence = classify_source(url)
    return {
        **article,
        "event_labels": labels,
        "source_type": source_type,
        "confidence": confidence,
        "verification_hint": build_verification_hint(labels, source_type, context),
    }


def classify_title(title: str) -> list[str]:
    lower = title.lower()
    labels = []
    for keyword, label, _ in EVENT_RULES:
        if keyword.lower() in lower and label not in labels:
            labels.append(label)
    return labels[:4]


def classify_source(url: str) -> tuple[str, str]:
    lower = url.lower()
    for marker, source_type, confidence in SOURCE_TIERS:
        if marker in lower:
            return source_type, confidence
    return "普通新闻源", "线索"


def build_verification_hint(labels: list[str], source_type: str, context: str) -> str:
    if source_type in {"监管披露", "公司IR"}:
        return "来源相对接近原始披露，但仍要核对日期、口径和全文。"

    for _, label, hint in EVENT_RULES:
        if label in labels:
            return hint

    if context:
        return f"先确认这条线索是否直接关系到{context}，再回到原始来源核验。"
    return "先回到原始报道或官方披露核验，不把标题直接当作结论。"


def summarize_events(categories: list[dict]) -> list[dict]:
    counts: dict[str, int] = {}
    examples: dict[str, str] = {}
    for category in categories:
        for article in category.get("articles", []):
            for label in article.get("event_labels", []):
                counts[label] = counts.get(label, 0) + 1
                examples.setdefault(label, article.get("title", ""))
    return [
        {"label": label, "count": count, "example": examples.get(label, "")}
        for label, count in sorted(counts.items(), key=lambda row: row[1], reverse=True)
    ][:8]


def summarize_company_events(articles: list[dict]) -> list[str]:
    items = []
    for article in articles[:3]:
        labels = "、".join(article.get("event_labels", [])) or article.get("source_type", "新闻线索")
        title = article.get("title", "")
        if title:
            items.append(f"{labels}：{title}")
    return items

