# PARKED 2026-11-08 (HS-S56): the tests of the parked allowed_tools_for_thread
# (parked/holdspeak/services/thread_modes_allowed_tools.py). The bound-mode
# cases stay live as TestPaletteFor in tests/unit/test_thread_modes.py.
from __future__ import annotations

from holdspeak.db import Database
from holdspeak.services.thread_modes import _DESK_TOOLS, seed_modes
from holdspeak.services.thread_tools import TOOL_NAMES
from parked.holdspeak.services.thread_modes_allowed_tools import allowed_tools_for_thread


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
