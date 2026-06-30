# 早报网页界面

松果现在可以把 `output_bundle.json` 展示成网页卡片。

## 先生成早报输出包

```powershell
cd E:\松果\ai-butler
python .\backend\app\morning_brief_demo.py --save
```

## 启动本地网页服务器

```powershell
python -m http.server 8765
```

然后在浏览器打开：

```text
http://localhost:8765/frontend/
```

也可以直接运行脚本：

```powershell
.\scripts\start_dashboard.ps1
```

默认会读取：

```text
demos/latest.json
```

也就是最近一次 `--save` 生成的早报。

如果要查看指定日期：

```text
http://localhost:8765/frontend/?date=2026-06-26
```

## 当前页面包含

- 数字人状态区：展示表情、动作、镜头标签
- 信息源栏：展示天气、市场、新闻、公司、日程来源
- 早报卡片：读取 `screen_cards.json` 对应的信息
- 语音分段：读取 `speech_script.json`，并支持浏览器内置朗读

## 下一步

后续可以把这个静态页面升级成正式前端：

- 自动读取最新日期
- 接入真实 TTS 音色
- 接入数字人渲染引擎
- 增加“追问松果”的对话输入框

## 语音播放

如果当天早报保存时生成了 `speech_audio.wav`，网页的“朗读”按钮会优先播放本地音频；音频不可用时，再退回到浏览器内置朗读。
