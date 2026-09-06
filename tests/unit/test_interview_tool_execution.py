"""Actual kernel claims/receipts and refusals around interview domain calls."""
from __future__ import annotations

import time

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _build, _dispose
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.thread_tools import ThreadToolExecutor

OWNER = Principal(PrincipalKind.OWNER, "interview-owner")


@pytest.fixture
def rig(tmp_path, monkeypatch):
    from holdspeak.kernel import runtime
    monkeypatch.setattr(runtime, "_mode", lambda: "yolo")
    db = Database(tmp_path / "kernel-interview.db")
    broker = _build(db)
    thread = db.threads.create_thread()
    parent = broker.parent_run_controller.start(OWNER, kind="tool.turn", definition_ref=f"thread:{thread.id}", definition_revision="1", input_snapshot={"thread_id": thread.id}, deadline_at=time.time() + 60, child_budget=3)
    calls = []
    executor = ThreadToolExecutor(db, dispatch_fn=lambda *args: calls.append(args) or {"observed": True}, principal=OWNER, control_mode_fn=lambda: "yolo", broker=broker, allowed_names=frozenset({"interview.get"}))
    executor._parent_context = parent.context
    yield db, broker, parent, thread, executor, calls
    _dispose(broker)
    db.close()


def test_real_tool_child_claim_receipt_and_replay_refusal(rig):
    _db, broker, parent, thread, executor, calls = rig
    call = {"id": "read-context", "name": "interview.get", "arguments": {"thread_id": thread.id}}
    handle = executor.admit(parent.operation_id, thread.id, call)
    result = executor.execute(handle)
    assert result.kind != "tool_execution_failed", result.payload
    assert result.receipt_id.startswith("rcpt_")
    operation = broker.store.operation(handle.kernel_child_id)
    assert operation["state"] == "succeeded"
    assert operation["parent_operation_id"] == parent.operation_id
    assert calls[0][2] is OWNER
    with pytest.raises(ValueError, match="reconciliation"):
        executor.admit(parent.operation_id, thread.id, call)
    assert len(calls) == 1
    broker.parent_run_controller.close(parent.context, "succeeded", f"thread:{thread.id}", principal=OWNER)


def test_model_cannot_call_classified_but_unoffered_tool(rig):
    _db, _broker, parent, thread, executor, calls = rig
    with pytest.raises(ValueError, match="palette"):
        executor.admit(parent.operation_id, thread.id, {"id": "bad", "name": "desk.delete", "arguments": {}})
    assert calls == []


def test_revoked_parent_never_dispatches(rig):
    _db, broker, parent, thread, executor, calls = rig
    broker.store.revoke_warrant(parent.operation_id)
    with pytest.raises(ValueError, match="admission"):
        executor.admit(parent.operation_id, thread.id, {"id": "bad", "name": "interview.get", "arguments": {"thread_id": thread.id}})
    assert calls == []


def test_explicit_deny_is_terminal_without_effect(rig):
    db, broker, parent, thread, executor, calls = rig
    db.threads.set_tool_policy(thread.id, "interview.get", "deny")
    handle = executor.admit(parent.operation_id, thread.id, {"id": "deny", "name": "interview.get", "arguments": {"thread_id": thread.id}})
    result = executor.execute(handle)
    assert result.kind == "tool_denied"
    assert result.receipt_id.startswith("rcpt_")
    assert calls == []
