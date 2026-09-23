"""PHILO-3-03 (A3): the brief producer's day moves under test, never the machine clock.

The defect: ``MondayBriefService.generate`` read ``datetime.datetime.now()``
directly (holdspeak/services/monday_brief_service.py compute_window) and the
route passed no ``now``, so a same-day Generate returned the existing brief
and the NEXT producer-day could not be reached by any case: recording a
decision after an empty brief proved nothing about inclusion (COUNCIL.md A3,
Astra's finding). The seam is ONE injectable clock: ``MondayBriefService(clock=)``,
defaulting to the real wall clock, wired from the app factory through
``MeetingWebServer(brief_clock=)`` -> ``WebContext.brief_clock`` -> the brief
router. Production never passes it.
"""
from __future__ import annotations

import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.monday_brief_service import MondayBriefService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_decisions_router, build_primitives_router
from holdspeak.web.routes import monday_brief as brief_routes

TITLE = "Adopt the one desk bus"
ITEM = f"Review decision: {TITLE}"
# A Wednesday, so the window rule is the plain "yesterday 17:00" one.
DAY_ONE = datetime.datetime(2026, 9, 23, 9, 30)


class MovableClock:
    """The test's producer clock: a fixed instant the test moves by hand."""

    def __init__(self, start: datetime.datetime) -> None:
        self.now = start

    def __call__(self) -> datetime.datetime:
        return self.now

    def advance(self, **delta: int) -> None:
        self.now = self.now + datetime.timedelta(**delta)


def _texts(brief) -> list[str]:
    return [item.text for items in brief.sections.values() for item in items]


def test_the_producer_clock_moves_the_brief_day_and_keeps_the_same_day_id(tmp_path):
    db = Database(tmp_path / "brief.db")
    clock = MovableClock(DAY_ONE)
    service = MondayBriefService(db, clock=clock)

    empty = service.generate(None)
    assert empty.is_empty and ITEM not in _texts(empty)
    assert empty.period_end.startswith("2026-09-23")

    db.desk_decisions.upsert(decision_id="decision-a3", title=TITLE, status="proposed")

    same_day = service.generate(None)
    assert same_day.id == empty.id, "same producer-day: generate returns the existing brief"
    assert ITEM not in _texts(same_day)

    clock.advance(days=1)
    next_day = service.generate(None)
    assert next_day.id != empty.id, "a new producer-day mints a new brief"
    assert next_day.period_end.startswith("2026-09-24")
    assert ITEM in _texts(next_day)
    assert service.get_latest(None).id == next_day.id


def test_the_default_clock_is_the_wall_clock(tmp_path):
    service = MondayBriefService(Database(tmp_path / "brief.db"))
    before = datetime.datetime.now()
    brief = service.generate(None)
    after = datetime.datetime.now()
    generated = datetime.datetime.fromisoformat(brief.generated_at)
    assert before <= generated <= after


def _hub_app(db: Database, monkeypatch, tmp_path, clock) -> TestClient:
    """The routes the hub mounts, with the clock wired the way the app factory wires it."""
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr(brief_routes, "get_database", lambda: db)
    monkeypatch.setattr(brief_routes, "get_observer", lambda: None)
    # never the owner's keychain: the People overlay reads a file key store
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people.key"))
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "test-owner")
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, brief_clock=clock)
    app.include_router(build_decisions_router(None))
    app.include_router(build_primitives_router(ctx))
    app.include_router(brief_routes.build_monday_brief_router(ctx))
    return TestClient(app, raise_server_exceptions=False)


def test_the_route_reads_the_wired_clock_across_a_producer_day(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    clock = MovableClock(DAY_ONE)
    client = _hub_app(db, monkeypatch, tmp_path, clock)

    first = client.post("/api/brief/generate")
    assert first.status_code == 200, first.text
    first_id = first.json()["id"]
    assert first.json()["generated_label"] == "GENERATED SEP 23 09:30"

    created = client.post("/api/decisions", json={"title": TITLE, "status": "proposed"})
    assert created.status_code == 201, created.text

    again = client.post("/api/brief/generate")
    assert again.json()["id"] == first_id
    assert ITEM not in again.text

    clock.advance(days=1)
    next_day = client.post("/api/brief/generate")
    assert next_day.status_code == 200, next_day.text
    body = next_day.json()
    assert body["id"] != first_id
    assert ITEM in [item["text"] for item in body["sections"]["decisions"]]
    assert body["generated_label"] == "GENERATED SEP 24 09:30"

    latest = client.get("/api/brief/latest").json()
    assert latest["id"] == body["id"]
    assert latest["period_label"] == "SEP 21 – 24"


def test_the_web_server_carries_the_clock_to_the_context():
    """The app factory's one wire: MeetingWebServer(brief_clock=) -> WebContext."""
    import inspect

    from holdspeak.web_server import MeetingWebServer

    assert "brief_clock" in inspect.signature(MeetingWebServer.__init__).parameters
    source = inspect.getsource(MeetingWebServer._create_app)
    assert "brief_clock=self._brief_clock" in source
