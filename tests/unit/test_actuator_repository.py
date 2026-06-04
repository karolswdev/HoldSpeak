"""HS-37-02 — ActuatorRepository persistence + lifecycle tests.

A proposal is durable, idempotent, lifecycle-enforced, and audited — the
properties that make "no silent egress" provable after the fact.
"""

from __future__ import annotations

import pytest

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState


def _db(tmp_path) -> Database:
    db = Database(tmp_path / "actuators.db")
    # actuator_proposals FK-references meetings(id) — seed one.
    from datetime import datetime

    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="t", segments=[])
    )
    return db


def _record(db: Database, *, key="k1", **overrides):
    kwargs = dict(
        meeting_id="m1",
        window_id="w1",
        plugin_id="followup_ticket_actuator",
        plugin_version="1.0.0",
        idempotency_key=key,
        target="github",
        action="create_issue",
        preview="Open a follow-up issue for the unowned action item",
        payload={"repo": "acme/app", "title": "Follow up"},
        reversible=True,
        required_capabilities=["actuator"],
    )
    kwargs.update(overrides)
    return db.actuators.record_proposal(**kwargs)


# ──────────────────────────── Round-trip ──────────────────────────────


def test_record_and_reload_all_fields(tmp_path) -> None:
    db = _db(tmp_path)
    proposal = _record(db)

    assert proposal.status == "proposed"
    assert proposal.target == "github"
    assert proposal.action == "create_issue"
    assert proposal.preview.startswith("Open a follow-up")
    assert proposal.payload == {"repo": "acme/app", "title": "Follow up"}
    assert proposal.reversible is True
    assert proposal.required_capabilities == ["actuator"]
    assert proposal.decided_by is None and proposal.executed_at is None

    reloaded = db.actuators.get_proposal(proposal.id)
    assert reloaded == proposal

    listed = db.actuators.list_proposals("m1")
    assert [p.id for p in listed] == [proposal.id]
    assert db.actuators.list_proposals("m1", status="proposed")
    assert db.actuators.list_proposals("m1", status="executed") == []


def test_opening_audit_entry_is_written(tmp_path) -> None:
    db = _db(tmp_path)
    proposal = _record(db)
    audit = db.actuators.list_audit(proposal.id)
    assert len(audit) == 1
    assert audit[0].from_status is None
    assert audit[0].to_status == "proposed"
    assert audit[0].actor == "system"


# ──────────────────────────── Idempotency ─────────────────────────────


def test_re_proposal_is_idempotent(tmp_path) -> None:
    db = _db(tmp_path)
    first = _record(db, key="same")
    second = _record(db, key="same", preview="DIFFERENT (ignored)")

    assert first.id == second.id
    assert second.preview == first.preview  # original row, unchanged
    assert len(db.actuators.list_proposals("m1")) == 1
    # No duplicate opening audit entry.
    assert len(db.actuators.list_audit(first.id)) == 1


# ──────────────────────────── Lifecycle ───────────────────────────────


def test_full_lifecycle_proposed_approved_executed(tmp_path) -> None:
    db = _db(tmp_path)
    p = _record(db)

    approved = db.actuators.transition_proposal(p.id, to_status="approved", actor="karol")
    assert approved.status == "approved"
    assert approved.decided_by == "karol"
    assert approved.decided_at is not None
    assert approved.executed_at is None

    executed = db.actuators.transition_proposal(
        p.id, to_status="executed", result={"issue_url": "https://x/1"}
    )
    assert executed.status == "executed"
    assert executed.executed_at is not None
    assert executed.result == {"issue_url": "https://x/1"}
    # decided_by preserved from the approval (the human), not overwritten.
    assert executed.decided_by == "karol"

    audit = db.actuators.list_audit(p.id)
    assert [(a.from_status, a.to_status) for a in audit] == [
        (None, "proposed"),
        ("proposed", "approved"),
        ("approved", "executed"),
    ]


def test_reject_is_terminal(tmp_path) -> None:
    db = _db(tmp_path)
    p = _record(db)
    rejected = db.actuators.transition_proposal(p.id, to_status="rejected", actor="karol")
    assert rejected.status == "rejected"
    with pytest.raises(ValueError, match="illegal"):
        db.actuators.transition_proposal(p.id, to_status="approved")


def test_failed_can_be_re_approved_for_retry(tmp_path) -> None:
    db = _db(tmp_path)
    p = _record(db)
    db.actuators.transition_proposal(p.id, to_status="approved")
    failed = db.actuators.transition_proposal(
        p.id, to_status="failed", error="connector timeout"
    )
    assert failed.status == "failed"
    assert failed.error == "connector timeout"
    # retry path: failed -> approved -> executed
    db.actuators.transition_proposal(p.id, to_status="approved")
    executed = db.actuators.transition_proposal(p.id, to_status="executed")
    assert executed.status == "executed"


@pytest.mark.parametrize(
    "from_to",
    [
        ("proposed", "executed"),  # must be approved first
        ("proposed", "failed"),
        ("executed", "proposed"),  # terminal
    ],
)
def test_illegal_transitions_are_rejected(tmp_path, from_to) -> None:
    db = _db(tmp_path)
    p = _record(db)
    src, dst = from_to
    # Drive to the `src` state legally first.
    if src == "executed":
        db.actuators.transition_proposal(p.id, to_status="approved")
        db.actuators.transition_proposal(p.id, to_status="executed")
    with pytest.raises(ValueError, match="illegal|unknown"):
        db.actuators.transition_proposal(p.id, to_status=dst)


def test_unknown_status_and_unknown_proposal(tmp_path) -> None:
    db = _db(tmp_path)
    p = _record(db)
    with pytest.raises(ValueError, match="unknown proposal status"):
        db.actuators.transition_proposal(p.id, to_status="banana")
    with pytest.raises(KeyError):
        db.actuators.transition_proposal("nope", to_status="approved")


def test_required_fields_validated(tmp_path) -> None:
    db = _db(tmp_path)
    with pytest.raises(ValueError, match="target is required"):
        _record(db, target="  ")
    with pytest.raises(ValueError, match="idempotency_key is required"):
        _record(db, key="")


# ──────────── Persistence adapter: a `proposed` run → a proposal ───────────


def test_record_actuator_proposal_from_a_proposed_run(tmp_path) -> None:
    # HS-37-02: the pipeline persistence seam — a `proposed` PluginRun carries
    # the ActuatorProposal payload (HS-37-01) and lands as a durable proposal.
    from holdspeak.plugins.contracts import PluginRun
    from holdspeak.plugins.persistence import record_actuator_proposal

    db = _db(tmp_path)
    run = PluginRun(
        plugin_id="followup_ticket_actuator",
        plugin_version="1.0.0",
        window_id="w1",
        meeting_id="m1",
        profile="balanced",
        status="proposed",
        idempotency_key="run-key-1",
        started_at=0.0,
        finished_at=0.1,
        duration_ms=100.0,
        output={
            "target": "jira",
            "action": "create_issue",
            "preview": "File a follow-up ticket",
            "payload": {"project": "ENG", "summary": "Follow up"},
            "reversible": False,
            "required_capabilities": ["actuator"],
        },
    )
    record_actuator_proposal(db, run)

    proposals = db.actuators.list_proposals("m1")
    assert len(proposals) == 1
    assert proposals[0].status == "proposed"
    assert proposals[0].target == "jira"
    assert proposals[0].payload == {"project": "ENG", "summary": "Follow up"}
    assert proposals[0].idempotency_key == "run-key-1"
