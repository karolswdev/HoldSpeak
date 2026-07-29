"""Durable decision records derived from synthesis artifacts (HS-109-01).

Decision rows carry sync clocks and tombstones in the house shape, but v31 does
not put them on the sync wire. The desktop archive remains their sole authority
until a later phase defines cross-device lifecycle conflict semantics.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

from .base import BaseRepository

_LIFECYCLES = frozenset({"recorded", "accepted", "superseded", "rejected"})


class DecisionTransitionRefused(ValueError):
    """A named refusal for an illegal decision lifecycle transition."""

    code = "illegal_decision_lifecycle_transition"

    def __init__(self, current: str, action: str, detail: str = "") -> None:
        message = f"{self.code}: cannot {action} decision in {current} lifecycle"
        if detail:
            message += f" ({detail})"
        super().__init__(message)
        self.current = current
        self.action = action


@dataclass(frozen=True)
class DecisionRecord:
    id: str
    text: str
    rationale: Optional[str]
    decided_at: str
    date_basis: str
    source_timestamp: Optional[float]
    provenance_label: Optional[str]
    source_artifact_id: str
    source_meeting_id: str
    source_state: str
    project_key: Optional[str]
    lifecycle: str
    superseded_by: Optional[str]
    created_at: str
    updated_at: str
    last_modified: str
    deleted: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionMoment:
    meeting_id: str
    source_timestamp: float
    segment_id: int
    segment_index: int
    segment_start: float
    segment_end: float
    speaker: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionLifecycleReceipt:
    receipt_id: str
    actor: str
    operation: str
    subject: str
    outcome: str
    from_lifecycle: str
    to_lifecycle: str
    superseded_by: Optional[str]
    recorded_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def derive_decision_id(
    meeting_id: str, artifact_id: str, payload: dict[str, Any]
) -> str:
    """Derive stable identity from source keys and the decision's TEXT.

    Identity anchors on what was decided — rationale, timestamps, and other
    provenance are metadata that may sharpen across plugin reruns without
    minting a second record for the same decision (HS-109-02: a rerun that
    gains a verified moment must update in place, never duplicate).
    """
    text = " ".join(str(payload.get("decision") or "").split()).lower()
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    key = f"{str(meeting_id).strip()}|{str(artifact_id).strip()}|{text_hash}"
    return "dec-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def _loads_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value or "{}"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _project_key(
    conn: sqlite3.Connection,
    meeting_id: str,
    structured: dict[str, Any],
    entry: dict[str, Any],
) -> Optional[str]:
    for candidate in (
        entry.get("project_key"),
        entry.get("project_id"),
        structured.get("project_key"),
        structured.get("project_id"),
    ):
        clean = str(candidate or "").strip()
        if clean:
            return clean
    rows = conn.execute(
        "SELECT project_id FROM meeting_projects WHERE meeting_id = ? ORDER BY project_id",
        (meeting_id,),
    ).fetchall()
    return str(rows[0][0]) if len(rows) == 1 else None


def _segment_value(segment: Any, name: str) -> Any:
    if isinstance(segment, dict):
        return segment.get(name)
    try:
        return segment[name]
    except (KeyError, IndexError, TypeError):
        return getattr(segment, name, None)


def _coerce_reported_timestamp(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def validate_source_timestamp(segments: list[Any], value: Any) -> Optional[float]:
    """Return a numeric offset only inside the meeting's real segment window."""
    timestamp = _coerce_reported_timestamp(value)
    if timestamp is None or not segments:
        return None
    bounds: list[tuple[float, float]] = []
    for segment in segments:
        try:
            start = float(_segment_value(segment, "start_time"))
            end = float(_segment_value(segment, "end_time"))
        except (TypeError, ValueError):
            continue
        if end >= start:
            bounds.append((start, end))
    if not bounds:
        return None
    range_start = min(start for start, _ in bounds)
    range_end = max(end for _, end in bounds)
    return timestamp if range_start <= timestamp <= range_end else None


def _normalize_anchor_text(value: Any) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def anchor_decision_timestamp(segments: list[Any], decision_text: str) -> Optional[float]:
    """Anchor only when normalized decision text is a literal segment substring."""
    needle = _normalize_anchor_text(decision_text)
    if not needle:
        return None
    for segment in segments:
        haystack = _normalize_anchor_text(_segment_value(segment, "text"))
        if needle not in haystack:
            continue
        try:
            return float(_segment_value(segment, "start_time"))
        except (TypeError, ValueError):
            continue
    return None


