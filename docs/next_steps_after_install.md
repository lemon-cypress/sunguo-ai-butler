# 安装完成后的下一步

## 1. 重启电脑或重新打开终端

如果刚安装完 Python、Git、VS Code、GitHub Desktop，建议先重启一次电脑。

重启后打开 PowerShell，运行：

```powershell
python --version
pip --version
git --version
code --version
```

如果 `python --version` 不行，试：

```powershell
py --version
```

## 2. 运行松果第一个早报 Demo

进入项目目录：

```powershell
cd E:\松果\ai-butler
```

运行：

```powershell
python .\backend\app\morning_brief_demo.py
```

如果 `python` 不行，试：

```powershell
py .\backend\app\morning_brief_demo.py
```

## 3. 你应该看到什么

你会看到一份文字版早安汇报，包括：

- 北京-朝阳天气和穿衣建议
- 全球市场和宏观
- 行业、板块和公司线索
- 政治、军事和社会新闻
- 松果项目今日任务
- 今日待办
- 生活细节提醒
- 历史故事
- 笑话

## 4. API Key 先不要填

你已经拿到了 OpenAI API Key，但现在先不要发到聊天里。

下一步我们会创建本地 `.env` 文件，把 key 放进去：

```text
OPENAI_API_KEY=你的_key
```

`.env` 已经被 `.gitignore` 忽略，不会上传到 GitHub。

## 5. Outlook 暂时先不接

Outlook 读写日历下一阶段做。

原因：

- 需要 Microsoft Graph。
- 需要 OAuth 授权。
- 需要创建 Azure App。
- 需要谨慎处理日历写入权限。

第一阶段我们先用假日程模拟，等早报体验跑通后再接真实 Outlook。

