"""The persona chat turn on the hub (HS-83-02, the web parity of the iPad's
`recipeReply`).

``POST /api/recipes/{id}/chat`` assembles ONE turn — the persona's standing
context (manual + the KB honesty block), HSM-15-12 grounding hydrated from the
canonical store, the last 12 turns, the question — runs it on the recipe's
profile-or-default engine, answers with the turn's honest egress, and persists
NOTHING. ``POST /api/recipes/{id}/keep`` mints the run-born artifact only when
the human says keep.
"""
from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router


@pytest.fixture
def env(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


class _FakeIntel:
    active_provider = "local"

    def __init__(self):
        self.captured = {}

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        self.captured["system_prompt"] = system_prompt
        self.captured["user_prompt"] = user_prompt
        return "SPOKEN"


def _seed_persona(db, *, kb_id=None, manual="The team is three engineers."):
    db.recipes.upsert(
        recipe_id="recipe_scout", name="Scout", avatar="🦊", role="digs for the facts",
        system_prompt="You are a sharp researcher.", user_template="{input}",
        manual_context=manual, kb_id=kb_id,
    )


def test_chat_requires_question_and_a_real_persona(env) -> None:
    db, client = env
    _seed_persona(db)
    # The question gate is first (cheap check before any lookup)...
    assert client.post("/api/recipes/recipe_scout/chat", json={}).status_code == 400
    assert client.post("/api/recipes/recipe_scout/chat", json={"question": "  "}).status_code == 400
    # ...then the persona must be real.
    assert client.post("/api/recipes/ghost/chat", json={"question": "hi"}).status_code == 404


def test_chat_assembles_the_turn_and_persists_nothing(env, monkeypatch) -> None:
    """The envelope, block by block: [CONTEXT] (manual + hydrated KB),
    [GROUNDING] (refs hydrated from the store), [CONVERSATION SO FAR]
    (12-turn window), [USER]. The role rides the system channel."""
    db, client = env
    db.notes.upsert(note_id="note_kb", title="Mesh sync owner",
                    body_markdown="Karol owns the mesh sync review.")
    db.kbs.upsert(kb_id="kb_mesh", name="Mesh", member_ids=["note:note_kb"])
    _seed_persona(db, kb_id="kb_mesh")
    db.meetings.save_meeting(MeetingState(
        id="m_chat", started_at=datetime(2026, 7, 6, 10, 0, 0), title="Q3 kickoff",
        segments=[TranscriptSegment(text="The codename is BLUE LANTERN.",
                                    speaker="Karol", start_time=0.0, end_time=3.0)],
    ))

    fake = _FakeIntel()
    monkeypatch.setattr("holdspeak.intel.providers.build_configured_meeting_intel", lambda: fake)
    monkeypatch.setattr("holdspeak.web.routes.sync._hub_model_name", lambda ctx: "HubModel-9B")

    history = [{"role": "you", "text": f"turn {i}"} for i in range(10)] + [
        {"role": "agent", "text": "an earlier answer"},
        {"role": "you", "text": "the 12th visible turn"},
        {"role": "you", "text": "the 13th visible turn"},
    ]
    before = len(db.plugins.list_run_artifacts())
    resp = client.post("/api/recipes/recipe_scout/chat", json={
        "question": "What is the codename?",
        "history": history,
        "grounding": {"meeting_ids": ["m_chat"], "expand": "full"},
    })
    assert resp.status_code == 200
    body = resp.json()

    assert fake.captured["system_prompt"] == "You are a sharp researcher."
    up = fake.captured["user_prompt"]
    # Block order: context → grounding → conversation → user.
    assert up.index("[CONTEXT]") < up.index("[GROUNDING]") < up.index("[CONVERSATION SO FAR]") < up.index("[USER]")
    assert "The team is three engineers." in up
    assert "[KB: Mesh]" in up and "Karol owns the mesh sync review." in up
    assert "[MEETING: Q3 kickoff — 2026-07-06]" in up and "BLUE LANTERN" in up
    # The 13-turn history windows to 12: the oldest turn falls off.
    assert "turn 0" not in up and "turn 1" in up
    assert "User: the 13th visible turn" in up and "Scout: an earlier answer" in up
    assert up.rstrip().endswith("Reply as Scout.")

    assert body["output"] == "SPOKEN"
    assert body["egress"] == {"scope": "local"}
    assert body["model"] == "HubModel-9B"
    assert body["context_ids"] == ["m_chat"]
    assert body["context_titles"] == ["Q3 kickoff"]
    assert body["grounding"]["expand"] == "full"
    # A chat turn persists NOTHING — harvest is the human's judgment.
    assert len(db.plugins.list_run_artifacts()) == before


def test_chat_kb_honesty_marker_when_nothing_hydrates(env, monkeypatch) -> None:
    db, client = env
    db.kbs.upsert(kb_id="kb_empty", name="Ghost shelf", member_ids=["note:missing"])
    _seed_persona(db, kb_id="kb_empty", manual="")
    fake = _FakeIntel()
    monkeypatch.setattr("holdspeak.intel.providers.build_configured_meeting_intel", lambda: fake)
    monkeypatch.setattr("holdspeak.web.routes.sync._hub_model_name", lambda ctx: "HubModel-9B")
    assert client.post("/api/recipes/recipe_scout/chat", json={"question": "hi"}).status_code == 200
    assert "[KB: Ghost shelf — no hydrated members]" in fake.captured["user_prompt"]


def test_chat_grounding_refuses_unknown_ids(env) -> None:
    db, client = env
    _seed_persona(db)
    resp = client.post("/api/recipes/recipe_scout/chat", json={
        "question": "hi", "grounding": {"meeting_ids": ["ghost_m"]},
    })
    assert resp.status_code == 400
    assert resp.json()["unknown_ids"] == ["ghost_m"]


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
