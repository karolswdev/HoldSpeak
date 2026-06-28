"""CAD-3 — agent-blocker push: collecting awaiting sessions + the reply route."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.agent_context as agent_context
import holdspeak.tmux_transport as tmux_transport
from holdspeak.cadence.collector import LoopCollector
from holdspeak.cadence.models import EvidenceRef, OpenLoop
from holdspeak.db import get_database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes.cadence import build_cadence_router


def _write_agent_state(path: Path, *, pane="editor:0.1", awaiting=True):
    path.write_text(json.dumps({"sessions": {"sess-1": {
        "agent": "codex", "session_id": "sess-1", "cwd": "/home/k/dev/holdspeak",
        "updated_at": "2026-06-28T10:00:00+00:00", "hook_event_name": "Stop",
        "repo_root": "/home/k/dev/holdspeak", "project_name": "holdspeak",
        "awaiting_response": awaiting,
        "last_assistant_text": "Should I store pairing state in SQLite or config?",
        "tmux_pane": pane, "pinned": True,  # pinned = age-exempt, deterministic
    }}}))


@pytest.fixture
def db(tmp_path: Path, monkeypatch):
    reset_database()
    monkeypatch.setattr(agent_context, "AGENT_CONTEXT_FILE", tmp_path / "agent_sessions.json")
    yield get_database(tmp_path / "agent.db")
    reset_database()


def test_collector_projects_awaiting_agent_as_top_loop(db, tmp_path, monkeypatch):
    _write_agent_state(tmp_path / "agent_sessions.json")
    loops = LoopCollector(db).collect()
    agent_loops = [l for l in loops if l.source_type == "agent_question"]
    assert len(agent_loops) == 1
    loop = agent_loops[0]
    assert "SQLite or config" in loop.title
    assert loop.priority == "urgent"
    assert loop.evidence[0].kind == "agent_session"
    # it should outrank a plain meeting action (the agent boost dominates)
    assert db.cadence.list_loops()[0].source_type == "agent_question"


def test_answered_agent_closes_its_loop_on_recollect(db, tmp_path):
    _write_agent_state(tmp_path / "agent_sessions.json")
    LoopCollector(db).collect()
    loop = db.cadence.get_loop_by_source("agent_question", "sess-1")
    # the agent is no longer awaiting (answered elsewhere) -> source vanishes -> closed
    _write_agent_state(tmp_path / "agent_sessions.json", awaiting=False)
    LoopCollector(db).collect()
    assert db.cadence.get_loop_by_source("agent_question", "sess-1").status == "closed"
    assert loop is not None


@pytest.fixture
def client(db, tmp_path, monkeypatch):
    # seed an agent_question loop directly + a meeting_action loop (the non-agent case)
    db.cadence.upsert_loop(OpenLoop(
        source_type="agent_question", source_id="sess-1", title="SQLite or config?",
        owner="you", priority="urgent",
        evidence=[EvidenceRef(kind="agent_session", ref_id="sess-1", label="codex session")],
    ))
    db.cadence.upsert_loop(OpenLoop(source_type="meeting_action", source_id="a1", title="File it"))
    app = FastAPI()
    app.include_router(build_cadence_router(WebContext(get_state=lambda: {})))
    return TestClient(app), db


class _Sess:
    session_id = "sess-1"
    tmux_pane = "editor:0.1"


def test_reply_delivers_into_pane_and_closes(client, monkeypatch):
    c, db = client
    sent = {}
    monkeypatch.setattr(agent_context, "list_recent_awaiting_agent_sessions", lambda **k: [_Sess()])
    monkeypatch.setattr(tmux_transport, "send_text_to_pane",
                        lambda **kw: (sent.update(kw) or tmux_transport.TmuxDelivery(pane=kw["pane"], submitted=True)))
    loop_id = db.cadence.get_loop_by_source("agent_question", "sess-1").id
    r = c.post(f"/api/cadence/loops/{loop_id}/reply", json={"text": "Use SQLite; add a migration."})
    assert r.status_code == 200 and r.json()["delivered"] is True
    assert sent["pane"] == "editor:0.1" and "SQLite" in sent["text"]
    assert db.cadence.get_loop(loop_id).status == "closed"  # question handled


def test_reply_rejects_empty_and_non_agent_and_missing_pane(client, monkeypatch):
    c, db = client
    agent_id = db.cadence.get_loop_by_source("agent_question", "sess-1").id
    action_id = db.cadence.get_loop_by_source("meeting_action", "a1").id
    # empty text
    assert c.post(f"/api/cadence/loops/{agent_id}/reply", json={"text": "  "}).status_code == 400
    # non-agent loop
    assert c.post(f"/api/cadence/loops/{action_id}/reply", json={"text": "hi"}).status_code == 400
    # no resolvable pane / session
    monkeypatch.setattr(agent_context, "list_recent_awaiting_agent_sessions", lambda **k: [])
    assert c.post(f"/api/cadence/loops/{agent_id}/reply", json={"text": "hi"}).status_code == 409
    # never autonomous: nothing delivered, loop stays open
    assert db.cadence.get_loop(agent_id).status != "closed"
