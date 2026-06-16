---
name: blackcow-app-scraper
description: Extract app reviews + metadata from App Store / Google Play Store URLs using Python libraries — no MCP, no API keys.
---

---
name: blackcow-app-scraper
description: Extract app reviews + metadata from App Store / Google Play Store URLs. Uses gplay-scraper (Play Store) and app-reviews (App Store) Python libraries — no MCP required, no API keys needed. Returns structured JSON with metadata, reviews, similar apps, and developer portfolio.
metadata:
  version: 1.0.0
  requires:
    - python3.14 (Homebrew)
    - .venv with gplay-scraper, app-reviews
  script: scripts/app_scraper.py
---

# blackcow-app-scraper

You are a review scraping specialist. Your goal is to extract structured review data and app metadata from App Store and Google Play Store.

## When to Use

Use this skill when the user:
- Shares an App Store or Play Store URL and wants reviews extracted
- Asks "what are users saying about this app?"
- Needs structured review data for analysis
- Wants competitor app intelligence (metadata + similar apps)

## How It Works

1. Parse the URL to determine store type (App Store / Play Store)
2. Run `scripts/app_scraper.py` with the URL and desired count
3. Returns structured JSON with:
   - `metadata` — title, developer, rating, installs, description, version, screenshots
   - `reviews` — id, rating, author, text, thumbs_up, version, date (sorted newest)
   - `similar_apps` — competitor apps from Play Store (Play Store only)
   - `developer_apps` — other apps by same developer (Play Store only)

## Usage

```bash
cd /Users/honeyhead/Project/blackcow-ops
.venv/bin/python scripts/app_scraper.py "<app-url>" --count 100 --format json
```

**Arguments:**
- `url` — App Store URL (`apps.apple.com/.../id123456`) or Play Store URL (`play.google.com/...?id=com.example&hl=ko`), or bare ID/package name
- `--count` — number of reviews (default 200, max ~500 for Play Store, 500 for App Store)
- `--format` — `json` (default) or `csv`

## Output Format

Save the output JSON to the project directory for other skills to consume:

```
Output saved to: .blackcow/app-scraper/<app-name>.json
```

## What You Get

| Field | Description |
|------|-------------|
| metadata.title | App name |
| metadata.rating | Average rating |
| metadata.rating_count | Total ratings count |
| metadata.installs | Install range (Play Store) |
| metadata.description | Full description |
| metadata.screenshots | Array of screenshot URLs |
| reviews[].rating | 1-5 star rating |
| reviews[].text | Review content |
| reviews[].created_at | ISO datetime |
| reviews[].app_version | Version at time of review |
| similar_apps[] | Related apps by Play Store algorithm |

## Notes

- No API keys or authentication required
- Play Store: ~500 review limit via gplay-scraper
- App Store: 500 review limit via RSS feed
- Developer responses are NOT included (they're separate in the Play Store data model)
- Use `blackcow-app-intel` skill for analysis of scraped data
