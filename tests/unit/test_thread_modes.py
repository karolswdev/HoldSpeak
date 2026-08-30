"""HS-153-01/02: Thread modes (recipes with kind='mode') and notes tag query.

Seeds idempotent; kind filter; allow-lists; mode_for_thread; unknown
names fail closed; notes list_by_tag; prompt note seed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.services.thread_modes import (
    FORWARD_TOOLS,
    MODE_SEEDS,
    _CHASE_TOOLS,
    _DESK_TOOLS,
    _DRAFT_TOOLS,
    _PLAN_TOOLS,
    allowed_tools_for_thread,
    mode_for_thread,
    seed_modes,
)
from holdspeak.services.thread_tools import TOOL_NAMES


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "test_modes.db")


# ---------------------------------------------------------------------------
# Seeds idempotent
# ---------------------------------------------------------------------------

class TestSeedModes:
    def test_seed_modes_creates_four(self, db: Database) -> None:
        created = seed_modes(db)
        assert created == 4
        modes = db.recipes.list_by_kind("mode")
        assert len(modes) == 4
        names = {m.name for m in modes}
        assert names == {"Desk", "Chase", "Draft", "Plan"}

    def test_seed_modes_idempotent(self, db: Database) -> None:
        first = seed_modes(db)
        assert first == 4
        second = seed_modes(db)
        assert second == 0
        # Still exactly 4
        assert len(db.recipes.list_by_kind("mode")) == 4

    def test_seed_modes_does_not_resurrect_deleted(self, db: Database) -> None:
        seed_modes(db)
        db.recipes.delete("hs-seed-mode-desk")
        # Seed again -- should not recreate the deleted one
        created = seed_modes(db)
        assert created == 0
        live = [m for m in db.recipes.list_by_kind("mode") if not m.deleted]
        assert len(live) == 3

    def test_seed_modes_have_kind_mode(self, db: Database) -> None:
        seed_modes(db)
        for mode in db.recipes.list_by_kind("mode"):
            assert mode.kind == "mode"

    def test_seed_ids_are_deterministic(self, db: Database) -> None:
        seed_modes(db)
        ids = {m.id for m in db.recipes.list_by_kind("mode")}
        assert ids == {
            "hs-seed-mode-desk",
            "hs-seed-mode-chase",
            "hs-seed-mode-draft",
            "hs-seed-mode-plan",
        }


# ---------------------------------------------------------------------------
# Kind filter on recipes
# ---------------------------------------------------------------------------

class TestKindFilter:
    def test_list_by_kind_returns_only_modes(self, db: Database) -> None:
        seed_modes(db)
        # Create an ordinary recipe
        db.recipes.upsert(recipe_id="test-ordinary", name="Ordinary")
        modes = db.recipes.list_by_kind("mode")
        assert all(m.kind == "mode" for m in modes)
        assert len(modes) == 4

    def test_list_by_kind_empty_returns_ordinary(self, db: Database) -> None:
        seed_modes(db)
        db.recipes.upsert(recipe_id="test-ordinary", name="Ordinary")
        ordinary = db.recipes.list_by_kind("")
        assert len(ordinary) == 1
        assert ordinary[0].id == "test-ordinary"

    def test_kind_persisted_on_upsert(self, db: Database) -> None:
        db.recipes.upsert(recipe_id="custom-mode", name="Custom", kind="mode")
        rec = db.recipes.get("custom-mode")
        assert rec is not None
        assert rec.kind == "mode"


# ---------------------------------------------------------------------------
# Allow-lists: sizes and fail-closed
# ---------------------------------------------------------------------------

class TestAllowLists:
    def test_desk_size(self) -> None:
        assert len(_DESK_TOOLS) == 55

    def test_chase_size(self) -> None:
        # Chase includes door.add_item which is a forward reference
        assert len(_CHASE_TOOLS) == 61

    def test_draft_empty(self) -> None:
        assert len(_DRAFT_TOOLS) == 0

    def test_plan_size(self) -> None:
        assert len(_PLAN_TOOLS) == 7

    def test_desk_is_subset_of_chase(self) -> None:
        assert _DESK_TOOLS < _CHASE_TOOLS

    def test_plan_is_subset_of_desk(self) -> None:
        assert _PLAN_TOOLS < _DESK_TOOLS

    def test_every_seed_name_exists_in_tool_names_or_forward(self) -> None:
        """Fail-closed: every name in every seed mode's allow-list must exist
        in TOOL_NAMES, except forward references in FORWARD_TOOLS."""
        for mode in MODE_SEEDS:
            unknown = mode.tools - TOOL_NAMES - FORWARD_TOOLS
            assert unknown == set(), (
                f"Mode {mode.name!r} references tools not in TOOL_NAMES or "
                f"FORWARD_TOOLS: {sorted(unknown)}"
            )

    def test_forward_tools_are_declared_not_in_tool_names(self) -> None:
        """Forward references must NOT be in TOOL_NAMES yet.
        When a forward tool lands in TOOL_NAMES, remove it from FORWARD_TOOLS."""
        for name in FORWARD_TOOLS:
            assert name not in TOOL_NAMES, (
                f"{name} is in TOOL_NAMES -- remove it from FORWARD_TOOLS"
            )

    def test_forward_tools_empty_when_all_landed(self) -> None:
        """When all forward tools have landed, FORWARD_TOOLS should be empty."""
        # door.add_item landed in HS-153-05
        assert FORWARD_TOOLS == frozenset()


# ---------------------------------------------------------------------------
# mode_for_thread and allowed_tools_for_thread
# ---------------------------------------------------------------------------

class TestModeForThread:
    def test_no_recipe_returns_none(self, db: Database) -> None:
        thread = db.threads.create_thread(title="No recipe")
        assert mode_for_thread(db, thread.id) is None

    def test_ordinary_recipe_returns_none(self, db: Database) -> None:
        db.recipes.upsert(recipe_id="r1", name="Agent")
        thread = db.threads.create_thread(title="Ordinary", recipe_id="r1")
        assert mode_for_thread(db, thread.id) is None

    def test_mode_recipe_returns_mode(self, db: Database) -> None:
        seed_modes(db)
        thread = db.threads.create_thread(
            title="Mode", recipe_id="hs-seed-mode-desk"
        )
        mode = mode_for_thread(db, thread.id)
        assert mode is not None
        assert mode.name == "Desk"
        assert mode.id == "hs-seed-mode-desk"

    def test_nonexistent_thread_returns_none(self, db: Database) -> None:
        assert mode_for_thread(db, "nonexistent") is None


class TestAllowedToolsForThread:
    def test_no_mode_defaults_to_desk(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Default")
        tools = allowed_tools_for_thread(db, thread.id)
        # Desk intersected with TOOL_NAMES = Desk (all Desk names are in TOOL_NAMES)
        assert tools == _DESK_TOOLS & TOOL_NAMES

    def test_chase_mode_includes_effects(self, db: Database) -> None:
        seed_modes(db)
        thread = db.threads.create_thread(
            title="Chase", recipe_id="hs-seed-mode-chase"
        )
        tools = allowed_tools_for_thread(db, thread.id)
        assert "people.commitment.transition" in tools
        assert "follow_through.complete" in tools
        # door.add_item landed in HS-153-05
        assert "door.add_item" in tools

    def test_draft_mode_empty(self, db: Database) -> None:
        seed_modes(db)
        thread = db.threads.create_thread(
            title="Draft", recipe_id="hs-seed-mode-draft"
        )
        tools = allowed_tools_for_thread(db, thread.id)
        assert tools == frozenset()

    def test_plan_mode_subset(self, db: Database) -> None:
        seed_modes(db)
        thread = db.threads.create_thread(
            title="Plan", recipe_id="hs-seed-mode-plan"
        )
        tools = allowed_tools_for_thread(db, thread.id)
        assert "thought.get_default_context" in tools
        assert "door.get" in tools
        assert "memory.search" in tools
        assert "desk.list" not in tools


# ---------------------------------------------------------------------------
# Notes tag query
# ---------------------------------------------------------------------------

class TestNotesListByTag:
    def test_list_by_tag_returns_matching(self, db: Database) -> None:
        db.notes.upsert(note_id="n1", title="Prompt A", tags=["prompt"])
        db.notes.upsert(note_id="n2", title="Regular", tags=["other"])
        db.notes.upsert(note_id="n3", title="Prompt B", tags=["prompt", "other"])
        results = db.notes.list_by_tag("prompt")
        ids = {n.id for n in results}
        assert ids == {"n1", "n3"}

    def test_list_by_tag_empty_tag_returns_empty(self, db: Database) -> None:
        db.notes.upsert(note_id="n1", title="Prompt A", tags=["prompt"])
        assert db.notes.list_by_tag("") == []

    def test_list_by_tag_no_match(self, db: Database) -> None:
        db.notes.upsert(note_id="n1", title="Note", tags=["other"])
        assert db.notes.list_by_tag("nonexistent") == []

    def test_list_by_tag_excludes_deleted(self, db: Database) -> None:
        db.notes.upsert(note_id="n1", title="Prompt", tags=["prompt"])
        db.notes.delete("n1")
        assert db.notes.list_by_tag("prompt") == []
        # include_deleted returns it
        assert len(db.notes.list_by_tag("prompt", include_deleted=True)) == 1


# ---------------------------------------------------------------------------
# Prompt note seed
# ---------------------------------------------------------------------------

class TestPromptNoteSeed:
    def test_weekly_update_seed_exists(self, db: Database) -> None:
        from holdspeak.db.seed import apply_seed
        apply_seed(db)
        results = db.notes.list_by_tag("prompt")
        assert len(results) >= 1
        titles = {n.title for n in results}
        assert "Weekly update" in titles

    def test_weekly_update_seed_is_idempotent(self, db: Database) -> None:
        from holdspeak.db.seed import apply_seed
        apply_seed(db)
        apply_seed(db)
        results = db.notes.list_by_tag("prompt")
        assert len([n for n in results if n.title == "Weekly update"]) == 1
