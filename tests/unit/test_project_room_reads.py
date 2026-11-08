"""The Room's reads live in project_room_reads; ProjectService delegates (2026-11-08).

The move changes no answer: each ``ProjectService._read_room_*`` method gives
the same dict as the module function for one seeded Room, and the module
loads without the project runtime.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import project_room_reads as room_reads
from holdspeak.services.project_service import ProjectService

OWNER = Principal(PrincipalKind.OWNER, "room-reads-test")


def test_the_room_reads_module_does_not_reach_the_project_service() -> None:
    probe = ("import sys, holdspeak.services.project_room_reads; "
             "print(' '.join(sorted(m for m in sys.modules if m.startswith('holdspeak'))))")
    loaded = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, check=True).stdout.split()
    assert "holdspeak.services.project_room_reads" in loaded, loaded
    for module in loaded:
        assert "project_service" not in module, loaded
        assert not module.startswith(("holdspeak.web", "holdspeak.runtime")), loaded


@pytest.fixture
def seeded(tmp_path):
    reset_database()
    db = Database(tmp_path / "room-reads.db")
    svc = ProjectService(db, review_available=True)
    project_id = svc.create_project(OWNER, {"name": "Atlas"})["id"]
    past = (datetime.now(timezone.utc) - timedelta(days=3)).date().isoformat()
    svc.create_item(OWNER, project_id, {"item_type": "milestone", "title": "Beta", "due_at": past})
    svc.create_item(OWNER, project_id, {"item_type": "risk", "title": "Vendor late", "severity": "high",
                                        "details": {"likelihood": "high", "impact": "slip"}})
    db.project_observations.insert_review(
        review_id="prev_reads", project_id=project_id, status="open", opened_at="2026-01-10T10:00:00+00:00")
    db.project_observations.insert_proposal(
        proposal_id="pprop_reads", project_id=project_id, review_window_key="prev_reads",
        proposal_kind="add_item", target_ref="ref-0", title="proposal 0")
    yield db, svc, project_id
    reset_database()


def test_each_delegating_method_answers_what_the_module_function_answers(seeded) -> None:
    db, svc, pid = seeded
    now = datetime.now(timezone.utc)
    pairs: list[tuple[Any, Any]] = [
        (svc._read_room_items(pid), room_reads._read_room_items(db, pid)),
        (svc._read_room_resources(pid), room_reads._read_room_resources(db, pid)),
        (svc._read_room_changes(pid), room_reads._read_room_changes(db, pid)),
        (svc._read_room_updates(OWNER, pid), room_reads._read_room_updates(db, OWNER, pid)),
        (svc._read_room_steward(pid), room_reads._read_room_steward(db, pid)),
        (svc._read_room_review(pid), room_reads._read_room_review(db, pid, review_available=True)),
        (svc._read_room_needs_you(pid), room_reads._read_room_needs_you(
            db, pid, review_available=True, proposal_needs=svc.proposal_needs,
            resolve_review_people=svc._resolve_review_people)),
        (svc._read_room_sources(pid), room_reads._read_room_sources(db, pid)),
        (svc._read_room_health(pid, None), room_reads._read_room_health(
            db, pid, None, resolve_review_people=svc._resolve_review_people)),
        (svc._read_room_since_read(pid, None), room_reads._read_room_since_read(db, pid, None)),
        (svc._read_room_decisions(pid), room_reads._read_room_decisions(db, pid)),
        (svc._read_room_commitments(pid), room_reads._read_room_commitments(db, pid)),
        (svc._read_room_receipts(pid), room_reads._read_room_receipts(db, pid)),
        (svc._room_overdue_milestone_items(pid, now), room_reads._room_overdue_milestone_items(db, pid, now)),
        (svc._count_overdue_commitments(pid), room_reads._count_overdue_commitments(db, pid)),
        (svc._room_week(OWNER, pid), room_reads._room_week(db, OWNER, pid)),
    ]
    for via_service, via_module in pairs:
        assert via_service == via_module
    # The seed is visible: the overdue milestone is a Needs-you row.
    needs = pairs[6][0]["items"]
    assert any(row.get("kind") == "milestone" for row in needs)
    assert [row["title"] for row in needs if row.get("source") == "delta"] == ["1 proposal waiting"]
    # The pure helpers are the module's own function objects.
    assert ProjectService._nudge_target is room_reads._nudge_target
    assert ProjectService._fold_watch_duplicates is room_reads._fold_watch_duplicates
    assert ProjectService._read_room_target is room_reads._read_room_target
    # The whole Room still composes from the delegates.
    assert svc.room(OWNER, pid)["now"]["state"] == "ok"
