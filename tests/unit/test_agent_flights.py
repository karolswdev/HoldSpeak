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
    pr = {"number": 412, "url": "https://github.com/acme/ledger/pull/412", "state": "open",
          "title": "Freeze the ledger before the cutover"}
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(db, "claude:s1", "action:ai_1"),
            follow_through={"pr": pr, "pr_state": "pr_open"})
    [flight] = agent_flights(db, ledger=ledger)
    assert flight["state"] == "pr_open"
    # PHILO-15 B50: the PR's own title rides with it (the drawer's PR object).
    assert flight["pr"] == {"number": 412, "url": pr["url"], "state": "open",
                            "title": "Freeze the ledger before the cutover"}
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


# ── PHILO-14 C4 (Astra r1 on #947, finding 4): the Conductor's history ──


def test_history_cuts_on_the_end_not_the_launch(db, tmp_path, registry):
    """A launch started 30 h ago that ended 2 min ago is in the last 24 h;
    one that ended 25 h ago is not. Through hook ingest and the ledger."""
    from holdspeak.services.agent_flights import launch_history

    now = datetime.now(timezone.utc)
    hook(registry, "claude", "late", "SessionStart", now=now - timedelta(hours=30))
    hook(registry, "claude", "late", "SessionEnd", now=now - timedelta(minutes=2))
    hook(registry, "claude", "early", "SessionStart", now=now - timedelta(hours=30))
    hook(registry, "claude", "early", "SessionEnd", now=now - timedelta(hours=25))
    ledger = LaunchLedger(tmp_path / "launches.json")
    old = (now - timedelta(hours=30)).isoformat().replace("+00:00", "Z")
    _launch(ledger, "l-late", ("action", "ai_1"), launched_at=old, attempt_id=_attempt(db, "claude:late", "action:ai_1"))
    _launch(ledger, "l-early", ("decision", "d1"), launched_at=old, attempt_id=_attempt(db, "claude:early", "decision:d1"))
    history = launch_history(db, ledger=ledger, now=now)
    assert [(f["launch_id"], f["state"]) for f in history] == [("l-late", "ended")]
    ended = datetime.fromisoformat(history[0]["ended_at"].replace("Z", "+00:00"))
    assert abs((now - ended).total_seconds() - 120) < 5
    [flight] = [f for f in agent_flights(db, ledger=ledger, now=now) if f["launch_id"] == "l-late"]
    assert flight["ended_at"] == history[0]["ended_at"]


def test_a_relaunch_keeps_the_earlier_receipt(db, tmp_path, registry):
    """Relaunching an item: the flight is the new launch; the earlier launch,
    merged and closed an hour ago, stays in the history with its close."""
    from holdspeak.services.agent_flights import launch_history

    now = datetime.now(timezone.utc)
    hook(registry, "claude", "first", "SessionEnd", now=now - timedelta(hours=1))
    hook(registry, "claude", "second", "PreToolUse", tool_name="Write")
    ledger = LaunchLedger(tmp_path / "launches.json")
    merged_at = (now - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    _launch(ledger, "first", ("action", "ai_1"), attempt_id=_attempt(db, "claude:first", "action:ai_1"),
            follow_through={"pr": {"number": 412, "url": "u", "state": "merged"}, "close": "closed",
                            "evidence": {"merged_at": merged_at}})
    _launch(ledger, "second", ("action", "ai_1"), attempt_id=_attempt(db, "claude:second", "action:ai_1"))
    assert [(f["launch_id"], f["state"], f["ended_at"]) for f in agent_flights(db, ledger=ledger, now=now)] == [
        ("second", "working", None)]
    history = launch_history(db, ledger=ledger, now=now)
    assert [(f["launch_id"], f["state"], f["close"], f["ended_at"]) for f in history] == [
        ("first", "merged", "closed", merged_at)]


def test_sessions_route_serves_history_and_the_hub_launch_count(monkeypatch, tmp_path, registry):
    """[finding 7] The cap is the hub's count (`live_launches`: launched,
    follow-through not done, tmux session alive), never the client's: an
    open PR whose agent left is not a running launch."""
    from types import SimpleNamespace

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import holdspeak.db as dbmod
    from holdspeak.delivery import factory_launch
    from holdspeak.web.routes.system.coders import build_coders_router

    database = Database(tmp_path / "hub.db")
    _seed(database)
    hook(registry, "claude", "s1", "SessionEnd")
    launches = tmp_path / "launches.json"
    ledger = LaunchLedger(launches)
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(database, "claude:s1", "action:ai_1"),
            follow_through={"pr": {"number": 7, "url": "u", "state": "open"}, "pr_state": "pr_open"})
    monkeypatch.setattr(dbmod, "get_database", lambda: database)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", launches)
    alive = {"hs-l1": False}

    class Reads:
        def launcher(self):
            from holdspeak.services.agent_hand_preview import LaunchReads

            launcher = LaunchReads(ledger_path=launches).launcher()
            launcher._session_alive = lambda name: alive.get(name, False)
            return launcher

    app = FastAPI()
    app.include_router(build_coders_router(SimpleNamespace(broadcast=None, agent_hand_reads=Reads())))
    body = TestClient(app).get("/api/coders/sessions?include_ended=false").json()
    # Betterment AG5: the cap is the setting `agents.working_at_once` (default 6).
    assert body["launches"] == {"live": 0, "cap": 6}
    assert body["history"] == []
    assert [f["state"] for f in body["flights"]] == ["pr_open"]
    alive["hs-l1"] = True
    # AG5: a live tmux session whose agent ended holds no slot ...
    assert TestClient(app).get("/api/coders/sessions").json()["launches"] == {"live": 0, "cap": 6}
    # ... an agent that works does.
    hook(registry, "claude", "s1", "UserPromptSubmit", prompt="the next step")
    assert TestClient(app).get("/api/coders/sessions").json()["launches"] == {"live": 1, "cap": 6}


