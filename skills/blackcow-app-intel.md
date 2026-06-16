---
name: blackcow-app-intel
description: Analyze scraped app reviews into intelligence — complaints, praise, feature gaps, competitor landscape, PRD-ready context.
---

---
name: blackcow-app-intel
description: Analyzes scraped app review data into actionable intelligence — user sentiment breakdown, top complaints, praise, feature requests, competitor landscape, and PRD-ready context. Feeds into blackcow-plan, create-prd, competitor-analysis, and aso-audit skills.
metadata:
  version: 1.0.0
  dependencies:
    - blackcow-app-scraper
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
.venv/bin/python scripts/app_scraper.py "<url>" --count 200 > .blackcow/app-scraper/<app-name>.json
```

If they provide an existing JSON file, read it directly.

### Step 2: Analyze Reviews

Read through all reviews. Categorize each review into:

| Category | Signal | Example |
|----------|--------|---------|
| **complaint** | Bug, missing feature, poor UX, unfair pricing, too many ads | "광고가 너무 많아요" |
| **praise** | Love the app, great UX, worth paying | "진짜 돈 들어옴 최고" |
| **feature_request** | "I wish it could...", "add X" | "복권 한번에 여러장 긁기 해줘요" |
| **bug_report** | Crash, error, not working | "응모권이 안 쌓여요" |
| **ux_issue** | Confusing, hard to use, annoying flow | "하루 몇번인지 표시좀" |
| **competitor_mention** | Comparing to another app | "캐시워크보다 좋음" |

### Step 3: Generate The Report

Produce a markdown report saved to `.blackcow/app-intel/<app-name>.md` with these sections:

```markdown
# App Intelligence Report: <App Name>

## 1. Executive Summary
(3-5 bullets: what this app does, who it's for, overall user sentiment, key finding)

## 2. App Profile
| Field | Value |
|-------|-------|
| Store | Play Store / App Store |
| Rating | ⭐X.X (N reviews) |
| Installs | XXX |
| Developer | Name |
| Category | Category |
| Price | Free / $X.XX |

## 3. User Sentiment Overview
| Sentiment | Count | % |
|-----------|-------|---|
| 😍 Praise | N | X% |
| 😡 Complaint | N | X% |
| 💡 Feature Request | N | X% |
| 🐛 Bug Report | N | X% |
| 🤔 UX Issue | N | X% |

## 4. Top Complaints (What Users HATE)
(Ranked by frequency + impact)

| # | Issue | Count | Severity | Example Quote |
|---|-------|-------|----------|---------------|
| 1 | ... | N | 🔴High | "..." |
| 2 | ... | N | 🟡Med | "..." |

**Implication for PRD:** (how to avoid these pitfalls when building a similar app)

## 5. Top Praises (What Users LOVE)
| # | Praise | Count | Example Quote |
|---|--------|-------|---------------|
| 1 | ... | N | "..." |

**Implication for PRD:** (what to replicate/improve upon)

## 6. Feature Requests & Unmet Needs
| # | Request | Count | Feasibility |
|---|---------|-------|-------------|
| 1 | ... | N | Easy / Medium / Hard |

**Opportunity:** (what niche/gap this reveals)

## 7. Competitive Landscape

### Similar Apps (from Play Store)
| App | Rating | Installs | Key Differentiator |
|-----|--------|----------|-------------------|
| ... | ⭐X.X | N | ... |

### Developer Portfolio (same developer's other apps)
| App | Rating | Installs |
|-----|--------|----------|
| ... | ⭐X.X | N |

## 8. Weakness Map (앱의 아킬레스건)

| Area | Current State | User Pain Level |
|------|---------------|-----------------|
| Ad Experience | ... | 🔴 / 🟡 / 🟢 |
| Reward Rate | ... | 🔴 / 🟡 / 🟢 |
| Stability/Bugs | ... | 🔴 / 🟡 / 🟢 |
| UX/Clarity | ... | 🔴 / 🟡 / 🟢 |
| Customer Support | ... | 🔴 / 🟡 / 🟢 |
| Payout/Trust | ... | 🔴 / 🟡 / 🟢 |

## 9. PRD-Ready Takeaways
(5-7 concrete, actionable points that can go directly into a PRD)
1. ...
2. ...

## 10. Raw Data
- Scraper output: `.blackcow/app-scraper/<app-name>.json`
- Review count: N
- Date range: YYYY-MM-DD ~ YYYY-MM-DD
```

### Step 4: Cross-Skill Integration

After generating the report, mention how it connects:
- `blackcow-plan` → use Weakness Map + Feature Requests to plan roadmap
- `create-prd` → use PRD-Ready Takeaways section directly
- `aso-audit` → use App Profile metadata to score listing
- `competitor-analysis` → use Similar Apps section as competitor list
- `keyword-research` → use description text to extract keyword themes

## Notes

- Always save outputs to `.blackcow/app-intel/` directory
- The report should be **actionable**, not just descriptive
- When analyzing a competitor for building a similar app, emphasize what to do DIFFERENTLY
- Developer responses in reviews should be noted but treated separately from user sentiment
- The report language should match the language of the reviews (Korean for Korean apps, etc.)
