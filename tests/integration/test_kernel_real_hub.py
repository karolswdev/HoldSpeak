"""HS-106-04 proof: real HTTP, real hub processes, and real SIGKILL."""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from holdspeak.db import Database
from holdspeak.deployment_revisions import capture_deployment_revision
from holdspeak.inference_targets import resolve_inference_target
from holdspeak.kernel.inference_runner import InferenceRunner, InvocationRequest, ServiceContract
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind

_REPO = Path(__file__).resolve().parents[2]
_OWNER_TOKEN = "kernel-proof-owner"
_NODE_TOKEN = "kernel-proof-node"


def _operation(key: str) -> dict[str, Any]:
    return {
        "request_schema": 1,
        "request_id": f"request-{key}",
        "idempotency_key": f"key-{key}",
        "operation": {"name": "tool.call", "version": 1},
        "subject_refs": ["story:HS-106-04"],
        "target": {"ref": f"gate:proposal-{key}"},
        "arguments": {
            "proposal_id": f"proposal-{key}",
            "tool": "Bash",
            "args_sha256": "a" * 64,
            "args_head": "git status",
            "cwd": "/workspace",
            "ttl_seconds": 60,
        },
        "placement": "node:node_kernel_proof",
    }


def test_real_http_executor_receipt_and_sigkill_cursor_replay(tmp_path: Path) -> None:
    home = tmp_path / "home"
    config = home / ".config" / "holdspeak" / "config.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps({"config_version": 1, "meeting": {"web_auth_token": _OWNER_TOKEN}}),
        encoding="utf-8",
    )
    node_store = home / ".holdspeak" / "node_auth_tokens.json"
    node_store.parent.mkdir(parents=True)
    node_store.write_text(
        json.dumps(
            {
                "node_tokens_schema": 1,
                "nodes": {
                    "proof": {
                        "node_id": "node_kernel_proof",
                        "token": _NODE_TOKEN,
                        "revoked": False,
                        "created_at": "proof",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    os.chmod(node_store, 0o600)
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.update(HOME=str(home), HOLDSPEAK_WEB_PORT=str(port), PYTHONUNBUFFERED="1")

    def request(
        method: str, path: str, body: Any = None, *, token: str = _OWNER_TOKEN,
        node: bool = False,
    ) -> tuple[int, dict[str, Any]]:
        data = None if body is None else json.dumps(body).encode()
        headers = {"content-type": "application/json"}
        if node:
            headers["x-holdspeak-node-token"] = token
        else:
            headers["authorization"] = f"Bearer {token}"
        outgoing = urllib.request.Request(
            base + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(outgoing, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc)

    def start() -> subprocess.Popen[str]:
        process = subprocess.Popen(
            [sys.executable, "-m", "holdspeak.main", "web", "--no-open"],
            cwd=_REPO,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for _ in range(100):
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise AssertionError(f"spawned hub exited early:\n{output}")
            try:
                with urllib.request.urlopen(base + "/health", timeout=0.2):
                    return process
            except Exception:
                time.sleep(0.1)
        process.kill()
        output = process.stdout.read() if process.stdout else ""
        raise AssertionError(f"spawned hub did not become healthy:\n{output}")

    process = start()
    try:
        status, issued = request(
            "POST", "/api/principals/agents", {"identity": "agent:kernel-proof"}
        )
        assert status == 201
        agent_token = issued["credential"]

        refused_request = _operation("refused")
        refused_request["arguments"]["audio_frames"] = ["forbidden"]
        status, refused = request(
            "POST", "/api/kernel/submit", refused_request, token=agent_token
        )
        assert (
            status, refused["state"], refused["receipt"]["state"],
            refused["receipt"]["outcome"],
        ) == (202, "refused", "refused", "journal_content_forbidden")

        status, submitted = request(
            "POST", "/api/kernel/submit", _operation("complete"), token=agent_token
        )
        assert (status, submitted["state"]) == (202, "awaiting_decision")
        operation_id = submitted["operation_id"]

        status, agent_refusal = request(
            "POST",
            f"/api/kernel/operations/{operation_id}/decide",
            {"decision": "approve", "expected_revision": submitted["revision"]},
            token=agent_token,
        )
        assert (status, agent_refusal["error"], agent_refusal["missing_right"]) == (
            403, "principal_right_required", "decide"
        )

        status, immutable = request(
            "POST",
            f"/api/kernel/operations/{operation_id}/decide",
            {
                "decision": "approve",
                "expected_revision": submitted["revision"],
                "payload": {"changed": True},
                "target": {"ref": "other"},
                "placement": "node:other",
            },
        )
        assert (status, immutable) == (
            409,
            {
                "error": "admitted_envelope_immutable",
                "fields": ["payload", "placement", "target"],
            },
        )

        status, approved = request(
            "POST",
            f"/api/kernel/operations/{operation_id}/decide",
            {"decision": "approve", "expected_revision": submitted["revision"]},
        )
        assert (status, approved["state"]) == (200, "awaiting_execution")
        status, claimed = request(
            "POST", "/api/kernel/executor/claim", {}, token=_NODE_TOKEN, node=True
        )
        assert (status, claimed["operations"][0]["state"]) == (200, "claimed")
        status, terminal = request(
            "POST",
            f"/api/kernel/executor/operations/{operation_id}/receipt",
            {"outcome": "succeeded", "result_ref": "gate:proposal-complete"},
            token=_NODE_TOKEN,
            node=True,
        )
        assert (status, terminal["state"], terminal["outcome"]) == (
            200, "succeeded", "succeeded"
        )
        status, before = request(
            "GET", f"/api/kernel/events?after_cursor=0&operation_id={operation_id}"
        )
        assert status == 200 and len(before["events"]) == 5

        status, pending = request(
            "POST", "/api/kernel/submit", _operation("pending"), token=agent_token
        )
        assert (status, pending["state"]) == (202, "awaiting_decision")
        os.kill(process.pid, signal.SIGKILL)
        assert process.wait(timeout=10) == -signal.SIGKILL

        process = start()
        status, replay = request(
            "GET", f"/api/kernel/events?after_cursor=0&operation_id={operation_id}"
        )
        assert status == 200 and replay == before
        status, recovered = request(
            "GET",
            f"/api/kernel/read?refs=operation:{pending['operation_id']}&view=receipt",
        )
        item = recovered["objects"][0]
        assert (status, item["operation"]["state"], item["receipt"]["outcome"]) == (
            200, "indeterminate", "hub_restart_during_decision"
        )

        print(
            json.dumps(
                {
                    "submit": submitted["state"],
                    "refusal_receipt": refused["receipt"]["outcome"],
                    "agent_decide": agent_refusal["error"],
                    "immutable": immutable["error"],
                    "claim": claimed["operations"][0]["state"],
                    "receipt": terminal["outcome"],
                    "sigkill": -signal.SIGKILL,
                    "cursor_replay_same": replay == before,
                    "recovered": item["receipt"]["outcome"],
                },
                sort_keys=True,
            )
        )
    finally:
        if process.poll() is None:
            os.kill(process.pid, signal.SIGKILL)
            process.wait(timeout=10)


def test_synthetic_admitted_reference_invocation_and_cancelled_stream(tmp_path: Path) -> None:
    database = Database(tmp_path / "runner-hub.db")
    database.profiles.upsert(
        profile_id="reference", name="Reference", kind="onDevice", model_file="/reference.gguf",
    )
    revision = capture_deployment_revision(database, resolve_inference_target(database, "reference"))
    broker = _configure(database)
    owner = Principal(PrincipalKind.OWNER, "integration-owner")
    runner = InferenceRunner(
        broker, database, engine_factory=lambda value, **_kw: {"revision": value.id},
        principal_provider=lambda: owner,
    )

    class Reference:
        def dispatch(self, engine, payload, cancellation):
            return "reference-result"

        def cancel(self):
            return "cancelled"

    payload = {"request": "private"}
    invocation = InvocationRequest(
        deployment_revision=revision.id,
        definition_origin=ServiceContract.for_payload("ask", "v1", payload),
        deadline_at=time.time() + 10, payload=payload,
    )
    succeeded = runner.invoke(invocation, Reference())
    assert succeeded.outcome == "succeeded"

    started, release = threading.Event(), threading.Event()

    class Streaming(Reference):
        def dispatch(self, engine, payload, cancellation):
            started.set()
            release.wait(2)
            return "late-stream"

    cancelled = []
    streaming = InvocationRequest(**{**invocation.__dict__, "invocation_id": "integration_cancel"})
    thread = threading.Thread(
        target=lambda: cancelled.append(runner.invoke(streaming, Streaming()))
    )
    thread.start()
    assert started.wait(2)
    assert runner.cancel("integration_cancel") == "cancelled"
    release.set()
    thread.join(2)
    assert cancelled[0].outcome == "cancelled"
