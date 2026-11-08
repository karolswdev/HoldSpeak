"""HS-S34: an observer detaches from a Thread turn; cancellation and
persisted completion stay distinct terminal facts.

The real ``ThreadService`` runs each turn with a gated fake engine (the turn
waits for the test's ``release``). The observer is ``ask_desk.run_loop`` (the
Ask and the Calls wait on it) and the Ask's ``ask_text`` tap.

Case A: the owner cancels. A cancel before the turn settles stops it; a
cancel after the answer is saved is refused and the answer stays complete.
Case B: the turn is saved while the observer is away; the next read gives
the answer, and no observer or turn stays registered (also when a terminal
frame fails to send).
Case C: a late answer after detach is saved on the turn and read later; it
is never sent to the detached observer.
"""
from __future__ import annotations

import asyncio
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.kernel.inference_stream import Delta
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import ask_desk, thread_turns
from holdspeak.services.thread_service import ThreadService

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
ANSWER = "The late answer is here."


class _GatedEngine:
    """An adoption service whose one pass waits for ``release``."""

    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()

    @property
    def inference_adoption_service(self) -> "_GatedEngine":
        return self

    def admit(self, principal, *, command_id, capability_id, operation_id, payload, invocation_id,
              reserved_output_tokens=512):
        return {
            "execution": {"id": f"exec_{uuid.uuid4().hex[:8]}"},
            "route_plan": {"id": "rp_test", "egress_scope": "same_device", "model_id": "test-model"},
            "operation_request_plan": {"id": "orp_test"},
        }

    def execute_stream(self, principal, *, execution_id, adapter, on_delta, publish=None, payload_redactor=None):
        self.started.set()
        assert self.release.wait(5.0), "the test never released the engine"
        on_delta(Delta(kind="text", text=ANSWER))
        on_delta(Delta(kind="usage", meta={"prompt_tokens": 3, "completion_tokens": 5}))
        on_delta(Delta(kind="done"))
        return {"outcome": "succeeded", "result": {"output": ANSWER},
                "receipt": {"id": "receipt_gated", "outcome": "succeeded"}}


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "turns.db")


@pytest.fixture(autouse=True)
def _no_live_turns():
    yield
    for turn in thread_turns.live():
        thread_turns.cancel(turn.message_id)


