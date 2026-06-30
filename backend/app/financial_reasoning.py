from __future__ import annotations


def build_finance_reasoning(brief: dict) -> dict:
    """Build a repeatable fact-reason-impact-check framework for finance content."""
    market_data = brief.get("market_data", {})
    theme_data = brief.get("theme_data", {})
    company_data = brief.get("company_data", {})
    memory = brief.get("memory_summary", {})

    market_items = build_market_reasoning(market_data)
    theme_items = build_theme_reasoning(theme_data)
    company_items = build_company_reasoning(company_data)
    all_items = market_items + theme_items + company_items

    return {
        "version": "finance-reasoning-v1",
        "summary": build_summary(all_items, memory),
        "rules": [
            "先说事实，再说可能原因，不把价格变化直接当成结论。",
            "每条线索都要说明可能影响谁，以及下一步该核验什么。",
            "投资相关内容只做信息整理和研究线索，不给买卖建议。",
        ],
        "market": market_items,
        "themes": theme_items,
        "companies": company_items,
        "source": {
            "market": market_data.get("source", "unknown"),
            "themes": theme_data.get("source", "unknown"),
            "companies": company_data.get("source", "unknown"),
        },
    }


def build_market_reasoning(market_data: dict) -> list[dict]:
    items = []
    for index in market_data.get("indices", [])[:8]:
        change = first_number(index.get("change_percent_from_previous_close"), index.get("change_percent_from_open"))
        if change is None:
            continue
        if abs(change) < 1:
            continue

        region = index.get("region", "")
        name = index.get("name", "")
        direction = direction_text(change)
        items.append(
            reasoning_item(
                title=f"{region}{name}{direction}",
                fact=f"{name}较前收盘约{format_percent(change)}，属于需要关注的指数波动。",
                possible_reason=market_reason(region, name, change),
                impact=market_impact(region, name, change),
                follow_up=[
                    "核对同一区域其他主要指数是否同向变化。",
                    "查看利率、汇率、政策预期、科技股和大宗商品是否有共同解释。",
                ],
                confidence="中",
                source=market_data.get("source", "unknown"),
            )
        )
    return sorted(items, key=lambda item: item["abs_change"], reverse=True)[:5]


def build_theme_reasoning(theme_data: dict) -> list[dict]:
    items = []
    for item in theme_data.get("items", [])[:10]:
        change = item.get("change_percent_from_previous_close")
        if change is None or abs(change) < 1:
            continue

        name = item.get("name", "")
        theme = item.get("theme", "")
        industries = item.get("affected_industries", [])[:4]
        direction = direction_text(change)
        items.append(
            reasoning_item(
                title=f"{name}{direction}",
                fact=f"{theme}里的{name}较前收盘约{format_percent(change)}。",
                possible_reason=theme_reason(theme, name, change),
                impact=f"可能影响：{'、'.join(industries) if industries else '相关产业链'}。",
                follow_up=[
                    "核对现货、期货、库存、供需和政策消息是否同步支持。",
                    "再看相关公司公告、财报和行业新闻，避免只根据价格波动下判断。",
                ],
                confidence="中",
                source=theme_data.get("source", "unknown"),
            )
        )
    return sorted(items, key=lambda row: row["abs_change"], reverse=True)[:5]


def build_company_reasoning(company_data: dict) -> list[dict]:
    items = []
    for item in company_data.get("items", [])[:10]:
        quote = item.get("quote") or {}
        change = quote.get("change_percent_from_previous_close")
        articles = item.get("articles", [])
        if change is None and not articles:
            continue
        if change is not None and abs(change) < 2 and not articles:
            continue

        name = item.get("name", "")
        sector = item.get("sector", "")
        first_article = articles[0] if articles else {}
        verification_sources = item.get("verification_sources", [])
        official_filings = item.get("official_filings", [])
        headline = first_article.get("title", "")
        fact_parts = []
        if change is not None:
            fact_parts.append(f"股价较前收盘约{format_percent(change)}")
        if headline:
            labels = "、".join(first_article.get("event_labels", [])) or first_article.get("source_type", "新闻线索")
            fact_parts.append(f"出现{labels}线索：{headline}")

        items.append(
            reasoning_item(
                title=f"{name}需要核验原因",
                fact="；".join(fact_parts),
                possible_reason=company_reason(name, sector, headline, change, first_article),
                impact=f"可能影响：{sector or '公司观察池'}，以及同一产业链里的可比公司。",
                follow_up=[
                    first_article.get("verification_hint", "优先核对公司公告、财报、投资者关系材料和交易所披露。"),
                    format_official_filings(official_filings),
                    format_verification_sources(verification_sources),
                    "把新闻标题当作线索，不直接当作已经确认的事实。",
                ],
                confidence="线索",
                source=company_data.get("source", "unknown"),
                verification_sources=verification_sources,
                official_filings=official_filings,
            )
        )
    return sorted(items, key=lambda row: row["abs_change"], reverse=True)[:6]


