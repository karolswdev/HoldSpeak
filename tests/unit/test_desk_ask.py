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
    assert ("note:n-mira", "1:1 with Mira") in {(row["ref"], row["title"]) for row in body["looked_at"]}
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
    assert ("note:n-mira", "1:1 with Mira") in {(row["ref"], row["title"]) for row in body["looked_at"]}
    thread = client.get(f"/api/threads/{body['thread_id']}").json()
    about = [r for r in thread["refs"] if r["origin"] == "reference"]
    assert [(r["ref_kind"], r["ref_id"], json.loads(r["frozen_json"])["title"]) for r in about] == [
        ("note", "n-mira", "1:1 with Mira")]


def test_a_project_in_about_is_read_as_its_records(hub) -> None:
    """Betterment Q5: a project chip in About (sent as the selection, as the
    Room's Ask and Ask about this send it) grounds on the project's records,
    not its title alone."""
    hub.db.projects.create_project(project_id="p-ledger", name="Ledger cutover", description="", keywords=[])
    hub.db.notes.upsert(
        note_id="n-freeze", title="Freeze plan",
        body_markdown="The quokka gate holds the freeze until the reconciliation job runs under ten minutes.",
    )
    hub.db.project_relationships.upsert(project_id="p-ledger", resource_ref="note:n-freeze")
    client, seen = _ask_app(hub, ["The reconciliation job must run under ten minutes first."])
    body = client.post("/api/ask", json={
        "prompt": "What blocks the freeze?", "lens": "Ask", "thread": True,
        "context": [{"id": "p-ledger", "kind": "project", "title": "Ledger cutover", "ref": "project:p-ledger"}],
    }).json()
    assert body["output"].startswith("The reconciliation job")
    assert "quokka gate" in seen[-1], seen[-1][:2000]
    assert ("note:n-freeze", "Freeze plan") in {(row["ref"], row["title"]) for row in body["looked_at"]}
    # The question's About is still the project.
    thread = client.get(f"/api/threads/{body['thread_id']}").json()
    about = [(r["ref_kind"], r["ref_id"]) for r in thread["refs"] if r["origin"] == "reference"]
    assert about == [("project", "p-ledger")]


# ── Ask hub gaps (canvas ask-direction-2026-10-27): the words arrive, the
# references carry their facts, the claims are kept, a slow ask comes back ──

from holdspeak.intel.engine import MeetingIntel  # noqa: E402


class _StreamingEngine(MeetingIntel):
    """The hub's own engine class, whose stream writes the answer in pieces.

    Only ``run_prompt_stream`` (the meeting engine's streaming seam) is
    replaced; each piece waits for ``gate`` once ``hold_after`` pieces are
    out, so the test can read the run while it writes."""

    def __init__(self, model: str, pieces: list[str], gate: Any = None, hold_after: int = 99) -> None:  # noqa: D107
        self._active_provider = "fixture"
        self._active_model = model
        self._pieces, self._gate, self._hold_after = list(pieces), gate, hold_after

    def run_prompt_stream(self, **_kw: Any) -> Any:
        from holdspeak.kernel.inference_stream import Delta

        for index, piece in enumerate(self._pieces):
            if index == self._hold_after and self._gate is not None:
                assert self._gate.wait(10)
            yield Delta(kind="text", text=piece)
        yield Delta(kind="done")


def _frames_app(hub: Any, engine: Any, monkeypatch: Any) -> tuple[TestClient, list[tuple[str, Any]]]:
    from holdspeak.services import ask_service
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.primitives.ask import build_ask_router
    from holdspeak.web.routes.threads import build_threads_router

    monkeypatch.setattr(ask_service, "TEXT_FRAME_SECONDS", 0.0)
    _seed_routes(hub.db)
    hub.broker.inference_adoption_service.migrate_legacy_config(OWNER, SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="glass-lan"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="glass-lan"))))
    _assign(hub.db, "ask.answer", ["glass-lan"], "ask-window-lan")
    hub.broker.inference_runner._engine_factory = lambda rev, **_kw: engine
    frames: list[tuple[str, Any]] = []
    ctx = WebContext(get_state=lambda: {}, broadcast=lambda kind, data: frames.append((kind, data)))
    app = FastAPI()
    app.include_router(build_ask_router(ctx))
    app.include_router(build_threads_router(ctx))
    return TestClient(app), frames


