"""HS-112-03 — the architect's desk seed + reset-to-seed.

The packaged fresh-desk manifest applies through the repositories,
idempotent by deterministic id; reset TOMBSTONES every desk primitive
(rows retained, `deleted=1` — sync would resurrect a hard purge) and
re-applies the seed. Meetings and the dictation journal survive by
design. Routes are exercised over a real tmp-path Database, the same
harness the sibling primitive-route tests use.
"""
from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.db.seed import DEFAULT_SEED, apply_seed, load_manifest, reset_desk
from holdspeak.principals import PrincipalRight, required_right
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_desk_seed_router, build_sync_router

DRAWERS = {
    "hs-desk-adrs": "ADRs",
    "hs-desk-meetings": "Meetings",
    "hs-desk-rules": "Rules",
    "hs-desk-decisions": "Decisions",
    "hs-desk-reference": "Reference",
    "hs-desk-inbox": "Inbox",
}


@pytest.fixture
def db(tmp_path):
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


@pytest.fixture
def client(db, monkeypatch) -> TestClient:
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    ctx = WebContext(get_state=lambda: {})
    app.include_router(build_desk_seed_router(ctx))
    app.include_router(build_sync_router(ctx))
    return TestClient(app)


def _snapshot(db: Database) -> dict:
    """The live desk, content included — the identity the id contract pins."""
    return {
        "directories": [(d.id, d.name, d.parent_id) for d in db.directories.list()],
        "notes": [(n.id, n.title, n.body_markdown, tuple(n.tags)) for n in db.notes.list()],
        "memberships": sorted(
            (m.primitive_id, m.directory_id) for m in db.directory_memberships.list()
        ),
        "kbs": [k.id for k in db.kbs.list()],
        "recipes": [r.id for r in db.recipes.list()],
        "chains": [c.id for c in db.chains.list()],
        "workflows": [w.id for w in db.workflows.list()],
    }


# ── the seed ───────────────────────────────────────────────────────────────
def test_fresh_db_seeds_exactly_the_manifest(db) -> None:
    report = apply_seed(db)
    assert report.manifest == DEFAULT_SEED
    assert report.applied == {"directories": 6, "notes": 2}
    assert report.filed == 2

    snap = _snapshot(db)
    assert dict((i, n) for i, n, _ in snap["directories"]) == DRAWERS
    # Six drawers, two starter notes, NOTHING else — sparse is the contract.
    assert snap["kbs"] == snap["recipes"] == snap["chains"] == snap["workflows"] == []

    notes = {n[0]: n for n in snap["notes"]}
    adr = notes["hs-desk-note-adr-template"]
    assert adr[1] == "ADR template"
    for heading in ("## Context", "## Decision", "## Consequences", "Status:"):
        assert heading in adr[2]
    rules = notes["hs-desk-note-working-rules"]
    assert rules[1] == "Working rules"
    assert "Inbox is the landing zone" in rules[2]
    assert "Reset to seed lives in Prefs" in rules[2]

    assert snap["memberships"] == [
        ("note:hs-desk-note-adr-template", "hs-desk-adrs"),
        ("note:hs-desk-note-working-rules", "hs-desk-rules"),
    ]


def test_apply_twice_is_identical_no_duplicates(db) -> None:
    apply_seed(db)
    first = _snapshot(db)
    report = apply_seed(db)
    assert report.applied == {"directories": 6, "notes": 2}
    assert _snapshot(db) == first  # ids stable, zero duplicates


def test_seed_route_applies_the_packaged_manifest(client, db) -> None:
    resp = client.post("/api/desk/seed")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["applied"] == {"directories": 6, "notes": 2}
    assert body["filed"] == 2
    assert body["total"] == 8
    assert {d.id for d in db.directories.list()} == set(DRAWERS)


# ── the reset ──────────────────────────────────────────────────────────────
def _populate_clutter(db: Database) -> None:
    db.notes.upsert(note_id="clutter-note", title="Scratch")
    db.kbs.upsert(kb_id="clutter-kb", name="Old KB")
    db.recipes.upsert(recipe_id="clutter-agent", name="Old agent")
    db.chains.upsert(chain_id="clutter-chain", name="Old chain", steps=["clutter-agent"])
    db.workflows.upsert(workflow_id="clutter-wf", name="Old wf", prompt="p")
    db.directories.upsert(directory_id="clutter-zone", name="Junk drawer")
    db.directory_memberships.upsert(
        primitive_id="note:clutter-note", directory_id="clutter-zone"
    )


