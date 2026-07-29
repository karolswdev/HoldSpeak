"""HS-106-06 real hub and real loopback egress proof."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

_REPO = Path(__file__).resolve().parents[2]
_OWNER_TOKEN = "hs10606-owner-token"


class _Destination(BaseHTTPRequestHandler):
    calls: list[dict[str, Any]] = []

    def do_POST(self) -> None:  # noqa: N802
        size = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(size)
        self.__class__.calls.append(json.loads(body))
        self.send_response(204)
        self.end_headers()

    def log_message(self, *_args: Any) -> None:
        return None


def _request(key: str, proposal_id: str) -> dict[str, Any]:
    return {
        "request_schema": 1,
        "request_id": f"request-{key}",
        "idempotency_key": f"actuator-{key}",
        "operation": {"name": "actuator.egress", "version": 1},
        "subject_refs": ["note:release-card"],
        "target": {"ref": f"actuator:{proposal_id}"},
        "placement": "node:actuator-local",
        "arguments": {
            "proposal_id": proposal_id,
            "meeting_id": None,
            "origin": "desk",
            "window_id": "note:release-card",
            "plugin_id": "builtin.webhook_post",
            "plugin_version": "1",
            "target": "webhook",
            "action": "post_message",
            "preview": f"Kernel egress {key}",
            "payload": {"body": {"text": f"Kernel egress {key}"}},
            "reversible": False,
            "required_capabilities": ["actuator"],
        },
    }


@pytest.mark.integration
def test_real_hub_durable_actuator_egress_and_refusals(tmp_path: Path) -> None:
    _Destination.calls = []
    destination = ThreadingHTTPServer(("127.0.0.1", 0), _Destination)
    destination_thread = threading.Thread(target=destination.serve_forever, daemon=True)
    destination_thread.start()
    destination_url = f"http://127.0.0.1:{destination.server_address[1]}/sink"

    home = tmp_path / "home"
    config = home / ".config" / "holdspeak" / "config.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps(
            {
                "config_version": 1,
                "control_mode": "neutral",
                "meeting": {
                    "web_auth_token": _OWNER_TOKEN,
                    "companion_webhook_url": destination_url,
                },
            }
        ),
        encoding="utf-8",
    )
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.update(HOME=str(home), HOLDSPEAK_WEB_PORT=str(port), PYTHONUNBUFFERED="1")

    def call(method: str, path: str, body: Any = None) -> tuple[int, dict[str, Any]]:
        outgoing = urllib.request.Request(
            base + path,
            data=None if body is None else json.dumps(body).encode(),
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {_OWNER_TOKEN}",
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(outgoing, timeout=15) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc)

    def start_hub() -> subprocess.Popen[str]:
        process = subprocess.Popen(
            [sys.executable, "-m", "holdspeak.main", "web", "--no-open"],
            cwd=_REPO,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for _ in range(150):
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise AssertionError(f"spawned hub exited early:\n{output}")
            try:
                urllib.request.urlopen(base + "/health", timeout=0.2).close()
                return process
            except Exception:
                time.sleep(0.1)
        process.kill()
        raise AssertionError("spawned hub did not become healthy")

    hub = start_hub()
    try:

        live_id = str(uuid.uuid4())
        status, submitted = call("POST", "/api/kernel/submit", _request("live", live_id))
        assert status == 202 and submitted["state"] == "awaiting_decision"
        status, review = call(
            "GET",
            f"/api/kernel/read?refs=operation:{submitted['operation_id']}&view=full",
        )
        assert status == 200
        assert review["objects"][0]["canonical"]["preview"] == "Kernel egress live"
        assert review["objects"][0]["canonical"]["payload"] == {
            "body": {"text": "Kernel egress live"}
        }
        time.sleep(0.15)
        status, approved = call(
            "POST",
            f"/api/kernel/operations/{submitted['operation_id']}/decide",
            {"decision": "approve", "expected_revision": submitted["revision"]},
        )
        assert status == 200 and approved["state"] == "awaiting_execution"
        hub.terminate()
        hub.wait(timeout=5)
        hub = start_hub()
        status, executed = call(
            "POST",
            f"/api/desk/actuators/webhook/{live_id}/decision",
            {"decision": "approved", "decided_by": "owner-session"},
        )
        assert status == 200, executed
        assert executed["proposal"]["status"] == "executed"
        assert _Destination.calls == [{"text": "Kernel egress live"}]

        status, readback = call(
            "GET",
            f"/api/kernel/read?refs=operation:{submitted['operation_id']}&view=full",
        )
        assert status == 200
        projection = readback["objects"][0]
        assert projection["receipt"]["state"] == "succeeded"
        assert [row["outcome"] for row in projection["native_receipts"]] == [
            "proposed", "approved", "executed"
        ]

        reject_id = str(uuid.uuid4())
        _, pending = call("POST", "/api/kernel/submit", _request("reject", reject_id))
        _, rejected = call(
            "POST",
            f"/api/kernel/operations/{pending['operation_id']}/decide",
            {"decision": "reject", "expected_revision": pending["revision"]},
        )
        assert rejected["receipt"]["state"] == "refused"
        assert _Destination.calls == [{"text": "Kernel egress live"}]

        stale_id = str(uuid.uuid4())
        _, stale = call("POST", "/api/kernel/submit", _request("stale", stale_id))
        stale_status, stale_refusal = call(
            "POST",
            f"/api/kernel/operations/{stale['operation_id']}/decide",
            {"decision": "approve", "expected_revision": stale["revision"] - 1},
        )
        assert stale_status == 409
        assert stale_refusal["error"] == "operation_revision_conflict"

        _, setup = call("GET", "/api/setup/status")
        assert setup["trust"]["last_egress"]["id"] == "kernel_external_egress"
        assert setup["trust"]["last_egress"]["name"] == (
            f"127.0.0.1:{destination.server_address[1]}"
        )
        print(
            json.dumps(
                {
                    "real_destination": destination_url,
                    "effect": _Destination.calls[0],
                    "operation_id": submitted["operation_id"],
                    "reviewed_preview": review["objects"][0]["canonical"]["preview"],
                    "receipt": projection["receipt"]["state"],
                    "historic_audit_projection": [
                        row["outcome"] for row in projection["native_receipts"]
                    ],
                    "rejected": rejected["receipt"]["state"],
                    "stale": stale_refusal["error"],
                    "badge_source": setup["trust"]["last_egress"],
                },
                sort_keys=True,
            )
        )
    finally:
        hub.terminate()
        try:
            hub.wait(timeout=5)
        except subprocess.TimeoutExpired:
            hub.kill()
            hub.wait(timeout=5)
        destination.shutdown()
        destination.server_close()
