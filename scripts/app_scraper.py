#!/usr/bin/env python3
"""blackcow-app-scraper — Extract app reviews + metadata from Play Store & App Store.
Usage:
  .venv/bin/python scripts/app_scraper.py <app-url> [--count N] [--format json|csv]
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── helpers ──────────────────────────────────────────────────────────────

def parse_url(url: str) -> dict[str, str | None]:
    """Parse an App Store or Play Store URL and return {store, app_id, lang}."""
    # App Store: https://apps.apple.com/.../id123456789
    m = re.search(r'/id(\d+)', url)
    if m:
        return {"store": "appstore", "app_id": m.group(1), "lang": None}

    # Play Store: ...?id=com.example.app&hl=ko
    m = re.search(r'[?&]id=([\w.]+)', url)
    if m:
        pkg = m.group(1)
        lang_match = re.search(r'hl=(\w+)', url)
        return {"store": "playstore", "app_id": pkg, "lang": lang_match.group(1) if lang_match else "ko"}

    # bare package name
    if re.match(r'^[\w.]+\.[\w.]+$', url):
        return {"store": "playstore", "app_id": url, "lang": "ko"}

    # bare numeric ID
    if url.isdigit():
        return {"store": "appstore", "app_id": url, "lang": None}

    print("⚠️  Could not parse URL. Assuming Play Store package name.", file=sys.stderr)
    return {"store": "playstore", "app_id": url, "lang": "ko"}


# ── Play Store scraping (gplay-scraper) ─────────────────────────────────

def fetch_playstore(app_id: str, lang: str, count: int) -> dict[str, Any]:
    from gplay_scraper import GPlayScraper
    scraper = GPlayScraper()
    data = scraper.app_analyze(app_id, lang=lang, country="kr")
    reviews = scraper.reviews_analyze(app_id, count=count, sort="NEWEST", lang=lang, country="kr")
    similar = scraper.similar_analyze(app_id, count=10, lang=lang, country="kr")
    developer_apps = []
    # Developer id may not always be returned – try extracting
    dev_id = data.get("developerId")
    if dev_id and dev_id != "%ED%8A%B8%EB%A6%AC%EA%B1%B0%EC%8A%A4":
        try:
            developer_apps = scraper.developer_analyze(dev_id, count=20, lang=lang, country="kr")
        except Exception:
            pass

    return {
        "store": "playstore",
        "app_id": app_id,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "metadata": _normalize_playstore_meta(data),
        "reviews": [_normalize_playstore_review(r) for r in reviews],
        "similar_apps": similar[:10],
        "developer_apps": developer_apps[:20] if developer_apps else [],
        "count": len(reviews),
    }


def _normalize_playstore_meta(raw: dict) -> dict:
    return {
        "title": raw.get("title"),
        "developer": raw.get("developer"),
        "category": raw.get("genre"),
        "rating": raw.get("score"),
        "rating_count": raw.get("ratings"),
        "installs": raw.get("installs"),
        "description": raw.get("description"),
        "price": raw.get("price"),
        "version": raw.get("version"),
        "updated": raw.get("lastUpdated"),
        "icon_url": raw.get("icon"),
        "screenshots": raw.get("screenshots", []),
        "url": raw.get("appUrl"),
        "free": raw.get("free"),
        "contains_ads": raw.get("containsAds"),
        "ad_supported": raw.get("adSupported"),
        "offers_iap": raw.get("offersIAP"),
        "in_app_price_range": raw.get("inAppProductPrice"),
        "content_rating": raw.get("contentRating"),
        "released": raw.get("released"),
        "android_version": raw.get("androidVersion"),
    }


def _normalize_playstore_review(raw: dict) -> dict:
    return {
        "id": raw.get("reviewId"),
        "rating": raw.get("score"),
        "author": raw.get("userName"),
        "text": raw.get("content"),
        "thumbs_up": raw.get("thumbsUpCount", 0),
        "app_version": raw.get("appVersion"),
        "created_at": raw.get("at"),
        "is_dev_response": False,
    }


# ── App Store scraping (app-reviews) ────────────────────────────────────

def fetch_appstore(app_id: str, count: int) -> dict[str, Any]:
    from app_reviews import AppStoreReviews, AppStoreSearch, Country
    client = AppStoreReviews()
    result = client.fetch(app_id, countries=[Country.US, Country.KR])
    search = AppStoreSearch()
    metadata = search.lookup(app_id)

    return {
        "store": "appstore",
        "app_id": app_id,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "metadata": _normalize_appstore_meta(metadata),
        "reviews": [_normalize_appstore_review(r) for r in result.reviews][:count],
        "similar_apps": [],
        "developer_apps": [],
        "count": min(len(result.reviews), count),
    }


def _normalize_appstore_meta(meta) -> dict:
    if meta is None:
        return {}
    return {
        "title": meta.name,
        "developer": meta.developer,
        "category": meta.category,
        "rating": meta.rating,
        "rating_count": meta.rating_count,
        "description": None,
        "price": meta.price,
        "version": meta.version,
        "updated": None,
        "icon_url": meta.icon_url,
        "screenshots": [],
        "url": meta.url,
    }


def _normalize_appstore_review(review) -> dict:
    return {
        "id": review.id,
        "rating": review.rating,
        "author": review.author_name,
        "title": review.title,
        "text": review.body,
        "thumbs_up": 0,
        "app_version": review.app_version,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "is_dev_response": False,
    }


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="blackcow-app-scraper")
    parser.add_argument("url", help="App Store or Play Store URL, or app ID")
    parser.add_argument("--count", type=int, default=200, help="Number of reviews (default: 200)")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    args = parser.parse_args()

    info = parse_url(args.url)
    store = info["store"]
    app_id = info["app_id"]
    lang = info["lang"]

    print(f"🔍 Fetching {store}:{app_id} (count={args.count})", file=sys.stderr)

    try:
        if store == "playstore":
            result = fetch_playstore(app_id, lang, args.count)
        else:
            result = fetch_appstore(app_id, args.count)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "csv":
        _write_csv(result, sys.stdout)
    else:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False, default=str)

    print(f"\n✅ Done — {result['count']} reviews", file=sys.stderr)


def _write_csv(result: dict, out):
    import csv
    writer = csv.writer(out)
    writer.writerow(["id", "rating", "author", "text", "thumbs_up", "app_version", "created_at", "is_dev_response"])
    for r in result["reviews"]:
        writer.writerow([r["id"], r["rating"], r["author"], r["text"], r["thumbs_up"], r["app_version"], r["created_at"], r["is_dev_response"]])


if __name__ == "__main__":
    main()
