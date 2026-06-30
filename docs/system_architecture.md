# 松果系统架构 v1

## 1. 总体架构

```text
用户
  |
  v
输入层：文字 / 语音 / 定时触发
  |
  v
Agent 大脑
  |-- 人格 Prompt
  |-- 任务规划
  |-- 工具调用
  |-- 安全确认
  |-- 输出结构化状态
  |
  v
数据与工具层
  |-- 全球关键事件摘要
  |-- 天气 API
  |-- Outlook 日历
  |-- 本地待办
  |-- 长期记忆
  |
  v
呈现层
  |-- 命令行 v0
  |-- Web 控制台 v1
  |-- 语音播报 v1
  |-- Unreal 数字人 v2
  |-- 画框 / 伪全息终端 v3
```

## 2. 推荐技术栈

### 后端

- Python
- FastAPI
- SQLite 起步，后续 PostgreSQL
- APScheduler 或 Celery Beat 做定时任务
- OpenAI API 做 LLM、摘要、工具调用

### 前端

- React 或 Next.js
- 用于管理角色、记忆、日程、提醒、早报历史

### 数字人

- Unreal Engine
- MetaHuman
- Blueprint 状态机
- 后端通过 WebSocket 或 HTTP 发送角色状态

### 语音

- Speech-to-Text：先用 API 跑通
- Text-to-Speech：先选一个稳定中文音色
- 后续增加多音色、情绪语音和口型同步

### 硬件

- 第一步：电脑屏幕或平板竖屏展示
- 第二步：画框模式
- 第三步：亚克力反射伪全息底座
- 第四步：研究透明屏、裸眼 3D、光场显示

## 3. 第一版数据结构

### UserProfile

```json
{
  "name": "",
  "city": "",
  "timezone": "Asia/Shanghai",
  "work_focus": [],
  "preferences": []
}
```

### MorningBrief

```json
{
  "date": "2026-06-26",
  "global_events": [],
  "weather": {},
  "outlook_schedule": [],
  "top_priorities": [],
  "risks": [],
  "suggestions": []
}
```

### AvatarState

```json
{
  "dialogue": "",
  "emotion": "warm",
  "action": "speak",
  "gesture": "idle",
  "location": "desk",
  "voice": "default_female_warm",
  "outfit": "daily"
}
```

## 4. 安全边界

- 所有外部账号接入必须由用户显式授权。
- Outlook 第一阶段只读，不自动改动日历。
- 新闻和财经内容需要保留来源和时间。
- 智能家居控制必须先从低风险设备开始，例如灯、插座、窗帘。
- 涉及门锁、支付、消息发送等动作必须暂缓。

