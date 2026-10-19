"""Betterment daily D8: notices only for what needs him (owner decision 2).

The hub half, on the recon's week (tests/fixtures/daily_week/) through the
product's own producers, with today as its Monday and the LAN engine set (the
one number reads 4: Email Dana and the design review are his, due today; two
decisions wait). ``HOLDSPEAK_DESKTOP_NOTIFY=0`` (the rig switch) keeps every
post off the owner's screen; the decision is still recorded in the receipt.

Also here: the two D8 follow-ups on the same rule, "No engine for summaries"
asks only when a meeting waits, and People on a desk with no store yet (or no
keychain) is never a 503 loop.
"""
from __future__ import annotations

import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from test_desk_needs_you import _boot  # noqa: E402
from test_philo5_the_loop import Hub  # noqa: E402

OWNER = None


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak import desk_presence
    from holdspeak.db import reset_database

    keyfile = tmp_path / "people.key"
    keyfile.write_text("{}")
    keyfile.chmod(0o600)
    desk_presence.clear()
    yield _boot(tmp_path, monkeypatch)
    desk_presence.clear()
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _owner() -> Any:
    from holdspeak.principals import Principal, PrincipalKind

    return Principal(PrincipalKind.OWNER, "d8-heartbeat")


def _calendar(hub: Hub, mira: str, *, minutes: int) -> datetime:
    """A 1:1 with Mira ``minutes`` from now (her series linked to her), applied
    by the real calendar ingest. Returns its start."""
    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

    start = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(minutes=minutes)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HoldSpeak//daily D8//EN",
             "BEGIN:VEVENT", "UID:daily-mira-1on1", f"DTSTART:{start:%Y%m%dT%H%M%SZ}",
             f"DTEND:{start + timedelta(minutes=30):%Y%m%dT%H%M%SZ}", "SUMMARY:1:1 with Mira", "END:VEVENT",
             "END:VCALENDAR", ""]
    ics = Path(tempfile.mkdtemp(prefix="daily-d8-ics-")) / "week.ics"
    ics.write_text("\r\n".join(lines), encoding="utf-8")
    put = hub.client.put("/api/settings", json={"calendar": {"sources": [
        {"id": "daily-work", "label": "Work", "url": str(ics), "enabled": True}]}})
    assert put.status_code == 200, put.text
    assert CalendarIngestConductor().refresh() is True
    linked = hub.client.post(f"/api/people/relationships/{mira}/calendar-links",
                             json={"uid": "daily-mira-1on1", "source_id": "daily-work", "label": "1:1 with Mira"})
    assert linked.status_code == 200, linked.text
    return start


def _heartbeat(hub: Hub, *, notifier: Any = None, quiet: tuple[int, int] | None = None) -> Any:
    from holdspeak.services.heartbeat_service import HeartbeatService

    service = HeartbeatService(hub.db, notifier=notifier)
    hour = datetime.now().hour
    start, end = quiet if quiet is not None else ((hour + 3) % 24, (hour + 5) % 24)
    service.update_settings({"notify": "edge", "quiet_hours": {"start": start, "end": end}})
    return service


def _titles(hub: Hub, ids: list[str]) -> list[str]:
    rows = hub.client.get("/api/desk/needs-you?fresh=1").json()["items"]
    by_id = {str(row.get("notifyKey") or row.get("id")): row["title"] for row in rows}
    return sorted(by_id.get(key, key) for key in ids)


def test_a_sweep_notifies_for_his_due_rows_and_never_for_theirs(hub: Hub) -> None:
    """Email Dana (mine, due today) notifies; Theo's rows (theirs) never do,
    nor the decisions with no meeting soon. The rig posts nothing and the
    receipt records the decision."""
    from tests.fixtures.daily_week import seed

    seed(hub, monday=date.today(), engine=True)
    service = _heartbeat(hub)
    receipt = service._run_notification_decision(_owner(), service.get_settings())
    told = _titles(hub, receipt["noticeItems"])
    assert told == ["Email Dana about the cutover window", "Review design doc on settlement retries"], told
    for theirs in ("Profile the reconciliation job", "Write up alert rule changes",
                   "Draft the rollback runbook", "Do it"):
        assert theirs not in told
    assert receipt["count"] == 4
    assert receipt["fired"] is False and receipt["outcome"] == "not_posted_in_rig", receipt


