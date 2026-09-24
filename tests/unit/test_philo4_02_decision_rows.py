"""PHILO-4-02 red fences for decision provenance and Arrival order."""

from __future__ import annotations

import datetime
import uuid
from types import SimpleNamespace

from holdspeak.db.core import Database
from holdspeak.meeting_session import MeetingState
from holdspeak.services.monday_brief_service import MondayBriefService
import holdspeak.services.monday_brief_service as brief_module


NOW = datetime.datetime(2026, 8, 4, 9, 30)


def _upsert_desk_decision(
    db: Database,
    *,
    decision_id: str,
    title: str,
    created_at: str,
) -> None:
    # This is the same durable desk-decision producer used by the desk. The
    # ids are deliberately not a recency signal.
    db.desk_decisions.upsert(
        decision_id=decision_id,
        title=title,
        status="proposed",
        created_at=created_at,
    )


def _fixed_uuid4(*values: str):
    sequence = iter(values)
    return lambda: uuid.UUID(next(sequence))


def test_generate_carries_created_at_on_every_decision_item(tmp_path, monkeypatch):
    db = Database(tmp_path / "brief.db")
    service = MondayBriefService(db, clock=lambda: NOW)
    _upsert_desk_decision(
        db,
        decision_id="decision-z-old",
        title="Old decision one",
        created_at="2026-08-01T08:45:00",
    )
    _upsert_desk_decision(
        db,
        decision_id="decision-a-new",
        title="Newest decision",
        created_at="2026-08-04T08:45:00",
    )
    monkeypatch.setattr(
        brief_module,
        "uuid",
        SimpleNamespace(uuid4=_fixed_uuid4("f" * 32, "0" * 32, "1" * 32)),
    )

    generated = service.generate(None, now=NOW)
    reloaded = service.get_latest(None)
    assert reloaded is not None
    assert generated.id == reloaded.id
    assert [item.created_at for item in reloaded.sections["decisions"]] == [
        "2026-08-04T08:45:00",
        "2026-08-01T08:45:00",
    ]
    assert all(item.created_at for item in reloaded.sections["decisions"])


def test_generate_and_reload_sorts_decisions_by_record_created_at(tmp_path, monkeypatch):
    db = Database(tmp_path / "brief.db")
    service = MondayBriefService(db, clock=lambda: NOW)
    _upsert_desk_decision(
        db,
        decision_id="decision-z-old",
        title="Old decision one",
        created_at="2026-08-01T08:45:00",
    )
    _upsert_desk_decision(
        db,
        decision_id="decision-m-old",
        title="Old decision two",
        created_at="2026-08-02T08:45:00",
    )
    _upsert_desk_decision(
        db,
        decision_id="decision-a-new",
        title="Newest decision",
        created_at="2026-08-04T08:45:00",
    )
    # The generated item ids are fixed only to make the pre-fix reload order
    # deterministic. The assertion below uses the record timestamps/text.
    monkeypatch.setattr(
        brief_module,
        "uuid",
        SimpleNamespace(uuid4=_fixed_uuid4("f" * 32, "0" * 32, "1" * 32, "2" * 32)),
    )

    service.generate(None, now=NOW)
    reloaded = service.get_latest(None)
    assert reloaded is not None
    assert [item.text for item in reloaded.sections["decisions"]] == [
        "Review decision: Newest decision",
        "Review decision: Old decision two",
        "Review decision: Old decision one",
    ]


def test_generate_carries_created_at_from_meeting_decision_projection(tmp_path):
    db = Database(tmp_path / "brief.db")
    db.meetings.save_meeting(
        MeetingState(
            id="meeting-decision-source",
            title="Decision fixture",
            started_at=datetime.datetime(2026, 8, 3, 8),
            ended_at=datetime.datetime(2026, 8, 3, 8, 30),
        )
    )
    db.plugins.record_artifact(
        artifact_id="decision-artifact",
        meeting_id="meeting-decision-source",
        artifact_type="decisions",
        title="Decision fixture",
        structured_json={"decisions": [{"decision": "Use the local desk"}]},
        plugin_id="decision_capture",
    )
    decision = db.decisions.list(lifecycle="recorded")[0]

    service = MondayBriefService(db, clock=lambda: NOW)
    service.generate(None, now=NOW)
    reloaded = service.get_latest(None)
    assert reloaded is not None
    item = next(
        item for item in reloaded.sections["decisions"]
        if item.text == "Review decision: Use the local desk"
    )
    assert item.created_at == decision.created_at
