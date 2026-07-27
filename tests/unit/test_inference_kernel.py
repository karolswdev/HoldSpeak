"""HS-106-07: inference, child effects, cancellation, and restart honesty."""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.broker import Broker
from holdspeak.kernel.executor import ExecutorPlane
from holdspeak.kernel.inference import executor_identity
from holdspeak.kernel.journal import JournalStore
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.web.routes.primitives.invocations import recover_inference_on_startup

OWNER = Principal(PrincipalKind.OWNER, "owner-session")


@pytest.fixture
def rig(tmp_path: Path, monkeypatch):
    import holdspeak.db.core as db_core
    from holdspeak.kernel import runtime

    database = Database(tmp_path / "inference-kernel.db")
    monkeypatch.setattr(db_core, "_db", database)
    broker = _configure(database)
    monkeypatch.setattr(runtime, "_broker", broker)
    monkeypatch.setattr(runtime, "_database_id", id(database))
    return database, broker


def _run_request(key: str = "one", **arguments) -> dict:
    invocation_id = arguments.pop("invocation_id", f"invocation_{key}")
    values = {
        "invocation_id": invocation_id,
        "definition_ref": "persona:proof",
        "definition_revision": "rev-7",
        "grounding_refs": [{"ref": "note:ground", "revision": "rev-3"}],
        "requested_target_id": "this_machine",
        "deadline_at": time.time() + 300,
        "input_snapshot": {"input": "prove the run"},
        **arguments,
    }
    return {
        "request_schema": 1, "request_id": f"request-{key}",
        "idempotency_key": f"inference-{key}",
        "operation": {"name": "inference.run", "version": 1},
        "target": {}, "arguments": values,
    }


def _running(rig, key: str = "one"):
    database, broker = rig
    submitted = broker.submit(_run_request(key), OWNER)
    approved = broker.decide(
        submitted["operation_id"], "approve", submitted["revision"], OWNER
    )
    operation = broker.store.operation(approved["operation_id"])
    node = Principal(PrincipalKind.NODE, operation["placement"].removeprefix("node:"))
    claimed = broker.claim(node, operation["native_id"])["operations"][0]
    database.capability_invocations.start_attempt(
        invocation_id=operation["native_id"], attempt_id=f"attempt_{key}",
        destination="this_machine",
    )
    return operation, node, claimed


def test_codec_derives_placement_model_egress_and_rejects_assertions(rig) -> None:
    database, broker = rig
    handle = broker.submit(_run_request(), OWNER)
    operation = broker.store.operation(handle["operation_id"])
    assert operation["placement"] == f"node:{executor_identity('this_machine')}"
    events = broker.events(0, {"operation_id": handle["operation_id"]}, OWNER)["events"]
    admitted = next(item for item in events if item["event_type"] == "operation.admitted")
    assert "persona:proof" in admitted["refs"]
    assert "revision:rev-7" in admitted["refs"]
    assert "revision:rev-3" in admitted["refs"]
    assert "egress:none" in admitted["refs"]
    assert database.capability_invocations.get("invocation_one") is not None

    asserted = _run_request("asserted")
    asserted["placement"] = "node:client-chose-this"
    refused = broker.submit(asserted, OWNER)
    assert refused["receipt"]["outcome"] == "inference_placement_not_client_settable"


def test_token_stream_is_refused_before_any_native_invocation(rig) -> None:
    database, broker = rig
    request = _run_request("tokens")
    request["arguments"]["input_snapshot"]["token_stream"] = ["secret-token"]
    refused = broker.submit(request, OWNER)
    assert refused["receipt"]["outcome"] == "journal_content_forbidden"
    assert database.capability_invocations.get("invocation_tokens") is None
    journal = broker.events(0, {}, OWNER)["events"]
    assert "secret-token" not in str(journal)


