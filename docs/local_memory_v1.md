# 本地记忆 v1

## 目标

让松果记住你的长期偏好，而不是每天都从零开始。

当前记忆文件：

```text
backend/data/user_profile.json
```

目前包括：

- 主人称呼和城市
- 松果项目名称和人设
- 关注国家/地区
- 关注市场和宏观变量
- 关注行业
- 关注公司
- 新闻主题
- 生活提醒偏好
- 当前项目阶段和优先级

## 查看记忆

命令行：

```powershell
cd E:\松果\ai-butler
python .\backend\app\memory_cli.py show
```

网页：

```text
http://127.0.0.1:8765/frontend/
```

在“提醒配置”下面会看到“记忆管理”面板。

## 添加记忆

命令行添加关注行业：

```powershell
python .\backend\app\memory_cli.py add industries 低空经济
```

网页添加也可以，直接在“记忆管理”面板里选择类型并输入内容。

命令行添加关注公司：

```powershell
python .\backend\app\memory_cli.py add companies 特斯拉
```

命令行添加生活提醒：

```powershell
python .\backend\app\memory_cli.py add life_reminders 午休20分钟
```

## 删除记忆

命令行删除：

```powershell
python .\backend\app\memory_cli.py remove companies 特斯拉
```

网页删除：

- 在“记忆管理”面板里点击标签右侧的 `×`

## 在早报中的使用

早报生成时会把记忆写入：

```text
morning_brief_input.json -> user_profile / memory_summary
output_bundle.json -> memory_summary
screen_cards.json -> 松果记住了
```

网页追问可以问：

```text
你记住了什么？
我关注哪些公司？
你知道我关心什么吗？
```

## 当前边界

v1 已经支持本地文件记忆、命令行增删、网页增删、早报读取和追问读取。

还没有完成：

- 自然语言确认后写入长期记忆。
- 给不同关注项设置优先级。
- 记录你对早报内容的反馈。
- 根据记忆自动调整新闻、行业和公司权重。

## 后续升级

下一版建议做“自然语言记忆写入”，比如你说“以后帮我重点关注特斯拉和小米汽车”，松果自己提炼并确认后再写入。
