"""Full daily pipeline: fetch -> translate/summarize/categorize -> build dashboard.

Called by run_daily.bat from Windows Task Scheduler, or directly for a
manual refresh.
"""
import os
import subprocess
import sys

from common import RAW_INCOMING_JSON, ROOT, load_json

import fetch_rss
import fetch_reddit
import build_dashboard


def run_processor_subagent():
    pending = load_json(RAW_INCOMING_JSON, [])
    if not pending:
        print("[run_daily] no new items — skipping news-processor")
        return

    print(f"[run_daily] {len(pending)} new items — invoking news-processor sub-agent")
    env = os.environ.copy()
    env["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"] = "0"  # never give up early — wait until it's actually done
    result = subprocess.run(
        [
            "claude",
            "-p",
            "Use the news-processor subagent to translate, summarize, and "
            "categorize the new items in data/raw_incoming.json, then "
            "append them to data/news.json.",
            "--allowedTools",
            "Read Write",
        ],
        cwd=str(ROOT),
        env=env,
        shell=(sys.platform == "win32"),
    )
    if result.returncode != 0:
        print(f"[run_daily] WARNING: news-processor exited with code {result.returncode}")


def publish_to_github():
    """Commit + push docs/index.html so the public GitHub Pages URL updates.
    No-ops quietly if this repo has no git remote configured yet."""
    remote = subprocess.run(
        ["git", "remote"], cwd=str(ROOT), capture_output=True, text=True
    )
    if not remote.stdout.strip():
        print("[run_daily] no git remote configured — skipping publish")
        return

    subprocess.run(["git", "add", "docs/index.html", "data/news.json"], cwd=str(ROOT))
    commit = subprocess.run(
        ["git", "commit", "-m", "Daily news update"], cwd=str(ROOT), capture_output=True, text=True
    )
    if commit.returncode != 0:
        print("[run_daily] nothing new to publish")
        return

    push = subprocess.run(["git", "push"], cwd=str(ROOT), capture_output=True, text=True)
    if push.returncode != 0:
        print(f"[run_daily] WARNING: git push failed: {push.stderr}")
    else:
        print("[run_daily] published to GitHub Pages")


def main():
    print("[run_daily] fetching RSS...")
    fetch_rss.main()

    print("[run_daily] fetching Reddit...")
    fetch_reddit.main()

    run_processor_subagent()

    print("[run_daily] building dashboard...")
    build_dashboard.main()

    print("[run_daily] publishing...")
    publish_to_github()

    print("[run_daily] done")


if __name__ == "__main__":
    main()
