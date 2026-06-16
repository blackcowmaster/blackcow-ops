#!/usr/bin/env python3
"""blackcow-app-scraper — Extract app reviews + metadata from Play Store & App Store.
Usage:
  .venv/bin/python scripts/app_scraper.py <app-url> [--count N] [--format json|csv]
  .venv/bin/python scripts/app_scraper.py --search "<query>" --country CN [--limit 10]
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
        "summary": raw.get("summary"),
        "developer": raw.get("developer"),
        "category": raw.get("genre"),
        "genre_id": raw.get("genreId"),
        "rating": raw.get("score"),
        "rating_count": raw.get("ratings"),
        "review_count": raw.get("reviews"),
        "rating_histogram": raw.get("histogram"),
        "installs": raw.get("installs"),
        "real_installs": raw.get("realInstalls"),
        "min_installs": raw.get("minInstalls"),
        "description": raw.get("description"),
        "whats_new": raw.get("whatsNew"),
        "price": raw.get("price"),
        "currency": raw.get("currency"),
        "version": raw.get("version"),
        "released": raw.get("released"),
        "updated": raw.get("lastUpdated"),
        "android_version": raw.get("androidVersion"),
        "content_rating": raw.get("contentRating"),
        "content_rating_desc": raw.get("contentRatingDescription"),
        "free": raw.get("free"),
        "contains_ads": raw.get("containsAds"),
        "ad_supported": raw.get("adSupported"),
        "offers_iap": raw.get("offersIAP"),
        "in_app_price_range": raw.get("inAppProductPrice"),
        "privacy_policy_url": raw.get("privacyPolicy"),
        "developer_website": raw.get("developerWebsite"),
        "developer_email": raw.get("developerEmail"),
        "publisher_country": raw.get("publisherCountry"),
        "icon_url": raw.get("icon"),
        "screenshots": raw.get("screenshots", []),
        "url": raw.get("appUrl"),
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

# ── Search Mode ──────────────────────────────────────────────────────────

def _do_search(args):
    from app_reviews import AppStoreSearch, AppStoreReviews, Country
    import urllib.request

    search = AppStoreSearch()
    country = Country[args.country] if args.country in Country.__members__ else Country.CN

    print(f"🔍 Searching App Store ({args.country}): {args.search}", file=sys.stderr)
    results = search.search(args.search, country=country, limit=args.limit)

    output = []
    for i, r in enumerate(results):
        # Fetch screenshots via iTunes Lookup API
        screenshots = _fetch_screenshots(r.app_id, args.country.lower())

        entry = {
            "name": r.name,
            "app_id": r.app_id,
            "developer": r.developer,
            "category": r.category,
            "rating": r.rating,
            "rating_count": r.rating_count,
            "price": r.price,
            "version": r.version,
            "icon_url": r.icon_url,
            "screenshots": screenshots,
            "url": r.url,
        }

        # check Korean store for the same app name
        if args.check_kr:
            kr_results = search.search(r.name, country=Country.KR, limit=3)
            kr_match = None
            for kr in kr_results:
                if kr.developer == r.developer or _name_similarity(kr.name, r.name) > 0.7:
                    kr_match = {"name": kr.name, "app_id": kr.app_id, "rating": kr.rating}
                    break
            entry["kr_available"] = kr_match is not None
            entry["kr_match"] = kr_match
            if kr_match:
                print(f"  🇰🇷 KR: {kr_match['name']} ⭐{kr_match['rating']} ({len(screenshots)} screens)", file=sys.stderr)
            else:
                print(f"  🚀 NO KR: {r.name[:50]} ⭐{r.rating} ({len(screenshots)} screens)", file=sys.stderr)
        else:
            print(f"  📱 {r.name[:50]} ⭐{r.rating} ({len(screenshots)} screens)", file=sys.stderr)

        output.append(entry)

    json.dump(output, sys.stdout, indent=2, ensure_ascii=False, default=str)
    print(f"\n✅ Found {len(output)} apps", file=sys.stderr)
    if args.check_kr:
        missing = sum(1 for e in output if not e["kr_available"])
        print(f"🚀 {missing}/{len(output)} apps NOT available in Korea", file=sys.stderr)


def _fetch_screenshots(app_id: str, country: str = "cn") -> list[str]:
    """Fetch screenshot URLs from iTunes Lookup API."""
    import urllib.request
    try:
        url = f"https://itunes.apple.com/lookup?id={app_id}&country={country}"
        req = urllib.request.Request(url, headers={"User-Agent": "blackcow-app-scraper/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("resultCount", 0) > 0:
                result = data["results"][0]
                return result.get("screenshotUrls", [])
    except Exception as e:
        print(f"    ⚠️ Screenshot fetch failed for {app_id}: {e}", file=sys.stderr)
    return []


def _name_similarity(a: str, b: str) -> float:
    """Simple word-overlap similarity for app name matching."""
    a_words = set(a.lower().split())
    b_words = set(b.lower().split())
    if not a_words or not b_words:
        return 0
    return len(a_words & b_words) / min(len(a_words), len(b_words))


def main():
    parser = argparse.ArgumentParser(description="blackcow-app-scraper")
    parser.add_argument("url", nargs="?", help="App Store or Play Store URL, or app ID")
    parser.add_argument("--count", type=int, default=200, help="Number of reviews (default: 200)")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--search", help="Search App Store for keyword (e.g. '走路赚钱')")
    parser.add_argument("--country", default="CN", help="Country code for search (default: CN)")
    parser.add_argument("--limit", type=int, default=10, help="Results limit for search (default: 10)")
    parser.add_argument("--check-kr", action="store_true", help="After search, check if each app exists in KR store")
    args = parser.parse_args()

    # ── search mode ──────────────────────────────────────────────────────
    if args.search:
        _do_search(args)
        return

    if not args.url:
        parser.error("URL required unless using --search")

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
