"""People against the real hub, on the daily week (Betterment daily D0).

The fixture is the recon's week (``tests/fixtures/daily_week``): three
meetings, Mira Okafor, Theo Park and Jun Sato, no owner alias set, and the
recon's nine keeps. The hub is ``tests/unit/test_desk_needs_you.py``'s
isolated one (``MeetingWebServer`` + ``TestClient``).
"""
from __future__ import annotations

import json
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


# ── Betterment D6: people come from his work ─────────────────────────────


def _week_without_people(hub: Any) -> None:
    """The recon's three meetings and nine keeps, and no People store at all."""
    from tests.fixtures.daily_week import keep_nine, seed_meetings

    seed_meetings(hub.db)
    keep_nine(hub.client)


def _suggestions(hub: Any) -> list[dict[str, Any]]:
    return _ok(hub.client.get("/api/people/suggestions"))["suggestions"]


def test_his_three_reports_come_from_his_meetings(hub: Any) -> None:
    _week_without_people(hub)
    assert _ok(hub.client.get("/api/people/readiness"))["state"] == "unconfigured"
    found = _suggestions(hub)
    # Theo first (a 1:1), then by promises: Jun owes two, Mira one.
    assert [s["name"] for s in found] == ["Theo", "Jun", "Mira"]
    by_name = {s["name"]: s for s in found}
    # Theo had a 1:1 with him: a Report. Mira and Jun only shared a meeting: Peers.
    assert by_name["Theo"]["relationship_kind"] == "direct_report"
    assert by_name["Mira"]["relationship_kind"] == "peer"
    assert by_name["Mira"]["promise_count"] == 1
    assert by_name["Mira"]["meetings"][0]["title"] == "Payments platform sync"
    # A decision's words, "Me" and the speaker label are never a person.
    assert not {"Do it", "Me", "Remote"} & set(by_name)


def test_three_add_presses_make_them_and_mira_prep_shows_her_promise(hub: Any) -> None:
    _week_without_people(hub)
    made = {}
    for key in ("mira", "theo", "jun"):
        made[key] = _ok(hub.client.post("/api/people/suggestions/add", json={"key": key}), 201)["relationship"]
    assert _ok(hub.client.get("/api/people/readiness"))["state"] == "ready", "the first Add made the store"
    assert _suggestions(hub) == []
    mira = _brief(hub, made["mira"]["id"])
    assert [(a["task"], a["due"]) for a in mira["open_meeting_actions"]] == [("Draft the rollback runbook", "2026-10-20")]
    theo = _brief(hub, made["theo"]["id"])
    assert [a["task"] for a in theo["i_owe_meeting_actions"]] == ["Review design doc on settlement retries"]
    assert made["theo"]["relationship_kind"] == "direct_report"


def test_not_a_person_hides_the_name_for_good(hub: Any) -> None:
    _week_without_people(hub)
    assert _ok(hub.client.post("/api/people/suggestions/hide", json={"key": "Jun"})) == {"hidden": "jun"}
    assert [s["name"] for s in _suggestions(hub)] == ["Theo", "Mira"]
    assert _ok(hub.client.get("/api/people/relationships"))["relationships"] == []


def test_a_one_on_one_series_names_the_full_person_and_links_the_series(hub: Any) -> None:
    import json as _json

    _week_without_people(hub)
    with hub.db._connection() as conn:
        for day in ("2099-10-19T09:30:00", "2099-10-26T09:30:00"):
            conn.execute(
                """INSERT INTO calendar_events (id, uid, title, starts_at, ends_at, last_seen_at,
                       subscription_revision, source_id, source_label, attendees_json)
                   VALUES (?, 'mira-1on1', '1:1 with Mira', ?, ?, 0, 'r1', 'work', 'Work', ?)""",
                (f"ev-{day}", day, day.replace("09:30", "10:00"),
                 _json.dumps(["karol@example.com", "mira.okafor@example.com"])),
            )
    found = {s["name"]: s for s in _suggestions(hub)}
    assert "Mira" not in found, "the spoken Mira and the series are one person"
    mira = found["Mira Okafor"]
    assert mira["said"] == "Mira" and mira["relationship_kind"] == "direct_report"
    assert mira["series"]["next_starts_at"] == "2099-10-19T09:30:00"
    made = _ok(hub.client.post("/api/people/suggestions/add", json={"key": mira["key"]}), 201)["relationship"]
    assert made["display_name"] == "Mira Okafor"
    assert made["owner_aliases"] == ["Mira"]
    assert [link["uid"] for link in made["calendar_links"]] == ["mira-1on1"]
    brief = _brief(hub, made["id"])
    assert brief["next_one_on_one"]["starts_at"] == "2099-10-19T09:30:00"
    assert [a["task"] for a in brief["open_meeting_actions"]] == ["Draft the rollback runbook"]


