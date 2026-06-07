"""HS-49-01 — screenshot the meeting aftercare digest on the history view.

Boots the real `MeetingWebServer` against a seeded temp DB (so the `/history`
page and the `/api/meetings/{id}/aftercare` endpoint both come from the live
runtime, not a mock), drives a headless browser to open the seeded meeting, and
captures the meeting-detail modal with the aftercare panel ("your next move")
sitting above the artifact dump.

Run via:

    uv run --extra dev --extra meeting python scripts/screenshot_aftercare_digest.py
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
from holdspeak.meeting_session import IntelSnapshot, MeetingState
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
        "created_at": datetime(2026, 6, 4, 10, 0, 0).isoformat(),
    }


def _seed(db_path: Path) -> str:
    reset_database()
    db = get_database(db_path)
    # Prior meeting: a decision + a task since closed, so "since last" has signal.
    db.meetings.save_meeting(
        MeetingState(
            id="prior",
            started_at=datetime(2026, 6, 2, 9, 0, 0),
            title="API design kickoff",
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[
                    _action("p1", "Stand up the staging cluster", owner="Priya", status="done"),
                    _action("p2", "Draft the auth spec", owner="Sam"),
                ],
            ),
        )
    )
    db.plugins.record_artifact(
        artifact_id="prior-decisions",
        meeting_id="prior",
        artifact_type="decisions",
        title="Decisions",
        structured_json={"decisions": [{"decision": "Use Postgres for the primary store"}]},
        plugin_id="decision_capture",
    )
    # Current meeting: open work by owner, two decisions (one new), a new task.
    db.meetings.save_meeting(
        MeetingState(
            id="current",
            started_at=datetime(2026, 6, 5, 10, 0, 0),
            title="API design follow-up",
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[
                    _action("c1", "Draft the auth spec", owner="Sam", source_timestamp=128.0),
                    _action("c2", "Wire the rate limiter", owner="Priya"),
                    _action("c3", "Pick a name for the service"),
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
                {"decision": "Use Postgres for the primary store", "rationale": "Transactions and team familiarity"},
                {"decision": "Adopt feature flags for the rollout", "rationale": "Ship behind a kill switch"},
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
    meeting_id = _seed(tmp / "aftercare.db")

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
            page = browser.new_page(viewport={"width": 1280, "height": 1500})
            page.goto(f"{origin}/history", wait_until="networkidle")
            page.wait_for_timeout(900)
            # Open the seeded meeting via the app's own loader.
            page.evaluate(
                "id => { const el = document.querySelector('[x-data]'); "
                "Alpine.$data(el).openMeeting(id); }",
                meeting_id,
            )
            page.wait_for_selector(".aftercare-card", state="visible", timeout=8000)
            page.wait_for_timeout(700)
            modal = page.query_selector(".modal-card") or page
            out = OUT_DIR / "story-01-aftercare-digest.png"
            modal.screenshot(path=str(out))
            print(f"  ✓ aftercare digest → {out}")
            browser.close()
    finally:
        uv_server.should_exit = True
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
