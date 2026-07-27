"""HS-106-06: the durable actuator driver on the shared operation spine."""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from holdspeak import kernel
from holdspeak.db import Database
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _as_principal, _configure
from holdspeak.plugins.actuator_executor import ActuatorExecutor
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
AGENT = Principal(PrincipalKind.AGENT, "agent:actuator-proof")
NODE = Principal(PrincipalKind.NODE, "actuator-local")


@pytest.fixture
def rig(tmp_path: Path, monkeypatch):
    import holdspeak.db.core as db_core

    database = Database(tmp_path / "actuator-kernel.db")
    monkeypatch.setattr(db_core, "_db", database)
    return database, _configure(database)


def _request(key: str = "one", *, proposal_id: str | None = None) -> dict:
    proposal_id = proposal_id or str(uuid.uuid4())
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
            "preview": "Ship release 106",
            "payload": {"body": {"text": "Ship release 106"}},
            "reversible": False,
            "required_capabilities": ["actuator"],
        },
    }


def _submit(request: dict) -> dict:
    with _as_principal(AGENT):
        return kernel.submit(request)


def _approve(handle: dict) -> dict:
    with _as_principal(OWNER):
        return kernel.decide(handle["operation_id"], "approve", handle["revision"])


def test_submit_wait_approve_exact_claim_execute_receipt(rig) -> None:
    database, broker = rig
    request = _request()
    proposal_id = request["arguments"]["proposal_id"]
    handle = _submit(request)

    proposal = database.actuators.get_proposal(proposal_id)
    assert handle["state"] == "awaiting_decision"
    assert proposal is not None and proposal.status == "proposed"
    assert proposal.preview == "Ship release 106"

    approved = _approve(handle)
    assert approved["state"] == "awaiting_execution"
    assert database.actuators.get_proposal(proposal_id).status == "approved"

    sent = []
    executor = ActuatorExecutor(
        database,
        connector=lambda proposal: sent.append(dict(proposal.payload)) or {"status": 204},
        allow_actuators=True,
        operation_broker=broker,
        executor_principal=NODE,
    )
    executed = executor.execute(proposal_id)

    assert executed.status == "executed"
    assert sent == [{"body": {"text": "Ship release 106"}}]
    receipt = broker.store.receipt(handle["operation_id"])
    assert receipt["state"] == "succeeded"
    assert receipt["result_ref"].startswith("actuator-audit:")
    with _as_principal(AGENT):
        projected = kernel.read(
            [f"operation:{handle['operation_id']}"], "full", "committed"
        )["objects"][0]
    assert [row["outcome"] for row in projected["native_receipts"]] == [
        "proposed", "approved", "executed"
    ]
    assert broker.store.last_receipt_for_ref("egress:webhook") is not None


def test_native_id_exact_claim_selects_requested_proposal(rig) -> None:
    database, broker = rig
    first_request = _request("first")
    second_request = _request("second")
    first = _submit(first_request)
    second = _submit(second_request)
    _approve(first)
    _approve(second)

    second_id = second_request["arguments"]["proposal_id"]
    executor = ActuatorExecutor(
        database,
        connector=lambda proposal: {"delivered": proposal.preview},
        allow_actuators=True,
        operation_broker=broker,
        executor_principal=NODE,
    )
    assert executor.execute(second_id).status == "executed"
    assert broker.store.operation(first["operation_id"])["state"] == "awaiting_execution"
    assert broker.store.operation(second["operation_id"])["state"] == "succeeded"


def test_connector_failure_still_closes_with_failure_receipt(rig) -> None:
    database, broker = rig
    request = _request("failure")
    handle = _submit(request)
    _approve(handle)

    def unavailable(_proposal):
        raise ConnectionError("destination unavailable")

    executor = ActuatorExecutor(
        database,
        connector=unavailable,
        allow_actuators=True,
        operation_broker=broker,
        executor_principal=NODE,
    )
    failed = executor.execute(request["arguments"]["proposal_id"])
    assert failed.status == "failed"
    assert broker.store.receipt(handle["operation_id"])["state"] == "failed"


def test_reject_is_refusal_receipt_and_never_executes(rig) -> None:
    database, broker = rig
    request = _request("reject")
    proposal_id = request["arguments"]["proposal_id"]
    handle = _submit(request)
    with _as_principal(OWNER):
        rejected = kernel.decide(
            handle["operation_id"], "reject", handle["revision"]
        )

    assert rejected["state"] == "refused"
    assert rejected["receipt"]["outcome"] == "owner_rejected"
    assert database.actuators.get_proposal(proposal_id).status == "rejected"
    assert broker.claim(NODE, native_id=proposal_id) == {"operations": []}


def test_stale_revision_refuses_by_name_before_native_approval(rig) -> None:
    database, _ = rig
    request = _request("stale")
    proposal_id = request["arguments"]["proposal_id"]
    handle = _submit(request)

    with _as_principal(OWNER), pytest.raises(KernelRefused) as caught:
        kernel.decide(handle["operation_id"], "approve", handle["revision"] - 1)

    assert caught.value.reason == "operation_revision_conflict"
    assert database.actuators.get_proposal(proposal_id).status == "proposed"


def test_approved_operation_survives_hub_restart_before_egress(rig) -> None:
    database, _ = rig
    request = _request("restart")
    proposal_id = request["arguments"]["proposal_id"]
    handle = _submit(request)
    _approve(handle)

    restarted = _configure(database)
    assert restarted.store.operation(handle["operation_id"])["state"] == "awaiting_execution"
    assert restarted.store.receipt(handle["operation_id"]) is None
    executor = ActuatorExecutor(
        database,
        connector=lambda proposal: {"delivered": proposal.target},
        allow_actuators=True,
        operation_broker=restarted,
        executor_principal=NODE,
    )
    executed = executor.execute(proposal_id)

    assert executed.status == "executed"
    assert restarted.store.receipt(handle["operation_id"])["state"] == "succeeded"
