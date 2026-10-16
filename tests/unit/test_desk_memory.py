"""Desk memory: the hub half, through the real hub's routes.

The test diet (2026-10-11) moves the hub facts of two browser files here,
with each file's own seed (copied: the e2e modules import Playwright):

* tests/e2e/test_hs526_desk_memory_glass.py — the unscoped Desk memory read:
  a transcript hit recalls its parent Meeting, and the durable
  ``meeting_artifact`` edge brings the Artifact beside it; a query with
  nothing behind it answers nothing.
* tests/e2e/test_memory_faces_glass.py — beliefs and standing pages made
  through the real sweep, extract, consolidate and page paths (the slice 4
  and slice 5 fixture engines): the ``cutover`` beliefs, the Atlas pages with
  ONE stale page, the desk's pages, and the deletes that take a source away.

The face halves are vitest: web/src/desk/__tests__/memory.app.test.tsx, plus
the existing fences it cites.  The project-scoped edge fence stays in
tests/unit/test_relationship_aware_memory.py; the route fences on another
seed stay in tests/unit/test_memory_faces_routes.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _recall(hub: Hub, query: str) -> dict[str, Any]:
    resp = hub.client.get("/api/memory/recall", params={"query": query, "filter": "all"})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _pages(hub: Hub, **params: str) -> list[dict[str, Any]]:
    resp = hub.client.get("/api/memory/pages", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()["pages"]


# ── HS-526: the unscoped Desk memory read ───────────────────────────────


def _seed_hs526() -> None:
    """The e2e's seed: the product's own seams (notes, the capture path's
    meeting and segment rows, the plugin artifact and its meeting edge)."""
    from holdspeak.db import get_database

    db = get_database()
    db.notes.upsert(
        note_id="hs526-n1", title="Zephyr rollout note",
        body_markdown="Zephyr rollout owners, gates, and the cut-over window.",
        last_modified="2026-02-03T09:00:00", created_at="2026-02-03T09:00:00",
    )
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings(id,started_at,ended_at,title,"
            " duration_seconds,intel_status,capture_status,provenance)"
            " VALUES ('hs526-m1','2026-02-01T09:00:00','2026-02-01T09:30:00',"
            "         'Launch review',1800.0,'disabled','finalized','desktop')"
        )
        conn.execute("DELETE FROM segments WHERE meeting_id='hs526-m1'")
        conn.execute(
            "INSERT INTO segments(meeting_id,text,speaker,start_time,end_time)"
            " VALUES ('hs526-m1','The zephyr rollout starts Friday','Ada',0,4)"
        )
    db.plugins.record_artifact(
        artifact_id="hs526-a1", meeting_id="hs526-m1", artifact_type="memo",
        title="Rollout checklist", body_markdown="Owners and gates", updated_at="2026-02-02T09:00:00",
    )


def test_a_transcript_hit_recalls_its_meeting_and_the_artifact_over_the_edge(hub: Hub) -> None:
    """replaces: tests/e2e/test_hs526_desk_memory_glass.py::test_desk_memory_results (hub half)"""
    _seed_hs526()
    body = _recall(hub, "zephyr")
    # The parent Meeting, not the isolated segment; the word is marked.
    [meeting] = body["meetings"]
    assert (meeting["source_ref"], meeting["title"]) == ("meeting:hs526-m1", "Launch review"), meeting
    assert "<mark>zephyr</mark>" in meeting["snippet"].lower(), meeting
    # The Artifact never holds the word: it arrives over the durable edge.
    artifact = next(h for h in body["also"] if h["source_ref"] == "artifact:hs526-a1")
    assert artifact["title"] == "Rollout checklist"
    assert (artifact["retrieval_origin"], artifact["related_to"], artifact["relationship"]) == (
        "relationship", "meeting:hs526-m1", "meeting_artifact"), artifact
    assert body["remembered"] >= 2


def test_a_query_with_nothing_behind_it_answers_nothing(hub: Hub) -> None:
    """replaces: tests/e2e/test_hs526_desk_memory_glass.py::test_desk_memory_empty (hub half)"""
    _seed_hs526()
    body = _recall(hub, "unfindablequasar")
    assert body["remembered"] == 0, body
    for key in ("current", "superseded", "disputed", "owed", "meetings", "briefs", "also", "beliefs"):
        assert body[key] == [], (key, body[key])


# ── Memory on the Desk: beliefs and standing pages ───────────────────────


def _seed_memory_faces() -> None:
    """The e2e's seed: beliefs and pages through the real paths, in the hub's own database."""
    from holdspeak.db import get_database
    from holdspeak.memory.pages import spec_for, write_page, write_pending
    from holdspeak.memory.retain import sweep
    from tests.unit.test_memory_slice4_observations import (
        Rules,
        _filed_note,
        _learn,
        _meeting,
    )
    from tests.unit.test_memory_slice5_pages import Pages

    db = get_database()
    db.projects.create_project(project_id="atlas", name="Atlas cutover")
    _meeting(db, "m-0924", "Cutover date is 10-10. Cutover rollback owner is Marek.", day=24)
    _learn(db)
    _filed_note(db, "n-1001", "Cutover date is 10-17.", "atlas")
    _learn(db)  # supersedes the 10-10 belief
    _meeting(db, "m-0929", "Cutover rollback owner is Priya.", day=29)
    _learn(db, Rules("contradicts"))
    _filed_note(db, "n-desk-1", "Hiring loop reply is owed.", None)
    _filed_note(db, "n-desk-2", "Billing contract is waiting.", None)
    _learn(db)
    write_pending(db, Pages())
    # One new Atlas source after the pages were built: every Atlas page is
    # stale; three are written again, so ONE stays stale.
    with db._connection() as conn:
        conn.execute("UPDATE memory_sources SET updated_at='2026-01-01T00:00:00+00:00'")
        conn.execute("UPDATE memory_pages SET last_memory_seen_at='2026-01-01T00:00:00+00:00'")
    _filed_note(db, "n-1003", "Cutover freeze is 10-12.", "atlas")
    sweep(db)
    for slug in ("what-we-decided", "what-is-open", "risks-and-disputes"):
        write_page(db, Pages(), ("project", "atlas"), spec_for("project", slug))


def _belief_texts(hub: Hub) -> list[str]:
    return [b["text"] for b in _recall(hub, "cutover")["beliefs"]]


def test_the_cutover_beliefs_are_current_disputed_and_superseded(hub: Hub) -> None:
    """replaces: tests/e2e/test_memory_faces_glass.py::test_memory_on_the_desk (hub half: beliefs)"""
    _seed_memory_faces()
    beliefs = _recall(hub, "cutover")["beliefs"]
    assert [b["state"] for b in beliefs] == ["current", "disputed", "disputed", "superseded"], beliefs
    current = beliefs[0]
    # The old text unfolds under the current belief (the face strikes it through).
    assert [h["text"] for h in current["history"]] == ["Cutover date is 10-10."], current["history"]
    # One disputed belief's ref is the contradicting meeting: AGAINST · MTG 09-29 · 10:00.
    against = [(e["token"], e["against"]) for b in beliefs if b["state"] == "disputed" for e in b["evidence"]]
    assert ("MTG 09-29 · 10:00", True) in against, against
    assert [bool(b["since"]) for b in beliefs if b["state"] == "superseded"] == [True]


def test_the_atlas_pages_hold_one_stale_page_and_the_desk_its_own(hub: Hub) -> None:
    """replaces: tests/e2e/test_memory_faces_glass.py::test_memory_on_the_desk (hub half: pages)"""
    _seed_memory_faces()
    atlas = _pages(hub, project_id="atlas")
    assert [p["slug"] for p in atlas] == ["what-we-decided", "what-is-open", "risks-and-disputes",
                                          "what-changed-this-week"], atlas
    stale = [(p["slug"], p["new_sources"]) for p in atlas if p["stale"]]
    assert stale == [("what-changed-this-week", 1)], stale  # the face: STALE · 1 NEW SOURCE
    assert "Harbor" not in json.dumps(atlas)
    desk = _pages(hub, scope="desk")
    assert [p["slug"] for p in desk] in (["what-i-owe", "what-changed-this-week"], ["what-changed-this-week"]), desk
    text = json.dumps(desk)
    assert "Atlas" not in text and "Cutover" not in text


def test_a_deleted_source_leaves_the_beliefs_and_the_pages(hub: Hub) -> None:
    """replaces: tests/e2e/test_memory_faces_glass.py::test_memory_on_the_desk (hub half: the deletes)"""
    _seed_memory_faces()
    assert "Cutover date is 10-17." in json.dumps(_pages(hub, project_id="atlas"))
    gone = hub.client.delete("/api/notes/n-1001")
    assert gone.status_code in (200, 204), gone.text
    # The Room's re-read after the bus frame: the note's sentence is not served.
    assert "Cutover date is 10-17." not in json.dumps(_pages(hub, project_id="atlas"))
    # Desk memory on `cutover` once n-1001 is gone: Marek stands, 10-17 does not.
    texts = _belief_texts(hub)
    assert "Cutover rollback owner is Marek." in texts and "Cutover date is 10-17." not in texts, texts
    # The meeting two beliefs rest on is deleted: both leave.
    gone = hub.client.delete("/api/meetings/m-0924")
    assert gone.status_code in (200, 204), gone.text
    texts = _belief_texts(hub)
    assert "Cutover rollback owner is Marek." not in texts and "Cutover date is 10-10." not in texts, texts


# ── HS-200-13: recall of a superseded decision chain, and the chain across a restart ──
#
# The seed of tests/e2e/test_hs200_continuity_glass.py (`_seed_chain`), copied:
# two meetings linked to a Room, three proposals confirmed through the real
# route, Saturday's decision superseded by Sunday's. The answers the Desk
# memory face reads are recorded for web/src/desk/__tests__/memory.app.test.tsx
# (fixtures/memory-continuity/recall.json; HOLDSPEAK_WIRE_WRITE=1 rewrites it).

CONTINUITY_FIXTURES = (Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__"
                       / "fixtures" / "memory-continuity")
SAT, SUN = "2026-09-02", "2026-09-07"
OLD_TEXT = "Freeze window is Saturday 02:00"
NEW_TEXT = "Freeze window is Sunday 02:00, not Saturday"
NEW_WHY = "Payments cannot drain the queue before 02:00 on a weekday."
CMT_TEXT = "Priya confirms the freeze window"


def _ok(response: Any) -> Any:
    assert response.status_code == 200, (response.request.url, response.status_code, response.text[:300])
    return response.json()


def _seed_continuity_meeting(meeting_id: str, day: str, title: str) -> None:
    from holdspeak.db import get_database

    with get_database()._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, 3600, 'complete', 'finalized', 'desktop')",
            (meeting_id, f"{day}T11:00:00", f"{day}T12:00:00", title),
        )
        conn.execute("DELETE FROM segments WHERE meeting_id = ?", (meeting_id,))
        for start, text in ((0.0, "Let's start with the cut-over sequencing for the payments platform"),
                            (1080.0, "Cut-over runs on the read replica first, then we flip writes"),
                            (1860.0, NEW_TEXT), (1980.0, CMT_TEXT)):
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
                "VALUES (?, ?, 'Marek', ?, ?)",
                (meeting_id, text, start, start + 60.0),
            )


def _continuity_propose(meeting_id: str, project_id: str, kind: str, text: str, *,
                        segment_index: int, rationale: str | None = None) -> str:
    from holdspeak.db import get_database

    prop = get_database().proposals.create_proposal(
        meeting_id=meeting_id, project_id=project_id, kind=kind, text=text,
        source_plugin="decision_capture" if kind == "decision" else "action_owner_enforcer",
        segment_timestamp=1860.0, span_start=1860.0, span_end=1920.0,
        segment_index=segment_index, support="supported", rationale=rationale,
        model_host="192.168.1.43",
    )
    assert prop is not None
    return prop.id


def _seed_continuity_chain(hub: Hub) -> dict[str, Any]:
    pid = _ok(hub.client.post("/api/projects", json={
        "name": "Q4 Platform", "description": "Seeded for the HS-200-13 proof.",
        "command_id": "hs200-13-q4-platform",
    }))["project"]["id"]
    _seed_continuity_meeting("m-sat", SAT, "Cut-over planning")
    _seed_continuity_meeting("m-sun", SUN, "Architecture review")
    for mid in ("m-sat", "m-sun"):
        _ok(hub.client.post(f"/api/projects/{pid}/meetings/{mid}", json={}))

    def confirm(proposal_id: str) -> dict[str, Any]:
        return _ok(hub.client.post(f"/api/proposals/{proposal_id}/confirm", json={}))

    old = confirm(_continuity_propose("m-sat", pid, "decision", OLD_TEXT, segment_index=2,
                                      rationale="Least traffic on Saturday"))
    new = confirm(_continuity_propose("m-sun", pid, "decision", NEW_TEXT, segment_index=2, rationale=NEW_WHY))
    cmt = confirm(_continuity_propose("m-sun", pid, "action", CMT_TEXT, segment_index=3))
    sealed = _ok(hub.client.post(f"/api/decision-records/{old['decision_record_id']}/supersede",
                                 json={"successor_id": new["decision_record_id"], "reason": "moved to Sunday"}))
    assert sealed["lifecycle"] == "superseded", sealed
    return {"project_id": pid, "old": old, "new": new, "cmt": cmt}


def _recall_read(hub: Hub, **params: str) -> dict[str, Any]:
    return _ok(hub.client.get("/api/memory/recall", params=params))


def test_the_recall_minute_reads_the_current_decision_carries_it_and_names_an_owner(
    hub: Hub, tmp_path: Path,
) -> None:
    """replaces: tests/e2e/test_hs200_continuity_glass.py::TestContinuityGlass::test_recall_1440 (T1 half:
      the recall wire, the carry, the owed row's next action after Name an owner)

    The same seed, the same presses the face makes, through the real routes.
    The answers are the fixture memory.app.test.tsx replays."""
    from tests.unit.test_desk_speak import _record

    chain = _seed_continuity_chain(hub)
    recent = _recall_read(hub, recent="1", filter="all")
    searched = _recall_read(hub, query="freeze window", filter="all")
    assert [c["id"] for c in searched["current"]] == [chain["new"]["decision_record_id"]]
    assert [c["id"] for c in searched["superseded"]] == [chain["old"]["decision_record_id"]]
    assert [r["id"] for r in searched["owed"]] == [chain["cmt"]["commitment_id"]]
    assert searched["current"][0]["rationale"] == NEW_WHY
    assert searched["current"][0]["carried"] is False
    recorded_source = {
        "kind": "meeting", "meeting_id": "m-sun", "title": "Architecture review",
        "started_at": f"{SUN}T11:00:00", "scope": "meeting:m-sun",
    }
    assert searched["owed"][0]["source"] == recorded_source
    assert recent["owed"][0]["source"] == recorded_source

    carry_body = {"project_id": chain["project_id"]}
    carried = _ok(hub.client.post(f"/api/decision-records/{chain['new']['decision_record_id']}/carry",
                                  json=carry_body))
    assert carried["replayed"] is False and carried["project_id"] == chain["project_id"]
    after_carry = _recall_read(hub, query="freeze window", filter="all")
    assert after_carry["current"][0]["carried"] is True
    assert after_carry["owed"][0]["source"] == recorded_source

    owed = after_carry["owed"][0]
    name_body = {"card_id": owed["action_item_id"], "verb": "delegate", "payload": {"to": "Priya"}}
    named = _ok(hub.client.post("/api/follow-through/complete", json=name_body))
    after_name = _recall_read(hub, query="freeze window", filter="all")
    assert after_name["owed"][0]["next_action"] == "set_date", after_name["owed"]
    assert after_name["owed"][0]["owner"] == "Priya"
    assert after_name["owed"][0]["source"] == recorded_source
    # Naming an owner does not complete the commitment (AC4).
    board = _ok(hub.client.get("/api/follow-through/board"))
    cards = [c for lane in board.values() if isinstance(lane, list) for c in lane
             if c.get("id") == chain["cmt"]["action_item_id"]]
    assert cards and cards[0]["status"] in ("open", "pending"), cards

    miss = _recall_read(hub, query="unfindablequasar", filter="all")
    assert miss["current"] == [] and miss["owed"] == [] and miss["meetings"] == []
    # The one other read the Desk memory window makes (its coder sessions).
    coders = _ok(hub.client.get("/api/coders/sessions?include_ended=false"))

    _record("recall", {
        "recent": recent, "searched": searched,
        "carry": {"path": f"/api/decision-records/{chain['new']['decision_record_id']}/carry",
                  "body": carry_body, "answer": carried},
        "after_carry": after_carry,
        "name_owner": {"body": name_body, "answer": named},
        "after_name": after_name, "miss": miss,
        "coders_sessions": coders,
    }, tmp_path, "tests/unit/test_desk_memory.py::test_the_recall_minute_reads_the_current_decision_carries_it_and_names_an_owner",
        folder=CONTINUITY_FIXTURES)


def test_the_decision_chain_and_the_carry_survive_a_hub_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """replaces: tests/e2e/test_hs200_continuity_glass.py::TestContinuityGlass::test_chain_survives_a_hub_restart

    The first hub seeds the chain, carries the current decision and reads
    Needs you once; a second hub boots on the same HOME and database file."""
    from holdspeak.db import get_database, reset_database
    from holdspeak.services.brief_carry import pending_carries
    from holdspeak.services.needs_you_aggregate import LastKnownStore, shared_last_known

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    try:
        first = _boot(tmp_path, monkeypatch)
        first_store = first.root.needs_you_last_known
        assert first_store is shared_last_known(lambda: first.db)
        assert first_store._db_factory() is first.db
        chain = _seed_continuity_chain(first)
        carried = _ok(first.client.post(f"/api/decision-records/{chain['new']['decision_record_id']}/carry", json={}))
        assert carried["replayed"] is False and carried["project_id"] == chain["project_id"]
        needs = _ok(first.client.get("/api/desk/needs-you?fresh=1"))
        row = next(i for i in needs["items"] if i["source"] == "commitment" and i["title"] == CMT_TEXT)
        assert row["nextAction"] == "name_owner" and row["actionItemId"] == chain["cmt"]["action_item_id"]
        first.client.close()

        # ── the SECOND hub on the same HOME (the same database file) ──
        second = _boot(tmp_path, monkeypatch)
        assert second.root.needs_you_last_known is shared_last_known(lambda: second.db)
        assert second.root.needs_you_last_known is not first_store
        assert second.root.needs_you_last_known._db_factory() is second.db
        wire = _recall_read(second, query="freeze window", filter="all")
        assert [c["id"] for c in wire["current"]] == [chain["new"]["decision_record_id"]]
        assert wire["current"][0]["carried"] is True, "the carry mark did not survive the restart"
        assert wire["current"][0]["rationale"] == NEW_WHY
        assert [c["id"] for c in wire["superseded"]] == [chain["old"]["decision_record_id"]]
        assert [r["id"] for r in wire["owed"]] == [chain["cmt"]["commitment_id"]]

        marks = pending_carries(get_database(), chain["project_id"])
        assert len(marks) == 1, marks
        assert marks[0]["current_record_id"] == chain["new"]["decision_record_id"]
        assert marks[0]["ref"] == marks[0]["current_ref"] and marks[0]["superseded"] is False
        assert marks[0]["text"] == NEW_TEXT and marks[0]["rationale"] == NEW_WHY
        remembered = LastKnownStore(db_factory=get_database).recall(f"project:{chain['project_id']}")
        assert remembered is not None and any(i.get("source") == "commitment" for i in remembered["items"])
        again = _ok(second.client.get("/api/desk/needs-you?fresh=1"))
        assert any(i["source"] == "commitment" and i["nextAction"] == "name_owner" for i in again["items"])
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


def test_a_prior_service_read_does_not_take_the_hubs_last_known_observations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.services import needs_you_aggregate
    from holdspeak.services.project_service import ProjectService

    # A lawful bare service read can bind the fallback before a hub starts.
    # The hub must persist its observations into its own database afterward.
    fallback = needs_you_aggregate.LastKnownStore()
    monkeypatch.setattr(needs_you_aggregate, "_LAST_KNOWN", fallback)
    prior = Database(tmp_path / "prior.db")
    prior.projects.create_project(project_id="prior-project", name="Prior service project")
    ProjectService(prior).needs_you(Principal(PrincipalKind.OWNER, "pytest"))
    assert needs_you_aggregate.shared_last_known(lambda: prior) is fallback
    assert fallback._db_factory() is prior
    assert fallback.source_ids() == ["project:prior-project"]
    restarted = tmp_path / "restarted"
    restarted.mkdir()
    try:
        test_the_decision_chain_and_the_carry_survive_a_hub_restart(restarted, monkeypatch)
        with prior._connection() as conn:
            rows = conn.execute("SELECT source_id FROM needs_you_last_known").fetchall()
        assert [row["source_id"] for row in rows] == ["project:prior-project"], (
            "the hub changed the prior service's observations"
        )
        assert needs_you_aggregate.shared_last_known(lambda: prior) is fallback
        assert fallback._db_factory() is prior, "starting a hub changed the bare service binding"
    finally:
        prior.close()


# ── from test_hs202_desk_memory_recent.py: HS-202-02 job 4 — Desk memory shows the desk's memory. ──
#
# 03-interaction-walk.md finding 7: "Desk memory shows nothing on a desk that
# has memory. The window's body is empty while the same desk holds a meeting,
# two decision records and a generated brief — all of them visible on the
# Floor behind the window."
#
# Traced: the face is query-first and has no zero-query read at all. Its only
# endpoint call requires a non-empty query
# (`holdspeak/services/recall_service.py:135-137` raises
# `query is required`), so a cold open asks the hub for nothing and renders
# a blank field under the filter chips.
#
# The source fix is a RECENT read: `GET /api/memory/recall?recent=1` with no
# query answers the desk's most recent memory. The blank-query refusal is
# UNCHANGED — `tests/unit/test_phase200_continuity.py:653` still pins the 400
# for a bare `query=""`, because a search with no words is still a search
# with no words.


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


# ── Astra's counsel finding 5 (PR #595): a desk of only meetings, or only
# notes, read EMPTY. `_memory_hits` sent an empty query into the FTS
# matcher, which raises `ValueError("query must contain searchable text")`
# (holdspeak/db/memory.py:101-105) and was swallowed into `[]`
# (recall_service.py:477-482). Decisions and briefs had a recent path;
# every other kind did not.


def _seed_meeting(db, meeting_id: str = "m-recent") -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO meetings (id, title, started_at)
               VALUES (?, ?, ?)""",
            (meeting_id, "Architecture review", "2026-09-19T11:00:00"),
        )
        conn.execute(
            """INSERT INTO segments
               (meeting_id, text, speaker, start_time, end_time)
               VALUES (?, ?, ?, ?, ?)""",
            (
                meeting_id,
                "We agreed the freeze window moves to Sunday.",
                "Karol",
                0.0,
                6.0,
            ),
        )


