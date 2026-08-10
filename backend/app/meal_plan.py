from __future__ import annotations

import json
import random
import re
from collections import deque

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


# 组合逻辑以《中国居民膳食指南（2022）》的平衡膳食原则为基础：
# 谷薯类为主，增加全谷杂豆；鱼禽蛋瘦肉和大豆轮换；每餐搭配蔬菜，
# 并优先蒸、煮、炖、少油快炒。这里是健康成人的一般饮食建议，
# 不替代过敏、孕期、慢病等个体化医嘱。
BREAKFAST_LIBRARY = MEALS["breakfast"] + [
    {"label": "早餐", "title": "玉米鸡蛋羹 + 全麦馒头 + 无糖豆浆", "summary": "谷物、蛋类和豆制饮品组合，适合忙碌早晨。", "items": [
        item("主食", "全麦馒头", ["全麦馒头 4 个（约 400 克）"], ["第一步：馒头放入蒸锅，水开后蒸 6 分钟。"]),
        item("蛋白质", "玉米鸡蛋羹", ["鸡蛋 6 个", "甜玉米粒 180 克", "温水 450 毫升", "盐少许"], ["第一步：鸡蛋打散，加入温水和少许盐搅匀，过滤到大碗中。", "第二步：放入玉米粒，盖盘后水开上锅蒸 12 分钟，关火焖 2 分钟。"]),
        item("饮品", "无糖豆浆", ["无糖豆浆 1 升"], ["第一步：豆浆小火加热至微温，分杯即可。"]),
    ]},
    {"label": "早餐", "title": "红薯小米粥 + 鸡蛋 + 清炒生菜", "summary": "粗粮薯类替代部分精白主食，清淡又耐饱。", "items": [
        item("主食", "红薯小米粥", ["小米 160 克", "红薯 500 克", "清水 2 升"], ["第一步：红薯去皮切块，小米淘洗。", "第二步：小米和水煮开后转小火煮 20 分钟，加入红薯再煮 12 分钟。"]),
        item("蛋白质", "水煮蛋", ["鸡蛋 4 个"], ["第一步：鸡蛋冷水下锅，水开后煮 8 分钟，过凉水剥壳。"]),
        item("蔬菜", "清炒生菜", ["生菜 500 克", "蒜 2 瓣", "食用油 1 汤匙", "盐少许"], ["第一步：生菜洗净沥干，蒜切末。", "第二步：热锅少油炒香蒜末，放生菜大火快炒 1 分钟，加少许盐出锅。"]),
    ]},
    {"label": "早餐", "title": "番茄豆腐面 + 原味酸奶", "summary": "一锅面配豆腐和番茄，补充蛋白质与蔬菜。", "items": [
        item("主食", "番茄豆腐面", ["全麦挂面 360 克", "番茄 3 个", "北豆腐 400 克", "小白菜 300 克", "鸡蛋 2 个", "盐少许"], ["第一步：番茄切块、豆腐切丁，小白菜洗净。", "第二步：锅中加水煮开，放番茄和豆腐煮 4 分钟后下挂面。", "第三步：面条将熟时放小白菜和鸡蛋，煮熟后加少许盐即可。"]),
        item("奶类", "原味酸奶", ["原味无糖酸奶 800 克"], ["第一步：酸奶分装 4 碗，饭后或随餐食用。"]),
    ]},
    {"label": "早餐", "title": "杂粮饭团 + 煎豆腐 + 热牛奶", "summary": "利用隔夜杂粮饭，搭配豆制品，十几分钟完成。", "items": [
        item("主食", "杂粮饭团", ["杂粮饭 600 克", "紫菜碎 10 克", "胡萝卜半根"], ["第一步：胡萝卜擦丝焯水 1 分钟，和温热杂粮饭、紫菜碎拌匀。", "第二步：分成 8 个小饭团，装盘即可。"]),
        item("蛋白质", "香煎豆腐", ["北豆腐 500 克", "葱花少许", "生抽 1 汤匙", "食用油 1 汤匙"], ["第一步：豆腐切厚片，用厨房纸吸干表面水分。", "第二步：平底锅刷薄油，豆腐两面各煎 3 分钟，淋少许生抽和葱花。"]),
        item("饮品", "热牛奶", ["牛奶 1 升"], ["第一步：小火加热至微温，分杯即可。"]),
    ]},
    {"label": "早餐", "title": "南瓜燕麦粥 + 虾仁滑蛋 + 焯青菜", "summary": "用虾和鸡蛋提供优质蛋白，配粗粮粥更均衡。", "items": [
        item("主食", "南瓜燕麦粥", ["燕麦片 180 克", "南瓜 400 克", "清水 1.8 升"], ["第一步：南瓜去皮切块，加水煮 12 分钟。", "第二步：放燕麦片再煮 5 分钟，搅匀即可。"]),
        item("蛋白质", "虾仁滑蛋", ["虾仁 400 克", "鸡蛋 5 个", "食用油 1 汤匙", "盐少许"], ["第一步：虾仁焯水 1 分钟，鸡蛋打散加少许盐。", "第二步：锅中少油，先炒虾仁 1 分钟，再倒蛋液炒至凝固。"]),
        item("蔬菜", "焯青菜", ["上海青 400 克", "盐少许"], ["第一步：青菜洗净，沸水加少许盐焯 1 分钟，沥水装盘。"]),
    ]},
    {"label": "早餐", "title": "全麦卷饼 + 鸡丝彩椒 + 无糖豆浆", "summary": "全谷主食搭配鸡肉与彩椒，颜色和口感更丰富。", "items": [
        item("主食", "全麦卷饼", ["全麦饼皮 8 张"], ["第一步：平底锅不放油，每张饼皮两面各加热 30 秒。"]),
        item("荤菜", "鸡丝彩椒", ["鸡胸肉 500 克", "红黄彩椒各 1 个", "黄瓜 1 根", "生抽 1 汤匙", "食用油 1 汤匙"], ["第一步：鸡胸肉煮熟撕丝，彩椒和黄瓜切丝。", "第二步：彩椒少油快炒 2 分钟，加入鸡丝、生抽翻匀，和黄瓜一起卷入饼皮。"]),
        item("饮品", "无糖豆浆", ["无糖豆浆 1 升"], ["第一步：豆浆加热至微温后分杯。"]),
    ]},
]

