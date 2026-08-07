"""HS-119-03 — the toolkit seed + reset-to-seed.

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
import holdspeak.db.seed as seed_module
from holdspeak.config import Config
from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.db.seed import DEFAULT_SEED, apply_seed, load_manifest, reset_desk
from holdspeak.principals import PrincipalRight, required_right
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_desk_seed_router, build_sync_router

ZONES = {
    "hs-seed-inbox": "Inbox",
    "hs-seed-work": "Work",
}

PROFILE_IDS = [
    "hs-seed-local-4b-resolver",
    "hs-seed-local-small",
    "hs-seed-local-medium",
    "hs-seed-cloud-openai",
    "hs-seed-cloud-anthropic",
]


@pytest.fixture
def db(tmp_path, monkeypatch):
    reset_database()
    monkeypatch.setattr(seed_module, "CONFIG_FILE", tmp_path / "config.json")
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
    assert report.applied == {"directories": 2}
    assert report.profiles_seeded == 5
    assert report.workbenches_seeded == 1
    assert report.filed == 0

    snap = _snapshot(db)
    assert dict((i, n) for i, n, _ in snap["directories"]) == ZONES
    assert snap["notes"] == []
    assert snap["kbs"] == snap["chains"] == snap["recipes"] == snap["workflows"] == []
    assert snap["memberships"] == []

    profiles = {p.id: p for p in db.profiles.list()}
    assert set(profiles) == set(PROFILE_IDS)
    assert profiles["hs-seed-cloud-openai"].requires_key is True
    assert profiles["hs-seed-local-4b-resolver"].requires_key is False

    workbenches = db.workbenches.list()
    assert len(workbenches) == 1
    wb = workbenches[0]
    assert wb.id == "hs-seed-workbench"
    assert wb.name == "Workbench"
    assert wb.resolver_profile_id == "hs-seed-local-4b-resolver"


def test_no_demo_content_after_seeding(db) -> None:
    apply_seed(db)
    snap = _snapshot(db)
    assert snap["notes"] == []
    assert snap["recipes"] == []
    assert snap["workflows"] == []
    assert snap["kbs"] == []
    assert snap["chains"] == []


def test_apply_twice_is_identical_no_duplicates(db) -> None:
    apply_seed(db)
    first = _snapshot(db)
    report = apply_seed(db)
    assert report.applied == {"directories": 2}
    assert report.profiles_seeded == 5
    assert report.workbenches_seeded == 1
    assert _snapshot(db) == first


def test_seed_adopts_profile_into_an_unset_existing_config(db) -> None:
    Config().save(seed_module.CONFIG_FILE)
    report = apply_seed(db)
    assert report.profiles_adopted == {
        "dictation.runtime.profile_id": "hs-seed-local-4b-resolver",
        "meeting.intel_profile_id": "hs-seed-local-4b-resolver",
    }
    config = Config.load(seed_module.CONFIG_FILE)
    assert config.dictation.runtime.profile_id == "hs-seed-local-4b-resolver"
    assert config.meeting.intel_profile_id == "hs-seed-local-4b-resolver"


def test_seed_route_applies_the_packaged_manifest(client, db) -> None:
    resp = client.post("/api/desk/seed")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["applied"] == {"directories": 2}
    assert body["profiles_seeded"] == 5
    assert body["workbenches_seeded"] == 1
    assert body["filed"] == 0
    assert body["total"] == 8
    assert {d.id for d in db.directories.list()} == set(ZONES)


def test_starter_workbench_wired_to_resolver(db) -> None:
    apply_seed(db)
    wb = db.workbenches.get("hs-seed-workbench")
    assert wb is not None
    assert wb.resolver_profile_id == "hs-seed-local-4b-resolver"


def test_cloud_profiles_require_key(db) -> None:
    apply_seed(db)
    profiles = {p.id: p for p in db.profiles.list()}
    assert profiles["hs-seed-cloud-openai"].requires_key is True
    assert profiles["hs-seed-cloud-anthropic"].requires_key is True
    assert profiles["hs-seed-local-4b-resolver"].requires_key is False
    assert profiles["hs-seed-local-small"].requires_key is False
    assert profiles["hs-seed-local-medium"].requires_key is False


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
    db.workbenches.upsert(workbench_id="clutter-wb", name="Old workbench")


def test_reset_tombstones_clutter_and_reseeds(db) -> None:
    _populate_clutter(db)
    report = reset_desk(db)

    assert report.tombstoned["notes"] == 1
    assert report.tombstoned["kbs"] == 1
    assert report.tombstoned["recipes"] == 1
    assert report.tombstoned["chains"] == 1
    assert report.tombstoned["workflows"] == 1
    assert report.tombstoned["workbenches"] == 1
    assert report.tombstoned["directory_memberships"] == 1
    assert report.tombstoned["directories"] == 1

    assert db.notes.get("clutter-note") is None
    assert db.notes.get("clutter-note", include_deleted=True).deleted is True
    assert db.directories.get("clutter-zone", include_deleted=True).deleted is True
    assert db.kbs.get("clutter-kb", include_deleted=True).deleted is True
    assert db.workbenches.get("clutter-wb", include_deleted=True).deleted is True
    membership = db.directory_memberships.get("note:clutter-note", include_deleted=True)
    assert membership is not None and membership.deleted is True

    assert {d.id for d in db.directories.list()} == set(ZONES)
    assert {n.id for n in db.notes.list()} == set()
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
    assert body["tombstoned_total"] == 8
    assert body["tombstoned"]["directories"] == 1
    assert body["tombstoned"]["workbenches"] == 1
    assert body["seeded"] == {"directories": 2}
    assert body["seeded_total"] == 8
    assert body["profiles_seeded"] == 5
    assert "dictation.runtime.profile_id" in body["profiles_adopted"]
    assert body["filed"] == 0
    assert body["manifest"] == DEFAULT_SEED


def test_sync_pull_reports_tombstones_never_resurrects(client, db) -> None:
    _populate_clutter(db)
    assert client.post("/api/desk/reset").status_code == 200

    pull = client.get("/api/sync/pull").json()
    by_id = {rec["meta"]["id"]: rec["meta"] for rec in pull.get("notes", [])}
    assert by_id.get("clutter-note", {}).get("deleted") is True
    dirs = {rec["meta"]["id"]: rec["meta"] for rec in pull["directories"]}
    assert dirs["clutter-zone"]["deleted"] is True
    assert dirs["hs-seed-inbox"]["deleted"] is False


# ── the edge ───────────────────────────────────────────────────────────────
def test_seed_and_reset_are_owner_verbs(client) -> None:
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
    assert ids == list(ZONES)
    assert all(i.startswith("hs-seed-") for i in ids)
