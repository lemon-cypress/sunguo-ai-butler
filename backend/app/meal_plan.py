from __future__ import annotations

import json
import random
import re

from deepseek_client import DeepSeekClientError, create_chat_completion
from openai_client import OpenAIClientError, create_response


class MealPlanError(RuntimeError):
    pass


def item(category: str, name: str, ingredients: list[str], steps: list[str]) -> dict:
    return {"category": category, "name": name, "ingredients": ingredients, "steps": steps}


MEALS = {
    "breakfast": [
        {
            "label": "早餐",
            "title": "燕麦鸡蛋蔬菜饼 + 热牛奶",
            "summary": "一份主餐配热牛奶，少油、耐饱，适合 4 位成人。",
            "items": [
                item("主餐", "燕麦鸡蛋蔬菜饼", ["鸡蛋 6 个", "即食燕麦片 120 克", "菠菜 200 克", "胡萝卜 1 根", "面粉 80 克", "食用油少许", "盐少许"], ["第一步：菠菜焯水 30 秒，挤干切碎；胡萝卜擦丝。", "第二步：将鸡蛋、燕麦、面粉、菠菜和胡萝卜混合，加约 80 毫升清水和少许盐，调成面糊。", "第三步：平底锅刷薄油，中小火将面糊分批煎成 4 至 6 张饼，每面煎 3 至 4 分钟。"]),
                item("饮品", "热牛奶", ["牛奶 1 升"], ["第一步：将牛奶倒入奶锅，小火加热至微温即可，不要煮沸。"]),
            ],
        },
        {
            "label": "早餐",
            "title": "小米南瓜粥 + 水煮蛋 + 凉拌黄瓜",
            "summary": "一粥一蛋一蔬菜，做法简单、口味清淡。",
            "items": [
                item("主食", "小米南瓜粥", ["小米 180 克", "贝贝南瓜 300 克", "清水 2 升"], ["第一步：小米淘洗，南瓜去皮切小块。", "第二步：锅中加水和小米煮开后转小火，煮 20 分钟。", "第三步：加入南瓜再煮 10 分钟，南瓜软烂后即可。"]),
                item("蛋白质", "水煮蛋", ["鸡蛋 4 个"], ["第一步：鸡蛋冷水下锅，水开后煮 8 分钟。", "第二步：捞出过凉水，剥壳后对半切开。"]),
                item("蔬菜", "凉拌黄瓜", ["黄瓜 2 根", "蒜 2 瓣", "生抽 1 汤匙", "香醋 1 汤匙", "香油少许"], ["第一步：黄瓜拍碎切段，蒜切末。", "第二步：加生抽、香醋和少许香油拌匀，静置 5 分钟即可。"]),
            ],
        },
        {
            "label": "早餐",
            "title": "全麦三明治 + 番茄生菜 + 无糖豆浆",
            "summary": "不用开油锅，十几分钟就能完成。",
            "items": [
                item("主食", "全麦鸡蛋三明治", ["全麦吐司 8 片", "鸡蛋 4 个", "低脂奶酪片 4 片", "生菜 8 片", "番茄 2 个"], ["第一步：鸡蛋煮熟后切片，番茄切片并洗净生菜。", "第二步：吐司夹入生菜、番茄、鸡蛋和奶酪片，对切后装盘。"]),
                item("饮品", "无糖豆浆", ["无糖豆浆 1 升"], ["第一步：豆浆倒入锅中加热至微温，搅拌后分杯即可。"]),
            ],
        },
    ],
    "dinner": [
        {
            "label": "晚餐",
            "title": "杂粮饭 + 香菇鸡腿肉 + 白灼西兰花",
            "summary": "主食、肉菜和绿叶菜分开做，约 30 分钟完成。",
            "items": [
                item("主食", "杂粮饭", ["大米 280 克", "小米或糙米 80 克", "清水适量"], ["第一步：大米和杂粮淘洗后浸泡 10 分钟。", "第二步：按电饭煲刻度加水，启动煮饭程序。"]),
                item("荤菜", "香菇鸡腿肉", ["去骨鸡腿肉 800 克", "鲜香菇 250 克", "胡萝卜 1 根", "洋葱半个", "生抽 2 汤匙", "食用油 1 汤匙"], ["第一步：鸡腿肉、香菇、胡萝卜和洋葱切小块。", "第二步：锅中放油，先炒香洋葱，再放鸡腿肉炒至变色。", "第三步：加入香菇、胡萝卜和生抽，盖盖中小火焖 8 分钟，熟透后出锅。"]),
                item("素菜", "白灼西兰花", ["西兰花 500 克", "蒜 3 瓣", "盐少许", "食用油少许"], ["第一步：西兰花切小朵，沸水中加少许盐，焯 2 分钟后捞出。", "第二步：蒜末加少量热油和盐拌匀，淋在西兰花上即可。"]),
            ],
        },
        {
            "label": "晚餐",
            "title": "米饭 + 番茄牛肉片 + 清炒油麦菜",
            "summary": "酸甜开胃，肉菜和绿叶菜各一道，食材常见。",
            "items": [
                item("主食", "米饭", ["大米 360 克", "清水适量"], ["第一步：大米淘洗后按电饭煲刻度加水，启动煮饭程序。"]),
                item("荤菜", "番茄牛肉片", ["牛里脊 600 克", "番茄 4 个", "洋葱半个", "生抽 1 汤匙", "淀粉 1 汤匙", "食用油 1 汤匙"], ["第一步：牛肉逆纹切薄片，加生抽和淀粉抓匀；番茄切块。", "第二步：热锅少油，牛肉快速炒至变色后盛出。", "第三步：用原锅炒番茄和洋葱至出汁，放回牛肉翻匀，煮 2 分钟即可。"]),
                item("素菜", "清炒油麦菜", ["油麦菜 600 克", "蒜 3 瓣", "食用油少许", "盐少许"], ["第一步：油麦菜洗净切段，蒜切末。", "第二步：热锅少油炒香蒜末，放油麦菜大火快炒 2 分钟，加少许盐出锅。"]),
            ],
        },
        {
            "label": "晚餐",
            "title": "玉米饭 + 清蒸鲈鱼 + 上汤娃娃菜",
            "summary": "少油蒸制，清淡但有足够蛋白质。",
            "items": [
                item("主食", "玉米饭", ["大米 300 克", "甜玉米粒 180 克", "清水适量"], ["第一步：大米淘洗后加入玉米粒和适量清水。", "第二步：放入电饭煲，启动煮饭程序。"]),
                item("荤菜", "清蒸鲈鱼", ["鲈鱼 1 条（约 900 克）", "姜 1 小块", "葱 2 根", "蒸鱼豉油 2 汤匙"], ["第一步：鲈鱼处理干净，鱼身划两刀，铺姜丝和葱段。", "第二步：水开后上锅蒸 10 分钟，关火焖 2 分钟。", "第三步：倒掉盘中水分，淋蒸鱼豉油即可。"]),
                item("素菜", "上汤娃娃菜", ["娃娃菜 3 棵", "蒜 3 瓣", "清水 250 毫升", "盐少许"], ["第一步：娃娃菜对半切开，蒜切末。", "第二步：锅中加蒜末和清水，放入娃娃菜盖盖煮 5 分钟，加少许盐即可。"]),
            ],
        },
    ],
}


