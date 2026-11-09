"""Ask through the one engine door (handover Part IV item 2).

An answer is one door job (``ask.answer``): the engine the Answers
assignment names, one receipt, and a failure is one Needs-you row with
Retry (kind ``ask``), like every other door job (``test_engine_failures``).
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import engine_door
from holdspeak.services.ask_service import AskService
from holdspeak.services.errors import ServiceError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.needs_you_membership import engine_items
from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile

OWNER = Principal(PrincipalKind.OWNER, "ask-owner")
QUESTION = "What do I owe Mira this week?"


class _Engine:
    down = True
    calls = 0

    def run_prompt(self, **_kwargs: Any) -> str:
        _Engine.calls += 1
        if _Engine.down:
            raise RuntimeError("connection refused by /Users/someone/model.gguf")
        return "Feedback on her design doc, due Friday."


def assign_answers(db: Database, factory: Any = None, profile: str = "answers") -> Any:
    """The Answers assignment (``ask.answer``) on one fixture profile; with
    ``factory``, the runner builds that engine. Returns the kernel broker."""
    _profile(db, profile)
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": f"assign-ask-{profile}", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "ask.answer"},
        "entries": [{"profile_id": profile, "profile_revision": 1}],
    })
    broker = _configure(db)
    if factory is not None:
        broker.inference_runner._engine_factory = lambda *_a, **_k: factory()
    return broker


@pytest.fixture
def broker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    db = Database(tmp_path / "ask-door.db")
    broker = assign_answers(db, _Engine)
    _Engine.down, _Engine.calls = True, 0
    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    return broker


def test_an_answer_runs_through_the_door_and_the_receipt_names_its_engine(broker: Any) -> None:
    _Engine.down = False
    result = asyncio.run(AskService(broker.database, broker=broker).ask(OWNER, QUESTION, invocation_id="ask_" + "1" * 32))
    assert result["output"] == "Feedback on her design doc, due Friday."
    assert result["invocation_id"] == "ask_" + "1" * 32
    assert result["profile_id"] == "answers"
    assert result["route_execution_receipt"]["execution_id"] == result["operation_id"]
    assert result["route"]["receipt"] == result["operation_id"] and result["egress"]["scope"]
    with broker.database._connection() as conn:
        native = conn.execute("SELECT native_id FROM kernel_operations WHERE operation_id=?",
                              (result["operation_id"],)).fetchone()["native_id"]
        kept = conn.execute("SELECT invocation_id FROM ask_results").fetchone()
    assert native.startswith("door_") and "_ask_" + "1" * 32 + "_" in native  # the runner id carries the Ask id
    assert kept["invocation_id"] == "ask_" + "1" * 32   # the kept answer is under the Ask's own id
    assert engine_door.failure_items(broker.database) == []


def test_ask_with_the_engine_off_is_a_needs_you_row_with_retry(broker: Any) -> None:
    service = AskService(broker.database, broker=broker)
    with pytest.raises(ServiceError) as refused:
        asyncio.run(service.ask_in_thread(OWNER, QUESTION))
    assert refused.value.context["reason"] in {"did_not_answer", "not_reachable"}

    (item,) = engine_door.failure_items(broker.database)
    assert item["job"] == "ask.answer" and item["kind"] == "ask"
    assert item["words"] == "your question" and item["can_retry"] is True
    assert item["open_ref"] == "window:ask:desk"   # a first Ask that failed keeps no thread
    (row,) = engine_items([item])
    assert row["title"].startswith("answers could not run your question · ")
    assert row["engine"]["verbs"][0]["body"] == {"kind": "ask", "key": f"|{QUESTION}"}
    assert "/Users" not in str(row)

    _Engine.down = False
    answered = engine_door.retry(OWNER, "ask", item["retry_key"])
    assert answered["output"] == "Feedback on her design doc, due Friday."
    assert answered["thread_id"]
    assert engine_door.failure_items(broker.database) == []


def test_a_stop_reaches_the_door_run(broker: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.services.ask_service as ask_module

    stopped: list[str] = []
    monkeypatch.setitem(ask_module._DOOR_IDS, "ask_" + "2" * 32, "door_x_y_z_ask_" + "2" * 32)
    monkeypatch.setattr(broker.inference_runner, "cancel", lambda iid: stopped.append(iid) or "cancel_requested")
    AskService(broker.database, broker=broker).cancel(OWNER, "ask_" + "2" * 32)
    assert stopped == ["door_x_y_z_ask_" + "2" * 32]


def test_a_stopped_answer_leaves_no_needs_you_row(broker: Any) -> None:
    """His Stop is a decision: the runner's receipt says cancelled and
    nothing waits in Needs you (only an answer that failed on its own does)."""
    import threading

    started, release = threading.Event(), threading.Event()

    class _Slow:
        def run_prompt(self, **_kwargs: Any) -> str:
            started.set()
            release.wait(5)
            return "Too late."

        def cancel(self) -> str:
            release.set()
            return "cancelled"

    broker.inference_runner._engine_factory = lambda *_a, **_k: _Slow()
    service = AskService(broker.database, broker=broker)
    invocation_id = "ask_" + "3" * 32
    outcome: dict[str, Any] = {}

    def ask() -> None:
        try:
            outcome["result"] = asyncio.run(service.ask(OWNER, QUESTION, invocation_id=invocation_id))
        except ServiceError as exc:
            outcome["error"] = exc

    runner = threading.Thread(target=ask)
    runner.start()
    assert started.wait(5)
    service.cancel(OWNER, invocation_id)
    release.set()
    runner.join(10)
    assert "error" in outcome  # the answer was stopped, not given
    assert engine_door.failure_items(broker.database) == []
