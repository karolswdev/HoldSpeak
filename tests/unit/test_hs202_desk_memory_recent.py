"""HS-202-02 job 4 — Desk memory shows the desk's memory.

03-interaction-walk.md finding 7: "Desk memory shows nothing on a desk that
has memory. The window's body is empty while the same desk holds a meeting,
two decision records and a generated brief — all of them visible on the
Floor behind the window."

Traced: the face is query-first and has no zero-query read at all. Its only
endpoint call requires a non-empty query
(`holdspeak/services/recall_service.py:135-137` raises
`query is required`), so a cold open asks the hub for nothing and renders
a blank field under the filter chips.

The source fix is a RECENT read: `GET /api/memory/recall?recent=1` with no
query answers the desk's most recent memory. The blank-query refusal is
UNCHANGED — `tests/unit/test_phase200_continuity.py:653` still pins the 400
for a bare `query=""`, because a search with no words is still a search
with no words.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "the-owner")


def _db(tmp_path: Path) -> Database:
    return Database(tmp_path / "hs202-recent.db")


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.services.memory_service import MemoryService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.memory import build_memory_router

    reset_database()
    db = _db(tmp_path)
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()

    @app.middleware("http")
    async def _principal(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(
        build_memory_router(
            WebContext(get_state=lambda: {}, memory_service=MemoryService(db))
        )
    )
    yield db, TestClient(app)
    reset_database()


def _seed(db) -> None:
    from holdspeak.services.decision_record_service import DecisionRecordService

    records = DecisionRecordService(db)
    records.create(
        OWNER,
        decision_text="Freeze window is Saturday 02:00",
        source_type="desk",
        source_id="desk-seed-1",
    )
    records.create(
        OWNER,
        decision_text="Ship the reader behind a flag",
        source_type="desk",
        source_id="desk-seed-2",
    )
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO monday_briefs
               (id, headline, generated_at, period_start, period_end)
               VALUES (?, ?, ?, ?, ?)""",
            (
                "brief-seed",
                "The week ahead",
                "2026-09-20T08:00:00",
                "2026-09-14",
                "2026-09-20",
            ),
        )
        conn.execute(
            """INSERT INTO monday_brief_items
               (id, brief_id, section, text, detail, source_ref, priority)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                "brief-item-seed",
                "brief-seed",
                "THIS WEEK",
                "Close the reader flag",
                "Two reviews outstanding",
                "",
                3,
            ),
        )


def test_the_recent_read_answers_a_desk_that_has_memory(client) -> None:
    db, http = client
    _seed(db)

    body = http.get("/api/memory/recall", params={"recent": "1"}).json()

    assert body["recent"] is True
    assert body["query"] == ""
    assert body["remembered"] > 0, body
    texts = [card["text"] for card in body["current"]]
    assert "Freeze window is Saturday 02:00" in texts
    assert "Ship the reader behind a flag" in texts
    assert [item["title"] for item in body["briefs"]] == ["Close the reader flag"]


def test_the_recent_read_honours_the_filter(client) -> None:
    db, http = client
    _seed(db)

    briefs = http.get(
        "/api/memory/recall", params={"recent": "1", "filter": "briefs"}
    ).json()
    assert [item["title"] for item in briefs["briefs"]] == ["Close the reader flag"]
    assert briefs["current"] == []

    decisions = http.get(
        "/api/memory/recall", params={"recent": "1", "filter": "decisions"}
    ).json()
    assert len(decisions["current"]) == 2
    assert decisions["briefs"] == []

    assert (
        http.get(
            "/api/memory/recall", params={"recent": "1", "filter": "nope"}
        ).status_code
        == 400
    )


def test_a_blank_query_is_still_refused(client) -> None:
    """The recent read is an EXPLICIT intent, never a silent fallback."""
    db, http = client
    _seed(db)
    assert http.get("/api/memory/recall", params={"query": ""}).status_code == 400
    assert (
        http.get("/api/memory/recall", params={"query": "", "recent": "0"}).status_code
        == 400
    )


def test_the_recent_read_states_an_empty_desk_honestly(client) -> None:
    _db_, http = client
    body = http.get("/api/memory/recall", params={"recent": "1"}).json()
    assert body["recent"] is True
    assert body["remembered"] == 0
    assert body["searched_at"]