def _wait(predicate, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise TimeoutError("condition not met")


async def _await(predicate, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        await asyncio.sleep(0.02)
    raise TimeoutError("condition not met")


def _service(db: Database, engine: _GatedEngine, frames: list[tuple[str, Any]], hook=None) -> ThreadService:
    def broadcast(kind: str, data: Any = None, *args: Any, **kwargs: Any) -> None:
        frames.append((kind, data))
        if hook is not None:
            hook(kind, data)

    return ThreadService(db, broadcast=broadcast, broker=engine)


def _assistant_message(db: Database, thread_id: str) -> Any:
    rows = [m for m in db.threads.list_path(thread_id) if m.role == "assistant"]
    assert len(rows) == 1
    return db.threads.get_message(rows[0].id)


# ── Case A: the owner cancels ───────────────────────────────────────────────


def test_a_cancel_before_the_turn_settles_stops_it(db) -> None:
    engine, frames = _GatedEngine(), []
    svc = _service(db, engine, frames)
    thread_id = svc.create(title="Cancel")["id"]

    async def scenario() -> dict[str, Any]:
        task = asyncio.ensure_future(ask_desk.run_loop(
            svc, OWNER, thread_id=thread_id, question="Go", refs=[], invocation_id="inv-a1"))
        await _await(engine.started.is_set)
        assert ask_desk.cancel_loop("inv-a1") is True
        engine.release.set()
        return await asyncio.wait_for(task, 5.0)

    turn = asyncio.run(scenario())
    assert turn["aborted"] is True
    assert turn["state"] == "cancelled"
    message = _assistant_message(db, thread_id)
    assert message.aborted_at is not None and not message.streaming
    assert thread_turns.read(db.threads, turn["assistant_message_id"])["state"] == "cancelled"
    assert thread_turns.live() == []


def test_a_cancel_after_the_answer_is_saved_is_refused(db) -> None:
    """Before HS-S34 a cancel in the window between the saved answer and the
    turn's clean-up said "stopped" (``cancel_loop`` True, ``abort`` aborted)
    for a turn that had completed."""
    engine, frames = _GatedEngine(), []
    late_cancels: list[Any] = []
    holder: dict[str, ThreadService] = {}

    def hook(kind: str, data: Any) -> None:
        if kind == "thread_turn_done":
            late_cancels.append(ask_desk.cancel_loop("inv-a2"))
            late_cancels.append(holder["svc"].abort(data["thread_id"])["aborted"])

    svc = _service(db, engine, frames, hook)
    holder["svc"] = svc
    thread_id = svc.create(title="Late cancel")["id"]
    engine.release.set()
    turn = asyncio.run(asyncio.wait_for(ask_desk.run_loop(
        svc, OWNER, thread_id=thread_id, question="Go", refs=[], invocation_id="inv-a2"), 5.0))

    assert late_cancels == [False, False]
    assert turn["aborted"] is False
    assert turn["state"] == "completed"
    assert turn["text"] == ANSWER
    message = _assistant_message(db, thread_id)
    assert message.aborted_at is None and not message.streaming


# ── Case B: saved while the observer was away ───────────────────────────────


def test_b_a_turn_saved_while_the_observer_was_away_reads_complete(db) -> None:
    engine, frames = _GatedEngine(), []
    svc = _service(db, engine, frames)
    thread_id = svc.create(title="Away")["id"]

    async def scenario() -> None:
        task = asyncio.ensure_future(ask_desk.run_loop(
            svc, OWNER, thread_id=thread_id, question="Go", refs=[], invocation_id="inv-b1"))
        await _await(engine.started.is_set)
        task.cancel()  # the observer goes away (a call hangs up, a page closes)
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    message_id = _assistant_message(db, thread_id).id
    assert thread_turns.observers(message_id) == []  # detached, not left registered
    assert "inv-b1" not in ask_desk._LOOP_TURNS
    engine.release.set()
    _wait(lambda: not thread_turns.live())

    read = thread_turns.read(db.threads, message_id)
    assert read["state"] == "completed"
    assert read["text"] == ANSWER
    assert not _assistant_message(db, thread_id).aborted_at


def test_b_a_failed_terminal_frame_leaves_no_turn_registered(db) -> None:
    """Before HS-S34 a raise in a terminal frame skipped the clean-up: the
    turn stayed in ``_active_turns`` and its observer waited 15 minutes for
    an answer saved already."""
    engine, frames = _GatedEngine(), []

    def hook(kind: str, data: Any) -> None:
        if kind == "thread_turn_done":
            raise RuntimeError("a subscriber is gone")

    svc = _service(db, engine, frames, hook)
    thread_id = svc.create(title="Frame fails")["id"]
    engine.release.set()
    turn = asyncio.run(asyncio.wait_for(ask_desk.run_loop(
        svc, OWNER, thread_id=thread_id, question="Go", refs=[], invocation_id="inv-b2"), 5.0))

    assert turn["state"] == "completed"
    assert turn["text"] == ANSWER
    assert thread_turns.live() == []
    assert ThreadService._tool_executor._executors.get(turn["assistant_message_id"]) is None


def test_b_detach_is_explicit_and_idempotent(db) -> None:
    engine, frames = _GatedEngine(), []
    svc = _service(db, engine, frames)
    thread_id = svc.create(title="Detach")["id"]
    ids = asyncio.run(svc.start_turn(OWNER, thread_id, "Go"))
    message_id = ids["assistant_message_id"]
    observer = thread_turns.observe(message_id)
    assert observer is not None and observer.attached
    assert thread_turns.observers(message_id) == [observer]
    observer.detach()
    observer.detach()
    assert not observer.attached
    assert thread_turns.observers(message_id) == []
    engine.release.set()
    _wait(lambda: not thread_turns.live())
    assert thread_turns.read(db.threads, message_id)["state"] == "completed"
    assert thread_turns.observe(message_id) is None  # a settled turn is read, not observed


# ── Case C: a late answer after detach ──────────────────────────────────────


def test_c_a_late_answer_is_saved_and_never_sent_to_the_detached_ask(db) -> None:
    """Before HS-S34 the Ask's tap stayed on the turn after the Ask detached:
    the late answer went out as ``ask_text`` frames of an Ask that had
    ended."""
    from holdspeak.services.ask_service import AskService

    engine, frames = _GatedEngine(), []
    svc = _service(db, engine, frames)
    sent: list[dict[str, Any]] = []
    ask = object.__new__(AskService)
    ask._db = db
    ask._thread_service = lambda **_kw: svc
    ask._progress = None
    ask._text = sent.append

    async def scenario() -> None:
        task = asyncio.ensure_future(ask._ask_in_loop(
            OWNER, "Go", None, thread_id="", context=[], invocation_id="inv-c1"))
        await _await(engine.started.is_set)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    engine.release.set()
    _wait(lambda: not thread_turns.live())

    assert sent == []  # nothing reached the detached Ask
    assert any(kind == "thread_turn_done" for kind, _ in frames)  # the desk chat still hears it
    thread_id = next(t.id for t in db.threads.list())
    message = _assistant_message(db, thread_id)
    read = thread_turns.read(db.threads, message.id)
    assert read["state"] == "completed" and read["text"] == ANSWER
    answer = [m for m in svc.get(thread_id)["messages"] if m["role"] == "assistant"]
    assert answer and answer[0]["id"] == message.id
