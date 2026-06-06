#!/usr/bin/env python3
"""Capture a screenshot of the Phase-45 dictation Journal (HS-45-02).

Starts a real MeetingWebServer backed by a temp DB seeded with a few realistic
journal rows (spoken + dry-run, varied routing/latency, one corrected), drives
the `/dictation` Journal tab with Playwright, and writes a PNG. Run after
`cd web && npm run build`:

    .venv/bin/python scripts/screenshot_journal.py <out.png>
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


def _seed(db) -> None:
    j = db.dictation_journal
    j.record(
        source="dictation",
        transcript="ok so add idempotency to the charge endpoint so retries don't double-post",
        final_text=(
            "Implement idempotency for the POST /charges endpoint: persist the "
            "Idempotency-Key, and on a repeat key return the original response "
            "instead of posting a second ledger entry. Add a retry test."
        ),
        intent="agent_task",
        block_id="agent_task_buildout",
        target_profile="claude_code",
        project_root="/work/ledgerline",
        stage_ms={"intent-router": 3791.0, "kb-enricher": 1.0, "project-rewriter": 15825.0},
        total_ms=19616.0,
        rewrite_pass_ms=[5269.0, 5284.0],
        confidence=0.85,
        warnings=[],
        retention=500,
    )
    j.record(
        source="dry_run",
        transcript="remind me to follow up with the vendor about the SLA next week",
        final_text="Remind me to follow up with the vendor about the SLA next week.",
        intent="note",
        block_id="quick_note",
        target_profile="notes",
        stage_ms={"intent-router": 240.0, "kb-enricher": 2.0},
        total_ms=242.0,
        confidence=0.71,
        warnings=["intent-router: confidence below the strong-match threshold"],
        retention=500,
    )
    rec = j.record(
        source="dictation",
        transcript="route this to the deploy block",
        final_text="Deploy the current branch to staging and run the smoke suite.",
        intent="deploy",
        block_id="deploy_runbook",
        target_profile="terminal",
        stage_ms={"intent-router": 410.0, "project-rewriter": 2980.0},
        total_ms=3390.0,
        rewrite_pass_ms=[2980.0],
        confidence=0.62,
        retention=500,
    )
    j.mark_corrected(rec.id, correction_id=1)


def main(out_path: str) -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import Database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = Database(tmp / "journal.db")
    _seed(db)

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        ),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 1500})
            page.goto(f"{url}/dictation", wait_until="networkidle")
            page.click('.scope-row button[data-section="journal"]')
            page.wait_for_selector(".journal-card", state="visible")
            page.wait_for_timeout(400)
            page.screenshot(path=out_path, full_page=True)
            browser.close()
    finally:
        server.stop()

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "journal.png"
    raise SystemExit(main(out))
