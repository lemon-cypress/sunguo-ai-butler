from __future__ import annotations


def build_insights(brief: dict) -> dict:
    market = build_market_insights(brief.get("market_data", {}))
    news = build_news_insights(brief.get("news_data", {}))
    themes = build_theme_insights(brief.get("theme_data", {}))
    companies = build_company_insights(brief.get("company_data", {}))
    priorities = build_priority_insights(brief)
    return {
        "market": market,
        "news": news,
        "themes": themes,
        "companies": companies,
        "priorities": priorities,
        "disclaimer": "以下为早报线索和辅助判断，不构成投资建议；新闻标题需要进一步核验来源和原文。",
    }


def build_market_insights(market_data: dict) -> dict:
    indices = market_data.get("indices", [])
    movers = []
    by_region: dict[str, list[dict]] = {}

    for index in indices:
        change = index.get("change_percent_from_previous_close")
        if change is None:
            change = index.get("change_percent_from_open")
        if change is None:
            continue

        enriched = {
            "name": index.get("name", ""),
            "region": index.get("region", ""),
            "change_percent": change,
        }
        by_region.setdefault(enriched["region"], []).append(enriched)
        if abs(change) >= 1:
            movers.append(enriched)

    movers = sorted(movers, key=lambda item: abs(item["change_percent"]), reverse=True)
    tone = classify_market_tone([item["change_percent"] for item in movers])

    return {
        "source": market_data.get("source", "unknown"),
        "tone": tone,
        "notable_movers": movers[:5],
        "region_summary": summarize_regions(by_region),
        "watch_points": build_market_watch_points(movers),
    }


def classify_market_tone(changes: list[float]) -> str:
    if not changes:
        return "数据不足，暂不判断市场情绪"
    negative = sum(1 for value in changes if value <= -1)
    positive = sum(1 for value in changes if value >= 1)
    if negative >= max(2, positive + 1):
        return "偏谨慎，多个主要指数出现明显下跌"
    if positive >= max(2, negative + 1):
        return "偏积极，多个主要指数出现明显上涨"
    return "分化，适合先看结构再看方向"


def summarize_regions(by_region: dict[str, list[dict]]) -> list[str]:
    summary = []
    for region, items in by_region.items():
        if not items:
            continue
        avg = sum(item["change_percent"] for item in items) / len(items)
        summary.append(f"{region}平均变化约 {avg:.2f}%")
    return summary


def build_market_watch_points(movers: list[dict]) -> list[str]:
    if not movers:
        return ["先确认主要指数是否有一致方向，再看行业和公司新闻是否能解释变化。"]

    watch_points = []
    worst = min(movers, key=lambda item: item["change_percent"])
    best = max(movers, key=lambda item: item["change_percent"])
    if worst["change_percent"] <= -1:
        watch_points.append(f"关注{worst['region']}的{worst['name']}下跌是否由科技、汇率、利率或地缘因素驱动。")
    if best["change_percent"] >= 1:
        watch_points.append(f"关注{best['region']}的{best['name']}上涨是否有政策、财报或资金流支持。")
    watch_points.append("后续需要把指数变化和行业/公司公告对应起来，避免只看价格不看原因。")
    return watch_points


def build_news_insights(news_data: dict) -> dict:
    categories = news_data.get("categories", [])
    headline_groups = []
    keywords = {
        "earthquake": "自然灾害",
        "stock": "股市",
        "markets": "市场",
        "tech": "科技",
        "oil": "能源",
        "prices": "价格",
        "war": "地缘冲突",
        "military": "军事",
        "election": "政治",
        "chancellor": "财政政策",
        "fire": "公共安全",
    }
    topic_hits: dict[str, int] = {}

    for category in categories:
        articles = category.get("articles", [])
        titles = [article.get("title", "") for article in articles if article.get("title")]
        if titles:
            headline_groups.append(
                {
                    "label": category.get("label", category.get("category", "新闻")),
                    "top_titles": titles[:3],
                }
            )
        for title in titles:
            lower = title.lower()
            for key, label in keywords.items():
                if key in lower:
                    topic_hits[label] = topic_hits.get(label, 0) + 1

    topics = sorted(topic_hits.items(), key=lambda item: item[1], reverse=True)
    return {
        "source": news_data.get("source", "unknown"),
        "headline_groups": headline_groups,
        "possible_topics": [topic for topic, _ in topics[:5]],
        "watch_points": build_news_watch_points([topic for topic, _ in topics[:5]]),
    }


def build_news_watch_points(topics: list[str]) -> list[str]:
    if not topics:
        return ["新闻源暂时不足，先不要做强判断。"]

    points = []
    if "市场" in topics or "股市" in topics:
        points.append("把市场类新闻与主要指数涨跌放在一起看，寻找是否有共同解释。")
    if "能源" in topics or "价格" in topics:
        points.append("关注能源和产品价格变化是否会传导到通胀、运输、制造和消费。")
    if "地缘冲突" in topics or "军事" in topics:
        points.append("地缘风险需要单独标记，避免和普通市场波动混在一起。")
    if "公共安全" in topics or "自然灾害" in topics:
        points.append("社会事件更适合提示风险和影响范围，不宜直接推导投资结论。")
    if not points:
        points.append("先按宏观、市场、行业、社会四类归档，再决定是否进入正式早报。")
    return points


