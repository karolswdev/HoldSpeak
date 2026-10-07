"""Conductor F2: the in-flight read join (launch ledger x Work attempt x session).

`services.agent_flights` names, per item handed to an agent, the agent, its
state, its session and its PR, from the records K2 and K4 write. Sessions
come from the product's own hook ingest (`ingest_agent_hook_event`) into an
isolated registry; launches from `LaunchLedger`; attempts from
`db.work_attempts`. The `/api/coders/sessions` route carries the flights as
`flights` and on each session row it names (`flight`). The peek envelope
carries the one blocked predicate (`blocked`).

Astra round 1 on #906 fences: the session is the attempt's BINDING only
(never a tmux-name match); lifecycle and freshness resolve against the whole
registry before the route's presentation filter.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import holdspeak.agent_context as agent_context
from holdspeak.agent_context import ingest_agent_hook_event
from holdspeak.db import Database
from holdspeak.delivery.factory_launch import LaunchLedger
from holdspeak.services.agent_flights import agent_flights, annotate_sessions
from tests.unit.test_agent_hand import PROJECT, _seed


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "hub.db")
    _seed(database)
    return database


@pytest.fixture
def registry(tmp_path, monkeypatch):
    path = tmp_path / "agent_context.json"
    monkeypatch.setattr(agent_context, "AGENT_CONTEXT_FILE", path)
    return path


def hook(registry, agent: str, sid: str, event: str, *, now=None, **payload):
    return ingest_agent_hook_event(
        agent=agent, state_path=registry, now=now,
        payload={"session_id": sid, "cwd": "/tmp/x", "hook_event_name": event, **payload},
    )


def _attempt(db: Database, session_key: str | None, origin: str) -> str:
    attempt = db.work_attempts.create(
        source_id="src_1", worktree_id="wt_1", project=PROJECT, story_id=origin.replace(":", "-"),
        node_id="this-node", session_id=session_key, target_id="tgt_1", kind="launch",
        exact=True, claimed_by="launch:claude-default", state="working", origin_ref=origin,
    )
    return attempt.attempt_id


def _launch(ledger: LaunchLedger, launch_id: str, origin: tuple[str, str], **fields) -> None:
    ledger.record({
        "launch_id": launch_id, "state": "launched", "profile_id": "claude-default",
        "origin_ref": {"kind": origin[0], "id": origin[1]}, "session": f"hs-{launch_id}",
        "target": {"target_id": "tgt_1", "pane_id": "%1"},
        "launched_at": "2026-10-06T10:00:00Z", **fields,
    })


def test_waiting_session_names_its_item_project_and_agent(db, tmp_path, registry):
    hook(registry, "claude", "s1", "Notification", message="Jordan or Avery?")
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(db, "claude:s1", "action:ai_1"))
    [flight] = agent_flights(db, ledger=ledger)
    assert flight["origin_ref"] == "action:ai_1"
    assert flight["title"] == "Fix the login timeout"
    assert (flight["project_id"], flight["project_name"]) == (PROJECT, "Railsproj")
    assert (flight["agent"], flight["state"], flight["session_key"]) == ("claude", "waiting", "claude:s1")
    assert flight["pr"] is None

    rows = [{"session": {"agent": "claude", "session_id": "s1"}}]
    annotate_sessions(rows, [flight])
    assert rows[0]["flight"]["title"] == "Fix the login timeout"


def test_an_unbound_launch_never_takes_another_pane_s_session_by_name(db, tmp_path, registry):
    """[P1] The launch targets %1 and its tmux session `hs-l2`; no rider has
    bound a session. A hooked session on %999 that happens to sit in a tmux
    session of the same name is NOT this launch's session."""
    hook(registry, "codex", "x1", "PreToolUse", tool_name="Bash", tmux_pane="%999", tmux_session="hs-l2")
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "l2", ("decision", "d1"), profile_id="codex-default", attempt_id=_attempt(db, None, "decision:d1"))
    [flight] = agent_flights(db, ledger=ledger)
    assert (flight["agent"], flight["state"], flight["session_key"]) == ("codex", "starting", None)

    rows = [{"session": {"agent": "codex", "session_id": "x1"}}]
    annotate_sessions(rows, [flight])
    assert "flight" not in rows[0]


