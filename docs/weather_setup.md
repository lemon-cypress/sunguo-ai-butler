# 天气模块设置

## 当前方案

松果当前使用 Open-Meteo 获取天气。

优点：

- 不需要 API Key。
- 适合第一阶段快速验证。
- 失败时会自动回退到内置假天气。

## 默认位置

默认城市：

```text
北京-朝阳
```

默认经纬度：

```text
WEATHER_LATITUDE=39.9219
WEATHER_LONGITUDE=116.4433
```

这是北京朝阳附近的近似坐标。后续如果要更精确，可以换成你常住位置附近坐标。

## `.env` 配置

```text
DEFAULT_CITY=北京-朝阳
WEATHER_LATITUDE=39.9219
WEATHER_LONGITUDE=116.4433
WEATHER_TIMEOUT_SECONDS=30
WEATHER_RETRIES=2
USE_REAL_WEATHER=true
TIMEZONE=Asia/Shanghai
```

## 为什么有时会获取失败

如果看到：

```text
_ssl.c:1015: The handshake operation timed out
```

这表示程序已经尝试连接 Open-Meteo，但 HTTPS 握手超时。常见原因：

- 当前网络访问 `api.open-meteo.com` 不稳定。
- 代理、VPN、防火墙或安全软件影响了 HTTPS 连接。
- Open-Meteo 接口临时慢或不可达。

这不是 DeepSeek 的问题，也不是早报主流程坏了。脚本会自动回退到内置假天气，保证早报还能生成。

可以尝试：

```powershell
python .\backend\app\morning_brief_demo.py --save
```

或临时跳过真实天气：

```powershell
python .\backend\app\morning_brief_demo.py --mock-weather --save
```

如果你的网络经常连不上 Open-Meteo，后续可以替换为国内天气源，比如和风天气、彩云天气或高德天气。

## 运行真实天气早报

```powershell
cd E:\松果\ai-butler
python .\backend\app\morning_brief_demo.py --save
```

## 强制使用假天气

如果想排查问题，运行：

```powershell
python .\backend\app\morning_brief_demo.py --mock-weather --no-ai
```

## 查看结构化天气输入

```powershell
python .\backend\app\morning_brief_demo.py --show-json
```

看 `weather.source` 字段：

- `Open-Meteo`：真实天气
- `mock`：内置假天气
