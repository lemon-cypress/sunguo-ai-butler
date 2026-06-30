from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date


@dataclass(frozen=True)
class MarketEvent:
    region: str
    summary: str
    possible_driver: str


@dataclass(frozen=True)
class Task:
    time: str
    title: str
    priority: str


def build_mock_brief(
    city: str = "北京-朝阳",
    weather: dict | None = None,
    schedule: dict | None = None,
    market_data: dict | None = None,
    news_data: dict | None = None,
    theme_data: dict | None = None,
    company_data: dict | None = None,
) -> dict:
    """Build a first mock morning brief without external APIs."""
    markets = [
        MarketEvent(
            "中国",
            "主要指数小幅震荡，市场继续关注政策预期和成交量变化。",
            "宏观政策、人民币汇率、地产和消费数据。",
        ),
        MarketEvent(
            "美国",
            "科技股仍是市场关注焦点，投资者关注通胀、利率和大型公司财报。",
            "美联储利率路径、AI 资本开支、企业盈利。",
        ),
        MarketEvent(
            "日本/韩国",
            "出口、半导体和汇率仍然影响市场情绪。",
            "日元走势、芯片产业链、全球需求。",
        ),
        MarketEvent(
            "欧洲",
            "市场关注通胀回落、央行政策和能源价格。",
            "欧洲央行政策、能源供给、制造业数据。",
        ),
    ]

    tasks = [
        Task("09:30", "检查今天日程，确认是否有会议需要提前准备", "高"),
        Task("14:00", "整理松果早报的固定栏目", "中"),
        Task("20:30", "复盘今天学习和项目进度", "中"),
    ]

    return {
        "date": date.today().isoformat(),
        "city": city,
        "weather": weather or {
            "source": "mock",
            "condition": "多云转晴",
            "temperature": "22-31°C",
            "rain": "降雨概率较低",
            "outfit": "建议穿轻薄短袖或衬衫，早晚如果外出久一些，可以带一件薄外套。",
        },
        "markets": [asdict(event) for event in markets],
        "market_data": market_data or {
            "source": "mock",
            "indices": [],
            "note": "市场数据暂未接入。",
        },
        "industry": [
            "AI 算力、半导体、机器人、创新药、新能源和消费电子是第一批需要持续跟踪的方向。",
            "后续真实版本会抓取公司公告、财报和行业新闻，并区分事实、推测和投资线索。",
        ],
        "news_data": news_data or {
            "source": "mock",
            "categories": [],
            "note": "新闻数据暂未接入。",
        },
        "theme_data": theme_data or {
            "source": "mock",
            "items": [],
            "note": "主题价格数据暂未接入。",
        },
        "company_data": company_data or {
            "source": "mock",
            "items": [],
            "note": "公司观察池暂未接入。",
        },
        "politics_and_society": [
            "政治和军事板块会关注地缘冲突、选举、制裁、外交和军费变化。",
            "社会新闻会筛选公共安全、科技应用、教育、医疗和城市治理相关事件。",
        ],
        "sunguo_project": [
            "今天的松果项目任务是把日程能力从 Outlook 迁移到本地日程文件。",
            "保留 Outlook 模块作为以后公司授权后的可选能力。",
            "下一步优先推进财经/新闻真实数据源。",
        ],
        "schedule": schedule or {
            "source": "local",
            "events": [],
            "write_proposals": [],
            "safety_note": "当前使用本地日程文件。",
        },
        "outlook_tasks": [asdict(task) for task in tasks],
        "life_reminders": [
            "记得刷牙、喝水，出门前看一下钥匙和手机。",
            "如果今天久坐，上午和下午各做一次 3 分钟拉伸。",
            "晚上可以简单整理桌面，让明天早上开始得更轻松。",
        ],
        "history_story": (
            "今天的小故事：乔布斯早年非常重视产品演示。他明白用户往往不是先理解技术细节，"
            "而是先被一个清楚、有画面感的体验打动。松果也一样，第一版先把每天早上的核心体验做顺。"
        ),
        "joke": "今天的小笑话：程序员说自己很会做饭，因为他每次都严格按照菜谱执行，直到发现盐也有版本兼容问题。",
    }