def test_tool_effect_is_causally_linked_child_with_own_receipt(rig, tmp_path: Path) -> None:
    _, broker = rig
    parent, _, _ = _running(rig, "child")
    proposal_id = "proposal-child"
    child_request = {
        "request_schema": 1, "request_id": proposal_id,
        "idempotency_key": proposal_id,
        "operation": {"name": "tool.call", "version": 1},
        "parent_operation_id": parent["operation_id"],
        "target": {"ref": f"gate:{proposal_id}"},
        "placement": "node:tool-child",
        "arguments": {
            "proposal_id": proposal_id, "tool": "Write",
            "args_sha256": hashlib.sha256(b"child file effect").hexdigest(),
            "args_head": "write child proof", "cwd": "/proof", "ttl_seconds": 30,
        },
    }
    child = broker.submit(child_request, OWNER)
    approved = broker.decide(child["operation_id"], "approve", child["revision"], OWNER)
    tool_node = Principal(PrincipalKind.NODE, "tool-child")
    broker.claim(tool_node, proposal_id)
    effect_path = tmp_path / "child-proof.txt"
    effect_path.write_text("written only after child admission", encoding="utf-8")
    receipt = broker.receipt(
        approved["operation_id"], "succeeded", f"file:{effect_path}", tool_node
    )
    stored = broker.store.operation(approved["operation_id"])
    assert stored["parent_operation_id"] == parent["operation_id"]
    assert stored["correlation_id"] == parent["correlation_id"]
    assert receipt["outcome"] == "succeeded"
    events = broker.events(0, {"operation_id": approved["operation_id"]}, OWNER)["events"]
    assert {item["causation_id"] for item in events} == {parent["operation_id"]}
    assert {item["correlation_id"] for item in events} == {parent["correlation_id"]}
    print(
        json.dumps(
            {
                "parent": parent["operation_id"], "child": stored["operation_id"],
                "child_parent": stored["parent_operation_id"],
                "correlation": stored["correlation_id"], "effect_path": str(effect_path),
                "effect_content": effect_path.read_text(encoding="utf-8"),
                "child_receipt": receipt, "child_journal": events,
            },
            sort_keys=True,
        )
    )


def test_cancellation_is_a_child_operation_with_receipt(rig) -> None:
    database, broker = rig
    parent, node, _ = _running(rig, "cancel")
    signal_id = "cancel_" + uuid.uuid4().hex
    signal = broker.submit(
        {
            "request_schema": 1, "request_id": signal_id, "idempotency_key": signal_id,
            "operation": {"name": "inference.cancel", "version": 1},
            "parent_operation_id": parent["operation_id"], "target": {},
            "arguments": {
                "invocation_id": parent["native_id"], "signal_id": signal_id,
                "reason": "owner_cancelled",
            },
        },
        OWNER,
    )
    approved = broker.decide(signal["operation_id"], "approve", signal["revision"], OWNER)
    broker.claim(node, signal_id)
    invocation = database.capability_invocations.cancel(parent["native_id"])
    receipt = broker.receipt(
        approved["operation_id"], "succeeded", f"invocation:{parent['native_id']}", node
    )
    assert invocation.state == "cancelled"
    assert receipt["outcome"] == "succeeded"
    assert broker.store.operation(approved["operation_id"])["parent_operation_id"] == parent["operation_id"]


