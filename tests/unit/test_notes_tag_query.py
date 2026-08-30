"""HS-153-02 — Notes tag query: list_by_tag(json_each) + GET /api/notes?tag=prompt.

Proves: a note with tags [prompt, x] matches ?tag=prompt; a note
without 'prompt' does not; deleted notes excluded; the route returns
the correct shape.
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


# ── repository-level tests ──────────────────────────────────────────


class TestListByTag:
    """NoteRepository.list_by_tag (json_each over tags_json)."""

    def test_matches_single_tag(self, db: Database) -> None:
        db.notes.upsert(
            note_id="p1", title="Weekly update",
            body_markdown="Summarize.", tags=["prompt"],
        )
        db.notes.upsert(
            note_id="n1", title="Plain note",
            body_markdown="Just a note.", tags=[],
        )
        results = db.notes.list_by_tag("prompt")
        assert len(results) == 1
        assert results[0].id == "p1"

    def test_matches_multi_tag_note(self, db: Database) -> None:
        """A note tagged [prompt, x] matches ?tag=prompt."""
        db.notes.upsert(
            note_id="p2", title="1:1 prep",
            body_markdown="Prepare.", tags=["prompt", "meeting"],
        )
        results = db.notes.list_by_tag("prompt")
        assert len(results) == 1
        assert results[0].id == "p2"

    def test_no_match_returns_empty(self, db: Database) -> None:
        db.notes.upsert(
            note_id="n1", title="Untagged",
            body_markdown="Nothing.", tags=["other"],
        )
        assert db.notes.list_by_tag("prompt") == []

    def test_deleted_excluded(self, db: Database) -> None:
        db.notes.upsert(
            note_id="p3", title="Deleted prompt",
            body_markdown="Gone.", tags=["prompt"],
        )
        db.notes.delete("p3")
        assert db.notes.list_by_tag("prompt") == []

    def test_deleted_included_when_flag_set(self, db: Database) -> None:
        db.notes.upsert(
            note_id="p4", title="Deleted but included",
            body_markdown="Still here.", tags=["prompt"],
        )
        db.notes.delete("p4")
        results = db.notes.list_by_tag("prompt", include_deleted=True)
        assert len(results) == 1
        assert results[0].id == "p4"

    def test_empty_tag_returns_empty(self, db: Database) -> None:
        db.notes.upsert(
            note_id="p5", title="Tagged",
            body_markdown="x", tags=["prompt"],
        )
        assert db.notes.list_by_tag("") == []
        assert db.notes.list_by_tag("  ") == []

    def test_multiple_prompts_returned(self, db: Database) -> None:
        """At least two prompt seeds means the completion list has items."""
        db.notes.upsert(
            note_id="p1", title="Weekly update",
            body_markdown="Week summary.", tags=["prompt"],
        )
        db.notes.upsert(
            note_id="p2", title="1:1 prep",
            body_markdown="1:1 prep.", tags=["prompt"],
        )
        results = db.notes.list_by_tag("prompt")
        assert len(results) == 2
        titles = {r.title for r in results}
        assert "Weekly update" in titles
        assert "1:1 prep" in titles


# ── service-level test ──────────────────────────────────────────────


class TestPrimitiveServiceListNotes:
    def test_list_notes_with_tag(self, db: Database) -> None:
        from holdspeak.services.primitive_service import PrimitiveService

        db.notes.upsert(
            note_id="p1", title="Weekly update",
            body_markdown="Summary.", tags=["prompt"],
        )
        db.notes.upsert(
            note_id="n1", title="Plain",
            body_markdown="Nope.", tags=["general"],
        )
        svc = PrimitiveService(db)
        results = svc.list_notes(None, tag="prompt")
        assert len(results) == 1
        assert results[0]["id"] == "p1"
        assert results[0]["title"] == "Weekly update"


# ── seed test ───────────────────────────────────────────────────────


class TestSeedPromptNotes:
    """The fresh-desk seed includes at least two prompt notes."""

    def test_seed_creates_prompt_notes(self, db: Database) -> None:
        from holdspeak.db.seed import apply_seed

        apply_seed(db)
        prompts = db.notes.list_by_tag("prompt")
        assert len(prompts) >= 2, f"Expected >=2 seed prompts, got {len(prompts)}"
        titles = {p.title for p in prompts}
        assert "Weekly update" in titles
        assert "1:1 prep" in titles
