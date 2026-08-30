"""Tests for the /api/recipes/{id}/chat thread alias (HS-151-04).

The route creates/reuses a thread bound to the recipe and starts a turn.
Retired RecipeService.chat()-specific tests (body assembly, grounding,
KB honesty) were deleted — those behaviours no longer exist.
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router


@pytest.fixture
def env(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    hub_model = tmp_path / "HubModel-9B.gguf"
    hub_model.touch()
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path",
        lambda: str(hub_model),
    )
    db.profiles.upsert(
        profile_id="chat-default", name="Chat default", kind="onDevice",
        model_file=str(hub_model),
    )
    InferenceAssignmentService(db).set_assignment(
        Principal(PrincipalKind.OWNER, "chat-test-owner"),
        {
            "command_id": "chat-test-default-assignment",
            "expected_revision": 0,
            "scope": {"kind": "global"},
            "entries": [{"profile_id": "legacy-chat-default"}],
        },
    )
    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


def _seed_persona(db, *, kb_id=None, manual="The team is three engineers."):
    db.recipes.upsert(
        recipe_id="recipe_scout", name="Scout", avatar="\U0001f98a", role="digs for the facts",
        system_prompt="You are a sharp researcher.", user_template="{input}",
        manual_context=manual, kb_id=kb_id,
    )


def test_chat_alias_requires_text(env) -> None:
    """The alias requires non-blank text (question or text field)."""
    db, client = env
    _seed_persona(db)
    assert client.post("/api/recipes/recipe_scout/chat", json={}).status_code == 400
    assert client.post("/api/recipes/recipe_scout/chat", json={"question": "  "}).status_code == 400
    assert client.post("/api/recipes/recipe_scout/chat", json={"text": ""}).status_code == 400


# HS-151-04: test_chat_assembles_the_turn_and_persists_nothing DELETED —
# tested RecipeService.chat() body shape (block assembly, output, egress,
# context_ids); the alias creates a thread+turn, none of those apply.

# HS-151-04: test_chat_kb_honesty_marker_when_nothing_hydrates DELETED —
# tested RecipeService.chat() KB honesty marker in user_prompt.

# HS-151-04: test_chat_grounding_refuses_unknown_ids DELETED —
# the alias does not accept a grounding body; ref refusal is tested via
# ThreadService.start_turn(refs=...) in test_thread_service.py.


def test_keep_mints_the_run_born_artifact(env) -> None:
    db, client = env
    _seed_persona(db)
    resp = client.post("/api/recipes/recipe_scout/keep", json={
        "question": "What is the codename?", "output": "BLUE LANTERN.",
    })
    assert resp.status_code == 201
    aid = resp.json()["artifact_id"]
    art = db.plugins.get_artifact(aid)
    assert art is not None
    assert art.title.startswith("Scout: What is the codename?")
    assert art.body_markdown == "BLUE LANTERN."
    assert {"source_type": "recipe", "source_ref": "recipe_scout"} in art.sources
    assert aid in {a.id for a in db.plugins.list_run_artifacts()}
    assert client.post("/api/recipes/recipe_scout/keep", json={"output": " "}).status_code == 400
    assert client.post("/api/recipes/ghost/keep", json={"output": "x"}).status_code == 404


# ── Engine-off-the-loop regression for the chat alias ──────────────


class _LoopSpy:
    """Records whether the engine ran on the event loop's thread."""

    active_provider = "local"

    def __init__(self) -> None:
        self.on_loop: bool | None = None

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        try:
            asyncio.get_running_loop()
            self.on_loop = True
        except RuntimeError:
            self.on_loop = False
        return "SPY-RAN"


@pytest.fixture
def spy(monkeypatch) -> _LoopSpy:
    s = _LoopSpy()
    from holdspeak.kernel.inference_runner import InferenceRunner
    monkeypatch.setitem(InferenceRunner.__init__.__kwdefaults__, "engine_factory", lambda revision, **_kw: s)
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: s)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: s)
    return s


def test_chat_alias_creates_thread_and_returns_ids(env, spy) -> None:
    """The alias creates a thread, starts a turn, returns 201 with ids."""
    db, client = env
    _seed_persona(db)
    resp = client.post("/api/recipes/recipe_scout/chat", json={"question": "hi"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "thread_id" in body
    assert "user_message_id" in body
    assert "assistant_message_id" in body
    # The thread must be bound to the recipe.
    thread = db.threads.get(body["thread_id"])
    assert thread is not None
    assert thread.recipe_id == "recipe_scout"


def test_chat_alias_reuses_existing_thread(env, spy) -> None:
    """A second chat to the same recipe reuses the thread created by the first."""
    db, client = env
    _seed_persona(db)
    r1 = client.post("/api/recipes/recipe_scout/chat", json={"text": "first"})
    assert r1.status_code == 201
    r2 = client.post("/api/recipes/recipe_scout/chat", json={"text": "second"})
    assert r2.status_code == 201
    assert r1.json()["thread_id"] == r2.json()["thread_id"]


def test_chat_alias_engine_runs_off_the_loop(env, spy) -> None:
    """The engine dispatched by the chat alias runs off the event loop.

    Regression guard: the broken inline ThreadService construction passed
    broker=None, crashing the daemon thread. The shared factory wires the
    kernel broker, and the engine runs in a daemon thread (off the loop).
    """
    db, client = env
    _seed_persona(db)
    resp = client.post("/api/recipes/recipe_scout/chat", json={"question": "hi"})
    assert resp.status_code == 201
    # The turn runs on a daemon thread; wait for the spy to fire.
    for _ in range(100):
        if spy.on_loop is not None:
            break
        time.sleep(0.02)
    assert spy.on_loop is False, (
        "the engine ran ON the event loop -- the thread alias must dispatch "
        "the turn to a daemon thread so the request never blocks the loop"
    )
