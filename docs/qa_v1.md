# 追问能力 v1

## 目标

让松果可以围绕当天早报继续回答：

- 今天最重要的三件事是什么？
- 为什么重要？
- 有哪些证据？
- 影响哪些对象？
- 下一步核验什么？
- 数据源是否可靠？
- 今天有哪些待办和提醒？
- 松果记住了哪些偏好？

## 当前实现方式

v1 不调用大模型，直接基于最新早报里的结构化数据回答。这样稳定、免费、可解释，也方便先把产品体验跑顺。

主要读取：

```text
demos/latest.json
demos/YYYY-MM-DD/output_bundle.json
output_bundle.brief_analysis
output_bundle.finance_reasoning
output_bundle.reminder_plan
output_bundle.screen_cards
output_bundle.source_summary
output_bundle.memory_summary
```

## 后端能力

核心文件：

```text
backend/app/qa_builder.py
backend/app/ask_sunguo.py
backend/app/dashboard_server.py
```

已支持：

- 摘要追问：今天最重要的三件事。
- 事件追问：为什么重要、证据、影响、下一步核验。
- 财经追问：市场、板块、公司、原因、影响、官方披露、核验入口。
- 日程追问：今天待办、松果项目下一步。
- 提醒追问：今天会提醒什么、是否有吃药提醒。
- 记忆追问：关注国家、行业、公司、生活提醒、当前项目重点。
- 来源追问：天气、市场、新闻、主题、公司、日程的数据来源。

## 命令行追问

```powershell
cd E:\松果\ai-butler
python .\backend\app\ask_sunguo.py 今天最重要的三件事是什么？
```

也可以问：

```powershell
python .\backend\app\ask_sunguo.py 第一件事为什么重要？
python .\backend\app\ask_sunguo.py 有哪些证据？
python .\backend\app\ask_sunguo.py 下一步需要核验什么？
python .\backend\app\ask_sunguo.py 数据可靠吗？
python .\backend\app\ask_sunguo.py 半导体为什么下跌？
python .\backend\app\ask_sunguo.py 微软最近披露是什么？
python .\backend\app\ask_sunguo.py 今天松果项目该做什么？
```

JSON 输出：

```powershell
python .\backend\app\ask_sunguo.py 半导体为什么下跌？ --json
```

## 网页追问

启动 API 版网页：

```powershell
.\scripts\start_dashboard_api.ps1
```

打开：

```text
http://127.0.0.1:8765/frontend/
```

页面底部有“追问松果”区域，可以输入问题，也可以点击快捷问题按钮。

如果网页由 `dashboard_server.py` 启动，会优先调用：

```text
POST /api/ask
```

如果 API 不可用，网页会自动回退到浏览器本地规则回答。

## 下一步升级

- 接入 DeepSeek，让松果可以回答更自由的问题。
- 给每个回答增加“事实 / 推测 / 待核验”的明显标签。
- 把回答接入 TTS，让松果能把追问答案读出来。
- 让数字人根据回答类型切换表情和动作。
- 增加追问历史，让松果知道上一轮问了什么。
