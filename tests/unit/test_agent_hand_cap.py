"""Betterment AG5: working at once, and a queue.

The limit is the setting ``agents.working_at_once`` (default 6). Only an
agent that starts, works or needs the owner holds a slot: a done turn, a
quiet (idle) one and a launch stopped by a restart do not. At the limit a
hand with ``queue`` waits in ``agent_hand_queue`` and the heartbeat's
``start_queued`` starts it when a slot frees.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from holdspeak.config import Config
from holdspeak.config.agents import AgentsConfig
from holdspeak.delivery import factory_launch
from holdspeak.delivery.factory_launch import LaunchLedger
from holdspeak.services.agent_hand_queue import HandQueue, queued_flights, start_queued
from holdspeak.services.agent_hand_service import AgentHandRefused, working_at_once, working_launches
from tests.unit.test_agent_flights import _attempt, _launch, _turn, hook
from tests.unit.test_agent_flights import db, registry  # noqa: F401  (fixtures)
from tests.unit.test_agent_hand import OWNER, _rig

DONE = "Done. The timeout is fixed and the tests pass. Branch is ready for review."
QUESTION = "Should I also bump the retry count, or keep it at three?"


def _launcher(ledger: LaunchLedger, alive: bool = True) -> SimpleNamespace:
    return SimpleNamespace(_ledger=ledger, _session_alive=lambda _name: alive)


def test_done_quiet_and_stopped_agents_do_not_count(db, tmp_path, registry):  # noqa: F811
    """Three agents, two done: one slot is taken. An agent that asks and one
    that has not registered take a slot; an idle one and one stopped by a
    restart do not."""
    ledger = LaunchLedger(tmp_path / "launches.json")
    _turn(registry, "done1", DONE)
    _turn(registry, "done2", DONE)
    hook(registry, "claude", "busy", "UserPromptSubmit", prompt="the brief")
    hook(registry, "claude", "busy", "PreToolUse", tool_name="Bash")
    _launch(ledger, "l1", ("action", "ai_1"), attempt_id=_attempt(db, "claude:done1", "action:ai_1"))
    _launch(ledger, "l2", ("decision", "d1"), attempt_id=_attempt(db, "claude:done2", "decision:d1"))
    _launch(ledger, "l3", ("decision_record", "dr1"), attempt_id=_attempt(db, "claude:busy", "decision_record:dr1"))
    assert [r["launch_id"] for r in working_launches(_launcher(ledger), db)] == ["l3"]

    _turn(registry, "asks", QUESTION)
    hook(registry, "claude", "quiet", "SessionStart", source="startup")
    hook(registry, "claude", "quiet", "Notification", notification_type="idle_prompt",
         message="Claude is waiting for your input")
    _launch(ledger, "l4", ("action", "ai_2"), attempt_id=_attempt(db, "claude:asks", "action:ai_2"))
    _launch(ledger, "l5", ("action", "ai_3"), attempt_id=_attempt(db, "claude:quiet", "action:ai_3"))
    _launch(ledger, "l6", ("action", "ai_4"), attempt_id=_attempt(db, None, "action:ai_4"))
    _launch(ledger, "l7", ("action", "ai_5"), state="stopped_by_restart",
            attempt_id=_attempt(db, "claude:busy2", "action:ai_5"))
    assert sorted(r["launch_id"] for r in working_launches(_launcher(ledger), db)) == ["l3", "l4", "l6"]
    # A launch whose tmux session is gone holds nothing (as before AG5).
    assert working_launches(_launcher(ledger, alive=False), db) == []


def test_the_setting_defaults_to_six_and_is_clamped(tmp_path, monkeypatch):
    assert AgentsConfig().working_at_once == 6
    assert AgentsConfig(working_at_once=0).working_at_once == 1
    assert AgentsConfig(working_at_once=99).working_at_once == 20
    assert AgentsConfig(working_at_once="x").working_at_once == 6
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"agents": {"working_at_once": 8}}), encoding="utf-8")
    assert Config.load(path).agents.working_at_once == 8
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls, *a, **k: Config()))
    assert working_at_once() == 6


def test_the_settings_write_takes_the_limit(tmp_path, monkeypatch):
    """Settings ▸ Agents writes `agents.working_at_once` through the one
    settings update (clamped)."""
    from holdspeak.config import core as config_core
    from holdspeak.db import Database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.settings_service import SettingsService

    path = tmp_path / "config.json"
    monkeypatch.setattr(config_core, "_active_config_file", lambda: path)
    Config().save(path)
    service = SettingsService(Database(tmp_path / "settings.db"))
    service.update_settings(Principal(PrincipalKind.OWNER, "owner-session"), {"agents": {"working_at_once": 4}})
    assert Config.load(path).agents.working_at_once == 4
    service.update_settings(Principal(PrincipalKind.OWNER, "owner-session"), {"agents": {"working_at_once": 0}})
    assert Config.load(path).agents.working_at_once == 1


@pytest.fixture
def queue_home(tmp_path, monkeypatch):
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", tmp_path / "home-launches.json")
    return tmp_path / "agent_hand_queue.json"


def test_at_the_limit_a_hand_waits_and_starts_when_a_slot_frees(tmp_path, db, monkeypatch, queue_home, registry):  # noqa: F811
    rig = _rig(tmp_path, db, monkeypatch)
    rig.hand._max_live = 1
    first = rig.hand.hand(OWNER, "action", "ai_1")
    assert first["status"] == "launched"
    # The launched agent works (its rider's session, as the hooks report it).
    hook(registry, "claude", "smoke-session", "UserPromptSubmit", prompt="the brief")
    # Without the queue the limit still refuses by name.
    with pytest.raises(AgentHandRefused) as exc:
        rig.hand.hand(OWNER, "decision", "d1")
    assert exc.value.code == "launch_cap_reached"
    # "Start when one is free": the hand waits; nothing is made yet.
    waiting = rig.hand.hand(OWNER, "decision", "d1", queue=True)
    assert waiting["status"] == "queued" and waiting["working_at_once"] == 1
    assert not (rig.repo.parent / "hs-decision-d1").exists()
    assert queue_home.exists()
    # A second press on the same item keeps one entry.
    assert rig.hand.hand(OWNER, "decision", "d1", queue=True)["queue_id"] == waiting["queue_id"]
    [flight] = queued_flights(db)
    assert (flight["origin_ref"], flight["state"], flight["launch_id"]) == ("decision:d1", "queued", None)

    # The heartbeat with no free slot leaves it queued.
    assert start_queued(rig.hand) == []
    assert len(HandQueue().list()) == 1
    # The first agent's session ends: the slot is free, the queued hand starts.
    rig.tmux.ended = True
    [started] = start_queued(rig.hand)
    assert started["status"] == "launched" and started["origin_ref"] == {"kind": "decision", "id": "d1"}
    assert (rig.repo.parent / "hs-decision-d1").exists()
    assert HandQueue().list() == []


def test_a_queued_hand_the_hand_refuses_leaves_the_queue(tmp_path, db, monkeypatch, queue_home):  # noqa: F811
    rig = _rig(tmp_path, db, monkeypatch)
    HandQueue().add("action", "no_such_item")
    [answer] = start_queued(rig.hand)
    assert (answer["status"], answer["code"]) == ("refused", "item_unknown")
    assert HandQueue().list() == []


def test_the_route_answers_202_for_a_queued_hand(monkeypatch, tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from holdspeak.web.routes import agent_hand as route

    class _Ops:
        def invoke(self, _principal, name, body):
            assert name == "agent.hand" and body["queue"] is True
            return {"status": "queued", "queue_id": "queue_1"}

    app = FastAPI()
    monkeypatch.setattr("holdspeak.operations.for_context", lambda *_a, **_k: _Ops())
    app.include_router(route.build_agent_hand_router(SimpleNamespace()))
    answer = TestClient(app).post("/api/agent/hand", json={"kind": "action", "id": "ai_1", "queue": True})
    assert answer.status_code == 202 and answer.json()["status"] == "queued"
