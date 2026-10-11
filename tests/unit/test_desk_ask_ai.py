"""Ask AI and the thread window: the hub half of the browser walks (test diet, 2026-10-11).

Each test calls the real hub code the browser walk drove: the thread routes
(``build_threads_router``), the real kernel broker and route chain with
fixture engines at the runner seam, and the in-process MCP dispatch. The face
half of each walk is in vitest (``web/src/desk/__tests__/askai.app.test.tsx``,
``routeInFooter.test.tsx`` and ``ThreadToolRows.test.tsx``).
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "ask-ai-owner")

# The routes the browser walk seeded (tests/e2e/test_route_in_footer_glass.py).
ROUTES = {
    "glass-lan": {"model": "qwen3.8-27b", "boundary": "private_network", "endpoint": "http://192.168.1.43:8080/v1"},
    "glass-local": {"model": "Qwen3.5 4B", "boundary": "same_device", "endpoint": ""},
    "glass-cloud": {"model": "gpt-5-mini", "boundary": "external_service", "endpoint": "https://api.openai.com/v1"},
}


# ── the hub rig ─────────────────────────────────────────────────────────────


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolated HOME, the hub's one database, the real kernel broker and the
    real thread routes. Every global is patched through ``monkeypatch``."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database
    from holdspeak.kernel.runtime import _service
    from holdspeak.services.thread_service import ThreadService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.threads import build_threads_router

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(home / "people.key"))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", home / "holdspeak.db")
    reset_database()
    db = get_database()
    broker = _service()
    app = FastAPI()
    app.include_router(build_threads_router(WebContext(get_state=lambda: {})))
    registered: list[str] = []
    try:
        yield SimpleNamespace(db=db, broker=broker, client=TestClient(app), registered=registered)
    finally:
        for msg_id in registered:
            ThreadService._tool_executor.unregister(msg_id)
        reset_database()


def _seed_routes(db: Any) -> None:
    """The three fixture deployments of the route walk (LAN, LOCAL, CLOUD)."""
    from holdspeak.deployment_revisions import DeploymentRevision
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

    original = DeploymentRevision.__dict__["from_artifact"]
    for pid, route in ROUTES.items():
        def with_endpoint(cls, *, _endpoint=route["endpoint"], **kw):
            return original.__func__(cls, **{**kw, "endpoint": _endpoint})

        DeploymentRevision.from_artifact = classmethod(with_endpoint)
        try:
            _profile(db, pid, model=route["model"], boundary=route["boundary"],
                     claims=("language", _result_claim("chat.turn"), _result_claim("ask.answer"),
                             _result_claim("thought.interview"), _result_claim("speech.intent_classify")))
        finally:
            DeploymentRevision.from_artifact = original


def _assign(db: Any, capability: str, profile_ids: list[str], command: str) -> None:
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    with db._connection() as conn:
        row = conn.execute(
            "SELECT revision FROM inference_assignment_heads WHERE assignment_key=?",
            (f"capability:{capability}",),
        ).fetchone()
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": command,
        "expected_revision": int(row["revision"]) if row is not None else 0,
        "scope": {"kind": "capability", "capability_id": capability},
        "entries": [{"profile_id": p, "profile_revision": 1} for p in profile_ids],
    })


def _executions(db: Any) -> list[str]:
    with db._connection() as conn:
        return [r["id"] for r in conn.execute("SELECT id FROM inference_route_executions ORDER BY rowid")]


class _ToolThenTextEngine:
    """Calls one tool on the first pass, then answers in text (the walks' engines)."""

    active_provider = "fixture"

    def __init__(self, model: str, call: dict[str, Any], answer: str) -> None:
        self.active_model = model
        self._call = call
        self._answer = answer

    def run_prompt_stream(self, *, messages: Any = None, **_kw: Any) -> Any:
        from holdspeak.kernel.inference_stream import Delta

        if any(m.get("role") == "tool" for m in (messages or [])):
            yield Delta(kind="text", text=self._answer)
        else:
            yield Delta(kind="tool_calls", meta={"tool_calls": [self._call]})
        yield Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 5})
        yield Delta(kind="done")

    def run_prompt(self, **_kw: Any) -> str:
        return self._answer


