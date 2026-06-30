# Outlook 日历接入计划

## 当前状态

松果当前已经接入“模拟 Outlook 日程”：

- 可以在早报里展示今日事项。
- 可以生成“建议写入日历的事项”。
- 不会自动创建、修改或删除真实日历事件。

## 安全原则

真实接入 Outlook 后仍然遵守：

- 读取日历：可以在用户授权后自动读取。
- 写入日历：必须先展示待写入内容。
- 修改日历：必须先展示原事件和修改后事件。
- 删除日历：必须二次确认。
- 日志：每次写入都要记录时间、动作、事件标题和结果。

## Microsoft Graph 官方接口

### 读取日历视图

Microsoft Graph 使用：

```http
GET /me/calendar/calendarView?startDateTime={start_datetime}&endDateTime={end_datetime}
```

用途：读取某个时间范围内的事件。

### 创建日历事件

Microsoft Graph 使用：

```http
POST /me/calendar/events
```

用途：在默认日历中创建事件。

### 权限

第一阶段需要 delegated permission：

```text
Calendars.ReadWrite
```

它允许用户授权后读取和写入自己的日历。

## 我们的接入顺序

### 第 1 步：模拟数据

已完成。

### 第 2 步：只读真实 Outlook

目标：

- 完成 Microsoft App 注册。
- 用户登录授权。
- 读取今天日程。
- 早报里标记 `source=Microsoft Graph`。

### 第 3 步：创建测试事件

目标：

- 只在用户确认后创建。
- 先创建一个低风险测试事件。
- 写入后把 Graph 返回的事件 ID 保存下来。

### 第 4 步：修改和删除

目标：

- 只能修改松果创建过的事件。
- 删除前二次确认。
- 保留操作日志。

## 当前命令

查看模拟 Outlook 输入：

```powershell
cd E:\松果\ai-butler
python .\backend\app\morning_brief_demo.py --show-json
```

生成并保存早报：

```powershell
python .\backend\app\morning_brief_demo.py --save
```

## 真实 Outlook 只读接入

### 1. 创建 Microsoft 应用

进入 Azure Portal / Microsoft Entra 管理中心，创建一个应用注册。

需要准备：

- Application (client) ID
- 支持 public client / device code flow
- Delegated permissions:
  - `User.Read`
  - `Calendars.ReadWrite`
  - `offline_access`

### 2. 配置 `.env`

```text
USE_REAL_OUTLOOK=true
MICROSOFT_CLIENT_ID=你的_Application_Client_ID
MICROSOFT_TENANT=common
MICROSOFT_SCOPES=offline_access User.Read Calendars.ReadWrite
MICROSOFT_TOKEN_PATH=backend/data/ms_graph_token.json
```

注意：

- `MICROSOFT_TENANT` 不要留空。个人 Outlook / Hotmail / Live 账号先用 `common`。
- `MICROSOFT_CLIENT_ID` 不是你的 Outlook 邮箱。
- `MICROSOFT_CLIENT_ID` 必须是 Azure / Microsoft Entra 应用注册里的 Application (client) ID，格式通常像 `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`。
- 如果看到 `AADSTS50059 No tenant-identifying information`，通常是 `MICROSOFT_TENANT` 为空；请改成 `MICROSOFT_TENANT=common` 后重试。

错误示例：

```text
MICROSOFT_CLIENT_ID=someone@example.com
```

正确示例：

```text
MICROSOFT_CLIENT_ID=00000000-0000-0000-0000-000000000000
```

### 3. 登录授权

```powershell
cd E:\松果\ai-butler
python .\backend\app\outlook_auth.py
```

脚本会显示一个网址和验证码。打开网址，输入验证码，登录 Microsoft 账号并授权。

授权成功后，token 会保存到：

```text
backend/data/ms_graph_token.json
```

这个文件已加入 `.gitignore`，不要上传。

### 4. 测试读取今日 Outlook 日程

```powershell
python .\backend\app\outlook_calendar.py
```

如果成功，会输出 `source=Microsoft Graph` 的日程 JSON。

### 5. 让早报读取真实日程

```powershell
python .\backend\app\morning_brief_demo.py --save
```

如果真实 Outlook 读取失败，早报会自动回退到模拟日程。
