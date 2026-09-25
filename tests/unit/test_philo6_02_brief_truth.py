"""PHILO-6-02 — the brief's truth: the producer link of the fences.

One brief from the REAL producer, served by the REAL brief routes:

* the hub's producer clock is in ``Etc/GMT+11`` (a timestamp with its own
  -11:00 offset), so the rendered link can run the browser in another zone;
* a real summary run call through ``MeetingIntelService`` and the REAL
  ``@observe_service`` + ``SQLiteObserver`` (no engine is assigned, so the
  run is refused: one change receipt and one failure receipt);
* a real failing observed call (an Ack on an unknown item ->
  ``MondayBriefService.shelve``), the PHILO-4-03 breakage producer;
* a THIS WEEK item (a calendar event later this week);
* one shelved row (an Ack through the route after generation).

The latest-brief payload is written to the vitest fixture
(``web/src/desk/chair/__tests__/fixtures/philo6/brief-truth.json``) BEFORE the
wording asserts, with ``PHILO6_WRITE_FIXTURE=1``; otherwise a drift between
the producer and the fixture fails here. The wording asserts are the (c)
fence: no stored item carries ``Service.method`` text; a summary run call is
worded as a request.
"""
from __future__ import annotations

import datetime
import json
import os
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
import holdspeak.services.observer as observer_module
from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.services.meeting_route_projection import project_route
from holdspeak.services.sqlite_observer import SQLiteObserver
from holdspeak.web.context import WebContext
from holdspeak.web.routes import monday_brief as brief_routes

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "web/src/desk/chair/__tests__/fixtures/philo6/brief-truth.json"
HUB_ZONE = ZoneInfo("Etc/GMT+11")  # UTC-11
# A Friday morning in the hub's zone; the lookback starts Thursday 17:00.
GENERATED = datetime.datetime(2026, 9, 25, 7, 19, tzinfo=HUB_ZONE)
EVENTS_AT = datetime.datetime(2026, 9, 25, 6, 0, tzinfo=HUB_ZONE)
MEETING_TITLE = "Architecture review"
OWNER = Principal(PrincipalKind.OWNER, "test-owner")
RAW = re.compile(r"[A-Z][A-Za-z]*(?:Service|Manager|Handler|Provider)\.[a-z_]+")


def _hub(db: Database, monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr(brief_routes, "get_database", lambda: db)
    monkeypatch.setattr(
        brief_routes, "get_observer", lambda: SQLiteObserver(db._connection)
    )
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people.key"))
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, brief_clock=lambda: GENERATED)
    app.include_router(brief_routes.build_monday_brief_router(ctx))
    return TestClient(app, raise_server_exceptions=True)


