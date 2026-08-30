"""Tests for the /api/recipes/{id}/chat thread alias (HS-151-04).

The route creates/reuses a thread bound to the recipe and starts a turn.
Retired RecipeService.chat()-specific tests (body assembly, grounding,
KB honesty) were deleted — those behaviours no longer exist.
"""
from __future__ import annotations

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
