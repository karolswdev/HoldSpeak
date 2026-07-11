"""Durable request identity for paired dictation delivery (HS-93-05).

The companion chooses a delivery id before it sends. The hub claims that id
before invoking the typing hook and retains the terminal HTTP response. A
reconnect with the same id and request therefore reads the original Receipt;
it never invokes the effect a second time.

This is deliberately a narrow delivery ledger, not a queue. A row stranded in
``pending`` has an unknown outcome and is never replayed automatically: losing
one uncertain delivery is preferable to silently typing it twice.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Optional

from .base import BaseRepository

_DELIVERY_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class DictationDeliveryRepository(BaseRepository):
    """Claim and complete exactly one remote-dictation request identity."""

    def claim(
        self,
        delivery_id: str,
        *,
        request_hash: str,
        now: Optional[datetime] = None,
    ) -> dict[str, Any]:
        clean_id = str(delivery_id or "").strip()
        clean_hash = str(request_hash or "").strip().lower()
        if not _DELIVERY_ID.fullmatch(clean_id):
            raise ValueError("delivery_id must be 1..128 identifier characters")
        if len(clean_hash) != 64 or any(c not in "0123456789abcdef" for c in clean_hash):
            raise ValueError("request_hash must be a SHA-256 hex digest")
        timestamp = (now or datetime.now()).isoformat()
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO remote_dictation_deliveries
                    (delivery_id, request_hash, status, created_at, updated_at)
                VALUES (?, ?, 'pending', ?, ?)
                ON CONFLICT(delivery_id) DO NOTHING
                """,
                (clean_id, clean_hash, timestamp, timestamp),
            )
            inserted = bool(cursor.rowcount and cursor.rowcount > 0)
            row = conn.execute(
                "SELECT * FROM remote_dictation_deliveries WHERE delivery_id = ?",
                (clean_id,),
            ).fetchone()
        if row is None:  # pragma: no cover - defensive SQLite invariant
            raise RuntimeError("delivery claim was not readable")
        if row["request_hash"] != clean_hash:
            raise ValueError("delivery_id already belongs to a different request")
        record = self._record(row)
        record["claim_state"] = "claimed" if inserted else str(row["status"])
        return record

    def complete(
        self,
        delivery_id: str,
        *,
        response_status: int,
        response: dict[str, Any],
        now: Optional[datetime] = None,
    ) -> dict[str, Any]:
        return self._finish(
            delivery_id,
            status="succeeded",
            response_status=response_status,
            response=response,
            error=None,
            now=now,
        )

    def fail(
        self,
        delivery_id: str,
        *,
        response_status: int,
        response: dict[str, Any],
        error: str,
        now: Optional[datetime] = None,
    ) -> dict[str, Any]:
        return self._finish(
            delivery_id,
            status="failed",
            response_status=response_status,
            response=response,
            error=str(error or "delivery failed"),
            now=now,
        )

    def get(self, delivery_id: str) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM remote_dictation_deliveries WHERE delivery_id = ?",
                (str(delivery_id or "").strip(),),
            ).fetchone()
        return self._record(row) if row is not None else None

    def _finish(
        self,
        delivery_id: str,
        *,
        status: str,
        response_status: int,
        response: dict[str, Any],
        error: Optional[str],
        now: Optional[datetime],
    ) -> dict[str, Any]:
        clean_id = str(delivery_id or "").strip()
        timestamp = (now or datetime.now()).isoformat()
        response_json = json.dumps(response, separators=(",", ":"), sort_keys=True)
        with self._connection() as conn:
            cursor = conn.execute(
                """
                UPDATE remote_dictation_deliveries
                SET status = ?, response_status = ?, response_json = ?,
                    error = ?, updated_at = ?
                WHERE delivery_id = ? AND status = 'pending'
                """,
                (
                    status,
                    int(response_status),
                    response_json,
                    error,
                    timestamp,
                    clean_id,
                ),
            )
            row = conn.execute(
                "SELECT * FROM remote_dictation_deliveries WHERE delivery_id = ?",
                (clean_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"unknown dictation delivery: {delivery_id}")
        # A second finisher can only observe the first terminal result. It
        # cannot overwrite it with a different side-effect claim.
        if not cursor.rowcount and row["status"] == "pending":
            raise RuntimeError("dictation delivery remained pending")
        return self._record(row)

    @staticmethod
    def _record(row: Any) -> dict[str, Any]:
        response: dict[str, Any] = {}
        raw = row["response_json"]
        if isinstance(raw, str) and raw:
            try:
                decoded = json.loads(raw)
                if isinstance(decoded, dict):
                    response = decoded
            except json.JSONDecodeError:
                response = {}
        return {
            "delivery_id": row["delivery_id"],
            "request_hash": row["request_hash"],
            "status": row["status"],
            "response_status": row["response_status"],
            "response": response,
            "error": row["error"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


__all__ = ["DictationDeliveryRepository"]
