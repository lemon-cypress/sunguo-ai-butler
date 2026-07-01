# 松果每日自动更新网页

目标：只要 ECS 正常运行，松果网页每天自动更新到当天最新早报，不再手动复制 `demos` 文件。

## 现在已经实现的逻辑

- 运行 `python3 backend/app/morning_brief_demo.py --save`
- 无论是真实数据还是 mock 数据
- 都会自动刷新：
  - `demos/latest.json`
- 如果当天产出是 mock 数据，`demos/latest.json` 会自动指向：
  - `mock/YYYY-MM-DD/output_bundle.json`

这意味着前端网页始终读取当天最新结果。

## 当前语音说明

- ECS 是 Linux 环境，不带 Windows PowerShell 语音引擎
- 所以当前每日自动刷新时：
  - 早报文本、卡片、3D 动作、追问数据会正常更新
  - 如果服务器端 TTS 失败，网页依然可以正常显示当天最新内容
- 下一步我们可以把它换成真正的服务端 TTS，例如 Edge TTS

## 一次性部署定时任务

在 ECS 上执行：

```bash
cd /opt/sunguo/ai-butler
sudo cp deploy/aliyun/sunguo-brief-refresh.service /etc/systemd/system/
sudo cp deploy/aliyun/sunguo-brief-refresh.timer /etc/systemd/system/
sudo chmod +x deploy/aliyun/refresh_sunguo_brief.sh
sudo systemctl daemon-reload
sudo systemctl enable sunguo-brief-refresh.timer
sudo systemctl start sunguo-brief-refresh.timer
sudo systemctl status sunguo-brief-refresh.timer --no-pager
```

## 立即手动跑一次

```bash
cd /opt/sunguo/ai-butler
sudo bash deploy/aliyun/refresh_sunguo_brief.sh
cat demos/latest.json
```

## 查看是否已经定时生效

```bash
systemctl list-timers --all | grep sunguo
```

## 查看日志

```bash
tail -n 80 /opt/sunguo/logs/brief-refresh.log
```

## 默认执行时间

当前定时器是每天早上 `07:00`。

如需改时间，编辑：

- `deploy/aliyun/sunguo-brief-refresh.timer`

例如改成每天 06:30：

```ini
OnCalendar=*-*-* 06:30:00
```

改完后在 ECS 上执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart sunguo-brief-refresh.timer
```