def _moment_iso(started_at: str, source_timestamp: float) -> str:
    return (datetime.fromisoformat(started_at) + timedelta(seconds=source_timestamp)).isoformat()


def _project_artifact_row(
    conn: sqlite3.Connection, artifact: sqlite3.Row
) -> dict[str, int]:
    counts = {"artifacts": 1, "decisions": 0, "inserted": 0, "updated": 0, "unchanged": 0, "skipped": 0}
    meeting_id = str(artifact["meeting_id"] or "").strip()
    artifact_id = str(artifact["id"] or "").strip()
    if not meeting_id or not artifact_id:
        counts["skipped"] += 1
        return counts
    meeting = conn.execute(
        "SELECT started_at FROM meetings WHERE id = ?", (meeting_id,)
    ).fetchone()
    if meeting is None:
        counts["skipped"] += 1
        return counts
    structured = _loads_object(artifact["structured_json"])
    entries = structured.get("decisions")
    if not isinstance(entries, list):
        return counts

    segments = conn.execute(
        "SELECT * FROM segments WHERE meeting_id = ? ORDER BY start_time,id",
        (meeting_id,),
    ).fetchall()
    meeting_started_at = str(meeting["started_at"])
    now_iso = datetime.now().isoformat()
    for raw in entries:
        if not isinstance(raw, dict):
            counts["skipped"] += 1
            continue
        text = str(raw.get("decision") or "").strip()
        if not text:
            counts["skipped"] += 1
            continue
        counts["decisions"] += 1
        rationale = str(raw.get("rationale") or "").strip() or None
        source_timestamp = validate_source_timestamp(segments, raw.get("source_timestamp"))
        provenance_label: Optional[str] = None
        if source_timestamp is not None:
            provenance_label = "reported"
        else:
            source_timestamp = anchor_decision_timestamp(segments, text)
            if source_timestamp is not None:
                provenance_label = "anchored"
        if source_timestamp is None:
            decided_at = meeting_started_at
            date_basis = "meeting_date"
        else:
            decided_at = _moment_iso(meeting_started_at, source_timestamp)
            date_basis = "transcript_moment"
        project_key = _project_key(conn, meeting_id, structured, raw)
        decision_id = derive_decision_id(meeting_id, artifact_id, raw)
        existing = conn.execute(
            "SELECT * FROM decisions WHERE id = ?", (decision_id,)
        ).fetchone()
        projected = (
            text,
            rationale,
            decided_at,
            date_basis,
            source_timestamp,
            provenance_label,
            artifact_id,
            meeting_id,
            "linked",
            project_key,
        )
        if existing is None:
            conn.execute(
                """INSERT INTO decisions (
                       id,text,rationale,decided_at,date_basis,source_timestamp,
                       provenance_label,source_artifact_id,source_meeting_id,
                       source_state,project_key,lifecycle,superseded_by,created_at,
                       updated_at,last_modified,deleted)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,'recorded',NULL,?,?,?,0)""",
                (decision_id, *projected, now_iso, now_iso, now_iso),
            )
            counts["inserted"] += 1
            continue
        current = tuple(
            existing[name]
            for name in (
                "text",
                "rationale",
                "decided_at",
                "date_basis",
                "source_timestamp",
                "provenance_label",
                "source_artifact_id",
                "source_meeting_id",
                "source_state",
                "project_key",
            )
        )
        if current == projected and not bool(existing["deleted"]):
            counts["unchanged"] += 1
            continue
        conn.execute(
            """UPDATE decisions SET text=?,rationale=?,decided_at=?,date_basis=?,
                       source_timestamp=?,provenance_label=?,source_artifact_id=?,
                       source_meeting_id=?,source_state=?,project_key=?,updated_at=?,
                       last_modified=?,deleted=0
                   WHERE id=?""",
            (*projected, now_iso, now_iso, decision_id),
        )
        counts["updated"] += 1
    return counts


