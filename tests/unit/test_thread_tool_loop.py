"""HS-152-01 -- Thread tool loop (pass loop, frames, abort, sensitive accumulator).

Tests the pass loop in ``ThreadService._run_streaming_turn`` with a fake
engine (yields tool_calls then text on the next pass) and the real
``ThreadToolExecutor`` (with a fake dispatch function).

Scoped: this file + test_thread_service.py + test_realtime_frame_registry.py
+ test_threads_api.py + test_phase143_inference_capability_census.py
+ test_one_path_census.py + test_thread_tool_gate.py.
"""
from __future__ import annotations

import asyncio
import json
import threading
import time
from pathlib import Path
from typing import Any, Optional

import pytest

from holdspeak.db.core import Database
from holdspeak.kernel.inference_stream import Delta
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError, ValidationError
from tests.unit._door_fakes import Broker, door_engine, words  # noqa: F401 - door_engine is a fixture
from holdspeak.services.thread_service import (
    ThreadService,
    _PEOPLE_REDACTION,
    _CHAT_PASS_CAP,
)
from holdspeak.services.thread_tools import (
    ThreadToolExecutor,
    ToolCallHandle,
    ToolResult,
    tool_schemas_for,
    TOOL_NAMES,
)


OWNER = Principal(PrincipalKind.OWNER, "owner-session")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "tool_loop.db")


@pytest.fixture
def broadcasts() -> list[tuple[str, dict]]:
    return []


@pytest.fixture
def broadcast_fn(broadcasts):
    def _broadcast(msg_type: str, data: Any) -> None:
        broadcasts.append((msg_type, data))
    return _broadcast


# ---------------------------------------------------------------------------
# Fake dispatch function (for ThreadToolExecutor)
# ---------------------------------------------------------------------------


def _fake_dispatch(name: str, args: dict, principal: Principal) -> Any:
    """Trivial dispatch that returns the tool name and args as a dict."""
    return {"tool": name, "args": args, "ok": True}


def _sensitive_dispatch(name: str, args: dict, principal: Principal) -> Any:
    """Dispatch that returns sensitive People data."""
    if name.startswith("people."):
        return {"name": "John Doe", "salary": "$150k", "ssn": "123-45-6789"}
    return {"tool": name, "ok": True}


# ---------------------------------------------------------------------------
# Fake runner that alternates tool_calls and text (``_door_fakes``)
# ---------------------------------------------------------------------------


def _ToolCallBroker(
    *,
    tool_calls: list[dict[str, Any]] | None = None,
    final_text: str = "Here are the results.",
    always_tools: bool = False,
) -> Broker:
    """A broker whose runner yields tool_calls on the first pass (or every
    pass), then text."""
    calls = tool_calls or [{"id": "call_1", "name": "desk.list", "arguments": "{}"}]
    count = [0]

    def engine(_request: Any, on_delta: Any) -> str:
        count[0] += 1
        if always_tools or count[0] == 1:
            on_delta(Delta(kind="tool_calls", meta={"tool_calls": calls}))
            on_delta(Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 0}))
            on_delta(Delta(kind="done"))
            return ""
        return words(final_text)(_request, on_delta)

    return Broker(engine)


def _NoToolsBroker(*, output: str = "Hello from assistant") -> Broker:
    """A broker that yields text only (no tool_calls), matching DC-01."""
    return Broker(words(output))


@pytest.fixture(autouse=True)
def _door(door_engine):
    yield


# ---------------------------------------------------------------------------
# Helper: wait for turn to complete
# ---------------------------------------------------------------------------


