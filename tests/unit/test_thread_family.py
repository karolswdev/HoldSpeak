"""HS-152-05: thread MCP family — thread.set_status writes the row,
classification, palette membership, and derive_result_kind function.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.mcp.families.thread import TOOLS, dispatch
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.thread_tools import (
    CHAT_PALETTE,
    TOOL_NAMES,
    derive_result_kind,
    tool_class,
    tool_sensitive,
)


OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "test_thread_family.db")


# ── thread.set_status ──────────────────────────────────────────────

class TestThreadSetStatus:
    """thread.set_status writes the status_line row and returns it."""

    def test_writes_status_line(self, db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("holdspeak.mcp.families.thread.get_database", lambda: db)
        thread = db.threads.create_thread(title="Test Thread")
        result = dispatch(
            "thread.set_status",
            {"thread_id": thread.id, "text": "Preparing brief..."},
            OWNER,
        )
        assert result["status_line"] == "Preparing brief..."
        assert result["thread_id"] == thread.id
        # Verify the DB row was updated
        row = db.threads.get(thread.id)
        assert row is not None
        assert row.status_line == "Preparing brief..."

    def test_clears_status_line_with_empty_string(self, db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("holdspeak.mcp.families.thread.get_database", lambda: db)
        thread = db.threads.create_thread(title="Test Thread")
        dispatch(
            "thread.set_status",
            {"thread_id": thread.id, "text": "Something"},
            OWNER,
        )
        result = dispatch(
            "thread.set_status",
            {"thread_id": thread.id, "text": ""},
            OWNER,
        )
        assert result["status_line"] == ""
        row = db.threads.get(thread.id)
        assert row is not None
        assert row.status_line == ""

    def test_rejects_missing_thread_id(self, db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("holdspeak.mcp.families.thread.get_database", lambda: db)
        from holdspeak.services.errors import ServiceError
        with pytest.raises(ServiceError, match="thread_id"):
            dispatch("thread.set_status", {"text": "hello"}, OWNER)

    def test_unknown_tool_raises_lookup_error(self, db: Database) -> None:
        with pytest.raises(LookupError):
            dispatch("thread.unknown_tool", {}, OWNER)


# ── Classification and palette ─────────────────────────────────────

class TestThreadClassification:
    """thread.set_status is classified and in the palette."""

    def test_classified_as_effect_proposal(self) -> None:
        assert tool_class("thread.set_status") == "effect_proposal"

    def test_not_sensitive(self) -> None:
        assert tool_sensitive("thread.set_status") is False

    def test_in_tool_names(self) -> None:
        assert "thread.set_status" in TOOL_NAMES

    def test_in_chat_palette(self) -> None:
        assert "thread.set_status" in CHAT_PALETTE

    def test_tools_list_has_schema(self) -> None:
        names = [t["name"] for t in TOOLS]
        assert "thread.set_status" in names
        schema = next(t for t in TOOLS if t["name"] == "thread.set_status")
        assert "inputSchema" in schema
        props = schema["inputSchema"]["properties"]
        assert "thread_id" in props
        assert "text" in props


# ── derive_result_kind ─────────────────────────────────────────────

class TestDeriveResultKind:
    """Semantic kind derivation from tool name and args."""

    def test_meeting_tools(self) -> None:
        assert derive_result_kind("meeting.get") == "meeting"
        assert derive_result_kind("meeting.list") == "meeting"

    def test_people_tools(self) -> None:
        assert derive_result_kind("people.readiness") == "person"
        assert derive_result_kind("people.relationship.list") == "person"

    def test_board_tools(self) -> None:
        assert derive_result_kind("door.get") == "board"
        assert derive_result_kind("follow_through.board") == "board"

    def test_note_tools(self) -> None:
        assert derive_result_kind("desk.list", {"kind": "notes"}) == "note"
        assert derive_result_kind("desk.get", {"kind": "notes"}) == "note"
        assert derive_result_kind("desk.create", {"kind": "notes"}) == "note"
        # Non-note desk kinds stay data
        assert derive_result_kind("desk.get", {"kind": "decisions"}) == "data"

    def test_decision_tools(self) -> None:
        assert derive_result_kind("decision_record.list") == "decision"
        assert derive_result_kind("decision_record.get") == "decision"
        assert derive_result_kind("decision.supersede") == "decision"

    def test_unknown_stays_data(self) -> None:
        assert derive_result_kind("desk.list") == "data"
        assert derive_result_kind("zone.file") == "data"
        assert derive_result_kind("memory.search") == "data"


# ── TOOL_RESULT_BYTE_CAP ──────────────────────────────────────────

class TestToolResultByteCap:
    """A dispatch returning >32 KB truncates the result text at a UTF-8
    boundary and carries truncated=True + original_bytes in the meta."""

    def test_large_result_truncated(self, db: Database) -> None:
        from holdspeak.services.thread_tools import (
            TOOL_RESULT_BYTE_CAP,
            ThreadToolExecutor,
        )

        # A dispatch that returns 200 KB of data
        large_data = {"items": [{"id": str(i), "text": "x" * 1000} for i in range(200)]}

        def big_dispatch(name: str, args: dict, principal: Any) -> Any:
            return large_data

        executor = ThreadToolExecutor(
            db,
            dispatch_fn=big_dispatch,
            principal=OWNER,
            control_mode_fn=lambda: "yolo",
        )

        thread = db.threads.create_thread(title="Cap Test")
        handle = executor.admit(
            turn_operation_id="op-cap",
            thread_id=thread.id,
            call={"id": "call-cap", "name": "desk.list", "arguments": {"kind": "notes"}},
        )
        result = executor.execute(handle)

        # Result must be truncated
        assert result.truncated is True
        assert result.original_bytes > TOOL_RESULT_BYTE_CAP

        # The serialized payload text must fit within the cap
        import json
        result_text = json.dumps(result.payload, default=str)
        from holdspeak.services.thread_tools import _truncate_utf8
        truncated_text = _truncate_utf8(result_text, TOOL_RESULT_BYTE_CAP)
        assert len(truncated_text.encode("utf-8")) <= TOOL_RESULT_BYTE_CAP

    def test_small_result_not_truncated(self, db: Database) -> None:
        from holdspeak.services.thread_tools import ThreadToolExecutor

        def small_dispatch(name: str, args: dict, principal: Any) -> Any:
            return {"items": [{"id": "1", "text": "hello"}]}

        executor = ThreadToolExecutor(
            db,
            dispatch_fn=small_dispatch,
            principal=OWNER,
            control_mode_fn=lambda: "yolo",
        )

        thread = db.threads.create_thread(title="Small Test")
        handle = executor.admit(
            turn_operation_id="op-small",
            thread_id=thread.id,
            call={"id": "call-small", "name": "desk.list", "arguments": {"kind": "notes"}},
        )
        result = executor.execute(handle)

        assert result.truncated is False
        assert result.original_bytes == 0
