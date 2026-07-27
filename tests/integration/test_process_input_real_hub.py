"""HS-106-05: process.input over real HTTP into a real tmux pane."""
from __future__ import annotations

import json
import os
import shutil
import signal
import select
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from holdspeak.coder_steering import arm, clear_grants
from holdspeak.db import Database
from holdspeak.db.delivery_receipts import NodeReceiptLedger
from holdspeak.delivery.commands import HubCommandService, NodeCommandProcessor
from holdspeak.delivery.terminal import TerminalTargetRegistry
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.tmux_transport import send_text_to_pane

_REPO = Path(__file__).resolve().parents[2]
_OWNER_TOKEN = "process-input-proof-owner"


@pytest.mark.skipif(shutil.which("tmux") is None, reason="tmux is required for real terminal proof")
def test_real_http_process_input_types_into_real_tmux(tmp_path: Path) -> None:
    home = tmp_path / "home"
    config = home / ".config" / "holdspeak" / "config.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps(
            {
                "config_version": 1,
                "control_mode": "yolo",
                "meeting": {"web_auth_token": _OWNER_TOKEN},
            }
        ),
        encoding="utf-8",
    )
    received = tmp_path / "received.txt"
    tmux_name = f"hs10605_{os.getpid()}"
    subprocess.run(
        [
            "tmux",
            "new-session",
            "-d",
            "-s",
            tmux_name,
            f"sh -c 'IFS= read -r line; printf %s \"$line\" > {received}; sleep 3'",
        ],
        check=True,
    )
    pane = subprocess.run(
        ["tmux", "display-message", "-p", "-t", f"{tmux_name}:0.0", "#{pane_id}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.update(HOME=str(home), HOLDSPEAK_WEB_PORT=str(port), PYTHONUNBUFFERED="1")

    def request(method: str, path: str, body: Any = None) -> tuple[int, dict[str, Any]]:
        data = None if body is None else json.dumps(body).encode()
        outgoing = urllib.request.Request(
            base + path,
            data=data,
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {_OWNER_TOKEN}",
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(outgoing, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc)

    hub = subprocess.Popen(
        [sys.executable, "-m", "holdspeak.main", "web", "--no-open"],
        cwd=_REPO,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        for _ in range(300):
            if hub.poll() is not None:
                output = hub.stdout.read() if hub.stdout else ""
                raise AssertionError(f"spawned hub exited early:\n{output}")
            try:
                with urllib.request.urlopen(base + "/health", timeout=0.2):
                    break
            except Exception:
                time.sleep(0.1)
        else:
            hub.kill()
            output = hub.stdout.read() if hub.stdout else ""
            raise AssertionError(f"spawned hub did not become healthy:\n{output}")

        status, target = request(
            "POST", "/api/delivery/terminal/targets", {"ref": f"pane:{pane}"}
        )
        assert status == 200 and target["pane_id"] == pane
        started = time.monotonic()
        status, delivered = request(
            "POST",
            "/api/delivery/terminal/commands",
            {
                "target_id": target["target_id"],
                "target_generation": target["target_generation"],
                "operation": {
                    "family": "coder_steering",
                    "verb": "terminal.text",
                },
                "payload": {
                    "text": "REAL_PROCESS_INPUT_106_05",
                    "session_key": "pane-proof",
                    "submit": True,
                    "agent": "claude",
                },
            },
        )
        latency_ms = (time.monotonic() - started) * 1000
        assert status == 200
        assert delivered["operation_id"].startswith("op_")
        assert delivered["receipt"]["outcome"] == "delivered"
        for _ in range(50):
            if received.exists():
                break
            time.sleep(0.05)
        assert received.read_text(encoding="utf-8") == "REAL_PROCESS_INPUT_106_05"
        status, projected = request(
            "GET",
            f"/api/kernel/read?refs=operation:{delivered['operation_id']}&view=receipt",
        )
        receipt = projected["objects"][0]["receipt"]
        assert status == 200 and receipt["state"] == "succeeded"
        print(
            json.dumps(
                {
                    "operation_id": delivered["operation_id"],
                    "pane": pane,
                    "received": received.read_text(encoding="utf-8"),
                    "receipt": receipt["state"],
                    "latency_ms": round(latency_ms, 2),
                },
                sort_keys=True,
            )
        )
    finally:
        hub.kill()
        hub.wait(timeout=10)
        subprocess.run(["tmux", "kill-session", "-t", tmux_name], check=False)


@pytest.mark.skipif(
    shutil.which("tmux") is None or not hasattr(os, "fork"),
    reason="tmux and fork are required for the real SIGKILL proof",
)
def test_real_sigkill_mid_send_reconciles_indeterminate_by_command_id(tmp_path: Path) -> None:
    clear_grants()
    received = tmp_path / "killed-send.txt"
    tmux_name = f"hs10605_kill_{os.getpid()}"
    subprocess.run(
        [
            "tmux",
            "new-session",
            "-d",
            "-s",
            tmux_name,
            f"sh -c 'IFS= read -r line; printf %s \"$line\" > {received}; sleep 10'",
        ],
        check=True,
    )
    pane = subprocess.run(
        ["tmux", "display-message", "-p", "-t", f"{tmux_name}:0.0", "#{pane_id}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    targets = TerminalTargetRegistry()
    target = targets.issue(f"pane:{pane}")
    assert target["status"] == "issued"
    grant = arm("sigkill:agent", pane, control_mode="neutral")
    assert grant["status"] == "armed"

    db = Database(tmp_path / "hub.db")
    hub_processor = NodeCommandProcessor(
        node_id="local",
        targets=targets,
        ledger=NodeReceiptLedger(tmp_path / "hub-node.db"),
    )
    service = HubCommandService(
        repo=db.delivery_receipts,
        processor=hub_processor,
        local_node_id="local",
        mode_loader=lambda: "neutral",
    )
    owner = Principal(PrincipalKind.OWNER, "owner-session")
    submitted = service.submit_process_input(
        {
            "node_id": "edge",
            "target_id": target["target_id"],
            "target_generation": target["target_generation"],
            "expected_sequence": 1,
            "operation": {"family": "coder_steering", "verb": "terminal.text"},
            "payload": {
                "text": "LANDED_BEFORE_SIGKILL_10605",
                "session_key": "sigkill:agent",
                "submit": True,
                "agent": "claude",
            },
        },
        owner,
        authority_snapshot={
            "outcome": "allowed",
            "authority_basis": "scoped_grant",
            "reason_code": "steering_grant_active",
            "policy_version": "operation-policy/v2",
            "mode": "neutral",
        },
    )
    envelope = service.claim_for_node("edge")[0]
    assert envelope["authority"]["decision"] == "allowed_by_active_grant"
    ledger_path = tmp_path / "edge-node.db"
    ready_read, ready_write = os.pipe()
    child = os.fork()
    if child == 0:
        try:
            os.close(ready_read)

            def transport(**kwargs):
                send_text_to_pane(**kwargs)
                os.write(ready_write, b"typed")
                time.sleep(30)

            processor = NodeCommandProcessor(
                node_id="edge",
                targets=targets,
                ledger=NodeReceiptLedger(ledger_path),
                text_transport=transport,
                audit=lambda **kwargs: 1,
            )
            child_result = processor.process(envelope)
            os.write(ready_write, f"RET:{child_result!r}".encode())
        except BaseException as exc:
            os.write(ready_write, f"ERR:{exc!r}".encode())
        finally:
            os._exit(0)
    os.close(ready_write)
    try:
        readable, _, _ = select.select([ready_read], [], [], 10)
        assert readable and os.read(ready_read, 16) == b"typed"
        os.kill(child, signal.SIGKILL)
        _, status = os.waitpid(child, 0)
        assert os.waitstatus_to_exitcode(status) == -signal.SIGKILL
        for _ in range(50):
            if received.exists():
                break
            time.sleep(0.05)
        assert received.read_text(encoding="utf-8") == "LANDED_BEFORE_SIGKILL_10605"

        assert service.receipt(submitted["command_id"])["hub_state"] == "unknown"
        probes = service.claim_for_node("edge")
        assert probes == [{"kind": "reconcile", "command_id": submitted["command_id"]}]
        restarted = NodeCommandProcessor(
            node_id="edge",
            targets=targets,
            ledger=NodeReceiptLedger(ledger_path),
        )
        service.record_results("edge", [restarted.reconcile(submitted["command_id"])])
        aggregate = service.receipt(submitted["command_id"])
        kernel = service._kernel_service().store.receipt(submitted["operation_id"])
        assert aggregate["hub_state"] == "indeterminate_after_node_reset"
        assert kernel["state"] == "indeterminate"
        print(
            json.dumps(
                {
                    "command_id": submitted["command_id"],
                    "operation_id": submitted["operation_id"],
                    "sigkill": -signal.SIGKILL,
                    "text_landed": received.read_text(encoding="utf-8"),
                    "aggregate": aggregate["hub_state"],
                    "kernel_receipt": kernel["state"],
                    "reconcile": "by_command_id",
                },
                sort_keys=True,
            )
        )
    finally:
        os.close(ready_read)
        try:
            os.kill(child, signal.SIGKILL)
        except ProcessLookupError:
            pass
        subprocess.run(["tmux", "kill-session", "-t", tmux_name], check=False)
        clear_grants()
