"""PHILO-15 01 — the "No engine for summaries" row asks the route policy.

The meeting-intel queue reads the exact capability, group and global heads
(``meeting-intel-queue@2``). The assignment roster states that answer as
``task_overrides[].queue``, and ``meeting_path_blockers`` reads it, so a
"Default for AI work" clears the row exactly when a summary would run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_service_route_policy import (
    builtin_service_route_policy_registry,
)
from holdspeak.services.needs_you_membership import meeting_path_blockers
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim

SUMMARY = "meeting.deferred_analysis"


@pytest.fixture
def db(tmp_path: Path) -> Database:
    database = Database(tmp_path / "blocker.db")
    _profile(
        database,
        "lan-model",
        claims=("language", "structured_output", _result_claim(SUMMARY)),
        modalities=("language", "text"),
    )
    return database


def _set(service: InferenceAssignmentService, command: str, scope: dict, expected: int = 0) -> dict:
    return service.set_assignment(OWNER, {
        "command_id": command, "expected_revision": expected, "scope": scope,
        "entries": [{"profile_id": "lan-model", "profile_revision": 1}],
    })


def _summary_row(roster: dict) -> dict:
    return next(row for row in roster["task_overrides"] if row["id"] == SUMMARY)


def _keys(roster: dict) -> list[str]:
    return [blocker["key"] for blocker in meeting_path_blockers(roster)]


def test_policy_names_the_queue_sources() -> None:
    found = builtin_service_route_policy_registry().assignment_sources(
        "meeting-intel-queue", SUMMARY
    )
    assert found == ("meeting-intel-queue@2", ("capability", "group", "global"))
    assert builtin_service_route_policy_registry().assignment_sources(
        "meeting-intel-queue", "ask.answer"
    ) is None


def test_nothing_assigned_keeps_the_blocker(db: Database) -> None:
    roster = InferenceAssignmentService(db).assignment_summary(OWNER)
    row = _summary_row(roster)
    assert row["queue"] == {
        "policy_id": "meeting-intel-queue@2", "status": "no_assignment", "inherited_from": None,
    }
    assert _keys(roster) == ["engines"]


def test_default_assigned_without_exact_capability_clears_the_blocker(db: Database) -> None:
    service = InferenceAssignmentService(db)
    _set(service, "set-default", {"kind": "global"})
    roster = service.assignment_summary(OWNER)
    row = _summary_row(roster)
    assert row["has_override"] is False
    assert row["queue"]["status"] == "assigned"
    assert row["queue"]["inherited_from"] == "global"
    assert "summary" not in _keys(roster)
    assert "engines" not in _keys(roster)


def test_cleared_exact_capability_with_default_present_has_no_blocker(db: Database) -> None:
    service = InferenceAssignmentService(db)
    _set(service, "set-default", {"kind": "global"})
    exact = _set(service, "set-exact", {"kind": "capability", "capability_id": SUMMARY})
    service.clear_assignment(OWNER, {
        "command_id": "clear-exact", "expected_revision": exact["revision"],
        "scope": {"kind": "capability", "capability_id": SUMMARY}, "capability_id": SUMMARY,
    })
    roster = service.assignment_summary(OWNER)
    row = _summary_row(roster)
    assert row["has_override"] is False
    assert row["queue"]["status"] == "assigned"
    assert "summary" not in _keys(roster)


def test_the_row_follows_the_policy_not_a_copy_of_it(db: Database) -> None:
    """A capability-only queue policy (revision 1) keeps the row over a default."""

    class CapabilityOnly:
        def assignment_sources(self, service_identity: str, capability_id: str):
            if service_identity == "meeting-intel-queue" and capability_id == SUMMARY:
                return ("meeting-intel-queue@1", ("capability",))
            return None

    service = InferenceAssignmentService(db)
    _set(service, "set-default", {"kind": "global"})
    service._service_route_policies = CapabilityOnly()
    roster = service.assignment_summary(OWNER)
    row = _summary_row(roster)
    assert row["effective"]["status"] == "assigned"
    assert row["queue"]["status"] == "no_assignment"
    # The fixture's language model does not run speech, so both halves are
    # missing: one "engines" row. Without the stub (above) it is "speech".
    assert _keys(roster) == ["engines"]


def test_a_roster_without_queue_falls_back_to_the_owner_chain() -> None:
    def roster(status: str) -> dict:
        return {"task_overrides": [
            {"id": SUMMARY, "has_override": False, "effective": {"status": status}},
        ]}

    assert _keys(roster("assigned")) == []
    assert _keys(roster("no_assignment")) == ["summary"]
