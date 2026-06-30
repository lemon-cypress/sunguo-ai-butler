# 松果

松果是一个有数字人形象的 AI 私人管家项目。

第一阶段先做 Character-to-Agent 软件原型：早安汇报、全球关键事件、天气穿衣建议、Outlook 日程和待办。

## 当前进度

- 产品 MVP 文档已完成。
- 角色圣经 v1 已完成。
- 早报需求 v1 已完成。
- 第一个假数据早安汇报 Demo 已创建。

## 第一个运行命令

```powershell
cd E:\松果\ai-butler
python .\backend\app\morning_brief_demo.py
```

保存每天的早报：

```powershell
python .\backend\app\morning_brief_demo.py --save
```

只看结构化输入：

```powershell
python .\backend\app\morning_brief_demo.py --show-json
```

不调用模型，强制模板版：

```powershell
python .\backend\app\morning_brief_demo.py --no-ai
```

不调用真实天气，强制假天气：

```powershell
python .\backend\app\morning_brief_demo.py --mock-weather --no-ai
```

不调用真实市场/新闻：

```powershell
python .\backend\app\morning_brief_demo.py --mock-market --mock-news --mock-themes --mock-companies --no-ai
```

打开早报网页：

```powershell
python -m http.server 8765
```

也可以直接用脚本启动网页：

```powershell
.\scripts\start_dashboard.ps1
```

浏览器访问：

```text
http://localhost:8765/frontend/
```

Outlook 登录授权：

```powershell
python .\backend\app\outlook_auth.py
```

读取今日 Outlook 日程：

```powershell
python .\backend\app\outlook_calendar.py
```

## DeepSeek setup

Create a .env file with:

```text
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_MODEL=deepseek-v4-flash
DEFAULT_CITY=Beijing-Chaoyang
TIMEZONE=Asia/Shanghai
```

## Voice upgrade

To make the voice more natural, install the neural TTS package:

```powershell
python -m pip install edge-tts
```

Then add this to `.env`:

```text
TTS_ENGINE=auto
TTS_VOICE=zh-CN-XiaoxiaoNeural
```

Notes:

- `auto` tries `edge-tts` first, then falls back to Windows SAPI.
- If `edge-tts` is not installed, the project still works with the local voice.
- This path should make Sunguo sound closer to a real human assistant.

Details:

- `docs/deepseek_local_setup.md`
- `docs/openai_local_setup.md`
- `docs/output_layer.md`
- `docs/web_dashboard.md`
- `docs/brief_quality_v2.md`
- `docs/qa_v1.md`
- `docs/local_memory_v1.md`
- `docs/financial_reasoning_v1.md`
- `docs/news_enrichment_v1.md`
- `docs/company_verification_sources_v1.md`
- `docs/sec_filings_v1.md`
- `docs/aliyun_ecs_domain_deploy.md`
- `docs/github_publish.md`
- `docs/ecs_github_update_workflow.md`
