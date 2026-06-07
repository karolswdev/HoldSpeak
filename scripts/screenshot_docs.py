#!/usr/bin/env python3
"""HS-46-04: capture the documentation screenshot set, reproducibly.

Boots one real `MeetingWebServer` backed by a temp DB seeded with realistic
state (a dictation journal + a meeting with synthesized artifacts), drives the
marquee surfaces with Playwright, and writes a known set of PNGs to
`docs/assets/screenshots/`:

    welcome.png  — the first-run /welcome wizard
    journal.png  — the dictation Journal (said -> typed -> routed -> latency)
    history.png  — a saved meeting's elevated artifact cards at /history

No microphone and no LLM endpoint are required — every surface is driven from
seeded state and the dry-run/journal data. Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python scripts/screenshot_docs.py            # all three
    .venv/bin/python scripts/screenshot_docs.py welcome    # one surface

The seeded DB is the global singleton so the `/history` routes (which call
`get_database()`) see it; the journal repo is also injected into the server.
"""
from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

OUT_DIR = Path(__file__).parent.parent / "docs" / "assets" / "screenshots"
MEETING_ID = "docs-demo-meeting"


def _seed_journal(db) -> None:
    """A few realistic dictation rows: spoken + dry-run, varied routing, one
    corrected — the same kind of data the journal records live."""
    j = db.dictation_journal
    j.record(
        source="dictation",
        transcript="ok so add idempotency to the charge endpoint so retries don't double-post",
        final_text=(
            "Implement idempotency for the POST /charges endpoint: persist the "
            "Idempotency-Key and, on a repeat key, return the original response "
            "instead of posting a second ledger entry. Add a retry test."
        ),
        intent="agent_task",
        block_id="agent_task_buildout",
        target_profile="claude_code",
        project_root="/work/ledgerline",
        stage_ms={"intent-router": 379.0, "kb-enricher": 1.0, "project-rewriter": 1582.0},
        total_ms=1962.0,
        rewrite_pass_ms=[527.0, 528.0],
        confidence=0.86,
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
        transcript="route this to the deploy block and run the smoke suite",
        final_text="Deploy the current branch to staging and run the smoke suite.",
        intent="deploy",
        block_id="deploy_ops",
        target_profile="terminal",
        stage_ms={"intent-router": 198.0, "kb-enricher": 1.0},
        total_ms=199.0,
        confidence=0.79,
        warnings=[],
        retention=500,
    )
    # One corrected row, so the "taught" state is visible.
    try:
        db.dictation_journal.mark_corrected(rec, correction_id="demo-correction")
    except Exception:
        pass


