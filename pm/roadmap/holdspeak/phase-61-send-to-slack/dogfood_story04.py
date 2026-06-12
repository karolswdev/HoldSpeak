#!/usr/bin/env python3
"""HS-61-04 closeout dogfood: the REAL POST, end to end, no mocks anywhere.

A real local incoming-webhook-shaped receiver (stdlib HTTP server answering
200 "ok" like Slack does) listens on loopback. A real browser drives the real
UI: open the meeting, click Send to Slack, then click Approve on the proposal
card. The real decision route runs the real `build_slack_connector` over the
real gated-connector stack, and the real urllib transport POSTs to the
receiver. Asserted on the wire:

  1. NOTHING is received before the approval click (never egress unapproved);
  2. exactly ONE POST arrives after it, body byte-equal to the stored
     proposal preview (`{"text": <preview>}`);
  3. the live wrong-host probe: a connector whose manifest allows only
     127.0.0.1, handed a proposal pointing at another host, refuses BEFORE
     any socket opens (real transport, no fake client);
  4. the off-proof: with the URL cleared, the export route refuses with 400.

Run after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-61-send-to-slack/dogfood_story04.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

OUT_DIR = Path(__file__).resolve().parent / "screenshots"

RECEIVED: list[dict] = []


class _WebhookReceiver(BaseHTTPRequestHandler):
    """Shaped like a Slack incoming webhook: accepts a JSON POST, says ok."""

    def do_POST(self):  # noqa: N802 - http.server contract
        length = int(self.headers.get("Content-Length") or 0)
        RECEIVED.append(
            {
                "path": self.path,
                "content_type": self.headers.get("Content-Type"),
                "body": self.rfile.read(length).decode("utf-8"),
            }
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):  # quiet
        pass


def main() -> int:
    import httpx
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.config import Config
    from holdspeak.db import get_database, reset_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    receiver = HTTPServer(("127.0.0.1", 0), _WebhookReceiver)
    receiver_port = receiver.server_address[1]
    threading.Thread(target=receiver.serve_forever, daemon=True).start()
    webhook_url = f"http://127.0.0.1:{receiver_port}/services/T0/B0/closeout"

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    config = Config()
    config.meeting.slack_webhook_url = webhook_url
    config.save(path=config_module.CONFIG_FILE)
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    db.meetings.save_meeting(
        MeetingState(
            id="m-closeout",
            started_at=datetime(2026, 6, 12, 10, 0, 0),
            title="Phase 61 closeout sync",
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[
                    {
                        "id": "a1",
                        "task": "Ship the Slack export",
                        "owner": "Karol",
                        "due": "today",
                        "status": "pending",
                        "review_state": "accepted",
                        "source_timestamp": None,
                        "created_at": datetime(2026, 6, 12, 10, 0, 0).isoformat(),
                    },
                ],
            ),
        )
    )

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        ),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    failures: list[str] = []
    page_errors: list[str] = []

    def check(ok: bool, label: str) -> None:
        print(("PASS  " if ok else "FAIL  ") + label)
        if not ok:
            failures.append(label)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 920})
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            # 1. The real UI path: open the meeting, click Send to Slack.
            page.goto(f"{url}/history", wait_until="networkidle")
            page.click("text=Phase 61 closeout sync")
            page.wait_for_selector(".aftercare-card", timeout=5000)
            page.click(".aftercare-head-actions .slack-btn")
            page.wait_for_selector(".proposal-card", timeout=5000)
            page.wait_for_timeout(400)

            proposals = db.actuators.list_proposals("m-closeout")
            check(
                len(proposals) == 1 and proposals[0].status == "proposed",
                "the click recorded one proposed proposal",
            )
            preview = proposals[0].preview
            check(
                RECEIVED == [],
                "NOTHING reached the receiver before approval (never egress unapproved)",
            )
            guard = page.text_content(".proposal-guard") or ""
            check(
                "approving sends this exact message to Slack" in guard,
                "the proposal card states the slack approval truth",
            )
            page.screenshot(path=str(OUT_DIR / "story04-proposed.png"), full_page=True)

            # 2. The real approval click → the REAL POST.
            page.click(".proposal-actions .btn.primary")
            page.wait_for_timeout(1200)
            body_text = page.text_content("body") or ""
            check("Approved — sent to Slack." in body_text, "the UI flash reports the send")
            check(len(RECEIVED) == 1, f"exactly one POST hit the receiver (got {len(RECEIVED)})")
            if RECEIVED:
                wire = RECEIVED[0]
                check(
                    wire["path"] == "/services/T0/B0/closeout",
                    "the POST hit the configured webhook path",
                )
                check(
                    wire["content_type"] == "application/json",
                    "the POST is JSON, the incoming-webhook contract",
                )
                check(
                    json.loads(wire["body"]) == {"text": preview},
                    "the wire body is byte-equal to the stored proposal preview",
                )
            final = db.actuators.get_proposal(proposals[0].id)
            check(final.status == "executed", f"the proposal is executed (is {final.status})")
            audit = db.actuators.list_audit(proposals[0].id)
            check(
                [a.to_status for a in audit] == ["proposed", "approved", "executed"],
                "the audit trail is the full lifecycle",
            )
            page.wait_for_timeout(400)
            page.screenshot(path=str(OUT_DIR / "story04-executed.png"), full_page=True)

            browser.close()

        # 3. The live wrong-host probe: a manifest for 127.0.0.1 only, handed
        #    a proposal pointing somewhere else, refuses BEFORE egress — real
        #    transport, no fake client (if the gate failed, a socket to a
        #    non-routable TEST-NET address would hang/fail differently).
        from holdspeak.plugins.actuators import ActuatorProposal
        from holdspeak.plugins.builtin.webhook_post_actuator import build_webhook_connector

        gate_only = build_webhook_connector(allowed_hosts=["127.0.0.1"])
        try:
            gate_only(
                ActuatorProposal(
                    target="slack",
                    action="post_message",
                    preview="must never leave",
                    payload={"url": "https://192.0.2.55/exfil", "body": {"text": "x"}},
                )
            )
            check(False, "wrong-host probe: the gate let a foreign host through")
        except Exception as exc:
            check(
                "192.0.2.55" in str(exc) or "allow" in str(exc).lower(),
                f"wrong-host probe refused before egress ({type(exc).__name__})",
            )
        check(len(RECEIVED) == 1, "the receiver still saw exactly one POST after the probe")

        # 4. The off-proof at the API: clear the URL → the route refuses.
        config = Config.load()
        config.meeting.slack_webhook_url = ""
        config.save(path=config_module.CONFIG_FILE)
        res = httpx.post(
            f"{url}/api/meetings/m-closeout/export/slack", json={"what": "digest"}
        )
        check(
            res.status_code == 400 and "not configured" in res.json()["error"],
            "off-proof: unconfigured export refuses with 400",
        )
    finally:
        server.stop()
        receiver.shutdown()

    check(not page_errors, f"zero uncaught page errors (saw {page_errors!r})")
    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} failure(s))")
        return 1
    print("RESULT: PASS (all checks + zero page errors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
