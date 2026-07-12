"""Steering audit repository (HS-87-03).

Every keystroke toward a pane is remembered — delivered or refused —
answering who/when/session/pane/what-shape/what-rode-along. The
receipt is privacy-respecting: the steer's sha256 and its first 120
characters, never the full text.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Optional

from .base import BaseRepository

TEXT_HEAD_CHARS = 120


def _iso_z(raw: object) -> str:
    """SQLite `datetime('now')` ("YYYY-MM-DD HH:MM:SS", UTC-naive) → the
    wire's UTC-Z instant ("YYYY-MM-DDTHH:MM:SSZ"), the contract §2 rule.
    An already-ISO value (a test-supplied Z string) passes through."""
    text = str(raw or "")
    if not text:
        return ""
    if text.endswith("Z") or "T" in text:
        return text
    return text.replace(" ", "T", 1) + "Z"


@dataclass(frozen=True)
class SteeringAuditEntry:
    id: int
    ts: str
    session_key: str
    agent: str
    pane_id: Optional[str]
    text_sha256: str
    text_head: str
    grounding: list[Any]
    submit: bool
    outcome: str
    detail: Optional[str]
    operation: dict[str, Any]
    policy_snapshot: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "ts": self.ts,
            "session_key": self.session_key,
            "agent": self.agent,
            "pane_id": self.pane_id,
            "text_sha256": self.text_sha256,
            "text_head": self.text_head,
            "grounding": list(self.grounding),
            "submit": self.submit,
            "outcome": self.outcome,
            "detail": self.detail,
            "operation": dict(self.operation),
            "policy_snapshot": dict(self.policy_snapshot),
        }


class SteeringAuditRepository(BaseRepository):
    def record(
        self,
        *,
        session_key: str,
        agent: str = "",
        pane_id: Optional[str] = None,
        text: str,
        grounding: Optional[list[Any]] = None,
        submit: bool = True,
        outcome: str,
        detail: Optional[str] = None,
        operation: Optional[dict[str, Any]] = None,
        policy_snapshot: Optional[dict[str, Any]] = None,
    ) -> int:
        """One audit row per steer attempt; returns the row id."""
        digest = hashlib.sha256(str(text).encode("utf-8", "replace")).hexdigest()
        head = str(text)[:TEXT_HEAD_CHARS]
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO steering_audit
                    (session_key, agent, pane_id, text_sha256, text_head,
                     grounding_json, submit, outcome, detail, operation_json,
                     policy_snapshot_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_key,
                    agent,
                    pane_id,
                    digest,
                    head,
                    self._json_dumps(list(grounding or []), fallback="[]"),
                    1 if submit else 0,
                    outcome,
                    detail,
                    self._json_dumps(dict(operation or {}), fallback="{}"),
                    self._json_dumps(dict(policy_snapshot or {}), fallback="{}"),
                ),
            )
            return int(cursor.lastrowid or 0)

    def list(
        self, *, session_key: Optional[str] = None, limit: int = 50
    ) -> list[SteeringAuditEntry]:
        """Newest first; optionally one session's trail."""
        limit = max(1, min(int(limit), 500))
        query = (
            "SELECT id, ts, session_key, agent, pane_id, text_sha256, "
            "text_head, grounding_json, submit, outcome, detail, "
            "operation_json, policy_snapshot_json "
            "FROM steering_audit "
        )
        params: tuple[Any, ...] = ()
        if session_key:
            query += "WHERE session_key = ? "
            params = (session_key,)
        query += "ORDER BY id DESC LIMIT ?"
        params += (limit,)
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            SteeringAuditEntry(
                id=int(row[0]),
                ts=_iso_z(row[1]),
                session_key=str(row[2]),
                agent=str(row[3] or ""),
                pane_id=row[4],
                text_sha256=str(row[5]),
                text_head=str(row[6] or ""),
                grounding=self._json_loads_list(row[7]),
                submit=bool(row[8]),
                outcome=str(row[9]),
                detail=row[10],
                operation=self._json_loads_dict(row[11]),
                policy_snapshot=self._json_loads_dict(row[12]),
            )
            for row in rows
        ]


__all__ = ["SteeringAuditEntry", "SteeringAuditRepository", "TEXT_HEAD_CHARS"]
