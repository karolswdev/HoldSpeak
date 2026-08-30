"""HS-153-05 -- Thread todo: /todo → door.add_item through the ThreadToolExecutor.

Tests that the todo route goes through the SAME executor path as a model
call: receipt row, tool_call part, correct source_type/source_ref on the
action_items row, and safe/yolo control mode handling.

Scoped: this file + test_thread_compaction.py + test_hs153_practice_capabilities.py.
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.db.core import Database
from holdspeak.kernel.inference_stream import Delta
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.thread_service import ThreadService


OWNER = Principal(PrincipalKind.OWNER, "todo-test-owner")


# ---------------------------------------------------------------------------
# Hub helper (same pattern as test_thread_guardrail.py)
# ---------------------------------------------------------------------------


def _hub(
    tmp_path: Path,
    *,
    control_mode: str = "yolo",
):
    """Boot a real hub for todo tests."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = Path(tempfile.mkdtemp(prefix="hs153-todo-"))
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
    from holdspeak.services.thread_modes import seed_modes, seed_guardrails
    seed_modes(db)
    seed_guardrails(db)

    # Set up profile + assignments
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    owner = Principal(PrincipalKind.OWNER, "owner-session")
    profile_id = "todo-test"
    _profile(db, profile_id, claims=("language", _result_claim("chat.turn")))
    InferenceAssignmentService(db).set_assignment(owner, {
        "command_id": "assign-turn",
        "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })

    from holdspeak.db.reconcile import _backfill_chat_practice_assignments
    with db._connection() as conn:
        _backfill_chat_practice_assignments(conn)

    from holdspeak.kernel.runtime import _service as _kernel_service
    broker = _kernel_service()

    class _TurnEngine:
        active_provider = "turn-engine"
        active_model = "turn-model"

        def run_prompt_stream(self, *, messages=None, **kw):
            yield Delta(kind="text", text="OK")
            yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 1})
            yield Delta(kind="done")

        def run_prompt_messages(self, **kw):
            return "OK"

        def run_prompt(self, **kw):
            return "OK"

    broker.inference_runner._engine_factory = lambda rev, **kw: _TurnEngine()

    from holdspeak.mcp.tools import dispatch as mcp_dispatch
    broadcasts: list[tuple[str, dict]] = []
    svc = ThreadService(
        db,
        broadcast=lambda t, d: broadcasts.append((t, d)),
        broker=broker,
        tool_dispatch_fn=mcp_dispatch,
        control_mode_fn=lambda: control_mode,
    )

    return {
        "db": db,
        "svc": svc,
        "broadcasts": broadcasts,
        "owner": owner,
        "server": server,
        "old_home": old_home,
    }