def _seed(db: Database, client: TestClient, monkeypatch) -> str:
    # Distinct receipt times keep the producer's row order stable.
    now = {"t": EVENTS_AT.timestamp()}
    monkeypatch.setattr(observer_module, "time", SimpleNamespace(time=lambda: now["t"]))
    meeting = MeetingState(
        id="m-arch",
        started_at=datetime.datetime(2026, 9, 25, 5, 0),
        ended_at=datetime.datetime(2026, 9, 25, 5, 30),
        title=MEETING_TITLE,
        tags=[],
        segments=[
            TranscriptSegment(
                text="we keep retrieval local", speaker="Me", start_time=0.0, end_time=4.0
            )
        ],
    )
    db.meetings.save_meeting(meeting)
    # The real summary run call, observed by the real observer. No engine is
    # assigned, so the hub refuses it: a change receipt and a failure receipt.
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    intel = MeetingIntelService(db, observer=SQLiteObserver(db._connection))
    try:
        intel.run_intelligence(
            OWNER, meeting.id, expected_selection_hash=route["selection_hash"]
        )
    except Exception:  # noqa: BLE001 - the refusal is the recorded producer fact.
        pass
    # The PHILO-4-03 breakage producer: an Ack on an unknown item.
    now["t"] += 300
    failed = client.post(
        "/api/brief/items/brief-item-missing/shelf", json={"state": "acknowledged"}
    )
    assert failed.status_code == 404
    # THIS WEEK: one calendar event on Saturday (stored UTC, as ingest does).
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO calendar_events
               (id, uid, title, starts_at, ends_at, last_seen_at,
                subscription_revision, source_id, source_label)
               VALUES ('evt-sat', 'uid-sat', 'Design review',
                       '2026-09-26T21:00:00Z', '2026-09-26T22:00:00Z', 0,
                       'rev', 'src1', 'WORK')"""
        )
    return meeting.id


def _stable(payload: dict[str, Any]) -> dict[str, Any]:
    """Stable stand-ins for the random ids, in order of first appearance.

    The producer reads items back ``ORDER BY priority DESC, id ASC`` and the
    breakage ids carry a random event id, so rows of equal priority come
    back in a random order; they are ordered by text here."""
    payload = dict(payload)
    payload["sections"] = {
        name: sorted(rows, key=lambda row: (-int(row.get("priority") or 0), row["text"]))
        for name, rows in payload["sections"].items()
    }
    text = json.dumps(payload, sort_keys=True)
    token = re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-f]{32}"
    )
    names: dict[str, str] = {}
    for value in token.findall(text):
        names.setdefault(value, f"philo6-{len(names):02d}")
    return json.loads(token.sub(lambda m: names[m.group(0)], text))


def test_the_real_producer_brief(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    client = _hub(db, monkeypatch, tmp_path)
    _seed(db, client, monkeypatch)

    first = client.post("/api/brief/generate")
    assert first.status_code == 200, first.text
    body = first.json()
    changed = [i["text"] for i in body["sections"]["changed"]]
    broke = [i["text"] for i in body["sections"]["broke"]]
    assert body["sections"]["this_week"], body["sections"]
    # One shelved row: Ack the brief-triage failure through the route.
    triage = [
        i for i in body["sections"]["broke"]
        if "Unknown brief item" in str(i.get("detail") or "")
    ]
    assert len(triage) == 1, broke
    acked = client.post(
        f"/api/brief/items/{triage[0]['id']}/shelf", json={"state": "acknowledged"}
    )
    assert acked.status_code == 200, acked.text
    latest = client.get("/api/brief/latest")
    assert latest.status_code == 200
    payload = _stable(latest.json())
    # The hub's own label is in the hub's offset (07:19), the stamp is not.
    assert payload["generated_label"] == "GENERATED SEP 25 07:19"
    assert payload["generated_at"].endswith("-11:00")

    if os.environ.get("PHILO6_WRITE_FIXTURE") == "1":
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    recorded = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert recorded == payload, (
        "the vitest fixture drifted from the real producer; "
        "re-run with PHILO6_WRITE_FIXTURE=1"
    )

    # (c) no stored item carries Service.method text.
    with db._connection() as conn:
        stored = [str(r["text"]) for r in conn.execute("SELECT text FROM monday_brief_items")]
    assert stored, "the producer stored no items"
    assert [t for t in stored if RAW.search(t)] == [], stored
    # A summary run call is a REQUEST, never a completion; the refusal is
    # worded `<what> did not <verb>`, and both name the meeting.
    assert f"Summary requested: {MEETING_TITLE}" in changed, changed
    assert f"Summary did not start: {MEETING_TITLE}" in broke, broke
    assert "Brief triage did not save" in broke, broke


def test_generic_fallback_has_no_raw_names(tmp_path):
    """Every observed call outside the word table still reads as words."""
    from holdspeak.services.monday_brief_service import MondayBriefService

    db = Database(tmp_path / "hub.db")
    service = MondayBriefService(db)
    with db._connection() as conn:
        change = service._operation_text(conn, "NoteService", "create_note", "{}", broke=False)
        broke = service._operation_text(conn, "SyncService", "push", "{}", broke=True)
    assert change == "Note: create note"
    assert broke == "Sync: push did not complete"
    assert not RAW.search(change) and not RAW.search(broke)
