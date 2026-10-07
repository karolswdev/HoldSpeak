"""PHILO-15-09 (B04): the Brief tells the truth about the day.

Rehearsal 1a (docs/internal/philo/phase-15/rehearsal-1a/BOUNCES.md, B04): after
a meeting, a decision, a person and a Project, the Brief said "No changes", a
second Generate returned the 10:50 brief unchanged, it was titled "Monday
Brief" on a Wednesday, and its two date ranges disagreed.

Rulings fenced here:
  1. Generate on the same day REGENERATES from the current desk: same id, new
     body; an unchanged item keeps its shelf state.
  2. The title is "Brief · <weekday> <date>".
  3. One date range, computed once (the window head and the sent document).
  4. "No changes" only when the collectors found nothing: the rehearsal's day
     (meeting + decision + person + Project) is listed.
"""
from __future__ import annotations

import datetime

from holdspeak.db.core import Database
from holdspeak.people.keys import MemoryKeyStore
from holdspeak.people.store import EncryptedPeopleStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.document_sources import render_document
from holdspeak.services.monday_brief_service import (
    MondayBriefService,
    brief_period_label,
    brief_title,
)
from holdspeak.services.people_service import PeopleService

OWNER = Principal(PrincipalKind.OWNER, "philo15-09-owner")


def _texts(brief) -> list[str]:
    return [item.text for items in brief.sections.values() for item in items]


def _item(brief, text: str):
    return next(item for items in brief.sections.values() for item in items if item.text == text)


def _desk(tmp_path):
    db = Database(tmp_path / "hub.db")
    people = EncryptedPeopleStore(tmp_path / "people.sqlite3", MemoryKeyStore())
    people.initialize()
    return db, people, MondayBriefService(db, people_store=people)


def _the_rehearsal_day(db: Database, people: EncryptedPeopleStore) -> None:
    """What the owner did in rehearsal 1a: a meeting, a decision, a person, a Project."""
    ended = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(minutes=1)
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO meetings (id, started_at, ended_at, title, duration_seconds, capture_status)
               VALUES (?, ?, ?, ?, ?, 'finalized')""",
            ("meeting-day-one", (ended - datetime.timedelta(seconds=35)).isoformat(),
             ended.isoformat(), "Architect sync", 35.0),
        )
    db.desk_decisions.upsert(
        decision_id="decision-sqlite", title="Use SQLite for the local meeting ledger",
        status="accepted",
    )
    db.projects.create_project(project_id="project-ledger", name="Local ledger")
    PeopleService(people).create_relationship(OWNER, {"display_name": "Priya Shah"})


def test_the_rehearsal_day_is_listed_and_generate_regenerates(tmp_path):
    db, people, service = _desk(tmp_path)

    morning = service.generate(None)
    assert morning.headline == "No changes" and morning.is_empty

    _the_rehearsal_day(db, people)
    again = service.generate(None)

    assert again.id == morning.id, "the same day keeps the brief's id"
    assert again.generated_at > morning.generated_at, "a newer GENERATED time"
    assert again.headline != "No changes"
    texts = _texts(again)
    for wanted in (
        "Meeting recorded: Architect sync",
        "Decision made: Use SQLite for the local meeting ledger",
        "Project added: Local ledger",
        "Person added",
    ):
        assert wanted in texts, (wanted, texts)
    # The brief is sent to other places: no People content in it.
    assert not [t for t in texts if "Priya" in t]
    # The decision he made is not one he must review.
    assert "Review decision: Use SQLite for the local meeting ledger" not in texts
    assert service.get_latest(None).id == morning.id
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM monday_briefs").fetchone()[0] == 1


def test_an_unchanged_item_keeps_its_shelf_state_and_a_gone_one_leaves(tmp_path):
    db, people, service = _desk(tmp_path)
    _the_rehearsal_day(db, people)
    first = service.generate(None)
    project = _item(first, "Project added: Local ledger")
    service.shelve(None, project.id, "acknowledged")

    db.projects.create_project(project_id="project-two", name="Second Project")
    db.desk_decisions.delete("decision-sqlite")
    second = service.generate(None)

    kept = _item(second, "Project added: Local ledger")
    assert kept.id == project.id
    assert second.shelf == {project.id: "acknowledged"}
    assert "Project added: Second Project" in _texts(second)
    assert "Decision made: Use SQLite for the local meeting ledger" not in _texts(second)


def test_a_proposed_decision_is_reviewed_not_made(tmp_path):
    db, _people, service = _desk(tmp_path)
    db.desk_decisions.upsert(decision_id="decision-agent", title="Adopt the queue", status="proposed")
    texts = _texts(service.generate(None))
    assert "Review decision: Adopt the queue" in texts
    assert "Decision made: Adopt the queue" not in texts


def test_the_title_is_the_briefs_own_day_and_the_range_is_one():
    # Wednesday 7 Oct 2026: never "Monday" unless it is.
    assert brief_title("2026-10-07T10:50:00-06:00") == "Brief · Wednesday 7 Oct 2026"
    assert brief_title("2026-10-05T08:00:00-06:00") == "Brief · Monday 5 Oct 2026"
    # The window (yesterday 17:00 to now), never the week.
    assert brief_period_label("2026-10-06T17:00:00-06:00", "2026-10-07T10:50:00-06:00") == "OCT 06-07"
    assert brief_period_label("2026-09-30T17:00:00-06:00", "2026-10-01T09:00:00-06:00") == "SEP 30 - OCT 01"


def test_the_sent_document_says_the_same_title_and_range(tmp_path):
    db, people, service = _desk(tmp_path)
    _the_rehearsal_day(db, people)
    brief = service.generate(None)
    document = render_document(db, f"monday_brief:{brief.id}")
    title = brief_title(brief.period_end)
    label = brief_period_label(brief.period_start, brief.period_end)
    assert document.title == title
    assert document.body_md.startswith(f"# {title}\nPeriod: {label}\n")
    assert "Monday Brief" not in document.body_md


def test_the_schedule_keeps_one_brief_a_day(tmp_path):
    db, people, service = _desk(tmp_path)
    morning = service.generate(None, regenerate=False)
    _the_rehearsal_day(db, people)
    scheduled = service.generate(None, regenerate=False)
    assert scheduled.id == morning.id and scheduled.generated_at == morning.generated_at
    assert scheduled.headline == "No changes"
