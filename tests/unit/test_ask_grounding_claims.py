"""HS-103-03 — the Ask-AI answer path attaches a per-claim support signal
(quiet, additive, never blocking) alongside the generated output."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router


@pytest.fixture
def rig(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "ask_grounding.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    # These route tests inject an engine; local model-file readiness is outside
    # the behavior they cover.
    monkeypatch.setattr(
        "holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", "")
    )
    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


class _FakeIntel:
    active_provider = "local"

    def __init__(self, output: str) -> None:
        self._output = output

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        return self._output


def _mock_intel(monkeypatch, output: str) -> None:
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel",
        lambda: _FakeIntel(output),
    )


def test_flags_an_unsupported_claim_and_not_a_supported_one(rig, monkeypatch) -> None:
    db, client = rig
    db.notes.upsert(
        note_id="n1",
        title="Standup notes",
        body_markdown="Sarah will own the migration script. Budget was approved.",
    )
    _mock_intel(
        monkeypatch,
        "- Sarah owns the migration script\n"
        "- The team relocated to Mars next quarter\n",
    )
    res = client.post(
        "/api/ask",
        json={
            "prompt": "Summarize",
            "context": [{"id": "n1", "kind": "note", "title": "Standup notes"}],
        },
    )
    assert res.status_code == 200
    body = res.json()
    claims = body["grounding_claims"]
    assert len(claims) == 2
    supported = next(c for c in claims if "migration" in c["text"])
    unsupported = next(c for c in claims if "Mars" in c["text"])
    assert supported["flagged"] is False
    assert unsupported["flagged"] is True
    # additive only: the raw output is untouched
    assert body["output"] == (
        "- Sarah owns the migration script\n"
        "- The team relocated to Mars next quarter\n"
    )


def test_no_grounding_claims_when_no_context_material(rig, monkeypatch) -> None:
    """A context-free ask has nothing to be unsupported BY — skip scoring
    rather than flagging every claim against an empty source."""
    _, client = rig
    _mock_intel(monkeypatch, "Whatever the model says.")
    res = client.post("/api/ask", json={"prompt": "Just answer"})
    assert res.status_code == 200
    assert "grounding_claims" not in res.json()
