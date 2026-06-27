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