# ── Betterment AG0: tell the truth about state ───────────────────────
#
# The hook sequence is the fake Claude Code's (docs/internal/betterment/
# agents/rig/fake_claude.py), which the recon walk recorded end to end.

QUESTION = ("I found two places for the rollback flag. Should it live in "
            "config/flags.yaml (shared with staging) or in an env var (per host)? "
            "Answer 1 for config, 2 for env.")
DONE = ("Done. The rollback flag now lives in the place you chose, with a test. "
        "Branch is ready for review; I did not open a PR.")


def _turn(registry, sid: str, words: str, *, now=None) -> None:
    hook(registry, "claude", sid, "UserPromptSubmit", prompt="the brief", now=now)
    hook(registry, "claude", sid, "PostToolUse", tool_name="Bash", now=now)
    hook(registry, "claude", sid, "Stop", last_assistant_message=words, now=now)


def test_a_stop_without_a_question_is_done_without_a_pr(db, tmp_path, registry):
    """RECON step 13: "Done. … I did not open a PR." read "Working" forever.
    Now it is done and new, and Claude Code's idle reminder after it (the
    Notification `idle_prompt`) keeps it done, never an ask."""
    hook(registry, "claude", "s1", "SessionStart", source="startup")
    _turn(registry, "s1", DONE)
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(db, "claude:s1", "action:ai_1"))
    [flight] = agent_flights(db, ledger=ledger)
    assert (flight["state"], flight["turn_end"], flight["new"]) == ("done", "done", True)
    assert flight["turn_id"] and flight["pr"] is None
    hook(registry, "claude", "s1", "Notification", notification_type="idle_prompt",
         message="Claude is waiting for your input")
    [after] = agent_flights(db, ledger=ledger)
    assert (after["state"], after["turn_id"], after["new"]) == ("done", flight["turn_id"], True)


def test_a_stop_with_a_question_asks(db, tmp_path, registry):
    _turn(registry, "s1", QUESTION)
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(db, "claude:s1", "action:ai_1"))
    [flight] = agent_flights(db, ledger=ledger)
    assert (flight["state"], flight["turn_end"], flight["new"]) == ("waiting", "asks", False)


