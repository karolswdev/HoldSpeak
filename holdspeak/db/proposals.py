"""HS-172-03: Follow-through proposals repository.

Manages the ``follow_through_proposals`` table: intel-extracted decisions
and action items that arrive as PROPOSALS in NEEDS YOU.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .base import BaseRepository


@dataclass(frozen=True)
class Proposal:
    id: str
    meeting_id: str
    project_id: Optional[str]
    kind: str  # "decision" | "action"
    text: str
    owner_hint: Optional[str]
    due_hint: Optional[str]
    source_artifact_id: Optional[str]
    source_plugin: str
    segment_timestamp: Optional[float]
    speaker_label: Optional[str]
    model_host: Optional[str]
    fingerprint: str
    state: str  # "proposed" | "confirmed" | "dismissed"
    original_text: Optional[str]
    created_at: str
    decided_at: Optional[str]


def _fingerprint(meeting_id: str, source_plugin: str, text: str) -> str:
    """Deterministic fingerprint for dedup: (meeting_id, plugin, text hash)."""
    raw = f"{meeting_id}:{source_plugin}:{text.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class ProposalRepository(BaseRepository):
    table = "proposals"

    def create_proposal(
        self,
        *,
        meeting_id: str,
        project_id: Optional[str],
        kind: str,
        text: str,
        owner_hint: Optional[str] = None,
        due_hint: Optional[str] = None,
        source_artifact_id: Optional[str] = None,
        source_plugin: str,
        segment_timestamp: Optional[float] = None,
        speaker_label: Optional[str] = None,
        model_host: Optional[str] = None,
    ) -> Optional[Proposal]:
        """Insert a proposal; returns None if the fingerprint already exists."""
        fp = _fingerprint(meeting_id, source_plugin, text)
        proposal_id = f"prop-{uuid.uuid4().hex[:16]}"
        now = datetime.now().isoformat()
        with self._connection() as conn:
            # Check dedup: a proposed row with the same fingerprint.
            existing = conn.execute(
                "SELECT id FROM follow_through_proposals "
                "WHERE meeting_id = ? AND fingerprint = ? AND state = 'proposed'",
                (meeting_id, fp),
            ).fetchone()
            if existing is not None:
                return None
            conn.execute(
                """INSERT INTO follow_through_proposals
                   (id, meeting_id, project_id, kind, text, owner_hint,
                    due_hint, source_artifact_id, source_plugin,
                    segment_timestamp, speaker_label, model_host,
                    fingerprint, state, original_text, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?)""",
                (
                    proposal_id, meeting_id, project_id, kind, text,
                    owner_hint, due_hint, source_artifact_id, source_plugin,
                    segment_timestamp, speaker_label, model_host,
                    fp, text, now,
                ),
            )
        return Proposal(
            id=proposal_id,
            meeting_id=meeting_id,
            project_id=project_id,
            kind=kind,
            text=text,
            owner_hint=owner_hint,
            due_hint=due_hint,
            source_artifact_id=source_artifact_id,
            source_plugin=source_plugin,
            segment_timestamp=segment_timestamp,
            speaker_label=speaker_label,
            model_host=model_host,
            fingerprint=fp,
            state="proposed",
            original_text=text,
            created_at=now,
            decided_at=None,
        )

    def list_proposals(
        self,
        *,
        meeting_id: Optional[str] = None,
        project_id: Optional[str] = None,
        state: Optional[str] = None,
    ) -> list[Proposal]:
        """List proposals filtered by meeting, project, or state."""
        clauses = []
        params: list[Any] = []
        if meeting_id is not None:
            clauses.append("meeting_id = ?")
            params.append(meeting_id)
        if project_id is not None:
            clauses.append("project_id = ?")
            params.append(project_id)
        if state is not None:
            clauses.append("state = ?")
            params.append(state)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM follow_through_proposals{where} ORDER BY created_at DESC",
                params,
            ).fetchall()
        return [self._to_proposal(r) for r in rows]

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM follow_through_proposals WHERE id = ?",
                (proposal_id,),
            ).fetchone()
        return self._to_proposal(row) if row else None

    def confirm_proposal(
        self,
        proposal_id: str,
        *,
        text: Optional[str] = None,
        owner: Optional[str] = None,
        due: Optional[str] = None,
    ) -> Optional[Proposal]:
        """Confirm a proposal: set state=confirmed; optionally amend text/owner/due."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM follow_through_proposals WHERE id = ? AND state = 'proposed'",
                (proposal_id,),
            ).fetchone()
            if row is None:
                return None
            updates = ["state = 'confirmed'", "decided_at = ?"]
            params: list[Any] = [now]
            if text is not None:
                updates.append("text = ?")
                params.append(text)
            if owner is not None:
                updates.append("owner_hint = ?")
                params.append(owner)
            if due is not None:
                updates.append("due_hint = ?")
                params.append(due)
            params.append(proposal_id)
            conn.execute(
                f"UPDATE follow_through_proposals SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            updated = conn.execute(
                "SELECT * FROM follow_through_proposals WHERE id = ?",
                (proposal_id,),
            ).fetchone()
        return self._to_proposal(updated) if updated else None

    def dismiss_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Dismiss a proposal."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM follow_through_proposals WHERE id = ? AND state = 'proposed'",
                (proposal_id,),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE follow_through_proposals SET state = 'dismissed', decided_at = ? WHERE id = ?",
                (now, proposal_id),
            )
            updated = conn.execute(
                "SELECT * FROM follow_through_proposals WHERE id = ?",
                (proposal_id,),
            ).fetchone()
        return self._to_proposal(updated) if updated else None

    @staticmethod
    def _to_proposal(row: Any) -> Proposal:
        return Proposal(
            id=str(row["id"]),
            meeting_id=str(row["meeting_id"]),
            project_id=str(row["project_id"]) if row["project_id"] else None,
            kind=str(row["kind"]),
            text=str(row["text"]),
            owner_hint=str(row["owner_hint"]) if row["owner_hint"] else None,
            due_hint=str(row["due_hint"]) if row["due_hint"] else None,
            source_artifact_id=str(row["source_artifact_id"]) if row["source_artifact_id"] else None,
            source_plugin=str(row["source_plugin"]),
            segment_timestamp=float(row["segment_timestamp"]) if row["segment_timestamp"] is not None else None,
            speaker_label=str(row["speaker_label"]) if row["speaker_label"] else None,
            model_host=str(row["model_host"]) if row["model_host"] else None,
            fingerprint=str(row["fingerprint"]),
            state=str(row["state"]),
            original_text=str(row["original_text"]) if row["original_text"] else None,
            created_at=str(row["created_at"]),
            decided_at=str(row["decided_at"]) if row["decided_at"] else None,
        )
