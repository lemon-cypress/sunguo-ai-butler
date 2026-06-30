# SEC 最近披露 v1

目标：在公司观察池里自动补充最近官方披露元数据，让松果可以回答“某家公司最近披露是什么”。

## 新增模块

`backend/app/sec_client.py`

它会从 SEC `data.sec.gov/submissions` 读取公司最近披露元数据，并筛选：

- `10-K`
- `10-Q`
- `8-K`
- `20-F`
- `6-K`

输出字段包括：

- `form`：披露类型。
- `filing_date`：提交日期。
- `report_date`：报告日期。
- `url`：SEC 原文链接。
- `use_for`：这类披露适合核验什么。

## 已接入位置

- `verification_sources.py`：为重点公司维护 CIK。
- `company_client.py`：公司观察池抓取时附加 `official_filings`。
- `financial_reasoning.py`：公司线索 follow-up 中加入最近 SEC 披露。
- `qa_builder.py`：支持“微软最近披露是什么”“AMD 最近 SEC 披露是什么”。
- `frontend/app.js`：网页追问同步支持披露类问题。

## 可以这样问

- 微软最近披露是什么？
- AMD 最近 SEC 披露是什么？
- 英伟达 10-Q 去哪里看？
- 公司最近 8-K 是什么？

## 当前边界

- 当前只抓披露元数据和原文链接，不自动解析财报正文。
- SEC 请求需要网络可用，并且未来最好配置正式 User-Agent 联系邮箱。
- 下一版可以解析 10-Q/10-K/8-K 的标题、Item 编号、财务摘要和风险因素变化。
