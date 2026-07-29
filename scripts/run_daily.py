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


BATCH_TIMEOUT_SECONDS = 20 * 60  # a 10-item batch should never legitimately take this long


def run_one_batch():
    """Invoke the news-processor for a single (small, capped) batch.
    Returns the subprocess return code, or None if it had to be killed for
    running past BATCH_TIMEOUT_SECONDS (e.g. stuck waiting on a login
    prompt in a context with no interactive login — this keeps an
    unattended scheduled run from hanging forever)."""
    env = os.environ.copy()
    env["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"] = "0"  # don't give up on a legitimately long batch
    try:
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
            timeout=BATCH_TIMEOUT_SECONDS,
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"[run_daily] news-processor exceeded {BATCH_TIMEOUT_SECONDS}s — killing it "
              f"(likely stuck, e.g. not logged in). Publishing whatever's already checkpointed.")
        return None


def run_processor_and_publish(max_batches=20):
    """Process the queue in small batches (news-processor caps itself at 10
    items/run) and publish after every single batch — so if a usage limit
    or any other error cuts a later batch short, everything translated so
    far is already live on the dashboard, not stuck waiting on the rest."""
    pending = load_json(RAW_INCOMING_JSON, [])
    if not pending:
        print("[run_daily] no new items — skipping news-processor")
        return

    for i in range(max_batches):
        pending = load_json(RAW_INCOMING_JSON, [])
        if not pending:
            print("[run_daily] queue fully drained")
            break

        before = len(pending)
        print(f"[run_daily] batch {i + 1}: {before} items pending — invoking news-processor")
        code = run_one_batch()

        print("[run_daily] building dashboard...")
        build_dashboard.main()
        print("[run_daily] publishing...")
        publish_to_github()

        if code != 0:
            print(f"[run_daily] news-processor stopped (exit {code}) — likely a usage limit. "
                  f"Progress so far is published; next run resumes automatically.")
            break

        after = len(load_json(RAW_INCOMING_JSON, []))
        if after >= before:
            print("[run_daily] no progress made this batch — stopping to avoid looping forever")
            break


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

    run_processor_and_publish()

    print("[run_daily] done")


if __name__ == "__main__":
    main()
