# 财经与新闻数据源

## 当前目标

先把真实市场和新闻线索接入松果早报，不追求一开始就做成专业终端。

当前接入：

- 市场指数：Yahoo Finance chart 公开接口。
- 新闻线索：RSS feed。
- 商品/主题价格：Yahoo Finance chart 公开接口。
- 公司观察池：Yahoo Finance chart + Google News RSS。

## 重要边界

- 指数数据用于早报线索，不作为交易系统。
- 新闻标题是线索，不等于事实核验完成。
- 投资内容只做“值得关注的方向”，不做买卖建议。

## 配置

`.env` 中默认：

```text
USE_REAL_MARKETS=true
MARKET_SYMBOLS_PATH=backend/data/market_symbols.json
USE_REAL_NEWS=true
NEWS_FEEDS_PATH=backend/data/news_feeds.json
NEWS_MAX_RECORDS_PER_QUERY=5
USE_REAL_THEMES=true
THEME_SYMBOLS_PATH=backend/data/theme_symbols.json
USE_REAL_COMPANIES=true
COMPANY_WATCHLIST_PATH=backend/data/company_watchlist.json
COMPANY_NEWS_MAX_RECORDS=3
```

## 市场指数列表

位置：

```text
backend/data/market_symbols.json
```

你可以在里面添加或删除指数。

## 新闻查询列表

位置：

```text
backend/data/news_feeds.json
```

每一项包括：

```json
{
  "category": "business",
  "label": "商业财经",
  "url": "https://feeds.bbci.co.uk/news/business/rss.xml"
}
```

## 运行

```powershell
cd E:\松果\ai-butler
python .\backend\app\morning_brief_demo.py --save
```

查看结构化输入：

```powershell
python .\backend\app\morning_brief_demo.py --show-json
```

如果网络不稳定，可以跳过真实市场和新闻：

```powershell
python .\backend\app\morning_brief_demo.py --mock-market --mock-news --mock-themes --mock-companies --save
```

## 主题/商品价格列表

位置：

```text
backend/data/theme_symbols.json
```

当前包括：

- 原油
- 天然气
- 黄金
- 铜
- 半导体 ETF
- 能源 ETF
- 航运 ETF
