"""Pull new posts from the subreddits listed in sources.json.

Uses Reddit's public read-only JSON endpoints (no auth required). If
REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET are set in .env, switches to OAuth
app-only auth instead, which has much higher rate limits.

Appends genuinely new items to data/raw_incoming.json, same contract as
fetch_rss.py.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

from common import RAW_INCOMING_JSON, existing_ids, load_json, load_sources, make_id, save_json

load_dotenv()

USER_AGENT = "news-agent/1.0 (Windows; personal use dashboard)"
MAX_AGE_HOURS = 24


def get_oauth_token():
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    try:
        resp = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        print(f"[reddit] OAuth failed, falling back to public JSON: {e}", file=sys.stderr)
        return None


def fetch_subreddit(source: dict, token, min_score: int, seen_ids: set) -> list:
    sub = source["subreddit"]
    listing = source.get("listing", "hot")
    limit = source.get("limit", 10)

    if token:
        url = f"https://oauth.reddit.com/r/{sub}/{listing}"
        headers = {"User-Agent": USER_AGENT, "Authorization": f"Bearer {token}"}
    else:
        url = f"https://www.reddit.com/r/{sub}/{listing}.json"
        headers = {"User-Agent": USER_AGENT}

    items = []
    try:
        resp = requests.get(url, headers=headers, params={"limit": limit}, timeout=15)
        resp.raise_for_status()
        children = resp.json()["data"]["children"]
    except Exception as e:
        print(f"[reddit] FAILED {source['name']}: {e}", file=sys.stderr)
        return items

    cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)

    for child in children:
        post = child.get("data", {})
        if post.get("stickied"):
            continue
        if post.get("score", 0) < min_score:
            continue
        permalink = post.get("permalink")
        title = post.get("title")
        if not permalink or not title:
            continue
        published_at = datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc)
        if published_at < cutoff:
            continue
        url_full = f"https://www.reddit.com{permalink}"
        item_id = make_id(url_full)
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)
        external_link = post.get("url_overridden_by_dest") or ""
        snippet = post.get("selftext", "")[:1200] or external_link
        items.append(
            {
                "id": item_id,
                "url": url_full,
                "title_original": title.strip(),
                "content_snippet": snippet,
                "source": source["name"],
                "source_type": "reddit",
                "category_hint": source["domain"],
                "published_at": published_at.isoformat(),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
            }
        )
    return items


def main():
    sources = load_sources()
    min_score = sources.get("reddit_min_score", 50)
    seen_ids = existing_ids()
    pending = load_json(RAW_INCOMING_JSON, [])
    token = get_oauth_token()

    new_items = []
    for source in sources.get("reddit", []):
        found = fetch_subreddit(source, token, min_score, seen_ids)
        new_items.extend(found)
        print(f"[reddit] {source['name']}: {len(found)} new")

    save_json(RAW_INCOMING_JSON, pending + new_items)
    print(f"[reddit] total new items this run: {len(new_items)}")


if __name__ == "__main__":
    main()