def random_meal(meal_type: str) -> dict:
    if meal_type not in MEALS:
        raise MealPlanError("餐别仅支持 breakfast 或 dinner")
    return random.choice(MEALS[meal_type])


def random_plan() -> dict:
    return {"breakfast": random_meal("breakfast"), "dinner": random_meal("dinner"), "source": "random"}


def _extract_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\\s*|\\s*```$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise MealPlanError("模型没有返回可用的餐谱数据")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as error:
        raise MealPlanError("模型返回的餐谱格式不正确，请重试") from error


def _short_text(value: object, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _validate_meal(raw: object, label: str) -> dict:
    if not isinstance(raw, dict):
        raise MealPlanError(f"模型没有生成{label}")
    title = _short_text(raw.get("title"), 60)
    summary = _short_text(raw.get("summary"), 120)
    items = raw.get("items")
    if len(title) < 2 or not isinstance(items, list) or not 2 <= len(items) <= 4:
        raise MealPlanError(f"模型生成的{label}不完整，请重试")
    clean_items = []
    for raw_item in items:
        if not isinstance(raw_item, dict):
            continue
        category = _short_text(raw_item.get("category"), 12) or "菜品"
        name = _short_text(raw_item.get("name"), 40)
        ingredients = [_short_text(value, 60) for value in raw_item.get("ingredients", []) if _short_text(value, 60)][:12]
        steps = [_short_text(value, 160) for value in raw_item.get("steps", []) if _short_text(value, 160)][:5]
        if not name or not ingredients or len(steps) < 2:
            continue
        clean_steps = [step if re.match(r"^第[一二三四五六七八九十0-9]+步[：:]", step) else f"第{index}步：{step}" for index, step in enumerate(steps, 1)]
        clean_items.append({"category": category, "name": name, "ingredients": ingredients, "steps": clean_steps})
    if len(clean_items) < 2:
        raise MealPlanError(f"模型生成的{label}菜品不完整，请重试")
    return {"label": label, "title": title, "summary": summary or "按你的偏好安排，建议少油少盐制作。", "items": clean_items}


def generate_plan_from_preference(preference: str, settings) -> dict:
    preference = _short_text(preference, 500)
    if not preference:
        return random_plan()
    prompt = f"""
你是家庭餐谱助手。为 4 位成人安排今天早餐和晚餐，婴儿不计入。
用户偏好：{preference}
要求：健康、家常、制作简单；早餐和晚餐各 2 至 4 项，晚餐必须把主食、荤菜、素菜拆成独立项目；不要使用生食、酒精或复杂烘焙；食材写明适合 4 人的用量；每个项目给出 2 至 5 个以“第一步：”开始的具体步骤。
只返回 JSON，不要 Markdown。格式必须为：
{{"breakfast":{{"title":"菜名 + 菜名","summary":"一句说明","items":[{{"category":"主食/荤菜/素菜/饮品","name":"名称","ingredients":["食材及用量"],"steps":["第一步：..."]}}]}},"dinner":{{"title":"菜名 + 菜名","summary":"一句说明","items":[...]}}}}
""".strip()
    try:
        if settings.ai_provider == "deepseek" and settings.deepseek_api_key:
            model = "deepseek-chat" if "v4" in settings.deepseek_model.lower() or "reason" in settings.deepseek_model.lower() else settings.deepseek_model
            raw = create_chat_completion(settings.deepseek_api_key, model, prompt, json_mode=True)
        elif settings.ai_provider == "openai" and settings.openai_api_key:
            raw = create_response(settings.openai_api_key, settings.openai_model, prompt)
        else:
            raise MealPlanError("未配置可用的 AI 密钥，暂时无法按描述生成餐谱")
    except (DeepSeekClientError, OpenAIClientError) as error:
        raise MealPlanError(f"按描述生成餐谱失败：{error}") from error
    payload = _extract_json(raw)
    return {
        "breakfast": _validate_meal(payload.get("breakfast"), "早餐"),
        "dinner": _validate_meal(payload.get("dinner"), "晚餐"),
        "source": "preference",
    }


def generate_meal_from_preference(meal_type: str, preference: str, settings) -> dict:
    label = {"breakfast": "早餐", "dinner": "晚餐"}.get(meal_type)
    if not label:
        raise MealPlanError("请选择早餐或晚餐")
    preference = _short_text(preference, 500)
    if not preference:
        raise MealPlanError(f"请先写下{label}想吃什么、忌口或现有食材")
    meal_rules = "2 至 3 项，主餐和饮品可分开" if meal_type == "breakfast" else "必须包含并拆分主食、荤菜、素菜，共 3 项"
    prompt = f"""
你是家庭餐谱助手。只为 4 位成人安排今天的{label}，婴儿不计入。
用户偏好：{preference}
要求：健康、家常、制作简单、少油少盐；{label}{meal_rules}；不要使用生食、酒精或复杂烘焙；食材写明适合 4 人的用量；每个项目给出 2 至 5 个以“第一步：”开始的具体步骤。
只返回 JSON，不要 Markdown。格式必须为：
{{"title":"菜名 + 菜名","summary":"一句说明","items":[{{"category":"主食/荤菜/素菜/饮品","name":"名称","ingredients":["食材及用量"],"steps":["第一步：..."]}}]}}
""".strip()
    try:
        if settings.ai_provider == "deepseek" and settings.deepseek_api_key:
            model = "deepseek-chat" if "v4" in settings.deepseek_model.lower() or "reason" in settings.deepseek_model.lower() else settings.deepseek_model
            raw = create_chat_completion(settings.deepseek_api_key, model, prompt, json_mode=True)
        elif settings.ai_provider == "openai" and settings.openai_api_key:
            raw = create_response(settings.openai_api_key, settings.openai_model, prompt)
        else:
            raise MealPlanError("未配置可用的 AI 密钥，暂时无法按描述生成餐谱")
    except (DeepSeekClientError, OpenAIClientError) as error:
        raise MealPlanError(f"按描述生成餐谱失败：{error}") from error
    return _validate_meal(_extract_json(raw), label)
