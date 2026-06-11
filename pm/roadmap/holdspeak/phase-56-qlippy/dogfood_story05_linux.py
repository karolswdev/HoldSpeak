#!/usr/bin/env python3
"""HS-56-05 dogfood (Linux): the GTK overlay hosts a clickable card on real X11.

Runs ON the Linux box (a real Xorg session — proven on 192.168.1.43, GNOME on
X11). No mocks in the chain: the REAL production wiring
(`build_desktop_presence_host` → `FreedesktopPresenceRenderer` → the GTK
WebKit overlay child process showing the real `/presence` page) is driven
with real activity; a real aftercare proposal's real broadcast slides the
Qlippy card out inside the overlay; the 0.4 s card poll grows the window and
opens its input shape; a REAL `xdotool` click (sent by the orchestrator over
SSH) on the overlay's Approve button records the audited decision.

Protocol with the orchestrator (the Mac):
  - prints `READY url=<url>` once the overlay is up,
  - waits for `/tmp/hs5605.fire` to exist before filing the proposal (so the
    orchestrator's geometry-oracle page can connect first),
  - prints `PROPOSAL=<id>` after filing,
  - then waits up to 90 s for the proposal to leave `proposed` (the click).

Orchestrate from the dev Mac:

    rsync the tree; then run the SSH/xdotool sequence in evidence-story-05.md
"""
from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

FIRE = Path("/tmp/hs5605.fire")
PORT = 8765


def _seed_meeting(db, meeting_id):
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    started = datetime(2026, 6, 10, 10, 0, 0)
    state = MeetingState(
        id=meeting_id,
        started_at=started,
        ended_at=datetime(2026, 6, 10, 11, 0, 0),
        title="Linux HUD dogfood",
        segments=[TranscriptSegment(text="fix the flaky login test", speaker="Me", start_time=0.0, end_time=10.0)],
    )
    state.intel = IntelSnapshot(
        timestamp=60.0,
        topics=[],
        action_items=[{
            "id": "a1", "task": "Fix the flaky login test", "owner": "Me",
            "due": None, "status": "pending", "review_state": "accepted",
            "source_timestamp": None, "created_at": started.isoformat(),
        }],
        summary="",
    )
    db.meetings.save_meeting(state)


def main() -> int:
    import httpx

    import holdspeak.config as config_module
    from holdspeak.db import get_database, reset_database
    from holdspeak.desktop_presence import build_desktop_presence_host
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    if FIRE.exists():
        FIRE.unlink()
    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = get_database(tmp / "dogfood.db")
    _seed_meeting(db, "m-hud-linux")

    # Loopback only (the server rightly refuses non-loopback without an auth
    # token); the orchestrator's geometry oracle reaches it over an SSH tunnel.
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        port=PORT,
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    failures: list[str] = []
    host = None
    try:
        httpx.put(
            f"http://127.0.0.1:{PORT}/api/settings",
            json={"presence": {"enabled": True, "mascot": True}},
            timeout=10,
        )

        # The REAL production wiring: config-enabled host → freedesktop
        # renderer → GTK WebKit overlay (overlay-capable: real Xorg).
        host = build_desktop_presence_host(
            url_provider=lambda: f"http://127.0.0.1:{PORT}", config_enabled=True
        )
        if host is None:
            print("FAIL  no native renderer selected on this box")
            print("RESULT: FAIL")
            return 1
        host.handle_activity({"state": "listening", "label": "Listening", "detail": "dogfood"})
        time.sleep(8.0)  # overlay child + webview load
        print(f"READY url={url}", flush=True)

        # Wait for the orchestrator's oracle page to connect, then file the
        # REAL proposal — one broadcast, every connected webview gets it.
        deadline = time.time() + 60
        while not FIRE.exists() and time.time() < deadline:
            time.sleep(0.2)
        if not FIRE.exists():
            failures.append("orchestrator never fired")
        else:
            filed = httpx.post(
                f"http://127.0.0.1:{PORT}/api/meetings/m-hud-linux/aftercare/file-issue",
                json={"action_item_id": "a1", "repo": "acme/widgets"},
                timeout=10,
            ).json()
            proposal_id = filed["proposal"]["id"]
            print(f"PROPOSAL={proposal_id}", flush=True)

            # The overlay's 0.4 s poll grows the frame; the orchestrator
            # clicks Approve with xdotool. Wait for the decision to land.
            decided = None
            deadline = time.time() + 90
            while time.time() < deadline:
                stored = db.actuators.get_proposal(proposal_id)
                if stored.status != "proposed":
                    decided = stored
                    break
                time.sleep(0.5)
            if decided is None:
                failures.append("the native click never landed (still proposed)")
            elif decided.status == "approved" and decided.decided_by:
                print(
                    f"PASS  a REAL xdotool click on the overlay's Approve recorded the audited "
                    f"decision (status={decided.status}, by={decided.decided_by!r}) — no side effect",
                    flush=True,
                )
            else:
                failures.append(f"unexpected decision state: {decided.status}")
            time.sleep(10.0)  # let the card resolve + the frame return to passive (observable)
    finally:
        if host is not None:
            host.close()
        server.stop()
        reset_database()
        if FIRE.exists():
            FIRE.unlink()

    if failures:
        for f in failures:
            print(f"FAIL  {f}")
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
