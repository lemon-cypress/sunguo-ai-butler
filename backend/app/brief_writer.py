from __future__ import annotations

import json
from pathlib import Path

from tts_service import DEFAULT_RATE, DEFAULT_VOLUME, DEFAULT_VOICE_NAME, render_speech_audio


def write_latest_index(latest_path: Path, date_text: str, path_prefix: str = "", speech_audio_name: str | None = None) -> Path:
    normalized_prefix = path_prefix.strip("/")

    def build_path(filename: str) -> str:
        if normalized_prefix:
            return f"{normalized_prefix}/{date_text}/{filename}"
        return f"{date_text}/{filename}"

    latest_payload = {
        "date": date_text,
        "bundle_path": build_path("output_bundle.json"),
        "screen_cards_path": build_path("screen_cards.json"),
        "speech_script_path": build_path("speech_script.json"),
        "avatar_timeline_path": build_path("avatar_timeline.json"),
        "avatar_3d_path": build_path("avatar_3d.json"),
    }
    if speech_audio_name:
        latest_payload["speech_audio_path"] = build_path(speech_audio_name)
    latest_path.write_text(
        json.dumps(latest_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return latest_path


def save_daily_brief(output_dir: Path, brief: dict, rendered_text: str) -> tuple[Path, Path]:
    """Save structured input and rendered brief text for later review."""
    date_text = str(brief.get("date", "unknown-date"))
    daily_dir = output_dir / date_text
    daily_dir.mkdir(parents=True, exist_ok=True)

    json_path = daily_dir / "morning_brief_input.json"
    text_path = daily_dir / "morning_brief.txt"

    json_path.write_text(
        json.dumps(brief, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    text_path.write_text(rendered_text, encoding="utf-8")
    return json_path, text_path


def save_output_bundle(output_dir: Path, output_bundle: dict, update_latest: bool = True) -> dict[str, Path]:
    """Save all output shapes for later UI, TTS, and avatar integration."""
    date_text = str(output_bundle.get("date", "unknown-date"))
    daily_dir = output_dir / date_text
    daily_dir.mkdir(parents=True, exist_ok=True)

    bundle_payload = dict(output_bundle)
    paths = {
        "output_bundle": daily_dir / "output_bundle.json",
        "screen_cards": daily_dir / "screen_cards.json",
        "speech_script": daily_dir / "speech_script.json",
        "avatar_timeline": daily_dir / "avatar_timeline.json",
        "avatar_3d": daily_dir / "avatar_3d.json",
    }
    paths["screen_cards"].write_text(
        json.dumps(bundle_payload.get("screen_cards", []), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    paths["speech_script"].write_text(
        json.dumps(bundle_payload.get("speech_script", []), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    paths["avatar_timeline"].write_text(
        json.dumps(bundle_payload.get("avatar_timeline", []), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    paths["avatar_3d"].write_text(
        json.dumps(bundle_payload.get("avatar_3d", {}), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    try:
        speech_audio_path = render_speech_audio(
            paths["speech_script"],
            daily_dir / "speech_audio.wav",
            voice_name=DEFAULT_VOICE_NAME,
            rate=DEFAULT_RATE,
            volume=DEFAULT_VOLUME,
        )
    except Exception as error:
        print(f"TTS 生成失败，先保留文本和分段语音脚本：{error}")
        speech_audio_path = None

    if speech_audio_path:
        bundle_payload["speech_audio_path"] = f"{date_text}/{speech_audio_path.name}"
        paths["speech_audio"] = speech_audio_path

    paths["output_bundle"].write_text(
        json.dumps(bundle_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if update_latest:
        latest_path = output_dir / "latest.json"
        paths["latest"] = write_latest_index(
            latest_path,
            date_text,
            speech_audio_name=speech_audio_path.name if speech_audio_path else None,
        )
    return paths
