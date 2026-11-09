# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_scheduled_recording_mcp.py to restore.

# ruff: noqa


# --- TestScheduledRecordingToolsCatalogue::test_tool_names_in_catalogue: P1/P5: re-types five tool names; the round trip and -5 repeat the create/update/delete and zero-duration cases beside them
# (was a method of class TestScheduledRecordingToolsCatalogue)
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


# --- TestScheduledRecordingToolsCRUD::test_full_round_trip: P1/P5: re-types five tool names; the round trip and -5 repeat the create/update/delete and zero-duration cases beside them
# (was a method of class TestScheduledRecordingToolsCRUD)
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


# --- TestScheduledRecordingToolsRefusals::test_negative_duration_is_error: P1/P5: re-types five tool names; the round trip and -5 repeat the create/update/delete and zero-duration cases beside them
# (was a method of class TestScheduledRecordingToolsRefusals)
def test_negative_duration_is_error(self) -> None:
    error = _call_error("scheduled_recording.create", {
        "title": "Neg", "cron_expr": "0 9 * * 1", "duration_minutes": -5,
    })
    assert "duration" in error.lower()