def _seed_meeting(db) -> None:
    """A saved meeting with three synthesized artifacts, in the structured_json
    shapes the /history elevated cards render (requirements / decisions /
    risk register)."""
    from holdspeak.meeting_session import Bookmark, MeetingState, TranscriptSegment

    state = MeetingState(
        id=MEETING_ID,
        started_at=datetime(2026, 6, 4, 10, 0, 0),
        ended_at=datetime(2026, 6, 4, 10, 47, 0),
        title="Payments platform — architecture sync",
        tags=["architecture", "payments"],
        segments=[
            TranscriptSegment(
                text="We need the charge endpoint to be idempotent before launch.",
                speaker="Me",
                start_time=12.0,
                end_time=16.0,
            ),
            TranscriptSegment(
                text="Agreed. The risk is double-posting on a client retry storm.",
                speaker="Priya",
                start_time=17.0,
                end_time=22.0,
            ),
            TranscriptSegment(
                text="Let's require an Idempotency-Key header and dedupe server-side.",
                speaker="Me",
                start_time=23.0,
                end_time=28.0,
            ),
        ],
        bookmarks=[Bookmark(timestamp=23.0, label="Idempotency decision")],
        mic_label="Me",
        remote_label="Priya",
    )
    db.meetings.save_meeting(state)

    db.plugins.record_artifact(
        artifact_id=f"{MEETING_ID}-requirements",
        meeting_id=MEETING_ID,
        artifact_type="requirements",
        title="Requirements",
        body_markdown="Extracted requirements for the payments launch.",
        structured_json={
            "requirements": [
                {"text": "The POST /charges endpoint MUST be idempotent per Idempotency-Key.", "type": "functional"},
                {"text": "A repeated key MUST return the original response, not a new charge.", "type": "acceptance"},
                {"text": "Dedupe MUST hold under a client retry storm (≥100 rps burst).", "type": "non_functional"},
                {"text": "Keys are scoped per merchant account.", "type": "constraint"},
            ]
        },
        confidence=0.84,
        status="needs_review",
        plugin_id="requirements_extractor",
        plugin_version="1.0.0",
    )
    db.plugins.record_artifact(
        artifact_id=f"{MEETING_ID}-decisions",
        meeting_id=MEETING_ID,
        artifact_type="decisions",
        title="Decisions & open questions",
        body_markdown="Decisions captured from the sync.",
        structured_json={
            "decisions": [
                {
                    "decision": "Require an Idempotency-Key header on POST /charges and dedupe server-side.",
                    "rationale": "Prevents double-posting on client retries without a distributed lock.",
                },
                {
                    "decision": "Persist keys for 24h, then expire.",
                    "rationale": "Bounds storage while covering realistic retry windows.",
                },
            ],
            "open_questions": [
                "Do we backfill idempotency for the legacy /v1/charge route, or only v2?",
                "What's the response when a key is reused with a different body — 409 or replay?",
            ],
        },
        confidence=0.8,
        status="needs_review",
        plugin_id="decision_capture",
        plugin_version="1.0.0",
    )
    db.plugins.record_artifact(
        artifact_id=f"{MEETING_ID}-risks",
        meeting_id=MEETING_ID,
        artifact_type="risk_register",
        title="Risk register",
        body_markdown="Risks surfaced during the sync.",
        structured_json={
            "risks": [
                {
                    "risk": "Retry storm double-posts charges before idempotency ships.",
                    "impact": "high",
                    "likelihood": "medium",
                    "mitigation": "Gate launch on the Idempotency-Key requirement.",
                    "owner": "Priya",
                },
                {
                    "risk": "Key store becomes a hot path under burst load.",
                    "impact": "medium",
                    "likelihood": "medium",
                    "mitigation": "Benchmark the dedupe lookup; cache per merchant.",
                    "owner": "Me",
                },
            ]
        },
        confidence=0.77,
        status="needs_review",
        plugin_id="risk_heatmap",
        plugin_version="1.0.0",
    )


def _build_server(db):
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    return MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        ),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )


def _capture_welcome(page, url, out: Path) -> None:
    page.set_viewport_size({"width": 1280, "height": 860})
    page.goto(f"{url}/welcome", wait_until="networkidle")
    page.wait_for_timeout(700)
    page.screenshot(path=str(out / "welcome.png"))


def _capture_journal(page, url, out: Path) -> None:
    page.set_viewport_size({"width": 1280, "height": 1500})
    page.goto(f"{url}/dictation", wait_until="networkidle")
    page.click('.scope-row button[data-section="journal"]')
    page.wait_for_selector(".journal-card", state="visible")
    page.wait_for_timeout(400)
    page.screenshot(path=str(out / "journal.png"), full_page=True)


def _capture_history(page, url, out: Path) -> None:
    page.set_viewport_size({"width": 1280, "height": 1700})
    page.goto(f"{url}/history", wait_until="networkidle")
    page.wait_for_selector(".meeting-card", state="visible")
    page.click(".meeting-card")
    # The detail panel renders the elevated artifact cards.
    page.wait_for_selector(".artifact-card__title", state="visible")
    page.wait_for_timeout(500)
    page.screenshot(path=str(out / "history.png"), full_page=True)


CAPTURES = {
    "welcome": _capture_welcome,
    "journal": _capture_journal,
    "history": _capture_history,
}


def main(argv: list[str]) -> int:
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import get_database, reset_database

    wanted = [a for a in argv if a in CAPTURES] or list(CAPTURES)

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    # Make the seeded DB the global singleton so /history's get_database() uses it.
    db = get_database(tmp / "docs.db")
    _seed_journal(db)
    _seed_meeting(db)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    server = _build_server(db)
    url = server.start()
    time.sleep(1.0)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            for name in wanted:
                CAPTURES[name](page, url, OUT_DIR)
                print(f"Wrote {OUT_DIR / (name + '.png')}")
            browser.close()
    finally:
        server.stop()
        reset_database()

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
