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

import pytest
import re

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

    morning = service.generate(OWNER)
    # A cold desk: at most the setup row (no summary engine), none of the day.
    assert not [t for t in _texts(morning) if t.startswith(("Meeting recorded", "Decision made", "Project added"))]

    _the_rehearsal_day(db, people)
    again = service.generate(OWNER)

    assert again.id == morning.id, "the same day keeps the brief's id"
    assert again.generated_at > morning.generated_at, "a newer GENERATED time"
    assert again.headline != morning.headline
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
    first = service.generate(OWNER)
    project = _item(first, "Project added: Local ledger")
    service.shelve(None, project.id, "acknowledged")

    db.projects.create_project(project_id="project-two", name="Second Project")
    db.desk_decisions.delete("decision-sqlite")
    second = service.generate(OWNER)

    kept = _item(second, "Project added: Local ledger")
    assert kept.id == project.id
    assert second.shelf == {project.id: "acknowledged"}
    assert "Project added: Second Project" in _texts(second)
    assert "Decision made: Use SQLite for the local meeting ledger" not in _texts(second)


def test_a_proposed_decision_is_reviewed_not_made(tmp_path):
    db, _people, service = _desk(tmp_path)
    db.desk_decisions.upsert(decision_id="decision-agent", title="Adopt the queue", status="proposed")
    texts = _texts(service.generate(OWNER))
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
    brief = service.generate(OWNER)
    document = render_document(db, f"monday_brief:{brief.id}")
    title = brief_title(brief.period_end)
    label = brief_period_label(brief.period_start, brief.period_end)
    assert document.title == title
    assert document.body_md.startswith(f"# {title}\nPeriod: {label}\n")
    assert "Monday Brief" not in document.body_md


def test_the_schedule_keeps_one_brief_a_day(tmp_path):
    db, people, service = _desk(tmp_path)
    morning = service.generate(OWNER, regenerate=False)
    _the_rehearsal_day(db, people)
    scheduled = service.generate(OWNER, regenerate=False)
    assert scheduled.id == morning.id and scheduled.generated_at == morning.generated_at
    assert scheduled.headline == morning.headline
    assert _texts(scheduled) == _texts(morning)


# ── Astra r1 (P1): the Brief never asks for the People key ────────────


class _SpyKeys(MemoryKeyStore):
    """A key store that counts every key request and can be locked."""

    def __init__(self) -> None:
        super().__init__()
        self.gets = 0
        self.locked = False

    def get(self, key_id: str) -> bytes:
        self.gets += 1
        if self.locked:
            from holdspeak.people.keys import PeopleKeyError

            raise PeopleKeyError("people_key_missing")
        return super().get(key_id)


def _hub_door(db: Database, people: EncryptedPeopleStore):
    """The Door as the hub composes it (web_server.py: People projection on)."""
    from holdspeak.services.door_service import DoorService
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.refinement_thought_service import RefinementThoughtService

    people_service = PeopleService(people)
    return DoorService(
        FollowThroughService(db, people_projection=people_service), RefinementThoughtService(db),
        db.scheduled_recordings, db.calendar_events, db=db, people_service=people_service,
    )


def _keyed_desk(tmp_path, monkeypatch):
    from holdspeak.services import needs_you_membership

    db = Database(tmp_path / "hub.db")
    keys = _SpyKeys()
    people = EncryptedPeopleStore(tmp_path / "people.sqlite3", keys)
    people.initialize()
    _the_rehearsal_day(db, people)
    service = PeopleService(people)
    rel = service.create_relationship(OWNER, {"display_name": "Sam Rivera"})
    request = service.create_request(OWNER, rel["id"], {"body": "Sam: send the status by Thursday"})
    service.accept_request(OWNER, request["id"])
    door = _hub_door(db, people)
    monkeypatch.setattr(
        needs_you_membership, "_hub_service",
        lambda name, build: door if name == "door_service" else build(),
    )
    return db, people, keys


def _conductor():
    """The scheduled job's own principal (runtime/cadence.py, #975)."""
    from holdspeak.runtime.cadence import BRIEF_PRINCIPAL_IDENTITY

    return Principal(PrincipalKind.BRIEF_CONDUCTOR, BRIEF_PRINCIPAL_IDENTITY)


PRINCIPALS = pytest.mark.parametrize("who", ["owner", "brief_conductor"])


def _who(name: str):
    return OWNER if name == "owner" else _conductor()