def test_three_drivers_reach_literal_same_spine_functions(rig, monkeypatch) -> None:
    _, broker = rig
    calls: list[tuple[str, str, str]] = []
    original_admit = Broker._admit_authority
    original_create = JournalStore.create_operation
    original_append = JournalStore.append
    original_terminal = ExecutorPlane._terminal

    def traced_admit(self, request, spec, principal, operation_id):
        calls.append((request.name, "admission+principal", "Broker._admit_authority"))
        return original_admit(self, request, spec, principal, operation_id)

    def traced_create(self, values):
        calls.append((values["name"], "journal-write", "JournalStore.create_operation"))
        return original_create(self, values)

    def traced_append(self, event_type, operation_id, **kwargs):
        operation = self.operation(operation_id)
        if operation is not None:
            calls.append((operation["name"], "journal-event", "JournalStore.append"))
        return original_append(self, event_type, operation_id, **kwargs)

    def traced_terminal(self, operation, state, outcome, result_ref=""):
        calls.append((operation["name"], "receipt", "ExecutorPlane._terminal"))
        return original_terminal(self, operation, state, outcome, result_ref)

    monkeypatch.setattr(Broker, "_admit_authority", traced_admit)
    monkeypatch.setattr(JournalStore, "create_operation", traced_create)
    monkeypatch.setattr(JournalStore, "append", traced_append)
    monkeypatch.setattr(ExecutorPlane, "_terminal", traced_terminal)

    process_id = str(uuid.uuid4())
    process = {
        "request_schema": 1, "request_id": process_id,
        "idempotency_key": f"process.input:{process_id}",
        "operation": {"name": "process.input", "version": 1},
        "target": {"ref": "process:term-proof"}, "placement": "node:local",
        "arguments": {
            "text": "same spine", "submit": False, "expected_generation": "gen-1",
            "command_id": process_id, "session_key": "proof", "agent": "proof",
            "expected_sequence": 1, "expires_in_seconds": 30,
        },
    }
    proposal_id = str(uuid.uuid4())
    actuator = {
        "request_schema": 1, "request_id": proposal_id,
        "idempotency_key": f"actuator:{proposal_id}",
        "operation": {"name": "actuator.egress", "version": 1},
        "target": {"ref": f"actuator:{proposal_id}"},
        "placement": "node:actuator-local",
        "arguments": {
            "proposal_id": proposal_id, "meeting_id": None, "origin": "desk",
            "window_id": "note:proof", "plugin_id": "builtin.webhook_post",
            "plugin_version": "1", "target": "webhook", "action": "post_message",
            "preview": "same spine", "payload": {"body": {"text": "same spine"}},
            "reversible": False, "required_capabilities": ["actuator"],
        },
    }
    requests = (process, actuator, _run_request("shared"))
    for request in requests:
        submitted = broker.submit(request, OWNER)
        approved = broker.decide(
            submitted["operation_id"], "approve", submitted["revision"], OWNER
        )
        operation = broker.store.operation(approved["operation_id"])
        node = Principal(PrincipalKind.NODE, operation["placement"].removeprefix("node:"))
        broker.claim(node, operation["native_id"])
        broker.receipt(operation["operation_id"], "succeeded", "result:shared", node)

    expected = {"process.input", "actuator.egress", "inference.run"}
    functions = {
        (layer, function): {name for name, seen_layer, seen_function in calls
                            if seen_layer == layer and seen_function == function}
        for layer, function in (
            ("admission+principal", "Broker._admit_authority"),
            ("journal-write", "JournalStore.create_operation"),
            ("journal-event", "JournalStore.append"),
            ("receipt", "ExecutorPlane._terminal"),
        )
    }
    assert all(names == expected for names in functions.values())
    print(json.dumps({f"{layer}: {function}": sorted(names)
                      for (layer, function), names in functions.items()}, sort_keys=True))


def test_hub_restart_projects_claimed_run_and_desk_state_as_unknown(rig) -> None:
    database, broker = rig
    parent, _, _ = _running(rig, "restart")
    recovered = recover_inference_on_startup()
    invocation = database.capability_invocations.get(parent["native_id"])
    process = broker.read(
        [f"operation:{parent['operation_id']}"], "process", "committed", OWNER
    )["objects"][0]["process"]
    assert recovered == [parent["native_id"]]
    assert invocation is not None and invocation.state == "unknown"
    assert invocation.attempts[0].state == "unknown"
    assert process["domain_state"] == "unknown"
    assert broker.store.receipt(parent["operation_id"])["outcome"] == "indeterminate"