DINNER_STAPLES = [
    item("主食", "杂粮饭", ["大米 280 克", "糙米或小米 100 克", "清水适量"], ["第一步：大米和杂粮淘洗，浸泡 15 分钟。", "第二步：按电饭煲刻度加水，启动煮饭程序。"]),
    item("主食", "玉米饭", ["大米 300 克", "甜玉米粒 200 克", "清水适量"], ["第一步：大米淘洗后与玉米粒混合。", "第二步：按电饭煲刻度加水煮熟。"]),
    item("主食", "红薯饭", ["大米 300 克", "红薯 500 克", "清水适量"], ["第一步：红薯去皮切小块，大米淘洗。", "第二步：将红薯铺在米上，按电饭煲刻度加水煮熟。"]),
    item("主食", "荞麦面", ["荞麦面 480 克", "小白菜 300 克"], ["第一步：水开后下荞麦面煮 5 分钟。", "第二步：放小白菜煮 1 分钟，捞出分碗。"]),
    item("主食", "紫薯燕麦饭", ["大米 260 克", "燕麦米 100 克", "紫薯 400 克", "清水适量"], ["第一步：紫薯去皮切块，米类淘洗。", "第二步：紫薯和米一起放入电饭煲，按刻度加水煮熟。"]),
    item("主食", "山药小米饭", ["大米 280 克", "小米 80 克", "山药 350 克", "清水适量"], ["第一步：山药去皮切丁，米类淘洗。", "第二步：食材放电饭煲，按刻度加水煮熟。"]),
]

