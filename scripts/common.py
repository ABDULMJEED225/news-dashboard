import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
NEWS_JSON = DATA_DIR / "news.json"
RAW_INCOMING_JSON = DATA_DIR / "raw_incoming.json"
SOURCES_JSON = ROOT / "sources.json"


def make_id(url: str) -> str:
    return hashlib.sha1(url.strip().encode("utf-8")).hexdigest()[:16]


def load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return default
        return json.loads(content)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_sources():
    return load_json(SOURCES_JSON, {"rss": [], "reddit": [], "reddit_min_score": 50})


def existing_ids() -> set:
    archive = load_json(NEWS_JSON, [])
    ids = {item["id"] for item in archive if "id" in item}
    # also skip anything already queued from a run that hasn't been processed yet
    pending = load_json(RAW_INCOMING_JSON, [])
    ids |= {item["id"] for item in pending if "id" in item}
    return ids