def test_a_jira_assignee_on_his_watched_issues_is_suggested(hub: Any) -> None:
    import json as _json

    with hub.db._connection() as conn:
        conn.execute(
            """INSERT INTO connector_watches (id, connector_id, query_kind, snapshot_json)
               VALUES ('w-jira', 'jira', 'issues', ?)""",
            (_json.dumps({"entities": {"PAY-1": {"key": "PAY-1", "assignee": "Priya Raman"},
                                       "PAY-2": {"key": "PAY-2", "assignee": "unassigned"}}}),),
        )
    found = _suggestions(hub)
    assert [(s["name"], s["source"], s["jira"]) for s in found] == [("Priya Raman", "jira", True)]


def test_a_people_503_logs_the_readiness_and_the_caller(
    hub: Any, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.services.people_service import PeopleService, PeopleUnavailable

    seed(hub, keep=False)

    def refuse(self: Any, principal: Any, read: bool = False) -> None:
        raise PeopleUnavailable("people_store_unavailable")

    monkeypatch.setattr(PeopleService, "readiness_state", lambda self: "locked")
    monkeypatch.setattr(PeopleService, "_require_ready_owner", refuse)
    with caplog.at_level("WARNING", logger="holdspeak.web.routes.people"):
        response = hub.client.get("/api/people/relationships?counts=1", headers={"Referer": "http://hub/desk"})
    assert response.status_code == 503
    lines = [r.getMessage() for r in caplog.records if "people 503" in r.getMessage()]
    assert lines == ["people 503: code=people_store_unavailable readiness=locked "
                     "caller=GET /api/people/relationships from http://hub/desk"]


def test_mcp_reads_the_suggestions(hub: Any) -> None:
    from holdspeak.mcp.families import people as family
    from holdspeak.principals import Principal, PrincipalKind

    _week_without_people(hub)
    answer = family.dispatch("people.suggestions", {}, Principal(PrincipalKind.OWNER, "mcp-owner"))
    assert [s["name"] for s in answer["suggestions"]] == ["Theo", "Jun", "Mira"]
    assert "people.suggestions" in family.READ_TOOLS


_WIRES = Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__" / "fixtures" / "daily-week"


def test_people_from_work_wire(hub: Any) -> None:
    """The People face's reads on the week with no people, before and after
    the three Add presses (people.app.test.tsx replays them)."""
    from datetime import datetime

    from tests.unit.test_desk_speak import _record

    _week_without_people(hub)
    reads = ("/api/people/readiness", "/api/people/suggestions", "/api/door", "/api/settings")
    before = {path: _ok(hub.client.get(path)) for path in reads}
    assert before["/api/people/readiness"]["state"] == "unconfigured"
    assert not (before["/api/settings"].get("owner") or {}).get("name"), "his own name is not set"
    added = {key: _ok(hub.client.post("/api/people/suggestions/add", json={"key": key}), 201)
             for key in ("theo", "jun", "mira")}
    after = {path: _ok(hub.client.get(path)) for path in (*reads, "/api/people/relationships?counts=1")}
    mira = added["mira"]["relationship"]["id"]
    for path in (f"/api/people/relationships/{mira}", f"/api/people/relationships/{mira}/one-on-ones",
                 f"/api/people/relationships/{mira}/brief"):
        after[path] = _ok(hub.client.get(path))
    assert [a["task"] for a in after[f"/api/people/relationships/{mira}/brief"]["brief"]["open_meeting_actions"]] == [
        "Draft the rollback runbook"]
    # The ids are minted per run; the stored answers name them one way.
    text = json.dumps({"recordedAt": datetime.now().astimezone().isoformat(),
                       "before": before, "added": added, "after": after})
    for key, answer in added.items():
        text = text.replace(answer["relationship"]["id"], f"rel-{key}")
    _record("people-from-work", json.loads(text), Path(hub.db.db_path).parent, "tests/integration/test_desk_people.py::test_people_from_work_wire", folder=_WIRES)


def test_needs_you_says_when_people_could_not_be_read_wire(hub: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """A People store that exists but cannot be read (locked): the hub's
    Needs-you answer names it, and the faces draw one line (needs-you and
    today app tests replay this answer)."""
    from datetime import datetime

    from holdspeak.people.store import EncryptedPeopleStore
    from tests.unit.test_desk_speak import _record

    seeded = seed(hub)
    monkeypatch.setattr(EncryptedPeopleStore, "readiness", lambda self: "locked")
    answer = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))
    assert answer["peopleStoreState"] == "locked"
    assert hub.client.get("/api/people/relationships?counts=1").status_code == 503
    _record("needs-you-people-locked", json.loads(json.dumps({
        "recordedAt": datetime.now().astimezone().isoformat(),
        "gets": {"/api/desk/needs-you?fresh=1": answer, "/api/people/readiness": _ok(hub.client.get("/api/people/readiness"))},
    }).replace(seeded["project"], "proj-daily-week")), Path(hub.db.db_path).parent,
        "tests/integration/test_desk_people.py::test_needs_you_says_when_people_could_not_be_read_wire", folder=_WIRES)


