"""PHILO-4-04 storage fences for the ratified triaged headline.

The six-row fixture is the real ``_compose`` acceptance fixture from the
story-01 canvas harness. The storage test uses MondayBriefService.generate to
compose and persist those rows, then uses the real shelf and latest reads. Its
collector seams are explicit fixture adapters because the current full
producer puts c1 in THIS WEEK (the earlier story-02 proof). The new atlas
walk independently exercises full generation from two real desk decisions;
it does not exercise a due commitment. The extra THIS WEEK fixture below
proves composition and Arrival count scope, not collection.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from holdspeak.db.core import Database
from holdspeak.services.monday_brief_service import (
    BriefItem,
    LedgerSummary,
    MondayBriefService,
)


FIXTURE_PATH = (
    Path(__file__).parents[2]
    / "docs/internal/philo/phase-4/headline/fixture.json"
)
NOW = datetime.datetime(2026, 9, 23, 17, 40)


def _fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _items(fixture: dict[str, Any], section: str) -> list[BriefItem]:
    return [
        BriefItem(
            id=str(row["id"]),
            section=section,
            text=str(row["text"]),
            source_ref=str(row["source_ref"]),
            priority=int(row["priority"]),
        )
        for row in fixture["sections"].get(section, [])
    ]


def _fields(brief: Any) -> dict[str, list[tuple[Any, ...]]]:
    return {
        section: [
            (
                item.id,
                item.section,
                item.text,
                item.detail,
                item.source_ref,
                item.priority,
                item.created_at,
            )
            for item in items
        ]
        for section, items in brief.sections.items()
    }


def _fixture_fields(fixture: dict[str, Any]) -> dict[str, list[tuple[Any, ...]]]:
    return {
        section: [
            (
                str(row["id"]),
                section,
                str(row["text"]),
                None,
                str(row["source_ref"]),
                int(row["priority"]),
                None,
            )
            for row in rows
        ]
        for section, rows in fixture["sections"].items()
    } | {"this_week": [], "broke": []}


def _fixture_producer(service: MondayBriefService, monkeypatch: Any) -> None:
    """Adapt the canonical _compose fixture to the real generate producer.

    No monday_briefs or monday_brief_items rows are injected. generate still
    runs its real composition, INSERTs, and load path. These adapters only
    preserve the story's six-row canvas provenance, whose c1 cannot come from
    the current full collector without being moved to THIS WEEK.
    """

    fixture = _fixture()
    monkeypatch.setattr(service, "_collect_coverage_gaps", lambda _principal: [])
    monkeypatch.setattr(
        service,
        "_collect_waiting",
        lambda _principal: _items(fixture, "waiting"),
    )
    monkeypatch.setattr(
        service,
        "_collect_changes",
        lambda _start, _end: (_items(fixture, "changed"), LedgerSummary()),
    )
    monkeypatch.setattr(service, "_collect_meetings", lambda _start, _end: [])
    monkeypatch.setattr(
        service,
        "_collect_breakage",
        lambda _start, _end, _brief_id: [],
    )
    monkeypatch.setattr(
        service,
        "_collect_decisions",
        lambda _principal, _excluded: _items(fixture, "decisions"),
    )
    monkeypatch.setattr(
        service,
        "_collect_calendar_events",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        service,
        "_collect_meeting_watch",
        lambda *_args, **_kwargs: [],
    )


def test_compose_fixture_has_the_ratified_headline() -> None:
    fixture = _fixture()
    service = MondayBriefService(db=None)
    sections = {
        section: _items(fixture, section)
        for section in ("this_week", "changed", "broke", "waiting", "decisions")
    }

    headline, finalized = service._compose(sections)

    assert headline == fixture["headline"]
    assert sum(len(items) for items in finalized.values()) == fixture["total"]
    assert [
        item.id
        for section in ("changed", "waiting", "decisions")
        for item in finalized[section]
    ] == ["m1", "o1", "u1", "l1", "c1", "d2"]

    variant = fixture["this_week_variant"]
    sections["this_week"] = [
        BriefItem(
            id=str(variant["row"]["id"]),
            section="this_week",
            text=str(variant["row"]["text"]),
            source_ref=str(variant["row"]["source_ref"]),
            priority=int(variant["row"]["priority"]),
        )
    ]
    variant_headline, variant_finalized = service._compose(sections)

    assert variant_headline == variant["headline"]
    assert sum(len(items) for items in variant_finalized.values()) == variant["total"]


def test_real_generate_shelf_and_latest_preserve_all_six_rows(
    tmp_path, monkeypatch
) -> None:
    fixture = _fixture()
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    _fixture_producer(service, monkeypatch)

    generated = service.generate(None, now=NOW)
    generated_fields = _fields(generated)
    assert generated_fields == _fixture_fields(fixture)
    generated_headline = generated.headline
    generated_period = (generated.period_start, generated.period_end, generated.generated_at)

    expected_states = {}
    for index, item_id in enumerate(fixture["arrival_today"]):
        state = "acknowledged" if index % 2 == 0 else "deferred"
        expected_states[item_id] = state
        assert service.shelve(None, item_id, state) == {
            "item_id": item_id,
            "state": state,
        }

    same_day = service.generate(None, now=NOW)
    reopened = MondayBriefService(Database(tmp_path / "brief.db"))
    latest = reopened.get_latest(None)

    assert latest is not None
    assert same_day.id == generated.id == latest.id
    assert same_day.headline == latest.headline == generated_headline == fixture["headline"]
    assert (same_day.period_start, same_day.period_end, same_day.generated_at) == generated_period
    assert (latest.period_start, latest.period_end, latest.generated_at) == generated_period
    assert _fields(same_day) == generated_fields
    assert _fields(latest) == generated_fields
    assert same_day.shelf == latest.shelf == expected_states
    assert service.shelf(None, generated.id) == expected_states
