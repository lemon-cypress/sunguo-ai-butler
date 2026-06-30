# 财经解读框架 v1

目标：让松果早报不只罗列涨跌，而是把财经线索整理成固定的研究结构。

## 输出结构

`backend/app/financial_reasoning.py` 会生成：

- `summary`：今天财经线索的总览。
- `rules`：财经内容输出规则。
- `market`：主要指数线索。
- `themes`：商品、主题和行业价格线索。
- `companies`：公司观察池线索。

每条线索包含：

- `fact`：已经看到的数据或新闻线索。
- `possible_reason`：可能原因，只能作为待核验假设。
- `impact`：可能影响的行业、公司或资产。
- `follow_up`：下一步应该核验什么。
- `confidence`：可信度或线索等级。
- `source`：来源。

## 已接入位置

- `morning_brief_demo.py`：生成 `finance_reasoning`。
- `output_builder.py`：写入 `output_bundle.json`，并生成 `finance-reasoning` 屏幕卡片。
- `qa_builder.py`：支持追问原因、影响、核验。
- `frontend/app.js`：网页追问也支持财经问题。

## 可以这样追问

- 今天市场为什么变化？
- 这些变化影响哪些行业？
- 下一步核验什么？
- 今天有哪些财经机会线索？

## 当前边界

- 这不是投资建议。
- 新闻标题只作为线索，需要回到公告、财报、交易所披露、权威媒体或原始数据源核验。
- 下一版可以继续加入公司公告源、财报日历和宏观事件日历。
