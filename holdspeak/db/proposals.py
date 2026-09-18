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
    decision_record_id: Optional[str]
    commitment_id: Optional[str]
    created_at: str
    decided_at: Optional[str]
    # HS-200-12: retry identity, extraction provenance, transcript evidence,
    # the support axis, and the owner's supplied values.  All optional so a
    # row written before HS-200-12 still loads.
    retry_key: Optional[str] = None
    extraction_revision: Optional[str] = None
    job_id: Optional[str] = None
    job_attempt: Optional[int] = None
    extraction_model: Optional[str] = None
    span_start: Optional[float] = None
    span_end: Optional[float] = None
    segment_index: Optional[int] = None
    support: str = "unknown"
    support_record: Optional[dict[str, Any]] = None
    owner_supplied: Optional[str] = None
    due_supplied: Optional[str] = None
    edited_at: Optional[str] = None
    # HS-200-13: the extractor's rationale, carried through confirm (AC1).
    rationale: Optional[str] = None

    @property
    def owner(self) -> Optional[str]:
        """The owner the record would carry: supplied by the owner, else the hint."""
        return self.owner_supplied or self.owner_hint

    @property
    def due(self) -> Optional[str]:
        return self.due_supplied or self.due_hint

    @property
    def acceptance(self) -> str:
        """The C2 acceptance axis, derived from the one state word."""
        return {"confirmed": "accepted", "dismissed": "rejected"}.get(self.state, "unreviewed")


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
        retry_key: Optional[str] = None,
        extraction_revision: Optional[str] = None,
        job_id: Optional[str] = None,
        job_attempt: Optional[int] = None,
        extraction_model: Optional[str] = None,
        span_start: Optional[float] = None,
        span_end: Optional[float] = None,
        segment_index: Optional[int] = None,
        support: str = "unknown",
        support_record: Optional[dict[str, Any]] = None,
        rationale: Optional[str] = None,
    ) -> Optional[Proposal]:
        """Insert a proposal; returns None when its identity already exists.

        HS-200-12: the retry identity (``retry_key``) is checked in EVERY
        state -- a confirmed or dismissed proposal is still the same
        proposal when the same extraction lands again.  The text fingerprint
        stays as the belt for rows written without a key.
        """
        fp = _fingerprint(meeting_id, source_plugin, text)
        proposal_id = f"prop-{uuid.uuid4().hex[:16]}"
        now = datetime.now().isoformat()
        with self._connection() as conn:
            if retry_key:
                existing = conn.execute(
                    "SELECT id FROM follow_through_proposals "
                    "WHERE meeting_id = ? AND retry_key = ?",
                    (meeting_id, retry_key),
                ).fetchone()
                if existing is not None:
                    return None
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
                    fingerprint, state, original_text, created_at,
                    retry_key, extraction_revision, job_id, job_attempt,
                    extraction_model, span_start, span_end, segment_index,
                    support, support_record_json, rationale)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?, ?,
                           ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    proposal_id, meeting_id, project_id, kind, text,
                    owner_hint, due_hint, source_artifact_id, source_plugin,
                    segment_timestamp, speaker_label, model_host,
                    fp, text, now,
                    retry_key, extraction_revision, job_id, job_attempt,
                    extraction_model, span_start, span_end, segment_index,
                    support, json.dumps(support_record) if support_record else None,
                    (str(rationale).strip() or None) if rationale else None,
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
            decision_record_id=None,
            commitment_id=None,
            created_at=now,
            decided_at=None,
            retry_key=retry_key,
            extraction_revision=extraction_revision,
            job_id=job_id,
            job_attempt=job_attempt,
            extraction_model=extraction_model,
            span_start=span_start,
            span_end=span_end,
            segment_index=segment_index,
            support=support,
            support_record=dict(support_record) if support_record else None,
            rationale=(str(rationale).strip() or None) if rationale else None,
        )

    def edit_proposal(
        self,
        proposal_id: str,
        *,
        text: Optional[str] = None,
        owner: Optional[str] = None,
        due: Optional[str] = None,
        support: Optional[str] = None,
        support_record: Optional[dict[str, Any]] = None,
    ) -> Optional[Proposal]:
        """HS-200-12: amend a PROPOSED row in place.

        ``owner``/``due`` land in the *_supplied columns; the extraction
        hints are never rewritten (they are the ``was{}`` the Room reads).
        ``support``/``support_record`` are what the service decided the
        edit does to the C2 support axis.  Returns None when the row is not
        proposed (a decided proposal is immutable).
        """
        now = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM follow_through_proposals WHERE id = ? AND state = 'proposed'",
                (proposal_id,),
            ).fetchone()
            if row is None:
                return None
            updates = ["edited_at = ?"]
            params: list[Any] = [now]
            if text is not None:
                updates.append("text = ?")
                params.append(text)
            if owner is not None:
                updates.append("owner_supplied = ?")
                params.append(owner or None)
            if due is not None:
                updates.append("due_supplied = ?")
                params.append(due or None)
            if support is not None:
                updates.append("support = ?")
                params.append(support)
            if support_record is not None:
                updates.append("support_record_json = ?")
                params.append(json.dumps(support_record))
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
        decision_record_id: Optional[str] = None,
        commitment_id: Optional[str] = None,
        support: Optional[str] = None,
        support_record: Optional[dict[str, Any]] = None,
        conn: Any = None,
    ) -> Optional[Proposal]:
        """Confirm a proposal: set state=confirmed; optionally amend text/owner/due.

        HS-200-12: with ``conn`` the flip rides the CALLER's transaction and
        is conditional on ``state = 'proposed'`` -- the one atomic claim that
        makes two racing confirms (a double click, a retried POST) produce
        one record chain and one replay.
        """
        if conn is not None:
            return self._confirm_in(conn, proposal_id, text=text, owner=owner, due=due,
                                    decision_record_id=decision_record_id,
                                    commitment_id=commitment_id, support=support,
                                    support_record=support_record)
        with self._connection() as conn:
            return self._confirm_in(conn, proposal_id, text=text, owner=owner, due=due,
                                    decision_record_id=decision_record_id,
                                    commitment_id=commitment_id, support=support,
                                    support_record=support_record)

    def _confirm_in(
        self,
        conn: Any,
        proposal_id: str,
        *,
        text: Optional[str],
        owner: Optional[str],
        due: Optional[str],
        decision_record_id: Optional[str],
        commitment_id: Optional[str],
        support: Optional[str],
        support_record: Optional[dict[str, Any]],
    ) -> Optional[Proposal]:
        now = datetime.now().isoformat()
        if True:
            updates = ["state = 'confirmed'", "decided_at = ?"]
            params: list[Any] = [now]
            if text is not None:
                updates.append("text = ?")
                params.append(text)
            if owner is not None:
                updates.append("owner_supplied = ?")
                params.append(owner)
            if due is not None:
                updates.append("due_supplied = ?")
                params.append(due)
            if support is not None:
                updates.append("support = ?")
                params.append(support)
            if support_record is not None:
                updates.append("support_record_json = ?")
                params.append(json.dumps(support_record))
            # owner_hint and due_hint are the ORIGINAL extraction hints;
            # they stay unchanged so was{} can compare them against the
            # confirmed values in decision_commitments.
            if decision_record_id is not None:
                updates.append("decision_record_id = ?")
                params.append(decision_record_id)
            if commitment_id is not None:
                updates.append("commitment_id = ?")
                params.append(commitment_id)
            params.append(proposal_id)
            flipped = conn.execute(
                f"UPDATE follow_through_proposals SET {', '.join(updates)} "
                "WHERE id = ? AND state = 'proposed'",
                params,
            ).rowcount
            if not flipped:
                return None
            updated = conn.execute(
                "SELECT * FROM follow_through_proposals WHERE id = ?",
                (proposal_id,),
            ).fetchone()
        return self._to_proposal(updated) if updated else None

    def dismiss_proposal(self, proposal_id: str, *, conn: Any = None) -> Optional[Proposal]:
        """Dismiss a proposal (conditional on 'proposed'; None when it was not)."""
        if conn is not None:
            return self._dismiss_in(conn, proposal_id)
        with self._connection() as conn:
            return self._dismiss_in(conn, proposal_id)

    def _dismiss_in(self, conn: Any, proposal_id: str) -> Optional[Proposal]:
        now = datetime.now().isoformat()
        if True:
            flipped = conn.execute(
                "UPDATE follow_through_proposals SET state = 'dismissed', decided_at = ? "
                "WHERE id = ? AND state = 'proposed'",
                (now, proposal_id),
            ).rowcount
            if not flipped:
                return None
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
            decision_record_id=str(row["decision_record_id"]) if row["decision_record_id"] else None,
            commitment_id=str(row["commitment_id"]) if row["commitment_id"] else None,
            created_at=str(row["created_at"]),
            decided_at=str(row["decided_at"]) if row["decided_at"] else None,
            retry_key=_opt_str(row, "retry_key"),
            extraction_revision=_opt_str(row, "extraction_revision"),
            job_id=_opt_str(row, "job_id"),
            job_attempt=int(row["job_attempt"]) if _has(row, "job_attempt") and row["job_attempt"] is not None else None,
            extraction_model=_opt_str(row, "extraction_model"),
            span_start=float(row["span_start"]) if _has(row, "span_start") and row["span_start"] is not None else None,
            span_end=float(row["span_end"]) if _has(row, "span_end") and row["span_end"] is not None else None,
            segment_index=int(row["segment_index"]) if _has(row, "segment_index") and row["segment_index"] is not None else None,
            support=_opt_str(row, "support") or "unknown",
            support_record=_opt_json(row, "support_record_json"),
            owner_supplied=_opt_str(row, "owner_supplied"),
            due_supplied=_opt_str(row, "due_supplied"),
            edited_at=_opt_str(row, "edited_at"),
            rationale=_opt_str(row, "rationale"),
        )


def _has(row: Any, key: str) -> bool:
    try:
        return key in row.keys()
    except Exception:
        return False


def _opt_str(row: Any, key: str) -> Optional[str]:
    if not _has(row, key):
        return None
    value = row[key]
    return str(value) if value not in (None, "") else None


def _opt_json(row: Any, key: str) -> Optional[dict[str, Any]]:
    raw = _opt_str(row, key)
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None
