# News Dashboard

Daily gaming + tech news dashboard for `@mjeedka_store` — pulls from
official RSS feeds and Reddit, translates and summarizes into Arabic with
accurate categorization, and renders a static HTML page you can open
directly in a browser (no server needed). See `CLAUDE.md` for the pipeline
architecture.

## First-time setup

```bash
cd news-agent
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env
```

Reddit fetching works out of the box with no keys (uses public read-only
endpoints). If you ever hit rate limits, add free OAuth credentials from
https://www.reddit.com/prefs/apps to `.env`.

## Run it manually

```bash
cd news-agent
venv\Scripts\python scripts\run_daily.py
```

Then open `dashboard/index.html` in your browser. This:
1. Fetches new RSS + Reddit items (skips anything already in the archive)
2. If there's anything new, invokes the `news-processor` sub-agent (via
   `claude -p`) to translate, summarize, and categorize it
3. Rebuilds `dashboard/index.html` from the full archive in `data/news.json`

## Edit sources

Add/remove feeds or subreddits in `sources.json`. Each entry needs a
`domain` hint (`gaming` or `tech`) — the sub-agent still makes the final
category call from the actual content, this is just a starting hint.

## Daily automation

Not yet scheduled. To wire it into Windows Task Scheduler once you're happy
with a manual run:
```powershell
schtasks /create /tn "NewsDashboardDaily" /tr "E:\marlette\news-agent\scripts\run_daily.bat" /sc daily /st 07:30
```

## Using the dashboard

- **Search** filters titles, summaries, tags, and source live.
- **Category chips** (الكل / ألعاب / تقنية / تحديثات / مراجعات) filter the feed.
- Items fetched in the last 24 hours show a **جديد** badge.
- **نسخ للنشر** on any card copies a ready-to-post block (title + summary +
  source + link) to your clipboard.
- The full history stays in `data/news.json` forever — nothing is ever
  deleted, so you can always scroll back.
