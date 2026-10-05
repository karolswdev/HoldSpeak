"""Recipe chat searches memory through the live thread turn.

The agent tool turn (``RecipeService.chat`` -> ``AgentTurnService.run_recipe``)
is retired code with no caller.  Recipe chat is ``POST
/api/recipes/{id}/chat``, which starts a thread turn
(``web/routes/_thread_factory.py``).  This file proves that path end to end:

* the real hub, the real kernel broker, the real route and ThreadService,
  the real ``ThreadToolExecutor`` and the real MCP dispatch;
* a deterministic engine at the engine boundary that asks for
  ``memory.search`` on pass 1 and answers on pass 2;
* memory seeded through real producers: a desk note through
  ``PrimitiveService.create_note`` and a People note through the production
  People composition (``build_people_service``).

It asserts the tool runs through the executor, its result reaches pass 2,
no People content appears in it, and a secret in the note is redacted.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.kernel.inference_stream import Delta
from holdspeak.memory.defense import REDACTED
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
KEYWORD = "quorumvale"
SECRET = "hunter2SECRETVALUE"
PEOPLE_WORD = "PEOPLESENTINEL"
PEOPLE_NAME = "Zorvane Quillfeather"


class _MemorySearchEngine:
    """Pass 1 asks for memory.search; once a tool message is present, answer."""

    active_provider = "fake-memory"
    active_model = "memory-model"

    def __init__(self) -> None:
        self.calls: list[list[dict[str, Any]]] = []
        self.tools_seen: list[Any] = []

    def run_prompt_stream(self, *, messages=None, temperature=None, max_tokens=None, tools=None, **kw):
        msgs = [dict(m) for m in (messages or [])]
        self.calls.append(msgs)
        self.tools_seen.append(tools)
        if any(m.get("role") == "tool" for m in msgs):
            yield Delta(kind="text", text="Found it in memory.")
        else:
            yield Delta(kind="tool_calls", meta={"tool_calls": [{
                "id": "call_memory_1",
                "name": "memory.search",
                "arguments": json.dumps({"query": KEYWORD}),
            }]})
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 2})
        yield Delta(kind="done")

    def run_prompt_messages(self, *, messages=None, **kw):
        return "Found it in memory."

    def run_prompt(self, *, system_prompt="", user_prompt="", **kw):
        return "Found it in memory."


@pytest.fixture
def rig(monkeypatch, tmp_path):
    """Isolated HOME + the real hub + the real kernel broker.

    Every global the hub reads is patched through ``monkeypatch``, so the
    teardown puts back HOME, the config path and the database path: a later
    test on this worker never reopens this fixture's database.
    """
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    # The People store on a file key (never the macOS Keychain).
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(home / "people.key"))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", home / "holdspeak.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
    )
    server.start()
    db = get_database()
    from holdspeak.kernel.runtime import _service as _kernel_service

    try:
        yield db, _kernel_service()
    finally:
        server.stop()
        reset_database()


def _assign_chat_turn(db: Any) -> None:
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

    _profile(db, "memory-local", claims=("language", _result_claim("chat.turn")))
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "memory-live-assign",
        "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": "memory-local", "profile_revision": 1}],
    })


def _seed_memory(db: Any) -> str:
    """A desk note (with a secret) and a People note, by their real producers."""
    from holdspeak.mcp.families.people import build_people_service
    from holdspeak.people.store import production_people_store
    from holdspeak.services.primitive_service import PrimitiveService

    note = PrimitiveService(db).create_note(
        OWNER,
        title="Quorumvale staging",
        body_markdown=f"The {KEYWORD} rollout uses token={SECRET} for the staging API.",
    )

    production_people_store().initialize()
    people = build_people_service()
    relationship = people.create_relationship(OWNER, {"display_name": PEOPLE_NAME})
    people.create_note(
        OWNER, relationship["id"],
        {"topic": "Growth", "body": f"{PEOPLE_WORD} asked about {KEYWORD} and a promotion."},
    )
    assert PEOPLE_WORD in people.list_notes(OWNER, relationship["id"])[0]["body"]
    return str(note["id"])


def _chat_via_recipe_route(db: Any, text: str, broadcasts: list) -> str:
    """POST /api/recipes/{id}/chat, then wait for THIS turn's
    ``thread_turn_done`` (emitted after the message is completed)."""
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes import build_primitives_router

    done: dict[str, threading.Event] = {}
    lock = threading.Lock()

    def _broadcast(kind: str, data: Any) -> None:
        broadcasts.append((kind, data))
        if kind == "thread_turn_done":
            with lock:
                done.setdefault(str(data.get("message_id")), threading.Event()).set()

    db.recipes.upsert(recipe_id="recipe_scout", name="Scout", system_prompt="You are exact.")
    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {}, broadcast=_broadcast)))
    response = TestClient(app).post("/api/recipes/recipe_scout/chat", json={"text": text})
    assert response.status_code == 201, response.text
    aid = response.json()["assistant_message_id"]
    with lock:
        event = done.setdefault(aid, threading.Event())
    if not event.wait(timeout=20.0):
        pytest.fail("turn did not emit thread_turn_done")
    return aid


def _flat(messages: list[dict[str, Any]]) -> str:
    return "\n---\n".join(str(m.get("content", "")) for m in messages)


def test_recipe_chat_runs_memory_search_and_the_result_reaches_the_next_pass(rig) -> None:
    db, broker = rig
    _assign_chat_turn(db)
    note_id = _seed_memory(db)

    engine = _MemorySearchEngine()
    broker.inference_runner._engine_factory = lambda _rev, **_kw: engine
    broadcasts: list = []

    _chat_via_recipe_route(db, f"What do we know about {KEYWORD}?", broadcasts)

    # memory.search is offered to the model by default.
    offered = [tool["function"]["name"] for tool in (engine.tools_seen[0] or [])]
    assert "memory.search" in offered, offered

    # Two passes: the tool call, then the answer.
    assert len(engine.calls) == 2, f"expected 2 passes, got {len(engine.calls)}"
    assert not [m for m in engine.calls[0] if m.get("role") == "tool"]

    # The tool ran through the thread tool executor and succeeded.
    results = [d for t, d in broadcasts if t == "thread_tool_result"]
    assert results and results[0]["name"] == "memory.search", results
    assert results[0]["outcome"] == "succeeded", results[0]

    # Its result reached pass 2 as the tool message.
    tool_msgs = [m for m in engine.calls[1] if m.get("role") == "tool"]
    assert len(tool_msgs) == 1
    content = tool_msgs[0]["content"]
    payload = json.loads(content)
    refs = [hit.get("source_ref") for hit in payload.get("hits", [])]
    assert f"note:{note_id}" in refs, content

    # The secret in the note is redacted; it reaches the model nowhere.
    assert REDACTED in content, content
    assert SECRET not in content
    for call in engine.calls:
        assert SECRET not in _flat(call)

    # The People record never appears (no People row in memory).
    for call in engine.calls:
        flat = _flat(call)
        assert PEOPLE_WORD not in flat and "Quillfeather" not in flat

    done = [d for t, d in broadcasts if t == "thread_turn_done"]
    assert done and done[-1]["outcome"] == "succeeded"
