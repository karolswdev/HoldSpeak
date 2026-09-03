"""HS-166-03: WatchCondition@1 matcher -- six snapshot-level comparisons.

Tests: entered_state, due_within_days, overdue, inactive_for,
older_than, newer_than.  All with a frozen clock at 2026-09-01T00:00:00Z.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

import holdspeak.watch_condition_matcher as matcher_mod
from holdspeak.watch_condition_matcher import match_condition


FROZEN_NOW = datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def freeze_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(matcher_mod, "_clock", lambda: FROZEN_NOW)


def _transition(
    *,
    changed: dict | None = None,
    current: dict | None = None,
    event_type: str = "jira.issue.status_changed",
) -> dict:
    return {
        "event_type": event_type,
        "entity_ref": "KAN-1",
        "source_revision": "abc",
        "facts": {
            "entity_title": "Task 1",
            "url": "https://x",
            "changed": changed or {},
            "current": current or {},
        },
    }


# ── entered_state ────────────────────────────────────────────────────


class TestEnteredState:
    def test_matches_when_field_changed_to_value(self) -> None:
        t = _transition(changed={"status": ["todo", "Blocked"]})
        assert match_condition(
            {"field": "status", "comparison": "entered_state", "value": "Blocked"}, [t]
        )

    def test_no_match_wrong_value(self) -> None:
        t = _transition(changed={"status": ["todo", "In Progress"]})
        assert not match_condition(
            {"field": "status", "comparison": "entered_state", "value": "Blocked"}, [t]
        )

    def test_no_match_field_missing_from_changed(self) -> None:
        t = _transition(
            changed={"assignee": ["alice", "bob"]},
            current={"status": "Blocked"},
        )
        assert not match_condition(
            {"field": "status", "comparison": "entered_state", "value": "Blocked"}, [t]
        )

    def test_raw_value_not_pair(self) -> None:
        t = _transition(changed={"entity": "new"})
        assert match_condition(
            {"field": "entity", "comparison": "entered_state", "value": "new"}, [t]
        )


# ── due_within_days ──────────────────────────────────────────────────


class TestDueWithinDays:
    def test_due_within_range(self) -> None:
        t = _transition(
            changed={"status": ["todo", "in progress"]},
            current={"due_at": "2026-09-05"},
        )
        assert match_condition(
            {"field": "due_at", "comparison": "due_within_days", "value": 7}, [t]
        )

    def test_due_outside_range(self) -> None:
        t = _transition(
            changed={"status": ["todo", "in progress"]},
            current={"due_at": "2026-09-20"},
        )
        assert not match_condition(
            {"field": "due_at", "comparison": "due_within_days", "value": 7}, [t]
        )

    def test_due_in_changed_new_value(self) -> None:
        t = _transition(
            changed={"due_at": ["2026-12-01", "2026-09-03"]},
            current={"due_at": "2026-09-03"},
        )
        assert match_condition(
            {"field": "due_at", "comparison": "due_within_days", "value": 7}, [t]
        )

    def test_already_past_counts(self) -> None:
        t = _transition(current={"due_at": "2026-08-30"})
        assert match_condition(
            {"field": "due_at", "comparison": "due_within_days", "value": 7}, [t]
        )

    def test_string_duration(self) -> None:
        t = _transition(current={"due_at": "2026-09-05"})
        assert match_condition(
            {"field": "due_at", "comparison": "due_within_days", "value": "7"}, [t]
        )

    def test_no_due_at(self) -> None:
        t = _transition(current={"status": "open"})
        assert not match_condition(
            {"field": "due_at", "comparison": "due_within_days", "value": 7}, [t]
        )


# ── overdue ──────────────────────────────────────────────────────────


class TestOverdue:
    def test_past_due_no_resolution(self) -> None:
        t = _transition(current={"due_at": "2026-08-20", "resolution": ""})
        assert match_condition(
            {"field": "due_at", "comparison": "overdue"}, [t]
        )

    def test_future_due(self) -> None:
        t = _transition(current={"due_at": "2026-09-20", "resolution": ""})
        assert not match_condition(
            {"field": "due_at", "comparison": "overdue"}, [t]
        )

    def test_past_due_with_resolution(self) -> None:
        t = _transition(current={"due_at": "2026-08-20", "resolution": "fixed"})
        assert not match_condition(
            {"field": "due_at", "comparison": "overdue"}, [t]
        )

    def test_no_due_at(self) -> None:
        t = _transition(current={"resolution": ""})
        assert not match_condition(
            {"field": "due_at", "comparison": "overdue"}, [t]
        )


# ── inactive_for ─────────────────────────────────────────────────────


class TestInactiveFor:
    def test_inactive_beyond_threshold(self) -> None:
        t = _transition(
            event_type="jira.issue.discovered",
            current={"updated_at": "2026-08-01T00:00:00Z"},
        )
        assert match_condition(
            {"field": "updated_at", "comparison": "inactive_for", "value": 14}, [t]
        )

    def test_active_within_threshold(self) -> None:
        t = _transition(
            event_type="jira.issue.discovered",
            current={"updated_at": "2026-08-25T00:00:00Z"},
        )
        assert not match_condition(
            {"field": "updated_at", "comparison": "inactive_for", "value": 14}, [t]
        )


# ── older_than ───────────────────────────────────────────────────────


class TestOlderThan:
    def test_old_entity(self) -> None:
        t = _transition(current={"updated_at": "2026-08-01T00:00:00Z"})
        assert match_condition(
            {"field": "updated_at", "comparison": "older_than", "value": "7d"}, [t]
        )

    def test_recent_entity(self) -> None:
        t = _transition(current={"updated_at": "2026-08-31T00:00:00Z"})
        assert not match_condition(
            {"field": "updated_at", "comparison": "older_than", "value": "7d"}, [t]
        )

    def test_integer_value(self) -> None:
        t = _transition(current={"updated_at": "2026-08-01T00:00:00Z"})
        assert match_condition(
            {"field": "updated_at", "comparison": "older_than", "value": 7}, [t]
        )

    def test_from_changed_pair(self) -> None:
        t = _transition(
            changed={"updated_at": ["2026-07-01", "2026-08-01"]},
            current={"updated_at": "2026-08-01"},
        )
        assert match_condition(
            {"field": "updated_at", "comparison": "older_than", "value": 7}, [t]
        )


# ── newer_than ───────────────────────────────────────────────────────


class TestNewerThan:
    def test_recent_entity(self) -> None:
        t = _transition(current={"updated_at": "2026-08-31T00:00:00Z"})
        assert match_condition(
            {"field": "updated_at", "comparison": "newer_than", "value": 7}, [t]
        )

    def test_old_entity(self) -> None:
        t = _transition(current={"updated_at": "2026-08-01T00:00:00Z"})
        assert not match_condition(
            {"field": "updated_at", "comparison": "newer_than", "value": 7}, [t]
        )

    def test_string_duration(self) -> None:
        t = _transition(current={"updated_at": "2026-08-31T00:00:00Z"})
        assert match_condition(
            {"field": "updated_at", "comparison": "newer_than", "value": "7d"}, [t]
        )
