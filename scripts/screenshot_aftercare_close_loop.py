"""HS-49-03 — screenshot closing the loop (accepted action -> issue proposal).

Boots the real `MeetingWebServer` against a seeded temp DB with an accepted
action item, opens the meeting, and captures (1) the inline "File as issue" form
on the accepted item with its privacy note, and (2) the resulting `proposed`
actuator proposal surfaced in the existing proposals section — awaiting human
approval, nothing executed.

Run via:

    uv run --extra dev --extra meeting python scripts/screenshot_aftercare_close_loop.py
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


def _action(item_id, task, *, owner=None, review_state="pending"):
    return {
        "id": item_id,
        "task": task,
        "owner": owner,
        "due": "Friday",
        "status": "pending",
        "review_state": review_state,
        "source_timestamp": None,
        "created_at": datetime(2026, 6, 5, 10, 0, 0).isoformat(),
    }


def _seed(db_path: Path) -> str:
    reset_database()
    db = get_database(db_path)
    db.meetings.save_meeting(
        MeetingState(
            id="current",
            started_at=datetime(2026, 6, 5, 10, 0, 0),
            title="API design follow-up",
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[
                    _action("c1", "Wire the rate limiter behind a flag", owner="Priya", review_state="accepted"),
                    _action("c2", "Pick a service name"),
                ],
            ),
        )
    )
    return "current"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    meeting_id = _seed(tmp / "loop.db")

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
            page = browser.new_page(viewport={"width": 1280, "height": 1200})
            page.goto(f"{origin}/history", wait_until="networkidle")
            page.wait_for_timeout(900)
            page.evaluate(
                "id => { const el = document.querySelector('[x-data]'); "
                "Alpine.$data(el).openMeeting(id); }",
                meeting_id,
            )
            page.wait_for_selector(".loop-btn", state="visible", timeout=8000)
            page.locator(".loop-btn").first.click()
            page.wait_for_selector(".loop-form", state="visible", timeout=4000)
            page.locator(".loop-input").first.fill("acme/app")
            page.wait_for_timeout(400)
            page.locator(".modal-card").screenshot(
                path=str(OUT_DIR / "story-03-file-issue-form.png")
            )
            print("  ✓ file-issue form → story-03-file-issue-form.png")

            # Create the proposal, then capture it in the proposals section.
            page.evaluate(
                "id => { const el = document.querySelector('[x-data]'); "
                "const app = Alpine.$data(el); "
                "return app.fileActionAsIssue({ id: 'c1' }, 'acme/app'); }",
                meeting_id,
            )
            page.wait_for_timeout(700)
            page.evaluate(
                "() => { const c = document.querySelector('.proposal-card'); "
                "if (c) c.scrollIntoView({ block: 'center' }); }"
            )
            page.wait_for_timeout(500)
            page.locator(".modal-card").screenshot(
                path=str(OUT_DIR / "story-03-proposal-created.png")
            )
            print("  ✓ proposal created → story-03-proposal-created.png")
            browser.close()
    finally:
        uv_server.should_exit = True
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
