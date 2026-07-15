from __future__ import annotations

import argparse
import json
import mimetypes
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from local_memory import add_list_item, load_user_profile, remove_list_item, save_user_profile, summarize_profile
from qa_builder import answer_question, load_latest_bundle
from config import get_settings
from stock_watchlist import add_stock, load_stock_watchlist, remove_stock, search_stock
from touzid_client import TouzidClientError, fetch_stock_watchlist_snapshot

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REMINDERS_PATH = PROJECT_ROOT / "backend" / "data" / "reminders.json"
USER_PROFILE_PATH = PROJECT_ROOT / "backend" / "data" / "user_profile.json"
MOTION_CONFIG_PATH = PROJECT_ROOT / "frontend" / "avatar_motion_clips.json"
TODOS_PATH = PROJECT_ROOT / "backend" / "data" / "todos.json"
STOCK_WATCHLIST_PATH = PROJECT_ROOT / "backend" / "data" / "stock_watchlist.json"
MEMORY_SECTIONS = {"regions", "industries", "companies", "markets", "news_topics", "life_reminders"}
NEWS_REFRESH_LOCK = threading.Lock()
TODO_LOCK = threading.Lock()
STOCK_LOCK = threading.Lock()
NEWS_REFRESH_STATE = {"running": False, "last_error": "", "last_finished_at": ""}
NEWS_REFRESH_MIN_INTERVAL = timedelta(minutes=5)
STOCK_SNAPSHOT_CACHE = {"items": [], "updated_at": "", "error": ""}
STOCK_SNAPSHOT_MIN_INTERVAL = timedelta(seconds=90)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="ascii")


def run_news_refresh() -> None:
    """Refresh in the background so an ordinary F5 never leaves the page blank."""
    try:
        command = [sys.executable, str(PROJECT_ROOT / "backend" / "app" / "refresh_news_digest.py")]
        result = subprocess.run(
            command,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=150,
        )
        if result.returncode != 0:
            NEWS_REFRESH_STATE["last_error"] = (result.stderr or result.stdout or "news refresh failed")[-1000:]
        else:
            NEWS_REFRESH_STATE["last_error"] = ""
    except Exception as error:
        NEWS_REFRESH_STATE["last_error"] = str(error)
    finally:
        NEWS_REFRESH_STATE["last_finished_at"] = datetime.now(timezone.utc).isoformat()
        NEWS_REFRESH_STATE["running"] = False
        NEWS_REFRESH_LOCK.release()


def latest_bundle_is_fresh() -> bool:
    latest_path = PROJECT_ROOT / "demos" / "latest.json"
    if not latest_path.exists():
        return False


def stock_snapshot_is_fresh() -> bool:
    updated = STOCK_SNAPSHOT_CACHE.get("updated_at") or ""
    if not updated:
        return False
    try:
        return datetime.now(timezone.utc) - datetime.fromisoformat(updated) < STOCK_SNAPSHOT_MIN_INTERVAL
    except ValueError:
        return False


def get_stock_snapshot(force: bool = False) -> dict:
    """Fetch selected A-share indicators with a short server-side cache."""
    with STOCK_LOCK:
        selected = load_stock_watchlist(STOCK_WATCHLIST_PATH)
        if not force and stock_snapshot_is_fresh():
            return {"items": STOCK_SNAPSHOT_CACHE["items"], "cached": True, "error": STOCK_SNAPSHOT_CACHE["error"]}
        try:
            # This request originates from the long-running dashboard process,
            # not from morning_brief_demo.py. Load .env here before resolving
            # the Touzid token; otherwise a shell test succeeds while the web
            # endpoint incorrectly reports a missing credential.
            settings = get_settings()
            items = fetch_stock_watchlist_snapshot(
                selected,
                token=settings.touzid_token,
                token_path=settings.touzid_token_path,
                timeout_seconds=settings.touzid_timeout_seconds,
            )
            STOCK_SNAPSHOT_CACHE.update({
                "items": items,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "error": "",
            })
        except TouzidClientError as error:
            STOCK_SNAPSHOT_CACHE.update({
                "items": [],
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "error": str(error),
            })
        return {"items": STOCK_SNAPSHOT_CACHE["items"], "cached": False, "error": STOCK_SNAPSHOT_CACHE["error"]}
    try:
        latest = read_json(latest_path)
        bundle_path = PROJECT_ROOT / "demos" / str(latest.get("bundle_path") or "")
        if not bundle_path.exists():
            return False
        modified_at = datetime.fromtimestamp(bundle_path.stat().st_mtime, tz=timezone.utc)
        return datetime.now(timezone.utc) - modified_at < NEWS_REFRESH_MIN_INTERVAL
    except (OSError, ValueError, json.JSONDecodeError):
        return False


def read_todos() -> dict:
    if TODOS_PATH.exists():
        return read_json(TODOS_PATH)
    payload = {"version": "todo-list-v1", "items": []}
    write_json(TODOS_PATH, payload)
    return payload