def test_reset_tombstones_clutter_and_reseeds(db) -> None:
    _populate_clutter(db)
    report = reset_desk(db)

    assert report.tombstoned == {
        "notes": 1, "kbs": 1, "recipes": 1, "chains": 1, "workflows": 1,
        "directory_memberships": 1, "directories": 1,
    }
    # Tombstone, never purge: the rows REMAIN with deleted=1.
    assert db.notes.get("clutter-note") is None
    assert db.notes.get("clutter-note", include_deleted=True).deleted is True
    assert db.directories.get("clutter-zone", include_deleted=True).deleted is True
    assert db.kbs.get("clutter-kb", include_deleted=True).deleted is True
    membership = db.directory_memberships.get("note:clutter-note", include_deleted=True)
    assert membership is not None and membership.deleted is True

    # The seed is present and is the whole live desk.
    assert {d.id for d in db.directories.list()} == set(DRAWERS)
    assert {n.id for n in db.notes.list()} == {
        "hs-desk-note-adr-template", "hs-desk-note-working-rules",
    }
    assert report.seed is not None and report.seed.total == 8


def test_reset_leaves_meetings_and_journal_alone(db) -> None:
    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="Sprint review")
    )
    db.dictation_journal.record(
        source="dictation", transcript="hello", final_text="hello", total_ms=10.0
    )
    _populate_clutter(db)

    reset_desk(db)

    assert [m.id for m in db.meetings.list_meetings()] == ["m1"]
    assert db.dictation_journal.count() == 1


def test_reset_route_names_the_counts(client, db) -> None:
    _populate_clutter(db)
    resp = client.post("/api/desk/reset")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["tombstoned_total"] == 7
    assert body["tombstoned"]["directories"] == 1
    assert body["seeded"] == {"directories": 6, "notes": 2}
    assert body["seeded_total"] == 8
    assert body["filed"] == 2
    assert body["manifest"] == DEFAULT_SEED


def test_sync_pull_reports_tombstones_never_resurrects(client, db) -> None:
    _populate_clutter(db)
    assert client.post("/api/desk/reset").status_code == 200

    pull = client.get("/api/sync/pull").json()
    by_id = {rec["meta"]["id"]: rec["meta"] for rec in pull["notes"]}
    assert by_id["clutter-note"]["deleted"] is True  # the tombstone RIDES
    assert by_id["hs-desk-note-adr-template"]["deleted"] is False
    dirs = {rec["meta"]["id"]: rec["meta"] for rec in pull["directories"]}
    assert dirs["clutter-zone"]["deleted"] is True
    assert dirs["hs-desk-inbox"]["deleted"] is False
    memberships = {
        rec["meta"]["id"]: rec["meta"] for rec in pull["directory_memberships"]
    }
    assert memberships["note:clutter-note"]["deleted"] is True

    # Pulling again after a re-seed still reports the tombstones (a paired
    # device can never win them back with a stale copy).
    again = client.get("/api/sync/pull").json()
    assert {r["meta"]["id"] for r in again["notes"] if r["meta"]["deleted"]} == {
        "clutter-note"
    }


# ── the edge ───────────────────────────────────────────────────────────────
def test_seed_and_reset_are_owner_verbs(client) -> None:
    # The centralized route-right table (the one enforcement point,
    # HS-106-02) requires OWNER for both POSTs.
    assert required_right("POST", "/api/desk/seed") is PrincipalRight.OWNER
    assert required_right("POST", "/api/desk/reset") is PrincipalRight.OWNER


def test_unauthenticated_gets_the_named_refusal() -> None:
    from unittest.mock import MagicMock

    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(return_value={"timestamp": 1.0, "label": "x"}),
            on_stop=MagicMock(return_value={"status": "stopped"}),
            get_state=MagicMock(
                return_value={"id": "t", "duration": 1, "bookmarks": []}
            ),
        ),
        host="0.0.0.0",
        auth_token="s3cret",
    )
    edge = TestClient(server.app)
    edge.headers.pop("x-holdspeak-token", None)
    for path in ("/api/desk/seed", "/api/desk/reset"):
        refused = edge.post(path)
        assert refused.status_code == 401
        body = refused.json()
        assert body["error"] == "principal_right_required"
        assert body["principal"] == "none"
        assert body["missing_right"] == "owner"


def test_manifest_ships_in_the_package() -> None:
    manifest = load_manifest()
    ids = [item["id"] for item in manifest["directories"]]
    assert ids == list(DRAWERS)
    assert all(i.startswith("hs-desk-") for i in ids)
