"""HS-106-05: process.input codec and the terminal-command adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from holdspeak.db import Database
from holdspeak.db.delivery_receipts import NodeReceiptLedger
from holdspeak.delivery.commands import (
    CommandRefused,
    HubCommandService,
    NodeCommandProcessor,
)
from holdspeak.kernel.broker import Broker
from holdspeak.kernel.journal import JournalStore
from holdspeak.kernel.model import OperationSpec
from holdspeak.kernel.process_input import ProcessInputCodec
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
T0 = datetime(2026, 7, 26, 12, 0, 0, tzinfo=timezone.utc)


class Targets:
    def verify(self, target_id, generation):
        if target_id == "term_1" and generation == "gen_1":
            return {
                "status": "ok",
                "target_id": target_id,
                "target_generation": generation,
                "pane_id": "%1",
            }
        return {"status": "target_gone", "detail": "unknown target"}


class Tmux:
    def __call__(self, argv, cwd=None):
        return SimpleNamespace(returncode=0, stdout="%1\n", stderr="")


def request(command_id="aaaaaaaa-bbbb-cccc-dddd-eeeeffff0001"):
    return {
        "request_schema": 1,
        "request_id": command_id,
        "idempotency_key": f"process.input:{command_id}",
        "operation": {"name": "process.input", "version": 1},
        "subject_refs": ["coder_session:claude:test"],
        "target": {"ref": "process:term_1"},
        "arguments": {
            "text": "send this exactly",
            "submit": False,
            "expected_generation": "gen_1",
            "command_id": command_id,
            "session_key": "claude:test",
            "agent": "claude",
            "expected_sequence": 1,
            "expires_in_seconds": 30,
        },
        "placement": "node:local",
    }


def command(command_id="aaaaaaaa-bbbb-cccc-dddd-eeeeffff0001", node="local"):
    return {
        "command_id": command_id,
        "node_id": node,
        "target_id": "term_1",
        "target_generation": "gen_1",
        "expected_sequence": 1,
        "operation": {"family": "coder_steering", "verb": "terminal.text"},
        "payload": {
            "text": "send this exactly",
            "session_key": "claude:test",
            "submit": False,
            "agent": "claude",
        },
    }


def keys_command(command_id="aaaaaaaa-bbbb-cccc-dddd-eeeeffff0002"):
    return {
        "command_id": command_id,
        "node_id": "local",
        "target_id": "term_1",
        "target_generation": "gen_1",
        "expected_sequence": 1,
        "operation": {"family": "coder_steering", "verb": "terminal.keys"},
        "payload": {
            "keys": [{"named": "C-c"}, {"literal": "x"}],
            "session_key": "claude:test",
            "agent": "claude",
            "expected_pane_id": "%1",
        },
    }


def test_process_input_codec_binds_terminal_payload_without_journaling_text(tmp_path):
    db = Database(tmp_path / "hub.db")
    codec = ProcessInputCodec(db.delivery_receipts)
    broker = Broker(
        JournalStore(db._connection),
        (OperationSpec(codec.name, codec.version, codec, "agent.submit", "propose"),),
    )
    handle = broker.submit(request(), OWNER)
    operation = broker.store.operation(handle["operation_id"])
    assert handle["state"] == "awaiting_decision"
    assert operation["name"] == "process.input"
    assert operation["target_ref"] == "process:term_1"
    assert operation["native_id"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeffff0001"
    assert operation["envelope_sha256"].startswith("sha256:")
    events = broker.store.events(0, {"operation_id": handle["operation_id"]})["events"]
    assert "send this exactly" not in repr(events)
    assert "command:aaaaaaaa-bbbb-cccc-dddd-eeeeffff0001" in repr(events)


def test_local_process_input_uses_existing_node_protocol_and_closes_kernel_receipt(
    tmp_path, monkeypatch
):
    db = Database(tmp_path / "hub.db")
    sent = []
    processor = NodeCommandProcessor(
        node_id="local",
        targets=Targets(),
        ledger=NodeReceiptLedger(tmp_path / "node.db"),
        runner=Tmux(),
        text_transport=lambda **kwargs: sent.append(kwargs),
        audit=lambda **kwargs: 7,
        wall_now=lambda: T0,
    )
    import holdspeak.delivery.commands as commands_module

    calls = 0
    actual = commands_module.resolve_policy

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return actual(*args, **kwargs)

    monkeypatch.setattr(commands_module, "resolve_policy", counted)
    service = HubCommandService(
        repo=db.delivery_receipts,
        processor=processor,
        local_node_id="local",
        mode_loader=lambda: "yolo",
        wall_now=lambda: T0,
    )
    response = service.submit_process_input(command(), OWNER, include_result=True)
    operation = service._kernel_service().store.operation(response["operation_id"])
    receipt = service._kernel_service().store.receipt(response["operation_id"])
    assert response["result"]["status"] == "delivered"
    assert sent == [{"pane": "%1", "text": "send this exactly", "submit": False}]
    assert operation["native_id"] == response["command_id"]
    assert receipt["state"] == "succeeded"
    assert receipt["result_ref"] == f"command:{response['command_id']}"
    assert calls == 1


def test_local_failure_gets_failed_kernel_receipt(tmp_path):
    def fail_transport(**kwargs):
        raise RuntimeError("tmux transport failed")

    db = Database(tmp_path / "hub.db")
    service = HubCommandService(
        repo=db.delivery_receipts,
        processor=NodeCommandProcessor(
            node_id="local",
            targets=Targets(),
            ledger=NodeReceiptLedger(tmp_path / "node.db"),
            runner=Tmux(),
            text_transport=fail_transport,
            audit=lambda **kwargs: 8,
            wall_now=lambda: T0,
        ),
        local_node_id="local",
        mode_loader=lambda: "yolo",
        wall_now=lambda: T0,
    )

    response = service.submit_process_input(command(), OWNER)
    receipt = service._kernel_service().store.receipt(response["operation_id"])

    assert response["receipt"]["state"] == "failed"
    assert receipt["state"] == "failed"


def test_terminal_keys_use_process_input_and_close_one_kernel_receipt(tmp_path):
    db = Database(tmp_path / "hub.db")
    sent = []
    service = HubCommandService(
        repo=db.delivery_receipts,
        processor=NodeCommandProcessor(
            node_id="local",
            targets=Targets(),
            ledger=NodeReceiptLedger(tmp_path / "node.db"),
            runner=Tmux(),
            keys_transport=lambda **kwargs: sent.append(kwargs),
            audit=lambda **kwargs: 9,
            wall_now=lambda: T0,
        ),
        local_node_id="local",
        mode_loader=lambda: "yolo",
        wall_now=lambda: T0,
    )

    response = service.submit_process_input(keys_command(), OWNER, include_result=True)
    operation = service._kernel_service().store.operation(response["operation_id"])
    receipt = service._kernel_service().store.receipt(response["operation_id"])

    assert response["result"]["status"] == "delivered"
    assert sent == [
        {
            "pane": "%1",
            "keys": [("named", "C-c"), ("literal", "x")],
        }
    ]
    assert operation["name"] == "process.input"
    assert operation["native_id"] == response["command_id"]
    assert receipt["state"] == "succeeded"
    assert receipt["result_ref"] == f"command:{response['command_id']}"


def test_policy_deny_is_refused_only_after_kernel_admission(tmp_path):
    db = Database(tmp_path / "hub.db")
    service = HubCommandService(
        repo=db.delivery_receipts,
        processor=NodeCommandProcessor(
            node_id="local",
            targets=Targets(),
            ledger=NodeReceiptLedger(tmp_path / "node.db"),
            wall_now=lambda: T0,
        ),
        local_node_id="local",
        mode_loader=lambda: "neutral",
        wall_now=lambda: T0,
    )

    response = service.submit_process_input(
        command(),
        OWNER,
        authority_snapshot={
            "outcome": "grant_required",
            "authority_basis": "none",
            "reason_code": "steering_grant_required",
            "policy_version": "operation-policy/v2",
            "mode": "neutral",
        },
        include_result=True,
    )
    kernel = service._kernel_service()
    receipt = kernel.store.receipt(response["operation_id"])
    operation = kernel.store.operation(response["operation_id"])

    assert response["receipt"]["state"] == "refused"
    assert receipt["state"] == "refused"
    assert receipt["outcome"] == "refused"
    assert response["result"]["status"] == "unarmed"
    assert operation["decision"] == "approve"


def test_remote_send_dropped_before_claim_gets_refused_kernel_receipt(tmp_path):
    db = Database(tmp_path / "hub.db")
    service = HubCommandService(
        repo=db.delivery_receipts,
        processor=NodeCommandProcessor(
            node_id="local",
            targets=Targets(),
            ledger=NodeReceiptLedger(tmp_path / "hub-node.db"),
            wall_now=lambda: T0,
        ),
        local_node_id="local",
        mode_loader=lambda: "neutral",
        wall_now=lambda: T0,
    )
    response = service.submit_process_input(command(node="edge"), OWNER)
    service._queues.pop("edge")

    aggregate = service.receipt(response["command_id"])
    kernel = service._kernel_service()
    kernel_receipt = kernel.store.receipt(response["operation_id"])
    operation = kernel.store.operation(response["operation_id"])

    assert aggregate["hub_state"] == "not_executed"
    assert operation["claimed_by"] == "edge"
    assert kernel_receipt["state"] == "refused"
    assert kernel_receipt["outcome"] == "refused"


def test_remote_node_reset_becomes_indeterminate_and_reconciles_by_command_id(tmp_path):
    db = Database(tmp_path / "hub.db")
    hub_processor = NodeCommandProcessor(
        node_id="local",
        targets=Targets(),
        ledger=NodeReceiptLedger(tmp_path / "hub-node.db"),
        wall_now=lambda: T0,
    )
    service = HubCommandService(
        repo=db.delivery_receipts,
        processor=hub_processor,
        local_node_id="local",
        mode_loader=lambda: "neutral",
        wall_now=lambda: T0,
    )
    response = service.submit_process_input(command(node="edge"), OWNER)
    claimed = service.claim_for_node("edge")
    assert [item["command_id"] for item in claimed] == [response["command_id"]]
    assert service.receipt(response["command_id"])["hub_state"] == "unknown"
    probes = service.claim_for_node("edge")
    assert probes == [{"kind": "reconcile", "command_id": response["command_id"]}]

    restarted = NodeCommandProcessor(
        node_id="edge",
        targets=Targets(),
        ledger=NodeReceiptLedger(tmp_path / "restarted-node.db"),
        wall_now=lambda: T0,
    )
    answer = restarted.reconcile(response["command_id"])
    service.record_results("edge", [answer])
    aggregate = service.receipt(response["command_id"])
    kernel_receipt = service._kernel_service().store.receipt(response["operation_id"])
    assert aggregate["hub_state"] == "indeterminate_after_node_reset"
    assert kernel_receipt["state"] == "indeterminate"
    assert kernel_receipt["result_ref"] == f"command:{response['command_id']}"


def test_claimed_or_indeterminate_retry_never_redispatches(tmp_path):
    db = Database(tmp_path / "hub.db")
    processor = NodeCommandProcessor(
        node_id="local",
        targets=Targets(),
        ledger=NodeReceiptLedger(tmp_path / "hub-node.db"),
        wall_now=lambda: T0,
    )
    service = HubCommandService(
        repo=db.delivery_receipts,
        processor=processor,
        local_node_id="local",
        mode_loader=lambda: "neutral",
        wall_now=lambda: T0,
    )
    request_body = command(node="edge")
    first = service.submit_process_input(request_body, OWNER)
    claimed = service.claim_for_node("edge")
    assert [item["command_id"] for item in claimed] == [first["command_id"]]

    retry = service.submit_process_input(request_body, OWNER)
    assert retry["duplicate"] is True
    assert retry["state"] == "claimed"
    assert retry["kernel_state"] == "claimed"
    assert service.claim_for_node("edge") == []

    swapped = command(node="edge")
    swapped["payload"]["text"] = "different payload"
    with pytest.raises(CommandRefused) as exc:
        service.submit_process_input(swapped, OWNER)
    assert exc.value.reason == "idempotency_payload_mismatch"
    assert service.claim_for_node("edge") == []

    kernel = service._kernel_service()
    kernel.receipt(
        first["operation_id"],
        "indeterminate",
        f"command:{first['command_id']}",
        Principal(PrincipalKind.NODE, "edge"),
    )
    terminal_retry = service.submit_process_input(request_body, OWNER)
    assert terminal_retry["duplicate"] is True
    assert terminal_retry["kernel_state"] == "indeterminate"
    assert service.claim_for_node("edge") == []
    assert processor.executions == 0
