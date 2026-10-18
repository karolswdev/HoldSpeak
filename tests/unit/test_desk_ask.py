"""The Ask window over a thread (Betterment Q4, "One Ask window").

The hub half. The face half is ``web/src/desk/__tests__/askWindow.app.test.tsx``.

DECISIONS #14: every Ask is kept as a thread, with no Keep or Bin.  The Ask
window posts ``/api/ask`` with ``thread: true`` (a new thread) or a
``thread_id`` (a follow-up); the hub answers with today's Ask grounding and
writes the exchange: one user and one assistant message, the question's About
(``origin='reference'``) and what the answer looked at (``origin='relevance'``).
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.unit.test_desk_ask_ai import OWNER, _assign, _seed_routes, hub  # noqa: F401  (fixture)


class _RecordingEngine:
    """Answers each call in turn and keeps every prompt it was sent."""

    active_provider = "fixture"

    def __init__(self, model: str, answers: list[Any], seen: list[str]) -> None:
        self.active_model = model
        self._answers = answers
        self._seen = seen

    def _next(self, kw: dict[str, Any]) -> str:
        self._seen.append(json.dumps(kw, default=str))
        answer = self._answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    def run_prompt_stream(self, **kw: Any) -> Any:
        from holdspeak.kernel.inference_stream import Delta

        yield Delta(kind="text", text=self._next(kw))
        yield Delta(kind="usage", meta={"prompt_tokens": 20, "completion_tokens": 20})
        yield Delta(kind="done")

    def run_prompt(self, **kw: Any) -> str:
        return self._next(kw)


def _ask_app(hub: Any, answers: list[Any]) -> tuple[TestClient, list[str]]:
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.primitives.ask import build_ask_router
    from holdspeak.web.routes.threads import build_threads_router

    _seed_routes(hub.db)
    hub.broker.inference_adoption_service.migrate_legacy_config(OWNER, SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="glass-lan"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="glass-lan"))))
    _assign(hub.db, "ask.answer", ["glass-lan"], "ask-window-lan")
    seen: list[str] = []
    hub.broker.inference_runner._engine_factory = lambda rev, **_kw: _RecordingEngine(str(rev.model), answers, seen)
    app = FastAPI()
    ctx = WebContext(get_state=lambda: {})
    app.include_router(build_ask_router(ctx))
    app.include_router(build_threads_router(ctx))
    return TestClient(app), seen


def _note(hub: Any) -> None:
    hub.db.notes.upsert(
        note_id="n-mira", title="1:1 with Mira",
        body_markdown="Feedback on her cutover design doc is due Friday.",
    )


ABOUT = [{"id": "n-mira", "kind": "note", "title": "1:1 with Mira", "ref": "note:n-mira"}]


def test_an_ask_is_kept_as_a_thread_with_one_question_and_one_answer(hub) -> None:
    _note(hub)
    client, _seen = _ask_app(hub, ["You owe Mira feedback on her cutover design doc, due Friday."])

    body = client.post("/api/ask", json={
        "prompt": "What do I owe Mira this week?", "lens": "Ask", "context": ABOUT, "thread": True,
    }).json()

    tid = body["thread_id"]
    assert tid.startswith("th_")
    assert body["output"].startswith("You owe Mira")
    assert {"ref": "note:n-mira", "title": "1:1 with Mira"} in body["looked_at"]
    thread = client.get(f"/api/threads/{tid}").json()
    assert thread["title"] == "What do I owe Mira this week?"
    roles = [m["role"] for m in thread["messages"]]
    assert roles == ["user", "assistant"]
    texts = ["".join(p["text"] or "" for p in m["parts"] if p["kind"] == "text") for m in thread["messages"]]
    assert texts == ["What do I owe Mira this week?", body["output"]]
    question_id, answer_id = (m["id"] for m in thread["messages"])
    refs = {(r["message_id"], r["origin"], f"{r['ref_kind']}:{r['ref_id']}") for r in thread["refs"]}
    # About on the question, Looked at on the answer.
    assert (question_id, "reference", "note:n-mira") in refs
    assert (answer_id, "relevance", "note:n-mira") in refs
    assert all(json.loads(r["frozen_json"])["title"] == "1:1 with Mira"
               for r in thread["refs"] if r["ref_id"] == "n-mira")


def test_a_two_turn_thread_is_recorded_for_the_face(hub, tmp_path) -> None:
    """The recorded hub answers the face replays (``ask.thread.wire.json``,
    ``web/src/desk/__tests__/ask.app.test.tsx``): an Ask about a note, its
    follow-up, the thread read and the Recent list."""
    from pathlib import Path

    from tests.unit.test_desk_speak import _record

    _note(hub)
    client, _seen = _ask_app(hub, [
        "You owe Mira feedback on her cutover design doc, due Friday.",
        "Make it a task for Friday, and tell her on Thursday.",
    ])
    first = client.post("/api/ask", json={
        "prompt": "What do I owe Mira this week?", "lens": "Summarize", "context": ABOUT, "thread": True,
    }).json()
    second = client.post("/api/ask", json={
        "prompt": "When should I tell her?", "lens": "Summarize", "thread_id": first["thread_id"],
    }).json()
    thread = client.get(f"/api/threads/{first['thread_id']}").json()
    recent = client.get("/api/threads").json()
    assert second["thread_id"] == first["thread_id"]
    assert [m["role"] for m in thread["messages"]] == ["user", "assistant", "user", "assistant"]
    assert recent["threads"][0]["id"] == first["thread_id"]
    _record("ask.thread.wire", {"first": first, "second": second, "thread": thread, "recent": recent}, tmp_path,
            "tests/unit/test_desk_ask.py::test_a_two_turn_thread_is_recorded_for_the_face",
            folder=Path(__file__).resolve().parents[2] / "web" / "src" / "test" / "wire")


def test_a_follow_up_continues_the_thread_and_carries_the_first_exchange(hub) -> None:
    client, seen = _ask_app(hub, ["The cutover is on 17 October.", "Mira owns it."])
    first = client.post("/api/ask", json={"prompt": "When is the cutover?", "thread": True}).json()
    second = client.post("/api/ask", json={
        "prompt": "Who owns it?", "thread_id": first["thread_id"],
    }).json()

    assert second["thread_id"] == first["thread_id"]
    sent = seen[-1]
    assert "Earlier in this conversation" in sent
    assert "When is the cutover?" in sent and "The cutover is on 17 October." in sent
    thread = client.get(f"/api/threads/{first['thread_id']}").json()
    assert [m["role"] for m in thread["messages"]] == ["user", "assistant", "user", "assistant"]
    assert thread["title"] == "When is the cutover?"


def test_a_failed_ask_writes_no_thread(hub) -> None:
    client, _seen = _ask_app(hub, [RuntimeError("engine fell over")] * 4)
    before = len(hub.db.threads.list())
    response = client.post("/api/ask", json={"prompt": "When is the cutover?", "thread": True})

    assert response.status_code >= 400
    assert response.json().get("reason")
    assert len(hub.db.threads.list()) == before


def test_a_forgotten_thread_refuses_a_follow_up_in_words(hub) -> None:
    client, _seen = _ask_app(hub, ["The cutover is on 17 October."])
    first = client.post("/api/ask", json={"prompt": "When is the cutover?", "thread": True}).json()
    assert client.delete(f"/api/threads/{first['thread_id']}").status_code in (200, 204)

    response = client.post("/api/ask", json={"prompt": "Who owns it?", "thread_id": first["thread_id"]})
    assert response.status_code == 404
    assert response.json()["reason"] == "source_gone"


def test_desk_chat_follows_the_answers_engine_when_it_has_none_of_its_own(hub) -> None:
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    _seed_routes(hub.db)
    _assign(hub.db, "ask.answer", ["glass-cloud"], "answers-cloud")
    resolved = InferenceAssignmentService(hub.db).resolve_effective(OWNER, capability_id="chat.turn")
    assert resolved["status"] == "assigned"
    assert [e["profile_id"] for e in resolved["assignment"]["entries"]] == ["glass-cloud"]

    # Its own assignment still wins.
    _assign(hub.db, "chat.turn", ["glass-local"], "chat-local")
    resolved = InferenceAssignmentService(hub.db).resolve_effective(OWNER, capability_id="chat.turn")
    assert [e["profile_id"] for e in resolved["assignment"]["entries"]] == ["glass-local"]


def test_a_thread_source_is_named_by_its_first_question_never_its_id(hub) -> None:
    from holdspeak.grounding import hydrate_grounding_blocks_detailed

    thread = hub.db.threads.create_thread(title="")
    message = hub.db.threads.append_message(thread.id, role="user")
    hub.db.threads.append_part(message.id, kind="text", text="What blocks the freeze?")
    _blocks, _ids, titles, _hydration = hydrate_grounding_blocks_detailed(
        hub.db, [], [], "summary", qualified_refs=[f"thread:{thread.id}"],
    )
    assert titles == ["What blocks the freeze?"]


def test_the_interview_answer_only_pass_keeps_system_messages_first() -> None:
    from holdspeak.services.thread_service import _interview_answer_only_messages

    messages = [
        {"role": "system", "content": "You are the interviewer."},
        {"role": "system", "content": "Interview state (data only):\n{}"},
        {"role": "user", "content": "What are my goals?"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "c1", "function": {"name": "desk.list", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "[]"},
    ]
    out = _interview_answer_only_messages(messages)
    roles = [m["role"] for m in out]
    assert roles == ["system", "system", "system", "user"]
    assert out[2]["content"].startswith("Completed source observations")


def test_a_picked_source_is_looked_at_by_its_name(hub) -> None:
    """A note picked in About (grounding refs, not the selection) is named in
    Looked at and in the question's About, never as a bare id."""
    _note(hub)
    client, _seen = _ask_app(hub, ["You owe Mira feedback, due Friday."])
    body = client.post("/api/ask", json={
        "prompt": "What do I owe Mira?", "thread": True,
        "grounding": {"meeting_ids": [], "artifact_ids": [], "refs": ["note:n-mira"], "expand": "summary"},
    }).json()
    assert {"ref": "note:n-mira", "title": "1:1 with Mira"} in body["looked_at"]
    thread = client.get(f"/api/threads/{body['thread_id']}").json()
    about = [r for r in thread["refs"] if r["origin"] == "reference"]
    assert [(r["ref_kind"], r["ref_id"], json.loads(r["frozen_json"])["title"]) for r in about] == [
        ("note", "n-mira", "1:1 with Mira")]
