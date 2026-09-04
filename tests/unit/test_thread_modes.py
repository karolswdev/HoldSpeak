"""HS-153-01/02: Thread modes (recipes with kind='mode') and notes tag query.

Seeds idempotent; kind filter; allow-lists; mode_for_thread; palette_for;
unknown names fail closed; notes list_by_tag; prompt note seed.
"""
from __future__ import annotations

import logging
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
    _warned_modes,
    allowed_tools_for_thread,
    mode_for_thread,
    palette_for,
    seed_modes,
)
from holdspeak.services.thread_tools import CHAT_PALETTE, TOOL_NAMES


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "test_modes.db")


# ---------------------------------------------------------------------------
# Seeds idempotent
# ---------------------------------------------------------------------------

class TestSeedModes:
    def test_seed_modes_creates_four(self, db: Database) -> None:
        created = seed_modes(db)
        assert created == 5
        modes = db.recipes.list_by_kind("mode")
        assert len(modes) == 5
        names = {m.name for m in modes}
        assert names == {"Desk", "Chase", "Draft", "Plan", "Project"}

    def test_seed_modes_idempotent(self, db: Database) -> None:
        first = seed_modes(db)
        assert first == 5
        second = seed_modes(db)
        assert second == 0
        # Still exactly 4
        assert len(db.recipes.list_by_kind("mode")) == 5

    def test_seed_modes_does_not_resurrect_deleted(self, db: Database) -> None:
        seed_modes(db)
        db.recipes.delete("hs-seed-mode-desk")
        # Seed again -- should not recreate the deleted one
        created = seed_modes(db)
        assert created == 0
        live = [m for m in db.recipes.list_by_kind("mode") if not m.deleted]
        assert len(live) == 4

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
            "hs-seed-mode-plan", "hs-seed-mode-project"}


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
        assert len(modes) == 5

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
        # HS-168-02: + connection.list / connection.recheck (evidence_read).
        assert len(_DESK_TOOLS) == 57

    def test_chase_size(self) -> None:
        # Chase includes door.add_item which is a forward reference
        # HS-168-02: + connection.list / connection.recheck (evidence_read).
        assert len(_CHASE_TOOLS) == 63

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
# palette_for (HS-153-01)
# ---------------------------------------------------------------------------

