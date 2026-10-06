"""Conductor K3: a waiting coding agent reaches Needs you at once.

R5 membership (fresh awaiting in, stale out, answered out), the ranking
(a blocked agent ranks with the due-today rows), the ``coder`` coverage
kind, and the immediate edge (the Heartbeat's notify decision on the
transition into awaiting: Notify mode, quiet hours, fires once).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import needs_you_membership as membership
from holdspeak.services.attention_ranking import attention_class
from holdspeak.services.needs_you_aggregate import COVERAGE_KINDS, _read_dirty_at
from holdspeak.services.needs_you_membership import coder_items, compute_needs_you

NOW = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
OWNER = Principal(PrincipalKind.OWNER, "test")


def _session(
    session_id: str = "s1",
    *,
    agent: str = "claude",
    minutes_ago: float = 2,
    awaiting: bool = True,
    question: str | None = "Should I keep the old migration or drop it?",
    lifecycle: str = "waiting",
    event: str = "Stop",
) -> dict[str, Any]:
    return {
        "agent": agent,
        "session_id": session_id,
        "cwd": "/work/holdspeak",
        "project_name": "holdspeak",
        "repo_root": "/work/holdspeak",
        "updated_at": (NOW - timedelta(minutes=minutes_ago)).isoformat(),
        "hook_event_name": event,
        "awaiting_response": awaiting,
        "lifecycle": lifecycle,
        "question": question,
    }


# ── R5 membership ────────────────────────────────────────────────────


def test_a_fresh_awaiting_coder_is_a_member_with_its_facts() -> None:
    rows = coder_items([_session(agent="codex")], NOW)
    assert len(rows) == 1
    row = rows[0]
    assert row["ref"] == row["id"] == "coder:codex:s1"
    assert row["kind"] == row["source"] == "coder"
    assert row["sessionKey"] == "codex:s1"
    assert row["agent"] == "codex"
    assert row["cwd"] == "/work/holdspeak"
    assert row["projectName"] == "holdspeak"
    assert row["question"] == row["title"] == "Should I keep the old migration or drop it?"
    assert row["ageSeconds"] == 120
    assert row["why"] == "TO ANSWER"

    result = compute_needs_you(coders=[_session()], now=NOW)
    assert [m["ref"] for m in result["members"]] == ["coder:claude:s1"]
    assert result["count"] == 1 and result["waitingCount"] == 0


def test_a_stale_awaiting_coder_is_not_a_member() -> None:
    # 30 min is the agent_context recent default; 31 min is out.
    assert coder_items([_session(minutes_ago=31)], NOW) == []
    assert len(coder_items([_session(minutes_ago=29)], NOW)) == 1


def test_an_answered_coder_is_not_a_member() -> None:
    # The answer (a UserPromptSubmit or a clear) drops the flag and the question.
    assert coder_items([_session(awaiting=False, question=None, lifecycle="working")], NOW) == []
    assert coder_items([_session(awaiting=False)], NOW) == []
    assert coder_items([_session(question=None)], NOW) == []
    assert coder_items([_session(question="   ")], NOW) == []


def test_a_permission_prompt_is_a_member_to_approve() -> None:
    # The Notification hook records the ask and lifecycle ``waiting`` but
    # does not set ``awaiting_response``: the agent is still blocked on him.
    prompt = _session(awaiting=False, event="Notification",
                      question="Claude needs your permission to use Bash")
    rows = coder_items([prompt], NOW)
    assert [r["ref"] for r in rows] == ["coder:claude:s1"]
    assert rows[0]["why"] == "TO APPROVE"
    assert attention_class(rows[0], NOW.astimezone().replace(tzinfo=None)) == "due_today"
    # A question stays TO ANSWER.
    assert coder_items([_session()], NOW)[0]["why"] == "TO ANSWER"


def test_a_permission_prompt_that_is_stale_ended_or_empty_is_not_a_member() -> None:
    def prompt(**kw: Any) -> dict[str, Any]:
        base: dict[str, Any] = dict(awaiting=False, event="Notification", question="Allow Bash?")
        base.update(kw)
        return _session(**base)

    assert coder_items([prompt(minutes_ago=31)], NOW) == []
    assert coder_items([prompt(lifecycle="ended")], NOW) == []
    assert coder_items([prompt(question=None)], NOW) == []
    # Answered: the next working event replaces the latest hook event.
    assert coder_items([prompt(event="PreToolUse", lifecycle="working")], NOW) == []


def test_the_watcher_counts_a_permission_prompt_as_blocked() -> None:
    from holdspeak.agent_context import AgentSession
    from holdspeak.coder_steering import awaiting_snapshot

    prompt = AgentSession.from_mapping(
        _session(awaiting=False, event="Notification", question="Allow Bash?"))
    idle = AgentSession.from_mapping(_session("s2", awaiting=False, question=None, lifecycle="working"))
    assert awaiting_snapshot([prompt, idle]) == {"claude:s1": True, "claude:s2": False}


def test_an_ended_coder_is_not_a_member() -> None:
    assert coder_items([_session(lifecycle="ended")], NOW) == []


def test_a_coder_reads_the_agent_session_object_too() -> None:
    from holdspeak.agent_context import AgentSession

    rows = coder_items([AgentSession.from_mapping(_session())], NOW)
    assert [r["ref"] for r in rows] == ["coder:claude:s1"]


def test_a_long_question_is_cut_to_an_excerpt() -> None:
    rows = coder_items([_session(question="word " * 200)], NOW)
    assert len(rows[0]["question"]) == membership.CODER_EXCERPT_CHARS
    assert rows[0]["question"].endswith("…")


# ── ranking ──────────────────────────────────────────────────────────


def test_a_blocked_agent_ranks_with_the_due_today_rows() -> None:
    local_now = NOW.astimezone().replace(tzinfo=None)
    coder = coder_items([_session()], NOW)[0]
    assert attention_class(coder, local_now) == "due_today"

    room = [
        {"id": "p1:github:old", "ref": "old", "projectId": "p1", "title": "No due date row",
         "why": "CI RED", "since": (NOW - timedelta(days=1)).isoformat(), "source": "github",
         "severity": "danger"},
        {"id": "p1:jira:late", "ref": "late", "projectId": "p1", "title": "Overdue row",
         "why": "OVERDUE", "dueAt": (local_now - timedelta(days=2)).date().isoformat(),
         "source": "jira", "severity": "danger"},
    ]
    result = compute_needs_you(room_items=room, coders=[_session()], now=local_now)
    order = [row["ref"] for row in result["unmutedItems"]]
    assert order == ["late", "coder:claude:s1", "old"], order
    assert result["unmutedItems"][1]["rankClass"] == "due_today"


def test_two_blocked_agents_rank_oldest_wait_first() -> None:
    local_now = NOW.astimezone().replace(tzinfo=None)
    result = compute_needs_you(
        coders=[_session("new", minutes_ago=1), _session("old", minutes_ago=20)], now=local_now,
    )
    assert [row["ref"] for row in result["unmutedItems"]] == ["coder:claude:old", "coder:claude:new"]


# ── coverage kind ───────────────────────────────────────────────────


def _stub_hub_reads(monkeypatch: pytest.MonkeyPatch, coders: Any) -> None:
    monkeypatch.setattr(membership, "_read_door", lambda db, p: {"board": {}, "people_store_state": None})
    monkeypatch.setattr(membership, "_read_assignments", lambda db, p: {"task_overrides": []})
    monkeypatch.setattr(membership, "_read_summary_attention", lambda db, p: [])
    monkeypatch.setattr(membership, "_read_decisions", lambda db, p: [])
    monkeypatch.setattr(membership, "_read_coders", coders)


def test_coder_is_a_coverage_kind() -> None:
    assert "coder" in COVERAGE_KINDS


def test_compose_reads_the_coders_and_names_their_coverage(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_hub_reads(monkeypatch, lambda: [_session()])
    aggregate = {"items": [], "coverage": [], "complete": True}
    answer = membership.compose(None, OWNER, aggregate, muted_project_ids=[], now=NOW)
    assert [m["ref"] for m in answer["members"]] == ["coder:claude:s1"]
    coder_rows = [row for row in answer["coverage"] if row["kind"] == "coder"]
    assert len(coder_rows) == 1 and coder_rows[0]["state"] == "available"
    assert answer["complete"] is True

    # A recomposed (cached) answer keeps ONE coder coverage record.
    again = membership.compose(None, OWNER, membership.room_part(answer), muted_project_ids=[], now=NOW)
    assert len([row for row in again["coverage"] if row["kind"] == "coder"]) == 1


def test_a_failed_coder_read_is_named_never_a_silent_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken() -> list[Any]:
        raise OSError("registry unreadable")

    _stub_hub_reads(monkeypatch, broken)
    answer = membership.compose(None, OWNER, {"items": [], "coverage": [], "complete": True},
                                muted_project_ids=[], now=NOW)
    assert answer["sourceErrors"]["coders"] == "registry unreadable"
    assert answer["complete"] is False
    row = next(row for row in answer["coverage"] if row["kind"] == "coder")
    assert row["state"] == "failed" and row["repair"]["token"] == "READ FAILED"


# ── the immediate edge ───────────────────────────────────────────────


class _Clock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "k3.db")


def _service(db: Database, calls: list[tuple[str, str]], *, at: datetime, notify: str = "edge"):
    from holdspeak.services.heartbeat_service import HeartbeatService

    def notifier(title: str, body: str, *, click_url=None) -> bool:
        calls.append((title, body))
        return True

    svc = HeartbeatService(db, notifier=notifier, clock=_Clock(at), local_zone=timezone.utc)
    svc.update_settings({"notify": notify, "quiet_hours": {"start": 22, "end": 8}})
    return svc


def _coder_aggregate() -> dict[str, Any]:
    result = compute_needs_you(coders=[_session()], now=NOW)
    return {
        "count": result["count"], "projects": [], "items": result["unmutedItems"],
        "members": result["members"], "coverage": [], "complete": True,
    }


def _edge(svc) -> dict[str, Any]:
    with patch.object(svc, "_build_aggregate_via_canonical", return_value=_coder_aggregate()):
        return svc.notify_coder_edge(OWNER, session_key="claude:s1")


def test_the_edge_fires_once_and_marks_needs_you_dirty(db: Database) -> None:
    calls: list[tuple[str, str]] = []
    svc = _service(db, calls, at=NOW)
    assert _read_dirty_at(db) is None
    first = _edge(svc)
    assert first["outcome"] == "sent", first
    assert first["trigger"] == "coder.awaiting" and first["sessionKey"] == "claude:s1"
    assert calls == [("HoldSpeak", "1 need you")]
    assert _read_dirty_at(db) is not None

    # The same waiting agent again (a later edge, or the next sweep): silent.
    second = _edge(svc)
    assert second["outcome"] == "held_no_edge" and len(calls) == 1


def test_the_edge_holds_in_quiet_hours_then_delivers_once(db: Database) -> None:
    calls: list[tuple[str, str]] = []
    svc = _service(db, calls, at=datetime(2026, 10, 5, 23, 0, tzinfo=timezone.utc))
    held = _edge(svc)
    assert held["outcome"] == "held_quiet_hours" and not calls

    svc._clock = _Clock(datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc))
    assert _edge(svc)["outcome"] == "sent" and len(calls) == 1
    assert _edge(svc)["outcome"] == "held_no_edge" and len(calls) == 1


def test_the_edge_honors_notify_off(db: Database) -> None:
    calls: list[tuple[str, str]] = []
    svc = _service(db, calls, at=NOW, notify="off")
    assert _edge(svc)["outcome"] == "off" and not calls


def test_the_hub_watcher_edge_runs_the_heartbeat_decision(monkeypatch: pytest.MonkeyPatch, db: Database) -> None:
    from holdspeak import web_server
    from holdspeak.services.heartbeat_service import HeartbeatService

    seen: list[str] = []

    def fake_edge(self, principal=None, *, session_key: str = "") -> dict[str, Any]:
        seen.append(session_key)
        return {"outcome": "sent"}

    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr(HeartbeatService, "notify_coder_edge", fake_edge)
    assert web_server._coder_awaiting_edge(["claude:s1", "codex:s2"]) == {"outcome": "sent"}
    assert seen == ["claude:s1,codex:s2"]


def test_the_hub_watcher_edge_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak import web_server

    def broken() -> Database:
        raise RuntimeError("no database")

    monkeypatch.setattr("holdspeak.db.get_database", broken)
    assert web_server._coder_awaiting_edge(["claude:s1"]) is None
