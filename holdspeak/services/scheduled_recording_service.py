"""Transport-neutral service for scheduled recording CRUD + cancel (HS-136-02).

One core, two callers (HTTP routes and MCP tools). Validation, receipts,
and conductor interaction live here — transports only map to/from their
wire format.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict
from typing import Any, Optional

from ..cron import next_cron_fire
from ..db.scheduled_recordings import ScheduledRecording
from ..logging_config import get_logger
from ..principals import Principal
from .errors import ConflictError, NotFound, ValidationError

log = get_logger("services.scheduled_recording")


def _validate_cron(cron_expr: str) -> None:
    """Validate a cron expression by attempting to compute a next-fire time.

    Reuses holdspeak.cron which is the single parser the conductor also uses.
    A cron that produces no next-fire within 400 days is considered invalid.
    """
    if not cron_expr or not cron_expr.strip():
        raise ValidationError(
            "cron_expr is required",
            code="invalid_cron",
            context={"field": "cron_expr"},
        )
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValidationError(
            f"cron_expr must have exactly 5 fields (minute hour dom month dow), got {len(parts)}",
            code="invalid_cron",
            context={"field": "cron_expr", "value": cron_expr},
        )
    # Validate each field parses (next_cron_fire returns None for invalid)
    result = next_cron_fire(cron_expr)
    if result is None:
        raise ValidationError(
            f"cron_expr '{cron_expr}' does not produce a valid next-fire time",
            code="invalid_cron",
            context={"field": "cron_expr", "value": cron_expr},
        )


def _validate_duration(duration_minutes: int) -> None:
    """Duration must be a positive integer."""
    if not isinstance(duration_minutes, int) or duration_minutes < 1:
        raise ValidationError(
            f"duration_minutes must be a positive integer, got {duration_minutes!r}",
            code="invalid_duration",
            context={"field": "duration_minutes", "value": duration_minutes},
        )


def _epoch_to_iso(epoch: Optional[float]) -> Optional[str]:
    """Convert an epoch-seconds float to an ISO-8601 UTC string.

    The DB stores all timestamps as epoch-seconds floats; the HTTP/MCP wire
    contract declares them as ISO-8601 strings (matching meetings' startedAt
    etc.). This adapter bridges the gap so the client's ``new Date(iso)``
    parses correctly instead of reading epoch-seconds as epoch-milliseconds.
    """
    if epoch is None:
        return None
    from datetime import datetime, timezone
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")


def _schedule_dict(rec: ScheduledRecording) -> dict[str, Any]:
    d = asdict(rec)
    # Convert all epoch-seconds float fields to ISO-8601 strings (HS-136-03).
    for key in ("created_at", "next_fire_at", "last_fired_at", "armed_at", "deadline_at"):
        d[key] = _epoch_to_iso(d.get(key))
    return d


def _write_receipt(
    db: Any,
    schedule_id: str,
    state: str,
    outcome: str,
    *,
    detail: str = "",
) -> str:
    """Write a kernel receipt for a scheduled recording management event (V.2)."""
    receipt_id = f"sr_rcpt_{uuid.uuid4().hex[:12]}"
    now = time.time()
    operation_id = f"sr_op_{uuid.uuid4().hex[:12]}"
    idem_key = f"sr:{schedule_id}:{now}:{uuid.uuid4().hex[:8]}"
    try:
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO kernel_operations
                   (operation_id, request_id, idempotency_key, name, version,
                    principal_kind, principal_identity, target_ref, placement,
                    envelope_sha256, policy_version, authority_basis,
                    state, revision, native_id, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?,?)""",
                (
                    operation_id,
                    idem_key,
                    idem_key,
                    "scheduled_recording",
                    1,
                    "owner",
                    "scheduled-recording-service",
                    f"schedule:{schedule_id}",
                    "local",
                    "",
                    "",
                    f"schedule-management:{schedule_id}",
                    state,
                    operation_id,
                    now,
                    now,
                ),
            )
            conn.execute(
                """INSERT INTO kernel_receipts
                   (receipt_id, operation_id, state, outcome, result_ref, created_at)
                   VALUES (?,?,?,?,?,?)""",
                (receipt_id, operation_id, state, outcome, detail, now),
            )
    except Exception as exc:
        log.error(f"Receipt write failed for {schedule_id}: {exc}")
    return receipt_id