def normalize_todo(payload: dict) -> dict:
    title = str(payload.get("title", "")).strip()
    note = str(payload.get("note", "")).strip()
    if not title:
        raise ValueError("title is required")
    # Python deliberately randomizes hash() between processes.  A UUID keeps
    # the browser-facing ID stable and collision-free across server restarts.
    todo_id = f"todo-{uuid.uuid4().hex}"
    return {
        "id": todo_id,
        "title": title,
        "note": note,
        "completed": bool(payload.get("completed", False)),
    }



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
        if parsed.path == "/api/todos":
            return self.write_json_response(read_todos())
        if parsed.path == "/api/memory":
            return self.get_memory()
        if parsed.path == "/api/stocks/watchlist":
            return self.get_stock_watchlist()
        if parsed.path == "/api/news/status":
            return self.write_json_response({"ok": True, **NEWS_REFRESH_STATE})
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/todos/add":
                return self.add_todo()
            if parsed.path == "/api/todos/toggle":
                return self.toggle_todo()
            if parsed.path == "/api/todos/delete":
                return self.delete_todos()
            if parsed.path == "/api/reminders/add":
                return self.add_reminder()
            if parsed.path == "/api/reminders/toggle":
                return self.toggle_reminder()
            if parsed.path == "/api/brief/regenerate":
                return self.regenerate_brief()
            if parsed.path == "/api/news/refresh":
                return self.refresh_news()
            if parsed.path == "/api/ask":
                return self.answer_question()
            if parsed.path == "/api/memory/add":
                return self.add_memory()
            if parsed.path == "/api/memory/remove":
                return self.remove_memory()
            if parsed.path == "/api/stocks/search":
                return self.search_stocks()
            if parsed.path == "/api/stocks/add":
                return self.add_stock_watchlist()
            if parsed.path == "/api/stocks/remove":
                return self.remove_stock_watchlist()
            if parsed.path == "/api/stocks/refresh":
                return self.refresh_stock_watchlist()
            if parsed.path == "/api/motion/save":
                return self.save_motion_config()
        except Exception as error:
            return self.write_json_response({"ok": False, "error": str(error)}, status=400)
        self.write_json_response({"ok": False, "error": "unknown endpoint"}, status=404)

    def add_todo(self) -> None:
        new_item = normalize_todo(self.read_body_json())
        # The dashboard uses ThreadingHTTPServer, so serialize the read-modify-
        # write cycle and avoid dropping an item when two browser actions land
        # at nearly the same time.
        with TODO_LOCK:
            payload = read_todos()
            items = payload.setdefault("items", [])
            items.insert(0, new_item)
            write_json(TODOS_PATH, payload)
        self.write_json_response({"ok": True, "todos": payload})

    def toggle_todo(self) -> None:
        payload = self.read_body_json()
        todo_id = str(payload.get("id", "")).strip()
        completed = bool(payload.get("completed", False))
        if not todo_id:
            raise ValueError("id is required")
        with TODO_LOCK:
            todos = read_todos()
            matched = 0
            for item in todos.setdefault("items", []):
                if str(item.get("id", "")) == todo_id:
                    item["completed"] = completed
                    matched += 1
            if not matched:
                raise ValueError(f"no todo matched: {todo_id}")
            write_json(TODOS_PATH, todos)
        self.write_json_response({"ok": True, "todos": todos})

    def delete_todos(self) -> None:
        payload = self.read_body_json()
        ids = payload.get("ids", [])
        if not isinstance(ids, list) or not ids:
            raise ValueError("ids must be a non-empty list")
        id_set = {str(item).strip() for item in ids if str(item).strip()}
        with TODO_LOCK:
            todos = read_todos()
            before = len(todos.get("items", []))
            todos["items"] = [item for item in todos.get("items", []) if str(item.get("id", "")) not in id_set]
            deleted = before - len(todos["items"])
            if deleted <= 0:
                raise ValueError("no todos deleted")
            write_json(TODOS_PATH, todos)
        self.write_json_response({"ok": True, "deleted": deleted, "todos": todos})

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

    def get_stock_watchlist(self) -> None:
        selected = load_stock_watchlist(STOCK_WATCHLIST_PATH)
        snapshot = get_stock_snapshot()
        self.write_json_response({"ok": True, "watchlist": selected, **snapshot})

    def search_stocks(self) -> None:
        payload = self.read_body_json()
        query = str(payload.get("query", "")).strip()
        if not query:
            raise ValueError("请输入股票代码或名称")
        selected = load_stock_watchlist(STOCK_WATCHLIST_PATH)
        settings = get_settings()
        rows = search_stock(
            query,
            selected,
            token=settings.touzid_token,
            token_path=settings.touzid_token_path,
        )
        self.write_json_response({"ok": True, "items": rows})

    def add_stock_watchlist(self) -> None:
        payload = self.read_body_json()
        with STOCK_LOCK:
            items = add_stock(STOCK_WATCHLIST_PATH, payload)
            STOCK_SNAPSHOT_CACHE.update({"items": [], "updated_at": "", "error": ""})
        self.write_json_response({"ok": True, "watchlist": items})

    def remove_stock_watchlist(self) -> None:
        payload = self.read_body_json()
        symbol = str(payload.get("symbol", "")).strip()
        if not symbol:
            raise ValueError("缺少股票代码")
        with STOCK_LOCK:
            items = remove_stock(STOCK_WATCHLIST_PATH, symbol)
            STOCK_SNAPSHOT_CACHE.update({"items": [], "updated_at": "", "error": ""})
        self.write_json_response({"ok": True, "watchlist": items})

    def refresh_stock_watchlist(self) -> None:
        self.write_json_response({"ok": True, "watchlist": load_stock_watchlist(STOCK_WATCHLIST_PATH), **get_stock_snapshot(force=True)})
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

    def refresh_news(self) -> None:
        """Refresh only the news pool; used by a normal browser F5."""
        if latest_bundle_is_fresh():
            self.write_json_response({"ok": True, "running": False, "skipped": True, "message": "新闻池仍在最新窗口内"})
            return
        if not NEWS_REFRESH_LOCK.acquire(blocking=False):
            self.write_json_response({"ok": True, "running": True, "message": "新闻池正在刷新"}, status=202)
            return
        NEWS_REFRESH_STATE["running"] = True
        NEWS_REFRESH_STATE["last_error"] = ""
        threading.Thread(target=run_news_refresh, name="sunguo-news-refresh", daemon=True).start()
        self.write_json_response({"ok": True, "running": True, "message": "已开始刷新新闻池"}, status=202)



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