# ── Betterment D7: the 1:1 prep ──────────────────────────────────────────


def test_last_time_is_the_last_one_on_one_with_its_points(hub: Any) -> None:
    people = seed(hub)
    theo = _brief(hub, people["Theo"])["last_time"]
    # The Architecture review is newer, but the 1:1 with Theo is the last 1:1.
    assert (theo["title"], theo["one_on_one"]) == ("1:1 with Theo", True)
    assert [p["task"] for p in theo["points"]] == [
        "Review design doc on settlement retries", "Write up alert rule changes"]


def test_last_time_falls_back_to_the_last_meeting_she_was_in(hub: Any) -> None:
    people = seed(hub)
    mira = _brief(hub, people["Mira"])["last_time"]
    assert (mira["title"], mira["one_on_one"]) == ("Payments platform sync", False)
    assert "Draft the rollback runbook" in [p["task"] for p in mira["points"]]
    assert [d["decision_text"] for d in mira["decisions"]] == ["Freeze ledger writes during the cutover"]


def test_no_meeting_with_a_person_is_no_last_time(hub: Any) -> None:
    seed(hub)
    other = _ok(hub.client.post("/api/people/relationships", json={"display_name": "Priya Raman"}), 201)["relationship"]["id"]
    assert _brief(hub, other)["last_time"] is None


def test_one_on_one_prep_wire(hub: Any) -> None:
    """Today's reads and Mira's prep reads, from ONE boot of the week with her
    1:1 in 90 minutes (today.app.test.tsx presses Prep on the NEXT card;
    people.app.test.tsx draws the prep it opens)."""
    from datetime import date, datetime

    from tests.unit.test_desk_brief import _calendar_today, _ensured
    from tests.unit.test_desk_speak import _record

    seeded = seed(hub, monday=date.today(), engine=True)
    _calendar_today(hub, seeded["Mira"])
    mira = seeded["Mira"]
    gets = {
        "/api/desk/needs-you?fresh=1": _ok(hub.client.get("/api/desk/needs-you?fresh=1")),
        "/api/door": _ok(hub.client.get("/api/door")),
        "/api/brief/latest?ensure=1": _ensured(hub),
        "/api/meetings?limit=40": _ok(hub.client.get("/api/meetings?limit=40")),
        "/api/people/readiness": _ok(hub.client.get("/api/people/readiness")),
    }
    for rid in (mira, seeded["Theo"]):
        for path in (f"/api/people/relationships/{rid}", f"/api/people/relationships/{rid}/one-on-ones",
                     f"/api/people/relationships/{rid}/brief"):
            gets[path] = _ok(hub.client.get(path))
    theo = gets[f"/api/people/relationships/{seeded['Theo']}/brief"]["brief"]
    assert [a["task"] for a in theo["i_owe_meeting_actions"]] == ["Review design doc on settlement retries"]
    brief = gets[f"/api/people/relationships/{mira}/brief"]["brief"]
    assert brief["next_one_on_one"]["title"] == "1:1 with Mira"
    assert brief["last_time"]["title"] == "Payments platform sync"
    assert [a["task"] for a in brief["open_meeting_actions"]] == ["Draft the rollback runbook"]
    text = json.dumps({"recordedAt": datetime.now().astimezone().isoformat(), "gets": gets})
    text = text.replace(seeded["project"], "proj-daily-week")
    for name in ("Mira", "Theo", "Jun"):
        text = text.replace(seeded[name], f"rel-{name.lower()}")
    _record("one-on-one-prep", json.loads(text), Path(hub.db.db_path).parent,
            "tests/integration/test_desk_people.py::test_one_on_one_prep_wire", folder=_WIRES)
