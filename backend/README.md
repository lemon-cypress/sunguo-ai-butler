# 松果 Backend

第一阶段目标：先做一个可以运行的早安汇报 Demo。

## 运行方式

在 PowerShell 中进入项目目录：

```powershell
cd E:\松果\ai-butler
```

运行：

```powershell
python .\backend\app\morning_brief_demo.py
```

如果 `python` 不能用，试：

```powershell
py .\backend\app\morning_brief_demo.py
```

## 当前版本

这个版本使用假数据验证早报体验。

如果本地 `.env` 中配置了 `DEEPSEEK_API_KEY`，脚本会调用 DeepSeek 生成更自然的早报。

如果没有配置 API Key，或者调用失败，脚本会自动回退到模板版早报。

后续会逐步替换为：

- 真实天气 API
- 真实全球新闻和市场数据
- Outlook 日历读取和写入
- OpenAI API 生成自然语言播报
