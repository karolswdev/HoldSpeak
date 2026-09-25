"""PHILO-4-03: a failure selected into two briefs never collides.

The defect (Phase 3 closure, run ``20260924T012420Z``): breakage items had
source-only ids (``brief-break-pipeline-{event_id}``,
``brief-break-connector-{run_id}``). The lookback starts at the preceding
business close, so a Wednesday-evening failure is selected Wednesday evening
AND Thursday; the second brief re-inserted the same id against the table-wide
primary key and the hub answered 500 with
``sqlite3.IntegrityError: UNIQUE constraint failed: monday_brief_items.id``.

The fix: breakage ids are scoped to their brief. Both briefs keep their row,
the old brief keeps its triage, same-day regeneration returns the same brief
and the same ids.

The failures come from their real producers:

* pipeline: a real observed service call that fails on the hub (an Ack on an
  unknown brief item -> ``MondayBriefService.shelve`` raises LookupError ->
  ``@observe_service`` -> ``SQLiteObserver`` writes the ``pipeline_events``
  row). The observer's wall clock is pinned to Wednesday 18:00 so the event
  sits inside both lookbacks on any machine day; the write path is unchanged.
* connector: ``db.activity.record_connector_run`` -- the one writer every
  connector path calls on completion (``holdspeak/db/activity/enrichment.py``).
"""
from __future__ import annotations

import datetime
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
import holdspeak.services.observer as observer_module
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.sqlite_observer import SQLiteObserver
from holdspeak.web.context import WebContext
from holdspeak.web.routes import monday_brief as brief_routes

# A Wednesday evening: day two (Thursday) looks back to Wednesday 17:00, so a
# failure at 18:00 Wednesday is selected into both briefs.
DAY_ONE = datetime.datetime(2026, 9, 23, 18, 30)
FAILED_AT = datetime.datetime(2026, 9, 23, 18, 0)


class MovableClock:
    def __init__(self, start: datetime.datetime) -> None:
        self.now = start

    def __call__(self) -> datetime.datetime:
        return self.now

    def advance(self, **delta: int) -> None:
        self.now = self.now + datetime.timedelta(**delta)


def _hub(db: Database, monkeypatch, tmp_path, clock) -> TestClient:
    """The brief routes as the hub mounts them, with the REAL SQLite observer."""
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr(brief_routes, "get_database", lambda: db)
    monkeypatch.setattr(
        brief_routes, "get_observer", lambda: SQLiteObserver(db._connection)
    )
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people.key"))
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "test-owner")
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, brief_clock=clock)
    app.include_router(brief_routes.build_monday_brief_router(ctx))
    # Pre-fix the IntegrityError surfaces verbatim in the test output.
    return TestClient(app, raise_server_exceptions=True)


def _broke(body: dict) -> list[dict]:
    return list(body["sections"]["broke"])


def _stored_broke(db: Database, brief_id: str) -> list[tuple[str, str, str]]:
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT id, text, source_ref FROM monday_brief_items
               WHERE brief_id = ? AND section = 'broke' ORDER BY id""",
            (brief_id,),
        ).fetchall()
    return [(str(r["id"]), str(r["text"]), str(r["source_ref"])) for r in rows]


def _two_days(client: TestClient, clock: MovableClock, db: Database, source_ref: str):
    """Day one, Ack, same-day regenerate, advance a day, day two. Returns both bodies."""
    first = client.post("/api/brief/generate")
    assert first.status_code == 200, first.text
    day_one = first.json()
    rows = [item for item in _broke(day_one) if item["source_ref"] == source_ref]
    assert len(rows) == 1, _broke(day_one)
    day_one_item = rows[0]["id"]

    # (3) the owner triages the day-one row through the service.
    acked = client.post(
        f"/api/brief/items/{day_one_item}/shelf", json={"state": "acknowledged"}
    )
    assert acked.status_code == 200, acked.text

    # (4) same-day regeneration: the same brief, the same item ids.
    again = client.post("/api/brief/generate")
    assert again.status_code == 200, again.text
    assert again.json()["id"] == day_one["id"]
    assert [i["id"] for i in _broke(again.json())] == [i["id"] for i in _broke(day_one)]

    # (1) the next producer-day selects the same failure again.
    clock.advance(days=1)
    second = client.post("/api/brief/generate")
    assert second.status_code == 200, second.text
    day_two = second.json()
    assert day_two["id"] != day_one["id"]
    assert day_two["period_end"].startswith("2026-09-24")

    # (2) BOTH briefs read back with their breakage row for the same failure.
    one = [r for r in _stored_broke(db, day_one["id"]) if r[2] == source_ref]
    two = [r for r in _stored_broke(db, day_two["id"]) if r[2] == source_ref]
    assert len(one) == 1 and len(two) == 1, (one, two)
    assert one[0][0] == day_one_item
    assert two[0][0] != day_one_item
    assert one[0][1] == two[0][1], "the cause text is kept"
    assert day_one["id"] in day_one_item and day_two["id"] in two[0][0]

    # (3) day one's triage is preserved; day two's row starts untouched.
    from holdspeak.services.monday_brief_service import MondayBriefService

    service = MondayBriefService(db)
    assert service.shelf(None, day_one["id"]) == {day_one_item: "acknowledged"}
    assert service.shelf(None, day_two["id"]) == {}
    return day_one, day_two


def test_a_pipeline_failure_in_two_lookbacks_generates_both_briefs(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    clock = MovableClock(DAY_ONE)
    client = _hub(db, monkeypatch, tmp_path, clock)

    # The REAL producer: a failing observed service call on the hub.
    monkeypatch.setattr(
        observer_module, "time", SimpleNamespace(time=lambda: FAILED_AT.timestamp())
    )
    failed = client.post(
        "/api/brief/items/brief-item-missing/shelf", json={"state": "acknowledged"}
    )
    assert failed.status_code == 404
    with db._connection() as conn:
        events = conn.execute(
            "SELECT event_id, service, method, error FROM pipeline_events"
            " WHERE error IS NOT NULL"
        ).fetchall()
    assert len(events) == 1
    assert (events[0]["service"], events[0]["method"]) == ("MondayBriefService", "shelve")
    source_ref = f"pipeline-event:{events[0]['event_id']}"

    day_one, day_two = _two_days(client, clock, db, source_ref)
    row = [i for i in _broke(day_two) if i["source_ref"] == source_ref][0]
    assert row["text"] == "Brief triage did not save"
    assert "Unknown brief item" in row["detail"]


def test_a_connector_failure_in_two_lookbacks_generates_both_briefs(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    clock = MovableClock(DAY_ONE)
    client = _hub(db, monkeypatch, tmp_path, clock)

    run = db.activity.record_connector_run(
        connector_id="github",
        started_at=FAILED_AT,
        finished_at=FAILED_AT + datetime.timedelta(minutes=1),
        succeeded=False,
        error="token expired",
    )
    source_ref = f"connector-run:{run.id}"

    day_one, day_two = _two_days(client, clock, db, source_ref)
    row = [i for i in _broke(day_two) if i["source_ref"] == source_ref][0]
    assert row["text"] == "Connector github failed"
    assert row["detail"] == "token expired"
