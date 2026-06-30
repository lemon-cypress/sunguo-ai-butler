# 本地日程方案

## 为什么先不用 Outlook

公司 Microsoft 365 的 Outlook 日历接入需要管理员批准。当前阶段为了避免卡在企业权限流程，松果先使用本地日程文件。

Outlook 模块保留，但暂缓。

## 本地日程文件

位置：

```text
backend/data/local_schedule.json
```

格式：

```json
{
  "source": "local",
  "events": [
    {
      "start": "09:30",
      "end": "10:00",
      "title": "检查今日日程和项目优先级",
      "location": "本地",
      "importance": "high",
      "preparation": "打开松果项目目录，确认今天要完成的最小交付物。"
    }
  ]
}
```

## 如何修改今天日程

打开：

```powershell
notepad .\backend\data\local_schedule.json
```

修改 `events` 里的内容。

保存后运行：

```powershell
python .\backend\app\morning_brief_demo.py --save
```

## 后续升级

等公司授权可用后，可以把：

```text
OUTLOOK_FEATURE_ENABLED=false
USE_REAL_OUTLOOK=false
```

改成：

```text
OUTLOOK_FEATURE_ENABLED=true
USE_REAL_OUTLOOK=true
```

松果会尝试读取 Microsoft Graph；失败时仍然回退本地日程。
