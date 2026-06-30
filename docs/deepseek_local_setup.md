# DeepSeek API 本地配置

## 为什么可以用 DeepSeek

DeepSeek API 支持 OpenAI 兼容格式。官方文档中的 OpenAI 兼容 `base_url` 是：

```text
https://api.deepseek.com
```

聊天接口是：

```text
https://api.deepseek.com/chat/completions
```

当前项目默认使用：

```text
deepseek-v4-flash
```

后续如果需要更强推理，可以改成：

```text
deepseek-v4-pro
```

## 1. 获取 DeepSeek API Key

1. 打开 DeepSeek Platform：

```text
https://platform.deepseek.com/
```

2. 注册或登录账号。
3. 进入 API Keys 页面。
4. 创建一个新的 API Key。
5. 复制保存。不要发到聊天里，也不要上传 GitHub。

## 2. 配置 `.env`

打开 PowerShell：

```powershell
cd E:\松果\ai-butler
notepad .env
```

填入：

```text
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的_deepseek_key
DEEPSEEK_MODEL=deepseek-v4-flash
DEFAULT_CITY=北京-朝阳
TIMEZONE=Asia/Shanghai
```

保存后关闭记事本。

## 3. 运行

```powershell
cd E:\松果\ai-butler
python .\backend\app\morning_brief_demo.py
```

如果 `python` 不可用：

```powershell
py .\backend\app\morning_brief_demo.py
```

## 4. 如果失败

常见原因：

- DeepSeek 账号没有余额。
- API Key 填错。
- `.env` 文件不在 `E:\松果\ai-butler` 目录。
- 网络无法访问 `api.deepseek.com`。
- 模型名写错。

如果输出模板版早报，并显示 DeepSeek 错误信息，把错误截图发我即可。