DINNER_PROTEINS = [
    {"group": "fish", "dish": item("荤菜", "清蒸鲈鱼", ["鲈鱼 1 条（约 900 克）", "姜 1 小块", "葱 2 根", "蒸鱼豉油 2 汤匙"], ["第一步：鲈鱼处理干净，铺姜丝和葱段。", "第二步：水开后蒸 10 分钟，关火焖 2 分钟。", "第三步：倒掉盘中水分，淋蒸鱼豉油即可。"])},
    {"group": "fish", "dish": item("荤菜", "番茄龙利鱼", ["龙利鱼 700 克", "番茄 4 个", "洋葱半个", "食用油 1 汤匙"], ["第一步：龙利鱼切块，番茄切块。", "第二步：少油炒番茄至出汁，加鱼块和少量热水焖 6 分钟至熟。"] )},
    {"group": "fish", "dish": item("荤菜", "虾仁豆腐煲", ["虾仁 600 克", "北豆腐 500 克", "豌豆 150 克", "姜 1 小块"], ["第一步：豆腐切块，虾仁洗净。", "第二步：锅中加少量水和姜片，放豆腐、豌豆煮 4 分钟。", "第三步：加入虾仁煮 3 分钟至熟。"] )},
    {"group": "poultry", "dish": item("荤菜", "香菇鸡腿肉", ["去骨鸡腿肉 800 克", "鲜香菇 250 克", "胡萝卜 1 根", "洋葱半个", "生抽 2 汤匙", "食用油 1 汤匙"], ["第一步：食材切小块。", "第二步：少油炒洋葱和鸡腿肉至变色。", "第三步：加入香菇、胡萝卜和生抽，焖 8 分钟至熟。"] )},
    {"group": "poultry", "dish": item("荤菜", "芦笋鸡丁", ["鸡胸肉 700 克", "芦笋 400 克", "口蘑 250 克", "生抽 1 汤匙", "食用油 1 汤匙"], ["第一步：鸡胸肉切丁，芦笋切段，口蘑切片。", "第二步：少油炒鸡丁至变色，加入芦笋和口蘑快炒 4 分钟。", "第三步：加少许生抽翻匀至熟。"] )},
    {"group": "lean_meat", "dish": item("荤菜", "番茄牛肉片", ["牛里脊 600 克", "番茄 4 个", "洋葱半个", "淀粉 1 汤匙", "食用油 1 汤匙"], ["第一步：牛肉逆纹切片，加淀粉抓匀；番茄切块。", "第二步：少油滑炒牛肉至变色后盛出。", "第三步：番茄炒出汁后放回牛肉，煮 2 分钟。"] )},
    {"group": "lean_meat", "dish": item("荤菜", "西芹肉丝", ["瘦猪里脊 600 克", "西芹 500 克", "胡萝卜 1 根", "生抽 1 汤匙", "食用油 1 汤匙"], ["第一步：里脊和西芹切丝，胡萝卜切丝。", "第二步：少油炒肉丝至变色，加入蔬菜大火快炒 3 分钟。", "第三步：加少许生抽翻匀至熟。"] )},
    {"group": "soy", "dish": item("豆制品", "家常豆腐烧菌菇", ["北豆腐 700 克", "杏鲍菇 300 克", "青椒 2 个", "生抽 2 汤匙", "食用油 1 汤匙"], ["第一步：豆腐切块，菌菇和青椒切片。", "第二步：少油将豆腐两面煎黄，加入菌菇、青椒和生抽。", "第三步：加少量水焖 5 分钟至熟。"] )},
    {"group": "soy", "dish": item("豆制品", "毛豆鸡蛋炒豆腐", ["北豆腐 500 克", "毛豆仁 250 克", "鸡蛋 4 个", "番茄 2 个", "食用油 1 汤匙"], ["第一步：豆腐切丁，鸡蛋打散，番茄切块。", "第二步：少油炒鸡蛋盛出，再放豆腐、毛豆和番茄炒 5 分钟。", "第三步：放回鸡蛋翻匀至熟。"] )},
    {"group": "egg", "dish": item("蛋类", "木耳番茄炒蛋", ["鸡蛋 8 个", "番茄 5 个", "泡发木耳 200 克", "食用油 1 汤匙"], ["第一步：木耳焯水 2 分钟，鸡蛋打散，番茄切块。", "第二步：少油炒鸡蛋盛出，炒番茄和木耳至出汁。", "第三步：放回鸡蛋翻匀。"] )},
]

