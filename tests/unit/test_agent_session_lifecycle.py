"""HSM-17-02: the live-session lifecycle — hook events → state, question capture,
read-time staleness decay, and the secret filter on captured questions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from holdspeak.agent_context import (
    LIFECYCLE_ENDED,
    LIFECYCLE_IDLE,
    LIFECYCLE_WAITING,
    LIFECYCLE_WORKING,
    effective_state,
    ingest_agent_hook_event,
)

_NOW = datetime(2026, 7, 4, 12, 0, 0, tzinfo=timezone.utc)


def _ingest(state: Path, event: str, *, now=_NOW, cwd: str, **extra):
    payload = {"session_id": "s1", "hook_event_name": event, "cwd": cwd}
    payload.update(extra)
    return ingest_agent_hook_event(
        agent="claude", payload=payload, state_path=state, now=now
    )


def test_lifecycle_working_events_keep_the_session_working(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    cwd = str(tmp_path)
    for event in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse"):
        session = _ingest(state, event, cwd=cwd)
        assert session.lifecycle == LIFECYCLE_WORKING
        assert session.question is None


def test_notification_flips_to_waiting_and_captures_the_question(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    cwd = str(tmp_path)
    _ingest(state, "UserPromptSubmit", cwd=cwd)

    session = _ingest(
        state, "Notification", cwd=cwd,
        message="Claude needs your permission to run: rm -rf build/",
    )

    assert session.lifecycle == LIFECYCLE_WAITING
    assert session.question == "Claude needs your permission to run: rm -rf build/"


def test_resume_clears_the_question(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    cwd = str(tmp_path)
    _ingest(state, "Notification", cwd=cwd, message="Proceed with the migration?")

    session = _ingest(state, "UserPromptSubmit", cwd=cwd)

    assert session.lifecycle == LIFECYCLE_WORKING
    assert session.question is None


def test_stop_is_waiting_and_a_question_shaped_reply_becomes_the_question(
    tmp_path: Path,
) -> None:
    state = tmp_path / "state.json"
    cwd = str(tmp_path)
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        '{"type": "assistant", "message": {"content": [{"type": "text", '
        '"text": "Should I also update the fixtures?"}]}}\n',
        encoding="utf-8",
    )

    session = ingest_agent_hook_event(
        agent="claude",
        payload={
            "session_id": "s1",
            "hook_event_name": "Stop",
            "cwd": cwd,
            "transcript_path": str(transcript),
        },
        state_path=state,
        now=_NOW,
        capture_messages=True,
    )

    assert session.lifecycle == LIFECYCLE_WAITING
    assert session.question == "Should I also update the fixtures?"


def test_session_end_tombstones(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    cwd = str(tmp_path)
    _ingest(state, "UserPromptSubmit", cwd=cwd)

    session = _ingest(state, "SessionEnd", cwd=cwd)

    assert session.lifecycle == LIFECYCLE_ENDED
    assert effective_state(session, now=_NOW) == LIFECYCLE_ENDED
    # ended is sticky no matter how fresh the timestamp is
    assert effective_state(session, now=_NOW + timedelta(days=7)) == LIFECYCLE_ENDED


def test_effective_state_decays_idle_then_ended(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    session = _ingest(state, "UserPromptSubmit", cwd=str(tmp_path))

    assert effective_state(session, now=_NOW) == LIFECYCLE_WORKING
    assert (
        effective_state(session, now=_NOW + timedelta(minutes=31)) == LIFECYCLE_IDLE
    )
    assert (
        effective_state(session, now=_NOW + timedelta(hours=5)) == LIFECYCLE_ENDED
    )


def test_effective_state_honors_custom_windows(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    session = _ingest(state, "Notification", cwd=str(tmp_path), message="Proceed?")

    assert (
        effective_state(session, now=_NOW + timedelta(seconds=90), idle_after_seconds=60, dead_after_seconds=120)
        == LIFECYCLE_IDLE
    )
    assert (
        effective_state(session, now=_NOW + timedelta(seconds=200), idle_after_seconds=60, dead_after_seconds=120)
        == LIFECYCLE_ENDED
    )


def test_captured_question_is_secret_filtered(tmp_path: Path) -> None:
    state = tmp_path / "state.json"

    session = _ingest(
        state, "Notification", cwd=str(tmp_path),
        message="Use api_key sk-abcdefghijklmnop1234 for the deploy?",
    )

    assert session.lifecycle == LIFECYCLE_WAITING
    assert session.question == "[redacted: possible secret]"
    assert "sk-" not in (session.question or "")


def test_lifecycle_round_trips_through_the_registry(tmp_path: Path) -> None:
    from holdspeak.agent_context import list_agent_sessions

    state = tmp_path / "state.json"
    _ingest(state, "Notification", cwd=str(tmp_path), message="Merge it?")

    (loaded,) = list_agent_sessions(state_path=state)

    assert loaded.lifecycle == LIFECYCLE_WAITING
    assert loaded.question == "Merge it?"