class _TextEngine:
    active_provider = "fixture"

    def __init__(self, model: str, text: str) -> None:
        self.active_model = model
        self._text = text

    def run_prompt_stream(self, **_kw: Any) -> Any:
        from holdspeak.kernel.inference_stream import Delta

        for word in self._text.split(" "):
            yield Delta(kind="text", text=word + " ")
        yield Delta(kind="usage", meta={"prompt_tokens": 20, "completion_tokens": 20})
        yield Delta(kind="done")

    def run_prompt(self, **_kw: Any) -> str:
        return self._text


def _thread_service(hub: Any, frames: list, *, control_mode: str = "yolo") -> Any:
    """The hub's ThreadService wiring (web/routes/_thread_factory.py) with a
    recording broadcast and a fixed posture."""
    from holdspeak.mcp.tools import dispatch as mcp_dispatch
    from holdspeak.services.thread_service import ThreadService

    return ThreadService(
        hub.db,
        broadcast=lambda t, d: frames.append((t, d)),
        broker=hub.broker,
        tool_dispatch_fn=mcp_dispatch,
        control_mode_fn=lambda: control_mode,
    )


def _run_turn(svc: Any, frames: list, thread_id: str, text: str) -> dict[str, Any]:
    before = sum(1 for t, _ in frames if t == "thread_turn_done")
    turn = asyncio.run(svc.start_turn(OWNER, thread_id, text))
    end = time.monotonic() + 20
    while time.monotonic() < end and sum(1 for t, _ in frames if t == "thread_turn_done") <= before:
        time.sleep(0.05)
    done = [d for t, d in frames if t == "thread_turn_done"]
    assert len(done) > before, "the turn never sent thread_turn_done"
    return {"turn": turn, "done": done[-1]}


# ── HS-152-05 renderers: thread.set_status and desk.list(notes) ─────────────


def test_a_set_status_turn_saves_and_sends_the_status_line(hub) -> None:
    """replaces: tests/e2e/test_hs152_renderers_glass.py::test_set_status_updates_head_live

    The model calls thread.set_status through the real loop: the tool row is
    receipted, the live frames carry the text (the last one, sent before
    turn_done, is the persisted value), and the thread row keeps it."""
    _seed_routes(hub.db)
    _assign(hub.db, "chat.turn", ["glass-local"], "status-1")
    frames: list = []
    svc = _thread_service(hub, frames)
    tid = hub.client.post("/api/threads", json={"title": "Status Test"}).json()["id"]
    hub.broker.inference_runner._engine_factory = lambda rev, **_kw: _ToolThenTextEngine(
        str(rev.model),
        {"id": "glass-status-1", "name": "thread.set_status",
         "arguments": json.dumps({"thread_id": tid, "text": "Preparing your brief..."})},
        "Status set.",
    )
    _run_turn(svc, frames, tid, "Set my status")

    [result] = [d for t, d in frames if t == "thread_tool_result"]
    assert (result["name"], result["outcome"], result["kind"]) == ("thread.set_status", "succeeded", "data")
    status_texts = [d["text"] for t, d in frames if t == "thread_status_line"]
    assert "Preparing your brief..." in status_texts
    # The frame sent just before turn_done is the persisted value the head keeps.
    assert status_texts[-1] == "Preparing your brief..."
    assert hub.db.threads.get(tid).status_line == "Preparing your brief..."


