"""HS-152-04: /decide route 'always' flag writes an allow policy row.

When ``always=true`` and ``decision=approve``, the server writes a
``thread_tool_policy(decision='allow')`` row so future calls to the
same tool auto-admit per the truth table row 1.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.thread_tools import (
    ThreadToolExecutor,
    resolve_tool_decision,
)


OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "test_decide_always.db")


def _executor(
    db: Database,
    *,
    control_mode: str = "safe",
    dispatch_result: Any = {"ok": True},
) -> ThreadToolExecutor:
    def fake_dispatch(name: str, args: dict, principal: Principal) -> Any:
        return dispatch_result

    return ThreadToolExecutor(
        db,
        dispatch_fn=fake_dispatch,
        principal=OWNER,
        control_mode_fn=lambda: control_mode,
    )


def _call(name: str = "desk.create", args: dict | None = None) -> dict[str, Any]:
    return {
        "id": f"call-{name.replace('.', '-')}",
        "name": name,
        "arguments": args or {},
    }


class TestDecideAlways:
    """Tests for the 'always' flag on the /decide flow."""

    def test_always_approve_writes_allow_policy_row(self, db: Database) -> None:
        """When always=true + approve, the policy row is 'allow'."""
        exe = _executor(db, control_mode="safe")
        thread = db.threads.create_thread(title="test-always")
        thread_id = thread.id

        # In safe mode, effect_proposal is held
        handle = exe.admit("op-1", thread_id, _call("desk.create"))
        assert handle.state == "awaiting_decision"

        # Simulate what the /decide route does with always=true:
        # 1. Write the policy row
        db.threads.set_tool_policy(thread_id, handle.name, "allow")
        # 2. Decide
        exe.decide(handle, "approve")
        assert handle.state == "admitted"

        # Verify the policy row exists
        policy = db.threads.effective_tool_policy(thread_id, "desk.create")
        assert policy == "allow"

        # Now a second call to the same tool should auto-admit
        handle2 = exe.admit("op-1", thread_id, _call("desk.create"))
        assert handle2.state == "admitted", (
            "After Allow-always, the truth table row 1 (policy=allow) should admit"
        )

    def test_approve_without_always_writes_no_policy_row(self, db: Database) -> None:
        """Without always, approve does not write a policy row."""
        exe = _executor(db, control_mode="safe")
        thread = db.threads.create_thread(title="test-once")
        thread_id = thread.id

        handle = exe.admit("op-1", thread_id, _call("desk.create"))
        assert handle.state == "awaiting_decision"

        # Plain approve: no policy row written
        exe.decide(handle, "approve")
        assert handle.state == "admitted"

        policy = db.threads.effective_tool_policy(thread_id, "desk.create")
        assert policy is None, "Allow-once should not write a policy row"

        # A second call in safe mode is still held
        handle2 = exe.admit("op-1", thread_id, _call("desk.create"))
        assert handle2.state == "awaiting_decision"

    def test_deny_writes_no_policy_row(self, db: Database) -> None:
        """Deny does not write a policy row (settled design: 'Deny = refuse
        this call, no row')."""
        exe = _executor(db, control_mode="safe")
        thread = db.threads.create_thread(title="test-deny")
        thread_id = thread.id

        handle = exe.admit("op-1", thread_id, _call("desk.create"))
        assert handle.state == "awaiting_decision"

        exe.decide(handle, "deny")
        assert handle.state == "denied"

        policy = db.threads.effective_tool_policy(thread_id, "desk.create")
        assert policy is None, "Deny should not write a policy row"

    def test_always_flag_makes_policy_row_allow_resolve_admit(self, db: Database) -> None:
        """After Allow-always, resolve_tool_decision returns 'admit'."""
        thread = db.threads.create_thread(title="test-resolve")
        thread_id = thread.id
        db.threads.set_tool_policy(thread_id, "desk.create", "allow")

        policy = db.threads.effective_tool_policy(thread_id, "desk.create")
        assert resolve_tool_decision(policy, "safe", "effect_proposal") == "admit"


class TestElicitationRedispatch:
    """HS-152-04: elicitation flow — executor returns {"elicit": {...}},
    decide(approve, answer) stores the answer, re-execute dispatches with
    args.__answer."""

    def test_elicitation_hold_then_answer_redispatch(self, db: Database) -> None:
        """Dispatch returns {"elicit": {schema}} -> handle.state = awaiting_decision,
        handle.elicitation set. decide(approve, answer) -> state = admitted,
        handle.answer set. Re-execute dispatches with args.__answer."""
        call_log: list[dict] = []

        def elicit_dispatch(name: str, args: dict, principal: Principal) -> Any:
            call_log.append({"name": name, "args": dict(args)})
            if "__answer" not in args:
                return {"elicit": {"type": "object", "prompt": "Pick",
                                   "properties": {"fruit": {"type": "string"}}}}
            return {"ok": True, "received": args["__answer"]}

        exe = ThreadToolExecutor(
            db, dispatch_fn=elicit_dispatch, principal=OWNER,
            control_mode_fn=lambda: "yolo",
        )
        thread = db.threads.create_thread(title="elicit-test")

        # Auto-admitted in yolo
        handle = exe.admit("op-e", thread.id, _call("desk.list"))
        assert handle.state == "admitted"

        # First execute -> elicitation
        result1 = exe.execute(handle)
        assert result1.kind == "elicitation"
        assert result1.elicitation is not None
        assert handle.state == "awaiting_decision"
        assert handle.elicitation == {"type": "object", "prompt": "Pick",
                                       "properties": {"fruit": {"type": "string"}}}

        # User answers
        exe.decide(handle, "approve", answer={"fruit": "apple"})
        assert handle.state == "admitted"
        assert handle.answer == {"fruit": "apple"}

        # Re-execute -> normal result with __answer in args
        result2 = exe.execute(handle)
        assert result2.kind == "data"
        assert result2.payload == {"ok": True, "received": {"fruit": "apple"}}
        assert handle.state == "completed"

        # Verify dispatch was called twice: once without __answer, once with
        assert len(call_log) == 2
        assert "__answer" not in call_log[0]["args"]
        assert call_log[1]["args"]["__answer"] == {"fruit": "apple"}

    def test_elicitation_decline_denies(self, db: Database) -> None:
        """Declining an elicitation sets state=denied."""
        def elicit_dispatch(name: str, args: dict, principal: Principal) -> Any:
            return {"elicit": {"type": "object", "properties": {}}}

        exe = ThreadToolExecutor(
            db, dispatch_fn=elicit_dispatch, principal=OWNER,
            control_mode_fn=lambda: "yolo",
        )
        thread = db.threads.create_thread(title="elicit-decline")
        handle = exe.admit("op-d", thread.id, _call("desk.list"))
        result = exe.execute(handle)
        assert result.kind == "elicitation"
        assert handle.state == "awaiting_decision"

        # Decline
        exe.decide(handle, "deny")
        assert handle.state == "denied"

        # Execute the denied handle -> tool_denied
        result2 = exe.execute(handle)
        assert result2.kind == "tool_denied"
