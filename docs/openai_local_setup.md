# OpenAI API Key 本地配置

## 重要原则

不要把 API Key 发到聊天里。

不要把 API Key 写进 README、代码文件或 GitHub。

松果项目已经把 `.env` 加进 `.gitignore`，所以本地 `.env` 文件不会被上传。

## 1. 创建 `.env` 文件

打开 PowerShell：

```powershell
cd E:\松果\ai-butler
notepad .env
```

如果提示是否创建新文件，点“是”。

填入：

```text
OPENAI_API_KEY=你的真实_api_key
OPENAI_MODEL=gpt-5.5
DEFAULT_CITY=北京-朝阳
TIMEZONE=Asia/Shanghai
```

保存后关闭记事本。

## 2. 运行 AI 生成版早报

```powershell
cd E:\松果\ai-butler
python .\backend\app\morning_brief_demo.py
```

如果你的电脑上 `python` 命令不可用，试：

```powershell
py .\backend\app\morning_brief_demo.py
```

## 3. 如果模型报错

如果看到类似“model not found”或“没有权限”的错误，把 `.env` 里的模型改成你 OpenAI 后台可用的模型。

例如：

```text
OPENAI_MODEL=gpt-5.1
```

保存后重新运行脚本。

## 4. 如果中文乱码

在 PowerShell 里先运行：

```powershell
chcp 65001
```

然后再运行：

```powershell
python .\backend\app\morning_brief_demo.py
```

## 5. 当前脚本的行为

- 如果 `.env` 里有 `OPENAI_API_KEY`，脚本会调用 OpenAI 生成自然语言早报。
- 如果没有 API Key，脚本会自动回退到模板版早报。
- 如果 OpenAI 调用失败，脚本会显示错误原因，并回退到模板版早报。

