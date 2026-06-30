# 网页编辑提醒 v1

目标：让松果提醒可以在网页里查看、启用、关闭和新增，不再必须手工编辑 `backend/data/reminders.json`。

## 启动方式

推荐运行：

```powershell
.\scripts\start_dashboard_api.ps1
```

或者手动启动：

```powershell
python .\backend\app\dashboard_server.py --port 8765
```

然后打开：

```text
http://127.0.0.1:8765/frontend/
```

## 当前能力

- `GET /api/reminders`：读取提醒配置。
- `POST /api/reminders/add`：新增固定提醒。
- `POST /api/reminders/toggle`：按标题启用或关闭提醒。
- `POST /api/brief/regenerate`：在网页里重新生成早报。
- 网页会显示“提醒配置”面板。
- 面板里有“重新生成早报”和“快速测试生成”两个按钮。
- 如果仍使用普通 `python -m http.server 8765`，网页可查看早报，但会提示编辑服务未启动。

## 注意

保存配置后，需要重新生成早报，新的提醒才会进入当天 `reminder_plan`。
“重新生成早报”会刷新正式早报并自动刷新页面；“快速测试生成”只验证生成链路，不覆盖正式早报页面。

