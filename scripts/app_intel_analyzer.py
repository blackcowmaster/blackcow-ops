#!/usr/bin/env python3
"""blackcow-app-intel analyzer — Pure statistical analysis, NO language-dependent logic.
All sentiment/meaning extraction is left to the LLM.
Usage:
  .venv/bin/python scripts/app_intel_analyzer.py <.json file> [--lang ko|en] [-o report.md]
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any


def analyze_reviews(reviews: list[dict]) -> dict[str, Any]:
    """Run pure statistical analysis. No keyword matching, no sentiment."""
    total = len(reviews)
    if total == 0:
        return {"error": "no reviews"}

    # ── rating distribution ──────────────────────────────────────────────
    rating_counts = Counter(r["rating"] for r in reviews)
    avg_rating = round(sum(r["rating"] for r in reviews) / total, 2)

    # ── time series (weekly) ─────────────────────────────────────────────
    weeks = defaultdict(list)
    monthlies = defaultdict(list)
    for r in reviews:
        try:
            dt = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
            week_key = dt.strftime("%Y-W%W")
            month_key = dt.strftime("%Y-%m")
            weeks[week_key].append(r["rating"])
            monthlies[month_key].append(r["rating"])
        except (ValueError, KeyError):
            pass

    rating_trend = []
    for wk in sorted(weeks.keys()):
        vals = weeks[wk]
        rating_trend.append({"period": wk, "avg": round(sum(vals) / len(vals), 2), "count": len(vals)})

    monthly_trend = []
    for mo in sorted(monthlies.keys()):
        vals = monthlies[mo]
        monthly_trend.append({"period": mo, "avg": round(sum(vals) / len(vals), 2), "count": len(vals)})

    # ── version impact ───────────────────────────────────────────────────
    versions = defaultdict(list)
    version_dates = {}
    for r in reviews:
        v = r.get("app_version") or "unknown"
        versions[v].append(r["rating"])
        if v != "unknown":
            try:
                dt = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                if v not in version_dates or dt > version_dates[v]:
                    version_dates[v] = dt
            except (ValueError, KeyError):
                pass

    version_stats = []
    for v, ratings in versions.items():
        # sort by first seen date (newest first), unknowns last
        first_seen = version_dates.get(v, datetime(2000, 1, 1, tzinfo=timezone.utc))
        version_stats.append({
            "version": v,
            "count": len(ratings),
            "avg_rating": round(sum(ratings) / len(ratings), 2),
            "rating_spread": {"1": sum(1 for x in ratings if x == 1),
                              "2": sum(1 for x in ratings if x == 2),
                              "3": sum(1 for x in ratings if x == 3),
                              "4": sum(1 for x in ratings if x == 4),
                              "5": sum(1 for x in ratings if x == 5)},
            "first_seen": first_seen.strftime("%Y-%m-%d") if first_seen.year > 2000 else None,
        })

    version_stats.sort(key=lambda x: (x["first_seen"] or "0000", -x["count"]), reverse=True)

    # ── review length stats ──────────────────────────────────────────────
    lengths = [len(r["text"]) for r in reviews]
    avg_length = round(sum(lengths) / total, 1)
    short_reviews = sum(1 for l in lengths if l < 20)
    medium_reviews = sum(1 for l in lengths if 20 <= l < 80)
    long_reviews = sum(1 for l in lengths if l >= 80)

    # ── language detection (simple char-set based, no deps) ──────────────
    lang_chars = {"ko": 0, "en": 0, "ja": 0, "zh": 0, "other": 0}
    for r in reviews:
        text = r["text"]
        has_ko = any('\uAC00' <= c <= '\uD7AF' for c in text)
        has_ja = any('\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' for c in text)
        has_zh = any('\u4E00' <= c <= '\u9FFF' for c in text)
        has_en = any(c.isascii() and c.isalpha() for c in text)

        if has_ko:
            lang_chars["ko"] += 1
        elif has_ja:
            lang_chars["ja"] += 1
        elif has_zh:
            lang_chars["zh"] += 1
        elif has_en:
            lang_chars["en"] += 1
        else:
            lang_chars["other"] += 1

    # ── sampling for LLM ─────────────────────────────────────────────────
    # Pick the most valuable reviews for the LLM to read
    reviews_sorted_by_len = sorted(reviews, key=lambda x: len(x["text"]), reverse=True)

    sample_for_llm = {
        "all_1star": [r for r in reviews if r["rating"] == 1],  # LLM must read ALL 1★
        "all_2star": [r for r in reviews if r["rating"] == 2],
        "long_5star": [r for r in reviews_sorted_by_len if r["rating"] >= 4][:15],
        "longest_any": reviews_sorted_by_len[:15],
    }

    return {
        "total_reviews": total,
        "rating_distribution": dict(sorted(rating_counts.items(), reverse=True)),
        "avg_rating": avg_rating,
        "rating_trend_weekly": rating_trend[-12:],
        "rating_trend_monthly": monthly_trend,
        "version_stats": version_stats[:12],
        "review_length": {
            "avg_chars": avg_length,
            "short": short_reviews,
            "medium": medium_reviews,
            "long": long_reviews,
            "histogram": _length_histogram(lengths),
        },
        "language_mix": lang_chars,
        "date_range": {
            "earliest": reviews[-1].get("created_at", "") if reviews else "",
            "latest": reviews[0].get("created_at", "") if reviews else "",
        },
        "sample_for_llm": {
            "count_1star": len(sample_for_llm["all_1star"]),
            "count_2star": len(sample_for_llm["all_2star"]),
            "count_long_5star": len(sample_for_llm["long_5star"]),
            "reviews_1star": sample_for_llm["all_1star"],
            "reviews_2star": sample_for_llm["all_2star"],
            "reviews_long_5star": sample_for_llm["long_5star"],
            "reviews_longest": sample_for_llm["longest_any"],
        },
    }


def _length_histogram(lengths: list[int]) -> dict[str, int]:
    bins = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-120": 0, "120+": 0}
    for l in lengths:
        if l < 20:
            bins["0-20"] += 1
        elif l < 40:
            bins["20-40"] += 1
        elif l < 60:
            bins["40-60"] += 1
        elif l < 80:
            bins["60-80"] += 1
        elif l < 120:
            bins["80-120"] += 1
        else:
            bins["120+"] += 1
    return bins


# ── report generation ───────────────────────────────────────────────────

def print_report(stats: dict) -> str:
    """Generate a markdown stats report that the LLM can read as context."""
    d = stats["rating_distribution"]
    total = stats["total_reviews"]
    star_emoji = {5: "🟢", 4: "🔵", 3: "🟡", 2: "🟠", 1: "🔴"}

    lines = []
    lines.append("## Quantitative Stats Snapshot\n")
    lines.append(f"**Total reviews:** {total} | **Avg rating:** ⭐{stats['avg_rating']}\n")

    # Rating bar chart
    lines.append("### Rating Distribution\n")
    lines.append("| Stars | Count | % | Distribution |")
    lines.append("|-------|-------|---|-------------|")
    for star in range(5, 0, -1):
        cnt = d.get(star, 0)
        pct = round(cnt / total * 100)
        bar = "█" * (pct // 2)
        lines.append(f"| {star}★ | {cnt} | {pct}% | {bar} |")

    # Language mix
    lang = stats["language_mix"]
    if sum(lang.values()) > 0:
        lines.append("\n### Language Mix (char-set detection)\n")
        lines.append("| Lang | Count | % |")
        lines.append("|------|-------|---|")
        for l, cnt in sorted(lang.items(), key=lambda x: -x[1]):
            if cnt > 0:
                lines.append(f"| {l} | {cnt} | {round(cnt/total*100)}% |")

    # Review length
    rl = stats["review_length"]
    lines.append("\n### Review Length\n")
    lines.append(f"- Average: **{rl['avg_chars']} chars**")
    lines.append(f"- Short (<20): {rl['short']} | Medium: {rl['medium']} | Long (80+): {rl['long']}")
    lines.append(f"- Histogram: {rl['histogram']}")

    # Version stats
    vs = stats["version_stats"]
    if vs:
        lines.append("\n### Version Impact\n")
        lines.append("| Version | Reviews | Avg ★ | 1★ | 2★ | 3★ | 4★ | 5★ | First Seen |")
        lines.append("|---------|---------|-------|----|----|----|----|----|------------|")
        for v in vs[:8]:
            spread = v["rating_spread"]
            emoji = "🟢" if v["avg_rating"] >= 4 else ("🟡" if v["avg_rating"] >= 3 else "🔴")
            lines.append(
                f"| {emoji} {v['version'][:15]} | {v['count']} | {v['avg_rating']} | "
                f"{spread['1']} | {spread['2']} | {spread['3']} | {spread['4']} | {spread['5']} | "
                f"{v['first_seen'] or '-'} |"
            )

    # Rating trend
    rt = stats["rating_trend_weekly"]
    if rt:
        lines.append("\n### Rating Trend (weekly)\n")
        lines.append("| Week | Count | Avg ★ | Trend |")
        lines.append("|------|-------|--------|-------|")
        for w in rt:
            bar = "━" * max(1, int(w["avg"] * 2))
            lines.append(f"| {w['period']} | {w['count']} | {w['avg']} | {bar} |")

    # Date range
    dr = stats["date_range"]
    lines.append(f"\n**Date range:** {dr['latest'][:10]} ~ {dr['earliest'][:10]}\n")

    # Sample counts for LLM
    s = stats["sample_for_llm"]
    lines.append("\n### Reviews Ready for LLM Analysis\n")
    lines.append(f"- 🔴 1★ reviews: **{s['count_1star']}** (LLM should read ALL)")
    lines.append(f"- 🟠 2★ reviews: **{s['count_2star']}** (LLM should read ALL)")
    lines.append(f"- 🟢 Long 4-5★ reviews: **{s['count_long_5star']}** (sample)")

    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="blackcow-app-intel stats analyzer")
    parser.add_argument("json_file", help="Scraper JSON output")
    parser.add_argument("-o", "--output", help="Save stats markdown to file")
    parser.add_argument("--json-stats", action="store_true", help="Output JSON stats (for LLM consumption)")
    args = parser.parse_args()

    with open(args.json_file) as f:
        data = json.load(f)

    reviews = data.get("reviews", [])
    if not reviews:
        print("❌ No reviews found", file=sys.stderr)
        sys.exit(1)

    stats = analyze_reviews(reviews)

    if args.json_stats:
        # Output pure JSON for LLM to parse
        out = {k: v for k, v in stats.items() if k != "sample_for_llm"}
        print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    else:
        report = print_report(stats)
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"✅ Stats saved to {args.output}", file=sys.stderr)
        print(report)

    # Always write sample_for_llm as a separate JSON file (for the LLM to read inline)
    if args.output:
        sample_path = args.output.replace(".md", "-samples.json")
        with open(sample_path, "w") as f:
            json.dump(stats["sample_for_llm"], f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ Review samples saved to {sample_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
