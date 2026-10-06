"""Conductor K2: the same hook event from two sources is recorded once.

A Hand-to-agent launch runs the rider hooks from its ``--settings`` file; the
owner may also have them in ``~/.claude/settings.json`` (K1). Claude Code runs
both for one event with the same payload.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from holdspeak.agent_context.sessions import ingest_agent_hook_event

T0 = datetime(2026, 10, 6, 9, 0, 0, tzinfo=timezone.utc)


def _payload(event: str, tmp_path, **extra):
    transcript = tmp_path / "transcript.jsonl"
    if not transcript.exists():
        transcript.write_text('{"type": "user", "message": {"role": "user", "content": "go"}}\n')
    return {"session_id": "s1", "cwd": str(tmp_path), "hook_event_name": event,
            "transcript_path": str(transcript), **extra}


def _row(state):
    return json.loads(state.read_text(encoding="utf-8"))["sessions"]["claude:s1"]


def test_a_doubled_event_is_recorded_once(tmp_path) -> None:
    state = tmp_path / "state.json"
    ingest = lambda event, at, **kw: ingest_agent_hook_event(  # noqa: E731
        agent="claude", payload=_payload(event, tmp_path, **kw), state_path=state, now=at, env={},
    )
    ingest("SessionStart", T0)
    ingest("SessionStart", T0 + timedelta(milliseconds=40))
    assert _row(state)["event_count"] == 1

    ask = {"message": "Claude needs your permission to use Bash", "notification_type": "permission_prompt"}
    ingest("Notification", T0 + timedelta(seconds=2), **ask)
    first = _row(state)
    ingest("Notification", T0 + timedelta(seconds=2, milliseconds=30), **ask)
    second = _row(state)
    # One wait episode, one event: the notify edge (keyed on wait_id) stays single.
    assert second["wait_id"] == first["wait_id"]
    assert second["event_count"] == first["event_count"] == 2
    assert second["updated_at"] == first["updated_at"]


def test_a_repeated_event_outside_the_window_or_different_is_recorded(tmp_path) -> None:
    state = tmp_path / "state.json"
    ingest = lambda event, at, **kw: ingest_agent_hook_event(  # noqa: E731
        agent="claude", payload=_payload(event, tmp_path, **kw), state_path=state, now=at, env={},
    )
    ingest("PostToolUse", T0, tool_name="Bash", tool_use_id="t1")
    ingest("PostToolUse", T0 + timedelta(seconds=1), tool_name="Bash", tool_use_id="t2")
    ingest("PostToolUse", T0 + timedelta(seconds=30), tool_name="Bash", tool_use_id="t2")
    assert _row(state)["event_count"] == 3