def build_theme_insights(theme_data: dict) -> dict:
    items = theme_data.get("items", [])
    rising = []
    falling = []

    for item in items:
        change = item.get("change_percent_from_previous_close")
        if change is None:
            continue
        enriched = {
            "name": item.get("name", ""),
            "theme": item.get("theme", ""),
            "change_percent": change,
            "affected_industries": item.get("affected_industries", []),
        }
        if change >= 1:
            rising.append(enriched)
        elif change <= -1:
            falling.append(enriched)

    rising = sorted(rising, key=lambda item: item["change_percent"], reverse=True)
    falling = sorted(falling, key=lambda item: item["change_percent"])
    return {
        "source": theme_data.get("source", "unknown"),
        "rising": rising[:5],
        "falling": falling[:5],
        "opportunity_watch": build_theme_watch_points(rising, falling),
    }


def build_theme_watch_points(rising: list[dict], falling: list[dict]) -> list[str]:
    points = []
    for item in rising[:3]:
        industries = "、".join(item.get("affected_industries", [])[:4])
        points.append(f"{item['name']}上涨约 {item['change_percent']}%，关注对{industries}的传导。")
    for item in falling[:2]:
        industries = "、".join(item.get("affected_industries", [])[:4])
        points.append(f"{item['name']}下跌约 {abs(item['change_percent'])}%，关注{industries}是否受益或承压。")
    if not points:
        points.append("主题价格暂无明显变化，先观察能源、金属、半导体和航运是否出现连续趋势。")
    points.append("这些只是机会线索，后续需要结合公司公告、库存、供需和政策验证。")
    return points


def build_company_insights(company_data: dict) -> dict:
    items = company_data.get("items", [])
    price_movers = []
    article_events = []
    event_keywords = {
        "earnings": "财报",
        "revenue": "收入",
        "guidance": "业绩指引",
        "profit": "利润",
        "orders": "订单",
        "capex": "资本开支",
        "AI": "AI",
        "chips": "芯片",
        "cloud": "云",
        "oil": "油价",
        "freight": "运价",
    }

    for item in items:
        quote = item.get("quote") or {}
        change = quote.get("change_percent_from_previous_close")
        if change is not None and abs(change) >= 2:
            price_movers.append(
                {
                    "name": item.get("name", ""),
                    "symbol": item.get("symbol", ""),
                    "sector": item.get("sector", ""),
                    "change_percent": change,
                }
            )

        for article in item.get("articles", [])[:2]:
            title = article.get("title", "")
            labels = []
            lower = title.lower()
            for keyword, label in event_keywords.items():
                if keyword.lower() in lower:
                    labels.append(label)
            article_events.append(
                {
                    "company": item.get("name", ""),
                    "symbol": item.get("symbol", ""),
                    "sector": item.get("sector", ""),
                    "title": title,
                    "url": article.get("url", ""),
                    "labels": labels[:3],
                }
            )

    price_movers = sorted(price_movers, key=lambda row: abs(row["change_percent"]), reverse=True)
    return {
        "source": company_data.get("source", "unknown"),
        "price_movers": price_movers[:6],
        "article_events": article_events[:8],
        "watch_points": build_company_watch_points(price_movers, article_events),
    }


def build_company_watch_points(price_movers: list[dict], article_events: list[dict]) -> list[str]:
    points = []
    for mover in price_movers[:3]:
        direction = "上涨" if mover["change_percent"] > 0 else "下跌"
        points.append(f"{mover['name']}股价{direction}约 {abs(mover['change_percent'])}%，需要核对是否与财报、指引或行业新闻有关。")
    for event in article_events[:3]:
        labels = "、".join(event.get("labels", [])) or "公告/新闻"
        points.append(f"{event['company']}出现{labels}线索：{event['title']}")
    if not points:
        points.append("公司观察池暂无明显价格或公告线索，先保持跟踪。")
    points.append("公司层面必须回到交易所公告、公司 IR 或财报原文核验。")
    return points


def build_priority_insights(brief: dict) -> list[str]:
    tasks = brief.get("outlook_tasks", [])
    high_priority = [task for task in tasks if task.get("priority") == "高"]
    priorities = []
    if high_priority:
        task = high_priority[0]
        priorities.append(f"今天先处理 {task.get('time', '')} 的「{task.get('title', '')}」。")
    priorities.append("早报产品下一步要提升解读质量：少列标题，多讲为什么值得关注。")
    priorities.append("财经数据先当作线索，继续把价格变化连接到行业、公司和公告。")
    return priorities
