# 公司核验入口 v1

目标：当松果发现公司新闻或价格异动时，不只提示“需要核验”，还给出优先核验入口。

## 新增模块

`backend/app/verification_sources.py`

当前为重点公司维护：

- Investor Relations 页面。
- SEC/EDGAR 披露页面。
- Yahoo Finance 报价页面。

## 已接入位置

- `company_client.py`：公司观察池抓取时，为每家公司附加 `verification_sources`。
- `financial_reasoning.py`：公司线索会把官方入口放进 `follow_up` 和结构化字段。
- `qa_builder.py`：追问“公司核验入口”“微软官方链接”“AMD 核验入口”时，会优先回答对应公司。
- `frontend/app.js`：网页追问同步支持具体公司筛选。
- `output_builder.py`：财经解读卡片会显示前两条后续核验建议，包含官方入口。

## 可以这样问

- 公司核验入口在哪里？
- 微软官方链接在哪里？
- AMD 核验入口在哪里？
- 英伟达财报去哪里核验？

## 当前边界

- 这些链接是核验入口，不代表已经自动读取并验证了公告全文。
- 下一版可以接入 SEC companyfacts、财报日历、公司 IR 新闻稿 RSS 或交易所公告源，进一步自动抽取原文证据。
