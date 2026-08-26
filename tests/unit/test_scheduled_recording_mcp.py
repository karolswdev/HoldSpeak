"""HS-136-02: MCP tool tests for scheduled recording CRUD + cancel-armed.

Tests the same operations through the MCP tool layer, with identical
refusals to the HTTP path.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.mcp import server
from holdspeak.mcp import tools as mcp_tools
from holdspeak.mcp.server import handle_message
from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Database:
    return Database(db_path=tmp_path / "test.db")


@pytest.fixture(autouse=True)
def _patch_mcp(tmp_db: Database, monkeypatch: Any) -> None:
    monkeypatch.setattr(mcp_tools, "get_database", lambda: tmp_db)
    monkeypatch.setattr(mcp_tools, "get_observer", lambda: None)
    monkeypatch.setattr(
        server, "resolve_auth",
        lambda: SimpleNamespace(principal=Principal(PrincipalKind.OWNER, "test")),
    )
    # Stub out services that dispatch builds but scheduled_recording tools never use
    monkeypatch.setattr(mcp_tools, "MeetingService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "DictationService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "DeskService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "DecisionRecordService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "EventQueryService", lambda db: object())
    monkeypatch.setattr(mcp_tools, "FollowThroughService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "MondayBriefService", lambda db, **kw: object())


def _call(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    response = handle_message({
        "jsonrpc": "2.0", "id": name, "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    })
    assert response is not None
    result = response["result"]
    return {
        "value": json.loads(result["content"][0]["text"]),
        "isError": result["isError"],
    }


def _call_ok(name: str, arguments: dict[str, Any] | None = None) -> Any:
    result = _call(name, arguments)
    assert result["isError"] is False, f"Expected success, got error: {result['value']}"
    return result["value"]


def _call_error(name: str, arguments: dict[str, Any] | None = None) -> str:
    result = _call(name, arguments)
    assert result["isError"] is True, f"Expected error, got success: {result['value']}"
    return result["value"].get("error", str(result["value"]))


class TestScheduledRecordingToolsCatalogue:
    """The five scheduled_recording tools appear in the tool list."""

    def test_tool_names_in_catalogue(self) -> None:
        response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        assert response is not None
        names = {t["name"] for t in response["result"]["tools"]}
        expected = {
            "scheduled_recording.list",
            "scheduled_recording.create",
            "scheduled_recording.update",
            "scheduled_recording.delete",
            "scheduled_recording.cancel_armed",
        }
        assert expected <= names, f"Missing: {expected - names}"

    def test_tool_schemas_are_closed(self) -> None:
        response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        tools = response["result"]["tools"]
        for tool in tools:
            if tool["name"].startswith("scheduled_recording."):
                schema = tool["inputSchema"]
                assert schema["type"] == "object"
                assert schema["additionalProperties"] is False


class TestScheduledRecordingToolsCRUD:
    """CRUD operations through MCP tools, tested through the tool layer."""

    def test_list_empty(self) -> None:
        result = _call_ok("scheduled_recording.list")
        assert result == []

    def test_create_and_list(self) -> None:
        created = _call_ok("scheduled_recording.create", {
            "title": "Standup", "cron_expr": "0 9 * * 1", "duration_minutes": 30,
        })
        assert created["title"] == "Standup"
        assert created["cron_expr"] == "0 9 * * 1"
        assert created["duration_minutes"] == 30
        assert "receipt_id" in created

        listed = _call_ok("scheduled_recording.list")
        assert len(listed) == 1
        assert listed[0]["id"] == created["id"]

    def test_update(self) -> None:
        created = _call_ok("scheduled_recording.create", {
            "title": "Daily", "cron_expr": "0 8 * * *", "duration_minutes": 60,
        })
        schedule_id = created["id"]

        updated = _call_ok("scheduled_recording.update", {
            "schedule_id": schedule_id, "title": "Morning Daily", "duration_minutes": 45,
        })
        assert updated["title"] == "Morning Daily"
        assert updated["duration_minutes"] == 45

    def test_delete(self) -> None:
        created = _call_ok("scheduled_recording.create", {
            "title": "ToDelete", "cron_expr": "0 12 * * 5",
        })
        schedule_id = created["id"]

        deleted = _call_ok("scheduled_recording.delete", {"schedule_id": schedule_id})
        assert deleted["deleted"] is True
        assert "receipt_id" in deleted

        # Verify deleted: list should be empty
        listed = _call_ok("scheduled_recording.list")
        assert len(listed) == 0

    def test_full_round_trip(self) -> None:
        """Create -> list -> update -> delete through MCP."""
        created = _call_ok("scheduled_recording.create", {
            "title": "Retro", "cron_expr": "30 14 * * 5",
            "duration_minutes": 90, "one_shot": True,
        })
        schedule_id = created["id"]

        listed = _call_ok("scheduled_recording.list")
        assert any(s["id"] == schedule_id for s in listed)

        updated = _call_ok("scheduled_recording.update", {
            "schedule_id": schedule_id, "title": "Sprint Retro",
        })
        assert updated["title"] == "Sprint Retro"

        deleted = _call_ok("scheduled_recording.delete", {"schedule_id": schedule_id})
        assert deleted["deleted"] is True


class TestScheduledRecordingToolsRefusals:
    """Identical refusals to the HTTP path: bad cron and non-positive duration."""

    def test_bad_cron_is_error(self) -> None:
        error = _call_error("scheduled_recording.create", {
            "title": "Bad cron", "cron_expr": "not valid",
        })
        assert "cron" in error.lower() or "invalid" in error.lower()

    def test_empty_cron_is_error(self) -> None:
        error = _call_error("scheduled_recording.create", {
            "title": "No cron",
        })
        assert "cron" in error.lower() or "required" in error.lower()

    def test_non_positive_duration_is_error(self) -> None:
        error = _call_error("scheduled_recording.create", {
            "title": "Zero", "cron_expr": "0 9 * * 1", "duration_minutes": 0,
        })
        assert "duration" in error.lower()

    def test_negative_duration_is_error(self) -> None:
        error = _call_error("scheduled_recording.create", {
            "title": "Neg", "cron_expr": "0 9 * * 1", "duration_minutes": -5,
        })
        assert "duration" in error.lower()

    def test_bad_cron_on_update_is_error(self) -> None:
        created = _call_ok("scheduled_recording.create", {
            "title": "Valid", "cron_expr": "0 9 * * 1",
        })
        error = _call_error("scheduled_recording.update", {
            "schedule_id": created["id"], "cron_expr": "xxx",
        })
        assert "cron" in error.lower() or "invalid" in error.lower()

    def test_update_not_found_is_error(self) -> None:
        error = _call_error("scheduled_recording.update", {
            "schedule_id": "sr_ghost", "title": "Nope",
        })
        assert "not_found" in error.lower() or "unknown" in error.lower()

    def test_delete_not_found_is_error(self) -> None:
        error = _call_error("scheduled_recording.delete", {
            "schedule_id": "sr_phantom",
        })
        assert "not_found" in error.lower() or "unknown" in error.lower()


class TestScheduledRecordingToolsDelegation:
    """Enabling a schedule writes the bounded-delegation receipt; create tool returns the reference."""

    def test_create_enabled_returns_delegation_receipt(self) -> None:
        created = _call_ok("scheduled_recording.create", {
            "title": "Enabled", "cron_expr": "0 9 * * 1",
            "duration_minutes": 60, "enabled": True,
        })
        assert created["enabled"] is True
        assert "delegation_receipt_id" in created
        assert created["delegation_receipt_id"].startswith("sr_rcpt_")
        assert created["next_fire_at"] is not None

    def test_enable_via_update_returns_delegation_receipt(self) -> None:
        created = _call_ok("scheduled_recording.create", {
            "title": "Disabled", "cron_expr": "0 9 * * 1", "enabled": False,
        })
        schedule_id = created["id"]

        updated = _call_ok("scheduled_recording.update", {
            "schedule_id": schedule_id, "enabled": True,
        })
        assert updated["enabled"] is True
        assert "delegation_receipt_id" in updated
        assert updated["delegation_receipt_id"].startswith("sr_rcpt_")


class TestScheduledRecordingToolsCancelArmed:
    """Cancel-armed through MCP, with typed refusal when not armed."""

    def test_cancel_not_armed_is_error(self) -> None:
        created = _call_ok("scheduled_recording.create", {
            "title": "Idle", "cron_expr": "0 9 * * 1",
        })
        error = _call_error("scheduled_recording.cancel_armed", {
            "schedule_id": created["id"],
        })
        assert "not armed" in error.lower() or "not_armed" in error.lower()

    def test_cancel_not_found_is_error(self) -> None:
        error = _call_error("scheduled_recording.cancel_armed", {
            "schedule_id": "sr_ghost",
        })
        assert "not_found" in error.lower() or "unknown" in error.lower()

    def test_cancel_armed_with_conductor(self, tmp_db: Database, monkeypatch: Any) -> None:
        """When the conductor is running and the schedule is arming, cancel succeeds."""
        import holdspeak.scheduled_recording_conductor as src_module

        created = _call_ok("scheduled_recording.create", {
            "title": "Armed", "cron_expr": "0 9 * * 1",
        })
        schedule_id = created["id"]

        # Set state to arming
        tmp_db.scheduled_recordings.set_state(schedule_id, "arming")

        # Mock the conductor
        class FakeConductor:
            def cancel_armed(self, sid: str) -> bool:
                return True

        monkeypatch.setattr(src_module, "_conductor", FakeConductor())

        result = _call_ok("scheduled_recording.cancel_armed", {
            "schedule_id": schedule_id,
        })
        assert result["cancelled"] is True
        assert "receipt_id" in result

    def test_delete_while_arming_is_error(self, tmp_db: Database) -> None:
        """Cannot delete a schedule that is in 'arming' state."""
        created = _call_ok("scheduled_recording.create", {
            "title": "Arming", "cron_expr": "0 9 * * 1",
        })
        schedule_id = created["id"]

        tmp_db.scheduled_recordings.set_state(schedule_id, "arming")

        error = _call_error("scheduled_recording.delete", {
            "schedule_id": schedule_id,
        })
        assert "progress" in error.lower() or "arming" in error.lower()
