"""PHILO-15 04 (gap 14): ``GET /api/desk/parked`` composes the per-kind parked reads.

One read for the Parked drawer: parked meetings, parked Workbench items and
archived Projects, from the existing services (no new table). A kind whose
read fails is named in ``not_read``; the other kinds still answer. The edge
gate admits the owner only.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind, PrincipalRight, required_right
from holdspeak.services.meeting_service import MeetingService
from holdspeak.services.parked_service import parked_collection
from holdspeak.services.project_service import ProjectService
from holdspeak.services.workbench_service import WorkbenchService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.desk_parked import build_desk_parked_router

OWNER = Principal(PrincipalKind.OWNER, "philo15-owner")


def _seed(db: Database) -> None:
    for mid, title, parked in (("m-live", "Live sync", False), ("m-park", "Vendor call", True)):
        db.meetings.save_meeting(MeetingState(id=mid, started_at=datetime(2026, 10, 6, 10), title=title))
        if parked:
            assert db.meetings.delete_meeting(mid) is True
    bench = db.workbenches.upsert(workbench_id="wb-1", name="Ops")
    for iid, parked in (("wbi-live", False), ("wbi-park", True)):
        db.workbench_items.upsert(item_id=iid, workbench_id=bench.id, title=f"Item {iid}", status="pending")
    db.workbench_items._transition_parked(bench.id, ["wbi-park"], parked=True)
    db.projects.create_project(project_id="p-live", name="Live project")
    db.projects.create_project(project_id="p-old", name="Old migration")
    db.projects.update_project("p-old", is_archived=True)


def _services(db: Database) -> dict[str, Any]:
    return {"meeting_service": MeetingService(db), "workbench_service": WorkbenchService(db),
            "project_service": ProjectService(db)}


def test_every_parked_object_across_kinds_and_nothing_live(tmp_path: Path) -> None:
    db = Database(tmp_path / "h.db")
    _seed(db)
    answer = parked_collection(OWNER, **_services(db))
    assert answer["not_read"] == []
    by_ref = {row["ref"]: row for row in answer["items"]}
    assert set(by_ref) == {"meeting:m-park", "workbench_item:wbi-park", "project:p-old"}
    assert by_ref["meeting:m-park"]["name"] == "Vendor call"
    assert by_ref["workbench_item:wbi-park"]["home"] == {"workbench_id": "wb-1", "workbench_name": "Ops"}
    assert by_ref["project:p-old"]["kind"] == "project"


def test_a_failed_kind_is_named_and_the_others_still_answer(tmp_path: Path) -> None:
    db = Database(tmp_path / "h.db")
    _seed(db)

    class Broken:
        def list_workbenches(self, principal: Any) -> Any:
            raise RuntimeError("down")

    services = {**_services(db), "workbench_service": Broken()}
    answer = parked_collection(OWNER, **services)
    assert answer["not_read"] == ["workbench_item"]
    assert {row["kind"] for row in answer["items"]} == {"meeting", "project"}


def test_the_route_answers_the_owner_and_the_edge_admits_only_the_owner(tmp_path: Path) -> None:
    db = Database(tmp_path / "h.db")
    _seed(db)
    app = FastAPI()

    @app.middleware("http")
    async def owner(request: Request, call_next):  # noqa: ANN001
        request.state.principal = OWNER
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, **_services(db))
    app.include_router(build_desk_parked_router(ctx))
    body = TestClient(app).get("/api/desk/parked").json()
    assert sorted(row["ref"] for row in body["items"]) == [
        "meeting:m-park", "project:p-old", "workbench_item:wbi-park"]
    assert required_right("GET", "/api/desk/parked") is PrincipalRight.OWNER


def test_restore_from_the_drawer_takes_the_object_out_of_parked(tmp_path: Path) -> None:
    db = Database(tmp_path / "h.db")
    _seed(db)
    services = _services(db)
    services["meeting_service"].restore_meeting(OWNER, "m-park")
    refs = {row["ref"] for row in parked_collection(OWNER, **services)["items"]}
    assert "meeting:m-park" not in refs and "project:p-old" in refs


# ── Astra r1 on #974: every page, a partial read named, the real auth ──


def _park_many(db: Database, n: int) -> None:
    for i in range(n):
        db.meetings.save_meeting(MeetingState(id=f"m-{i:04d}", started_at=datetime(2026, 9, 1, 9), title=f"Old {i}"))
    with db._connection() as conn:
        conn.execute("UPDATE meetings SET parked = 1 WHERE id LIKE 'm-0%'")


def test_501_parked_meetings_are_all_read_through_the_hub(tmp_path: Path, monkeypatch) -> None:
    """One page is 500: the 501st parked meeting is in the drawer, nothing NOT READ."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_philo5_the_loop import _boot

    hub = _boot(tmp_path, monkeypatch)
    _park_many(hub.db, 501)
    body = hub.client.get("/api/desk/parked").json()
    meetings = [row for row in body["items"] if row["kind"] == "meeting"]
    assert len(meetings) == 501 and len({row["id"] for row in meetings}) == 501
    assert body["not_read"] == [] and body["partial"] == []


def test_a_page_that_fails_mid_way_is_partial_never_silently_short(tmp_path: Path) -> None:
    db = Database(tmp_path / "h.db")
    _park_many(db, 501)
    services = _services(db)
    real = services["meeting_service"].list_meetings
    calls: list[Any] = []

    def second_page_fails(principal: Any, **kw: Any) -> Any:
        calls.append(kw.get("cursor"))
        if len(calls) == 2:
            raise RuntimeError("database is locked")
        return real(principal, **kw)

    services["meeting_service"].list_meetings = second_page_fails
    answer = parked_collection(OWNER, **services)
    assert answer["not_read"] == ["meeting"] and answer["partial"] == ["meeting"]
    assert len([r for r in answer["items"] if r["kind"] == "meeting"]) == 500
    assert calls == [None, "500"]


def test_the_real_edge_refuses_anonymous_and_an_agent(tmp_path: Path, monkeypatch) -> None:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_conductor_k6_agent_mcp import _client, _launch_credential
    from test_philo5_the_loop import _boot

    hub = _boot(tmp_path, monkeypatch)
    assert hub.client.get("/api/desk/parked").status_code == 200
    assert _client(hub, None).get("/api/desk/parked").status_code == 401
    from holdspeak.principals import agent_credentials

    cred = _launch_credential("launch_p15parked01")
    try:
        assert _client(hub, cred.token).get("/api/desk/parked").status_code == 403
    finally:
        agent_credentials.revoke(cred.principal.identity)
