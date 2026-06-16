#!/usr/bin/env python3
"""blackcow-app-intel analyzer — Quantitative review analysis layer.
Reads a scraper JSON file and produces structured analytics.
Usage:
  .venv/bin/python scripts/app_intel_analyzer.py <.json file> [--lang ko|en]
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any


# ── keyword patterns for Korean reviews ─────────────────────────────────

COMPLAINT_PATTERNS = [
    "오류", "느리", "불편", "안되", "먹통", "꺼짐", "작동", "실행", "충돌",
    "버그", "안돼", "안들어가", "접속", "렉", "렉걸", "로딩", "멈춰", "멈추",
    "취소", "환불", "고객센터", "응대", "문의", "답변", "읽씹", "전화",
    "서울", "수도권", "지방", "출발", "사당", "지역",
    "비싸", "가격", "비용", "돈", "캐시", "포인트", "적립",
    "광고", "업데이트", "권한", "카메라", "토큰", "로그인", "계정",
    "친목", "소외", "대장", "크루", "클럽",
    "쓰레기", "최악", "별로", "망함", "짜증", "화나", "열받", "에바",
    "삭제", "지움", "탈퇴", "접었",
]

PRAISE_PATTERNS = [
    "좋아", "좋고", "좋네", "좋습", "굿", "굳", "최고", "짱", "갑",
    "편리", "편하", "편해", "편함", "유용", "쉽", "쉬워", "간편",
    "감사", "추천", "강추", "굿입니다", "만족",
    "재밌", "즐겁", "행복", "좋은", "멋지", "예쁘",
    "함께", "같이", "인연", "친구", "커뮤니티", "사람", "분들",
    "셔틀", "버스", "안전", "보험", "대장님", "리딩",
    "처음", "입문", "초보", "시작",
]

FEATURE_REQUEST_PATTERNS = [
    "있으면", "해줘", "해주", "추가", "개선", "필요", "원함", "바람",
    "없나", "없어", "아쉽", "아쉬", "부족", "없네", "없음",
    "만들어", "넣어", "됐으면", "했으면", "기능", "좀",
]


# ── analysis functions ──────────────────────────────────────────────────

def analyze_reviews(reviews: list[dict]) -> dict[str, Any]:
    """Run full quantitative analysis on review list."""
    total = len(reviews)
    if total == 0:
        return {"error": "no reviews"}

    # Rating distribution
    rating_counts = Counter(r["rating"] for r in reviews)
    avg_rating = sum(r["rating"] for r in reviews) / total

    # Category classification via keyword matching
    complaint_count = 0
    praise_count = 0
    feature_count = 0
    complaint_keywords = Counter()
    praise_keywords = Counter()

    for r in reviews:
        text = r["text"]
        is_complaint = any(kw in text for kw in COMPLAINT_PATTERNS)
        is_praise = any(kw in text for kw in PRAISE_PATTERNS)
        is_feature = any(kw in text for kw in FEATURE_REQUEST_PATTERNS)

        if is_complaint:
            complaint_count += 1
        if is_praise:
            praise_count += 1
        if is_feature:
            feature_count += 1

        # Count specific keywords
        for kw in COMPLAINT_PATTERNS:
            if kw in text:
                complaint_keywords[kw] += 1
        for kw in PRAISE_PATTERNS:
            if kw in text:
                praise_keywords[kw] += 1

    # Rating trend (by week)
    weeks = defaultdict(list)
    for r in reviews:
        try:
            dt = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
            week_key = dt.strftime("%Y-W%W")
            weeks[week_key].append(r["rating"])
        except (ValueError, KeyError):
            pass

    rating_trend = []
    for wk in sorted(weeks.keys()):
        vals = weeks[wk]
        rating_trend.append({"week": wk, "avg": round(sum(vals) / len(vals), 2), "count": len(vals)})

    # Version analysis
    versions = defaultdict(list)
    for r in reviews:
        v = r.get("app_version", "unknown")
        versions[v].append(r["rating"])

    version_stats = []
    for v, ratings in sorted(versions.items(), key=lambda x: -len(x[1])):
        version_stats.append({
            "version": v,
            "count": len(ratings),
            "avg_rating": round(sum(ratings) / len(ratings), 2),
        })

    # Review length distribution
    lengths = [len(r["text"]) for r in reviews]
    avg_length = sum(lengths) / total
    short_reviews = sum(1 for l in lengths if l < 20)
    medium_reviews = sum(1 for l in lengths if 20 <= l < 80)
    long_reviews = sum(1 for l in lengths if l >= 80)

    # Top keywords
    top_complaints = complaint_keywords.most_common(15)
    top_praises = praise_keywords.most_common(15)

    return {
        "total_reviews": total,
        "rating_distribution": dict(rating_counts),
        "avg_rating": round(avg_rating, 2),
        "sentiment": {
            "complaints": complaint_count,
            "praise": praise_count,
            "feature_requests": feature_count,
            "complaint_pct": round(complaint_count / total * 100, 1),
            "praise_pct": round(praise_count / total * 100, 1),
            "feature_pct": round(feature_count / total * 100, 1),
        },
        "top_complaint_keywords": top_complaints,
        "top_praise_keywords": top_praises,
        "rating_trend_weekly": rating_trend[-12:],  # last 12 weeks
        "version_stats": version_stats[:10],
        "review_length": {
            "avg_chars": round(avg_length, 1),
            "short": short_reviews,
            "medium": medium_reviews,
            "long": long_reviews,
        },
        "high_impact_reviews": [
            {
                "rating": r["rating"],
                "text": r["text"][:200],
                "length": len(r["text"]),
                "date": r.get("created_at", ""),
            }
            for r in sorted(reviews, key=lambda x: len(x["text"]), reverse=True)[:10]
            if len(r["text"]) > 100 and r["rating"] <= 2
        ],
    }


def print_report(stats: dict, lang: str = "ko") -> None:
    """Print a formatted analytics report."""
    if lang == "ko":
        _print_ko(stats)
    else:
        _print_en(stats)


def _print_ko(s: dict) -> None:
    print("=" * 60)
    print("          📊 APP INTEL — 정량 분석 리포트")
    print("=" * 60)
    print()
    print(f"  총 리뷰: {s['total_reviews']}개 | 평균 평점: ⭐{s['avg_rating']}")
    print()

    # Rating distribution
    print("  📈 평점 분포")
    for star in range(5, 0, -1):
        cnt = s["rating_distribution"].get(star, 0)
        pct = round(cnt / s["total_reviews"] * 100)
        bar = "█" * (pct // 2)
        print(f"  {star}★ {bar} {cnt}개 ({pct}%)")
    print()

    # Sentiment
    se = s["sentiment"]
    print("  🎭 감정 분류 (키워드 기반)")
    print(f"  😍 칭찬:   {se['praise']}개 ({se['praise_pct']}%)")
    print(f"  😡 불만:   {se['complaints']}개 ({se['complaint_pct']}%)")
    print(f"  💡 요청:   {se['feature_requests']}개 ({se['feature_pct']}%)")
    print()

    # Top keywords
    print("  🔥 불만 키워드 TOP10")
    for i, (kw, cnt) in enumerate(s["top_complaint_keywords"][:10], 1):
        bar = "▓" * min(cnt, 20)
        print(f"  {i:2}. {kw:<12} {bar} {cnt}")
    print()
    print("  ❤️  칭찬 키워드 TOP10")
    for i, (kw, cnt) in enumerate(s["top_praise_keywords"][:10], 1):
        bar = "▓" * min(cnt, 20)
        print(f"  {i:2}. {kw:<12} {bar} {cnt}")
    print()

    # Rating trend
    if s["rating_trend_weekly"]:
        print("  📅 평점 추이 (주간)")
        for w in s["rating_trend_weekly"]:
            bar = "━" * int(w["avg"] * 2)
            print(f"  {w['week']}  ⭐{w['avg']} {bar} ({w['count']}개)")
        print()

    # Version stats
    if s["version_stats"]:
        print("  📱 버전별 평점")
        for v in s["version_stats"]:
            emoji = "🟢" if v["avg_rating"] >= 4 else ("🟡" if v["avg_rating"] >= 3 else "🔴")
            vlabel = (v['version'] or 'unknown')[:12]
            print(f"  {emoji} v{vlabel:<12} ⭐{v['avg_rating']} ({v['count']}개)")
        print()

    # Review length
    rl = s["review_length"]
    print("  📝 리뷰 길이 분포")
    print(f"  짧음(<20자): {rl['short']}개 | 중간: {rl['medium']}개 | 긴글(80자+): {rl['long']}개")
    print(f"  평균 길이: {rl['avg_chars']}자")
    print()

    # High impact reviews
    if s["high_impact_reviews"]:
        print("  🚨 파급력 높은 부정 리뷰 (길고 낮은 평점)")
        for i, r in enumerate(s["high_impact_reviews"][:5], 1):
            print(f"  [{r['rating']}★] [{r['length']}자] {r['date'][:10]}")
            print(f"  {r['text'][:150]}...")
            print()


def _print_en(s: dict) -> None:
    # English version — similar structure, English labels
    print(f"Total: {s['total_reviews']} reviews | Avg: ⭐{s['avg_rating']}")
    print(f"Complaints: {s['sentiment']['complaint_pct']}% | Praise: {s['sentiment']['praise_pct']}%")
    print(f"Top complaint keywords: {[kw for kw, _ in s['top_complaint_keywords'][:5]]}")
    print(f"Top praise keywords: {[kw for kw, _ in s['top_praise_keywords'][:5]]}")


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="blackcow-app-intel quantitative analyzer")
    parser.add_argument("json_file", help="Path to scraper JSON output")
    parser.add_argument("--lang", default="ko", choices=["ko", "en"])
    parser.add_argument("--output", "-o", help="Save report to file instead of stdout")
    args = parser.parse_args()

    with open(args.json_file) as f:
        data = json.load(f)

    reviews = data.get("reviews", [])
    if not reviews:
        print("❌ No reviews found in JSON", file=sys.stderr)
        sys.exit(1)

    stats = analyze_reviews(reviews)

    import io
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    print_report(stats, args.lang)
    sys.stdout = old_stdout
    output = buf.getvalue()

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"✅ Report saved to {args.output}", file=sys.stderr)
    else:
        print(output)

    # Also print JSON stats on stdout (so LLM can consume it)
    print("\n<!-- QUANT_STATS_JSON", file=sys.stderr)
    json.dump(stats, sys.stderr, indent=2, ensure_ascii=False, default=str)
    print("-->", file=sys.stderr)


if __name__ == "__main__":
    main()