def test_the_thread_read_carries_the_saved_status_line(hub) -> None:
    """The thread read (GET /api/threads/{id}) carries the saved status_line,
    so a reloaded window's head shows it (web/src/desk/threads.ts getThread
    reads d.status_line). Before 2026-10-11 _thread_dict left it out and only
    the live frames carried it."""
    tid = hub.client.post("/api/threads", json={"title": "Status Read"}).json()["id"]
    assert hub.client.get(f"/api/threads/{tid}").json()["status_line"] in (None, "")
    hub.db.threads.patch(tid, status_line="Preparing your brief...")
    body = hub.client.get(f"/api/threads/{tid}").json()
    assert body["status_line"] == "Preparing your brief..."


def test_a_desk_list_notes_turn_returns_note_rows_the_face_hydrates(hub) -> None:
    """replaces: tests/e2e/test_hs152_renderers_glass.py::test_desk_list_renders_result

    desk.list(notes) over two seeded notes: the tool row is receipted with kind
    ``note``, and the persisted tool part (what ``hydrateToolRows`` reads) is a
    JSON array with both titles, keyed to the call, with ``meta_json.kind``
    ``note``. The note renderer (``ThreadToolRows.test.tsx`` "note kind renders
    NoteResultView with array (desk.list)") takes exactly this array."""
    from holdspeak.services.primitive_service import PrimitiveService

    _seed_routes(hub.db)
    _assign(hub.db, "chat.turn", ["glass-local"], "notes-1")
    primitives = PrimitiveService(hub.db)
    primitives.create_note(OWNER, title="Glass meeting note", body_markdown="Discussed the **Q3 plan**.")
    primitives.create_note(OWNER, title="Architecture decision", body_markdown="Chose React over Vue.")
    hub.broker.inference_runner._engine_factory = lambda rev, **_kw: _ToolThenTextEngine(
        str(rev.model),
        {"id": "glass-note-1", "name": "desk.list", "arguments": json.dumps({"kind": "notes"})},
        "Listed notes.",
    )
    frames: list = []
    svc = _thread_service(hub, frames)
    tid = hub.client.post("/api/threads", json={"title": "Note List"}).json()["id"]
    _run_turn(svc, frames, tid, "List my notes")

    [result] = [d for t, d in frames if t == "thread_tool_result"]
    assert (result["name"], result["outcome"], result["kind"]) == ("desk.list", "succeeded", "note")
    assert result["receipt_id"]
    wire = hub.client.get(f"/api/threads/{tid}").json()
    [tool_msg] = [m for m in wire["messages"] if m["role"] == "tool"]
    [part] = tool_msg["parts"]
    assert part["tool_call_id"] == "glass-note-1"
    assert part["meta_json"]["kind"] == "note"
    payload = json.loads(part["text"])
    assert isinstance(payload, list)
    assert {n["title"] for n in payload} >= {"Glass meeting note", "Architecture decision"}


# ── HS-152-04 hands: the /decide route the decision box presses ─────────────


def _held(hub: Any, *, name: str = "desk.create", dispatch: Callable[..., Any] | None = None,
          control_mode: str = "safe", elicit: bool = False) -> tuple[Any, Any, str]:
    """A held tool call registered where POST /decide finds it (the aggregator
    the live turn registers its executor in)."""
    from holdspeak.services.thread_service import ThreadService
    from holdspeak.services.thread_tools import ThreadToolExecutor

    executor = ThreadToolExecutor(
        hub.db, dispatch_fn=dispatch or (lambda n, a, p: {"ok": True}),
        principal=OWNER, control_mode_fn=lambda: control_mode,
    )
    tid = hub.client.post("/api/threads", json={"title": f"Hands {name}"}).json()["id"]
    handle = executor.admit("turn-op", tid, {"id": f"call-{len(hub.registered)}", "name": name, "arguments": {}})
    if elicit:
        assert executor.execute(handle).kind == "elicitation"
    assert handle.state == "awaiting_decision"
    msg_id = f"asst-{len(hub.registered)}"
    ThreadService._tool_executor.register(msg_id, executor)
    hub.registered.append(msg_id)
    return executor, handle, tid


