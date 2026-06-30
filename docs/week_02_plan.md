# 第 2 周行动清单

## 本周目标

把松果从“一次性 Demo”变成“每天都能产出早报文件的小工具”。

## 已完成

- DeepSeek 接入跑通。
- 松果可以根据结构化假数据生成早报。
- 支持 OpenAI / DeepSeek 两种模型供应商。
- API Key 放在本地 `.env`，不上传 GitHub。
- 北京-朝阳真实天气接入完成，当前使用 Open-Meteo。
- 天气接口失败时会自动回退到内置假天气。
- Outlook 模拟日程接入完成。
- 日历写入确认草案接入完成，但不会自动写入真实日历。
- 公司 Outlook 需要管理员批准，当前阶段改为本地日程方案。
- 本地日程文件 `backend/data/local_schedule.json` 已接入早报。
- Outlook 功能总开关默认关闭，不再影响当前早报主线。
- 财经/新闻真实数据源已接入。
- 早报解读层 `insights` 已接入，减少机械罗列。

## 本周新增能力

### 1. 保存每日早报

运行：

```powershell
cd E:\松果\ai-butler
python .\backend\app\morning_brief_demo.py --save
```

会保存：

```text
demos/YYYY-MM-DD/morning_brief_input.json
demos/YYYY-MM-DD/morning_brief.txt
```

### 2. 查看结构化输入

运行：

```powershell
python .\backend\app\morning_brief_demo.py --show-json
```

这个命令用来检查松果“拿到的原始信息”是什么。

### 3. 强制模板模式

运行：

```powershell
python .\backend\app\morning_brief_demo.py --no-ai
```

这个命令方便排查问题：如果模型接口失败，模板版仍然应该稳定可用。

## 你这周需要做什么

1. 每天至少跑一次：

```powershell
python .\backend\app\morning_brief_demo.py --save
```

2. 看生成的 `morning_brief.txt`，记录三类问题：

- 哪些栏目有用？
- 哪些栏目太啰嗦？
- 哪些栏目缺少真实数据？

3. 决定下一步优先接哪个真实数据源：

- 天气
- 财经/新闻
- 本地待办

## 当前建议的下一步

天气已经接入完成。

Outlook 因公司授权要求暂缓。

下一步建议接财经/新闻真实数据源。

原因：

- 新闻和市场数据需要来源、时间、去重和事实核验。
- 财经内容要避免把“观点”说成“事实”。
- 这是你最重视的早报核心内容之一。

财经/新闻真实数据源已接入，下一步建议继续细化：

- 行业板块专题。
- 公司公告和财报。
- 商品价格上涨线索。