def test_the_morning_notice_replaces_the_backlog_and_names_the_first_meeting(hub: Hub) -> None:
    """The first decision after the night: ONE notice, "4 need you · first:
    1:1 with Mira HH:MM"; the rows it covers never fire again."""
    from tests.fixtures.daily_week import seed

    seeded = seed(hub, monday=date.today(), engine=True)
    start = _calendar(hub, seeded["Mira"], minutes=90)
    posts: list[tuple[str, str, Any]] = []

    def notifier(title: str, body: str, *, click_url: Any = None) -> bool:
        posts.append((title, body, click_url))
        return True

    hour = datetime.now().hour
    service = _heartbeat(hub, notifier=notifier, quiet=((hour - 4) % 24, hour))
    settings = service.get_settings()
    quiet_end = datetime.now().astimezone().replace(hour=hour, minute=0, second=0, microsecond=0)
    settings["last_decision_at"] = (quiet_end - timedelta(hours=2)).isoformat()
    service._persist(settings)

    receipt = service._run_notification_decision(_owner(), service.get_settings())
    local = start.astimezone()
    first = f" · first: 1:1 with Mira {local:%H:%M}" if local.date() == datetime.now().astimezone().date() else ""
    assert [body for _, body, _ in posts] == [f"4 need you{first}"], posts
    assert posts[0][2] == "/?open=intelligence:desk"  # it opens Today (a desk address)
    assert receipt["morning"] is True and receipt["outcome"] == "sent"

    # The same morning: nothing more (the rows were told once).
    posts.clear()
    again = service._run_notification_decision(_owner(), service.get_settings())
    assert posts == [] and again["morning"] is False and again["outcome"] == "held_no_edge", again


def test_no_notice_for_the_window_in_front(hub: Hub) -> None:
    """With Needs you in front of him, no notice fires; what he saw there is
    told, so it does not fire after he leaves either."""
    from holdspeak import desk_presence
    from tests.fixtures.daily_week import seed

    seed(hub, monday=date.today(), engine=True)
    posts: list[str] = []

    def notifier(title: str, body: str, *, click_url: Any = None) -> bool:
        posts.append(body)
        return True

    service = _heartbeat(hub, notifier=notifier)
    desk_presence.report("chair:needs", True)
    receipt = service._run_notification_decision(_owner(), service.get_settings())
    assert posts == [] and receipt["outcome"] == "held_front_window", receipt
    assert receipt["frontWindow"] == "chair:needs"
    desk_presence.report("surface-meetings", True)
    after = service._run_notification_decision(_owner(), service.get_settings())
    assert posts == [] and after["outcome"] == "held_no_edge", after

    # A hidden page is not "in front": the same rows on a fresh edge fire.
    service._persist_edge(0, {}, "")
    desk_presence.report("chair:needs", False)
    hidden = service._run_notification_decision(_owner(), service.get_settings())
    assert hidden["fired"] is True and len(posts) == 1, hidden


def test_ten_minutes_before_a_one_on_one_prep_is_ready_once(hub: Hub) -> None:
    from tests.fixtures.daily_week import seed

    seeded = seed(hub, monday=date.today(), engine=True)
    start = _calendar(hub, seeded["Mira"], minutes=8)
    posts: list[tuple[str, Any]] = []

    def notifier(title: str, body: str, *, click_url: Any = None) -> bool:
        posts.append((body, click_url))
        return True

    service = _heartbeat(hub, notifier=notifier)
    receipt = service.prep_notices()
    assert posts == [(f"1:1 with Mira at {start.astimezone():%H:%M} · Prep ready",
                      f"/?open=people:{seeded['Mira']}")], posts
    assert receipt["outcome"] == "sent"
    assert service.prep_notices()["outcome"] == "held_no_edge" and len(posts) == 1


def test_no_engine_for_summaries_asks_only_when_a_meeting_waits(hub: Hub) -> None:
    """A fresh hub with no engine: nothing waits, so no row (D4 follow-up).
    A recorded meeting with words and no summary: the row asks."""
    from holdspeak.meeting_session.models import MeetingState, TranscriptSegment

    fresh = hub.client.get("/api/desk/needs-you?fresh=1").json()
    assert [b["key"] for b in fresh["blockers"]] == [] and fresh["count"] == 0, fresh["blockers"]

    start = datetime.now() - timedelta(hours=1)
    hub.db.meetings.save_meeting(MeetingState(
        id="m-waits", started_at=start, ended_at=start + timedelta(minutes=20), title="Waits",
        segments=[TranscriptSegment(text="We ship on Friday.", speaker="Me", start_time=0.0, end_time=5.0)],
        intel_status="pending"))
    waiting = hub.client.get("/api/desk/needs-you?fresh=1").json()
    assert "summary" in [b["key"] for b in waiting["blockers"]], waiting["blockers"]


