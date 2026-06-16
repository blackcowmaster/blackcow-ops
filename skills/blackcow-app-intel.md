---
name: blackcow-app-intel
description: Analyzes scraped app review data into actionable intelligence — user sentiment breakdown, top complaints, praise, feature requests, competitor landscape, and PRD-ready context. Now includes quantitative keyword analysis, rating trends, and version-impact detection. Feeds into blackcow-plan, create-prd, competitor-analysis, and aso-audit skills.
metadata:
  version: 1.2.0
  dependencies:
    - blackcow-app-scraper
    - scripts/app_intel_analyzer.py
---

# blackcow-app-intel

You are an app market intelligence analyst. Your goal is to transform raw review data into structured, actionable insights that feed directly into product planning, ASO audits, competitor analysis, and PRD creation.

## When to Use

Use this skill when the user:
- Wants to understand what users love/hate about a specific app
- Is researching a competitor to build a similar product
- Needs PRD input: "what should I build differently?"
- Asks "what are the weak points of this app?"
- Wants to understand the competitive landscape around an app

## Input

Either:
1. An App Store / Play Store URL (scraping runs automatically via `blackcow-app-scraper`)
2. A previously scraped JSON file from `blackcow-app-scraper`

## Workflow

### Step 1: Get the Data

If the user provides a URL, run the scraper first:
```bash
cd /Users/honeyhead/Project/blackcow-ops
mkdir -p .blackcow/app-scraper
.venv/bin/python scripts/app_scraper.py "<url>" --count 200 > .blackcow/app-scraper/<app-name>.json
```

### Step 2: Run Quantitative Analysis (NEW v1.1)

Run the analyzer script on the scraper JSON:
```bash
.venv/bin/python scripts/app_intel_analyzer.py .blackcow/app-scraper/<app-name>.json \
  --output .blackcow/app-intel/<app-name>-quant.md
```

This produces **objective, numerical evidence** for the LLM's qualitative review:
- **Rating distribution** — polarization detection (e.g. 72% 5★ vs 20% 1★ = review manipulation?)
- **Language mix** — char-set detection (ko/en/ja/zh), no external deps
- **Version impact** — per-version avg rating + 1-5★ spread (e.g. v1.56.3 ⭐2.0 with 1/1/1/0/0 = CRASH)
- **Rating trend (weekly/monthly)** — is the app improving or declining?
- **Review length histogram** — are complaints detailed or just "별로임 ㅡㅡ"?
- **Pre-selected review samples** — all 1★ + all 2★ + long 4-5★ reviews extracted to a separate JSON, ready for the LLM to read and classify sentiment

### Step 3: Read Reviews & Generate Qualitative Report

Read all 1-2★ reviews + a sample of 5★ + the longest reviews. Categorize:

| Category | Signal | Example |
|----------|--------|---------|
| **complaint** | Bug, missing feature, poor UX, unfair pricing | "고객센터 응대가 너무 늦고" |
| **praise** | Love the app, great UX, worth paying | "혼자 가도 커뮤니티로 안 외로움" |
| **feature_request** | "I wish it could...", "add X" | "지방 출발지도 만들어주세요" |
| **bug_report** | Crash, error, not working | "업데이트 하라는데 업데이트 없음" |
| **ux_issue** | Confusing, hard to use, annoying flow | "채팅방 입장이 안돼요" |

**Cross-reference with quantitative findings** — the analyzer says "지방 9회", so CONFIRM that pattern in actual review text.

### Step 4: Generate Final Report

Save to `.blackcow/app-intel/<app-name>.md`. Use this template:

```markdown
# App Intelligence Report: <App Name>

## 1. Executive Summary
(3-5 bullets)

## 2. Quantitative Snapshot (from analyzer)
- Rating: ⭐X.XX | Distribution: [chart]
- Sentiment: 😍 N% / 😡 N% / 💡 N%
- Top complaint keywords: [...]
- Top praise keywords: [...]
- ⚠️ Version alert: (if any version has crashed rating)
- 📉 Trend: (rating direction)

## 3. App Profile
(table with store, rating, installs, developer, category, price)

## 4. User Sentiment Overview
(sentiment table with counts + %)

## 5. Top Complaints (What Users HATE)
(ranked table with severity + quotes + PRD implication)

## 6. Top Praises (What Users LOVE)
(ranked table with quotes + PRD implication)

## 7. Feature Requests & Unmet Needs
(table with feasibility)

## 8. Competitive Landscape
(Similar Apps + Developer Portfolio tables)

## 9. Weakness Map
| Area | Current State | User Pain | Quant Evidence |
|------|---------------|-----------|----------------|
| Regional Coverage | Seoul-only | 🔴 | "지방 9회, 서울 7회" |
| Customer Support | Slow/Kakao only | 🔴 | "문의 6회, 안되 8회" |
| App Performance | Slow/crashing | 🟡 | v1.55.3 ⭐3.67 |
| ... | ... | ... | ... |

## 10. PRD-Ready Takeaways
(5-7 concrete, numbered, actionable points)

## 11. Raw Data
- Scraper: `.blackcow/app-scraper/<app-name>.json`
- Quant: `.blackcow/app-intel/<app-name>-quant.md`
```

### Step 5: Cross-Skill Integration

After generating the report, mention connections:
- `blackcow-plan` → Weakness Map + Feature Requests → roadmap
- `create-prd` → PRD-Ready Takeaways section → spec document
- `aso-audit` → Quantitative Snapshot metadata → ASO score
- `competitor-analysis` → Similar Apps section → competitor inputs
- `keyword-research` → description text → keyword themes

## Notes

- **Always run BOTH the quant analyzer (Step 2) AND qualitative review (Step 3)**
- The quant analyzer catches patterns LLM might miss (version crashes, keyword stats)
- The LLM catches nuance the analyzer misses (sarcasm, context, feature names)
- Developer responses should be treated separately
- Match report language to review language
