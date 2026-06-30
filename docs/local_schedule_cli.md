# 本地日程命令工具

Outlook 功能暂缓后，松果先使用本地日程文件：

```text
backend/data/local_schedule.json
```

你可以直接编辑这个 JSON，也可以用下面的命令维护。

## 查看日程

```powershell
cd E:\松果\ai-butler
python .\backend\app\local_schedule_cli.py list
```

## 添加日程

```powershell
python .\backend\app\local_schedule_cli.py add --start 16:00 --end 16:30 --title "整理松果下一步任务" --importance high --preparation "把今天遇到的问题写成 3 条"
```

可选字段：

- `--location`：地点，默认是 `本地`
- `--importance`：重要性，可选 `low`、`normal`、`high`
- `--preparation`：松果早报里提醒你提前准备什么

## 删除日程

先查看编号：

```powershell
python .\backend\app\local_schedule_cli.py list
```

再删除对应编号，例如删除第 1 条：

```powershell
python .\backend\app\local_schedule_cli.py delete 1
```

## 生成早报

改完本地日程后，重新生成早报：

```powershell
python .\backend\app\morning_brief_demo.py --save
```
