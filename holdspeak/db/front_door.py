"""Front Door apply-plan persistence (HS-156-02).

Durable, resumable pack-application plans.  Each plan tracks ordered items
with per-item state (queued -> running -> done/failed) so a crash or fault
never leaves a half-desk unaccounted.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .base import BaseRepository


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


class FrontDoorApplyRepository(BaseRepository):
    table = "front_door"

    def create_plan(self, *, pack_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        plan_id = "fdap_" + uuid.uuid4().hex
        now = _now()
        items_json = json.dumps(items, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO front_door_apply_plans "
                "(id, pack_id, status, items_json, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (plan_id, pack_id, "running", items_json, now, now),
            )
        return {
            "id": plan_id,
            "pack_id": pack_id,
            "status": "running",
            "items": items,
            "created_at": now,
            "updated_at": now,
        }

    def get_plan(self, plan_id: str) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, pack_id, status, items_json, created_at, updated_at "
                "FROM front_door_apply_plans WHERE id = ?",
                (plan_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": str(row["id"]),
            "pack_id": str(row["pack_id"]),
            "status": str(row["status"]),
            "items": json.loads(str(row["items_json"])),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }

    def get_latest_plan(self) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, pack_id, status, items_json, created_at, updated_at "
                "FROM front_door_apply_plans ORDER BY created_at DESC LIMIT 1",
            ).fetchone()
        if row is None:
            return None
        return {
            "id": str(row["id"]),
            "pack_id": str(row["pack_id"]),
            "status": str(row["status"]),
            "items": json.loads(str(row["items_json"])),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }

    def update_plan(self, plan_id: str, *, status: str, items: list[dict[str, Any]]) -> None:
        now = _now()
        items_json = json.dumps(items, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        with self._connection() as conn:
            conn.execute(
                "UPDATE front_door_apply_plans "
                "SET status = ?, items_json = ?, updated_at = ? "
                "WHERE id = ?",
                (status, items_json, now, plan_id),
            )

    def get_plan_by_pack(self, pack_id: str) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, pack_id, status, items_json, created_at, updated_at "
                "FROM front_door_apply_plans WHERE pack_id = ? "
                "ORDER BY created_at DESC LIMIT 1",
                (pack_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": str(row["id"]),
            "pack_id": str(row["pack_id"]),
            "status": str(row["status"]),
            "items": json.loads(str(row["items_json"])),
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
        }


__all__ = ["FrontDoorApplyRepository"]
