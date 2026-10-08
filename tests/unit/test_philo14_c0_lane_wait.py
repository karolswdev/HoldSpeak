"""PHILO-14 C0 (Astra R1 P2): the lane's wait honors the responder.

Through the real launch and responder paths (the K5 rig): a wait HoldSpeak
answered under YOLO is not a wait on the lane (its answer is in
``answers``), and a wait HoldSpeak is still deciding reads DECIDING, never
TO ANSWER.
"""
from __future__ import annotations

from types import SimpleNamespace

from holdspeak.agent_context import read_agent_sessions_strict
from holdspeak.services.agent_responder import ANSWERED
from holdspeak.services.launch_lane import DECIDING_KIND, launch_lane
from tests.unit.test_conductor_k5_supervision import (  # noqa: F401  (fixtures)
    KEY,
    ROUTINE_REPLY,
    _ask,
    _members,
    _model,
    _responder,
    db,
    launched,
)


def _lane(rig, tmp_path):
    reads = SimpleNamespace(launcher=lambda: SimpleNamespace(_ledger=rig.launches), registry=lambda: rig.registry)
    sessions = read_agent_sessions_strict(state_path=tmp_path / "agent_sessions.json")
    return launch_lane(
        rig.launch_id, db=rig.db, reads=reads, sessions=sessions, answers=rig.store,
        spool_dir=tmp_path / "agent-events",
    )


def test_a_deciding_wait_reads_deciding_and_an_answered_wait_is_gone(launched, tmp_path, monkeypatch) -> None:
    _model(launched, tmp_path, monkeypatch, ROUTINE_REPLY)
    _ask(launched, tmp_path, monkeypatch, "Shall I run the tests before I open the pull request?")
    responder = _responder(launched, tmp_path, "yolo")

    assert responder.triage([KEY]) == {"notify": [], "decide": [KEY]}
    lane = _lane(launched, tmp_path)
    assert lane["launch"]["session_key"] == KEY
    assert lane["wait"]["kind"] == DECIDING_KIND and lane["wait"]["wait_kind"] == "deciding"
    assert _members(launched, tmp_path) == [], "Needs you holds it back too"

    assert responder.decide(KEY)["outcome"] == ANSWERED
    lane = _lane(launched, tmp_path)
    assert lane["wait"] is None, "an answered wait is not a wait"
    assert _members(launched, tmp_path) == []
    assert [a["outcome"] for a in lane["answers"] if a["outcome"] == "auto_answered"] == ["auto_answered"]
    [answer] = [a for a in lane["answers"] if a["outcome"] == "auto_answered"]
    assert answer["text_head"].startswith("The desk: Yes. The brief says")  # PHILO-15 15
