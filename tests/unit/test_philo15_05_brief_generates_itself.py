"""PHILO-15 lane 05, ruling 2 (inventory gap 10): the morning Brief generates
itself.

The cadence thread's Brief job is ON by default and makes the day's Brief
once per local day at ``brief_hour`` (06:00), before the owner arrives. The
loop job (project, score, nudge) keeps its default: OFF. Quiet hours do not
hold the Brief: it is deterministic and sends nothing.

Real producers: the real CadenceMixin tick body, the real
MondayBriefService.generate over a real database, the real pipeline_events
receipt. The clock is the one fake.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.runtime.cadence import CadenceMixin


class _Runtime(CadenceMixin):
    def __init__(self) -> None:
        self.config = Config()  # the shipped defaults
        self.loop_ticks = 0

    def _cadence_service(self):  # the loop job: record, never run
        runtime = self

        class _Loop:
            def tick(self):
                runtime.loop_ticks += 1
                raise AssertionError("the loop job is off by default")

        return _Loop()


def _briefs(db: Database) -> list[str]:
    with db._connection() as conn:
        return [r["generated_at"] for r in conn.execute(
            "SELECT generated_at FROM monday_briefs ORDER BY generated_at"
        ).fetchall()]


def _receipts(db: Database) -> int:
    with db._connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM pipeline_events WHERE method='brief.regenerated'"
        ).fetchone()[0]


def test_the_brief_job_fires_once_per_local_day_at_its_hour(tmp_path: Path) -> None:
    db = Database(tmp_path / "brief.db")
    runtime = _Runtime()
    assert runtime._cadence_jobs_enabled() is True  # the thread starts on defaults
    clock = {"now": datetime(2026, 10, 8, 5, 55)}

    def tick() -> None:
        with patch("holdspeak.db.get_database", return_value=db), patch(
            "holdspeak.runtime.cadence.local_now", side_effect=lambda: clock["now"]
        ):
            runtime._cadence_tick_body()

    tick()  # 05:55: before the Brief hour (inside quiet hours)
    assert _briefs(db) == [] and _receipts(db) == 0

    clock["now"] = datetime(2026, 10, 8, 6, 0)
    tick()  # 06:00: the Brief is made, still inside quiet hours
    assert len(_briefs(db)) == 1 and _receipts(db) == 1

    for minute in (5, 30, 55):
        clock["now"] = datetime(2026, 10, 8, 7, minute)
        tick()  # the same local day: never twice
    clock["now"] = datetime(2026, 10, 8, 23, 50)
    tick()
    assert len(_briefs(db)) == 1 and _receipts(db) == 1

    clock["now"] = datetime(2026, 10, 9, 6, 1)
    tick()  # the next local day: once more
    assert len(_briefs(db)) == 2 and _receipts(db) == 2
    assert runtime.loop_ticks == 0  # the loop job kept its default: off


def test_the_brief_job_off_makes_no_brief(tmp_path: Path) -> None:
    db = Database(tmp_path / "off.db")
    runtime = _Runtime()
    runtime.config.cadence.brief_enabled = False
    assert runtime._cadence_jobs_enabled() is False  # no thread at all
    with patch("holdspeak.db.get_database", return_value=db), patch(
        "holdspeak.runtime.cadence.local_now", return_value=datetime(2026, 10, 8, 9, 0)
    ):
        runtime._cadence_tick_body()
    assert _briefs(db) == [] and _receipts(db) == 0


def test_the_cadence_status_names_the_brief_job(tmp_path: Path) -> None:
    # The Rhythm row's DAILY token reads this (web/src/pages/cores/CadenceCore.tsx).
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.cadence_service import CadenceService

    db = Database(tmp_path / "status.db")
    owner = Principal(PrincipalKind.OWNER, "philo15-05")
    status = CadenceService(db, Config().cadence).status(owner)
    assert status["enabled"] is False
    assert status["brief_job"] == {"enabled": True, "hour": 6}


# ── Astra r1 (#975) P1: the scheduled Brief never hides work ──────────────


def _seed(db: Database) -> None:
    """A desk with work waiting: a meeting with an unowned action item (and,
    on a fresh desk, the no-engine blocker the needs-you rule raises)."""
    from datetime import timedelta

    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    start = datetime(2026, 10, 7, 15, 0)
    db.meetings.save_meeting(MeetingState(
        id="m-ledger", started_at=start, ended_at=start + timedelta(minutes=30), title="Ledger sync",
        segments=[TranscriptSegment(text="Someone writes the runbook.", speaker="Me", start_time=1.0, end_time=3.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["ledger"], summary="Runbook needed.", action_items=[{
            "id": "m-ledger-a1", "task": "Write the rollback runbook", "owner": None, "due": None,
            "status": "pending", "review_state": "accepted", "source_timestamp": None,
            "created_at": start.isoformat()}]),
        intel_status="completed"))


def _items(brief) -> dict[str, list[str]]:
    return {section: sorted(item.text for item in items) for section, items in brief.sections.items() if items}


def test_the_scheduled_brief_holds_the_same_items_as_the_owners_generate(tmp_path: Path) -> None:
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.monday_brief_service import MondayBriefService

    six = datetime(2026, 10, 8, 6, 0).astimezone()
    scheduled_db = Database(tmp_path / "scheduled.db")
    owner_db = Database(tmp_path / "owner.db")
    _seed(scheduled_db)
    _seed(owner_db)

    runtime = _Runtime()
    with patch("holdspeak.db.get_database", return_value=scheduled_db), patch(
        "holdspeak.runtime.cadence.local_now", return_value=six
    ):
        runtime._cadence_tick_body()
    scheduled = MondayBriefService(scheduled_db).get_latest(Principal(PrincipalKind.OWNER, "owner-session"))
    owners = MondayBriefService(owner_db).generate(Principal(PrincipalKind.OWNER, "owner-session"), now=six)

    assert scheduled is not None
    assert _items(scheduled) == _items(owners), (scheduled.headline, owners.headline)
    # The work the r1 scheduled Brief hid: the blocker and the unowned item.
    assert _items(scheduled)["waiting"] == ["No engine yet", "Unassigned: Write the rollback runbook"]
    assert scheduled.headline == owners.headline
    assert scheduled.headline != "No changes"
    assert not any(text.startswith("NOT READ") for texts in _items(scheduled).values() for text in texts)


def test_an_unread_source_is_a_not_read_row_never_a_silent_zero(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.monday_brief_service import NOT_READ_REF, MondayBriefService

    db = Database(tmp_path / "partial.db")
    # A principal the needs-you rule cannot read for (the r1 defect's shape).
    brief = MondayBriefService(db).generate(
        Principal(PrincipalKind.SERVICE, "heartbeat"), now=datetime(2026, 10, 8, 6, 0).astimezone(),
    )
    waiting = brief.sections.get("waiting") or []
    unread = sorted(item.text for item in waiting if str(item.source_ref).startswith(NOT_READ_REF))
    assert unread == ["NOT READ · AI models", "NOT READ · Decisions"], [i.text for i in waiting]
    assert brief.headline != "No changes"
    assert brief.headline.startswith("2 sources not read")


def test_a_rule_that_cannot_be_read_at_all_is_a_not_read_row(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services import project_service
    from holdspeak.services.monday_brief_service import MondayBriefService

    def broken(self, principal):
        raise RuntimeError("needs-you store is locked")

    monkeypatch.setattr(project_service.ProjectService, "needs_you", broken)
    db = Database(tmp_path / "broken.db")
    brief = MondayBriefService(db).generate(
        Principal(PrincipalKind.OWNER, "owner-session"), now=datetime(2026, 10, 8, 6, 0).astimezone(),
    )
    texts = [item.text for item in brief.sections.get("waiting") or []]
    assert "NOT READ · Needs you" in texts, texts
    assert brief.headline != "No changes"
