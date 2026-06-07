"""HS-49-06 — before/after: artifact-only meeting view vs the aftercare surface.

Boots the real `MeetingWebServer` against a seeded temp DB and captures two
meeting-detail views:

  - before: a meeting with an artifact but nothing open / decided / changed, so
    the aftercare digest is empty and the panel does not render — the pre-Phase-49
    experience (you read an artifact, then go do the work elsewhere).
  - after: a meeting with open items (by owner), decisions, and a since-last diff,
    so the "Your next move" panel sits above the artifacts.

Run via:

    uv run --extra dev --extra meeting python scripts/screenshot_aftercare_before_after.py
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


def _action(item_id, task, *, owner=None, status="pending", due=None, source_timestamp=None):
    return {
        "id": item_id,
        "task": task,
        "owner": owner,
        "due": due,
        "status": status,
        "review_state": "pending",
        "source_timestamp": source_timestamp,
        "created_at": datetime(2026, 6, 5, 10, 0, 0).isoformat(),
    }


def _seed(db_path: Path) -> None:
    reset_database()
    db = get_database(db_path)

    # BEFORE: a lone meeting with a risk_register artifact and nothing open /
    # decided / changed -> aftercare is empty, the panel is hidden.
    db.meetings.save_meeting(
        MeetingState(id="before", started_at=datetime(2026, 6, 1, 9, 0, 0), title="Risk review (artifact only)")
    )
    db.plugins.record_artifact(
        artifact_id="before-risks", meeting_id="before", artifact_type="risk_register",
        title="Risk register", plugin_id="risk_heatmap", confidence=0.8, status="accepted",
        body_markdown=(
            "| Risk | Impact | Likelihood | Mitigation | Owner |\n"
            "|---|---|---|---|---|\n"
            "| Vendor lock-in | High | Medium | Abstract the storage layer | Sam |\n"
            "| Scope creep | Medium | High | Freeze the v1 surface | Priya |"
        ),
        structured_json={"risks": [
            {"risk": "Vendor lock-in", "impact": "High", "likelihood": "Medium", "mitigation": "Abstract the storage layer", "owner": "Sam"},
            {"risk": "Scope creep", "impact": "Medium", "likelihood": "High", "mitigation": "Freeze the v1 surface", "owner": "Priya"},
        ]},
    )

    # AFTER: a prior + current meeting so the panel has open / decided / changed.
    db.meetings.save_meeting(
        MeetingState(
            id="prior",
            started_at=datetime(2026, 6, 2, 9, 0, 0),
            title="API design kickoff",
            intel=IntelSnapshot(timestamp=0.0, action_items=[_action("p1", "Stand up the staging cluster", owner="Priya", status="done")]),
        )
    )
    db.plugins.record_artifact(
        artifact_id="prior-decisions", meeting_id="prior", artifact_type="decisions",
        title="Decisions", plugin_id="decision_capture",
        structured_json={"decisions": [{"decision": "Use Postgres for the primary store"}]},
    )
    db.meetings.save_meeting(
        MeetingState(
            id="after",
            started_at=datetime(2026, 6, 5, 10, 0, 0),
            title="API design follow-up",
            segments=[
                TranscriptSegment(text="Let's open the follow-up.", speaker="Me", start_time=0.0, end_time=60.0),
                TranscriptSegment(text="Priya owns the rate limiter.", speaker="Sam", start_time=60.0, end_time=140.0),
            ],
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[
                    _action("c1", "Wire the rate limiter", owner="Priya", due="Friday", source_timestamp=72.0),
                    _action("c2", "Pick a service name"),
                ],
            ),
        )
    )
    db.plugins.record_artifact(
        artifact_id="after-decisions", meeting_id="after", artifact_type="decisions",
        title="Decisions", plugin_id="decision_capture",
        structured_json={"decisions": [
            {"decision": "Use Postgres for the primary store", "rationale": "Transactions and team familiarity"},
            {"decision": "Adopt feature flags for the rollout", "rationale": "Ship behind a kill switch"},
        ]},
    )


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    _seed(tmp / "beforeafter.db")

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

    def shoot(page, meeting_id, name):
        page.evaluate(
            "id => { const el = document.querySelector('[x-data]'); "
            "Alpine.$data(el).openMeeting(id); }",
            meeting_id,
        )
        page.wait_for_timeout(1000)
        page.locator(".modal-card").screenshot(path=str(OUT_DIR / name))
        print(f"  ✓ {name}")
        page.evaluate("() => { const el = document.querySelector('[x-data]'); Alpine.$data(el).selectedMeeting = null; }")
        page.wait_for_timeout(300)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1280, "height": 1100})
            page.goto(f"{origin}/history", wait_until="networkidle")
            page.wait_for_timeout(900)
            shoot(page, "before", "story-06-before-artifact-only.png")
            shoot(page, "after", "story-06-after-aftercare.png")
            browser.close()
    finally:
        uv_server.should_exit = True
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
