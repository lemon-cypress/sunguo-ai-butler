from __future__ import annotations


def build_brief_analysis(brief: dict) -> dict:
    insights = brief.get("insights", {})
    stories = []

    market_story = build_market_story(brief, insights)
    if market_story:
        stories.append(market_story)

    theme_story = build_theme_story(brief, insights)
    if theme_story:
        stories.append(theme_story)

    company_story = build_company_story(brief, insights)
    if company_story:
        stories.append(company_story)

    news_story = build_news_story(brief, insights)
    if news_story:
        stories.append(news_story)

    schedule_story = build_schedule_story(brief)
    if schedule_story:
        stories.append(schedule_story)

    top_stories = stories[:3]
    return {
        "version": "brief-analysis-v1",
        "today_overview": build_overview(brief, top_stories),
        "top_stories": top_stories,
        "quality_rules": [
            "先讲结论，再讲证据。",
            "区分事实、线索和需要核验的推断。",
            "财经内容只做信息整理，不给买卖建议。",
        ],
    }


def build_market_story(brief: dict, insights: dict) -> dict | None:
    market = insights.get("market", {})
    movers = market.get("notable_movers", [])
    if not movers:
        return None

    strongest = sorted(movers, key=lambda item: abs(item.get("change_percent", 0)), reverse=True)[0]
    tone = market.get("tone", "市场方向待确认")
    evidence = f"{strongest.get('region', '')}{strongest.get('name', '')}变动约 {strongest.get('change_percent')}%。"
    return story(
        story_id="market",
        title=f"市场情绪：{tone}",
        why_it_matters="主要指数的同步变化会影响今天对风险偏好、行业强弱和公司新闻的解读顺序。",
        evidence=[evidence] + market.get("region_summary", [])[:2],
        impact=["全球市场", "科技/半导体", "汇率和利率预期"],
        confidence="中",
        source=brief.get("market_data", {}).get("source", "unknown"),
        follow_up=market.get("watch_points", [])[:2],
    )


def build_theme_story(brief: dict, insights: dict) -> dict | None:
    themes = insights.get("themes", {})
    candidates = themes.get("rising", []) + themes.get("falling", [])
    if not candidates:
        return None

    strongest = sorted(candidates, key=lambda item: abs(item.get("change_percent", 0)), reverse=True)[0]
    direction = "上涨" if strongest.get("change_percent", 0) > 0 else "下跌"
    industries = strongest.get("affected_industries", [])[:4]
    return story(
        story_id="themes",
        title=f"{strongest.get('name', '主题价格')}{direction}，关注产业传导",
        why_it_matters="商品和主题价格变化会传导到成本、利润率、通胀预期和相关行业情绪。",
        evidence=[f"{strongest.get('name', '')}{direction}约 {abs(strongest.get('change_percent', 0))}%。"],
        impact=industries or ["能源", "金属", "半导体", "航运"],
        confidence="中",
        source=brief.get("theme_data", {}).get("source", "unknown"),
        follow_up=themes.get("opportunity_watch", [])[:2],
    )


def build_company_story(brief: dict, insights: dict) -> dict | None:
    companies = insights.get("companies", {})
    movers = companies.get("price_movers", [])
    events = companies.get("article_events", [])
    if not movers and not events:
        return None

    if movers:
        strongest = sorted(movers, key=lambda item: abs(item.get("change_percent", 0)), reverse=True)[0]
        direction = "上涨" if strongest.get("change_percent", 0) > 0 else "下跌"
        title = f"{strongest.get('name', '重点公司')}{direction}，需要核验原因"
        evidence = [f"{strongest.get('name', '')}{direction}约 {abs(strongest.get('change_percent', 0))}%。"]
        impact = [strongest.get("sector", "公司观察池")]
    else:
        event = events[0]
        title = f"{event.get('company', '重点公司')}出现新闻线索"
        evidence = [event.get("title", "出现公司新闻线索")]
        impact = [event.get("sector", "公司观察池")]

    return story(
        story_id="companies",
        title=title,
        why_it_matters="公司层面的价格和新闻线索能帮助判断行业变化是否已经传导到具体企业。",
        evidence=evidence,
        impact=impact,
        confidence="线索",
        source=brief.get("company_data", {}).get("source", "unknown"),
        follow_up=companies.get("watch_points", [])[:2],
    )


def build_news_story(brief: dict, insights: dict) -> dict | None:
    news = insights.get("news", {})
    topics = news.get("possible_topics", [])
    if not topics:
        return None

    headline = first_headline(news)
    return story(
        story_id="news",
        title=f"新闻主题：{'、'.join(topics[:3])}",
        why_it_matters="新闻主题可以解释市场情绪，但标题本身不能直接当作最终事实。",
        evidence=[headline] if headline else topics[:3],
        impact=topics[:4],
        confidence="线索",
        source=brief.get("news_data", {}).get("source", "unknown"),
        follow_up=news.get("watch_points", [])[:2],
    )


def build_schedule_story(brief: dict) -> dict | None:
    tasks = brief.get("outlook_tasks", [])
    if not tasks:
        return None

    high = [task for task in tasks if task.get("priority") == "高"]
    task = high[0] if high else tasks[0]
    return story(
        story_id="schedule",
        title=f"今天先处理：{task.get('title', '')}",
        why_it_matters="项目推进要有一个清楚的当日抓手，避免早报只是看信息而不形成行动。",
        evidence=[f"{task.get('time', '')}｜{task.get('title', '')}｜优先级：{task.get('priority', '')}"],
        impact=["松果项目", "今日待办"],
        confidence="高",
        source=brief.get("schedule", {}).get("source", "local"),
        follow_up=["先完成最小可交付物，再扩展新能力。"],
    )


def build_overview(brief: dict, stories: list[dict]) -> str:
    if not stories:
        return "今天先保持轻量观察：天气、日程和市场线索都已整理，重点是把信息转成可执行行动。"

    first = stories[0]["title"]
    second = stories[1]["title"] if len(stories) > 1 else "待办事项已整理"
    return f"今天的早报重点是：{first}；同时关注{second}。我会把未核验内容标成线索，避免把标题直接当结论。"


def first_headline(news: dict) -> str:
    for group in news.get("headline_groups", []):
        titles = group.get("top_titles", [])
        if titles:
            return titles[0]
    return ""


def story(
    story_id: str,
    title: str,
    why_it_matters: str,
    evidence: list[str],
    impact: list[str],
    confidence: str,
    source: str,
    follow_up: list[str],
) -> dict:
    return {
        "id": story_id,
        "title": title,
        "why_it_matters": why_it_matters,
        "evidence": [item for item in evidence if item],
        "impact": [item for item in impact if item],
        "confidence": confidence,
        "source": source,
        "follow_up": [item for item in follow_up if item],
    }
