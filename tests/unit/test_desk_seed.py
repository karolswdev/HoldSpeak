"""HS-140-04 — the furnished desk seed + reset-to-seed.

The packaged fresh-desk manifest applies through the repositories,
preservation-first by deterministic id; reset TOMBSTONES every desk primitive
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
from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.db.seed import DEFAULT_SEED, apply_seed, load_manifest, reset_desk
from holdspeak.grounding import hydrate_grounding_blocks
from holdspeak.principals import PrincipalRight, required_right
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_desk_seed_router, build_sync_router

ZONES = {
    "hs-seed-inbox": "Inbox",
    "hs-seed-personal": "Personal",
    "hs-seed-work": "Work",
    "hs-seed-meetings": "Meetings",
    "hs-seed-decisions": "Decisions",
    "hs-seed-reference": "Reference",
}

START_HERE = "hs-seed-start-here"
CONTEXT_NOTES = {
    "hs-seed-about-me": "About me",
    "hs-seed-current-priorities": "Current priorities",
    "hs-seed-how-i-like-help": "How I like help",
    "hs-seed-people-vocabulary": "People & vocabulary",
    "hs-seed-meeting-preferences": "Meeting preferences",
}
EVERYDAY_CONTEXT = "hs-seed-everyday-context"


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
    assert report.applied == {"directories": 6, "notes": 7, "kbs": 1, "recipes": 4}
    assert report.profiles_seeded == report.workbenches_seeded == 0
    assert report.filed == 6

    snap = _snapshot(db)
    assert dict((i, n) for i, n, _ in snap["directories"]) == ZONES
    assert {n.id: n.title for n in db.notes.list()} == {
        START_HERE: "Start here", "hs-seed-prompt-weekly-update": "Weekly update", **CONTEXT_NOTES,
    }
    kb = db.kbs.get(EVERYDAY_CONTEXT)
    assert kb is not None and kb.name == "Everyday context"
    assert set(kb.member_ids) == {f"note:{note_id}" for note_id in CONTEXT_NOTES}
    assert {
        row.resource_ref for row in db.knowledge_memberships.list_for_knowledge(EVERYDAY_CONTEXT)
    } == set(kb.member_ids)
    assert sorted(snap["recipes"]) == ["hs-seed-mode-chase", "hs-seed-mode-desk", "hs-seed-mode-draft", "hs-seed-mode-plan"]
    assert snap["chains"] == snap["workflows"] == []
    assert db.profiles.list() == db.workbenches.list() == []


def test_starter_text_is_questions_not_invented_owner_facts(db) -> None:
    apply_seed(db)
    text = "\n".join(note.body_markdown for note in db.notes.list())
    assert "never automatically included" in db.notes.get(START_HERE).body_markdown
    assert "device-pairing" in db.notes.get(START_HERE).body_markdown
    for invented_fact in ("Karol", "Acme", "I am ", "My name is", "I work at"):
        assert invented_fact not in text


def test_apply_twice_is_identical_no_duplicates(db) -> None:
    apply_seed(db)
    first = _snapshot(db)
    report = apply_seed(db)
    assert report.applied == {}
    assert report.total == report.filed == 0
    assert _snapshot(db) == first


def test_ordinary_seed_preserves_edits_tombstones_filing_and_agent_attachment(db) -> None:
    apply_seed(db)
    db.notes.upsert(note_id="hs-seed-about-me", title="My name", body_markdown="Edited by me")
    db.kbs.upsert(kb_id=EVERYDAY_CONTEXT, name="My context", member_ids=[f"note:{START_HERE}"])
    db.directory_memberships.upsert(
        primitive_id="note:hs-seed-about-me", directory_id="hs-seed-reference"
    )
    db.recipes.upsert(recipe_id="my-agent", name="My agent", kb_id=EVERYDAY_CONTEXT)
    assert db.notes.delete("hs-seed-meeting-preferences")

    assert apply_seed(db).total == 0
    edited = db.notes.get("hs-seed-about-me")
    assert edited is not None and (edited.title, edited.body_markdown) == ("My name", "Edited by me")
    assert db.notes.get("hs-seed-meeting-preferences") is None
    assert db.notes.get("hs-seed-meeting-preferences", include_deleted=True).deleted is True
    assert db.kbs.get(EVERYDAY_CONTEXT).name == "My context"
    assert db.kbs.get(EVERYDAY_CONTEXT).member_ids == [f"note:{START_HERE}"]
    assert db.directory_memberships.get("note:hs-seed-about-me").directory_id == "hs-seed-reference"
    assert db.recipes.get("my-agent").kb_id == EVERYDAY_CONTEXT


def test_retry_completes_new_relationships_without_mutating_partial_desk(db) -> None:
    """An interrupted ordinary seed can safely finish its missing pieces."""
    manifest = load_manifest()
    for directory in manifest["directories"]:
        db.directories.upsert(directory_id=directory["id"], name=directory["name"])
    note_by_id = {note["id"]: note for note in manifest["notes"]}
    for note_id in CONTEXT_NOTES:
        if note_id == "hs-seed-current-priorities":
            continue  # This is the object the retry must create and file.
        note = note_by_id[note_id]
        db.notes.upsert(
            note_id=note_id,
            title="My edited note" if note_id == "hs-seed-about-me" else note["title"],
            body_markdown="My edited text" if note_id == "hs-seed-about-me" else note["body_markdown"],
        )
    db.directory_memberships.upsert(
        primitive_id="note:hs-seed-about-me", directory_id="hs-seed-reference"
    )
    db.notes.upsert(note_id=START_HERE, title="Start here")
    assert db.notes.delete(START_HERE)

    report = apply_seed(db)

    assert report.applied == {"notes": 2, "kbs": 1, "recipes": 4}
    assert report.filed == 1
    kb = db.kbs.get(EVERYDAY_CONTEXT)
    assert kb is not None and set(kb.member_ids) == {
        f"note:{note_id}" for note_id in CONTEXT_NOTES
    }
    assert db.directory_memberships.get(
        "note:hs-seed-current-priorities"
    ).directory_id == "hs-seed-work"
    about = db.notes.get("hs-seed-about-me")
    assert about is not None and (about.title, about.body_markdown) == (
        "My edited note", "My edited text",
    )
    assert db.directory_memberships.get(
        "note:hs-seed-about-me"
    ).directory_id == "hs-seed-reference"
    assert db.notes.get(START_HERE) is None
    assert db.notes.get(START_HERE, include_deleted=True).deleted is True


def test_seed_route_applies_the_packaged_manifest(client, db) -> None:
    resp = client.post("/api/desk/seed")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["applied"] == {"directories": 6, "notes": 7, "kbs": 1, "recipes": 4}
    assert body["profiles_seeded"] == body["workbenches_seeded"] == 0
    assert body["filed"] == 6
    assert body["total"] == 18
    assert {d.id for d in db.directories.list()} == set(ZONES)


def test_seeded_everyday_context_hydrates_edited_note_contents(db) -> None:
    apply_seed(db)
    db.notes.upsert(
        note_id="hs-seed-about-me", title="About me", body_markdown="Edited context arrives."
    )
    blocks, _ids, titles, unknown = hydrate_grounding_blocks(
        db, [], [], "summary", qualified_refs=[f"knowledge:{EVERYDAY_CONTEXT}"]
    )
    assert unknown == []
    assert titles == ["Everyday context"]
    assert "Edited context arrives." in blocks[0]


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
    assert {n.id for n in db.notes.list()} == {START_HERE, "hs-seed-prompt-weekly-update", *CONTEXT_NOTES}
    assert report.seed is not None and report.seed.total == 18


def test_reset_force_restores_edited_and_tombstoned_packaged_objects(db) -> None:
    apply_seed(db)
    db.notes.upsert(note_id="hs-seed-about-me", title="Changed", body_markdown="Changed")
    assert db.notes.delete("hs-seed-meeting-preferences")
    db.kbs.upsert(kb_id=EVERYDAY_CONTEXT, name="Changed context", member_ids=[])
    db.directory_memberships.upsert(
        primitive_id="note:hs-seed-about-me", directory_id="hs-seed-reference"
    )

    report = reset_desk(db)

    assert report.seed is not None and report.seed.applied == {
        "directories": 6, "notes": 7, "kbs": 1, "recipes": 4,
    }
    assert db.notes.get("hs-seed-about-me").title == "About me"
    assert db.notes.get("hs-seed-meeting-preferences") is not None
    assert db.kbs.get(EVERYDAY_CONTEXT).name == "Everyday context"
    assert set(db.kbs.get(EVERYDAY_CONTEXT).member_ids) == {
        f"note:{note_id}" for note_id in CONTEXT_NOTES
    }
    assert db.directory_memberships.get("note:hs-seed-about-me").directory_id == "hs-seed-personal"


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
    assert body["seeded"] == {"directories": 6, "notes": 7, "kbs": 1, "recipes": 4}
    assert body["seeded_total"] == 18
    assert body["profiles_seeded"] == 0
    assert body["profiles_adopted"] == {}
    assert body["filed"] == 6
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
