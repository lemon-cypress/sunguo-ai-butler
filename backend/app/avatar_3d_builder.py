from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AVATAR_3D_PROFILE_PATH = PROJECT_ROOT / "backend" / "data" / "avatar_3d_profile.json"
VIRTUAL_SPACE_PATH = PROJECT_ROOT / "backend" / "data" / "virtual_space.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_avatar_3d_package(brief: dict) -> dict:
    profile = load_json(AVATAR_3D_PROFILE_PATH)
    space = load_json(VIRTUAL_SPACE_PATH)
    memory = brief.get("memory_summary", {})
    butler = brief.get("butler_brief", {})
    speech_script = butler.get("speech_script", [])
    reminder_plan = brief.get("reminder_plan", {})

    navigation_points = build_navigation_points(space)
    runtime_state = build_runtime_state(memory, butler)
    animation_plan = build_animation_plan(speech_script, reminder_plan)

    return {
        "version": "avatar-3d-package-v1",
        "avatar_profile": profile,
        "virtual_space": space,
        "runtime_state": runtime_state,
        "animation_plan": animation_plan,
        "navigation_points": navigation_points,
        "space_storyboard": build_space_storyboard(space, animation_plan),
        "asset_requirements": build_asset_requirements(profile),
    }


def build_runtime_state(memory: dict, butler: dict) -> dict:
    return {
        "character_name": butler.get("name", "松果"),
        "owner_name": memory.get("owner_name", "小主人"),
        "default_expression": "warm",
        "default_pose": "idle_stand",
        "default_location": "briefing_spot",
        "wardrobe_slot": "daily_home_v1",
        "voice_slot": "cn_female_sunshine_v1",
    }


def build_animation_plan(speech_script: list[dict], reminder_plan: dict) -> dict:
    clips = []
    for index, item in enumerate(speech_script, start=1):
        voice = item.get("voice") or {}
        section = str(item.get("section", f"speech_{index}"))
        style = str(voice.get("style", "clear"))
        clips.append(
            {
                "id": f"clip_{index:02d}",
                "section": section,
                "state": map_style_to_state(style, section),
                "gesture": map_style_to_gesture(style, section),
                "locomotion": "idle_in_place",
                "look_at": "owner_camera",
                "duration_ms": estimate_clip_duration(str(item.get("text", "")), int(voice.get("pause_after_ms", 0) or 0)),
            }
        )

    reminders = []
    for index, item in enumerate((reminder_plan.get("items") or [])[:8], start=1):
        avatar = item.get("avatar") or {}
        reminders.append(
            {
                "id": f"reminder_{index:02d}",
                "trigger_time": item.get("time", ""),
                "expression": avatar.get("expression", "warm"),
                "gesture": avatar.get("gesture", "small_nod"),
                "locomotion": "walk_to_owner",
                "location": "owner_side",
            }
        )

    return {
        "briefing_clips": clips,
        "reminder_clips": reminders,
        "idle_loop": {
            "expression": "warm",
            "gesture": "breathing_idle",
            "locomotion": "ambient_shift",
        },
    }


def build_navigation_points(space: dict) -> list[dict]:
    points = []
    for item in space.get("hotspots", []):
        points.append(
            {
                "id": item.get("id", "point"),
                "label": item.get("label", "Point"),
                "location": item.get("location", [0, 0, 0]),
                "use_case": item.get("use_case", "general"),
            }
        )
    return points


def build_space_storyboard(space: dict, animation_plan: dict) -> list[dict]:
    hotspots = {item.get("id"): item for item in space.get("hotspots", [])}
    reminder_clips = animation_plan.get("reminder_clips", [])
    route = [
        {
            "step": 1,
            "location": "briefing_spot",
            "camera": "full_body",
            "action": "idle_greeting",
            "reason": "早报开始时以全身站姿亮相，建立私人管家的存在感。",
        },
        {
            "step": 2,
            "location": "window_side",
            "camera": "medium",
            "action": "weather_commentary",
            "reason": "讲天气和穿衣建议时走到窗边，空间语义更自然。",
        },
        {
            "step": 3,
            "location": "desk_side",
            "camera": "medium_close",
            "action": "market_briefing",
            "reason": "讲财经、项目和待办时靠近控制台或桌边。",
        },
    ]
    if reminder_clips:
        route.append(
            {
                "step": 4,
                "location": "owner_side",
                "camera": "medium",
                "action": "active_reminder",
                "reason": "到点提醒时靠近主人，提高陪伴感和提醒感。",
            }
        )
    route.append(
        {
            "step": len(route) + 1,
            "location": "briefing_spot",
            "camera": "full_body",
            "action": "warm_closing",
            "reason": "结束时回到主位，方便切回待机循环。",
        }
    )
    for item in route:
        hotspot = hotspots.get(item["location"], {})
        item["coordinates"] = hotspot.get("location", [0, 0, 0])
    return route


def build_asset_requirements(profile: dict) -> list[dict]:
    outfit = profile.get("outfit", {})
    face = profile.get("face", {})
    hair = profile.get("hair", {})
    return [
        {"category": "body", "target": "stylized_realistic_female_18yo", "notes": "full body rig for Unreal/Unity"},
        {"category": "face", "target": face.get("shape", "soft_oval"), "notes": "52 ARKit blendshapes or equivalent"},
        {"category": "hair", "target": hair.get("style", "long_soft_layers"), "notes": "front bangs plus pony-tail or loose back layers"},
        {"category": "outfit", "target": outfit.get("default", "mint_housekeeper_dress"), "notes": "daily outfit with warm home assistant tone"},
        {"category": "space", "target": "home_console_room_v1", "notes": "briefing point, desk point, ambient walking loop"},
    ]


def map_style_to_state(style: str, section: str) -> str:
    if style == "careful":
        return "focused"
    if style == "gentle":
        return "gentle"
    if style == "encouraging":
        return "encouraging"
    if section == "opening":
        return "smile"
    return "warm"


def map_style_to_gesture(style: str, section: str) -> str:
    if style == "careful":
        return "point_screen"
    if style == "gentle":
        return "open_palm"
    if style == "encouraging":
        return "checklist"
    if section == "opening":
        return "wave"
    return "small_nod"


def estimate_clip_duration(text: str, pause_ms: int) -> int:
    speaking_ms = min(7000, max(1800, len(text) * 55))
    return speaking_ms + pause_ms
