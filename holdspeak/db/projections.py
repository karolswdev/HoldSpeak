"""Additive Desk attention and receipt read model (HS-92-09).

Projection rows are rebuilt from authoritative domain records on every read.
Only the owner's presentation decision (acknowledge/dismiss) is persisted, so
this index cannot become a competing audit log or mutate its subject.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

from .base import BaseRepository


@dataclass(frozen=True)
class DeskProjection:
    id: str
    projection_kind: str
    subject_ref: str
    subject_label: str
    title: str
    summary: str
    reason_code: str
    decision_kind: str
    attention_state: str
    actual_destination: Optional[str]
    authority_basis: Optional[str]
    attempt: Optional[int]
    outcome: str
    timestamp: str
    correlation_id: Optional[str]
    source_kind: str
    source_id: str
    source_api: str
    detail_url: str
    severity: str = "normal"
    dismissed: bool = False
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProjectionRepository(BaseRepository):
    """Union authoritative journals into one pageable, non-sensitive read model."""

    def list(
        self,
        *,
        search: str = "",
        projection_kind: Optional[str] = None,
        attention_state: Optional[str] = None,
        subject_ref: Optional[str] = None,
        include_dismissed: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        rows = self._collect()
        states = self._presentation_states()
        projected: list[DeskProjection] = []
        for row in rows:
            row = DeskProjection(
                **{**row.to_dict(), "timestamp": self._normalize_timestamp(row.timestamp)}
            )
            overlay = states.get(row.id)
            if overlay:
                row = DeskProjection(
                    **{
                        **row.to_dict(),
                        "attention_state": (
                            "acknowledged"
                            if overlay["attention_state"] == "acknowledged"
                            else row.attention_state
                        ),
                        "dismissed": bool(overlay["dismissed_at"]),
                    }
                )
            projected.append(row)

        if not include_dismissed:
            projected = [row for row in projected if not row.dismissed]
        # Contextual Desk badges describe the subject, not the current drawer
        # query. Capture them before search/kind/state filters are applied.
        subject_counts: dict[str, dict[str, int]] = {}
        for row in projected:
            bucket = subject_counts.setdefault(
                row.subject_ref, {"needs_attention": 0, "receipts": 0}
            )
            if row.attention_state == "needs_attention":
                bucket["needs_attention"] += 1
            if row.projection_kind == "receipt":
                bucket["receipts"] += 1
        if projection_kind:
            projected = [row for row in projected if row.projection_kind == projection_kind]
        if attention_state:
            projected = [row for row in projected if row.attention_state == attention_state]
        if subject_ref:
            projected = [row for row in projected if row.subject_ref == subject_ref]
        term = str(search or "").strip().casefold()
        if term:
            projected = [
                row
                for row in projected
                if term
                in " ".join(
                    (row.subject_label, row.title, row.summary, row.reason_code, row.outcome)
                ).casefold()
            ]
        projected.sort(key=lambda row: (row.timestamp, row.id), reverse=True)
        total = len(projected)
        start = max(0, int(offset))
        bounded = max(1, min(int(limit), 200))
        page = projected[start : start + bounded]
        counts = {
            "needs_attention": sum(row.attention_state == "needs_attention" for row in projected),
            "unseen": sum(row.attention_state == "unseen" for row in projected),
            "acknowledged": sum(row.attention_state == "acknowledged" for row in projected),
            "receipts": sum(row.projection_kind == "receipt" for row in projected),
        }
        return {
            "projections": [row.to_dict() for row in page],
            "counts": counts,
            "subject_counts": subject_counts,
            "page": {
                "offset": start,
                "limit": bounded,
                "total": total,
                "has_more": start + len(page) < total,
            },
        }

    def set_presentation(self, projection_id: str, *, action: str) -> bool:
        clean = str(action or "").strip().lower()
        if clean not in {"acknowledge", "dismiss", "restore"}:
            raise ValueError("action must be acknowledge, dismiss, or restore")
        if not any(row.id == projection_id for row in self._collect()):
            return False
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO desk_projection_state
                   (projection_id,attention_state,dismissed_at,updated_at)
                   VALUES (?,CASE WHEN ?='acknowledge' THEN 'acknowledged' ELSE 'unseen' END,
                           CASE WHEN ?='dismiss' THEN datetime('now') ELSE NULL END,
                           datetime('now'))
                   ON CONFLICT(projection_id) DO UPDATE SET
                     attention_state=CASE WHEN ?='acknowledge' THEN 'acknowledged'
                                          WHEN ?='restore' THEN 'unseen'
                                          ELSE desk_projection_state.attention_state END,
                     dismissed_at=CASE WHEN ?='dismiss' THEN datetime('now')
                                       WHEN ?='restore' THEN NULL
                                       ELSE desk_projection_state.dismissed_at END,
                     updated_at=datetime('now')""",
                (projection_id, clean, clean, clean, clean, clean, clean),
            )
        return True

    def _presentation_states(self) -> dict[str, Any]:
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM desk_projection_state").fetchall()
        return {str(row["projection_id"]): row for row in rows}

    def _collect(self) -> list[DeskProjection]:
        with self._connection() as conn:
            meetings = {
                str(row["id"]): str(row["title"] or "Untitled meeting")
                for row in conn.execute("SELECT id,title FROM meetings").fetchall()
            }
            rows: list[DeskProjection] = []
            rows.extend(self._actuators(conn, meetings))
            rows.extend(self._invocations(conn))
            rows.extend(self._dictation(conn))
            rows.extend(self._steering(conn))
            rows.extend(self._meetings(conn, meetings))
            rows.extend(self._sync_conflicts(conn, meetings))
            rows.extend(self._artifacts(conn))
            rows.extend(self._jobs(conn, meetings))
            rows.extend(self._cadence(conn))
        return rows

    @staticmethod
    def _normalize_timestamp(value: str) -> str:
        """Make SQLite and ISO timestamps sort and render consistently as UTC."""
        clean = str(value or "").strip()
        if not clean:
            return "1970-01-01T00:00:00Z"
        if "T" not in clean and " " in clean:
            clean = clean.replace(" ", "T", 1)
        if clean.endswith("+00:00"):
            return clean[:-6] + "Z"
        if clean[-1:] != "Z" and "+" not in clean[10:] and "-" not in clean[10:]:
            clean += "Z"
        return clean

    def _actuators(self, conn: Any, meetings: dict[str, str]) -> list[DeskProjection]:
        rows = conn.execute("SELECT * FROM actuator_proposals").fetchall()
        result = []
        for row in rows:
            status = str(row["status"])
            target = str(row["target"])
            meeting_id = row["meeting_id"]
            payload = self._json_loads_dict(row["payload_json"])
            source = payload.get("_source") if isinstance(payload.get("_source"), dict) else {}
            source_ref = str(source.get("ref") or "").strip()
            if meeting_id:
                subject_ref = f"meeting:{meeting_id}"
                subject_label = meetings.get(str(meeting_id), "Untitled meeting")
            elif source_ref:
                subject_ref = source_ref
                subject_label = str(source.get("label") or source_ref.split(":", 1)[-1])
            else:
                subject_ref = f"integration:{target}"
                subject_label = target.title()
            policy = self._json_loads_dict(row["policy_snapshot_json"])
            operation = self._json_loads_dict(row["operation_json"])
            needs = status in {"proposed", "approved", "failed"}
            action_names = {
                "slack": ("send to Slack", "Slack send"),
                "webhook": ("post to Custom webhook", "Custom webhook post"),
                "github": ("create GitHub issue", "GitHub issue creation"),
            }
            commitment, noun = action_names.get(target, (f"run {target} action", f"{target.title()} action"))
            titles = {
                "proposed": f"Approve and {commitment}",
                "approved": f"{noun} awaits execution",
                "executed": f"{noun} succeeded",
                "failed": f"{noun} failed",
                "rejected": f"{noun} rejected",
            }
            result.append(DeskProjection(
                id=f"actuator:{row['id']}:{status}",
                projection_kind="attention" if needs else "receipt",
                subject_ref=subject_ref, subject_label=subject_label,
                title=titles.get(status, f"{target.title()} action: {status}"),
                summary=(
                    "The exact proposed effect and source remain on this Receipt."
                    if source_ref
                    else "The exact proposed effect remains in its source record."
                ),
                reason_code=f"effect_{status}", decision_kind="authorization",
                attention_state="needs_attention" if needs else "resolved",
                actual_destination=str(row["approved_destination"] or operation.get("destination") or target),
                authority_basis=str(policy.get("authorization_basis") or "per_action_required"),
                attempt=None, outcome=str(row["execution_state"] or status),
                timestamp=str(row["updated_at"]), correlation_id=f"actuator:{row['id']}",
                source_kind="actuator_proposal", source_id=str(row["id"]),
                source_api=(
                    f"/api/meetings/{meeting_id}/proposals"
                    if meeting_id
                    else "/api/desk/projections" if source_ref else "/api/mesh/inbox"
                ),
                detail_url=(
                    f"/history?meeting={meeting_id}"
                    if meeting_id
                    else f"/?open={source_ref}" if source_ref else "/"
                ),
                severity="error" if status == "failed" else "normal",
            ))
        return result

    def _invocations(self, conn: Any) -> list[DeskProjection]:
        labels: dict[str, str] = {}
        for table, kind, field in (
            ("recipes", "persona", "name"), ("chains", "sequence", "name"),
            ("workflows", "workflow", "name"),
        ):
            for row in conn.execute(f"SELECT id,{field} FROM {table}").fetchall():
                labels[f"{kind}:{row['id']}"] = str(row[field] or kind.title())
        result = []
        for row in conn.execute("SELECT * FROM capability_invocations").fetchall():
            state = str(row["state"])
            raw_ref = str(row["definition_ref"])
            kind, _, rid = raw_ref.partition(":")
            subject_ref = f"{'persona' if kind == 'recipe' else 'sequence' if kind == 'chain' else kind}:{rid}"
            attempt = conn.execute(
                "SELECT * FROM capability_attempts WHERE invocation_id=? ORDER BY attempt_index DESC LIMIT 1",
                (row["id"],),
            ).fetchone()
            placement = self._json_loads_dict(attempt["actual_placement_json"]) if attempt else {}
            target = placement.get("target") if isinstance(placement.get("target"), dict) else {}
            needs = state in {"failed", "unavailable", "empty"}
            active = state == "running"
            result.append(DeskProjection(
                id=f"invocation:{row['id']}:{state}",
                projection_kind="attention" if needs or active else "receipt",
                subject_ref=subject_ref, subject_label=labels.get(subject_ref, subject_ref),
                title=("Run needs recovery" if needs else "Run in progress" if active else f"Run {state}"),
                summary="Input and detailed attempts remain on the capability receipt.",
                reason_code=f"capability_{state}", decision_kind="execution",
                attention_state="needs_attention" if needs else "unseen" if active else "resolved",
                actual_destination=str(
                    target.get("name")
                    or placement.get("target_name")
                    or (attempt["destination"] if attempt else row["requested_placement"])
                ),
                authority_basis="explicit_run", attempt=int(attempt["attempt_index"]) if attempt else None,
                outcome=str(attempt["state"] if attempt else state), timestamp=str(row["updated_at"]),
                correlation_id=str(row["correlation_id"]), source_kind="capability_invocation",
                source_id=str(row["id"]), source_api=f"/api/invocations/{row['id']}",
                detail_url=f"/?open={rid}", severity="error" if needs else "normal",
            ))
        return result

    def _dictation(self, conn: Any) -> list[DeskProjection]:
        result = []
        for row in conn.execute("SELECT * FROM dictation_journal").fetchall():
            warnings = self._json_loads_list(row["warnings"])
            needs = bool(warnings)
            target = str(row["target_profile"] or "active_app")
            project_root = str(row["project_root"] or "").strip()
            subject_ref = f"project:{project_root}" if project_root else f"integration:{target}"
            subject_label = project_root.rsplit("/", 1)[-1] if project_root else target
            result.append(DeskProjection(
                id=f"dictation:{row['id']}:{'warning' if needs else 'complete'}",
                projection_kind="attention" if needs else "receipt",
                subject_ref=subject_ref, subject_label=subject_label,
                title="Dictation needs review" if needs else "Dictation delivered",
                summary="Transcript, final text, timing, and warnings remain in the private Dictation journal.",
                reason_code="dictation_warning" if needs else "dictation_complete",
                decision_kind="delivery",
                attention_state="needs_attention" if needs else "resolved",
                actual_destination=target, authority_basis="explicit_dictation",
                attempt=1, outcome="warning" if needs else "completed",
                timestamp=str(row["created_at"]), correlation_id=f"dictation:{row['id']}",
                source_kind="dictation_journal", source_id=str(row["id"]),
                source_api="/api/dictation/journal", detail_url="/history?kind=dictation",
                severity="warning" if needs else "normal",
            ))
        return result

    def _steering(self, conn: Any) -> list[DeskProjection]:
        result = []
        for row in conn.execute("SELECT * FROM steering_audit").fetchall():
            outcome = str(row["outcome"])
            refused = outcome != "delivered"
            key = str(row["session_key"])
            result.append(DeskProjection(
                id=f"steering:{row['id']}", projection_kind="attention" if refused else "receipt",
                subject_ref=f"coder_session:{key}", subject_label=key,
                title="Coder steer refused" if refused else "Coder steer delivered",
                summary="The source audit retains the bounded text fingerprint and delivery detail.",
                reason_code=f"steering_{outcome}", decision_kind="execution",
                attention_state="needs_attention" if refused else "resolved",
                actual_destination=str(row["pane_id"] or "unresolved pane"),
                authority_basis="armed_pane_grant", attempt=1, outcome=outcome,
                timestamp=str(row["ts"]), correlation_id=f"steering:{key}",
                source_kind="steering_audit", source_id=str(row["id"]),
                source_api=f"/api/coders/steering/audit?session_key={key}",
                detail_url=f"/?open={key}", severity="error" if refused else "normal",
            ))
        return result

    def _meetings(self, conn: Any, meetings: dict[str, str]) -> list[DeskProjection]:
        result = []
        for row in conn.execute("SELECT * FROM meetings").fetchall():
            status = str(row["capture_status"] or "finalized")
            needs = status in {"capture_failed", "recoverable", "recovered"}
            active = status in {"provisional", "recording"}
            result.append(DeskProjection(
                id=f"meeting:{row['id']}:capture:{status}",
                projection_kind="attention" if needs or active else "receipt",
                subject_ref=f"meeting:{row['id']}", subject_label=meetings[str(row["id"])],
                title="Meeting capture needs recovery" if needs else "Meeting is recording" if active else "Meeting saved",
                summary="Open the Meeting for its durable checkpoint, transcript, and recovery actions.",
                reason_code=f"capture_{status}", decision_kind="recovery",
                attention_state="needs_attention" if needs else "unseen" if active else "resolved",
                actual_destination="this_machine", authority_basis="explicit_capture",
                attempt=None, outcome=status, timestamp=str(row["updated_at"]),
                correlation_id=f"meeting:{row['id']}", source_kind="meeting",
                source_id=str(row["id"]), source_api=f"/api/meetings/{row['id']}",
                detail_url=f"/history?meeting={row['id']}", severity="error" if needs else "normal",
            ))
        return result

    def _sync_conflicts(self, conn: Any, meetings: dict[str, str]) -> list[DeskProjection]:
        result = []
        rows = conn.execute("SELECT * FROM meeting_sync_conflicts").fetchall()
        for row in rows:
            resolved = bool(row["resolved_at"])
            mid = str(row["meeting_id"])
            result.append(DeskProjection(
                id=f"sync_conflict:{row['id']}:{'resolved' if resolved else 'open'}",
                projection_kind="receipt" if resolved else "attention",
                subject_ref=f"meeting:{mid}", subject_label=meetings.get(mid, "Meeting"),
                title="Sync conflict resolved" if resolved else "Meeting sync needs a choice",
                summary="Both values remain in the source conflict record; no meeting content is copied here.",
                reason_code="sync_conflict_resolved" if resolved else "sync_conflict_open",
                decision_kind="sync", attention_state="resolved" if resolved else "needs_attention",
                actual_destination="paired_device", authority_basis="sync_conflict_policy",
                attempt=None, outcome="resolved" if resolved else "blocked",
                timestamp=str(row["resolved_at"] or row["detected_at"]),
                correlation_id=f"meeting:{mid}", source_kind="meeting_sync_conflict",
                source_id=str(row["id"]), source_api=f"/api/meetings/{mid}/sync-conflicts",
                detail_url=f"/history?meeting={mid}", severity="warning",
            ))
        return result

    def _artifacts(self, conn: Any) -> list[DeskProjection]:
        result = []
        for row in conn.execute("SELECT * FROM artifacts").fetchall():
            status = str(row["status"])
            needs = status in {"draft", "needs_review"}
            result.append(DeskProjection(
                id=f"artifact:{row['id']}:{status}",
                projection_kind="attention" if needs else "receipt",
                subject_ref=f"artifact:{row['id']}", subject_label=str(row["title"]),
                title="Artifact needs review" if needs else f"Artifact {status}",
                summary="Open the Artifact to inspect its content and cited source records.",
                reason_code=f"artifact_{status}", decision_kind="review",
                attention_state="needs_attention" if needs else "resolved",
                actual_destination="this_machine", authority_basis="content_review",
                attempt=None, outcome=status, timestamp=str(row["updated_at"]),
                correlation_id=(f"meeting:{row['meeting_id']}" if row["meeting_id"] else None),
                source_kind="artifact", source_id=str(row["id"]),
                source_api=(f"/api/meetings/{row['meeting_id']}/artifacts" if row["meeting_id"] else "/api/sync/pull"),
                detail_url=f"/?open={row['id']}",
            ))
        return result

    def _jobs(self, conn: Any, meetings: dict[str, str]) -> list[DeskProjection]:
        result = []
        for table, source_kind in (("intel_jobs", "intel_job"), ("plugin_run_jobs", "plugin_job")):
            for row in conn.execute(f"SELECT * FROM {table}").fetchall():
                state = str(row["status"])
                if state not in {"queued", "running", "failed"}:
                    continue
                mid = str(row["meeting_id"])
                failed = state == "failed"
                source_id = mid if table == "intel_jobs" else str(row["id"])
                label = "Meeting intelligence" if table == "intel_jobs" else str(row["plugin_id"])
                result.append(DeskProjection(
                    id=f"{source_kind}:{source_id}:{state}", projection_kind="attention",
                    subject_ref=f"meeting:{mid}", subject_label=meetings.get(mid, "Meeting"),
                    title=f"{label} {'failed' if failed else state}",
                    summary="The source queue retains retry history and error detail.",
                    reason_code=f"{source_kind}_{state}", decision_kind="execution",
                    attention_state="needs_attention" if failed else "unseen",
                    actual_destination="configured_inference_target", authority_basis="configured_queue",
                    attempt=int(row["attempts"]), outcome=state, timestamp=str(row["updated_at"]),
                    correlation_id=f"meeting:{mid}", source_kind=source_kind,
                    source_id=source_id, source_api="/api/intel/jobs" if table == "intel_jobs" else "/api/plugin-jobs",
                    detail_url=f"/history?meeting={mid}", severity="error" if failed else "normal",
                ))
        return result

    def _cadence(self, conn: Any) -> list[DeskProjection]:
        result = []
        for row in conn.execute("SELECT * FROM cadence_loops").fetchall():
            status = str(row["status"])
            actionable = status in {"open", "snoozed", "delegated"}
            source_type = str(row["source_type"])
            source_id = str(row["source_id"])
            if source_type == "agent_question":
                subject_ref = f"coder_session:{source_id}"
            elif source_type == "meeting_action":
                action = conn.execute(
                    "SELECT meeting_id FROM action_items WHERE id=?", (source_id,)
                ).fetchone()
                subject_ref = f"meeting:{action['meeting_id']}" if action else f"action_item:{source_id}"
            elif source_type == "proposal":
                proposal = conn.execute(
                    "SELECT meeting_id,target FROM actuator_proposals WHERE id=?", (source_id,)
                ).fetchone()
                subject_ref = (
                    f"meeting:{proposal['meeting_id']}"
                    if proposal and proposal["meeting_id"]
                    else f"integration:{proposal['target']}" if proposal else f"proposal:{source_id}"
                )
            else:
                subject_ref = f"{source_type}:{source_id}"
            result.append(DeskProjection(
                id=f"cadence:{row['id']}:{status}",
                projection_kind="attention" if actionable else "receipt",
                subject_ref=subject_ref, subject_label=str(row["title"]),
                title="Cadence loop needs you" if actionable else f"Cadence loop {status}",
                summary="Open Cadence for evidence and the prepared next action.",
                reason_code=f"cadence_{status}", decision_kind="attention",
                attention_state="needs_attention" if actionable else "resolved",
                actual_destination="this_machine", authority_basis="cadence_policy",
                attempt=int(row["nudge_count"]), outcome=status, timestamp=str(row["updated_at"]),
                correlation_id=f"cadence:{row['id']}", source_kind="cadence_loop",
                source_id=str(row["id"]), source_api=f"/api/cadence/loops/{row['id']}",
                detail_url="/cadence", severity="warning" if row["priority"] in {"high", "urgent"} else "normal",
            ))
        return result


__all__ = ["DeskProjection", "ProjectionRepository"]