DINNER_VEGETABLES = [
    item("素菜", "白灼西兰花", ["西兰花 600 克", "蒜 3 瓣", "盐少许"], ["第一步：西兰花切小朵，沸水加少许盐焯 2 分钟。", "第二步：蒜末加少量热油和盐拌匀，淋在西兰花上。"]),
    item("素菜", "蒜蓉油麦菜", ["油麦菜 650 克", "蒜 3 瓣", "食用油 1 汤匙", "盐少许"], ["第一步：油麦菜洗净切段，蒜切末。", "第二步：少油炒香蒜末，放油麦菜大火快炒 2 分钟。"]),
    item("素菜", "清炒荷兰豆胡萝卜", ["荷兰豆 450 克", "胡萝卜 2 根", "蒜 2 瓣", "食用油 1 汤匙"], ["第一步：荷兰豆撕筋，胡萝卜切片。", "第二步：沸水焯荷兰豆 1 分钟后，少油与胡萝卜快炒 3 分钟。"]),
    item("素菜", "上汤娃娃菜", ["娃娃菜 4 棵", "蒜 3 瓣", "清水 300 毫升", "盐少许"], ["第一步：娃娃菜对半切开，蒜切末。", "第二步：锅中加蒜末和清水，放娃娃菜盖盖煮 5 分钟。"]),
    item("素菜", "清炒菜心", ["菜心 650 克", "蒜 3 瓣", "食用油 1 汤匙", "盐少许"], ["第一步：菜心洗净切段，蒜切末。", "第二步：少油炒香蒜末，放菜心大火快炒 2 分钟。"]),
    item("素菜", "菌菇烩青菜", ["小青菜 500 克", "白玉菇 300 克", "胡萝卜半根", "食用油 1 汤匙"], ["第一步：青菜洗净，菌菇焯水 1 分钟。", "第二步：少油先炒菌菇和胡萝卜 2 分钟，再放青菜炒熟。"]),
    item("素菜", "清炒西葫芦木耳", ["西葫芦 2 个", "泡发木耳 180 克", "蒜 2 瓣", "食用油 1 汤匙"], ["第一步：西葫芦切片，木耳焯水。", "第二步：少油炒蒜末，放西葫芦和木耳快炒 4 分钟。"]),
    item("素菜", "醋溜白菜", ["大白菜 800 克", "蒜 3 瓣", "香醋 1 汤匙", "食用油 1 汤匙"], ["第一步：白菜切片，菜帮和菜叶分开。", "第二步：少油炒蒜末和菜帮 2 分钟，再放菜叶，出锅前加香醋。"]),
]

RECENT_BREAKFASTS: deque[str] = deque(maxlen=5)
RECENT_DINNER_PARTS: deque[str] = deque(maxlen=9)
RECENT_PROTEIN_GROUPS: deque[str] = deque(maxlen=5)


def _pick_fresh(options: list[dict], recent: deque[str]) -> dict:
    candidates = [option for option in options if option["name"] not in recent] or options
    chosen = random.choice(candidates)
    recent.append(chosen["name"])
    return chosen


def _build_combined_dinner() -> dict:
    staple = _pick_fresh(DINNER_STAPLES, RECENT_DINNER_PARTS)
    group_counts = {group: RECENT_PROTEIN_GROUPS.count(group) for group in {entry["group"] for entry in DINNER_PROTEINS}}
    least_used = min(group_counts.values())
    eligible_groups = {group for group, count in group_counts.items() if count == least_used}
    proteins = [entry for entry in DINNER_PROTEINS if entry["group"] in eligible_groups and entry["dish"]["name"] not in RECENT_DINNER_PARTS]
    protein = random.choice(proteins or DINNER_PROTEINS)
    RECENT_DINNER_PARTS.append(protein["dish"]["name"])
    RECENT_PROTEIN_GROUPS.append(protein["group"])
    vegetable = _pick_fresh(DINNER_VEGETABLES, RECENT_DINNER_PARTS)
    return {
        "label": "晚餐",
        "title": f"{staple['name']} + {protein['dish']['name']} + {vegetable['name']}",
        "summary": "组合说明：全谷/薯类主食搭配优质蛋白和蔬菜；蛋白质来源轮换，烹调以蒸、煮、炖、少油快炒为主。",
        "items": [staple, protein["dish"], vegetable],
    }


def random_meal(meal_type: str) -> dict:
    if meal_type not in MEALS:
        raise MealPlanError("餐别仅支持 breakfast 或 dinner")
    if meal_type == "breakfast":
        candidates = [meal for meal in BREAKFAST_LIBRARY if meal["title"] not in RECENT_BREAKFASTS] or BREAKFAST_LIBRARY
        chosen = random.choice(candidates)
        RECENT_BREAKFASTS.append(chosen["title"])
        return chosen
    return _build_combined_dinner()


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
要求：健康、家常、制作简单；优先全谷/杂豆或薯类主食，优先鱼、禽、蛋、瘦肉和大豆制品，搭配蔬菜；早餐和晚餐各 2 至 4 项，晚餐必须把主食、荤菜、素菜拆成独立项目；不要使用生食、酒精或复杂烘焙；食材写明适合 4 人的用量；每个项目给出 2 至 5 个以“第一步：”开始的具体步骤。
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
要求：健康、家常、制作简单、少油少盐；优先全谷/杂豆或薯类主食，优先鱼、禽、蛋、瘦肉和大豆制品，搭配蔬菜；{label}{meal_rules}；不要使用生食、酒精或复杂烘焙；食材写明适合 4 人的用量；每个项目给出 2 至 5 个以“第一步：”开始的具体步骤。
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
