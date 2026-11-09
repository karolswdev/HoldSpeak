# PARKED 2026-11-09 (fences diet, pipe/fences-diet): palette SIZES, a count edited on every legitimate tool change.
# Replaced by tests/unit/test_thread_modes.py::TestAllowLists::test_each_palette_holds_only_its_classes.
"""Parked from tests/unit/test_thread_modes.py (TestAllowLists)."""
from holdspeak.services.thread_modes import _CHASE_TOOLS, _DESK_TOOLS, _PLAN_TOOLS


class TestAllowListSizes:
    def test_desk_size(self) -> None:
        # HS-168-02: + connection.list / connection.recheck (evidence_read).
        # HS-170: + concierge.detect/propose/probe, desk.needs_you, settings.hub.
        # HS-171: + heartbeat.status (evidence_read).
        # HS-172 + HS-173: meeting.proposals, project.suggested_sources, steward.nudges.
        # PHILO-5-02: + monday_brief.shelf_read; PHILO-7-02: + kernel.receipt
        # (both evidence_read; the receipt is declared in the DESK palette,
        # tests/unit/test_philo7_article_xi.py).
        assert {"monday_brief.shelf_read", "kernel.receipt"} <= _DESK_TOOLS
        # #694 (the owner's ruling): connection.recheck is WORK (a read of his
        # connection), so Desk keeps it (mcp/tool_authority.py).
        assert "connection.recheck" in _DESK_TOOLS
        # Memory slice 4: + memory.observations (evidence_read).
        assert "memory.observations" in _DESK_TOOLS
        # Memory slice 6: + memory.page (evidence_read; MCP only in slice 5).
        assert "memory.page" in _DESK_TOOLS
        # Watch fold 4 (#2007): - event.list, reaction.list, reaction.presets,
        # watch.list, watch.preview (parked with ReactionService).
        assert len(_DESK_TOOLS) == 65

    def test_chase_size(self) -> None:
        # Chase includes door.add_item which is a forward reference
        # HS-168-02: + connection.list / connection.recheck (evidence_read).
        # HS-170: + concierge.detect/propose/probe, desk.needs_you, settings.hub.
        # HS-171: + heartbeat.status (evidence_read).
        # HS-172 + HS-173: meeting.proposals, project.suggested_sources, steward.nudges.
        # PHILO-5-02 + PHILO-7-02: + monday_brief.shelf_read, kernel.receipt (via Desk).
        # #694: unchanged; people.note.create is WORK and stays (the ruling).
        assert "people.note.create" in _CHASE_TOOLS
        # Memory slice 4: + memory.observations (via Desk).
        # Memory slice 6: + memory.page (via Desk).
        assert "memory.page" in _CHASE_TOOLS
        # Watch fold 4 (#2007): the five parked Desk reads leave Chase too.
        assert len(_CHASE_TOOLS) == 71

    def test_plan_size(self) -> None:
        # Memory slice 6: memory.page is not in Plan (its palette may not grow).
        assert len(_PLAN_TOOLS) == 7