def build_summary(items: list[dict], memory: dict) -> str:
    if not items:
        return "今天财经数据先保持观察：暂时没有足够强的价格或新闻线索，需要继续收集证据。"

    focus = memory.get("industries", [])[:3]
    focus_text = f"，尤其留意{'、'.join(focus)}" if focus else ""
    return f"今天财经部分先抓{len(items)}条高优先级线索{focus_text}；每条都按事实、可能原因、影响对象和后续核验来整理。"


def reasoning_item(
    title: str,
    fact: str,
    possible_reason: str,
    impact: str,
    follow_up: list[str],
    confidence: str,
    source: str,
    verification_sources: list[dict] | None = None,
    official_filings: list[dict] | None = None,
) -> dict:
    change = extract_change(fact)
    return {
        "title": title,
        "fact": fact,
        "possible_reason": possible_reason,
        "impact": impact,
        "follow_up": follow_up,
        "confidence": confidence,
        "source": source,
        "verification_sources": verification_sources or [],
        "official_filings": official_filings or [],
        "abs_change": abs(change) if change is not None else 0,
    }


def market_reason(region: str, name: str, change: float) -> str:
    if change < 0:
        return f"可能与{region}风险偏好下降、利率/汇率变化、科技股回调或政策预期变化有关，需要继续核验。"
    return f"可能与{region}风险偏好修复、政策预期、资金流入或大型权重股表现有关，需要继续核验。"


def market_impact(region: str, name: str, change: float) -> str:
    if any(token in name for token in ["纳斯达克", "日经", "KOSPI", "半导体"]):
        return "可能影响：科技股、半导体、AI算力、消费电子和相关ETF情绪。"
    if region in {"中国", "美国", "欧洲", "日本", "韩国"}:
        return f"可能影响：{region}市场风险偏好、跨市场资金流向和今天的行业强弱判断。"
    return "可能影响：整体风险偏好和资产配置情绪。"


def theme_reason(theme: str, name: str, change: float) -> str:
    if change > 0:
        return f"可能与{theme}供需、库存、避险情绪、政策预期或资金交易有关。"
    return f"可能与{theme}需求预期走弱、库存变化、美元/利率变化或风险偏好回落有关。"


def format_official_filings(filings: list[dict]) -> str:
    if not filings:
        return "官方披露：暂未抓到最近 SEC 文件，先使用公司 IR 和 SEC 页面核验。"
    filing = filings[0]
    summary = filing.get("document_summary", {}) or {}
    items = "；".join(summary.get("items", [])[:3])
    title = summary.get("title", "")
    extra = ""
    if items:
        extra = f" 摘要：{items}"
    elif title:
        extra = f" 标题：{title}"
    return (
        f"最近官方披露：{filing.get('form', '')}，提交日 {filing.get('filing_date', '')}，"
        f"用于：{filing.get('use_for', '')}{extra} 链接：{filing.get('url', '')}"
    )

def format_verification_sources(sources: list[dict]) -> str:
    if not sources:
        return "优先核对公司公告、财报、投资者关系材料和交易所披露。"
    top_sources = sources[:2]
    text = "；".join(f"{source.get('label', '核验入口')}：{source.get('url', '')}" for source in top_sources)
    return f"官方核验入口：{text}"

def company_reason(name: str, sector: str, headline: str, change: float | None, article: dict | None = None) -> str:
    reasons = []
    if change is not None and abs(change) >= 2:
        reasons.append("价格波动较明显，可能与财报、指引、订单、行业景气或资金交易有关")
    if headline:
        labels = "、".join((article or {}).get("event_labels", []))
        if labels:
            reasons.append(f"新闻标题指向{labels}事件")
        else:
            reasons.append("新闻标题提供了一个待核验方向")
    if sector:
        reasons.append(f"还要放回{sector}产业链里比较")
    return "；".join(reasons) + "。"


def first_number(*values) -> float | None:
    for value in values:
        if isinstance(value, (int, float)):
            return float(value)
    return None


def direction_text(change: float) -> str:
    return "上涨" if change > 0 else "下跌"


def format_percent(change: float) -> str:
    return f"{change:.2f}%"


def extract_change(text: str) -> float | None:
    marker = "约"
    if marker not in text or "%" not in text:
        return None
    raw = text.split(marker, 1)[1].split("%", 1)[0]
    try:
        return float(raw)
    except ValueError:
        return None




