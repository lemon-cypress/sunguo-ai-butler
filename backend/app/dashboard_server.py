from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from local_memory import add_list_item, load_user_profile, remove_list_item, save_user_profile, summarize_profile
from qa_builder import answer_question, load_latest_bundle

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REMINDERS_PATH = PROJECT_ROOT / "backend" / "data" / "reminders.json"
USER_PROFILE_PATH = PROJECT_ROOT / "backend" / "data" / "user_profile.json"
MOTION_CONFIG_PATH = PROJECT_ROOT / "frontend" / "avatar_motion_clips.json"
MEMORY_SECTIONS = {"regions", "industries", "companies", "markets", "news_topics", "life_reminders"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="ascii")



def merge_motion_config(base: dict, patch: dict) -> dict:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_motion_config(merged[key], value)
        else:
            merged[key] = value
    return merged

def normalize_reminder(payload: dict) -> dict:
    time = str(payload.get("time", "")).strip()
    title = str(payload.get("title", "")).strip()
    message = str(payload.get("message", "")).strip()
    reminder_type = str(payload.get("type", "life")).strip() or "life"
    priority = str(payload.get("priority", "normal")).strip() or "normal"
    if not time or len(time) != 5 or time[2] != ":":
        raise ValueError("time must look like HH:MM")
    if not title:
        raise ValueError("title is required")
    if not message:
        raise ValueError("message is required")
    return {
        "enabled": bool(payload.get("enabled", True)),
        "time": time,
        "type": reminder_type,
        "priority": "high" if priority == "high" else "normal",
        "title": title,
        "message": message,
        "voice_style": "careful" if reminder_type == "medicine" else "warm",
        "avatar_expression": "focused" if priority == "high" else "warm",
        "avatar_gesture": "small_nod",
    }


class DashboardHandler(SimpleHTTPRequestHandler):
    server_version = "SunguoDashboard/0.1"

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        clean = unquote(parsed.path).lstrip("/")
        if not clean:
            clean = "frontend/index.html"
        return str((PROJECT_ROOT / clean).resolve())

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/reminders":
            return self.write_json_response(read_json(REMINDERS_PATH))
        if parsed.path == "/api/memory":
            return self.get_memory()
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/reminders/add":
                return self.add_reminder()
            if parsed.path == "/api/reminders/toggle":
                return self.toggle_reminder()
            if parsed.path == "/api/brief/regenerate":
                return self.regenerate_brief()
            if parsed.path == "/api/ask":
                return self.answer_question()
            if parsed.path == "/api/memory/add":
                return self.add_memory()
            if parsed.path == "/api/memory/remove":
                return self.remove_memory()
            if parsed.path == "/api/motion/save":
                return self.save_motion_config()
        except Exception as error:
            return self.write_json_response({"ok": False, "error": str(error)}, status=400)
        self.write_json_response({"ok": False, "error": "unknown endpoint"}, status=404)

    def add_reminder(self) -> None:
        rules = read_json(REMINDERS_PATH)
        reminders = rules.setdefault("fixed_reminders", [])
        reminders.append(normalize_reminder(self.read_body_json()))
        write_json(REMINDERS_PATH, rules)
        self.write_json_response({"ok": True, "rules": rules})

    def toggle_reminder(self) -> None:
        payload = self.read_body_json()
        title = str(payload.get("title", "")).strip()
        enabled = bool(payload.get("enabled", True))
        if not title:
            raise ValueError("title is required")
        rules = read_json(REMINDERS_PATH)
        matched = 0
        for item in rules.setdefault("fixed_reminders", []):
            if title in str(item.get("title", "")):
                item["enabled"] = enabled
                matched += 1
        if not matched:
            raise ValueError(f"no reminder matched: {title}")
        write_json(REMINDERS_PATH, rules)
        self.write_json_response({"ok": True, "matched": matched, "rules": rules})

    def get_memory(self) -> None:
        profile = load_user_profile(USER_PROFILE_PATH)
        self.write_json_response({"ok": True, "profile": profile, "summary": summarize_profile(profile)})

    def add_memory(self) -> None:
        payload = self.read_body_json()
        section = str(payload.get("section", "")).strip()
        item = str(payload.get("item", "")).strip()
        if section not in MEMORY_SECTIONS:
            raise ValueError(f"unsupported memory section: {section}")
        if not item:
            raise ValueError("item is required")
        profile = load_user_profile(USER_PROFILE_PATH)
        profile = add_list_item(profile, section, item)
        save_user_profile(USER_PROFILE_PATH, profile)
        self.write_json_response({"ok": True, "profile": profile, "summary": summarize_profile(profile)})

    def remove_memory(self) -> None:
        payload = self.read_body_json()
        section = str(payload.get("section", "")).strip()
        item = str(payload.get("item", "")).strip()
        if section not in MEMORY_SECTIONS:
            raise ValueError(f"unsupported memory section: {section}")
        if not item:
            raise ValueError("item is required")
        profile = load_user_profile(USER_PROFILE_PATH)
        profile = remove_list_item(profile, section, item)
        save_user_profile(USER_PROFILE_PATH, profile)
        self.write_json_response({"ok": True, "profile": profile, "summary": summarize_profile(profile)})
    def answer_question(self) -> None:
        payload = self.read_body_json()
        question = str(payload.get("question", "")).strip()
        use_mock = bool(payload.get("mock", False))
        demos_dir = PROJECT_ROOT / "demos" / "mock" if use_mock else PROJECT_ROOT / "demos"
        bundle = load_latest_bundle(demos_dir)
        result = answer_question(bundle, question)
        self.write_json_response({"ok": True, "result": result})

    def regenerate_brief(self) -> None:
        payload = self.read_body_json()
        use_mock = bool(payload.get("mock", False))
        command = [
            sys.executable,
            str(PROJECT_ROOT / "backend" / "app" / "morning_brief_demo.py"),
            "--no-ai",
            "--save",
        ]
        if use_mock:
            command.extend([
                "--mock-weather",
                "--mock-market",
                "--mock-news",
                "--mock-themes",
                "--mock-companies",
            ])
        result = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "regenerate failed")[-2000:])
        latest_path = PROJECT_ROOT / "demos" / "mock" / "latest.json" if use_mock else PROJECT_ROOT / "demos" / "latest.json"
        latest = read_json(latest_path) if latest_path.exists() else {}
        self.write_json_response({
            "ok": True,
            "mock": use_mock,
            "latest": latest,
            "stdout_tail": result.stdout[-2000:],
        })



    def save_motion_config(self) -> None:
        payload = self.read_body_json()
        patch = payload.get("patch", {})
        if not isinstance(patch, dict):
            raise ValueError("patch must be an object")
        config = read_json(MOTION_CONFIG_PATH)
        merged = merge_motion_config(config, patch)
        write_json(MOTION_CONFIG_PATH, merged)
        self.write_json_response({"ok": True, "config": merged})

    def read_body_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(data or "{}")

    def write_json_response(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def guess_type(self, path: str) -> str:
        return mimetypes.guess_type(path)[0] or "application/octet-stream"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sunguo dashboard server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Sunguo dashboard: http://{args.host}:{args.port}/frontend/")
    server.serve_forever()


if __name__ == "__main__":
    main()