def _wait_done(db, msg_id, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        msg = db.threads.get_message(msg_id)
        if msg and not msg.streaming:
            return
        time.sleep(0.2)
    pytest.fail("Turn did not complete within timeout")


def _cleanup(hub):
    from holdspeak.db import reset_database
    hub["server"].stop()
    os.environ["HOME"] = hub["old_home"]
    reset_database()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTodoYolo:
    """In yolo mode, /todo → door.add_item executes immediately."""

    def test_todo_creates_action_item_with_thread_source(self, tmp_path: Path) -> None:
        hub = _hub(tmp_path, control_mode="yolo")
        try:
            svc = hub["svc"]
            db = hub["db"]
            owner = hub["owner"]

            thread = svc.create(title="todo test")
            tid = thread["id"]

            # Create a turn so there's a message to reference
            r1 = asyncio.run(svc.start_turn(owner, tid, "Plan the party"))
            _wait_done(db, r1["assistant_message_id"])

            # Execute /todo
            result = asyncio.run(svc.todo_from_thread(owner, tid, "buy the cake"))
            assert result["status"] == "ok"
            assert result.get("receipt_id")

            # Check action_items row
            with db._connection() as conn:
                row = conn.execute(
                    "SELECT * FROM action_items WHERE task='buy the cake'",
                ).fetchone()
                assert row is not None, "action_items row not found"
                assert row["source_type"] == "thread"
                assert row["source_ref"].startswith("thread:")
                assert row["meeting_id"] is None

        finally:
            _cleanup(hub)

    def test_todo_receipt_row_in_thread(self, tmp_path: Path) -> None:
        """The thread gets a system message with a tool_call part (receipt)."""
        hub = _hub(tmp_path, control_mode="yolo")
        try:
            svc = hub["svc"]
            db = hub["db"]
            owner = hub["owner"]

            thread = svc.create(title="receipt test")
            tid = thread["id"]

            r1 = asyncio.run(svc.start_turn(owner, tid, "Plan"))
            _wait_done(db, r1["assistant_message_id"])

            result = asyncio.run(svc.todo_from_thread(owner, tid, "send invites"))
            assert result["status"] == "ok"

            # Check that a system message with tool_call part exists
            path = db.threads.list_path(tid)
            system_msgs = [m for m in path if m.role == "system"]
            assert len(system_msgs) >= 1

            found_tool_call = False
            for msg in system_msgs:
                parts = db.threads.get_parts(msg.id)
                for part in parts:
                    if part.kind == "tool_call":
                        meta = json.loads(part.meta_json)
                        if meta.get("name") == "door.add_item":
                            found_tool_call = True
                            break
            assert found_tool_call, "No tool_call part for door.add_item found"

            # Check tool result frame was emitted
            result_frames = [
                d for t, d in hub["broadcasts"] if t == "thread_tool_result"
            ]
            assert len(result_frames) >= 1
            rf = result_frames[-1]
            assert rf["name"] == "door.add_item"
            assert rf["outcome"] == "succeeded"

        finally:
            _cleanup(hub)

    def test_todo_empty_text_raises(self, tmp_path: Path) -> None:
        hub = _hub(tmp_path, control_mode="yolo")
        try:
            svc = hub["svc"]
            thread = svc.create(title="empty todo")
            from holdspeak.services.errors import ValidationError
            with pytest.raises(ValidationError, match="Todo text must not be empty"):
                asyncio.run(svc.todo_from_thread(hub["owner"], thread["id"], "  "))
        finally:
            _cleanup(hub)

    def test_todo_source_ref_uses_latest_content_message(self, tmp_path: Path) -> None:
        """source_ref points to the latest user/assistant message."""
        hub = _hub(tmp_path, control_mode="yolo")
        try:
            svc = hub["svc"]
            db = hub["db"]
            owner = hub["owner"]

            thread = svc.create(title="ref test")
            tid = thread["id"]

            r1 = asyncio.run(svc.start_turn(owner, tid, "Hello"))
            _wait_done(db, r1["assistant_message_id"])
            r2 = asyncio.run(svc.start_turn(owner, tid, "World"))
            _wait_done(db, r2["assistant_message_id"])

            result = asyncio.run(svc.todo_from_thread(owner, tid, "check results"))
            assert result["status"] == "ok"

            with db._connection() as conn:
                row = conn.execute(
                    "SELECT source_ref FROM action_items WHERE task='check results'",
                ).fetchone()
                assert row is not None
                # Should reference the assistant message from the second turn
                # (the latest content message on the path)
                assert row["source_ref"] == f"thread:{r2['assistant_message_id']}"

        finally:
            _cleanup(hub)


class TestTodoSafe:
    """In safe mode, effect_proposal tools go through the pending/decision box."""

    def test_todo_safe_mode_holds_for_decision(self, tmp_path: Path) -> None:
        """Safe mode: door.add_item is effect_proposal → held → emits pending frame."""
        hub = _hub(tmp_path, control_mode="safe")
        try:
            svc = hub["svc"]
            db = hub["db"]
            owner = hub["owner"]

            thread = svc.create(title="safe todo")
            tid = thread["id"]

            r1 = asyncio.run(svc.start_turn(owner, tid, "Plan"))
            _wait_done(db, r1["assistant_message_id"])

            # Run todo in a thread since it will block waiting for decision
            import threading
            todo_result: dict[str, Any] = {}
            todo_error: list[Exception] = []

            def _run_todo():
                try:
                    todo_result.update(asyncio.run(
                        svc.todo_from_thread(owner, tid, "buy cake")
                    ))
                except Exception as e:
                    todo_error.append(e)

            bg = threading.Thread(target=_run_todo, daemon=True)
            bg.start()

            # Wait for pending frame
            deadline = time.monotonic() + 10
            pending_frames = []
            while time.monotonic() < deadline:
                pending_frames = [
                    d for t, d in hub["broadcasts"] if t == "thread_tool_pending"
                ]
                if pending_frames:
                    break
                time.sleep(0.1)

            assert len(pending_frames) >= 1, (
                f"Expected pending frame, got: {[t for t, _ in hub['broadcasts']]}"
            )
            pf = pending_frames[-1]
            assert pf["name"] == "door.add_item"
            assert pf["decision_required"] is True

            # Approve the decision
            call_id = pf["call_id"]
            handles = svc._tool_executor._handles
            if call_id in handles:
                handle = handles[call_id]
                # Find the executor and decide
                for ex in svc._tool_executor._executors.values():
                    if call_id in ex._handles:
                        ex.decide(ex._handles[call_id], "approve")
                        break

            bg.join(timeout=10)
            assert not todo_error, f"Todo raised: {todo_error}"
            assert todo_result.get("status") == "ok"

            # Check the action_items row was created
            with db._connection() as conn:
                row = conn.execute(
                    "SELECT * FROM action_items WHERE task='buy cake'",
                ).fetchone()
                assert row is not None

        finally:
            _cleanup(hub)


class TestTodoProvenance:
    """The Door board surfaces thread-sourced items with provenance."""

    def test_follow_through_service_thread_provenance(self, tmp_path: Path) -> None:
        """An action item with source_type='thread' gets CardProvenance.thread_id."""
        db = Database(tmp_path / "prov.db")
        from holdspeak.services.follow_through_service import FollowThroughService
        fts = FollowThroughService(db)

        # Insert an action item with thread source
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO action_items
                   (id, meeting_id, task, owner, due, status, review_state,
                    created_at, source_type, source_ref)
                   VALUES (?, NULL, ?, NULL, NULL, 'open', 'accepted', ?, ?, ?)""",
                ("ai_test1", "buy the cake", "2026-08-30T00:00:00", "thread", "thread:tm_abc123"),
            )

        board = fts.board(OWNER)
        all_cards = list(board.now) + list(board.waiting) + list(board.unassigned) + list(board.overdue)
        thread_cards = [c for c in all_cards if c.provenance and c.provenance.thread_id]
        assert len(thread_cards) >= 1, (
            f"Expected at least one card with thread_id provenance, "
            f"got: {[(c.id, c.provenance) for c in all_cards]}"
        )
        card = thread_cards[0]
        assert card.provenance.thread_id == "tm_abc123"
        assert card.provenance.available is True


class TestActionItemsListingDefect:
    """HS-153-06: list_action_items and get_action_item must return
    thread-sourced items whose meeting_id is NULL.

    Before the fix, the INNER JOIN on meetings excluded NULL meeting_id rows.
    """

    def test_list_action_items_includes_thread_sourced(self, tmp_path: Path) -> None:
        hub = _hub(tmp_path, control_mode="yolo")
        try:
            db = hub["db"]
            # Insert a thread-sourced action item directly (NULL meeting_id).
            with db._connection() as conn:
                conn.execute(
                    """INSERT INTO action_items
                       (id, meeting_id, task, owner, due, status, review_state,
                        created_at, source_type, source_ref)
                       VALUES (?, NULL, ?, NULL, NULL, 'open', 'accepted', ?, ?, ?)""",
                    ("ai_list_test", "Thread task", "2026-08-30T00:00:00",
                     "thread", "thread:tm_list"),
                )

            items = db.meetings.list_action_items(include_completed=True)
            thread_items = [it for it in items if it.source_type == "thread"]
            assert len(thread_items) >= 1, (
                f"Expected thread-sourced item in list, got {len(thread_items)}"
            )
            assert thread_items[0].meeting_id == ""
            assert thread_items[0].source_ref == "thread:tm_list"
        finally:
            _cleanup(hub)

    def test_get_action_item_finds_thread_sourced(self, tmp_path: Path) -> None:
        hub = _hub(tmp_path, control_mode="yolo")
        try:
            db = hub["db"]
            with db._connection() as conn:
                conn.execute(
                    """INSERT INTO action_items
                       (id, meeting_id, task, owner, due, status, review_state,
                        created_at, source_type, source_ref)
                       VALUES (?, NULL, ?, NULL, NULL, 'open', 'accepted', ?, ?, ?)""",
                    ("ai_get_test", "Find me", "2026-08-30T00:00:00",
                     "thread", "thread:tm_get"),
                )

            item = db.meetings.get_action_item("ai_get_test")
            assert item is not None, "get_action_item returned None for thread-sourced item"
            assert item.task == "Find me"
            assert item.source_type == "thread"
            assert item.meeting_id == ""
        finally:
            _cleanup(hub)
