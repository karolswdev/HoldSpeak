"""HSM-15-03 — the scratch hub for the mesh-inbox proof.

A REAL MeetingWebServer on loopback, seeded through the real repos with the
inbox's three lanes: a deferred intel job, a queued MIR plugin run, and two
PENDING actuator proposals (a meeting-origin github one + a desk-origin webhook
one). The driving shell points the iPad Simulator at it; when the driver
removes the url file, the hub prints each seeded proposal's final
status/decided_by — the receipt that an approval FROM THE HUD transitioned the
same row the desktop would.
"""
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from holdspeak.db import get_database, reset_database
from holdspeak.meeting_session.models import MeetingState
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/hsm15-inbox-proof")
OUT.mkdir(parents=True, exist_ok=True)
URLFILE = OUT / "hub-url.txt"


def seed(db):
    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="Q3 kickoff", segments=[])
    )
    db.intel.enqueue_intel_job("m1", transcript_hash="h1")
    db.plugins.enqueue_plugin_run_job(
        meeting_id="m1", window_id="w1", plugin_id="risk_register",
        plugin_version="1.0.0", transcript_hash="h1", idempotency_key="pj1",
    )
    github = db.actuators.record_proposal(
        meeting_id="m1", window_id="w1", plugin_id="followup_ticket_actuator",
        plugin_version="1.0.0", idempotency_key="k-github",
        target="github", action="create_issue",
        preview="Open a follow-up issue for the unowned action item",
        payload={"repo": "acme/app", "title": "Follow up"},
    )
    webhook = db.actuators.record_proposal(
        meeting_id=None, origin="desk", window_id="desk", plugin_id="desk_relay",
        plugin_version="1.0.0", idempotency_key="k-webhook",
        target="webhook", action="post_payload",
        preview="Digest → companion webhook",
        payload={"text": "digest"},
    )
    return [github.id, webhook.id]


def main():
    tmp = Path(tempfile.mkdtemp())
    reset_database()
    db = get_database(tmp / "holdspeak.db")
    ids = seed(db)
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        host="127.0.0.1")
    url = server.start()
    URLFILE.write_text(url)
    print(f"hub up at {url}; seeded proposals: {ids}", flush=True)
    try:
        while URLFILE.exists():
            time.sleep(0.5)
    finally:
        for pid in ids:
            p = db.actuators.get_proposal(pid)
            print(f"RESULT {pid}: status={p.status} decided_by={p.decided_by}", flush=True)
        server.stop()
        reset_database()


if __name__ == "__main__":
    main()
