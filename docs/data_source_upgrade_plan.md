# 松果数据源升级计划

目标：把当前的免费公开数据源升级为“可切换、可扩展、可逐步付费替换”的数据层。

## 当前默认数据源

- 天气：`WEATHER_PROVIDER=open_meteo`
- 市场：`MARKET_PROVIDER=yahoo`
- 新闻：`NEWS_PROVIDER=rss`
- 主题/商品：`THEME_PROVIDER=yahoo`
- 公司观察池：`COMPANY_PROVIDER=watchlist`

## 已经完成的工程准备

- `config.py` 已支持 provider 配置项
- `morning_brief_demo.py` 已支持按 provider 分流
- 当前真实可用 provider：
  - `open_meteo`
  - `yahoo`
  - `rss`
  - `watchlist`
- 下一步可直接接入的目标 provider：
  - `alphavantage`
  - `marketaux`
  - `finnhub`
  - `polygon`
  - `newsapi`
  - `gdelt`

## 推荐升级顺序

### 第一阶段：先升级新闻层

推荐：

- `NEWS_PROVIDER=marketaux`

原因：

- 比 RSS 更像正式财经资讯 API
- 更适合全球财经、公司事件、情绪分析
- 对松果“每天讲讲发生了什么”提升最大

### 第二阶段：升级市场与商品层

推荐优先级：

1. `alphavantage`
2. `finnhub`
3. `polygon`

建议：

- 如果更重视性价比和覆盖面，优先 `alphavantage`
- 如果更重视投资助手能力，优先 `finnhub`
- 如果更重视美股实时与工程稳定性，优先 `polygon`

### 第三阶段：升级全球事件层

推荐：

- `gdelt`
- 或 `newsapi` 作为较轻量的通用新闻补充

原因：

- 政治、军事、社会、国际热点更适合单独建一层

## 建议的配置方式

```text
MARKETAUX_API_KEY=your_key
ALPHAVANTAGE_API_KEY=your_key
FINNHUB_API_KEY=your_key
POLYGON_API_KEY=your_key
NEWSAPI_API_KEY=your_key

MARKET_PROVIDER=alphavantage
NEWS_PROVIDER=marketaux
THEME_PROVIDER=alphavantage
COMPANY_PROVIDER=watchlist
```

## 实施建议

### 方案 A：轻付费升级

- 新闻：Marketaux
- 市场：Alpha Vantage
- 主题：Alpha Vantage
- 公司：先保留 watchlist + SEC

适合当前松果阶段。

### 方案 B：偏投资助手

- 新闻：Marketaux
- 市场：Finnhub 或 Polygon
- 公司：Finnhub
- 全球事件：GDELT

更适合以后做高强度投研陪伴。

## 下一步代码任务

1. 新建 `marketaux_client.py`
2. 新建 `alphavantage_client.py`
3. 在 `morning_brief_demo.py` 中把对应 provider 从占位报错改成真实 API 调用
4. 在网页中展示 provider 名称与成功/失败状态

## 当前已完成

- `marketaux_client.py` 已接入
- `NEWS_PROVIDER=marketaux` 已能在主流程里调用
- 当前抓取接口：
  - `GET https://api.marketaux.com/v1/news/all`
- 当前默认拉取：
  - 过去 24 小时
  - 英文
  - 中国、美国、日本、韩国、英国、德国、法国
  - 自动去相似新闻

## 立即可用的配置

在 `.env` 里填写：

```text
MARKETAUX_API_KEY=你的真实key
NEWS_PROVIDER=marketaux
NEWS_MAX_RECORDS_PER_QUERY=10
```

然后运行：

```powershell
python .\backend\app\morning_brief_demo.py --save
```

如果暂时不用 Marketaux，改回：

```text
NEWS_PROVIDER=rss
```
