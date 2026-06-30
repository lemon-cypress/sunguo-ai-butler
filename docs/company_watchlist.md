# 公司观察池

## 当前目标

让松果开始跟踪重点公司的价格变化、财报/公告/指引/订单等新闻线索。

当前数据源：

- 公司价格：Yahoo Finance chart 公开接口。
- 公司新闻线索：Google News RSS 搜索。

## 观察池文件

位置：

```text
backend/data/company_watchlist.json
```

每家公司包含：

```json
{
  "symbol": "NVDA",
  "name": "英伟达",
  "sector": "AI算力/半导体",
  "keywords": ["earnings", "guidance", "AI chips", "data center"]
}
```

## 当前覆盖方向

- AI 算力/半导体
- 半导体制造
- 半导体设备
- 云/AI 应用
- 能源
- 航运

## 运行

```powershell
cd E:\松果\ai-butler
python .\backend\app\morning_brief_demo.py --save
```

默认只抓观察池前 5 家公司，避免早报生成太慢。可在 `.env` 调整：

```text
COMPANY_MAX_COUNT=5
COMPANY_TIMEOUT_SECONDS=10
COMPANY_NEWS_MAX_RECORDS=2
```

跳过真实公司数据：

```powershell
python .\backend\app\morning_brief_demo.py --mock-companies --save
```

## 注意

- 新闻标题只是线索，不代表公告已核验。
- 真正严肃的公司事件需要回到交易所公告、公司 IR 或财报原文。
- 后续可以增加 A 股、港股公司观察池。
