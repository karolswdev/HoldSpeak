"""HS-106-05: process.input into a real tmux pane (the real-HTTP proof is parked, 2026-11-08)."""
from __future__ import annotations

import json
import os
import shutil
import signal
import selectors
import subprocess
import time
from pathlib import Path

import pytest

from holdspeak.coder_steering import arm, clear_grants
from holdspeak.db import Database
from holdspeak.db.delivery_receipts import NodeReceiptLedger
from holdspeak.delivery.commands import HubCommandService, NodeCommandProcessor
from holdspeak.delivery.terminal import TerminalTargetRegistry
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.tmux_transport import send_text_to_pane


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
        with selectors.DefaultSelector() as readiness:
            readiness.register(ready_read, selectors.EVENT_READ)
            readable = readiness.select(timeout=10)
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