def test_allow_once_admits_the_call_and_writes_no_policy(hub) -> None:
    """replaces: tests/e2e/test_hs152_hands_glass.py::test_allow_once_decision_box_to_receipted
    (and the Allow-once leg of ::test_allow_always_auto_admit)"""
    executor, handle, tid = _held(hub)
    r = hub.client.post(f"/api/threads/{tid}/decide", json={"call_id": handle.call_id, "decision": "approve"})
    assert r.status_code == 200
    assert r.json() == {"call_id": handle.call_id, "decision": "approve", "always": False, "state": "admitted"}
    result = executor.execute(handle)
    assert result.kind == "data" and result.receipt_id.startswith("tr-")
    assert hub.db.threads.effective_tool_policy(tid, "desk.create") is None
    assert executor.admit("turn-op-2", tid, {"id": "again", "name": "desk.create", "arguments": {}}).state == "awaiting_decision"
    # A decision lands once.
    again = hub.client.post(f"/api/threads/{tid}/decide", json={"call_id": handle.call_id, "decision": "approve"})
    assert again.status_code == 409


def test_allow_always_writes_the_allow_policy_and_the_next_call_auto_admits(hub) -> None:
    """replaces: tests/e2e/test_hs152_hands_glass.py::test_allow_always_auto_admit

    The route itself writes the policy row (the unit suites write it by hand)."""
    executor, handle, tid = _held(hub)
    r = hub.client.post(f"/api/threads/{tid}/decide",
                        json={"call_id": handle.call_id, "decision": "approve", "always": True})
    assert r.status_code == 200
    assert r.json()["always"] is True and r.json()["state"] == "admitted"
    assert hub.db.threads.effective_tool_policy(tid, "desk.create") == "allow"
    nxt = executor.admit("turn-op-2", tid, {"id": "next", "name": "desk.create", "arguments": {}})
    assert nxt.state == "admitted", "the next call to the same tool must not show a decision box"


def test_deny_ends_the_call_tool_denied(hub) -> None:
    """replaces: tests/e2e/test_hs152_hands_glass.py::test_deny_shows_tool_denied_row"""
    executor, handle, tid = _held(hub)
    r = hub.client.post(f"/api/threads/{tid}/decide", json={"call_id": handle.call_id, "decision": "deny"})
    assert r.status_code == 200 and r.json()["state"] == "denied"
    assert executor.execute(handle).kind == "tool_denied"
    assert hub.db.threads.effective_tool_policy(tid, "desk.create") is None


def test_an_elicitation_answer_redispatches_and_a_decline_denies(hub) -> None:
    """replaces: tests/e2e/test_hs152_hands_glass.py::test_elicitation_form_submit_and_decline"""
    calls: list[dict] = []

    def elicit(name: str, args: dict, principal: Any) -> Any:
        calls.append(dict(args))
        if "__answer" not in args:
            return {"elicit": {"type": "object", "prompt": "Pick a fruit",
                               "properties": {"name": {"type": "string", "title": "Name"}}, "required": ["name"]}}
        return {"ok": True, "answer_received": args["__answer"]}

    executor, handle, tid = _held(hub, name="desk.list", dispatch=elicit, control_mode="yolo", elicit=True)
    r = hub.client.post(f"/api/threads/{tid}/decide",
                        json={"call_id": handle.call_id, "decision": "approve", "answer": {"name": "Apple"}})
    assert r.status_code == 200 and r.json()["state"] == "admitted"
    result = executor.execute(handle)
    assert result.kind == "data"
    assert result.payload == {"ok": True, "answer_received": {"name": "Apple"}}
    assert calls[-1]["__answer"] == {"name": "Apple"}

    executor2, declined, tid2 = _held(hub, name="desk.list", dispatch=elicit, control_mode="yolo", elicit=True)
    r = hub.client.post(f"/api/threads/{tid2}/decide", json={"call_id": declined.call_id, "decision": "deny"})
    assert r.status_code == 200 and r.json()["state"] == "denied"
    assert executor2.execute(declined).kind == "tool_denied"


