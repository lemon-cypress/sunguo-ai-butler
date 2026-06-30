# 可配置提醒 v2

目标：让松果的主动提醒从“代码写死”升级为“本地配置”，后续可以接网页编辑、Windows 通知和手机推送。

## 文件

- 配置文件：`backend/data/reminders.json`
- 生成模块：`backend/app/reminder_builder.py`
- 管理工具：`backend/app/reminder_cli.py`
- 输出字段：`reminder_plan`

## 当前能力

- 从本地日程生成提前 10 分钟提醒。
- 从 `reminders.json` 读取固定提醒，例如出门检查、补水、伸展、晚间收尾。
- 根据天气自动生成雨具提醒。
- 吃药提醒已预置模板，默认关闭，避免替用户假设药品安排。
- `reminder_plan` 会输出时间、类型、优先级、提醒话术、触发规则、语音风格、数字人动作。
- 网页和命令行追问支持“今天会提醒我什么？”

## 常用命令

列出提醒：

```powershell
python .\backend\app\reminder_cli.py list
```

启用吃药提醒：

```powershell
python .\backend\app\reminder_cli.py enable 吃药
```

关闭吃药提醒：

```powershell
python .\backend\app\reminder_cli.py disable 吃药
```

新增一条提醒：

```powershell
python .\backend\app\reminder_cli.py add --time 22:30 --title 刷牙 --message "睡前记得刷牙，明天醒来会舒服一点。" --type health
```

## 下一步

1. 做 Windows 桌面通知或浏览器通知。
2. 网页上增加“启用/关闭/新增提醒”的表单。
3. 支持重复规则，例如工作日、周末、每天、每周几。
4. 把提醒完成情况写入本地记忆，用来让松果更像真正的私人管家。