"""Primitive Framework hub — Note / KB / Agent / Chain / Workflow repositories.

The desktop is the canonical store for the desk's synced first-class primitives.
These cover create/read/update/list, tombstone deletes, and the last-modified +
deleted shape that the sync transport relies on.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db import Database, reset_database


@pytest.fixture
def db(tmp_path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def test_note_upsert_get_list_and_tombstone(db: Database) -> None:
    note = db.notes.upsert(note_id="n1", title="Hello", body_markdown="# Hi", tags=["x", "y"])
    assert note.id == "n1"
    assert note.title == "Hello"
    assert note.tags == ["x", "y"]
    assert note.deleted is False
    assert note.last_modified  # stamped

    # Read back.
    got = db.notes.get("n1")
    assert got is not None and got.body_markdown == "# Hi"

    # Update preserves created_at, advances last_modified.
    created = note.created_at
    updated = db.notes.upsert(note_id="n1", title="Hello 2", body_markdown="x", tags=[])
    assert updated.title == "Hello 2"
    assert updated.created_at == created

    # List excludes tombstones by default.
    assert [n.id for n in db.notes.list()] == ["n1"]
    assert db.notes.delete("n1") is True
    assert db.notes.get("n1") is None  # hidden by default
    assert db.notes.get("n1", include_deleted=True).deleted is True
    assert db.notes.list() == []
    assert [n.id for n in db.notes.list(include_deleted=True)] == ["n1"]


def test_note_requires_id(db: Database) -> None:
    with pytest.raises(ValueError):
        db.notes.upsert(note_id="  ")


def test_agent_persona_roundtrip(db: Database) -> None:
    agent = db.agents.upsert(
        agent_id="a1",
        name="Summarizer",
        avatar="robot",
        role="assistant",
        system_prompt="You summarize.",
        user_template="Summarize: {input}",
        tools=["web"],
        kb_id="kb1",
    )
    assert agent.name == "Summarizer"
    assert agent.tools == ["web"]
    assert agent.kb_id == "kb1"
    assert agent.system_prompt == "You summarize."

    got = db.agents.get("a1")
    assert got is not None and got.user_template == "Summarize: {input}"

    # to_dict carries the persona contract shape.
    d = agent.to_dict()
    for key in ("id", "name", "avatar", "role", "system_prompt", "user_template",
                "tools", "kb_id", "last_modified", "deleted"):
        assert key in d

    assert db.agents.delete("a1") is True
    assert db.agents.get("a1") is None


def test_kb_chain_workflow_roundtrip(db: Database) -> None:
    kb = db.kbs.upsert(kb_id="kb1", name="Specs", member_ids=["n1", "a1"])
    assert kb.member_ids == ["n1", "a1"]
    assert db.kbs.get("kb1").name == "Specs"

    chain = db.chains.upsert(chain_id="c1", name="Pipe", steps=["a1", "a2"])
    assert chain.steps == ["a1", "a2"]

    wf = db.workflows.upsert(
        workflow_id="w1", name="Graph", prompt="do it",
        graph_json={"nodes": [1, 2], "edges": []},
    )
    assert wf.graph_json == {"nodes": [1, 2], "edges": []}
    assert wf.prompt == "do it"

    assert [k.id for k in db.kbs.list()] == ["kb1"]
    assert [c.id for c in db.chains.list()] == ["c1"]
    assert [w.id for w in db.workflows.list()] == ["w1"]


def test_last_modified_is_iso_utc_z(db: Database) -> None:
    note = db.notes.upsert(note_id="n1", title="t")
    assert note.last_modified.endswith("Z")
    # An explicit last_modified is preserved (sync push supplies the peer's stamp).
    note2 = db.notes.upsert(note_id="n2", title="t2", last_modified="2030-01-01T00:00:00Z")
    assert note2.last_modified == "2030-01-01T00:00:00Z"


# ── Directory (organization/synced) ──────────────────────────────────────────
def test_directory_upsert_get_list_nesting_and_tombstone(db: Database) -> None:
    root = db.directories.upsert(directory_id="d1", name="Root")
    assert root.id == "d1" and root.name == "Root" and root.parent_id is None
    assert root.deleted is False and root.last_modified

    # Nesting via parent_id.
    child = db.directories.upsert(directory_id="d2", name="Child", parent_id="d1")
    assert child.parent_id == "d1"

    # List excludes tombstones; sorted by name.
    names = [d.name for d in db.directories.list()]
    assert names == ["Child", "Root"]

    # Update preserves created_at, advances last_modified.
    created = root.created_at
    renamed = db.directories.upsert(directory_id="d1", name="Root 2")
    assert renamed.name == "Root 2" and renamed.created_at == created

    # Tombstone hides it from the default list/get, stays with include_deleted.
    assert db.directories.delete("d1") is True
    assert db.directories.get("d1") is None
    assert db.directories.get("d1", include_deleted=True).deleted is True
    assert [d.id for d in db.directories.list()] == ["d2"]


def test_directory_upsert_requires_id(db: Database) -> None:
    with pytest.raises(ValueError):
        db.directories.upsert(directory_id="  ", name="x")


def test_directory_membership_map_and_refile(db: Database) -> None:
    db.directories.upsert(directory_id="d1", name="A")
    db.directories.upsert(directory_id="d2", name="B")

    # File a primitive — keyed by primitive_id, the record id IS the primitive id.
    m = db.directory_memberships.upsert(primitive_id="note_1", directory_id="d1")
    assert m.primitive_id == "note_1" and m.directory_id == "d1"
    assert m.id == "note_1"  # synced identity == map key
    assert m.deleted is False and m.last_modified

    # One filing per primitive: re-file overwrites the edge (no second row).
    moved = db.directory_memberships.upsert(primitive_id="note_1", directory_id="d2")
    assert moved.directory_id == "d2"
    assert len(db.directory_memberships.list()) == 1

    # list_for_directory reflects the move.
    assert [x.primitive_id for x in db.directory_memberships.list_for_directory("d2")] == ["note_1"]
    assert db.directory_memberships.list_for_directory("d1") == []

    # Unfile = tombstone (row stays so the unfile propagates over sync).
    assert db.directory_memberships.delete("note_1") is True
    assert db.directory_memberships.get("note_1") is None
    assert db.directory_memberships.get("note_1", include_deleted=True).deleted is True
    assert db.directory_memberships.list_for_directory("d2") == []


def test_directory_membership_live_requires_directory(db: Database) -> None:
    with pytest.raises(ValueError):
        db.directory_memberships.upsert(primitive_id="p1", directory_id="")
    # A tombstone may carry an empty directory (an unfile pushed from a peer).
    tomb = db.directory_memberships.upsert(primitive_id="p1", directory_id="", deleted=True)
    assert tomb.deleted is True
