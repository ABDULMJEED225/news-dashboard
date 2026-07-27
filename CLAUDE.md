# News Dashboard — Project Instructions

Daily-refreshed gaming + tech news dashboard for `@mjeedka_store`, aggregated
from official RSS feeds and Reddit, translated and summarized into Arabic,
rendered as a static HTML dashboard.

## Pipeline

1. `scripts/fetch_rss.py` and `scripts/fetch_reddit.py` pull raw items from
   `sources.json`, dedupe against `data/news.json` (by URL hash), and write
   only genuinely new items to `data/raw_incoming.json`.
2. The `news-processor` sub-agent (`.claude/agents/news-processor.md`) reads
   `data/raw_incoming.json`, translates each item to Arabic, writes a smart
   summary, assigns an accurate category, and appends the result to
   `data/news.json` — the permanent archive.
3. `scripts/build_dashboard.py` reads `data/news.json` and renders
   `dashboard/index.html`, a self-contained static page (no server needed).
4. `scripts/run_daily.py` runs all of the above in order and is what
   `scripts/run_daily.bat` calls from Windows Task Scheduler.

## Data contract

- `data/news.json` is the single source of truth and an append-only archive
  — never delete or rewrite past entries, only add new ones.
- `data/raw_incoming.json` is scratch space for one run: input to the
  sub-agent, safe to overwrite each run.
- The sub-agent must never fabricate a translation, summary, or category —
  if `raw_incoming.json` is missing or empty, it does nothing.
- The dashboard (`scripts/build_dashboard.py`) only reads `data/news.json`
  — it never calls any API directly.

## Secrets

All secrets live in `.env` (Reddit OAuth, Telegram). Never hardcode a token
in any script.
