#!/usr/bin/env python3
"""HS-62-03 (remote half, runs ON 192.168.1.43's real Xorg session): host the
real GTK overlay with a decision card showing the egress badge, so the
orchestrating Mac can photograph the native frame for the docs.

Boots the loopback server + the REAL production presence wiring, seeds a
meeting, files a real GitHub-issue proposal (its broadcast slides the card
out inside the overlay), prints READY/PROPOSAL, then holds for 60 s while
the orchestrator crops the X11 root window.
"""
from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PORT = 8765


def main() -> int:
    import httpx

    import holdspeak.config as config_module
    from holdspeak.db import get_database, reset_database
    from holdspeak.desktop_presence import build_desktop_presence_host
    from holdspeak.meeting_session import IntelSnapshot, MeetingState
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = get_database(tmp / "dogfood.db")

    started = datetime(2026, 6, 12, 10, 0, 0)
    state = MeetingState(
        id="m-badge",
        started_at=started,
        ended_at=datetime(2026, 6, 12, 11, 0, 0),
        title="Quiet trust dogfood",
    )
    state.intel = IntelSnapshot(
        timestamp=60.0,
        action_items=[{
            "id": "a1", "task": "Fix the flaky login test", "owner": "Me",
            "due": None, "status": "pending", "review_state": "accepted",
            "source_timestamp": None, "created_at": started.isoformat(),
        }],
    )
    db.meetings.save_meeting(state)

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        port=PORT,
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    host = None
    try:
        httpx.put(
            f"http://127.0.0.1:{PORT}/api/settings",
            json={"presence": {"enabled": True, "mascot": True}},
            timeout=10,
        )
        host = build_desktop_presence_host(
            url_provider=lambda: f"http://127.0.0.1:{PORT}", config_enabled=True
        )
        if host is None:
            print("FAIL no native renderer", flush=True)
            return 1
        host.handle_activity({"state": "listening", "label": "Listening", "detail": "dogfood"})
        time.sleep(8.0)  # overlay child + webview load
        print(f"READY url={url}", flush=True)

        time.sleep(3.0)
        filed = httpx.post(
            f"http://127.0.0.1:{PORT}/api/meetings/m-badge/aftercare/file-issue",
            json={"action_item_id": "a1", "repo": "acme/widgets"},
            timeout=10,
        ).json()
        print(f"PROPOSAL={filed['proposal']['id']}", flush=True)

        time.sleep(60.0)  # hold for the orchestrator's screenshot
        print("RESULT: PASS", flush=True)
        return 0
    finally:
        if host is not None:
            host.close()
        server.stop()
        reset_database()


if __name__ == "__main__":
    raise SystemExit(main())
