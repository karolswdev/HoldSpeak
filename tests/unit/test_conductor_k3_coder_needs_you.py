"""Conductor K3: a waiting coding agent reaches Needs you at once.

Every session here is written by the real producer: the agent hook ingestion
(``agent_context.ingest_agent_hook_event``) into a registry file, read back
by the same readers the hub uses. Covers R5 membership, the ONE blocked
predicate shared with the hub's watcher, the wait episode (notify once per
wait; a new wait after an answer notifies again; a restart stays silent),
the startup reconcile, the strict registry read, the permission/input
subtype, the wait-start ranking, and quiet hours against the 30 min
freshness rule.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from holdspeak import agent_context
from holdspeak.agent_context import ingest_agent_hook_event, read_agent_sessions_strict
from holdspeak.coder_steering import awaiting_snapshot, wait_snapshot
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import needs_you_membership as membership
from holdspeak.services.attention_ranking import attention_class
from holdspeak.services.needs_you_aggregate import COVERAGE_KINDS, _read_dirty_at
from holdspeak.services.needs_you_membership import coder_items, compute_needs_you

T0 = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
OWNER = Principal(PrincipalKind.OWNER, "test")


class Hooks:
    """A coding agent driving the real hook ingestion into one registry."""

    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.root = tmp_path
        self.registry = tmp_path / "agent_sessions.json"
        monkeypatch.setattr(agent_context, "AGENT_CONTEXT_FILE", self.registry)
        self.cwd = tmp_path / "repo"
        self.cwd.mkdir(exist_ok=True)

    def event(self, name: str, at: datetime, *, session: str = "s1", agent: str = "claude",
              **payload: Any):
        return ingest_agent_hook_event(
            agent=agent,
            payload={"session_id": session, "cwd": str(self.cwd), "hook_event_name": name, **payload},
            state_path=self.registry, now=at, capture_messages=True, env={},
        )

    def ask(self, text: str, at: datetime, *, session: str = "s1", agent: str = "claude"):
        """The agent ends its turn with a question (Stop + transcript)."""
        transcript = self.root / f"{agent}-{session}.jsonl"
        with transcript.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"role": "assistant", "content": text}) + "\n")
        return self.event("Stop", at, session=session, agent=agent, transcript_path=str(transcript))

    def prompt(self, at: datetime, *, session: str = "s1") -> Any:
        """The owner answers (UserPromptSubmit)."""
        return self.event("UserPromptSubmit", at, session=session, prompt="drop it")

    def notify(self, message: str, at: datetime, *, kind: str | None, session: str = "s1"):
        payload: dict[str, Any] = {"message": message}
        if kind is not None:
            payload["notification_type"] = kind
        return self.event("Notification", at, session=session, **payload)

    def sessions(self) -> list[Any]:
        return read_agent_sessions_strict(state_path=self.registry)

    def members(self, at: datetime) -> list[dict[str, Any]]:
        return coder_items(self.sessions(), at)


@pytest.fixture
def hooks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Hooks:
    return Hooks(tmp_path, monkeypatch)


# ── R5 membership ────────────────────────────────────────────────────


def test_a_fresh_question_is_a_member_with_its_facts(hooks: Hooks) -> None:
    hooks.ask("Should I keep the old migration or drop it?", T0, agent="codex")
    rows = hooks.members(T0 + timedelta(minutes=2))
    assert len(rows) == 1
    row = rows[0]
    assert row["ref"] == row["id"] == "coder:codex:s1"
    assert row["kind"] == row["source"] == "coder"
    assert row["sessionKey"] == "codex:s1" and row["agent"] == "codex"
    assert row["cwd"] == str(hooks.cwd.resolve())
    assert row["question"] == row["title"] == "Should I keep the old migration or drop it?"
    assert row["ageSeconds"] == 120 and row["why"] == "TO ANSWER"
    result = compute_needs_you(coders=hooks.sessions(), now=T0)
    assert [m["ref"] for m in result["members"]] == ["coder:codex:s1"]


def test_stale_answered_and_ended_waits_are_not_members(hooks: Hooks) -> None:
    hooks.ask("Keep the old migration?", T0)
    assert len(hooks.members(T0 + timedelta(minutes=29))) == 1
    assert hooks.members(T0 + timedelta(minutes=31)) == []  # the 30 min freshness
    hooks.prompt(T0 + timedelta(minutes=1))  # answered
    assert hooks.members(T0 + timedelta(minutes=2)) == []
    hooks.ask("And the index too?", T0 + timedelta(minutes=3))
    hooks.event("SessionEnd", T0 + timedelta(minutes=4))  # ended
    assert hooks.members(T0 + timedelta(minutes=5)) == []


def test_a_coder_is_a_coverage_kind() -> None:
    assert "coder" in COVERAGE_KINDS


# ── [P2-5] the Notification subtype ──────────────────────────────────


def test_a_permission_prompt_is_to_approve_and_an_input_prompt_is_to_answer(hooks: Hooks) -> None:
    hooks.notify("Claude needs your permission to use Bash", T0, kind="permission_prompt")
    rows = hooks.members(T0)
    assert [(r["ref"], r["why"]) for r in rows] == [("coder:claude:s1", "TO APPROVE")]
    assert attention_class(rows[0], T0) == "due_today"

    hooks.notify("Claude is waiting for your input", T0, kind="idle_prompt", session="s2")
    by_ref = {r["ref"]: r["why"] for r in hooks.members(T0)}
    assert by_ref["coder:claude:s2"] == "TO ANSWER"


def test_an_older_payload_without_the_subtype_is_read_from_its_message(hooks: Hooks) -> None:
    hooks.notify("Claude needs your permission to use Bash", T0, kind=None)
    hooks.notify("Claude is waiting for your input", T0, kind=None, session="s2")
    assert {r["ref"]: r["why"] for r in hooks.members(T0)} == {
        "coder:claude:s1": "TO APPROVE", "coder:claude:s2": "TO ANSWER",
    }


def test_auth_success_does_not_block(hooks: Hooks) -> None:
    hooks.notify("Authenticated", T0, kind="auth_success")
    assert hooks.members(T0) == []


def test_a_non_prompt_notification_never_creates_a_wait_after_work(hooks: Hooks) -> None:
    """Round 2 (B): Stop(question) -> PostToolUse -> Notification(auth_success)
    made a TO ANSWER row and a new wait id from a surviving flag."""
    hooks.ask("Keep the old migration?", T0)
    worked = hooks.event("PostToolUse", T0 + timedelta(minutes=1), tool_name="Bash")
    assert worked.awaiting_response is False  # working events clear the flag
    for kind in ("auth_success", "some_future_subtype"):
        after = hooks.notify("Authenticated", T0 + timedelta(minutes=2), kind=kind)
        assert after.wait_id is None and after.question is None
        assert hooks.members(T0 + timedelta(minutes=2)) == []
        assert wait_snapshot(hooks.sessions()) == {"claude:s1": ""}


def test_a_non_prompt_notification_never_extends_a_wait(hooks: Hooks) -> None:
    first = hooks.ask("Keep the old migration?", T0)
    later = hooks.notify("Authenticated", T0 + timedelta(minutes=20), kind="auth_success")
    # The open wait is unchanged: the same episode, the same question, and
    # its freshness is NOT moved, so it still expires 30 min after the ask.
    assert later.wait_id == first.wait_id and later.question == "Keep the old migration?"
    assert later.updated_at == first.updated_at
    assert len(hooks.members(T0 + timedelta(minutes=29))) == 1
    assert hooks.members(T0 + timedelta(minutes=31)) == []


def test_an_idle_reminder_keeps_the_question_the_agent_asked(hooks: Hooks) -> None:
    hooks.ask("Keep the old migration?", T0)
    hooks.notify("Claude is waiting for your input", T0 + timedelta(minutes=1), kind="idle_prompt")
    [row] = hooks.members(T0 + timedelta(minutes=1))
    assert row["question"] == "Keep the old migration?" and row["why"] == "TO ANSWER"


# ── [P1-2] ONE blocked predicate for membership and the watcher ──────


def test_membership_and_the_watcher_agree_through_work_and_a_permission_prompt(hooks: Hooks) -> None:
    def step() -> tuple[int, bool, bool]:
        sessions = hooks.sessions()
        return (len(coder_items(sessions, T0 + timedelta(minutes=5))),
                awaiting_snapshot(sessions)["claude:s1"],
                bool(wait_snapshot(sessions)["claude:s1"]))

    hooks.ask("Keep the old migration?", T0)
    assert step() == (1, True, True)
    # The agent went on working: the question and the awaiting_response
    # flag are cleared (round 2), and it is NOT blocked.
    hooks.event("PostToolUse", T0 + timedelta(minutes=1), tool_name="Bash")
    assert hooks.sessions()[0].awaiting_response is False
    assert step() == (0, False, False)
    hooks.notify("Claude needs your permission to use Bash", T0 + timedelta(minutes=2),
                 kind="permission_prompt")
    assert step() == (1, True, True)
    hooks.event("SessionEnd", T0 + timedelta(minutes=3))
    assert step() == (0, False, False)


# ── [P2-6] ranking by the wait's start ───────────────────────────────


def test_a_repeated_report_keeps_the_wait_start_and_the_order(hooks: Hooks) -> None:
    first = hooks.ask("Keep the old migration?", T0, session="first")
    hooks.ask("Rename the table?", T0 + timedelta(minutes=5), session="second")
    # The first agent reports its wait again (an idle reminder).
    hooks.notify("Claude is waiting for your input", T0 + timedelta(minutes=10),
                 kind="idle_prompt", session="first")
    now = T0 + timedelta(minutes=11)
    rows = {r["ref"]: r for r in hooks.members(now)}
    assert rows["coder:claude:first"]["since"] == first.wait_started_at
    assert datetime.fromisoformat(first.wait_started_at.replace("Z", "+00:00")) == T0
    assert rows["coder:claude:first"]["ageSeconds"] == 11 * 60
    order = [r["ref"] for r in compute_needs_you(coders=hooks.sessions(), now=now)["unmutedItems"]]
    assert order == ["coder:claude:first", "coder:claude:second"]


# ── [P1-1] the wait episode: notify once per wait ───────────────────


class _Clock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "k3.db")


def _service(db: Database, calls: list[tuple[str, str]], clock: _Clock, *, notify: str = "edge"):
    from holdspeak.services.heartbeat_service import HeartbeatService

    def notifier(title: str, body: str, *, click_url=None) -> bool:
        calls.append((title, body))
        return True

    svc = HeartbeatService(db, notifier=notifier, clock=clock, local_zone=timezone.utc)
    svc.update_settings({"notify": notify, "quiet_hours": {"start": 22, "end": 8}})
    return svc


def _edge(svc, hooks: Hooks, clock: _Clock) -> dict[str, Any]:
    """The edge decision over the registry AS IT IS at the clock's instant
    (the aggregate is rebuilt every call, never frozen)."""
    def build(principal=None) -> dict[str, Any]:
        result = compute_needs_you(coders=hooks.sessions(), now=clock.at)
        return {"count": result["count"], "projects": [], "items": result["unmutedItems"],
                "members": result["members"], "coverage": [], "complete": True}

    with patch.object(svc, "_build_aggregate_via_canonical", side_effect=build):
        return svc.notify_coder_edge(OWNER, session_key="claude:s1")


def test_answer_then_ask_again_notifies_again_and_one_wait_notifies_once(
    hooks: Hooks, db: Database,
) -> None:
    calls: list[tuple[str, str]] = []
    clock = _Clock(T0)
    svc = _service(db, calls, clock)
    first = hooks.ask("Keep the old migration?", T0)
    assert _edge(svc, hooks, clock)["outcome"] == "sent"
    assert _read_dirty_at(db) is not None

    # The same wait reported again: the episode and the ref are unchanged.
    clock.at = T0 + timedelta(minutes=1)
    again = hooks.notify("Claude is waiting for your input", clock.at, kind="idle_prompt")
    assert again.wait_id == first.wait_id
    assert _edge(svc, hooks, clock)["outcome"] == "held_no_edge"

    # A restart (a new service over the same database, the registry re-read).
    restarted = _service(db, calls, clock)
    assert hooks.sessions()[0].wait_id == first.wait_id
    assert _edge(restarted, hooks, clock)["outcome"] == "held_no_edge"
    assert len(calls) == 1

    # Answered, then a NEW question: a new episode, the same row ref.
    hooks.prompt(T0 + timedelta(minutes=2))
    clock.at = T0 + timedelta(minutes=3)
    second = hooks.ask("And the index too?", clock.at)
    assert second.wait_id and second.wait_id != first.wait_id
    [row] = hooks.members(clock.at)
    assert row["ref"] == "coder:claude:s1"
    assert _edge(restarted, hooks, clock)["outcome"] == "sent"
    assert len(calls) == 2


def test_the_edge_honors_notify_off(hooks: Hooks, db: Database) -> None:
    calls: list[tuple[str, str]] = []
    clock = _Clock(T0)
    svc = _service(db, calls, clock, notify="off")
    hooks.ask("Keep the old migration?", T0)
    assert _edge(svc, hooks, clock)["outcome"] == "off" and not calls


# ── quiet hours against the 30 min freshness ─────────────────────────


def test_a_wait_just_before_morning_is_delivered_once_at_the_end_of_quiet_hours(
    hooks: Hooks, db: Database,
) -> None:
    calls: list[tuple[str, str]] = []
    clock = _Clock(datetime(2026, 10, 6, 7, 50, tzinfo=timezone.utc))
    svc = _service(db, calls, clock)
    hooks.ask("Keep the old migration?", clock.at)
    assert _edge(svc, hooks, clock)["outcome"] == "held_quiet_hours" and not calls
    clock.at = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)  # the next decision
    assert _edge(svc, hooks, clock)["outcome"] == "sent" and len(calls) == 1
    clock.at = datetime(2026, 10, 6, 8, 15, tzinfo=timezone.utc)
    assert _edge(svc, hooks, clock)["outcome"] == "held_no_edge" and len(calls) == 1


def test_a_wait_at_night_expires_before_morning_and_is_never_delivered(
    hooks: Hooks, db: Database,
) -> None:
    calls: list[tuple[str, str]] = []
    clock = _Clock(datetime(2026, 10, 5, 23, 0, tzinfo=timezone.utc))
    svc = _service(db, calls, clock)
    hooks.ask("Keep the old migration?", clock.at)
    assert _edge(svc, hooks, clock)["outcome"] == "held_quiet_hours"
    clock.at = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)
    morning = _edge(svc, hooks, clock)
    # Nine hours later the wait is past the 30 min freshness: not a member.
    assert morning["count"] == 0 and morning["outcome"] == "held_no_edge"
    assert not calls


# ── [P2-3] the watcher's first read ──────────────────────────────────


def test_an_absent_registry_is_an_empty_baseline(hooks: Hooks) -> None:
    from holdspeak.web_server import _coder_watch_step

    snapshot, transitions, entered = _coder_watch_step(None, hooks.registry)
    assert (snapshot, transitions, entered) == ({}, [], [])
    hooks.ask("Keep the old migration?", T0)
    snapshot, transitions, entered = _coder_watch_step(snapshot, hooks.registry)
    assert transitions == ["claude:s1"] and entered == ["claude:s1"]


def test_answer_then_ask_between_two_reads_is_a_transition(hooks: Hooks) -> None:
    from holdspeak.web_server import _coder_watch_step

    hooks.ask("Keep the old migration?", T0)
    snapshot, _, _ = _coder_watch_step({}, hooks.registry)
    hooks.prompt(T0 + timedelta(minutes=1))
    hooks.ask("And the index too?", T0 + timedelta(minutes=2))
    _, transitions, entered = _coder_watch_step(snapshot, hooks.registry)
    assert entered == ["claude:s1"]


def test_startup_reconciles_open_waits_and_a_notified_wait_stays_silent(
    hooks: Hooks, db: Database,
) -> None:
    from holdspeak.web_server import _coder_watch_step

    calls: list[tuple[str, str]] = []
    clock = _Clock(T0)
    hooks.ask("Keep the old migration?", T0)
    # Hub start with a wait already open: no frames, the wait is reconciled.
    snapshot, transitions, entered = _coder_watch_step(None, hooks.registry)
    assert transitions == [] and entered == ["claude:s1"]
    assert _edge(_service(db, calls, clock), hooks, clock)["outcome"] == "sent"
    # A second start: the persisted notified set keeps it silent.
    _, _, entered = _coder_watch_step(None, hooks.registry)
    assert entered == ["claude:s1"]
    assert _edge(_service(db, calls, clock), hooks, clock)["outcome"] == "held_no_edge"
    assert len(calls) == 1


# ── [P2-4] the strict registry read ──────────────────────────────────


def _stub_other_hub_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(membership, "_read_door", lambda db, p: {"board": {}, "people_store_state": None})
    monkeypatch.setattr(membership, "_read_assignments", lambda db, p: {"task_overrides": []})
    monkeypatch.setattr(membership, "_read_summary_attention", lambda db, p: [])
    monkeypatch.setattr(membership, "_read_decisions", lambda db, p: [])


def _compose(aggregate: dict[str, Any] | None = None) -> dict[str, Any]:
    return membership.compose(None, OWNER, aggregate or {"items": [], "coverage": [], "complete": True},
                              muted_project_ids=[], now=T0)


def test_an_absent_registry_is_available_and_empty(
    hooks: Hooks, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_other_hub_reads(monkeypatch)
    answer = _compose()
    [row] = [r for r in answer["coverage"] if r["kind"] == "coder"]
    assert row["state"] == "available" and answer["complete"] is True and answer["count"] == 0


def test_a_registry_with_a_wait_composes_and_recomposes_one_coverage_record(
    hooks: Hooks, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_other_hub_reads(monkeypatch)
    hooks.ask("Keep the old migration?", T0)
    answer = _compose()
    assert [m["ref"] for m in answer["members"]] == ["coder:claude:s1"]
    again = _compose(membership.room_part(answer))
    assert len([r for r in again["coverage"] if r["kind"] == "coder"]) == 1


@pytest.mark.parametrize("body", [
    "{not json", "[]", '{"sessions": []}',
    # Round 2 (A): a registry with no sessions object, or with a row that is
    # not an object, is not an all-clear either.
    '{"version": 1}', '{"sessions": {"claude:s1": null}}',
    '{"sessions": {"claude:s1": "waiting"}}',
])
def test_a_malformed_registry_is_a_coverage_error_never_an_all_clear(
    hooks: Hooks, monkeypatch: pytest.MonkeyPatch, body: str,
) -> None:
    _stub_other_hub_reads(monkeypatch)
    hooks.registry.write_text(body, encoding="utf-8")
    answer = _compose()
    assert answer["sourceErrors"].get("coders")
    assert answer["complete"] is False
    [row] = [r for r in answer["coverage"] if r["kind"] == "coder"]
    assert row["state"] == "failed" and row["repair"]["token"] == "READ FAILED"


# ── the hub helper ───────────────────────────────────────────────────


def test_the_hub_edge_helper_runs_the_heartbeat_decision(
    monkeypatch: pytest.MonkeyPatch, db: Database,
) -> None:
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


def test_the_hub_edge_helper_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak import web_server

    def broken() -> Database:
        raise RuntimeError("no database")

    monkeypatch.setattr("holdspeak.db.get_database", broken)
    assert web_server._coder_awaiting_edge(["claude:s1"]) is None
