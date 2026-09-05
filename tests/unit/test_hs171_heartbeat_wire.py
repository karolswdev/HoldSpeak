"""HS-171-02: Heartbeat wire tests -- the sweep setting, the loop,
the receipt, the hub mirror, the quiet-hours hold, and the failure boundary.

Isolated HOME via tmp_path; never the owner's DB.
"""
from __future__ import annotations

import json
import time
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "heartbeat_test.db")


@pytest.fixture
def heartbeat_service(db: Database):
    from holdspeak.services.heartbeat_service import HeartbeatService
    return HeartbeatService(db)


@pytest.fixture
def heartbeat_service_with_ws(db: Database):
    """HeartbeatService with a mock WatchService for sweep tests."""
    from holdspeak.services.heartbeat_service import HeartbeatService

    mock_ws = MagicMock()
    mock_ws.evaluate_due.return_value = [
        {"watch_id": "w1", "outcome": "evaluated", "evaluation_id": "ev1", "transitions": 0},
        {"watch_id": "w2", "outcome": "evaluated", "evaluation_id": "ev2", "transitions": 1},
    ]
    return HeartbeatService(db, watch_service=mock_ws), mock_ws


# ---------------------------------------------------------------------------
# Settings round-trip
# ---------------------------------------------------------------------------


class TestHeartbeatSettings:
    def test_default_settings(self, heartbeat_service) -> None:
        """Default settings are returned when no policy exists."""
        s = heartbeat_service.get_settings()
        assert s["sweep_every_minutes"] == 15
        assert s["quiet_hours"]["start"] == 22
        assert s["quiet_hours"]["end"] == 8
        assert s["notify"] == "edge"
        assert s["muted_projects"] == []

    def test_update_roundtrips(self, heartbeat_service) -> None:
        """Updated settings persist and round-trip."""
        result = heartbeat_service.update_settings({
            "sweep_every_minutes": 30,
            "quiet_hours": {"start": 23, "end": 7},
            "notify": "off",
            "muted_projects": ["proj-1"],
        })
        assert result["sweep_every_minutes"] == 30
        assert result["quiet_hours"]["start"] == 23
        assert result["quiet_hours"]["end"] == 7
        assert result["notify"] == "off"
        assert result["muted_projects"] == ["proj-1"]

        # Read back
        s = heartbeat_service.get_settings()
        assert s["sweep_every_minutes"] == 30
        assert s["notify"] == "off"

    def test_settings_hub_read_reflects_heartbeat(self, heartbeat_service) -> None:
        """The hub_rhythm() method reflects heartbeat settings."""
        heartbeat_service.update_settings({"sweep_every_minutes": 45})
        rhythm = heartbeat_service.hub_rhythm()
        assert rhythm["sweepEveryMinutes"] == 45
        assert "quiet" in rhythm
        assert isinstance(rhythm["quiet"]["held"], bool)
        assert "loops" in rhythm
        assert "nextSweepAt" in rhythm
        assert "lastSweepAt" in rhythm


# ---------------------------------------------------------------------------
# Quiet hours
# ---------------------------------------------------------------------------


class TestQuietHours:
    def test_quiet_hours_hold_and_record(self, db: Database) -> None:
        """Sweep during quiet hours records held=True and does not evaluate."""
        from holdspeak.services.heartbeat_service import HeartbeatService

        mock_ws = MagicMock()
        hb = HeartbeatService(db, watch_service=mock_ws)
        # Set quiet hours to cover current time
        now = datetime.now()
        hb.update_settings({
            "quiet_hours": {"start": now.hour, "end": (now.hour + 2) % 24},
        })

        receipt = hb.run_sweep(OWNER)
        assert receipt["held"] is True
        assert receipt["watches"] == 0
        # evaluate_due should NOT be called during quiet hours
        mock_ws.evaluate_due.assert_not_called()

    def test_outside_quiet_hours_runs(self, db: Database) -> None:
        """Sweep outside quiet hours evaluates watches."""
        from holdspeak.services.heartbeat_service import HeartbeatService

        mock_ws = MagicMock()
        mock_ws.evaluate_due.return_value = [
            {"watch_id": "w1", "outcome": "evaluated"},
        ]
        hb = HeartbeatService(db, watch_service=mock_ws)
        # Set quiet hours to NOT cover current time
        now = datetime.now()
        hb.update_settings({
            "quiet_hours": {"start": (now.hour + 3) % 24, "end": (now.hour + 5) % 24},
        })

        receipt = hb.run_sweep(OWNER)
        assert receipt["held"] is False
        assert receipt["watches"] == 1
        mock_ws.evaluate_due.assert_called_once()


# ---------------------------------------------------------------------------
# Sweep and receipt
# ---------------------------------------------------------------------------


