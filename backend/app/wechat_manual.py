from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


WECHAT_HOSTS = {"mp.weixin.qq.com", "weixin.qq.com"}


def read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_whitelist(path: Path) -> dict:
    payload = read_json(path, {"accounts": []})
    accounts = [item for item in payload.get("accounts", []) if isinstance(item, dict) and str(item.get("name", "")).strip()]
    return {**payload, "accounts": accounts}


def load_articles(path: Path) -> dict:
    payload = read_json(path, {"version": "wechat-manual-articles-v1", "articles": []})
    articles = [item for item in payload.get("articles", []) if isinstance(item, dict)]
    return {"version": "wechat-manual-articles-v1", "articles": articles}


def add_article(path: Path, whitelist: dict, payload: dict) -> dict:
    account = str(payload.get("account", "")).strip()
    title = str(payload.get("title", "")).strip()
    url = str(payload.get("url", "")).strip()
    summary = str(payload.get("summary", "")).strip()
    allowed_accounts = {str(item.get("name", "")).strip() for item in whitelist.get("accounts", [])}
    if account not in allowed_accounts:
        raise ValueError("请选择白名单中的公众号")
    if not title:
        raise ValueError("请输入文章标题")
    if len(title) > 180 or len(summary) > 1200:
        raise ValueError("标题或摘要过长")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in WECHAT_HOSTS or not parsed.path.startswith("/s"):
        raise ValueError("仅支持粘贴 mp.weixin.qq.com 的公开文章链接")

    saved = load_articles(path)
    normalized_url = url.split("#", 1)[0]
    if any(str(item.get("url", "")).split("#", 1)[0] == normalized_url for item in saved["articles"]):
        raise ValueError("该文章链接已导入")
    item = {
        "id": f"wechat-{uuid.uuid4().hex}",
        "account": account,
        "title": title,
        "url": url,
        "summary": summary,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "source_confidence": "lead",
        "review_status": "待核实",
    }
    saved["articles"].insert(0, item)
    write_json(path, saved)
    return saved


def remove_article(path: Path, article_id: str) -> dict:
    saved = load_articles(path)
    before = len(saved["articles"])
    saved["articles"] = [item for item in saved["articles"] if str(item.get("id", "")) != article_id]
    if len(saved["articles"]) == before:
        raise ValueError("未找到该导入文章")
    write_json(path, saved)
    return saved


def build_news_snapshot(path: Path) -> dict:
    articles = load_articles(path).get("articles", [])
    return {
        "source": "微信公众号手动导入（待核实）",
        "categories": [{
            "category": "wechat_manual",
            "label": "微信公众号手动导入（待核实）",
            "articles": [{
                "title": item.get("title", ""),
                "description": item.get("summary", ""),
                "url": item.get("url", ""),
                "published": item.get("imported_at", ""),
                "source_name": f"微信公众号·{item.get('account', '')}",
                "source_type": "wechat_manual",
                "source_domain": "mp.weixin.qq.com",
                "confidence": "lead",
            } for item in articles],
        }] if articles else [],
        "errors": [],
        "note": "用户手动粘贴的公开文章链接，仅作为待核实线索；不会自动抓取正文或作为已验证事实展示。",
    }