def _desk_records(hub: Any) -> None:
    _note(hub)
    hub.db.projects.create_project(project_id="p-ledger", name="Payments ledger cutover", description="", keywords=[])
    with hub.db._connection() as conn:
        conn.execute(
            "INSERT INTO desk_decisions (id, title, status, decision_markdown, created_at, updated_at)"
            " VALUES ('d-freeze', 'Freeze the old ledger on Nov 5', 'accepted',"
            " 'We freeze the old ledger on Nov 5 after the reconciliation job runs.', '2026-10-27T08:00:00Z', '2026-10-27T08:00:00Z')")


STREAM_PIECES = [
    "You owe Mira feedback on her cutover design doc, due Friday.\n",
    "We freeze the old ledger on Nov 5 after the reconciliation job runs.",
]
STREAM_ABOUT = [
    *ABOUT,
    {"id": "d-freeze", "kind": "decision", "title": "Freeze the old ledger on Nov 5", "ref": "decision:d-freeze"},
]


def test_an_answer_arrives_as_text_frames_and_a_closed_window_claims_it_back(hub, tmp_path, monkeypatch) -> None:
    """Gaps 1, 2, 3 and 5, recorded for the face (``ask.stream.wire.json``):
    the ``ask_text`` frames as the engine writes, the run while it writes
    (what a reopened window reads), the answer with its references' facts
    and its claims by record, the run once answered, and the thread read."""
    import threading
    import time as _time
    from pathlib import Path

    from tests.unit.test_desk_speak import _record

    _desk_records(hub)
    gate = threading.Event()
    client, frames = _frames_app(hub, _StreamingEngine("qwen3.8-27b", STREAM_PIECES, gate, hold_after=1), monkeypatch)
    invocation = "ask_" + "b" * 32
    answer: dict[str, Any] = {}

    def ask() -> None:
        answer.update(client.post("/api/ask", json={
            "prompt": "What do I owe Mira, and when is the freeze?", "lens": "Ask", "context": STREAM_ABOUT,
            "thread": True, "invocation_id": invocation,
        }).json())

    worker = threading.Thread(target=ask)
    worker.start()
    deadline = _time.monotonic() + 10
    running: dict[str, Any] = {}
    while _time.monotonic() < deadline:
        running = client.get(f"/api/ask/runs?ids={invocation}").json()
        if running["runs"][0].get("text"):
            break
        _time.sleep(0.02)
    gate.set()
    worker.join(10)

    texts = [data for kind, data in frames if kind == "ask_text"]
    # The words arrive under the question: the first piece, then the whole answer.
    assert [t["text"] for t in texts][0] == STREAM_PIECES[0]
    assert texts[-1] == {"invocation_id": invocation, "text": "".join(STREAM_PIECES)}
    assert running["runs"][0]["state"] == "running"
    assert running["runs"][0]["text"] == STREAM_PIECES[0]
    assert running["runs"][0]["question"] == "What do I owe Mira, and when is the freeze?"
    assert answer["output"] == "".join(STREAM_PIECES)

    rows = {row["ref"]: row for row in answer["looked_at"]}
    assert rows["note:n-mira"]["kind"] == "note" and rows["note:n-mira"]["at"]
    assert rows["decision:d-freeze"]["state"] == "accepted"
    assert rows["decision:d-freeze"]["at"] == "2026-10-27T08:00:00Z"
    # A project read by a tool is named by its record, not by a kind word.
    from holdspeak.services.ask_service import reference_facts
    [project] = reference_facts(hub.db, [{"ref": "project:p-ledger", "title": "A project"}])
    assert project["title"] == "Payments ledger cutover" and project["kind"] == "project" and project["at"]
    claims = answer["grounding_claims"]
    assert {c["ref"] for c in claims if c.get("ref")} >= {"note:n-mira", "decision:d-freeze"}, claims

    done = client.get(f"/api/ask/runs?ids={invocation},ask_{'c' * 32}").json()
    assert done["runs"][0]["state"] == "answered"
    assert done["runs"][0]["thread_id"] == answer["thread_id"]
    assert done["runs"][1] == {"invocation_id": f"ask_{'c' * 32}", "state": "unknown", "reason": "did_not_answer"}

    # The thread keeps each reference's facts and the claims it supports.
    thread = client.get(f"/api/threads/{answer['thread_id']}").json()
    kept = {f"{r['ref_kind']}:{r['ref_id']}": json.loads(r["frozen_json"]) for r in thread["refs"] if r["origin"] == "relevance"}
    assert kept["decision:d-freeze"]["state"] == "accepted"
    assert kept["note:n-mira"]["claims"]
    _record("ask.stream.wire", {
        "frames": texts, "running": running, "answer": answer, "answered": done, "thread": thread,
    }, tmp_path, "tests/unit/test_desk_ask.py::test_an_answer_arrives_as_text_frames_and_a_closed_window_claims_it_back",
        folder=Path(__file__).resolve().parents[2] / "web" / "src" / "test" / "wire")


