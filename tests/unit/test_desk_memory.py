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
    from tests.unit.test_memory_slice4_observations import Rules, _filed_note, _learn, _meeting
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

    carry_body = {"project_id": chain["project_id"]}
    carried = _ok(hub.client.post(f"/api/decision-records/{chain['new']['decision_record_id']}/carry",
                                  json=carry_body))
    assert carried["replayed"] is False and carried["project_id"] == chain["project_id"]
    after_carry = _recall_read(hub, query="freeze window", filter="all")
    assert after_carry["current"][0]["carried"] is True

    owed = after_carry["owed"][0]
    name_body = {"card_id": owed["action_item_id"], "verb": "delegate", "payload": {"to": "Priya"}}
    named = _ok(hub.client.post("/api/follow-through/complete", json=name_body))
    after_name = _recall_read(hub, query="freeze window", filter="all")
    assert after_name["owed"][0]["next_action"] == "set_date", after_name["owed"]
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
    from holdspeak.services.needs_you_aggregate import LastKnownStore

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    try:
        first = _boot(tmp_path, monkeypatch)
        chain = _seed_continuity_chain(first)
        carried = _ok(first.client.post(f"/api/decision-records/{chain['new']['decision_record_id']}/carry", json={}))
        assert carried["replayed"] is False and carried["project_id"] == chain["project_id"]
        needs = _ok(first.client.get("/api/desk/needs-you?fresh=1"))
        row = next(i for i in needs["items"] if i["source"] == "commitment" and i["title"] == CMT_TEXT)
        assert row["nextAction"] == "name_owner" and row["actionItemId"] == chain["cmt"]["action_item_id"]
        first.client.close()

        # ── the SECOND hub on the same HOME (the same database file) ──
        second = _boot(tmp_path, monkeypatch)
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