def test_a_session_start_alone_is_never_done(db, tmp_path, registry):
    """herdr's completion sequence: a start-up (or a restored session) that
    goes idle, or stops with no prompt before it, finished nothing."""
    hook(registry, "claude", "s1", "SessionStart", source="startup")
    hook(registry, "claude", "s1", "Notification", notification_type="idle_prompt",
         message="Claude is waiting for your input")
    hook(registry, "claude", "s2", "SessionStart", source="resume")
    hook(registry, "claude", "s2", "Stop", last_assistant_message="Ready.")
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(db, "claude:s1", "action:ai_1"))
    _launch(ledger, "l2", ("decision", "d1"), attempt_id=_attempt(db, "claude:s2", "decision:d1"))
    states = {f["launch_id"]: (f["state"], f["turn_end"], f["new"]) for f in agent_flights(db, ledger=ledger)}
    assert states == {"l1": ("waiting", "idle", False), "l2": ("waiting", "idle", False)}


def test_seen_makes_a_done_turn_quiet_and_the_next_turn_is_new_again(monkeypatch, tmp_path, registry):
    """`POST /api/agent/launches/{id}/seen` stores the done turn's id as
    `seen_wait_id`: the flight is no longer new. The next done turn is."""
    from types import SimpleNamespace

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import holdspeak.db as dbmod
    from holdspeak.delivery import factory_launch
    from holdspeak.web.routes.agent_hand import build_agent_hand_router

    database = Database(tmp_path / "hub.db")
    _seed(database)
    launches = tmp_path / "launches.json"
    ledger = LaunchLedger(launches)
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(database, "claude:s1", "action:ai_1"))
    monkeypatch.setattr(dbmod, "get_database", lambda: database)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", launches)
    app = FastAPI()
    app.include_router(build_agent_hand_router(SimpleNamespace()))
    client = TestClient(app)

    assert client.post("/api/agent/launches/l1/seen", json={}).json()["seen"] is None
    _turn(registry, "s1", DONE)
    [first] = agent_flights(database, ledger=ledger)
    assert first["new"] is True
    seen = client.post("/api/agent/launches/l1/seen", json={})
    assert seen.status_code == 200 and seen.json()["seen"] == first["turn_id"]
    [quiet] = agent_flights(database, ledger=ledger)
    assert (quiet["state"], quiet["new"]) == ("done", False)

    later = datetime.now(timezone.utc) + timedelta(seconds=30)
    _turn(registry, "s1", "Done. The test now covers the env var too.", now=later)
    [second] = agent_flights(database, ledger=ledger)
    assert second["turn_id"] != first["turn_id"] and second["new"] is True
    assert client.post("/api/agent/launches/nope/seen", json={}).status_code == 404


def test_a_missing_tmux_session_is_stopped_by_restart(db, tmp_path, registry):
    """RECON step 21: after `tmux kill-server` and a hub restart both agents
    still asked. The check on hub start marks each launch whose tmux session
    is gone; its session ends, so Needs you and the Conductor drop the ask."""
    from holdspeak.agent_context import list_agent_sessions
    from holdspeak.services.agent_flights import launch_history
    from holdspeak.services.launch_lane import record_restart_stops
    from holdspeak.services.needs_you_membership import coder_items

    _turn(registry, "s1", QUESTION)
    _turn(registry, "s2", QUESTION)
    _turn(registry, "s3", DONE)
    hook(registry, "claude", "s4", "SessionEnd")
    ledger = LaunchLedger(tmp_path / "launches.json")
    for n, origin in (("1", ("action", "ai_1")), ("2", ("decision", "d1")),
                      ("3", ("decision_record", "dr1")), ("4", ("note", "n1"))):
        _launch(ledger, f"l{n}", origin, attempt_id=_attempt(db, f"claude:s{n}", f"{origin[0]}:{origin[1]}"))
    assert len(coder_items(list_agent_sessions(), datetime.now(timezone.utc))) == 2

    # hs-l1 and hs-l4 are gone; hs-l2 is alive; tmux could not be asked for hs-l3.
    alive = {"hs-l1": False, "hs-l2": True, "hs-l3": None, "hs-l4": False}
    stopped = record_restart_stops(db=db, ledger=ledger, alive=alive.get)
    assert stopped == ["l1"]   # l4's session ended by itself
    states = {f["launch_id"]: f["state"] for f in agent_flights(db, ledger=ledger)}
    assert states == {"l1": "stopped_by_restart", "l2": "waiting", "l3": "done", "l4": "ended"}
    assert ledger.get("l1")["stopped"]["by"] == "restart"
    assert [s.session_id for s in list_agent_sessions() if s.lifecycle == "ended"] == ["s1", "s4"]
    [row] = coder_items(list_agent_sessions(), datetime.now(timezone.utc))
    assert row["sessionKey"] == "claude:s2"
    history = {f["launch_id"]: f["state"] for f in launch_history(db, ledger=ledger)}
    assert history == {"l1": "stopped_by_restart", "l4": "ended"}
    # A second check changes nothing.
    assert record_restart_stops(db=db, ledger=ledger, alive=alive.get) == []