class TestPaletteFor:
    def test_no_mode_returns_none(self, db: Database) -> None:
        """No mode bound -> palette_for returns None (caller uses CHAT_PALETTE)."""
        thread = db.threads.create_thread(title="Bare")
        assert palette_for(db, thread.id) is None

    def test_desk_mode_returns_desk_palette(self, db: Database) -> None:
        seed_modes(db)
        thread = db.threads.create_thread(
            title="Desk", recipe_id="hs-seed-mode-desk"
        )
        palette = palette_for(db, thread.id)
        assert palette is not None
        assert palette == _DESK_TOOLS & TOOL_NAMES

    def test_draft_mode_returns_empty(self, db: Database) -> None:
        """Draft mode -> empty frozenset (caller omits tools key)."""
        seed_modes(db)
        thread = db.threads.create_thread(
            title="Draft", recipe_id="hs-seed-mode-draft"
        )
        palette = palette_for(db, thread.id)
        assert palette is not None
        assert palette == frozenset()

    def test_chase_contains_effects_not_desk_delete(self, db: Database) -> None:
        seed_modes(db)
        thread = db.threads.create_thread(
            title="Chase", recipe_id="hs-seed-mode-chase"
        )
        palette = palette_for(db, thread.id)
        assert palette is not None
        assert "people.commitment.transition" in palette
        assert "desk.delete" not in palette

    def test_custom_mode_unclassified_tool_dropped_and_logged(
        self, db: Database, caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Unclassified names in a custom mode are dropped and logged ONCE."""
        _warned_modes.discard("custom-bad-tool")
        db.recipes.upsert(
            recipe_id="custom-bad-tool",
            name="BadMode",
            kind="mode",
            tools=["desk.list", "totally.fake.tool", "another.bogus"],
        )
        thread = db.threads.create_thread(
            title="Custom", recipe_id="custom-bad-tool"
        )
        with caplog.at_level(logging.WARNING, logger="holdspeak.services.thread_modes"):
            palette = palette_for(db, thread.id)
        assert palette is not None
        assert "desk.list" in palette
        assert "totally.fake.tool" not in palette
        assert "another.bogus" not in palette
        # Check the warning was logged
        assert any("totally.fake.tool" in r.message for r in caplog.records)

        # Second call: no duplicate warning
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger="holdspeak.services.thread_modes"):
            palette2 = palette_for(db, thread.id)
        assert palette2 == palette
        assert not any("totally.fake.tool" in r.message for r in caplog.records)
        _warned_modes.discard("custom-bad-tool")

    def test_ordinary_recipe_returns_none(self, db: Database) -> None:
        """A non-mode recipe does not produce a palette."""
        db.recipes.upsert(recipe_id="agent-x", name="Agent X")
        thread = db.threads.create_thread(
            title="Agent", recipe_id="agent-x"
        )
        assert palette_for(db, thread.id) is None


# ---------------------------------------------------------------------------
# Seed on a fresh Database (HS-153-01 acceptance criterion 6)
# ---------------------------------------------------------------------------

class TestSeedOnFreshDatabase:
    def test_fresh_database_gets_four_modes(self, tmp_path: Path) -> None:
        """The owner's real DB gets the four modes without a migration:
        seed_modes runs on Database() + reconcile-time ensure."""
        fresh = Database(tmp_path / "fresh.db")
        created = seed_modes(fresh)
        assert created == 5
        modes = fresh.recipes.list_by_kind("mode")
        assert len(modes) == 5
        names = {m.name for m in modes}
        assert names == {"Desk", "Chase", "Draft", "Plan", "Project"}
        # Verify kind and avatar
        for m in modes:
            assert m.kind == "mode"
            assert m.avatar.startswith("#")


# ---------------------------------------------------------------------------
# Real coordinator + fake engine: palette seam (HS-153-01 acceptance)
# ---------------------------------------------------------------------------

class TestRealCoordinatorModePalette:
    """Drives ThreadService through the REAL RoutedInferenceCoordinator with a
    fake engine that captures the admitted payload.  Asserts:
    - Draft -> no ``tools`` key at all, one pass
    - Chase -> palette contains ``people.commitment.transition``, not ``desk.delete``
    - Mid-turn switch changes nothing until the next turn
    """

    @staticmethod
    def _hub(tmp_path: Path):
        """Boot a real hub, seed modes, return (db, svc, broker, engine)."""
        import os
        import tempfile
        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database, get_database
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.kernel.inference_stream import Delta

        home = Path(tempfile.mkdtemp(prefix="hs153-mode-"))
        old_home = os.environ.get("HOME", "")
        os.environ["HOME"] = str(home)
        config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
        db_core.DEFAULT_DB_PATH = tmp_path / "holdspeak.db"
        reset_database()

        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None,
                on_stop=lambda: None,
                get_state=lambda: {},
            ),
        )
        url = server.start()
        db = get_database()

        # Seed modes
        from holdspeak.services.thread_modes import seed_modes as _seed_modes
        _seed_modes(db)

        # Set up profile + assignment for chat.turn
        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        owner = Principal(PrincipalKind.OWNER, "owner-session")
        profile_id = "mode-palette-test"
        _profile(db, profile_id, claims=("language", _result_claim("chat.turn")))
        InferenceAssignmentService(db).set_assignment(owner, {
            "command_id": "mode-assign",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        })

        from holdspeak.kernel.runtime import _service as _kernel_service
        broker = _kernel_service()

        # Fake engine that captures the payload
        payloads: list[dict] = []

        class _CapturingEngine:
            active_provider = "capture-engine"
            active_model = "capture-model"

            def run_prompt_stream(self, *, messages=None, temperature=None,
                                  max_tokens=None, tools=None, **kw):
                payloads.append({
                    "messages": messages,
                    "tools": tools,
                    "kw": kw,
                })
                yield Delta(kind="text", text="OK ")
                yield Delta(kind="usage", meta={"prompt_tokens": 1, "completion_tokens": 1})
                yield Delta(kind="done")

            def run_prompt_messages(self, **kw):
                return "OK"

            def run_prompt(self, **kw):
                return "OK"

        engine = _CapturingEngine()
        broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

        from holdspeak.services.thread_service import ThreadService
        from holdspeak.mcp.tools import dispatch as mcp_dispatch
        broadcasts: list[tuple[str, dict]] = []
        svc = ThreadService(
            db,
            broadcast=lambda t, d: broadcasts.append((t, d)),
            broker=broker,
            tool_dispatch_fn=mcp_dispatch,
        )

        return db, svc, payloads, broadcasts, owner, server, old_home

    @staticmethod
    def _wait_done(db, msg_id, timeout=15):
        import time
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = db.threads.get_message(msg_id)
            if msg and not msg.streaming:
                return
            time.sleep(0.2)
        pytest.fail("Turn did not complete within timeout")

    def test_draft_mode_no_tools_key(self, tmp_path: Path) -> None:
        """Draft mode -> admitted payload has no ``tools`` key."""
        import asyncio
        from holdspeak.db import reset_database

        db, svc, payloads, broadcasts, owner, server, old_home = self._hub(tmp_path)
        try:
            thread = svc.create(title="Draft test", recipe_id="hs-seed-mode-draft")
            result = asyncio.run(svc.start_turn(owner, thread["id"], "Write freely"))
            self._wait_done(db, result["assistant_message_id"])

            assert len(payloads) >= 1, "Engine was not called"
            first_payload = payloads[0]
            assert first_payload["tools"] is None or first_payload["tools"] == [], (
                f"Draft should not have tools, got: {first_payload['tools']!r}"
            )
            server.stop()
        finally:
            import os
            os.environ["HOME"] = old_home
            reset_database()

    def test_chase_mode_palette_contains_people_not_desk_delete(
        self, tmp_path: Path,
    ) -> None:
        """Chase mode -> palette has people.commitment.transition, not desk.delete."""
        import asyncio
        from holdspeak.db import reset_database

        db, svc, payloads, broadcasts, owner, server, old_home = self._hub(tmp_path)
        try:
            thread = svc.create(title="Chase test", recipe_id="hs-seed-mode-chase")
            result = asyncio.run(svc.start_turn(owner, thread["id"], "Chase work"))
            self._wait_done(db, result["assistant_message_id"])

            assert len(payloads) >= 1, "Engine was not called"
            first_payload = payloads[0]
            tools = first_payload["tools"]
            assert tools is not None and len(tools) > 0, "Chase should have tools"
            tool_names = {t["function"]["name"] for t in tools}
            assert "people.commitment.transition" in tool_names
            assert "desk.delete" not in tool_names
            server.stop()
        finally:
            import os
            os.environ["HOME"] = old_home
            reset_database()

    def test_mid_turn_switch_does_not_affect_in_flight(
        self, tmp_path: Path,
    ) -> None:
        """A mid-turn PATCH to switch modes does not change the in-flight palette.
        The palette is resolved at admission; switching changes the NEXT turn."""
        import asyncio
        import time
        from holdspeak.db import reset_database
        from holdspeak.kernel.inference_stream import Delta

        db, svc, payloads, broadcasts, owner, server, old_home = self._hub(tmp_path)
        try:
            # Start with Chase mode
            thread = svc.create(title="Mid-turn test", recipe_id="hs-seed-mode-chase")
            tid = thread["id"]

            # Start a turn
            result = asyncio.run(svc.start_turn(owner, tid, "First turn"))
            self._wait_done(db, result["assistant_message_id"])

            assert len(payloads) >= 1
            turn1_tools = payloads[0]["tools"]
            assert turn1_tools is not None
            turn1_names = {t["function"]["name"] for t in turn1_tools}
            assert "people.commitment.transition" in turn1_names

            # Switch to Draft mid-flight (between turns, since we can't
            # truly patch during streaming in a unit test; the point is
            # the palette was already resolved at turn1 admission).
            db.threads.patch(tid, recipe_id="hs-seed-mode-draft")

            # Start turn 2 -- this should use Draft's palette (no tools)
            payloads.clear()
            result2 = asyncio.run(svc.start_turn(owner, tid, "Second turn"))
            self._wait_done(db, result2["assistant_message_id"])

            assert len(payloads) >= 1
            turn2_tools = payloads[0]["tools"]
            # Draft: no tools
            assert turn2_tools is None or turn2_tools == [], (
                f"After switching to Draft, tools should be empty: {turn2_tools!r}"
            )
            server.stop()
        finally:
            import os
            os.environ["HOME"] = old_home
            reset_database()


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
