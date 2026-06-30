from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherClientError(RuntimeError):
    pass


WEATHER_CODE_TEXT = {
    0: "晴",
    1: "大部晴朗",
    2: "局部多云",
    3: "阴",
    45: "有雾",
    48: "有雾凇",
    51: "小毛毛雨",
    53: "中等毛毛雨",
    55: "较强毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "短时小阵雨",
    81: "短时中阵雨",
    82: "短时强阵雨",
    95: "雷雨",
    96: "雷雨伴小冰雹",
    99: "雷雨伴强冰雹",
}


def fetch_weather(
    latitude: float,
    longitude: float,
    timezone: str,
    city: str,
    timeout_seconds: int = 30,
    retries: int = 2,
) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
        "timezone": timezone,
        "forecast_days": 1,
    }
    url = f"{OPEN_METEO_FORECAST_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "sunguo-ai-butler/0.1"})

    payload = fetch_json_with_retries(request, timeout_seconds=timeout_seconds, retries=retries)

    return normalize_weather(payload, city)


def fetch_json_with_retries(request: urllib.request.Request, timeout_seconds: int, retries: int) -> dict:
    last_error: Exception | None = None
    attempts = max(1, retries + 1)

    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, socket.timeout) as error:
            last_error = error
            if attempt < attempts:
                time.sleep(1.5 * attempt)
                continue
        except json.JSONDecodeError as error:
            raise WeatherClientError("Open-Meteo returned invalid JSON.") from error

    raise WeatherClientError(
        "Open-Meteo network error after "
        f"{attempts} attempt(s): {last_error}. "
        "这通常是网络到 Open-Meteo 的 HTTPS 握手超时、代理/VPN/防火墙拦截，或接口临时不可达。"
    ) from last_error


def normalize_weather(payload: dict, city: str) -> dict:
    current = payload.get("current", {})
    daily = payload.get("daily", {})

    current_temp = current.get("temperature_2m")
    current_code = current.get("weather_code")
    wind_speed = current.get("wind_speed_10m")
    max_temp = first_value(daily.get("temperature_2m_max"))
    min_temp = first_value(daily.get("temperature_2m_min"))
    rain_probability = first_value(daily.get("precipitation_probability_max"))
    daily_code = first_value(daily.get("weather_code"))

    weather_code = daily_code if daily_code is not None else current_code
    condition = WEATHER_CODE_TEXT.get(int(weather_code), "天气状况待确认") if weather_code is not None else "天气状况待确认"
    temperature = format_temperature(min_temp, max_temp, current_temp)
    rain = format_rain(rain_probability)
    outfit = build_outfit_suggestion(min_temp, max_temp, rain_probability, condition, wind_speed)

    return {
        "source": "Open-Meteo",
        "city": city,
        "condition": condition,
        "temperature": temperature,
        "current_temperature_c": current_temp,
        "min_temperature_c": min_temp,
        "max_temperature_c": max_temp,
        "rain": rain,
        "precipitation_probability_max": rain_probability,
        "wind_speed_10m_kmh": wind_speed,
        "outfit": outfit,
    }


def first_value(value):
    if isinstance(value, list) and value:
        return value[0]
    return None


def format_temperature(min_temp, max_temp, current_temp) -> str:
    if min_temp is not None and max_temp is not None:
        return f"{round(min_temp)}-{round(max_temp)}°C"
    if current_temp is not None:
        return f"当前约 {round(current_temp)}°C"
    return "温度待确认"


def format_rain(rain_probability) -> str:
    if rain_probability is None:
        return "降雨概率待确认"
    if rain_probability >= 70:
        return f"降雨概率较高，约 {round(rain_probability)}%"
    if rain_probability >= 40:
        return f"有一定降雨概率，约 {round(rain_probability)}%"
    return f"降雨概率较低，约 {round(rain_probability)}%"


def build_outfit_suggestion(min_temp, max_temp, rain_probability, condition: str, wind_speed) -> str:
    suggestions: list[str] = []

    if max_temp is None:
        suggestions.append("建议按体感准备衣物")
    elif max_temp >= 30:
        suggestions.append("建议穿轻薄透气的短袖、衬衫或薄款长裤")
    elif max_temp >= 24:
        suggestions.append("建议穿短袖、薄衬衫或轻便长裤")
    elif max_temp >= 16:
        suggestions.append("建议穿长袖或薄外套")
    else:
        suggestions.append("建议穿厚一点的外套，注意保暖")

    if min_temp is not None and max_temp is not None and max_temp - min_temp >= 9:
        suggestions.append("早晚温差比较明显，可以多带一件薄外套")

    if rain_probability is not None and rain_probability >= 40:
        suggestions.append("包里放一把伞更稳妥")

    if "雾" in condition:
        suggestions.append("能见度可能一般，出门路上稍微留意交通")

    if wind_speed is not None and wind_speed >= 25:
        suggestions.append("风有点大，尽量避免太轻薄的外搭")

    return "，".join(suggestions) + "。"