def backfill_decisions(conn: sqlite3.Connection) -> dict[str, int]:
    """Project every archived decisions artifact; safe to rerun."""
    rows = conn.execute(
        "SELECT * FROM artifacts WHERE artifact_type = 'decisions' ORDER BY created_at,id"
    ).fetchall()
    totals = {"artifacts": 0, "decisions": 0, "inserted": 0, "updated": 0, "unchanged": 0, "skipped": 0}
    for artifact in rows:
        result = _project_artifact_row(conn, artifact)
        for key, value in result.items():
            totals[key] += value
    return totals


class DecisionRepository(BaseRepository):
    """Query, reconcile, and transition durable decision records."""

    def reconcile_artifact(self, artifact_id: str) -> dict[str, int]:
        clean_id = str(artifact_id or "").strip()
        if not clean_id:
            raise ValueError("artifact_id is required")
        with self._connection() as conn:
            artifact = conn.execute(
                "SELECT * FROM artifacts WHERE id = ? AND artifact_type = 'decisions'",
                (clean_id,),
            ).fetchone()
            if artifact is None:
                return {"artifacts": 0, "decisions": 0, "inserted": 0, "updated": 0, "unchanged": 0, "skipped": 0}
            return _project_artifact_row(conn, artifact)

    def backfill(self) -> dict[str, int]:
        with self._connection() as conn:
            return backfill_decisions(conn)

    def resolve_segment(
        self, meeting_id: str, source_timestamp: Any
    ) -> Optional[DecisionMoment]:
        """Resolve a verified meeting offset to the same segment aftercare chooses."""
        clean_meeting_id = str(meeting_id or "").strip()
        if not clean_meeting_id:
            return None
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM segments WHERE meeting_id = ? ORDER BY start_time,id",
                (clean_meeting_id,),
            ).fetchall()
        timestamp = validate_source_timestamp(rows, source_timestamp)
        if timestamp is None:
            return None
        chosen_index = 0
        chosen = rows[0]
        for index, segment in enumerate(rows):
            if float(segment["start_time"]) <= timestamp:
                chosen_index = index
                chosen = segment
            else:
                break
        return DecisionMoment(
            meeting_id=clean_meeting_id,
            source_timestamp=timestamp,
            segment_id=int(chosen["id"]),
            segment_index=chosen_index,
            segment_start=float(chosen["start_time"]),
            segment_end=float(chosen["end_time"]),
            speaker=str(chosen["speaker"] or ""),
            text=str(chosen["text"] or ""),
        )

    def resolve_decision_moment(self, decision_id: str) -> Optional[DecisionMoment]:
        decision = self.get(decision_id)
        if decision is None or decision.source_timestamp is None:
            return None
        return self.resolve_segment(decision.source_meeting_id, decision.source_timestamp)

    def get(self, decision_id: str) -> Optional[DecisionRecord]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM decisions WHERE id = ? AND deleted = 0",
                (str(decision_id or "").strip(),),
            ).fetchone()
        return self._row(row) if row else None

    def get_with_lineage(self, decision_id: str) -> Optional[dict[str, Any]]:
        decision = self.get(decision_id)
        if decision is None:
            return None
        superseded_by = self.get(decision.superseded_by) if decision.superseded_by else None
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT * FROM decisions
                   WHERE superseded_by = ? AND deleted = 0
                   ORDER BY decided_at,id""",
                (decision.id,),
            ).fetchall()
        return {
            "decision": decision.to_dict(),
            "lineage": {
                "superseded_by": superseded_by.to_dict() if superseded_by else None,
                "supersedes": [self._row(row).to_dict() for row in rows],
            },
        }

    def list(
        self,
        *,
        project_key: Optional[str] = None,
        meeting_id: Optional[str] = None,
        lifecycle: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[DecisionRecord]:
        clauses = ["deleted = 0"]
        params: list[Any] = []
        if project_key is not None:
            clauses.append("project_key = ?")
            params.append(str(project_key).strip())
        if meeting_id is not None:
            clauses.append("source_meeting_id = ?")
            params.append(str(meeting_id).strip())
        if lifecycle is not None:
            clean_lifecycle = str(lifecycle).strip().lower()
            if clean_lifecycle not in _LIFECYCLES:
                raise ValueError(f"invalid decision lifecycle: {clean_lifecycle}")
            clauses.append("lifecycle = ?")
            params.append(clean_lifecycle)
        params.extend((max(1, min(int(limit), 500)), max(0, int(offset))))
        with self._connection() as conn:
            rows = conn.execute(
                f"""SELECT * FROM decisions WHERE {' AND '.join(clauses)}
                    ORDER BY decided_at DESC,id DESC LIMIT ? OFFSET ?""",
                params,
            ).fetchall()
        return [self._row(row) for row in rows]

    def accept(self, decision_id: str, *, actor: str) -> DecisionLifecycleReceipt:
        return self._transition(decision_id, action="accept", actor=actor)

    def reject(self, decision_id: str, *, actor: str) -> DecisionLifecycleReceipt:
        return self._transition(decision_id, action="reject", actor=actor)

    def supersede(
        self, decision_id: str, superseded_by: str, *, actor: str
    ) -> DecisionLifecycleReceipt:
        return self._transition(
            decision_id,
            action="supersede",
            actor=actor,
            superseded_by=str(superseded_by or "").strip(),
        )

    def _transition(
        self,
        decision_id: str,
        *,
        action: str,
        actor: str,
        superseded_by: Optional[str] = None,
    ) -> DecisionLifecycleReceipt:
        clean_id = str(decision_id or "").strip()
        clean_actor = str(actor or "").strip()
        if not clean_id:
            raise ValueError("decision_id is required")
        if not clean_actor:
            raise ValueError("actor is required")
        targets = {"accept": "accepted", "reject": "rejected", "supersede": "superseded"}
        if action not in targets:
            raise ValueError(f"unknown decision lifecycle action: {action}")
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM decisions WHERE id = ? AND deleted = 0", (clean_id,)
            ).fetchone()
            if row is None:
                raise KeyError(clean_id)
            current = str(row["lifecycle"])
            allowed = current == "recorded" or (action == "supersede" and current == "accepted")
            if not allowed:
                raise DecisionTransitionRefused(current, action)
            target_id: Optional[str] = None
            if action == "supersede":
                target_id = str(superseded_by or "").strip()
                if not target_id:
                    raise DecisionTransitionRefused(current, action, "superseded_by is required")
                if target_id == clean_id:
                    raise DecisionTransitionRefused(current, action, "a decision cannot supersede itself")
                replacement = conn.execute(
                    "SELECT lifecycle FROM decisions WHERE id = ? AND deleted = 0",
                    (target_id,),
                ).fetchone()
                if replacement is None:
                    raise DecisionTransitionRefused(current, action, "replacement decision not found")
                if str(replacement["lifecycle"]) not in {"recorded", "accepted"}:
                    raise DecisionTransitionRefused(
                        current, action, "replacement decision does not stand"
                    )
            target = targets[action]
            conn.execute(
                """UPDATE decisions SET lifecycle=?,superseded_by=?,updated_at=?,last_modified=?
                   WHERE id=?""",
                (target, target_id, now_iso, now_iso, clean_id),
            )
        receipt_key = f"{clean_id}|{action}|{clean_actor}|{now_iso}"
        return DecisionLifecycleReceipt(
            receipt_id="dec-rec-" + hashlib.sha256(receipt_key.encode()).hexdigest()[:20],
            actor=clean_actor,
            operation=f"decision.{action}",
            subject=f"decision:{clean_id}",
            outcome="applied",
            from_lifecycle=current,
            to_lifecycle=target,
            superseded_by=target_id,
            recorded_at=now_iso,
        )

    @staticmethod
    def _row(row: sqlite3.Row) -> DecisionRecord:
        return DecisionRecord(
            id=str(row["id"]),
            text=str(row["text"]),
            rationale=str(row["rationale"]) if row["rationale"] is not None else None,
            decided_at=str(row["decided_at"]),
            date_basis=str(row["date_basis"]),
            source_timestamp=(
                float(row["source_timestamp"])
                if row["source_timestamp"] is not None
                else None
            ),
            provenance_label=(
                str(row["provenance_label"])
                if row["provenance_label"] is not None
                else None
            ),
            source_artifact_id=str(row["source_artifact_id"]),
            source_meeting_id=str(row["source_meeting_id"]),
            source_state=str(row["source_state"]),
            project_key=str(row["project_key"]) if row["project_key"] is not None else None,
            lifecycle=str(row["lifecycle"]),
            superseded_by=str(row["superseded_by"]) if row["superseded_by"] is not None else None,
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            last_modified=str(row["last_modified"]),
            deleted=bool(row["deleted"]),
        )
