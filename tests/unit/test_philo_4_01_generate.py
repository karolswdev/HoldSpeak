"""PHILO-4-01 — Generate is always reachable (the producer's half).

Two fences on the REAL MondayBriefService over a real Database:

1. Ask 5 (ratified 2026-09-23): the empty brief's headline is `No changes`
   (ASD-STE100; it replaces `Nothing material changed.`). Red on the
   pre-fix producer.
2. Acceptance 4: Generate on the next producer-day, while the day-one
   brief still has an untriaged row, leaves the day-one triage exactly as
   it was: the Deferred row stays Deferred, the untriaged row stays
   untriaged (nothing is silently acknowledged or deferred), and the new
   brief starts with an empty shelf. Read back after the generation.
"""

from __future__ import annotations

import datetime
import uuid

from holdspeak.db.core import Database
from holdspeak.services.monday_brief_service import BriefItem, MondayBriefService


def test_empty_brief_headline_is_no_changes(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))

    headline, _sections = service._compose({})
    brief = service.generate(None, now=datetime.datetime(2026, 9, 23, 17, 40))

    assert headline == "No changes"
    assert brief.headline == "No changes"
    assert brief.is_empty is True
    assert service.get_latest(None).headline == "No changes"


def _waiting(*_args, **_kwargs) -> list[BriefItem]:
    """Two carried rows, minted fresh on every generation (the producer's shape)."""
    return [
        BriefItem(
            id=f"brief-item-{uuid.uuid4().hex}",
            section="waiting",
            text="Overdue: Send the vendor review notes",
            source_ref="action_item:o1",
            priority=300,
        ),
        BriefItem(
            id=f"brief-item-{uuid.uuid4().hex}",
            section="waiting",
            text="Unassigned: Draft the migration runbook",
            source_ref="action_item:u1",
            priority=200,
        ),
    ]


def test_next_day_generate_keeps_the_old_brief_triage(tmp_path, monkeypatch):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    monkeypatch.setattr(service, "_collect_waiting", _waiting)

    day_one = service.generate(None, now=datetime.datetime(2026, 9, 23, 17, 40))
    deferred_id, untriaged_id = (item.id for item in day_one.sections["waiting"])
    service.shelve(None, deferred_id, "deferred")
    before = service.shelf(None, day_one.id)
    assert before == {deferred_id: "deferred"}

    day_two = service.generate(None, now=datetime.datetime(2026, 9, 24, 8, 2))

    assert day_two.id != day_one.id
    # Read back: the day-one shelf is byte-for-byte what it was.
    assert service.shelf(None, day_one.id) == before
    assert untriaged_id not in service.shelf(None, day_one.id)
    # The next brief starts untriaged: new item ids, an empty shelf.
    assert service.shelf(None, day_two.id) == {}
    assert not {item.id for item in day_two.sections["waiting"]} & {deferred_id, untriaged_id}
    assert service.get_latest(None).id == day_two.id
