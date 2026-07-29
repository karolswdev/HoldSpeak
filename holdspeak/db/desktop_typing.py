"""Durable, content-free native receipts for ``desktop.type_text``."""
from __future__ import annotations

import json
from typing import Any, Mapping

from .base import BaseRepository


class DesktopTypeReceiptRepository(BaseRepository):
    def record(
        self,
        *,
        native_id: str,
        operation_id: str,
        target_ref: str,
        payload_sha256: str,
        text_bytes: int,
        submit: bool,
        head: str,
        authority_basis: str,
        gesture: str,
        outcome: str,
        result_ref: str,
        metadata: Mapping[str, Any],
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO desktop_type_receipts (
                    native_id, operation_id, target_ref, payload_sha256,
                    text_bytes, submit, head, authority_basis, gesture,
                    outcome, result_ref, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    native_id,
                    operation_id,
                    target_ref,
                    payload_sha256,
                    int(text_bytes),
                    int(submit),
                    str(head)[:120],
                    authority_basis,
                    gesture,
                    outcome,
                    result_ref,
                    json.dumps(dict(metadata), separators=(",", ":"), sort_keys=True),
                ),
            )
        return self.get(native_id) or {}

    def get(self, native_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM desktop_type_receipts WHERE native_id = ?",
                (str(native_id),),
            ).fetchone()
        if row is None:
            return None
        value = dict(row)
        value["submit"] = bool(value["submit"])
        value["metadata"] = json.loads(value.pop("metadata_json") or "{}")
        return value
