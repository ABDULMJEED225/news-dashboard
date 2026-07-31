"""Pull new items from the RSS feeds listed in sources.json.

Appends genuinely new items (not already in data/news.json or
data/raw_incoming.json) to data/raw_incoming.json for the news-processor
sub-agent to translate/summarize/categorize.
"""
import sys
from datetime import datetime, timedelta, timezone
from time import mktime

import feedparser

from common import RAW_INCOMING_JSON, existing_ids, load_json, load_sources, make_id, save_json

MAX_PER_FEED = 8
MAX_AGE_HOURS = 24


def parse_entry_date(entry):
    for key in ("published_parsed", "updated_parsed"):
        val = getattr(entry, key, None)
        if val:
            return datetime.fromtimestamp(mktime(val), tz=timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


def clean_summary(entry) -> str:
    raw = getattr(entry, "summary", "") or ""
    # crude tag strip — the sub-agent only needs the gist, not clean HTML
    import re

    return re.sub(r"<[^>]+>", " ", raw).strip()[:1200]


def fetch_feed(source: dict, seen_ids: set) -> list:
    items = []
    try:
        parsed = feedparser.parse(source["url"])
    except Exception as e:
        print(f"[rss] FAILED {source['name']}: {e}", file=sys.stderr)
        return items

    cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)

    for entry in parsed.entries[:MAX_PER_FEED]:
        url = getattr(entry, "link", None)
        title = getattr(entry, "title", None)
        if not url or not title:
            continue
        item_id = make_id(url)
        if item_id in seen_ids:
            continue
        published_at = parse_entry_date(entry)
        if datetime.fromisoformat(published_at) < cutoff:
            continue
        seen_ids.add(item_id)
        items.append(
            {
                "id": item_id,
                "url": url,
                "title_original": title.strip(),
                "content_snippet": clean_summary(entry),
                "source": source["name"],
                "source_type": "rss",
                "category_hint": source["domain"],
                "published_at": published_at,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    return items


def main():
    sources = load_sources()
    seen_ids = existing_ids()
    pending = load_json(RAW_INCOMING_JSON, [])

    new_items = []
    for source in sources.get("rss", []):
        found = fetch_feed(source, seen_ids)
        new_items.extend(found)
        print(f"[rss] {source['name']}: {len(found)} new")

    save_json(RAW_INCOMING_JSON, pending + new_items)
    print(f"[rss] total new items this run: {len(new_items)}")


if __name__ == "__main__":
    main()