def test_people_with_no_store_yet_lists_nobody_instead_of_a_503(hub: Hub) -> None:
    """The open People 503 (D6 log: code=people_store_unavailable
    readiness=unconfigured caller=GET /api/people/relationships): a desk with
    no People store yet has nobody; that is an answer, not a failure."""
    assert hub.client.get("/api/people/readiness").json()["state"] == "unconfigured"
    listed = hub.client.get("/api/people/relationships")
    assert listed.status_code == 200 and listed.json() == {"relationships": []}, listed.text
    counted = hub.client.get("/api/people/relationships?counts=1")
    assert counted.status_code == 200 and counted.json() == {"relationships": []}, counted.text


def test_people_on_a_mac_with_no_keychain_says_so(tmp_path: Path) -> None:
    """#1328 made key stores in a HOME with no keychain refuse with
    people_key_store_unavailable. The store reads ``no_key_store`` (faces
    word it "People is not set up on this Mac"); the first add says the same
    code, never a retry loop."""
    from holdspeak.people.keys import PeopleKeyError
    from holdspeak.people.store import EncryptedPeopleStore, PeopleReadiness
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.people_service import PeopleService, PeopleUnavailable

    class NoKeychain:
        def usable(self) -> bool:
            return False

        def get(self, key_id: str) -> bytes:
            raise PeopleKeyError("people_key_store_unavailable")

        def put(self, key_id: str, key: bytes) -> None:
            raise PeopleKeyError("people_key_store_unavailable")

        def delete(self, key_id: str) -> None:
            raise PeopleKeyError("people_key_store_unavailable")

    store = EncryptedPeopleStore(tmp_path / "people.v1.sqlite3", NoKeychain())
    assert store.readiness() is PeopleReadiness.NO_KEY_STORE
    service = PeopleService(store)
    owner = Principal(PrincipalKind.OWNER, "d8")
    assert service.readiness(owner)["state"] == "no_key_store"
    assert service.list_relationships(owner) == []
    with pytest.raises(PeopleUnavailable, match="people_key_store_unavailable"):
        service.create_relationship(owner, {"display_name": "Mira Okafor"})


def test_the_hub_says_people_is_not_set_up_on_this_mac(hub: Hub, tmp_path: Path) -> None:
    """The hub's answers on a Mac whose HOME has no keychain (the live store
    with its key store swapped for the refusing one #1328 made): readiness
    reads ``no_key_store``, the roster is empty, the first add says
    ``people_key_store_unavailable``. Recorded for the face
    (web/src/desk/__tests__/people.app.test.tsx, "People is not set up on
    this Mac"); HOLDSPEAK_WIRE_WRITE=1 rewrites the file."""
    from holdspeak.people.keys import PeopleKeyError
    from tests.unit.test_desk_speak import _record

    class NoKeychain:
        def usable(self) -> bool:
            return False

        def get(self, key_id: str) -> bytes:
            raise PeopleKeyError("people_key_store_unavailable")

        def put(self, key_id: str, key: bytes) -> None:
            raise PeopleKeyError("people_key_store_unavailable")

        def delete(self, key_id: str) -> None:
            raise PeopleKeyError("people_key_store_unavailable")

    people = composition.service("people_service", lambda: None)
    people._store.key_store = NoKeychain()
    readiness = hub.client.get("/api/people/readiness")
    assert readiness.status_code == 200 and readiness.json()["state"] == "no_key_store", readiness.text
    roster = hub.client.get("/api/people/relationships?counts=1")
    assert roster.status_code == 200 and roster.json() == {"relationships": []}, roster.text
    added = hub.client.post("/api/people/relationships", json={"display_name": "Mira Okafor"})
    assert added.status_code == 503 and added.json() == {"detail": "people_key_store_unavailable"}, added.text
    suggestions = hub.client.get("/api/people/suggestions")
    assert suggestions.status_code == 200, suggestions.text
    _record("people-no-key-store", {"before": {
        "/api/people/readiness": readiness.json(),
        "/api/people/relationships?counts=1": roster.json(),
        "/api/people/suggestions": suggestions.json(),
    }, "add": added.json()}, Path(hub.db.db_path).parent,
        "tests/unit/test_desk_notices.py::test_the_hub_says_people_is_not_set_up_on_this_mac",
        folder=Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__" / "fixtures" / "daily-week")