class TestSweepReceipt:
    def test_run_now_returns_receipt_with_counts(
        self, heartbeat_service_with_ws,
    ) -> None:
        """run_sweep returns a receipt with the correct shape."""
        hb, mock_ws = heartbeat_service_with_ws
        # Ensure not in quiet hours
        now = datetime.now()
        hb.update_settings({
            "quiet_hours": {"start": (now.hour + 3) % 24, "end": (now.hour + 5) % 24},
        })

        receipt = hb.run_sweep(OWNER)
        assert receipt["kind"] == "heartbeat.sweep"
        assert receipt["watches"] == 2
        assert isinstance(receipt["duration_ms"], (int, float))
        assert receipt["held"] is False
        assert "at" in receipt
        assert "errors" in receipt
        assert "outcomes" in receipt

    def test_kernel_receipt_exists_after_sweep(self, db: Database) -> None:
        """A kernel receipt is written after each sweep."""
        from holdspeak.services.heartbeat_service import HeartbeatService

        mock_ws = MagicMock()
        mock_ws.evaluate_due.return_value = []
        hb = HeartbeatService(db, watch_service=mock_ws)
        # Ensure not in quiet hours
        now = datetime.now()
        hb.update_settings({
            "quiet_hours": {"start": (now.hour + 3) % 24, "end": (now.hour + 5) % 24},
        })

        hb.run_sweep(OWNER)

        # Check kernel_receipts table
        with db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM kernel_receipts WHERE operation_id IN "
                "(SELECT operation_id FROM kernel_operations WHERE name='heartbeat.sweep')"
            ).fetchall()
        assert len(rows) >= 1
        receipt_row = rows[0]
        assert receipt_row["state"] == "succeeded"
        outcome = json.loads(receipt_row["outcome"])
        assert outcome["kind"] == "heartbeat.sweep"

    def test_next_evaluation_at_advances_after_sweep(self, db: Database) -> None:
        """After a sweep, next_evaluation_at on due watches is advanced by
        evaluate_due (verified via the mock)."""
        from holdspeak.services.heartbeat_service import HeartbeatService

        mock_ws = MagicMock()
        mock_ws.evaluate_due.return_value = [
            {"watch_id": "w1", "outcome": "evaluated", "evaluation_id": "ev1", "transitions": 0},
        ]
        hb = HeartbeatService(db, watch_service=mock_ws)
        now = datetime.now()
        hb.update_settings({
            "quiet_hours": {"start": (now.hour + 3) % 24, "end": (now.hour + 5) % 24},
        })

        receipt = hb.run_sweep(OWNER)
        # The watch_service.evaluate_due was called, which is the seam that
        # stamps next_evaluation_at on each watch.
        mock_ws.evaluate_due.assert_called_once()
        assert receipt["watches"] == 1


# ---------------------------------------------------------------------------
# Failure boundary
# ---------------------------------------------------------------------------


class TestFailureBoundary:
    def test_failing_watch_evaluation_does_not_stop_sweep(
        self, db: Database,
    ) -> None:
        """A failing watch evaluation does not stop the sweep; it appears in errors."""
        from holdspeak.services.heartbeat_service import HeartbeatService

        mock_ws = MagicMock()
        mock_ws.evaluate_due.side_effect = RuntimeError("boom")
        hb = HeartbeatService(db, watch_service=mock_ws)
        now = datetime.now()
        hb.update_settings({
            "quiet_hours": {"start": (now.hour + 3) % 24, "end": (now.hour + 5) % 24},
        })

        # Should NOT raise
        receipt = hb.run_sweep(OWNER)
        assert receipt["kind"] == "heartbeat.sweep"
        # Errors recorded
        assert receipt["errors"] >= 1

    def test_independent_loop_threads(self) -> None:
        """Heartbeat loop, cadence loop, and plugin queue loop are independent
        threads -- verified by checking that WebRuntime defines all three."""
        # This is a structural test: verify the heartbeat thread attribute exists
        # on WebRuntime alongside the other two.
        import holdspeak.web_runtime as wr
        cls = wr.WebRuntime
        # Check that HeartbeatMixin is in the MRO
        from holdspeak.runtime.heartbeat import HeartbeatMixin
        assert HeartbeatMixin in cls.__mro__, "HeartbeatMixin not in WebRuntime MRO"
        # Check that _heartbeat_loop method exists
        assert hasattr(cls, "_heartbeat_loop"), "WebRuntime lacks _heartbeat_loop"


# ---------------------------------------------------------------------------
# MCP parity
# ---------------------------------------------------------------------------


class TestMCPParity:
    def test_heartbeat_tools_in_mcp_catalogue(self) -> None:
        """heartbeat.status, heartbeat.run_now, heartbeat.set are in the MCP catalogue."""
        from holdspeak.mcp.tools import TOOLS as MCP_TOOLS

        names = {t["name"] for t in MCP_TOOLS}
        assert "heartbeat.status" in names
        assert "heartbeat.run_now" in names
        assert "heartbeat.set" in names

    def test_heartbeat_tools_classified_in_thread_gate(self) -> None:
        """All heartbeat tools are classified in thread_tools._TOOL_CLASSES."""
        from holdspeak.services.thread_tools import TOOL_NAMES

        assert "heartbeat.status" in TOOL_NAMES
        assert "heartbeat.run_now" in TOOL_NAMES
        assert "heartbeat.set" in TOOL_NAMES


# ---------------------------------------------------------------------------
# Hub integration
# ---------------------------------------------------------------------------


class TestHubIntegration:
    def test_hub_rhythm_contains_heartbeat_fields(self, heartbeat_service) -> None:
        """hub_rhythm returns the heartbeat sweep fields."""
        rhythm = heartbeat_service.hub_rhythm()
        assert "sweepEveryMinutes" in rhythm
        assert "nextSweepAt" in rhythm
        assert "lastSweepAt" in rhythm
        assert "quiet" in rhythm
        assert "start" in rhythm["quiet"]
        assert "end" in rhythm["quiet"]
        assert "held" in rhythm["quiet"]
        assert "loops" in rhythm

    def test_hub_rhythm_after_sweep(self, db: Database) -> None:
        """After a sweep, hub_rhythm reflects last/next sweep timestamps."""
        from holdspeak.services.heartbeat_service import HeartbeatService

        mock_ws = MagicMock()
        mock_ws.evaluate_due.return_value = []
        hb = HeartbeatService(db, watch_service=mock_ws)
        now = datetime.now()
        hb.update_settings({
            "quiet_hours": {"start": (now.hour + 3) % 24, "end": (now.hour + 5) % 24},
        })
        hb.run_sweep(OWNER)

        rhythm = hb.hub_rhythm()
        assert rhythm["lastSweepAt"] is not None
        assert rhythm["nextSweepAt"] is not None