def test_ended_and_expired_sessions_are_never_working(db, tmp_path, registry):
    """[P2] SessionEnd is `ended`; a session past the dead window, or gone from
    the registry, is `expired`. None of them reads WORKING."""
    now = datetime.now(timezone.utc)
    hook(registry, "claude", "done", "SessionStart")
    hook(registry, "claude", "done", "SessionEnd")
    hook(registry, "claude", "old", "PreToolUse", tool_name="Write", now=now - timedelta(hours=5))
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(db, "claude:done", "action:ai_1"))
    _launch(ledger, "l2", ("decision", "d1"), attempt_id=_attempt(db, "claude:old", "decision:d1"))
    _launch(ledger, "l3", ("decision_record", "dr1"), attempt_id=_attempt(db, "claude:gone", "decision_record:dr1"))
    states = {f["origin_ref"]: f["state"] for f in agent_flights(db, ledger=ledger, now=now)}
    assert states == {"action:ai_1": "ended", "decision:d1": "expired", "decision_record:dr1": "expired"}


def test_pr_is_the_fact_once_it_exists_even_after_the_session_ended(db, tmp_path, registry):
    hook(registry, "claude", "s1", "SessionEnd")
    ledger = LaunchLedger(tmp_path / "launches.json")
    pr = {"number": 412, "url": "https://github.com/acme/ledger/pull/412", "state": "open"}
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(db, "claude:s1", "action:ai_1"),
            follow_through={"pr": pr, "pr_state": "pr_open"})
    [flight] = agent_flights(db, ledger=ledger)
    assert flight["state"] == "pr_open"
    assert flight["pr"] == {"number": 412, "url": pr["url"], "state": "open"}
    # PHILO-14 C4: the launch's clock rides along (the Conductor's stale window).
    assert flight["launched_at"] == "2026-10-06T10:00:00Z"

    ledger.update("l1", follow_through={
        "pr": {**pr, "state": "merged"}, "close": "closed",
        "evidence": {"merged_at": "2026-10-06T15:29:00Z", "pr_url": pr["url"]},
        "cleanup": {"session": "killed", "worktree": "worktree_removed"},
    })
    [flight] = agent_flights(db, ledger=ledger)
    assert (flight["state"], flight["close"], flight["merged_at"], flight["session_cleanup"]) == (
        "merged", "closed", "2026-10-06T15:29:00Z", "killed")


def test_merged_awaiting_confirm_carries_no_cleanup_evidence(db, tmp_path, registry):
    """[P2] Secure: merged, the close waits for the owner, the session is alive.
    The flight says so (no session_cleanup), so the face keeps the session."""
    hook(registry, "claude", "s1", "PreToolUse", tool_name="Write")
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(db, "claude:s1", "action:ai_1"),
            follow_through={"pr": {"number": 9, "url": "u", "state": "merged"}, "close": "awaiting_confirm"})
    [flight] = agent_flights(db, ledger=ledger)
    assert (flight["state"], flight["close"], flight["session_cleanup"]) == ("merged", "awaiting_confirm", None)


def test_newest_launch_per_item_wins_and_unlaunched_records_are_skipped(db, tmp_path, registry):
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "old", ("action", "ai_1"), profile_id="codex-default")
    _launch(ledger, "new", ("action", "ai_1"))
    _launch(ledger, "failed", ("decision", "d1"), state="failed")
    _launch(ledger, "no-origin", ("", ""))
    flights = agent_flights(db, ledger=ledger)
    assert [(f["origin_ref"], f["launch_id"], f["agent"], f["state"]) for f in flights] == [
        ("action:ai_1", "new", "claude", "starting")]


def test_sessions_route_resolves_before_the_presentation_filter(monkeypatch, tmp_path, registry):
    """[P2] SessionEnd, then `include_ended=false`: no session is listed, and
    the flight says `ended`, never WORKING."""
    from types import SimpleNamespace

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import holdspeak.db as dbmod
    from holdspeak.delivery import factory_launch
    from holdspeak.web.routes.system.coders import build_coders_router

    database = Database(tmp_path / "hub.db")
    _seed(database)
    hook(registry, "claude", "s1", "SessionStart")
    hook(registry, "claude", "s1", "SessionEnd")
    hook(registry, "codex", "x1", "Notification", message="Allow Bash?")
    launches = tmp_path / "launches.json"
    ledger = LaunchLedger(launches)
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(database, "claude:s1", "action:ai_1"))
    _launch(ledger, "l2", ("decision", "d1"), profile_id="codex-default", attempt_id=_attempt(database, "codex:x1", "decision:d1"))
    monkeypatch.setattr(dbmod, "get_database", lambda: database)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", launches)
    app = FastAPI()
    app.include_router(build_coders_router(SimpleNamespace(broadcast=None)))
    body = TestClient(app).get("/api/coders/sessions?include_ended=false").json()
    assert [r["session"]["session_id"] for r in body["sessions"]] == ["x1"]
    assert {f["origin_ref"]: f["state"] for f in body["flights"]} == {"action:ai_1": "ended", "decision:d1": "waiting"}
    assert body["sessions"][0]["flight"]["title"] == "Use Redis for sessions"
