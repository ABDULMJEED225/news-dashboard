"""Daily pipeline: fetch -> build dashboard -> publish.

Called by run_daily.bat from Windows Task Scheduler, or directly for a
manual refresh.

Translation is NOT automated here. Invoking the news-processor subagent
via `claude -p` from an unattended script was tried and confirmed
unreliable (it exits 0 without writing anything, silently). Instead,
newly fetched items just accumulate in data/raw_incoming.json, and
translation happens by asking Claude Code to process the backlog during
an interactive session — see CLAUDE.md.
"""
import subprocess

from common import ROOT

import fetch_rss
import fetch_reddit
import build_dashboard


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

    print("[run_daily] building dashboard...")
    build_dashboard.main()

    print("[run_daily] publishing...")
    publish_to_github()

    print("[run_daily] done")


if __name__ == "__main__":
    main()