class ScheduledRecordingService:
    """CRUD + cancel-armed for scheduled recordings.

    Receipts are written for create, enable, cancel, and delete (Article V.2).
    The bounded-delegation receipt is written on enable (I5).
    """

    def __init__(self, db: Any) -> None:
        self.db = db

    def list_schedules(self, principal: Principal) -> list[dict[str, Any]]:
        """List all scheduled recordings."""
        return [_schedule_dict(r) for r in self.db.scheduled_recordings.list_all()]

    def get_schedule(self, principal: Principal, schedule_id: str) -> dict[str, Any]:
        """Get one scheduled recording by id."""
        rec = self.db.scheduled_recordings.get(schedule_id)
        if rec is None:
            raise NotFound("scheduled_recording", schedule_id)
        return _schedule_dict(rec)

    def create_schedule(
        self,
        principal: Principal,
        *,
        title: str = "",
        cron_expr: str,
        tz: str = "UTC",
        one_shot: bool = False,
        duration_minutes: int = 60,
        enabled: bool = False,
    ) -> dict[str, Any]:
        """Create a scheduled recording. Validates cron and duration."""
        _validate_cron(cron_expr)
        _validate_duration(duration_minutes)

        # Compute next_fire_at if enabling
        delegation_receipt_id = ""
        nf: Optional[float] = None
        if enabled:
            nf = next_cron_fire(cron_expr)
            delegation_receipt_id = _write_receipt(
                self.db, "pending", "succeeded", "delegation_enabled",
                detail=f"Bounded delegation for new schedule '{title}' "
                       f"(cron={cron_expr}, duration={duration_minutes}m)",
            )

        rec = self.db.scheduled_recordings.create(
            title=title,
            cron_expr=cron_expr,
            tz=tz,
            one_shot=one_shot,
            duration_minutes=duration_minutes,
            enabled=enabled,
            next_fire_at=nf,
            delegation_receipt_id=delegation_receipt_id,
        )

        # Write create receipt
        create_receipt_id = _write_receipt(
            self.db, rec.id, "succeeded", "schedule_created",
            detail=f"Created schedule '{rec.title}' (id={rec.id})",
        )

        result = _schedule_dict(rec)
        result["receipt_id"] = create_receipt_id
        if delegation_receipt_id:
            result["delegation_receipt_id"] = delegation_receipt_id
        return result

    def update_schedule(
        self,
        principal: Principal,
        schedule_id: str,
        *,
        title: Optional[str] = None,
        cron_expr: Optional[str] = None,
        tz: Optional[str] = None,
        one_shot: Optional[bool] = None,
        duration_minutes: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> dict[str, Any]:
        """Update a scheduled recording. Validates cron and duration if provided."""
        existing = self.db.scheduled_recordings.get(schedule_id)
        if existing is None:
            raise NotFound("scheduled_recording", schedule_id)

        if cron_expr is not None:
            _validate_cron(cron_expr)
        if duration_minutes is not None:
            _validate_duration(duration_minutes)

        # Compute next_fire_at if terms changed or enabling
        effective_cron = cron_expr if cron_expr is not None else existing.cron_expr
        kwargs: dict[str, Any] = {}
        if title is not None:
            kwargs["title"] = title
        if cron_expr is not None:
            kwargs["cron_expr"] = cron_expr
        if tz is not None:
            kwargs["tz"] = tz
        if one_shot is not None:
            kwargs["one_shot"] = one_shot
        if duration_minutes is not None:
            kwargs["duration_minutes"] = duration_minutes

        delegation_receipt_id: Optional[str] = None

        # Enabling or terms change while enabled: write delegation receipt (I5)
        terms_changed = cron_expr is not None or duration_minutes is not None
        was_enabled = existing.enabled
        will_enable = enabled if enabled is not None else was_enabled

        if will_enable and (enabled is True or terms_changed):
            # Write bounded-delegation receipt
            delegation_receipt_id = _write_receipt(
                self.db, schedule_id, "succeeded", "delegation_enabled",
                detail=f"Bounded delegation for schedule '{existing.title}' "
                       f"(cron={effective_cron}, duration="
                       f"{duration_minutes if duration_minutes is not None else existing.duration_minutes}m)",
            )
            kwargs["delegation_receipt_id"] = delegation_receipt_id

        if enabled is not None:
            kwargs["enabled"] = enabled

        # Recompute next_fire_at if cron changed or newly enabled
        if will_enable and (cron_expr is not None or (enabled is True and not was_enabled)):
            nf = next_cron_fire(effective_cron)
            kwargs["next_fire_at"] = nf

        rec = self.db.scheduled_recordings.update(schedule_id, **kwargs)
        if rec is None:
            raise NotFound("scheduled_recording", schedule_id)

        result = _schedule_dict(rec)
        if delegation_receipt_id:
            result["delegation_receipt_id"] = delegation_receipt_id
        return result

    def delete_schedule(
        self, principal: Principal, schedule_id: str
    ) -> dict[str, Any]:
        """Delete a scheduled recording. Writes a receipt (V.2)."""
        existing = self.db.scheduled_recordings.get(schedule_id)
        if existing is None:
            raise NotFound("scheduled_recording", schedule_id)

        # Cannot delete while armed or recording
        if existing.state in ("arming", "recording"):
            raise ConflictError(
                f"Cannot delete schedule in state '{existing.state}'; "
                f"cancel or wait for it to finish first",
                code="schedule_in_progress",
            )

        receipt_id = _write_receipt(
            self.db, schedule_id, "succeeded", "schedule_deleted",
            detail=f"Deleted schedule '{existing.title}' (id={schedule_id})",
        )

        self.db.scheduled_recordings.delete(schedule_id)
        return {"deleted": True, "id": schedule_id, "receipt_id": receipt_id}

    def cancel_armed(
        self, principal: Principal, schedule_id: str
    ) -> dict[str, Any]:
        """Cancel an armed (counting-down) scheduled recording.

        Delegates to the conductor's cancel_armed seam. The conductor
        handles the state transition and writes its own receipt for the
        cancel event. This service writes an additional management receipt
        for the cancel request itself.
        """
        existing = self.db.scheduled_recordings.get(schedule_id)
        if existing is None:
            raise NotFound("scheduled_recording", schedule_id)

        if existing.state != "arming":
            raise ConflictError(
                f"Schedule is not armed (state='{existing.state}')",
                code="not_armed",
            )

        # Call the conductor's cancel_armed seam
        from ..scheduled_recording_conductor import _conductor

        if _conductor is None:
            raise ConflictError(
                "Scheduled recording conductor is not running",
                code="conductor_unavailable",
            )

        cancelled = _conductor.cancel_armed(schedule_id)
        if not cancelled:
            raise ConflictError(
                "Schedule was not in arming state on the conductor",
                code="not_armed",
            )

        receipt_id = _write_receipt(
            self.db, schedule_id, "succeeded", "cancel_armed_requested",
            detail=f"Cancel-armed requested for schedule '{existing.title}' (id={schedule_id})",
        )

        # Re-read after cancel to get updated state
        rec = self.db.scheduled_recordings.get(schedule_id)
        result = _schedule_dict(rec) if rec else {"id": schedule_id}
        result["receipt_id"] = receipt_id
        result["cancelled"] = True
        return result