@PRINCIPALS
def test_the_scheduled_brief_asks_for_no_key(tmp_path, monkeypatch, who):
    db, people, keys = _keyed_desk(tmp_path, monkeypatch)
    # Control: the hub's own Needs read (the owner's face) asks for the key.
    from holdspeak.services.project_service import ProjectService

    keys.gets = 0
    ProjectService(db).needs_you(OWNER)
    assert keys.gets > 0, "the control must reach the People store"

    keys.gets = 0
    # The scheduled path (runtime/cadence.py): its brief-conductor principal
    # (#975), and the OWNER too (Astra r2: both principals).
    brief = MondayBriefService(db, people_store=people).generate(
        _who(who), regenerate=False, people_reads=False)
    assert keys.gets == 0, "the scheduled Brief asked for the People key"
    texts = _texts(brief)
    assert "Person added" not in texts  # two people: the plural line
    assert "2 people added" in texts
    assert not [t for t in texts if "Sam" in t or "Priya" in t]
    # The scheduled Brief says what it skipped: one counted NOT READ row.
    from holdspeak.services.monday_brief_service import PEOPLE_NOT_READ_TEXT

    assert texts.count(PEOPLE_NOT_READ_TEXT) == 1, texts
    row = next(i for i in brief.sections["waiting"] if i.text == PEOPLE_NOT_READ_TEXT)
    assert row.source_ref == "not_read:people"
    assert brief.headline.startswith("1 source not read"), brief.headline
    # The guard is what holds: the owner's own Generate (people_reads) reaches
    # the key, and the full brief has no NOT READ row.
    keys.gets = 0
    full = MondayBriefService(db, people_store=people).generate(OWNER)
    assert keys.gets > 0
    assert PEOPLE_NOT_READ_TEXT not in _texts(full)
    assert full.id == brief.id


@PRINCIPALS
def test_a_locked_people_store_makes_the_same_brief(tmp_path, monkeypatch, who):
    db, people, keys = _keyed_desk(tmp_path, monkeypatch)
    service = MondayBriefService(db, people_store=people)
    open_store = service.generate(_who(who), people_reads=False)
    keys.locked = True
    keys.gets = 0
    locked = service.generate(_who(who), people_reads=False)
    assert keys.gets == 0
    assert locked.id == open_store.id
    assert sorted(_texts(locked)) == sorted(_texts(open_store))
    assert locked.headline == open_store.headline


def test_the_cadence_job_makes_the_brief_key_free():
    """The scheduled job's own call (runtime/cadence.py) passes both flags."""
    import inspect

    from holdspeak.runtime import cadence

    source = inspect.getsource(cadence)
    assert "regenerate=False, people_reads=False" in source


def test_no_people_store_means_nothing_skipped(tmp_path):
    db = Database(tmp_path / "hub.db")
    absent = EncryptedPeopleStore(tmp_path / "none.sqlite3", MemoryKeyStore())
    from holdspeak.services.monday_brief_service import PEOPLE_NOT_READ_TEXT

    brief = MondayBriefService(db, people_store=absent).generate(OWNER, people_reads=False)
    assert PEOPLE_NOT_READ_TEXT not in _texts(brief)


def test_the_owners_generate_keeps_the_people_row_when_its_read_fails(tmp_path, monkeypatch):
    """Astra r2, P1: the owner's Generate with the key request refused: People
    was not read, so the NOT READ row stays and the brief is PARTIAL (a
    ``not_read:`` row; ChairHome's briefIsPartial)."""
    from holdspeak.services.monday_brief_service import NOT_READ_REF, PEOPLE_NOT_READ_TEXT

    db, people, keys = _keyed_desk(tmp_path, monkeypatch)
    keys.locked = True
    keys.gets = 0
    brief = MondayBriefService(db, people_store=people).generate(OWNER)
    assert keys.gets > 0, "the owner's Generate asked for the key"
    row = next(i for i in brief.sections["waiting"] if i.text == PEOPLE_NOT_READ_TEXT)
    assert row.source_ref.startswith(NOT_READ_REF)
    assert "source not read" in brief.headline or "sources not read" in brief.headline, brief.headline
    # Unlocked, the owner's Generate reads People and the row leaves.
    keys.locked = False
    full = MondayBriefService(db, people_store=people).generate(OWNER)
    assert PEOPLE_NOT_READ_TEXT not in _texts(full)


def test_an_unread_source_is_said_once(tmp_path, monkeypatch):
    """Astra r2, P2: a failed coder registry is ONE source not read, never also
    a thing waiting (the hub's count includes it; the Brief's waiting count is
    the members)."""
    from holdspeak.services import needs_you_membership as membership

    db = Database(tmp_path / "hub.db")

    def broken():
        raise RuntimeError("registry unreadable")

    monkeypatch.setattr(membership, "_read_coders", broken)
    brief = MondayBriefService(db).generate(OWNER)
    waiting = brief.sections["waiting"]
    coders = [i for i in waiting if i.source_ref == "not_read:coders"]
    assert len(coders) == 1, [(i.text, i.source_ref) for i in waiting]
    members = [i for i in waiting if not str(i.source_ref).startswith(("not_read:", "coverage:"))]
    assert re.search(r"(\d+) sources? not read", brief.headline).group(1) == str(len(waiting) - len(members))
    things = re.search(r"(\d+) things? waiting", brief.headline)
    assert (int(things.group(1)) if things else 0) == len(members), (brief.headline, members)
