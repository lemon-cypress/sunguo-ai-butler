# 输出层 v1

松果的输出层不只生成一篇早报文本，而是把同一份信息拆成多个下游模块可用的形态。

## 生成命令

```powershell
cd E:\松果\ai-butler
python .\backend\app\morning_brief_demo.py --save
```

如果只想验证输出结构，不调用真实接口：

```powershell
python .\backend\app\morning_brief_demo.py --mock-weather --mock-market --mock-news --mock-themes --mock-companies --no-ai --save
```

## 输出文件

保存位置：

```text
demos/YYYY-MM-DD/
```

文件说明：

- `morning_brief_input.json`：早报的结构化输入数据
- `morning_brief.txt`：当前文本版早报
- `output_bundle.json`：统一输出包，包含所有输出形态
- `screen_cards.json`：给前端页面或桌面屏幕展示的信息卡片
- `speech_script.json`：给 TTS 语音合成的分段台词
- `avatar_timeline.json`：给数字人/Unreal/Live2D 的表情、动作、镜头标签
- `../latest.json`：最近一次保存的早报索引，网页默认读取它

质量升级后，结构化数据里还会包含：

- `brief_analysis.today_overview`：今日总览
- `brief_analysis.top_stories`：三件重要事，含影响对象、证据、可信度和核验点

## 后续接入方向

### 屏幕卡片

`screen_cards.json` 可以直接给网页前端使用。第一版页面只需要按卡片类型展示：

- 天气和穿衣
- 今天先关注
- 市场和宏观
- 价格和行业线索
- 公司观察池
- 今天待办
- 生活提醒

### 语音台词

`speech_script.json` 每一段都有：

- `text`：要朗读的文字
- `voice.style`：语气风格，例如 `warm`、`careful`、`encouraging`
- `voice.speed`：语速
- `voice.pause_after_ms`：段落后的停顿

后续可以把它接到 TTS，生成 `mp3` 或 `wav`。

### 数字人动作

`avatar_timeline.json` 每一段都有：

- `expression`：表情
- `gesture`：动作
- `camera`：镜头
- `caption`：字幕/屏幕提示

后续可以映射到 Unreal、Live2D 或其他数字人系统。

## 当前原则

- 财经和新闻内容先作为线索，不直接生成买卖建议。
- 对未核验的新闻标题保持谨慎。
- 输出层先稳定结构，再追求视觉和语音效果。

## 本地语音

现在保存早报时，会额外生成：

- `speech_audio.wav`：本地 Windows 语音合成出来的音频
- `speech_audio_path`：在 `output_bundle.json` 和 `latest.json` 里的相对路径

网页会优先播放这份本地音频；如果音频缺失，再回退到浏览器内置朗读。