def test_a_failed_tool_call_ends_tool_execution_failed(hub) -> None:
    """replaces: tests/e2e/test_hs152_hands_glass.py::test_failed_tool_row_and_no_overflow
    (the failed-row half; the no-overflow half is geometry and stays a browser check)

    desk.get on a note that does not exist, through the real loop and the
    real MCP dispatch, sends a failed tool result with tool_execution_failed."""
    _seed_routes(hub.db)
    _assign(hub.db, "chat.turn", ["glass-local"], "fail-1")
    hub.broker.inference_runner._engine_factory = lambda rev, **_kw: _ToolThenTextEngine(
        str(rev.model),
        {"id": "glass-fail-1", "name": "desk.get",
         "arguments": json.dumps({"kind": "notes", "id": "nonexistent-note-9999"})},
        "That note is not there.",
    )
    frames: list = []
    svc = _thread_service(hub, frames, control_mode="safe")
    tid = hub.client.post("/api/threads", json={"title": "Fail"}).json()["id"]
    _run_turn(svc, frames, tid, "Get a bogus note")
    [result] = [d for t, d in frames if t == "thread_tool_result"]
    assert (result["name"], result["outcome"], result["kind"]) == ("desk.get", "failed", "tool_execution_failed")


# ── route in footer: the route chain names each turn's route ────────────────


def test_a_lan_ask_carries_the_lan_route_the_footer_prints(hub) -> None:
    """replaces: tests/e2e/test_route_in_footer_glass.py::test_ask_on_lan_lamp_on_the_turn_route_in_the_footer
    (the hub half; the face half is routeInFooter.test.tsx "the HUB> turn wears the LAN lamp ...")"""
    from holdspeak.services.ask_service import AskService

    _seed_routes(hub.db)
    hub.broker.inference_adoption_service.migrate_legacy_config(OWNER, SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="glass-lan"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="glass-lan"))))
    _assign(hub.db, "ask.answer", ["glass-lan"], "ask-lan-1")
    hub.broker.inference_runner._engine_factory = lambda rev, **_kw: _TextEngine(
        str(rev.model), "The cutover is on 17 October, after the freeze.")
    result = asyncio.run(AskService(hub.db, broker=hub.broker).ask(OWNER, "What did we decide about the cutover date?"))
    [execution] = _executions(hub.db)
    assert result["route"] == {"lamp": "private_network", "host": "192.168.1.43", "model": "qwen3.8-27b",
                               "receipt": execution, "fallback": False}


def test_a_chat_with_lan_local_cloud_turns_keeps_each_turns_route(hub) -> None:
    """replaces: tests/e2e/test_route_in_footer_glass.py::test_chat_with_lan_local_cloud_turns
    (the hub half; the face half is routeInFooter.test.tsx "each turn's lamp equals its
    receipt boundary" and "the footer names the last turn's full route")"""
    _seed_routes(hub.db)
    hub.broker.inference_runner._engine_factory = lambda rev, **_kw: _TextEngine(str(rev.model), f"answer from {rev.model}")
    frames: list = []
    svc = _thread_service(hub, frames)
    tid = hub.client.post("/api/threads", json={"title": "Cutover risks"}).json()["id"]
    for n, pid in enumerate(["glass-lan", "glass-local", "glass-cloud"], start=1):
        _assign(hub.db, "chat.turn", [pid], f"chat-{n}")
        _run_turn(svc, frames, tid, f"turn {n}")
    executions = _executions(hub.db)
    assert len(executions) == 3
    wire = hub.client.get(f"/api/threads/{tid}").json()
    turns = [m for m in wire["messages"] if m["role"] == "assistant"]
    got = [(m["egress_scope"], m["egress_host"], m["model_id"], m["egress_receipt_id"], bool(m["egress_fallback"]))
           for m in turns]
    assert got == [
        ("private_network", "192.168.1.43", "qwen3.8-27b", executions[0], False),
        ("local", "", "Qwen3.5 4B", executions[1], False),
        ("cloud", "api.openai.com", "gpt-5-mini", executions[2], False),
    ]
    done = [d for t, d in frames if t == "thread_turn_done"]
    assert [(d["egress"], d["host"], d["model"]) for d in done] == [
        ("private_network", "192.168.1.43", "qwen3.8-27b"),
        ("local", "", "Qwen3.5 4B"),
        ("cloud", "api.openai.com", "gpt-5-mini"),
    ]