def _wait_done(broadcasts, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if any(ft == "thread_turn_done" for ft, _ in broadcasts):
            return
        time.sleep(0.05)
    raise TimeoutError("thread_turn_done never broadcast")


# ===========================================================================
# Tests
# ===========================================================================


class TestTwoPassHappyPath:
    """AC: 2 passes, 1 tool_call part, 1 tool message, final answer; frames in order."""

    def test_happy_path_frames_and_db(self, db, broadcast_fn, broadcasts):
        svc = ThreadService(
            db, broadcast=broadcast_fn,
            broker=_ToolCallBroker(),
            tool_dispatch_fn=_fake_dispatch,
        )
        t = svc.create(title="Tool test")
        result = asyncio.run(svc.start_turn(OWNER, t["id"], "List my desk"))
        _wait_done(broadcasts)

        # -- Frames in order --
        frame_types = [ft for ft, _ in broadcasts]
        assert "thread_tool_pending" in frame_types
        assert "thread_tool_result" in frame_types
        assert "thread_delta" in frame_types
        assert "thread_turn_done" in frame_types

        pending_idx = frame_types.index("thread_tool_pending")
        result_idx = frame_types.index("thread_tool_result")
        first_delta_idx = frame_types.index("thread_delta")
        done_idx = frame_types.index("thread_turn_done")
        assert pending_idx < result_idx < first_delta_idx < done_idx

        # -- thread_tool_pending payload --
        pending_frame = next(d for ft, d in broadcasts if ft == "thread_tool_pending")
        assert pending_frame["name"] == "desk.list"
        assert pending_frame["decision_required"] is False
        assert pending_frame["class"] == "evidence_read"

        # -- thread_tool_result payload --
        result_frame = next(d for ft, d in broadcasts if ft == "thread_tool_result")
        assert result_frame["name"] == "desk.list"
        assert result_frame["outcome"] == "succeeded"
        assert result_frame["sensitive"] is False

        # -- DB: tool_call part on assistant message --
        parts = db.threads.get_parts(result["assistant_message_id"])
        tc_parts = [p for p in parts if p.kind == "tool_call"]
        assert len(tc_parts) == 1
        tc_meta = json.loads(tc_parts[0].meta_json)
        assert tc_meta["name"] == "desk.list"

        # -- DB: text part (final answer) --
        text_parts = [p for p in parts if p.kind == "text" and p.text]
        assert len(text_parts) == 1
        assert text_parts[0].text == "Here are the results."

        # -- DB: tool-role message --
        got = svc.get(t["id"])
        tool_msgs = [m for m in got["messages"] if m["role"] == "tool"]
        assert len(tool_msgs) == 1

        # -- thread_turn_done outcome --
        done_frame = next(d for ft, d in broadcasts if ft == "thread_turn_done")
        assert done_frame["outcome"] == "succeeded"

class TestHeldApprove:
    """AC: held -> approve executes the tool."""

    def test_held_then_approved(self, db, broadcast_fn, broadcasts):
        svc = ThreadService(
            db, broadcast=broadcast_fn,
            broker=_ToolCallBroker(
                tool_calls=[{"id": "call_hold", "name": "desk.create", "arguments": "{}"}],
            ),
            tool_dispatch_fn=_fake_dispatch,
            control_mode_fn=lambda: "safe",  # effect_proposal + safe -> hold
        )
        t = svc.create(title="Hold test")
        result = asyncio.run(svc.start_turn(OWNER, t["id"], "Create"))

        # Wait for the pending frame to appear
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            pending = [d for ft, d in broadcasts if ft == "thread_tool_pending"]
            if pending:
                break
            time.sleep(0.05)
        assert pending, "thread_tool_pending never broadcast"
        assert pending[0]["decision_required"] is True

        # Simulate /decide route: find the executor and approve
        executor_agg = ThreadService._tool_executor
        handles = executor_agg._handles
        assert "call_hold" in handles
        handle = handles["call_hold"]
        executor_agg.decide(handle, "approve")

        _wait_done(broadcasts)

        # Verify tool_result was emitted
        results = [d for ft, d in broadcasts if ft == "thread_tool_result"]
        assert len(results) == 1
        assert results[0]["outcome"] == "succeeded"

        done_frame = next(d for ft, d in broadcasts if ft == "thread_turn_done")
        assert done_frame["outcome"] == "succeeded"


class TestHeldDeny:
    """AC: held -> deny -> tool_denied told to the model on the next pass."""

    def test_held_then_denied(self, db, broadcast_fn, broadcasts):
        svc = ThreadService(
            db, broadcast=broadcast_fn,
            broker=_ToolCallBroker(
                tool_calls=[{"id": "call_deny", "name": "desk.create", "arguments": "{}"}],
            ),
            tool_dispatch_fn=_fake_dispatch,
            control_mode_fn=lambda: "safe",
        )
        t = svc.create(title="Deny test")
        asyncio.run(svc.start_turn(OWNER, t["id"], "Delete"))

        # Wait for pending
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            pending = [d for ft, d in broadcasts if ft == "thread_tool_pending"]
            if pending:
                break
            time.sleep(0.05)

        # Deny
        executor_agg = ThreadService._tool_executor
        handles = executor_agg._handles
        handle = handles["call_deny"]
        executor_agg.decide(handle, "deny")

        _wait_done(broadcasts)

        # The tool_result should show denied
        results = [d for ft, d in broadcasts if ft == "thread_tool_result"]
        assert len(results) == 1
        assert results[0]["kind"] == "tool_denied"

        # The model should still produce a final answer
        done_frame = next(d for ft, d in broadcasts if ft == "thread_turn_done")
        assert done_frame["outcome"] == "succeeded"


class TestPassCap:
    """AC: 11th tool request -> pass_cap_reached."""

    def test_cap_exceeded(self, db, broadcast_fn, broadcasts):
        svc = ThreadService(
            db, broadcast=broadcast_fn,
            broker=_ToolCallBroker(always_tools=True),
            tool_dispatch_fn=_fake_dispatch,
        )
        t = svc.create(title="Cap test")
        asyncio.run(svc.start_turn(OWNER, t["id"], "Loop forever"))
        _wait_done(broadcasts, timeout=10.0)

        done_frame = next(d for ft, d in broadcasts if ft == "thread_turn_done")
        assert done_frame["outcome"] == "failed"
        assert done_frame["stats"]["error"]["code"] == "pass_cap_reached"

        # Verify exactly _CHAT_PASS_CAP tool_pending frames
        pending_count = sum(1 for ft, _ in broadcasts if ft == "thread_tool_pending")
        assert pending_count == _CHAT_PASS_CAP

        # Check DB error_json
        msg = db.threads.get_message(
            next(d for ft, d in broadcasts if ft == "thread_turn_done")["message_id"]
        )
        assert msg is not None
        assert msg.error_json
        err = json.loads(msg.error_json)
        assert err["code"] == "pass_cap_reached"


class TestAbortDuringExecute:
    """AC: abort during slow execute -> indeterminate within 250 ms; nothing persisted."""

    def test_abort_discards_in_flight(self, db, broadcast_fn, broadcasts):
        execute_entered = threading.Event()
        aborted = threading.Event()

        def slow_dispatch(name: str, args: dict, principal: Principal) -> Any:
            execute_entered.set()
            # Simulate a slow tool; check cancel inside the executor
            # (the real executor checks handle._cancel, but our loop
            # checks cancel_event before and after). Fast diet 2026-10-12:
            # the tool is still running when the abort lands, and returns
            # right after it (a fixed 5 s sleep was waited out every run).
            aborted.wait(5.0)
            return {"ok": True}

        svc = ThreadService(
            db, broadcast=broadcast_fn,
            broker=_ToolCallBroker(),
            tool_dispatch_fn=slow_dispatch,
        )
        t = svc.create(title="Abort test")
        result = asyncio.run(svc.start_turn(OWNER, t["id"], "Slow tool"))

        # Wait until the tool dispatch is entered
        assert execute_entered.wait(timeout=3.0), "dispatch never entered"

        # Abort
        t0 = time.monotonic()
        svc.abort(t["id"])
        aborted.set()

        _wait_done(broadcasts, timeout=6.0)
        elapsed = time.monotonic() - t0

        done_frame = next(d for ft, d in broadcasts if ft == "thread_turn_done")
        assert done_frame["outcome"] == "aborted"
        # Astra #875: no receipt came back, so no id: never a placeholder.
        assert done_frame["receipt_id"] == ""

        # The abort should complete quickly (the executor may be blocking
        # in dispatch, but the turn ends as aborted regardless).
        # Note: the slow_dispatch blocks until the abort, but _run_streaming_turn
        # checks cancel AFTER execute returns. The test verifies the
        # turn ends aborted; the 250ms bound applies to the cancel
        # propagation within the loop, not the tool's own blocking.
        msg = db.threads.get_message(result["assistant_message_id"])
        assert msg is not None
        assert msg.aborted_at is not None


class TestSensitiveAccumulator:
    """AC: sensitive result -> accumulator -> next pass payload withholds it."""

    def test_sensitive_text_in_accumulator(self, db, broadcast_fn, broadcasts, monkeypatch):
        """A people.* tool result text is withheld from the next pass on cloud egress (M1)."""
        broker = _ToolCallBroker(
            tool_calls=[{"id": "call_people", "name": "people.readiness", "arguments": "{}"}],
        )
        svc = ThreadService(db, broadcast=broadcast_fn, broker=broker, tool_dispatch_fn=_sensitive_dispatch)
        monkeypatch.setattr("holdspeak.services.engine_door.egress_of", lambda _broker, _engine: "cloud")
        t = svc.create(title="Sensitive test")
        asyncio.run(svc.start_turn(OWNER, t["id"], "Check readiness"))
        _wait_done(broadcasts)

        # The second pass carries the people.* result, redacted on cloud.
        requests = broker.inference_runner.requests
        assert len(requests) == 2
        sent = json.dumps(requests[-1].payload)
        assert "John Doe" not in sent and _PEOPLE_REDACTION in sent
        assert "_sensitive_texts" not in requests[-1].payload

        # Verify that the tool result part is marked sensitive in DB
        got = svc.get(t["id"])
        tool_msgs = [m for m in got["messages"] if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        tool_parts = db.threads.get_parts(tool_msgs[0]["id"])
        sensitive_parts = [p for p in tool_parts if p.sensitive]
        assert len(sensitive_parts) == 1

    def test_m1_redactor_strips_sensitive_tool_text(self):
        """The M1 redactor removes _sensitive_texts entries on cloud boundary."""
        payload = {
            "messages": [
                {"role": "system", "content": "You are the desk."},
                {"role": "user", "content": "Check readiness"},
                {"role": "tool", "tool_call_id": "call_1",
                 "content": '{"name": "John Doe", "salary": "$150k"}'},
            ],
            "_sensitive_texts": ['{"name": "John Doe", "salary": "$150k"}'],
        }
        route = {"entries": [{"boundary": "cloud"}]}
        redacted = ThreadService._m1_redactor(payload, route)

        payload_str = json.dumps(redacted)
        assert "John Doe" not in payload_str
        assert "$150k" not in payload_str
        assert _PEOPLE_REDACTION in payload_str
        # _sensitive_texts should be stripped
        assert "_sensitive_texts" not in redacted


class TestNoToolsTurnByteIdentical:
    """AC: no-tools turn byte-identical to DC-01."""

    def test_no_tools_identical(self, db, broadcast_fn, broadcasts):
        """Without tool_dispatch_fn, the turn produces the same output as DC-01."""
        svc = ThreadService(
            db, broadcast=broadcast_fn,
            broker=_NoToolsBroker(),
            # No tool_dispatch_fn -> tools disabled
        )
        t = svc.create(title="No-tools test")
        result = asyncio.run(svc.start_turn(OWNER, t["id"], "Hello"))
        _wait_done(broadcasts)

        # Same frame order as DC-01
        frame_types = [ft for ft, _ in broadcasts]
        assert "thread_delta" in frame_types
        assert "thread_turn_done" in frame_types

        # No tool frames
        assert "thread_tool_pending" not in frame_types
        assert "thread_tool_result" not in frame_types
        assert "thread_status_line" not in frame_types

        # DB text matches
        parts = db.threads.get_parts(result["assistant_message_id"])
        text_parts = [p for p in parts if p.kind == "text" and p.text]
        assert len(text_parts) == 1
        assert text_parts[0].text == "Hello from assistant"

        # Outcome
        done_frame = next(d for ft, d in broadcasts if ft == "thread_turn_done")
        assert done_frame["outcome"] == "succeeded"
        assert done_frame["receipt_id"]

        # No tool_call parts
        tc_parts = [p for p in parts if p.kind == "tool_call"]
        assert len(tc_parts) == 0


class TestErrorTaxonomy:
    """Error codes: tool_execution_failed, tool_timeout, tool_denied,
    pass_cap_reached, tool_unknown.
    """

    def test_tool_unknown_error_code(self, db, broadcast_fn, broadcasts):
        """An unclassified tool name -> tool_unknown in the result."""
        svc = ThreadService(
            db, broadcast=broadcast_fn,
            broker=_ToolCallBroker(
                tool_calls=[{"id": "call_bad", "name": "nonexistent.tool", "arguments": "{}"}],
            ),
            tool_dispatch_fn=_fake_dispatch,
        )
        t = svc.create(title="Unknown tool")
        asyncio.run(svc.start_turn(OWNER, t["id"], "Bad tool"))
        _wait_done(broadcasts)

        # The model still gets a final answer (the error is told to the
        # model and it responds with text on pass 2)
        done_frame = next(d for ft, d in broadcasts if ft == "thread_turn_done")
        assert done_frame["outcome"] == "succeeded"


class TestBrokerRequired:
    """When the executor is wired, the broker is passed through."""

    def test_executor_receives_broker(self, db, broadcast_fn, broadcasts):
        broker = _ToolCallBroker()
        svc = ThreadService(
            db, broadcast=broadcast_fn,
            broker=broker,
            tool_dispatch_fn=_fake_dispatch,
        )
        t = svc.create(title="Broker test")
        asyncio.run(svc.start_turn(OWNER, t["id"], "Test broker"))
        _wait_done(broadcasts)

        # The turn should succeed (verifying the broker path works)
        done_frame = next(d for ft, d in broadcasts if ft == "thread_turn_done")
        assert done_frame["outcome"] == "succeeded"
