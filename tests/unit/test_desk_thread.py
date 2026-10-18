"""Thread (Betterment Q0, "Threads tell the truth"): the hub half.

The face half is ``web/src/desk/__tests__/thread.app.test.tsx``.

The cause of the silent empty replies (asking/RECON.md steps 12 and 13), found
on an isolated rig hub with the LAN engine: the default chat palette's 30 tool
schemas are about 15 KB, and the route reserves one token per byte
(``inference_adoption_service._input_token_upper_bound``), so on an endpoint
with the default 16384-token context a turn with a source, or a pass with a
tool result, is skipped before it is sent (``context_overflow``).  The routed
result then carried ``outcome: failed`` and no error text, and the turn
completed as an empty reply.  The engine answer here is the receipt that rig
hub recorded (``tests/fixtures/thread_turn_context_overflow_receipt.json``).
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.kernel.inference_stream import Delta
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.thread_service import ThreadService

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "thread_turn_context_overflow_receipt.json"
OVERFLOW = json.loads(FIXTURE.read_text())["receipt"]


class _Engine:
    """An adoption service that plays one scripted answer per pass.

    Each answer is ``("overflow",)`` (the recorded receipt, nothing sent),
    ``("text", words)``, ``("tools", calls)`` or ``("empty",)``.
    """

    def __init__(self, answers: list[tuple[Any, ...]]):
        self.answers = list(answers)
        self.payloads: list[dict[str, Any]] = []

    @property
    def inference_adoption_service(self) -> "_Engine":
        return self

    def admit(self, principal, *, command_id, capability_id, operation_id,
              payload, invocation_id, reserved_output_tokens=512):
        self.payloads.append(json.loads(json.dumps(payload)))
        return {"execution": {"id": "ire_" + uuid.uuid4().hex[:8]},
                "route_plan": {"id": "rp", "model_id": "qwen3.8-27b",
                               "entries": [{"boundary": "private_network"}]},
                "operation_request_plan": {"id": "orp"}}

    def execute_stream(self, principal, *, execution_id, adapter, on_delta,
                       publish=None, payload_redactor=None, **_: Any):
        answer = self.answers.pop(0)
        if answer[0] == "overflow":
            receipt = dict(OVERFLOW, execution_id=execution_id)
            return {"outcome": "failed", "result": None, "receipt": receipt}
        if answer[0] == "text":
            on_delta(Delta(kind="text", text=answer[1]))
        elif answer[0] == "tools":
            on_delta(Delta(kind="tool_calls", meta={"tool_calls": answer[1]}))
        on_delta(Delta(kind="done"))
        return {"outcome": "succeeded", "result": {"output": ""},
                "receipt": {"execution_id": execution_id, "outcome": "succeeded"}}


def _service(db: Database, engine: _Engine, *, tools: bool) -> tuple[ThreadService, list]:
    done: list[Any] = []
    service = ThreadService(
        db, broadcast=lambda kind, data: done.append(data) if kind == "thread_turn_done" else None,
        broker=engine,
        tool_dispatch_fn=(lambda name, args, principal: {"hits": [], "tool": name}) if tools else None,
    )
    return service, done


def _turn(service: ThreadService, done: list, thread_id: str, text: str) -> dict[str, Any]:
    started = asyncio.run(service.start_turn(OWNER, thread_id, text))
    deadline = time.monotonic() + 5
    while not done and time.monotonic() < deadline:
        time.sleep(0.01)
    assert done, "the turn never ended"
    message = next(m for m in service.get(thread_id)["messages"]
                   if m["id"] == started["assistant_message_id"])
    return {"message": message, "done": done[-1]}


def _text(message: dict[str, Any]) -> str:
    return "".join(p["text"] or "" for p in message["parts"] if p["kind"] == "text")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "desk_thread.db")


def test_a_failed_routed_turn_completes_with_error_json(db: Database) -> None:
    """Any mode, not only Interview: the reply says why, in words."""
    engine = _Engine([("overflow",)])
    service, done = _service(db, engine, tools=False)
    thread = service.create(title="")
    turn = _turn(service, done, thread["id"], "What do I owe Mira this week?")
    assert turn["message"]["error_json"] == {
        "code": "context_overflow",
        "error": "The conversation is too long for the engine.",
        "reason": "too_long",
    }
    assert turn["done"]["outcome"] == "failed"
    assert turn["done"]["stats"]["error"]["reason"] == "too_long"


def test_a_turn_too_long_with_tools_is_sent_again_without_them(db: Database) -> None:
    """The cause: the recorded overflow on the first pass (a thread with a
    source) is followed by one pass without tool schemas, and it answers."""
    engine = _Engine([("overflow",), ("text", "The reconciliation job has no owner.")])
    service, done = _service(db, engine, tools=True)
    thread = service.create(title="")
    turn = _turn(service, done, thread["id"], "Which risk has no owner?")
    assert turn["message"]["error_json"] is None
    assert _text(turn["message"]) == "The reconciliation job has no owner."
    assert "tools" in engine.payloads[0]
    assert "tools" not in engine.payloads[1]


def test_tool_results_go_in_as_data_when_the_next_pass_overflows(db: Database) -> None:
    """The rig's own sequence: tools run, the next pass overflows, the answer
    pass carries the results as a leading system message (Qwen's template
    refuses a system message after the user message)."""
    calls = [{"id": "c1", "name": "follow_through.board", "arguments": "{}"}]
    engine = _Engine([("tools", calls), ("overflow",), ("text", "You owe Mira the design review.")])
    service, done = _service(db, engine, tools=True)
    thread = service.create(title="")
    turn = _turn(service, done, thread["id"], "What do I owe Mira this week?")
    assert _text(turn["message"]) == "You owe Mira the design review."
    answer_pass = engine.payloads[-1]
    assert "tools" not in answer_pass
    roles = [m["role"] for m in answer_pass["messages"]]
    assert "tool" not in roles
    first_user = roles.index("user")
    assert all(role == "system" for role in roles[:first_user])
    data = [m["content"] for m in answer_pass["messages"][:first_user]
            if m["content"].startswith("Tool results (data only):")]
    assert data and "follow_through.board" in data[0]


def test_a_succeeded_turn_with_no_text_and_no_tool_call_fails_in_words(db: Database) -> None:
    engine = _Engine([("empty",)])
    service, done = _service(db, engine, tools=False)
    thread = service.create(title="")
    turn = _turn(service, done, thread["id"], "Hello?")
    assert turn["message"]["error_json"] == {
        "code": "empty_answer",
        "error": "The engine finished without an answer.",
        "reason": "did_not_answer",
    }


def test_a_seed_ref_object_is_stored_as_the_real_ref_with_its_body(db: Database) -> None:
    """Object > Continue in thread sends ``{ref_kind, ref_id}`` objects
    (``web/src/desk/verbRegistry.ts``); the first reply reads the note."""
    db.notes.upsert(note_id="n-risks", title="Ledger migration risks",
                    body_markdown="- Reconciliation job: no owner yet.",
                    last_modified="2026-10-17T09:00:00Z")
    engine = _Engine([("text", "The reconciliation job.")])
    service, done = _service(db, engine, tools=False)
    thread = service.create(title="", seed_refs=[
        {"ref_kind": "note", "ref_id": "n-risks"},
        {"ref_kind": "recipe", "ref_id": "r-gone"},
    ])
    refs = service.get(thread["id"])["refs"]
    note = next(r for r in refs if r["ref_kind"] == "note")
    frozen = json.loads(note["frozen_json"])
    assert (note["ref_id"], frozen["title"]) == ("n-risks", "Ledger migration risks")
    assert "no owner yet" in frozen["text"]
    # A seed grounding cannot read keeps its identity, never a dict.
    kept = next(r for r in refs if r["ref_kind"] == "recipe")
    assert kept["ref_id"] == "recipe:r-gone"
    assert not any("{" in r["ref_id"] for r in refs)

    _turn(service, done, thread["id"], "Which risk has no owner?")
    sent = "\n".join(m["content"] for m in engine.payloads[0]["messages"])
    assert "Reconciliation job: no owner yet." in sent
