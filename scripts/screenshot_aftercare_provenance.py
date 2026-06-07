"""HS-49-02 — screenshot the transcript-provenance jump ("show me the moment").

Boots the real `MeetingWebServer` against a seeded temp DB whose current meeting
has a transcript (segments) and timestamped action items + decisions, so the
aftercare surface shows "Show me the moment" buttons. Captures the panel, then
clicks a moment button and captures the transcript column with the justifying
segment flashed.

Run via:

    uv run --extra dev --extra meeting python scripts/screenshot_aftercare_provenance.py
"""
from __future__ import annotations

import socket
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import uvicorn
from playwright.sync_api import sync_playwright

from holdspeak.db import get_database, reset_database
from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "pm" / "roadmap" / "holdspeak" / "phase-49-meeting-aftercare" / "screenshots"


def _action(item_id, task, *, owner=None, status="pending", source_timestamp=None):
    return {
        "id": item_id,
        "task": task,
        "owner": owner,
        "due": None,
        "status": status,
        "review_state": "pending",
        "source_timestamp": source_timestamp,
        "created_at": datetime(2026, 6, 5, 10, 0, 0).isoformat(),
    }


def _seed(db_path: Path) -> str:
    reset_database()
    db = get_database(db_path)
    segments = [
        TranscriptSegment(text="Let's open the design follow-up.", speaker="Me", start_time=0.0, end_time=12.0),
        TranscriptSegment(text="We're keeping Postgres as the primary store.", speaker="Sam", start_time=12.0, end_time=40.0),
        TranscriptSegment(text="Priya, can you own the rate limiter this week?", speaker="Me", start_time=40.0, end_time=70.0),
        TranscriptSegment(text="Yes — I'll wire it behind the feature flag.", speaker="Priya", start_time=70.0, end_time=128.0),
        TranscriptSegment(text="Good. Let's also pick a service name before we ship.", speaker="Sam", start_time=128.0, end_time=160.0),
    ]
    db.meetings.save_meeting(
        MeetingState(
            id="current",
            started_at=datetime(2026, 6, 5, 10, 0, 0),
            title="API design follow-up",
            segments=segments,
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[
                    _action("c1", "Wire the rate limiter behind a flag", owner="Priya", source_timestamp=72.0),
                    _action("c2", "Pick a service name", owner="Sam", source_timestamp=130.0),
                ],
            ),
        )
    )
    db.plugins.record_artifact(
        artifact_id="current-decisions",
        meeting_id="current",
        artifact_type="decisions",
        title="Decisions",
        structured_json={
            "decisions": [
                {"decision": "Keep Postgres as the primary store", "rationale": "Transactions and team familiarity", "source_timestamp": 14.0},
            ]
        },
        plugin_id="decision_capture",
    )
    return "current"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    meeting_id = _seed(tmp / "provenance.db")

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    port = _free_port()
    config = uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="warning")
    uv_server = uvicorn.Server(config)
    thread = threading.Thread(target=uv_server.run, daemon=True)
    thread.start()

    origin = f"http://127.0.0.1:{port}"
    for _ in range(60):
        if uv_server.started:
            break
        time.sleep(0.25)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1280, "height": 1100})
            page.goto(f"{origin}/history", wait_until="networkidle")
            page.wait_for_timeout(900)
            page.evaluate(
                "id => { const el = document.querySelector('[x-data]'); "
                "Alpine.$data(el).openMeeting(id); }",
                meeting_id,
            )
            page.wait_for_selector(".moment-btn", state="visible", timeout=8000)
            page.wait_for_timeout(500)
            page.locator(".modal-card").screenshot(
                path=str(OUT_DIR / "story-02-provenance-buttons.png")
            )
            print("  ✓ provenance buttons → story-02-provenance-buttons.png")

            # Click the rate-limiter open item's jump (segment at 72.0 → index 3),
            # then capture the flashed segment in the transcript column.
            page.evaluate(
                "() => { const el = document.querySelector('[x-data]'); "
                "Alpine.$data(el).jumpToSegment(3); }"
            )
            page.wait_for_timeout(700)
            page.locator(".modal-card").screenshot(
                path=str(OUT_DIR / "story-02-provenance-jumped.png")
            )
            print("  ✓ jumped + flashed → story-02-provenance-jumped.png")
            browser.close()
    finally:
        uv_server.should_exit = True
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