def test_a_done_turn_is_a_coder_frame_and_never_a_wait(registry):
    """The watcher frames a completed turn within one 2 s read (the faces
    read Done at once), and never runs the notify decision for it."""
    from holdspeak.web_server import _coder_watch_step

    hook(registry, "claude", "s1", "SessionStart", source="startup")
    snapshot, _, _ = _coder_watch_step(None, registry)
    hook(registry, "claude", "s1", "UserPromptSubmit", prompt="the brief")
    snapshot, transitions, entered = _coder_watch_step(snapshot, registry)
    assert (transitions, entered) == ([], [])
    hook(registry, "claude", "s1", "Stop", last_assistant_message=DONE)
    snapshot, transitions, entered = _coder_watch_step(snapshot, registry)
    assert (transitions, entered) == (["claude:s1"], [])
    _, transitions, entered = _coder_watch_step(snapshot, registry)
    assert (transitions, entered) == ([], [])


def test_a_durable_review_result_wins_over_a_stale_working_screen(db, tmp_path, registry, monkeypatch):
    """AG12: a pane sampled before the final pair result cannot undo Done."""
    from holdspeak import agent_context
    from holdspeak.services import agent_flights as flights_module

    hook(registry, "claude", "review", "PreToolUse", tool_name="Read")
    session = next(s for s in agent_context.list_agent_sessions() if s.session_id == "review")
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(
        ledger, "review-done", ("action", "ai_1"),
        attempt_id=_attempt(db, "claude:review", "action:ai_1"),
        review={
            "requested": "claude", "status": "done", "role": "builder",
            "result": {"rounds": 2, "findings_left": [], "wording": "round 2, nothing left"},
        },
    )
    monkeypatch.setattr(
        flights_module, "_screen",
        lambda *_args: (None, "screen", ("working", None)),
    )

    flight = flights_module._flight(
        db, ledger.get("review-done"), {"claude:review": session}, datetime.now(timezone.utc),
    )
    assert (flight["state"], flight["state_source"], flight["turn_end"]) == ("done", "review", "done")
    assert flight["review"]["pair_result"]["rounds"] == 2


def test_a_review_finding_projects_as_an_owner_wait_after_a_stale_screen(db, tmp_path, registry, monkeypatch):
    """AG12: a persisted MUST finding is Waiting/Needs you across the fleet wire."""
    from holdspeak import agent_context
    from holdspeak.services import agent_flights as flights_module

    hook(registry, "claude", "review", "PreToolUse", tool_name="Read")
    session = next(s for s in agent_context.list_agent_sessions() if s.session_id == "review")
    ledger = LaunchLedger(tmp_path / "launches.json")
    _launch(
        ledger, "review-needs-you", ("action", "ai_1"),
        attempt_id=_attempt(db, "claude:review", "action:ai_1"),
        review={
            "requested": "claude", "status": "needs_you", "role": "builder",
            "findings_left": [{"level": "MUST", "text": "review_target.txt: apply the correction"}],
            "result": {
                "rounds": 1,
                "findings_left": [{"level": "MUST", "text": "review_target.txt: apply the correction"}],
            },
        },
    )
    monkeypatch.setattr(
        flights_module, "_screen",
        lambda *_args: (None, "screen", ("working", None)),
    )

    flight = flights_module._flight(
        db, ledger.get("review-needs-you"), {"claude:review": session}, datetime.now(timezone.utc),
    )
    assert (flight["state"], flight["state_source"], flight["turn_end"]) == ("waiting", "review", "asks")
    assert flight["review"]["status"] == "needs_you"
    assert flight["review"]["findings_left"][0]["level"] == "MUST"
