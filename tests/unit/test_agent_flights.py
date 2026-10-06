"""Conductor F2: the in-flight read join (launch ledger x Work attempt x session).

`services.agent_flights` names, per item handed to an agent, the agent, its
state (working, waiting, PR open, merged), its session and its PR, from the
records K2 and K4 write. The `/api/coders/sessions` route carries it as
`flights` and on each session row it names (`flight`). The peek envelope
carries the one blocked predicate (`blocked`).
"""
from __future__ import annotations

import pytest

from holdspeak.db import Database
from holdspeak.delivery.factory_launch import LaunchLedger
from holdspeak.services.agent_flights import agent_flights, annotate_sessions
from tests.unit.test_agent_hand import PROJECT, _seed


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "hub.db")
    _seed(database)
    return database


def _attempt(db: Database, session_key: str | None, origin: str) -> str:
    attempt = db.work_attempts.create(
        source_id="src_1", worktree_id="wt_1", project=PROJECT, story_id=origin.replace(":", "-"),
        node_id="this-node", session_id=session_key, target_id=None, kind="launch",
        exact=True, claimed_by="launch:claude-default", state="working", origin_ref=origin,
    )
    return attempt.attempt_id


def _launch(ledger: LaunchLedger, launch_id: str, origin: tuple[str, str], **fields) -> None:
    ledger.record({
        "launch_id": launch_id, "state": "launched", "profile_id": "claude-default",
        "origin_ref": {"kind": origin[0], "id": origin[1]}, "session": f"hs-{launch_id}",
        "launched_at": "2026-10-06T10:00:00Z", **fields,
    })


def _session(agent: str, sid: str, **fields) -> dict:
    return {"session": {"agent": agent, "session_id": sid, "state": "working", **fields}, "age_seconds": 30}


def test_waiting_session_names_its_item_project_and_agent(db, tmp_path):
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(db, "claude:s1", "action:ai_1"))
    sessions = [_session("claude", "s1", question="Jordan or Avery?", hook_event_name="Notification")]
    [flight] = agent_flights(db, sessions, ledger=ledger)
    assert flight["origin_ref"] == "action:ai_1"
    assert flight["title"] == "Fix the login timeout"
    assert (flight["project_id"], flight["project_name"]) == (PROJECT, "Railsproj")
    assert (flight["agent"], flight["state"], flight["session_key"]) == ("claude", "waiting", "claude:s1")
    assert flight["pr"] is None

    annotate_sessions(sessions, [flight])
    assert sessions[0]["flight"]["title"] == "Fix the login timeout"


def test_codex_working_bound_by_tmux_session_when_the_attempt_is_unbound(db, tmp_path):
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "l2", ("decision", "d1"), profile_id="codex-default", attempt_id=_attempt(db, None, "decision:d1"))
    sessions = [_session("codex", "x1", tmux_session="hs-l2")]
    [flight] = agent_flights(db, sessions, ledger=ledger)
    assert (flight["agent"], flight["state"], flight["session_key"]) == ("codex", "working", "codex:x1")


def test_pr_is_the_fact_once_it_exists_and_merged_carries_the_close(db, tmp_path):
    ledger = LaunchLedger(tmp_path / "launches.json")
    attempt = _attempt(db, "claude:s1", "action:ai_1")
    pr = {"number": 412, "url": "https://github.com/acme/ledger/pull/412", "state": "open"}
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=attempt, follow_through={"pr": pr, "pr_state": "pr_open"})
    sessions = [_session("claude", "s1", question="?", awaiting_response=True)]
    [flight] = agent_flights(db, sessions, ledger=ledger)
    assert flight["state"] == "pr_open"
    assert flight["pr"] == {"number": 412, "url": pr["url"], "state": "open"}

    ledger.update("l1", follow_through={
        "pr": {**pr, "state": "merged"}, "close": "closed",
        "evidence": {"merged_at": "2026-10-06T15:29:00Z", "pr_url": pr["url"]},
    })
    [flight] = agent_flights(db, sessions, ledger=ledger)
    assert (flight["state"], flight["close"], flight["merged_at"]) == ("merged", "closed", "2026-10-06T15:29:00Z")


def test_newest_launch_per_item_wins_and_unlaunched_records_are_skipped(db, tmp_path):
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "old", ("action", "ai_1"), profile_id="codex-default")
    _launch(ledger, "new", ("action", "ai_1"))
    _launch(ledger, "failed", ("decision", "d1"), state="failed")
    _launch(ledger, "no-origin", ("", ""))
    flights = agent_flights(db, [], ledger=ledger)
    assert [(f["origin_ref"], f["launch_id"], f["agent"]) for f in flights] == [("action:ai_1", "new", "claude")]
    # No session reported yet: the launched agent is working.
    assert flights[0]["state"] == "working"


def test_ended_session_without_a_pr_is_ended(db, tmp_path):
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(db, "claude:s1", "action:ai_1"))
    [flight] = agent_flights(db, [_session("claude", "s1", state="ended")], ledger=ledger)
    assert flight["state"] == "ended"


def test_sessions_route_carries_flights(monkeypatch, tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import holdspeak.db as dbmod
    from holdspeak.services import agent_flights as flights_mod
    from holdspeak.services.coder_service import CoderService
    from holdspeak.web.routes.system.coders import build_coders_router
    from types import SimpleNamespace

    database = Database(tmp_path / "hub.db")
    _seed(database)
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(database, "claude:s1", "action:ai_1"))
    monkeypatch.setattr(dbmod, "get_database", lambda: database)
    monkeypatch.setattr(CoderService, "list_sessions",
                        lambda self, principal, **kw: [_session("claude", "s1", question="Q?", awaiting_response=True)])
    real = flights_mod.agent_flights
    monkeypatch.setattr(flights_mod, "agent_flights", lambda db, items: real(db, items, ledger=ledger))
    app = FastAPI()
    app.include_router(build_coders_router(SimpleNamespace(broadcast=None)))
    body = TestClient(app).get("/api/coders/sessions").json()
    assert body["count"] == 1
    assert [(f["origin_ref"], f["state"]) for f in body["flights"]] == [("action:ai_1", "waiting")]
    assert body["sessions"][0]["flight"]["title"] == "Fix the login timeout"
