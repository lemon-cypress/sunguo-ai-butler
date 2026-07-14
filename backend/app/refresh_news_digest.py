from __future__ import annotations

"""Refresh only the editorial news portion of today's dashboard bundle.

This job deliberately avoids TTS, avatar, weather and reminder generation. It
can therefore run on a frequent schedule and keep the page's news module fresh
even if another optional subsystem is unavailable.
"""

import argparse
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from brief_writer import write_latest_index
from config import get_settings
from morning_brief_demo import (
    build_company_data,
    build_news_data,
    generate_ai_news_digest,
    remove_untranslated_news_items,
)
from news_digest_builder import build_news_digest
from news_enrichment import enrich_company_snapshot, enrich_news_snapshot


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMOS_DIR = PROJECT_ROOT / "demos"
BEIJING_TZ = timezone(timedelta(hours=8))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="刷新松果网页的新闻汇总")
    parser.add_argument("--date", help="指定 YYYY-MM-DD；默认使用 demos/latest.json")
    parser.add_argument("--no-ai", action="store_true", help="只生成本地事实卡摘要，不调用 DeepSeek")
    return parser.parse_args()


def resolve_bundle_path(date_text: str = "") -> tuple[Path, dict]:
    latest_path = DEMOS_DIR / "latest.json"
    if date_text:
        return DEMOS_DIR / date_text / "output_bundle.json", {"date": date_text}
    if not latest_path.exists():
        # A newly deployed server has no historical morning brief yet.  The
        # focused news refresh is self-sufficient: seed a minimal bundle and
        # let the normal news pipeline populate it on the first browser load.
        today = datetime.now(BEIJING_TZ).date().isoformat()
        today_path = DEMOS_DIR / today / "output_bundle.json"
        today_path.parent.mkdir(parents=True, exist_ok=True)
        if not today_path.exists():
            today_path.write_text(json.dumps({
                "version": "output-v1",
                "project": "松果",
                "date": today,
                "city": "北京-朝阳",
            }, ensure_ascii=False, indent=2), encoding="utf-8")
        return today_path, {"date": today, "bundle_path": f"{today}/output_bundle.json"}
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    bundle_path = DEMOS_DIR / str(latest.get("bundle_path") or "")
    if not bundle_path.exists():
        raise FileNotFoundError(f"Latest output bundle does not exist: {bundle_path}")

    # A previous demo run may leave latest.json pointing at demos/mock/… . A
    # scheduled refresh must never keep mutating that historical mock file or
    # make the browser look like it has today's news when it does not.
    today = datetime.now(BEIJING_TZ).date().isoformat()
    today_path = DEMOS_DIR / today / "output_bundle.json"
    if bundle_path.resolve() != today_path.resolve():
        today_path.parent.mkdir(parents=True, exist_ok=True)
        if not today_path.exists():
            shutil.copy2(bundle_path, today_path)
        latest = dict(latest)
        latest["date"] = today
        latest["bundle_path"] = f"{today}/output_bundle.json"
    return today_path, latest


def build_news_refresh_context(bundle: dict, news_data: dict, company_data: dict) -> dict:
    return {
        "date": bundle.get("date", ""),
        "city": bundle.get("city", ""),
        "news_data": news_data,
        "event_timeline": bundle.get("event_timeline", {}),
        "economic_calendar": bundle.get("economic_calendar", {}),
        "market_data": bundle.get("market_data", {}),
        "china_market_data": bundle.get("china_market_data", {}),
        "theme_data": bundle.get("theme_data", {}),
        "company_watchlist_data": company_data,
        "a_share_company_data": {
            "companies": (bundle.get("structured_market_data", {}) or {}).get("a_share_companies", []),
        },
        "structured_market_data": bundle.get("structured_market_data", {}),
    }


def main() -> None:
    args = parse_args()
    settings = get_settings()
    bundle_path, latest = resolve_bundle_path(args.date or "")
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["date"] = str(latest.get("date") or bundle.get("date") or "")

    news_data = enrich_news_snapshot(build_news_data(settings, use_mock_news=False))
    # Refresh official company filings alongside the general news pool. This
    # gives the editor recent SEC/EDGAR evidence instead of stale bundle data.
    company_data = enrich_company_snapshot(build_company_data(settings, use_mock_companies=False))
    brief = build_news_refresh_context(bundle, news_data, company_data)
    rule_digest = build_news_digest(brief)
    brief["news_digest"] = rule_digest
    brief["news_digest_rules"] = rule_digest

    digest = None if args.no_ai else generate_ai_news_digest(settings, brief)
    bundle["news_digest"] = digest or rule_digest
    # A temporary model/API failure must not send raw English RSS copy to the
    # Chinese dashboard. Keep the verified Chinese rows and let the selectable
    # original-title list remain the place for reading source-language articles.
    if digest is None:
        remove_untranslated_news_items(bundle["news_digest"])
    bundle["news_pool_audit"] = rule_digest.get("news_pool", {})
    bundle["news_data"] = news_data
    bundle["company_data"] = company_data
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    # Keep the default web entry on the fresh real-date bundle. The dashboard
    # reads demos/latest.json when no explicit date is selected.
    write_latest_index(DEMOS_DIR / "latest.json", bundle["date"])

    pool = rule_digest.get("news_pool", {})
    item_count = sum(len(section.get("items", [])) for section in (bundle["news_digest"].get("sections", []) or []))
    print(f"News refresh complete: {bundle_path}")
    print(f"fact cards={len(pool.get('top_candidates', []))}; digest items={item_count}; ai={'yes' if digest else 'no'}")
    print(f"dashboard source={bundle['date']}/output_bundle.json")


if __name__ == "__main__":
    main()
