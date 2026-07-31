# News Dashboard — Project Instructions

Daily-refreshed gaming + tech news dashboard for `@mjeedka_store`, aggregated
from official RSS feeds and Reddit, translated and summarized into Arabic,
rendered as a static HTML dashboard.

## Pipeline

1. `scripts/fetch_rss.py` and `scripts/fetch_reddit.py` pull raw items from
   `sources.json` published in the last 24h, dedupe against `data/news.json`
   (by URL hash), and write only genuinely new items to
   `data/raw_incoming.json`.
2. Translation is a **manual, interactive step** — ask Claude Code (in a
   normal chat session) to process the backlog in `data/raw_incoming.json`
   following the rules in `.claude/agents/news-processor.md`: translate
   each item to Arabic, write a smart summary, assign an accurate category,
   and append the result to `data/news.json` — the permanent archive.
   Checkpoint every ~15 items so progress survives interruption.
   (Invoking this via `claude -p ... --allowedTools` from an unattended
   Python subprocess was tried and confirmed broken — it exits 0 without
   writing anything, silently. Don't re-add that automation without solving
   why headless subagent invocation produces no output/effect.)
3. `scripts/build_dashboard.py` reads `data/news.json` and renders
   `dashboard/index.html`, a self-contained static page (no server needed).
4. `scripts/run_daily.py` runs fetch (RSS + Reddit) → build → publish, and
   is what `scripts/run_daily.bat` calls from Windows Task Scheduler. It
   does **not** translate — that backlog just accumulates until the next
   interactive session processes it.

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