def _seed_note(db, note_id: str = "note-recent") -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO notes (id, title, body_markdown, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                note_id,
                "A thought I want kept",
                "The reader flag needs two reviews.",
                "2026-09-19T12:00:00",
                "2026-09-19T12:00:00",
            ),
        )


def test_a_desk_of_only_meetings_is_not_empty(client) -> None:
    db, http = client
    _seed_meeting(db)

    body = http.get("/api/memory/recall", params={"recent": "1"}).json()

    assert body["remembered"] > 0, body
    assert [m["title"] for m in body["meetings"]] == ["Architecture review"]
    assert body["meetings"][0]["source_ref"] == "meeting:m-recent"


def test_a_desk_of_only_notes_is_not_empty(client) -> None:
    db, http = client
    _seed_note(db)

    body = http.get("/api/memory/recall", params={"recent": "1"}).json()

    assert body["remembered"] > 0, body
    assert [n["title"] for n in body["also"]] == ["A thought I want kept"]
    assert body["also"][0]["source_ref"] == "note:note-recent"


def test_the_meetings_filter_reads_recent_meetings(client) -> None:
    db, http = client
    _seed_meeting(db)
    _seed_note(db)

    body = http.get(
        "/api/memory/recall", params={"recent": "1", "filter": "meetings"}
    ).json()
    assert [m["title"] for m in body["meetings"]] == ["Architecture review"]
    assert body["also"] == []