# ── HS-154 call mode: a turn lands its words; call mode persists ────────────


def test_a_call_turn_lands_its_words_and_call_mode_persists(hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """replaces: tests/e2e/test_hs154_call_glass.py::test_call_loop_glass (hub half: the turn's words
      are the thread's user message, the fixture engine's answer its assistant message)
    replaces: tests/e2e/test_hs154_call_glass.py::test_call_chip_glass (hub half: a new thread reads
      call_mode 0; PATCH call_mode=1 answers 1 and the read keeps it)
    replaces: tests/e2e/test_hs154_call_glass.py::test_speaker_glyph_glass (hub half: the finished
      assistant row the glyph rides)

    The three thread reads are the fixture the face replays
    (web/src/desk/__tests__/fixtures/speak-hub/call.json, askai.app.test.tsx)."""
    from tests.unit.test_desk_speak import _record

    _seed_routes(hub.db)
    _assign(hub.db, "chat.turn", ["glass-local"], "call-1")
    hub.broker.inference_runner._engine_factory = lambda rev, **_kw: _TextEngine(
        str(rev.model), "Glass test response from the fake engine.")
    frames: list = []
    svc = _thread_service(hub, frames)
    created = hub.client.post("/api/threads", json={"title": "Call Loop Glass"})
    assert created.status_code == 201, created.text
    tid = created.json()["id"]
    fresh = hub.client.get(f"/api/threads/{tid}").json()
    assert fresh["call_mode"] == 0 and fresh["messages"] == []

    _run_turn(svc, frames, tid, "Hello from the call loop")
    after_turn = hub.client.get(f"/api/threads/{tid}").json()
    roles = [(m["role"], " ".join(p.get("text") or "" for p in m["parts"]).strip()) for m in after_turn["messages"]]
    assert roles == [("user", "Hello from the call loop"),
                     ("assistant", "Glass test response from the fake engine.")], roles
    assert all(m["streaming"] in (0, False) for m in after_turn["messages"])

    patched = hub.client.patch(f"/api/threads/{tid}", json={"call_mode": 1})
    assert patched.status_code == 200 and patched.json()["call_mode"] == 1, patched.text
    call_on = hub.client.get(f"/api/threads/{tid}").json()
    assert call_on["call_mode"] == 1

    # The voice the glyph speaks with: the hub's TTS status without the extra
    # (the browser rig pinned the same probe), so the face takes the browser voice.
    import holdspeak.web.routes.tts as tts_routes
    from holdspeak.web.context import WebContext

    monkeypatch.setattr(tts_routes, "_kokoro_checked", True)
    monkeypatch.setattr(tts_routes, "_kokoro_available", False)
    tts_app = FastAPI()
    tts_app.include_router(tts_routes.build_tts_router(WebContext(get_state=lambda: {})))
    tts_status = TestClient(tts_app).get("/api/tts/status").json()
    assert tts_status["installed"] is False and tts_status["model_ready"] is False

    _record("call", {"thread_id": tid, "fresh": fresh, "after_turn": after_turn, "call_on": call_on,
                     "patch_call_on": patched.json(), "tts_status": tts_status},
            tmp_path, "tests/unit/test_desk_ask_ai.py::test_a_call_turn_lands_its_words_and_call_mode_persists")