def test_an_engine_that_cannot_stream_sends_one_text_frame_at_the_end(hub, monkeypatch) -> None:
    client, frames = _frames_app(hub, _RecordingEngine("qwen3.8-27b", ["The cutover is on 17 October."], []), monkeypatch)
    body = client.post("/api/ask", json={"prompt": "When is the cutover?", "thread": True, "invocation_id": "ask_" + "d" * 32}).json()
    texts = [data for kind, data in frames if kind == "ask_text"]
    assert texts == [{"invocation_id": "ask_" + "d" * 32, "text": body["output"]}]


def test_a_failed_ask_reads_as_not_answered_when_claimed(hub, monkeypatch) -> None:
    client, _frames = _frames_app(hub, _RecordingEngine("qwen3.8-27b", [RuntimeError("engine fell over")] * 4, []), monkeypatch)
    invocation = "ask_" + "e" * 32
    assert client.post("/api/ask", json={"prompt": "When is the cutover?", "thread": True, "invocation_id": invocation}).status_code >= 400
    [run] = client.get(f"/api/ask/runs?ids={invocation}").json()["runs"]
    assert run["state"] == "failed" and run["reason"]
    assert "text" not in run


def test_the_no_engine_refusal_is_recorded_for_the_face(hub, tmp_path) -> None:  # noqa: ARG001 (the isolated hub)
    """``ask.no-engine.wire.json``: the hub's own 409 when nothing answers Ask."""
    from pathlib import Path

    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.primitives.ask import build_ask_router
    from tests.unit.test_desk_speak import _record

    app = FastAPI()
    app.include_router(build_ask_router(WebContext(get_state=lambda: {})))
    response = TestClient(app).post("/api/ask", json={"prompt": "What needs my attention today?", "thread": True})
    assert response.status_code == 409, response.text
    refusal = response.json()
    assert refusal["reason"] == "no_engine", refusal
    _record("ask.no-engine.wire", {"status": response.status_code, "refusal": refusal}, tmp_path,
            "tests/unit/test_desk_ask.py::test_the_no_engine_refusal_is_recorded_for_the_face",
            folder=Path(__file__).resolve().parents[2] / "web" / "src" / "test" / "wire")


def test_a_pull_request_the_tool_read_keeps_its_state() -> None:
    from holdspeak.services.run_trace import _object, _read_facts

    value = {"repository": "acme/ledger", "number": 412, "title": "Cutover flag", "state": "open"}
    ref, title = _object("provider.github_pr_get", {"owner_repo": "acme/ledger", "number": 412}, value)
    assert (ref, title) == ("pr:acme/ledger#412", "Cutover flag")
    assert _read_facts(ref, value) == {"state": "open"}