def test_recent_memory_is_newest_first(client) -> None:
    db, http = client
    _seed_meeting(db, "m-old")
    with db._connection() as conn:
        conn.execute("UPDATE meetings SET started_at=? WHERE id=?",
                     ("2026-01-01T09:00:00", "m-old"))
    _seed_meeting(db, "m-new")

    body = http.get("/api/memory/recall", params={"recent": "1"}).json()
    refs = [m["source_ref"] for m in body["meetings"]]
    assert refs.index("meeting:m-new") < refs.index("meeting:m-old"), refs


# ── Astra round 2, residual 3: the same hole, one kind further ──
# `recall_service.py:54` asks for `thread` under `also`, and RECENT had no
# spec for it (`db/memory.py`), so `recent()` skipped the kind in silence:
# a desk whose only memory is threads read as an empty desk, exactly as a
# desk of only meetings did before finding 5 was paid.


def _seed_thread(db, thread_id: str = "th-recent", *, updated_at: float = 1_758_000_000.0) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO threads (id, title, created_at, updated_at)
               VALUES (?, ?, ?, ?)""",
            (thread_id, "What the reader flag still needs", updated_at - 60, updated_at),
        )
        conn.execute(
            """INSERT INTO thread_messages
               (id, thread_id, role, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (f"{thread_id}-m1", thread_id, "user", updated_at - 30, updated_at - 30),
        )
        conn.execute(
            """INSERT INTO thread_message_parts
               (id, message_id, ordinal, kind, text)
               VALUES (?, ?, ?, ?, ?)""",
            (
                f"{thread_id}-p1",
                f"{thread_id}-m1",
                0,
                "text",
                "Two reviews outstanding before the flag comes down.",
            ),
        )


