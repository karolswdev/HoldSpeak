"""HS-175 C2 -- a real Cancel on an event-born recording.

Counsel H7-1: the arrival's Cancel POSTed the cancel route, which refused
anything not in ``arming`` (event-born rows are ``idle`` from creation until
``starts_at - lead``). The service now disables an ``idle`` event-linked row
by the owner's word -- ``enabled=0, state='cancelled',
last_outcome='owner_cancelled'`` and a ``scheduled_recording.cancelled.owner``
receipt -- refuses by name while capture runs (``already_recording``), and
still refuses a plain cron schedule that is merely idle (``not_armed``).
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, NotFound
from holdspeak.services.scheduled_recording_service import ScheduledRecordingService

OWNER = Principal(PrincipalKind.OWNER, "owner")


@pytest.fixture
def db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Database:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    return Database(tmp_path / "cancel.db")


def _event_born(db: Database, *, state: str = "idle", enabled: bool = True) -> Any:
    rec = db.scheduled_recordings.create(
        title="Standup",
        cron_expr="",
        tz="UTC",
        one_shot=True,
        duration_minutes=30,
        enabled=enabled,
        next_fire_at=time.time() + 3600,
        calendar_event_id="ev-standup",
        calendar_uid="uid-ev-standup",
        calendar_source_id="src-work",
        born_from="calendar_event",
    )
    if state != "idle":
        rec = db.scheduled_recordings.set_state(rec.id, state)
    return rec


def _receipts(db: Database, outcome: str) -> list[Any]:
    with db._connection() as conn:
        return conn.execute(
            "SELECT r.receipt_id, r.state, r.outcome, r.result_ref FROM kernel_receipts r "
            "WHERE r.outcome = ?",
            (outcome,),
        ).fetchall()


class TestCancelIdleEventBorn:
    def test_idle_event_born_row_is_cancelled_with_a_receipt(self, db: Database) -> None:
        rec = _event_born(db)
        assert rec.state == "idle" and rec.enabled

        result = ScheduledRecordingService(db).cancel_armed(OWNER, rec.id)

        assert result["cancelled"] is True
        assert result["state"] == "cancelled"
        assert result["enabled"] is False
        assert result["last_outcome"] == "owner_cancelled"
        after = db.scheduled_recordings.get(rec.id)
        assert after is not None
        assert (after.state, after.enabled, after.last_outcome) == (
            "cancelled", False, "owner_cancelled",
        )
        assert after.next_fire_at is None
        assert after.last_receipt_id == result["receipt_id"]
        receipts = _receipts(db, "scheduled_recording.cancelled.owner")
        assert len(receipts) == 1, receipts
        assert receipts[0]["receipt_id"] == result["receipt_id"]
        assert receipts[0]["state"] == "succeeded"
        assert "ev-standup" in receipts[0]["result_ref"]
        # Disabled means the door's armed index no longer sees it.
        assert [r.id for r in db.scheduled_recordings.list_enabled()] == []

    def test_cancelled_row_is_not_armed_again_by_a_second_cancel(self, db: Database) -> None:
        rec = _event_born(db)
        svc = ScheduledRecordingService(db)
        svc.cancel_armed(OWNER, rec.id)
        with pytest.raises(ConflictError) as exc:
            svc.cancel_armed(OWNER, rec.id)
        assert exc.value.code == "not_armed"
        assert len(_receipts(db, "scheduled_recording.cancelled.owner")) == 1

    def test_stamps_lane_w1_tombstone_when_the_column_exists(self, db: Database) -> None:
        """The tombstone column is W1's to add; when it is there, the owner's
        cancel fills it so the next calendar refresh does not re-arm."""
        with db._connection() as conn:
            # Lane W1's schema (75) carries the column already; add it only
            # when a DB predates it, so the test proves the stamp either way.
            cols = {r[1] for r in conn.execute("PRAGMA table_info(scheduled_recordings)")}
            if "owner_cancelled_at" not in cols:
                conn.execute("ALTER TABLE scheduled_recordings ADD COLUMN owner_cancelled_at REAL")
        rec = _event_born(db)
        before = time.time()
        ScheduledRecordingService(db).cancel_armed(OWNER, rec.id)
        with db._connection() as conn:
            stamped = conn.execute(
                "SELECT owner_cancelled_at FROM scheduled_recordings WHERE id=?", (rec.id,),
            ).fetchone()[0]
        assert stamped is not None and stamped >= before - 1

    def test_no_tombstone_column_is_not_a_failure(self, db: Database) -> None:
        rec = _event_born(db)
        result = ScheduledRecordingService(db).cancel_armed(OWNER, rec.id)
        assert result["state"] == "cancelled"


class TestCancelRefusedByName:
    def test_recording_row_is_refused_as_already_recording(self, db: Database) -> None:
        rec = _event_born(db, state="recording")
        with pytest.raises(ConflictError) as exc:
            ScheduledRecordingService(db).cancel_armed(OWNER, rec.id)
        assert exc.value.code == "already_recording"
        assert "stop the meeting" in str(exc.value).lower()
        after = db.scheduled_recordings.get(rec.id)
        assert after.state == "recording" and after.enabled
        assert _receipts(db, "scheduled_recording.cancelled.owner") == []

    def test_plain_cron_schedule_idle_is_still_not_armed(self, db: Database) -> None:
        rec = db.scheduled_recordings.create(
            title="Weekly", cron_expr="0 9 * * 1", tz="UTC", one_shot=False,
            duration_minutes=60, enabled=True, next_fire_at=time.time() + 3600,
        )
        with pytest.raises(ConflictError) as exc:
            ScheduledRecordingService(db).cancel_armed(OWNER, rec.id)
        assert exc.value.code == "not_armed"
        assert db.scheduled_recordings.get(rec.id).enabled

    def test_unknown_schedule_is_not_found(self, db: Database) -> None:
        with pytest.raises(NotFound):
            ScheduledRecordingService(db).cancel_armed(OWNER, "sr_ghost")

    def test_arming_still_goes_through_the_conductor(
        self, db: Database, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import holdspeak.scheduled_recording_conductor as conductor_module

        rec = _event_born(db, state="arming")
        seen: list[str] = []

        class FakeConductor:
            def cancel_armed(self, sid: str) -> bool:
                seen.append(sid)
                return True

        monkeypatch.setattr(conductor_module, "_conductor", FakeConductor())
        result = ScheduledRecordingService(db).cancel_armed(OWNER, rec.id)
        assert seen == [rec.id]
        assert result["cancelled"] is True
        assert len(_receipts(db, "cancel_armed_requested")) == 1
        assert _receipts(db, "scheduled_recording.cancelled.owner") == []


class TestDeleteOnEventBorn:
    """Counsel re-read condition 3 (hunt H-H): the event-born row IS the
    owner's tombstone; Delete must never remove it. A live row cancels
    (what the owner meant); a cancelled one is refused by name."""

    def test_delete_live_event_born_row_cancels_and_keeps_the_tombstone(self, db: Database) -> None:
        rec = _event_born(db)
        result = ScheduledRecordingService(db).delete_schedule(OWNER, rec.id)
        assert result["deleted"] is False and result["cancelled"] is True
        after = db.scheduled_recordings.get(rec.id)
        assert after is not None, "the row (the tombstone) must survive"
        assert (after.state, after.enabled, after.last_outcome) == ("cancelled", False, "owner_cancelled")
        assert after.owner_cancelled_at is not None
        assert len(_receipts(db, "scheduled_recording.cancelled.owner")) == 1
        assert _receipts(db, "schedule_deleted") == []
        # W1's tombstone read sees it: the next refresh will not re-arm the uid.
        assert db.scheduled_recordings.list_owner_cancelled_uids("src-work") == {"uid-ev-standup"}

    def test_delete_cancelled_event_born_row_is_refused_by_name(self, db: Database) -> None:
        rec = _event_born(db)
        svc = ScheduledRecordingService(db)
        svc.cancel_armed(OWNER, rec.id)
        with pytest.raises(ConflictError) as exc:
            svc.delete_schedule(OWNER, rec.id)
        assert exc.value.code == "event_born_cancel_instead"
        assert db.scheduled_recordings.get(rec.id) is not None
        assert db.scheduled_recordings.list_owner_cancelled_uids("src-work") == {"uid-ev-standup"}

    def test_delete_cron_row_still_hard_deletes(self, db: Database) -> None:
        rec = db.scheduled_recordings.create(
            title="Weekly", cron_expr="0 9 * * 1", tz="UTC", one_shot=False,
            duration_minutes=60, enabled=False,
        )
        result = ScheduledRecordingService(db).delete_schedule(OWNER, rec.id)
        assert result["deleted"] is True
        assert db.scheduled_recordings.get(rec.id) is None
        assert len(_receipts(db, "schedule_deleted")) == 1

    def test_mcp_delete_tool_cancels_the_event_born_row(
        self, db: Database, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The open-throttle MCP tool `scheduled_recording.delete` reaches the
        same service: the tombstone survives, the cancel is receipted."""
        import json
        from types import SimpleNamespace

        from holdspeak.mcp import server
        from holdspeak.mcp import tools as mcp_tools
        from holdspeak.mcp.server import handle_message

        monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
        monkeypatch.setattr(mcp_tools, "get_observer", lambda: None)
        monkeypatch.setattr(
            server, "resolve_auth",
            lambda: SimpleNamespace(principal=Principal(PrincipalKind.OWNER, "test")),
        )
        for name in ("MeetingService", "DictationService", "DeskService",
                     "DecisionRecordService", "FollowThroughService", "MondayBriefService"):
            monkeypatch.setattr(mcp_tools, name, lambda db, **kw: object())
        monkeypatch.setattr(mcp_tools, "EventQueryService", lambda db: object())

        rec = _event_born(db)

        def call(schedule_id: str) -> tuple[bool, Any]:
            response = handle_message({
                "jsonrpc": "2.0", "id": "del", "method": "tools/call",
                "params": {"name": "scheduled_recording.delete",
                           "arguments": {"schedule_id": schedule_id}},
            })
            result = response["result"]
            return result["isError"], json.loads(result["content"][0]["text"])

        is_error, value = call(rec.id)
        assert is_error is False, value
        assert value["deleted"] is False and value["cancelled"] is True
        after = db.scheduled_recordings.get(rec.id)
        assert after is not None and after.last_outcome == "owner_cancelled" and not after.enabled
        assert len(_receipts(db, "scheduled_recording.cancelled.owner")) == 1

        is_error, value = call(rec.id)
        assert is_error is True
        assert "cancel instead" in str(value).lower() or "event_born_cancel_instead" in str(value)
        assert db.scheduled_recordings.get(rec.id) is not None

