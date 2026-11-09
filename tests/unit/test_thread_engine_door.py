"""The chat turn through the one engine door (handover Part IV item 2).

Each pass of a turn is one door job (``engine_door.run_stream``) on the engine
the chat assignment names; a turn that fails waits in Needs you with Retry
(kind ``thread.turn``), like every other door job, and Retry runs the
thread's last turn again.  The real kernel broker runs; only the engine is
replaced.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.kernel.inference_stream import Delta
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import engine_door, thread_turns
from holdspeak.services.errors import ServiceError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.needs_you_membership import engine_items
from holdspeak.services.thread_service import ThreadService
from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile, _result_claim

OWNER = Principal(PrincipalKind.OWNER, "thread-door-owner")
ANSWER = "Feedback on her design doc, due Friday."


class _Engine:
    down = True
    calls = 0
    active_provider, active_model = "fixture", "chat-model"

    def run_prompt_stream(self, **_kwargs: Any):
        _Engine.calls += 1
        if _Engine.down:
            raise RuntimeError("connection refused by /Users/someone/model.gguf")
        yield Delta(kind="text", text=ANSWER)
        yield Delta(kind="done")


@pytest.fixture
def broker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    db = Database(tmp_path / "thread-door.db")
    _profile(db, "chat", claims=("language", _result_claim("chat.turn")))
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-chat", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": "chat", "profile_revision": 1}],
    })
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda *_a, **_k: _Engine()
    _Engine.down, _Engine.calls = True, 0
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    return broker


def _settled(db: Database, message_id: str) -> Any:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if thread_turns.get(message_id) is None and not db.threads.get_message(message_id).streaming:
            return db.threads.get_message(message_id)
        time.sleep(0.02)
    raise TimeoutError("the turn never settled")


def test_a_turn_runs_through_the_door_and_the_receipt_names_its_engine(broker: Any) -> None:
    _Engine.down = False
    svc = ThreadService(broker.database, broadcast=lambda *_: None, broker=broker)
    thread_id = svc.create(title="Mira")["id"]
    ids = asyncio.run(svc.start_turn(OWNER, thread_id, "What do I owe Mira?"))
    msg = _settled(broker.database, ids["assistant_message_id"])
    assert msg.error_json in ("", None)
    with broker.database._connection() as conn:
        native = conn.execute("SELECT native_id FROM kernel_operations WHERE operation_id=?",
                              (msg.receipt_id,)).fetchone()["native_id"]
    assert native.startswith("door_")  # a tracked door job: the runner's receipt is the record
    assert msg.egress_receipt_id == msg.receipt_id and msg.egress_scope
    assert engine_door.failure_items(broker.database) == []


def test_a_turn_with_the_engine_off_is_a_needs_you_row_with_retry(broker: Any) -> None:
    svc = ThreadService(broker.database, broadcast=lambda *_: None, broker=broker)
    thread_id = svc.create(title="Mira")["id"]
    ids = asyncio.run(svc.start_turn(OWNER, thread_id, "What do I owe Mira?"))
    failed = _settled(broker.database, ids["assistant_message_id"])
    assert failed.error_json and "/Users" not in failed.error_json

    (item,) = engine_door.failure_items(broker.database)
    assert (item["job"], item["kind"], item["retry_key"]) == ("chat.turn", "thread.turn", thread_id)
    assert item["words"] == "your message" and item["can_retry"] is True
    assert item["open_ref"] == f"thread:{thread_id}"
    (row,) = engine_items([item])
    assert row["engine"]["verbs"][0]["body"] == {"kind": "thread.turn", "key": thread_id}
    assert "/Users" not in str(row)

    _Engine.down = False
    again = engine_door.retry(OWNER, "thread.turn", item["retry_key"])
    answered = _settled(broker.database, again["assistant_message_id"])
    assert answered.error_json in ("", None)
    assert engine_door.failure_items(broker.database) == []


def test_a_turn_with_no_engine_assigned_is_refused_before_it_runs(broker: Any, monkeypatch) -> None:
    def no_engine(*_a: Any, **_k: Any) -> Any:
        raise engine_door.EngineDoorError("no_engine", "No engine is assigned to chat.turn")

    monkeypatch.setattr(engine_door, "engine_for", no_engine)
    svc = ThreadService(broker.database, broadcast=lambda *_: None, broker=broker)
    thread_id = svc.create(title="Mira")["id"]
    with pytest.raises(ServiceError) as refused:
        asyncio.run(svc.start_turn(OWNER, thread_id, "What do I owe Mira?"))
    assert refused.value.context["reason"] == "no_engine"
    assert _Engine.calls == 0


# ── A Stop is his decision, not a failure ───────────────────────────────


def test_a_stopped_turn_leaves_no_needs_you_row(broker: Any) -> None:
    import threading

    started, release = threading.Event(), threading.Event()

    class _Slow:
        active_provider, active_model = "fixture", "chat-model"

        def run_prompt_stream(self, **_kwargs: Any):
            yield Delta(kind="text", text="Feedback on ")
            started.set()
            release.wait(5)
            yield Delta(kind="text", text="her design doc.")
            yield Delta(kind="done")

    broker.inference_runner._engine_factory = lambda *_a, **_k: _Slow()
    svc = ThreadService(broker.database, broadcast=lambda *_: None, broker=broker)
    thread_id = svc.create(title="Mira")["id"]
    ids = asyncio.run(svc.start_turn(OWNER, thread_id, "What do I owe Mira?"))
    assert started.wait(5)
    assert svc.abort(thread_id)["aborted"] is True
    release.set()
    stopped = _settled(broker.database, ids["assistant_message_id"])
    assert stopped.aborted_at is not None
    with broker.database._connection() as conn:
        (signals,) = conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.cancel'").fetchone()
    assert signals == 1  # his Stop reached the runner as its cancel signal
    assert engine_door.failure_items(broker.database) == []


def test_a_stop_then_an_engine_off_turn_is_exactly_one_row(broker: Any) -> None:
    """Two turns in two threads: the first is stopped, the second fails on
    its own (engine off). Only the second waits in Needs you, with Retry."""
    import threading

    started, release = threading.Event(), threading.Event()

    class _SlowThenOff:
        active_provider, active_model = "fixture", "chat-model"

        def run_prompt_stream(self, **_kwargs: Any):
            if started.is_set():
                raise RuntimeError("connection refused")
            yield Delta(kind="text", text="Feedback on ")
            started.set()
            release.wait(5)
            yield Delta(kind="done")

    broker.inference_runner._engine_factory = lambda *_a, **_k: _SlowThenOff()
    svc = ThreadService(broker.database, broadcast=lambda *_: None, broker=broker)
    stopped_thread = svc.create(title="Mira")["id"]
    first = asyncio.run(svc.start_turn(OWNER, stopped_thread, "What do I owe Mira?"))
    assert started.wait(5)
    svc.abort(stopped_thread)
    release.set()
    _settled(broker.database, first["assistant_message_id"])
    failed_thread = svc.create(title="Tomás")["id"]
    second = asyncio.run(svc.start_turn(OWNER, failed_thread, "And Tomás?"))
    _settled(broker.database, second["assistant_message_id"])
    (item,) = engine_door.failure_items(broker.database)
    assert (item["retry_key"], item["can_retry"]) == (failed_thread, True)
