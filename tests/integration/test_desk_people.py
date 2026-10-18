"""People against the real hub, on the daily week (Betterment daily D0).

The fixture is the recon's week (``tests/fixtures/daily_week``): three
meetings, Mira Okafor, Theo Park and Jun Sato, no owner alias set, and the
recon's nine keeps. The hub is ``tests/unit/test_desk_needs_you.py``'s
isolated one (``MeetingWebServer`` + ``TestClient``).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "tests" / "unit"))
sys.path.insert(0, str(_ROOT))
from test_desk_needs_you import _ok, hub  # noqa: E402,F401  (the fixture)

from tests.fixtures.daily_week import seed  # noqa: E402


def _people() -> Any:
    from holdspeak.people import production_people_store
    from holdspeak.services.people_service import PeopleService

    return PeopleService(production_people_store())


def _brief(hub: Any, relationship_id: str) -> dict[str, Any]:
    return _ok(hub.client.get(f"/api/people/relationships/{relationship_id}/brief"))["brief"]


def test_a_first_name_reaches_the_person_with_no_alias(hub: Any) -> None:
    """Mira's promise shows in Mira's prep, its due a date, with no press."""
    people = seed(hub)
    mira = _brief(hub, people["Mira"])
    assert [(a["task"], a["due"], a["due_said"]) for a in mira["open_meeting_actions"]] == [
        ("Draft the rollback runbook", "2026-10-20", "Tuesday"),
    ]
    detail = _ok(hub.client.get(f"/api/people/relationships/{people['Mira']}"))["relationship"]
    assert not detail.get("owner_aliases"), "no alias was needed"


def test_what_i_owe_theo_comes_from_our_one_on_one(hub: Any) -> None:
    """'I'll review your design doc by Monday', said in the 1:1, is mine for Theo."""
    people = seed(hub)
    theo = _brief(hub, people["Theo"])
    assert [(a["task"], a["due"]) for a in theo["i_owe_meeting_actions"]] == [
        ("Review design doc on settlement retries", "2026-10-19"),
    ]
    assert sorted(a["task"] for a in theo["open_meeting_actions"]) == [
        "Profile the reconciliation job", "Write up alert rule changes",
    ]
    # Email Dana was said in a four-person meeting and names no Person: nobody's.
    for name in ("Mira", "Jun"):
        assert _brief(hub, people[name])["i_owe_meeting_actions"] == []


def test_a_mine_row_that_names_one_person_is_for_that_person(hub: Any) -> None:
    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment
    from datetime import datetime, timedelta

    people = seed(hub)
    start = datetime(2026, 10, 16, 16, 0)
    hub.db.meetings.save_meeting(MeetingState(
        id="m-daily-ops", started_at=start, ended_at=start + timedelta(minutes=20), title="Ops",
        segments=[TranscriptSegment(text=t, speaker=s, start_time=0.0, end_time=5.0)
                  for s, t in (("Me", "I'll share the cutover checklist with Jun."),
                               ("Mira", "Fine."), ("Theo", "Fine."))],
        intel=IntelSnapshot(timestamp=5.0, summary="", action_items=[ActionItem(
            task="Share the cutover checklist with Jun", owner="Me", due="Tuesday",
            review_state="accepted")]),
        intel_status="complete"))
    assert [a["task"] for a in _brief(hub, people["Jun"])["i_owe_meeting_actions"]] == [
        "Share the cutover checklist with Jun",
    ]


def test_two_people_with_one_first_name_stay_unresolved(hub: Any) -> None:
    people = seed(hub)
    other = _ok(hub.client.post("/api/people/relationships", json={
        "display_name": "Mira Chen", "relationship_kind": "peer",
    }), 201)["relationship"]["id"]
    for rid in (people["Mira"], other):
        assert _brief(hub, rid)["open_meeting_actions"] == []
    resolved = _people().resolve_owner_candidates("Mira")
    assert resolved["link"] == "ambiguous" and resolved["relationship"] is None
    assert {c["id"] for c in resolved["candidates"]} == {people["Mira"], other}


@pytest.mark.parametrize("name", ["Theo Park", "theo", "THEO"])
def test_a_full_or_first_name_resolves(hub: Any, name: str) -> None:
    people = seed(hub, keep=False)
    resolved = _people().resolve_relationship_by_owner(name)
    assert resolved["relationship"]["id"] == people["Theo"]