def test_a_desk_of_only_threads_is_not_empty(client) -> None:
    db, http = client
    _seed_thread(db)

    body = http.get("/api/memory/recall", params={"recent": "1"}).json()

    assert body["remembered"] > 0, body
    refs = [row["source_ref"] for row in body["also"]]
    assert "thread:th-recent" in refs, body["also"]
    row = next(r for r in body["also"] if r["source_ref"] == "thread:th-recent")
    assert row["title"] == "What the reader flag still needs"
    assert "Two reviews outstanding" in row["snippet"]


def test_a_deleted_thread_is_not_recent_memory(client) -> None:
    """The recency spec wears the lexical pass's own custody filters."""
    db, http = client
    _seed_thread(db, "th-gone")
    with db._connection() as conn:
        conn.execute(
            "UPDATE threads SET deleted_at=? WHERE id=?", (1_758_000_100.0, "th-gone")
        )

    body = http.get("/api/memory/recall", params={"recent": "1"}).json()
    assert [r["source_ref"] for r in body["also"]] == []


def test_every_kind_recall_asks_for_has_a_recent_source(client) -> None:
    """No kind may be asked for and then skipped in silence."""
    from holdspeak.db.memory import _ECOSYSTEM_SPECS, _RECENT_SPECS
    from holdspeak.services.recall_service import _ALSO_KINDS

    missing = [
        kind
        for kind in _ALSO_KINDS
        if kind not in _RECENT_SPECS and kind not in _ECOSYSTEM_SPECS
    ]
    assert missing == [], missing


# ── honest faces: a linked decision never says NO SOURCE ──────────────────


def test_a_meeting_decision_on_the_desk_memory_is_linked_not_no_source(hub: Hub) -> None:
    """replaces: tests/e2e/test_honest_faces_glass.py::test_desk_memory_does_not_say_no_source_beside_a_source (hub half)

    The recent read (Desk memory opened with no query) carries the meeting's
    decision with its source meeting, and its support axis is LINKED, never
    NO SOURCE. The face half: memory.app.test.tsx (the axes and Open source)."""
    from test_desk_needs_you import _seed_honest_faces

    _seed_honest_faces(hub)
    recall = _recall_read(hub, recent="1", filter="all")
    cards = [c for c in recall["current"] if c["text"] == "Freeze the old ledger on Nov 5"]
    assert len(cards) == 1, recall["current"]
    card = cards[0]
    assert card["axes"] == ["DECISION", "LINKED", "ACCEPTED"], card
    assert "NO SOURCE" not in card["axes"] and card["support"] == "LINKED", card
    assert (card["source"]["kind"], card["source"]["meeting_id"]) == ("meeting", "m-standup"), card
    assert card["source"]["token"].startswith("MTG "), card
