"""IntelRepository — the deferred-intel jobs/attempts queue.

Extracted verbatim from core.py in Phase 31 (HS-31-02). Intel *snapshots* live
with MeetingRepository (embedded in MeetingState); this repo owns the queue:
intel_jobs, intel_job_attempts, and meeting intel-status updates.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime
from typing import Optional, Any, Callable, Mapping, Sequence

from ..logging_config import get_logger
from .base import BaseRepository
from .models import IntelJob, IntelQueueSummary, IntelJobAttempt

log = get_logger("db.intel")

def _work_descriptor(
    raw: str,
) -> tuple[
    tuple[str, ...],
    tuple[float, ...],
    tuple[tuple[int, float], ...],
    tuple[dict[str, Any], ...],
    dict[str, Any],
]:
    """Read the backward-compatible, content-free displaced-work descriptor.

    C1 initially persisted a plain slug list.  Bound bookmark execution also
    needs the operation set frozen before parent admission, so new rows use a
    small object carrying the slugs and bookmark timestamps; old rows remain
    readable as their original list.
    """
    try:
        parsed = json.loads(raw or "[]")
    except (TypeError, ValueError):
        return (), (), (), (), {}
    if isinstance(parsed, list):
        return tuple(str(item) for item in parsed if str(item).strip()), (), (), (), {}
    if not isinstance(parsed, dict):
        return (), (), (), (), {}
    slugs = parsed.get("slugs", [])
    timestamps = parsed.get("bookmark_timestamps", [])
    frozen: list[float] = []
    if isinstance(timestamps, list):
        for value in timestamps:
            try:
                frozen.append(float(value))
            except (TypeError, ValueError):
                continue
    operations: list[tuple[int, float]] = []
    raw_operations = parsed.get("bookmark_operations", [])
    if isinstance(raw_operations, list):
        for value in raw_operations:
            if not isinstance(value, dict):
                continue
            try:
                operations.append((int(value["id"]), float(value["timestamp"])))
            except (KeyError, TypeError, ValueError):
                continue
    # v2 rows freeze timestamps only; retain them as unique synthetic operation
    # identities so old descriptors remain executable without mutable discovery.
    if not operations:
        operations = [(index, timestamp) for index, timestamp in enumerate(frozen, 1)]
    plugin_members: list[dict[str, Any]] = []
    raw_plugins = parsed.get("plugin_members", [])
    if isinstance(raw_plugins, list):
        for value in raw_plugins:
            if not isinstance(value, dict):
                continue
            capability_id = str(value.get("capability_id") or "").strip()
            plugin_id = str(value.get("plugin_id") or "").strip()
            revision = str(value.get("plugin_definition_revision") or "").strip()
            schema_sha256 = str(value.get("schema_sha256") or "").strip()
            output_schema = value.get("output_schema")
            if (
                capability_id != f"meeting.plugin.{plugin_id}"
                or not plugin_id
                or not revision
                or not schema_sha256
                or not isinstance(output_schema, dict)
            ):
                continue
            try:
                capability_revision = int(value.get("capability_revision") or 0)
            except (TypeError, ValueError):
                continue
            if capability_revision <= 0:
                continue
            plugin_members.append(
                {
                    "capability_id": capability_id,
                    "capability_revision": capability_revision,
                    "plugin_id": plugin_id,
                    "plugin_definition_revision": revision,
                    "schema_sha256": schema_sha256,
                    "output_schema": dict(output_schema),
                }
            )
    route = parsed.get("plugin_route")
    return (
        tuple(str(item) for item in slugs if str(item).strip())
        if isinstance(slugs, list) else (),
        tuple(frozen),
        tuple(operations),
        tuple(plugin_members),
        dict(route) if isinstance(route, dict) else {},
    )


def _displaced_work(row: Any) -> tuple[str, ...]:
    """The structured displaced-work slugs on one intel_jobs row (HS-131-08)."""
    if "displaced_work" not in set(row.keys()):
        return ()
    return _work_descriptor(str(row["displaced_work"] or "[]"))[0]


def _frozen_bookmark_timestamps(row: Any) -> tuple[float, ...]:
    """Return the immutable label-operation timestamps for a bound queue job."""
    if "displaced_work" not in set(row.keys()):
        return ()
    return _work_descriptor(str(row["displaced_work"] or "[]"))[1]


def _frozen_bookmark_operations(row: Any) -> tuple[tuple[int, float], ...]:
    """Return every immutable bookmark operation identity and timestamp."""
    if "displaced_work" not in set(row.keys()):
        return ()
    return _work_descriptor(str(row["displaced_work"] or "[]"))[2]


def _frozen_plugin_members(row: Any) -> tuple[dict[str, Any], ...]:
    """Return exact installed-plugin authority frozen with a C2 descriptor."""
    if "displaced_work" not in set(row.keys()):
        return ()
    return _work_descriptor(str(row["displaced_work"] or "[]"))[3]


def _frozen_plugin_route(row: Any) -> dict[str, Any]:
    """Return the content-free router decision frozen at bound claim planning."""
    if "displaced_work" not in set(row.keys()):
        return {}
    return _work_descriptor(str(row["displaced_work"] or "[]"))[4]


def _freeze_displaced_work(
    conn: Any,
    meeting_id: str,
    displaced_work: Sequence[str],
    *,
    plugin_members: Sequence[Mapping[str, Any]] = (),
    plugin_route: Mapping[str, Any] | None = None,
    recovery_origin_job_id: str | None = None,
) -> str:
    """Freeze content-free displaced operations before a parent can be admitted."""
    slugs = tuple(str(item) for item in displaced_work if str(item).strip())
    operations: tuple[tuple[int, float], ...] = ()
    if "bookmark-labels" in slugs:
        rows = conn.execute(
            "SELECT id,timestamp FROM bookmarks WHERE meeting_id=? ORDER BY timestamp,id",
            (meeting_id,),
        ).fetchall()
        operations = tuple((int(row["id"]), float(row["timestamp"])) for row in rows)
    return json.dumps(
        {
            "schema": "MeetingDeferredIntelWorkDescriptor@4",
            "slugs": list(slugs),
            "bookmark_timestamps": [timestamp for _, timestamp in operations],
            "bookmark_operations": [
                {"id": bookmark_id, "timestamp": timestamp}
                for bookmark_id, timestamp in operations
            ],
            # Exact capability authority for every planned plugin, never a host
            # string or mutable runtime lookup.  The output schema is retained so
            # a revision change after claim cannot reinterpret a queued child.
            "plugin_members": [dict(member) for member in plugin_members],
            "plugin_route": dict(plugin_route or {}),
            # Unknown Stop recovery has a new immutable descriptor as well as an
            # origin link.  That keeps the forever-reserved original and the
            # fresh normal admission simultaneously live without weakening the
            # one-live-owner descriptor index.
            **({"recovery_origin_job_id": recovery_origin_job_id}
               if recovery_origin_job_id else {}),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


MANUAL_INTEL_RETRY_REASON = "Retry remaining requested."
ROUTED_INTEL_RETRY_REASON = "Retry remaining routed intelligence requested."

_ACTIVE_JOB_STATUSES = ("reserved", "queued", "claimed", "running", "failed")
_TERMINAL_JOB_STATUSES = ("succeeded", "superseded", "skipped")

# A C1 bound queue row may have exactly one live executor across worker, HTTP,
# and CLI processes. The bearer is renewed by the runner; a crashed runner leaves
# a finite stale window that stored-ID recovery may take over with a new epoch.
BOUND_EXECUTOR_LEASE_SECONDS = 15.0

# Readers must select a lineage leaf before deciding whether it is unresolved.
# Filtering terminal successors first resurrects a failed ancestor after retry
# success, which lies to the Desk and makes an already-ready Meeting retryable.
_CURRENT_LINEAGE_CTE = """
WITH lineage_leaves AS (
    SELECT j.* FROM intel_jobs j
    WHERE NOT EXISTS (
        SELECT 1 FROM intel_jobs successor WHERE successor.origin_job_id=j.job_id
    )
), current_jobs AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY meeting_id
        ORDER BY requested_at DESC, updated_at DESC, job_id DESC
    ) AS current_rank
    FROM lineage_leaves
)
"""


def _work_descriptor_sha256(
    meeting_id: str, transcript_hash: str, displaced_work: str,
) -> str:
    """Hash the content-free work descriptor frozen with a job."""
    try:
        work = json.loads(displaced_work or "[]")
    except (TypeError, ValueError):
        work = []
    payload = json.dumps(
        {
            "schema": "MeetingDeferredIntelWorkDescriptor@1",
            "meeting_id": meeting_id,
            "transcript_hash": transcript_hash,
            "displaced_work": work if isinstance(work, (list, dict)) else [],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _job_id(
    meeting_id: str,
    transcript_hash: str,
    work_descriptor_sha256: str,
    requested_at: str,
    origin_job_id: str | None = None,
) -> str:
    """Derive a deterministic job ID without carrying private input bytes."""
    material = "\x1f".join(
        ("MeetingDeferredIntelJob@1", meeting_id, transcript_hash,
         work_descriptor_sha256, requested_at, origin_job_id or "")
    )
    return "ij_" + hashlib.sha256(material.encode("utf-8")).hexdigest()


def _claim_id(job_id: str) -> str:
    return "ic_" + hashlib.sha256(("claim@1:" + job_id).encode("utf-8")).hexdigest()


def _bound_command_id(job_id: str, kind: str) -> str:
    """Name durable bound commands from the immutable queue job identity."""
    digest = hashlib.sha256(f"{kind}@1:{job_id}".encode("utf-8")).hexdigest()
    return f"{kind}_{digest}"


def _successor_posture(old: Any) -> tuple[str, str]:
    """Reserve successors until a bound predecessor has a terminal receipt."""
    if str(old["parent_operation_id"] or "").strip():
        return "reserved", "awaiting_parent_terminal"
    return "queued", "queued"


def _durable_transcript_hash(conn: Any, meeting_id: str) -> str:
    """Recompute the queue fence from persisted segment fields only."""
    rows = conn.execute(
        """SELECT text,speaker,start_time,end_time FROM segments WHERE meeting_id=?
           ORDER BY start_time,id""",
        (meeting_id,),
    ).fetchall()
    payload = "\n".join(
        f"{float(row['start_time']):.3f}|{float(row['end_time']):.3f}|"
        f"{row['speaker']}|{row['text']}" for row in rows
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _plan_installed_plugin_members(
    conn: Any, meeting_id: str,
) -> tuple[tuple[dict[str, Any], ...], dict[str, Any]]:
    """Freeze the routed installed-plugin set from the composed registry.

    This is claim planning, not execution: it reads durable Meeting text only to
    derive the deterministic MIR route, then stores IDs/revisions/schemas and
    route metadata without retaining transcript bytes.  Config and a live host
    are intentionally absent from this boundary.
    """
    from ..inference_capabilities import process_inference_capability_registry
    from ..plugins.router import preview_route_from_transcript

    rows = conn.execute(
        "SELECT text,speaker FROM segments WHERE meeting_id=? ORDER BY start_time,id",
        (meeting_id,),
    ).fetchall()
    transcript = "\n".join(
        f"{str(row['speaker'] or '').strip()}: {str(row['text'] or '').strip()}".strip(": ")
        for row in rows
        if str(row["text"] or "").strip()
    )
    decision = preview_route_from_transcript(
        profile=None, transcript=transcript, tags=None,
    ).to_dict()
    registry = process_inference_capability_registry()
    members: list[dict[str, Any]] = []
    for plugin_id in decision.get("plugin_chain") or []:
        plugin_id = str(plugin_id).strip()
        capability_id = f"meeting.plugin.{plugin_id}"
        definition = registry.require(capability_id)
        if (
            definition.plugin_id != plugin_id
            or not definition.plugin_definition_revision
            or definition.id != capability_id
        ):
            raise ValueError(f"installed plugin capability is not exact: {plugin_id}")
        canonical = definition.canonical_dict()
        members.append(
            {
                "capability_id": definition.id,
                "capability_revision": definition.revision,
                "plugin_id": definition.plugin_id,
                "plugin_definition_revision": definition.plugin_definition_revision,
                "schema_sha256": definition.schema_sha256,
                "output_schema": dict(canonical["output_schema"]),
            }
        )
    route = {
        "profile": str(decision.get("profile") or "balanced"),
        "threshold": float(decision.get("threshold") or 0.0),
        "active_intents": [str(item) for item in decision.get("active_intents") or []],
        "intent_scores": {
            str(key): float(value)
            for key, value in dict(decision.get("intent_scores") or {}).items()
        },
        "plugin_chain": [str(item) for item in decision.get("plugin_chain") or []],
    }
    return tuple(members), route


class IntelRepository(BaseRepository):
    table = "intel"

    """Persistence for the deferred-intel queue (jobs, attempts, status)."""

    def enqueue_intel_job(
        self,
        meeting_id: str,
        *,
        transcript_hash: str,
        reason: Optional[str] = None,
        displaced_work: Sequence[str] = (),
        conn: Any | None = None,
        legacy_displaced_work: bool = False,
    ) -> str:
        """Queue or refresh deferred intelligence processing for a meeting.

        Passing the caller's open SQLite connection composes this Meeting-keyed
        upsert with its Stop fence.  The public method intentionally remains the
        one queue authority: callers must not duplicate its payload or status
        write in a sibling transaction.
        """
        if conn is None:
            with self._connection() as owned_conn:
                return self._enqueue_intel_job_in_transaction(
                    owned_conn,
                    meeting_id,
                    transcript_hash=transcript_hash,
                    reason=reason,
                    displaced_work=displaced_work,
                    legacy_displaced_work=legacy_displaced_work,
                )
        return self._enqueue_intel_job_in_transaction(
            conn,
            meeting_id,
            transcript_hash=transcript_hash,
            reason=reason,
            displaced_work=displaced_work,
            legacy_displaced_work=legacy_displaced_work,
        )

    @staticmethod
    def _enqueue_intel_job_in_transaction(
        conn: Any,
        meeting_id: str,
        *,
        transcript_hash: str,
        reason: Optional[str],
        displaced_work: Sequence[str],
        legacy_displaced_work: bool,
    ) -> str:
        """Create or refresh one immutable descriptor without reclaiming an owner.

        A matching queued row is idempotent.  A changed descriptor terminalizes
        the old non-running row and receives a fresh linked job ID; a running
        owner is deliberately left untouched (the Phase-B race fence).
        """
        now = datetime.now().isoformat()
        # Stop's Phase-B Meeting-keyed upsert is the durable handoff boundary.
        # It deliberately persists its historic plain slug list so retry/recovery
        # observes the same row even before C1 replaces it with a bound descriptor.
        work = (
            json.dumps(list(displaced_work), separators=(",", ":"))
            if legacy_displaced_work
            else _freeze_displaced_work(conn, meeting_id, displaced_work)
        )
        descriptor = _work_descriptor_sha256(meeting_id, transcript_hash, work)
        current = conn.execute(
            _CURRENT_LINEAGE_CTE + """
            SELECT * FROM current_jobs WHERE meeting_id=? AND current_rank=1 LIMIT 1
            """,
            (meeting_id,),
        ).fetchone()
        # Stop/recovery persist the historic plain list as their idempotency
        # boundary.  C1 may later replace that leaf with a V3 descriptor to freeze
        # bookmark IDs, but both encodings name the same Meeting handoff.  Never
        # let replay of the plain form supersede an unchanged V3 leaf (especially
        # a completed one) and reopen an already-ready Meeting.
        if (
            legacy_displaced_work
            and current is not None
            and str(current["transcript_hash"]) == transcript_hash
            and _work_descriptor(str(current["displaced_work"] or "[]"))[0]
            == _work_descriptor(work)[0]
        ):
            return str(current["job_id"])
        if current is not None and str(current["status"]) in {"running", "claimed"}:
            return str(current["job_id"])
        if (current is not None and str(current["status"]) in {"succeeded", "skipped"}
                and str(current["work_descriptor_sha256"]) == descriptor):
            return str(current["job_id"])
        if current is not None and str(current["work_descriptor_sha256"]) == descriptor:
            # Refreshing the same unclaimed descriptor is metadata-only; its
            # immutable work identity and queue ownership do not change.
            conn.execute(
                "UPDATE intel_jobs SET updated_at=?,last_error=? WHERE job_id=?",
                (now, reason, str(current["job_id"])),
            )
            job_id = str(current["job_id"])
        else:
            origin_job_id = str(current["job_id"]) if current is not None else None
            if current is not None:
                conn.execute(
                    """UPDATE intel_jobs SET status='superseded',
                       lifecycle_posture='superseded',updated_at=?
                       WHERE job_id=? AND status NOT IN ('running','claimed')""",
                    (now, origin_job_id),
                )
            job_id = _job_id(
                meeting_id, transcript_hash, descriptor, now, origin_job_id,
            )
            conn.execute(
                """INSERT INTO intel_jobs (
                    job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                    transcript_hash,displaced_work,status,lifecycle_posture,
                    requested_at,updated_at,attempts,last_error
                ) VALUES (?, ?, ?, ?, ?, ?, 'queued', 'queued', ?, ?, 0, ?)""",
                (job_id, meeting_id, origin_job_id, descriptor, transcript_hash,
                 work, now, now, reason),
            )
        conn.execute(
            """UPDATE meetings
            SET intel_status = 'queued', intel_status_detail = ?,
                intel_requested_at = COALESCE(intel_requested_at, ?),
                intel_completed_at = NULL, sync_modified_at = ?,
                updated_at = datetime('now')
            WHERE id = ? AND NOT EXISTS (
                SELECT 1 FROM intel_jobs WHERE meeting_id=?
                  AND status IN ('running','claimed')
            )""",
            (reason or "Queued for later processing.", now, now, meeting_id, meeting_id),
        )
        return job_id

    @staticmethod
    def stop_handoff_planning_reference(meeting_id: str) -> str:
        """Return the content-free planning reference for one live Meeting Stop."""
        return f"meeting-deferred:{meeting_id}"

    def stop_handoff_provider(
        self,
        *,
        meeting_id: str | None = None,
        transcript_hash: str | None = None,
        displaced_work: Sequence[str] = (),
        reason: str | None = None,
    ) -> Any:
        """Build the real queue-owned reserve-inert Stop provider.

        A live Stop supplies its already-frozen Meeting predicate to ``freeze``.
        Restart reconciliation needs only ``reconstruct`` and ``activate``, so it
        deliberately creates this same provider without a freeze plan.  All three
        callbacks use only the connection supplied by the bundle primitive.
        """
        from ..services.inference_parent_route_bundle_service import HandoffEvidenceProvider

        plan = None
        if meeting_id is not None or transcript_hash is not None or displaced_work:
            if not meeting_id or not transcript_hash:
                raise ValueError("Stop handoff requires meeting and transcript evidence")
            plan = {
                "meeting_id": str(meeting_id),
                "transcript_hash": str(transcript_hash),
                "displaced_work": tuple(str(item) for item in displaced_work if str(item).strip()),
                "reason": str(reason or "Queued deferred meeting intelligence."),
            }

        def freeze(conn: Any, planning_reference: str, context: Mapping[str, Any]) -> Mapping[str, Any]:
            if plan is None or planning_reference != self.stop_handoff_planning_reference(plan["meeting_id"]):
                raise ValueError("Stop handoff freeze plan is unavailable")
            return self._reserve_stop_handoff_in_transaction(
                conn,
                planning_reference=planning_reference,
                command_id=str(context["command_id"]),
                parent_operation_id=str(context["parent_operation_id"]),
                bundle_id=str(context["bundle"]["id"]),
                meeting_id=plan["meeting_id"],
                transcript_hash=plan["transcript_hash"],
                displaced_work=plan["displaced_work"],
                reason=plan["reason"],
            )

        return HandoffEvidenceProvider(
            "meeting-deferred-queue",
            1,
            freeze,
            self._reconstruct_stop_handoff_evidence,
            self._activate_stop_handoff_in_transaction,
        )

    @staticmethod
    def _reconstruct_stop_handoff_evidence(conn: Any, evidence_ref: str) -> Mapping[str, Any]:
        """Read the queue-owned reservation and activation marker only.

        This deliberately does not inspect the handoff settlement table.  The
        append-only activation event is the queue's independent lifecycle witness.
        """
        row = conn.execute(
            "SELECT * FROM intel_jobs WHERE job_id=?", (str(evidence_ref),)
        ).fetchone()
        if row is None:
            raise ValueError("Stop handoff reservation is missing")
        marker = conn.execute(
            """SELECT 1 FROM intel_job_attempts
                 WHERE job_id=? AND event_kind='handoff_activated' LIMIT 1""",
            (str(evidence_ref),),
        ).fetchone()
        status = str(row["status"])
        active = marker is not None
        if (active and status == "reserved") or (not active and status != "reserved"):
            raise ValueError("Stop handoff queue lifecycle is inconsistent")
        return {
            "schema": "InferenceParentHandoffEvidence@1",
            "planning_reference": IntelRepository.stop_handoff_planning_reference(
                str(row["meeting_id"])
            ),
            "evidence_ref": str(row["job_id"]),
            "evidence_sha256": str(row["work_descriptor_sha256"]),
            "state": "active" if active else "reserved",
        }

    @staticmethod
    def _activate_stop_handoff_in_transaction(conn: Any, evidence_ref: str) -> None:
        """Mark a reserved handoff job active and make it normally claimable."""
        row = conn.execute(
            "SELECT * FROM intel_jobs WHERE job_id=?", (str(evidence_ref),)
        ).fetchone()
        if row is None or str(row["status"]) != "reserved":
            raise ValueError("Stop handoff reservation cannot activate")
        now = datetime.now().isoformat()
        changed = conn.execute(
            """UPDATE intel_jobs SET status='queued',lifecycle_posture='queued',
                   updated_at=?,last_error=NULL WHERE job_id=? AND status='reserved'""",
            (now, str(evidence_ref)),
        )
        if changed.rowcount != 1:
            raise ValueError("Stop handoff activation lost its reservation")
        conn.execute(
            """INSERT INTO intel_job_attempts (
                meeting_id,job_id,origin_job_id,claim_id,parent_operation_id,bundle_id,
                event_kind,attempt,outcome,error,retry_at,created_at
            ) VALUES (?,?,NULL,NULL,NULL,NULL,'handoff_activated',0,'activated',NULL,NULL,?)""",
            (str(row["meeting_id"]), str(evidence_ref), now),
        )

    @staticmethod
    def _reserve_stop_handoff_in_transaction(
        conn: Any,
        *,
        planning_reference: str,
        command_id: str,
        parent_operation_id: str,
        bundle_id: str,
        meeting_id: str,
        transcript_hash: str,
        displaced_work: Sequence[str],
        reason: str,
    ) -> Mapping[str, Any]:
        """Persist only an inert queue reservation inside the Stop transaction."""
        now = datetime.now().isoformat()
        # A live Stop runs before the final Meeting checkpoint.  Retain the
        # immutable displaced slug set now; C1's existing normal claim converts
        # it to the V3 bookmark-operation descriptor only after the checkpoint,
        # rather than freezing a partial pre-save bookmark list.
        work = json.dumps(list(displaced_work), separators=(",", ":"))
        descriptor = _work_descriptor_sha256(meeting_id, transcript_hash, work)
        # The command is already a durable Stop idempotency key.  Deriving the
        # reservation identity from it prevents a fresh identity on callback
        # replay while retaining no transcript bytes in the identity material.
        job_id = _job_id(
            meeting_id, transcript_hash, descriptor, f"handoff:{command_id}", None
        )
        conn.execute(
            """INSERT INTO intel_jobs (
                job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                transcript_hash,displaced_work,status,lifecycle_posture,
                requested_at,updated_at,attempts,last_error
            ) VALUES (?,?,?,?,?,?,'reserved','reserved',?,?,0,?)""",
            (job_id, meeting_id, None, descriptor, transcript_hash, work, now, now, reason),
        )
        conn.execute(
            """INSERT INTO intel_job_attempts (
                meeting_id,job_id,origin_job_id,claim_id,parent_operation_id,bundle_id,
                event_kind,attempt,outcome,error,retry_at,created_at
            ) VALUES (?,?,NULL,NULL,?,?,'handoff_reserved',0,'reserved',NULL,NULL,?)""",
            (meeting_id, job_id, parent_operation_id, bundle_id, now),
        )
        conn.execute(
            """UPDATE meetings SET intel_status='queued',intel_status_detail=?,
                   intel_completed_at=NULL,sync_modified_at=?,updated_at=datetime('now')
                 WHERE id=?""",
            (reason, now, meeting_id),
        )
        return {
            "schema": "InferenceParentHandoffEvidence@1",
            "planning_reference": planning_reference,
            "evidence_ref": job_id,
            "evidence_sha256": descriptor,
            "state": "reserved",
        }

    @staticmethod
    def _is_unsettled_stop_reservation_in_transaction(conn: Any, job: Any | None) -> bool:
        """Whether this exact leaf is an inert C3 Stop reservation.

        Generic Retry/Skip may never rewrite provider-owned work while the Stop
        primitive has no settlement.  Both queue lifecycle fields are checked so
        an old skipped/superseded record cannot later qualify for unknown recovery.
        """
        if (
            job is None
            or str(job["status"] or "") != "reserved"
            or str(job["lifecycle_posture"] or "") != "reserved"
        ):
            return False
        return conn.execute(
            """SELECT 1 FROM inference_parent_stop_handoffs h
                 LEFT JOIN inference_parent_stop_handoff_settlements s
                   ON s.command_id=h.command_id
                WHERE h.evidence_ref=?
                  AND h.evidence_provider_id='meeting-deferred-queue'
                  AND h.evidence_provider_revision=1
                  AND s.command_id IS NULL
                LIMIT 1""",
            (str(job["job_id"]),),
        ).fetchone() is not None

    def has_unsettled_stop_reservation(self, meeting_id: str) -> bool:
        """Return whether the current lineage leaf is an inert Stop handoff."""
        with self._connection() as conn:
            job = conn.execute(
                _CURRENT_LINEAGE_CTE + """
                SELECT * FROM current_jobs WHERE meeting_id=? AND current_rank=1 LIMIT 1
                """,
                (meeting_id,),
            ).fetchone()
            return self._is_unsettled_stop_reservation_in_transaction(conn, job)

    def pending_stop_handoff_commands(self) -> list[str]:
        """Return this adopter's unsettled handoffs for normal queue recovery."""
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT h.command_id FROM inference_parent_stop_handoffs h
                     LEFT JOIN inference_parent_stop_handoff_settlements s
                       ON s.command_id=h.command_id
                    WHERE h.evidence_provider_id='meeting-deferred-queue'
                      AND h.evidence_provider_revision=1
                      AND s.command_id IS NULL
                    ORDER BY h.created_at,h.command_id"""
            ).fetchall()
        return [str(row["command_id"]) for row in rows]

    def admit_unknown_stop_handoff_recoveries(self) -> int:
        """Fresh-admit unknown Stop work without ever touching its reservation.

        The original queue row remains ``reserved`` forever.  A distinct
        descriptor and origin link make the local re-run ordinary queue work;
        normal SERVICE route binding later enforces exact saved assignments for
        any cross-boundary placement.
        """
        unknown = (
            "dispatch_outcome_unknown", "physical_outcome_unknown", "effect_indeterminate"
        )
        now = datetime.now().isoformat()
        created = 0
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                rows = conn.execute(
                    """SELECT h.command_id,h.parent_operation_id,h.bundle_id,h.evidence_ref,
                              j.meeting_id,j.transcript_hash,j.displaced_work,
                              j.work_descriptor_sha256,j.attempts
                         FROM inference_parent_stop_handoffs h
                         JOIN intel_jobs j ON j.job_id=h.evidence_ref
                         LEFT JOIN inference_parent_stop_handoff_settlements s
                           ON s.command_id=h.command_id
                        WHERE h.evidence_provider_id='meeting-deferred-queue'
                          AND h.evidence_provider_revision=1
                          AND j.status='reserved'
                          AND j.lifecycle_posture='reserved'
                          AND s.command_id IS NULL
                          AND NOT EXISTS (
                              SELECT 1
                                FROM inference_parent_stop_handoff_executions x
                                JOIN inference_route_executions e ON e.id=x.execution_id
                               WHERE x.command_id=h.command_id
                                 AND e.state IN ('active','stopping')
                          )
                          AND EXISTS (
                              SELECT 1
                                FROM inference_parent_stop_handoff_executions x
                                JOIN inference_route_executions e ON e.id=x.execution_id
                               WHERE x.command_id=h.command_id
                                 AND e.terminal_disposition IN (?,?,?)
                          )
                        ORDER BY h.created_at,h.command_id""",
                    unknown,
                ).fetchall()
                for row in rows:
                    old_job_id = str(row["evidence_ref"])
                    existing = conn.execute(
                        "SELECT job_id FROM intel_jobs WHERE origin_job_id=? LIMIT 1",
                        (old_job_id,),
                    ).fetchone()
                    if existing is not None:
                        continue
                    try:
                        raw = json.loads(str(row["displaced_work"] or "{}"))
                    except (TypeError, ValueError):
                        raw = {}
                    if isinstance(raw, list):
                        # The reservation deliberately keeps B-era slugs until
                        # after Stop's final checkpoint. Unknown recovery occurs
                        # later, so freeze concrete bookmark operations through
                        # C1's established descriptor builder before fresh claim.
                        recovery_work = _freeze_displaced_work(
                            conn,
                            str(row["meeting_id"]),
                            tuple(str(item) for item in raw),
                            recovery_origin_job_id=old_job_id,
                        )
                    else:
                        if not isinstance(raw, dict):
                            raw = {"schema": "MeetingDeferredIntelWorkDescriptor@4", "slugs": []}
                        recovery_work = json.dumps(
                            {**raw, "recovery_origin_job_id": old_job_id},
                            sort_keys=True, separators=(",", ":"),
                        )
                    descriptor = _work_descriptor_sha256(
                        str(row["meeting_id"]), str(row["transcript_hash"]), recovery_work,
                    )
                    fresh_job_id = _job_id(
                        str(row["meeting_id"]), str(row["transcript_hash"]), descriptor,
                        f"unknown-recovery:{row['command_id']}", old_job_id,
                    )
                    conn.execute(
                        """INSERT INTO intel_jobs (
                            job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                            transcript_hash,displaced_work,status,lifecycle_posture,
                            requested_at,updated_at,attempts,last_error
                        ) VALUES (?,?,?,?,?,?,'queued','queued',?,?,0,?)""",
                        (fresh_job_id, str(row["meeting_id"]), old_job_id, descriptor,
                         str(row["transcript_hash"]), recovery_work, now, now,
                         "stop_handoff_outcome_unknown"),
                    )
                    conn.execute(
                        """INSERT INTO intel_job_attempts (
                            meeting_id,job_id,origin_job_id,claim_id,parent_operation_id,bundle_id,
                            event_kind,attempt,outcome,error,retry_at,created_at
                        ) VALUES (?,?,NULL,NULL,?,?,'handoff_outcome_unknown',?,'reserved',NULL,NULL,?)""",
                        (str(row["meeting_id"]), old_job_id, str(row["parent_operation_id"]),
                         str(row["bundle_id"]), int(row["attempts"]), now),
                    )
                    conn.execute(
                        """INSERT INTO intel_job_attempts (
                            meeting_id,job_id,origin_job_id,claim_id,parent_operation_id,bundle_id,
                            event_kind,attempt,outcome,error,retry_at,created_at
                        ) VALUES (?,?,?,NULL,NULL,NULL,'handoff_unknown_recovery',0,'queued',NULL,NULL,?)""",
                        (str(row["meeting_id"]), fresh_job_id, old_job_id, now),
                    )
                    conn.execute(
                        """UPDATE meetings SET intel_status='queued',
                               intel_status_detail='stop_handoff_outcome_unknown',
                               intel_completed_at=NULL,sync_modified_at=?,updated_at=datetime('now')
                             WHERE id=?""",
                        (now, str(row["meeting_id"])),
                    )
                    created += 1
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return created

    def get_bound_claimed_intel_job(self) -> Optional[IntelJob]:
        """Return only a stale bound owner eligible for stored-ID recovery.

        A live lease means another worker, HTTP Process request, or CLI owns the
        executor.  Recovering it would be a second runner, not crash recovery.
        Historical C1 rows without a lease are treated as stale so upgrades retain
        their stored-ID recovery path.
        """
        now = time.time()
        with self._connection() as conn:
            row = conn.execute(
                """SELECT * FROM intel_jobs WHERE status IN ('claimed','running')
                   AND parent_operation_id IS NOT NULL AND bundle_id IS NOT NULL
                   AND bundle_sha256 IS NOT NULL AND claim_id IS NOT NULL
                   AND (executor_lease_expires_at IS NULL OR executor_lease_expires_at<=?)
                   ORDER BY requested_at ASC LIMIT 1""",
                (now,),
            ).fetchone()
        return self._job_from_row(row) if row is not None else None

    def take_over_stale_bound_executor(self, job_id: str) -> Optional[IntelJob]:
        """Atomically fence a stale C1 executor and return its new lease bearer."""
        now = time.time()
        token = "intel_executor_" + uuid.uuid4().hex
        expires_at = now + BOUND_EXECUTOR_LEASE_SECONDS
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            result = conn.execute(
                """UPDATE intel_jobs SET executor_lease_token=?,
                       executor_lease_epoch=executor_lease_epoch+1,
                       executor_lease_expires_at=?,updated_at=?
                   WHERE job_id=? AND status IN ('claimed','running')
                     AND parent_operation_id IS NOT NULL AND bundle_id IS NOT NULL
                     AND bundle_sha256 IS NOT NULL AND claim_id IS NOT NULL
                     AND (executor_lease_expires_at IS NULL OR executor_lease_expires_at<=?)""",
                (token, expires_at, datetime.now().isoformat(), job_id, now),
            )
            if result.rowcount != 1:
                conn.rollback()
                return None
            row = conn.execute("SELECT * FROM intel_jobs WHERE job_id=?", (job_id,)).fetchone()
            conn.commit()
        return self._job_from_row(row) if row is not None else None

    def renew_bound_executor_lease(self, job: IntelJob) -> bool:
        """Extend this exact bearer lease; false means takeover/terminality won."""
        if not job.job_id or not job.executor_lease_token or not job.executor_lease_epoch:
            return False
        now = time.time()
        with self._connection() as conn:
            result = conn.execute(
                """UPDATE intel_jobs SET executor_lease_expires_at=?,updated_at=?
                   WHERE job_id=? AND executor_lease_token=? AND executor_lease_epoch=?
                     AND status IN ('claimed','running')""",
                (
                    now + BOUND_EXECUTOR_LEASE_SECONDS, datetime.now().isoformat(),
                    job.job_id, job.executor_lease_token, int(job.executor_lease_epoch),
                ),
            )
            return result.rowcount == 1

    def release_bound_executor_lease(self, job: IntelJob) -> None:
        """Expire an exact executor bearer after its worker returns."""
        if not job.job_id or not job.executor_lease_token or not job.executor_lease_epoch:
            return
        with self._connection() as conn:
            conn.execute(
                """UPDATE intel_jobs SET executor_lease_expires_at=?
                   WHERE job_id=? AND executor_lease_token=? AND executor_lease_epoch=?""",
                (time.time(), job.job_id, job.executor_lease_token, int(job.executor_lease_epoch)),
            )

    def get_bound_terminal_pending_close_intel_job(self) -> Optional[IntelJob]:
        """Recover an old terminal queue row whose bound parent lacks a receipt."""
        with self._connection() as conn:
            row = conn.execute(
                """SELECT j.* FROM intel_jobs j
                   JOIN kernel_parent_runs p ON p.operation_id=j.parent_operation_id
                   LEFT JOIN kernel_receipts r ON r.operation_id=j.parent_operation_id
                   WHERE j.status IN ('failed','superseded','succeeded','skipped')
                     AND j.parent_operation_id IS NOT NULL
                     AND p.state IN ('OPEN','CANCELLING') AND r.operation_id IS NULL
                   ORDER BY j.updated_at ASC LIMIT 1"""
            ).fetchone()
        return self._job_from_row(row) if row is not None else None

    def get_legacy_claimed_intel_job(self) -> Optional[IntelJob]:
        """Return an in-flight pre-C1 owner for compatibility recovery only.

        New descriptors are never selected here: a C1 bound claim always writes
        both parent and bundle references in the same ownership transaction.
        """
        with self._connection() as conn:
            row = conn.execute(
                """SELECT * FROM intel_jobs WHERE status IN ('claimed','running')
                   AND (parent_operation_id IS NULL OR bundle_id IS NULL)
                   ORDER BY requested_at ASC LIMIT 1"""
            ).fetchone()
        return self._job_from_row(row) if row is not None else None

    def claim_next_intel_job(self, *, include_scheduled: bool = False) -> Optional[IntelJob]:
        """Claim the next queued intelligence job for processing."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            # Selection and ownership transition are one SQLite writer epoch.
            conn.execute("BEGIN IMMEDIATE")
            if include_scheduled:
                row = conn.execute(
                    """
                    SELECT j.* FROM intel_jobs j
                    JOIN meetings m ON m.id=j.meeting_id
                    WHERE j.status = 'queued'
                      AND m.capture_status IN ('finalized', 'recovered')
                      AND m.route_fence_pending = 0
                      AND NOT EXISTS (
                          SELECT 1 FROM intel_jobs owner
                          WHERE owner.meeting_id=j.meeting_id
                            AND owner.work_descriptor_sha256=j.work_descriptor_sha256
                            AND owner.status IN ('claimed','running')
                      )
                      AND NOT EXISTS (
                          SELECT 1 FROM intel_jobs predecessor
                          LEFT JOIN kernel_receipts receipt
                            ON receipt.operation_id=predecessor.parent_operation_id
                          WHERE predecessor.job_id=j.origin_job_id
                            AND predecessor.parent_operation_id IS NOT NULL
                            AND receipt.operation_id IS NULL
                      )
                    ORDER BY j.requested_at ASC
                    LIMIT 1
                    """
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT j.* FROM intel_jobs j
                    JOIN meetings m ON m.id=j.meeting_id
                    WHERE j.status = 'queued'
                      AND j.requested_at <= ?
                      AND m.capture_status IN ('finalized', 'recovered')
                      AND m.route_fence_pending = 0
                      AND NOT EXISTS (
                          SELECT 1 FROM intel_jobs owner
                          WHERE owner.meeting_id=j.meeting_id
                            AND owner.work_descriptor_sha256=j.work_descriptor_sha256
                            AND owner.status IN ('claimed','running')
                      )
                      AND NOT EXISTS (
                          SELECT 1 FROM intel_jobs predecessor
                          LEFT JOIN kernel_receipts receipt
                            ON receipt.operation_id=predecessor.parent_operation_id
                          WHERE predecessor.job_id=j.origin_job_id
                            AND predecessor.parent_operation_id IS NOT NULL
                            AND receipt.operation_id IS NULL
                      )
                    ORDER BY j.requested_at ASC
                    LIMIT 1
                    """,
                    (now_iso,),
                ).fetchone()
            if row is None:
                return None

            updated_at = datetime.now().isoformat()
            claim_id = _claim_id(str(row["job_id"]))
            claimed = conn.execute(
                """UPDATE intel_jobs SET status='running', lifecycle_posture='claimed',
                    claim_id=?, attempts=attempts+1, updated_at=?, last_error=NULL
                   WHERE job_id=? AND status='queued'""",
                (claim_id, updated_at, str(row["job_id"])),
            )
            if claimed.rowcount != 1:
                return None

            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'running',
                    intel_status_detail = 'Processing queued meeting intelligence.',
                    sync_modified_at = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (updated_at, row["meeting_id"]),
            )

            return IntelJob(
                meeting_id=row["meeting_id"],
                status="running",
                transcript_hash=row["transcript_hash"],
                requested_at=datetime.fromisoformat(row["requested_at"]),
                updated_at=datetime.fromisoformat(updated_at),
                attempts=int(row["attempts"]) + 1,
                # Preserve the queued reason on the claimed value so the
                # worker can resume the exact incomplete stage. The persisted
                # running row still clears last_error as before.
                last_error=row["last_error"],
                displaced_work=_displaced_work(row),
                job_id=str(row["job_id"]),
                origin_job_id=(str(row["origin_job_id"]) if row["origin_job_id"] else None),
                work_descriptor_sha256=str(row["work_descriptor_sha256"]),
                claim_id=(str(claim_id)),
                lifecycle_posture="claimed",
            )

    def claim_next_intel_job_bound(
        self,
        bind: Callable[[Any, IntelJob, Mapping[str, str]], Mapping[str, str]],
        *,
        include_scheduled: bool = False,
    ) -> Optional[IntelJob]:
        """Grant one queue owner only if its parent/bundle binding commits too.

        ``bind`` is the route-bundle spine's in-connection writer.  It receives
        the caller-owned SQLite connection and deterministic claim/parent/bundle
        command IDs, so a refusal raises and rolls back claim state, binding
        references, and the ledger event as one unit.  This C1 primitive does
        not execute model work; execution is an after-commit concern.
        """
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            due = "" if include_scheduled else " AND j.requested_at <= ?"
            params: tuple[Any, ...] = () if include_scheduled else (now,)
            row = conn.execute(
                """SELECT j.* FROM intel_jobs j JOIN meetings m ON m.id=j.meeting_id
                   WHERE j.status='queued' AND m.capture_status IN ('finalized','recovered')
                     AND m.route_fence_pending=0""" + due + """
                     AND NOT EXISTS (SELECT 1 FROM intel_jobs owner
                         WHERE owner.meeting_id=j.meeting_id
                           AND owner.work_descriptor_sha256=j.work_descriptor_sha256
                           AND owner.status IN ('claimed','running'))
                     AND NOT EXISTS (SELECT 1 FROM intel_jobs predecessor
                         LEFT JOIN kernel_receipts receipt
                           ON receipt.operation_id=predecessor.parent_operation_id
                         WHERE predecessor.job_id=j.origin_job_id
                           AND predecessor.parent_operation_id IS NOT NULL
                           AND receipt.operation_id IS NULL)
                   ORDER BY j.requested_at ASC LIMIT 1""",
                params,
            ).fetchone()
            if row is None:
                return None
            meeting_id, job_id = str(row["meeting_id"]), str(row["job_id"])
            durable_hash = _durable_transcript_hash(conn, meeting_id)
            if durable_hash != str(row["transcript_hash"]):
                work = str(row["displaced_work"])
                descriptor = _work_descriptor_sha256(meeting_id, durable_hash, work)
                conn.execute(
                    """UPDATE intel_jobs SET status='superseded',
                        lifecycle_posture='superseded',updated_at=?,
                        last_error='Transcript changed before bound claim.'
                        WHERE job_id=? AND status='queued'""",
                    (now, job_id),
                )
                fresh_id = _job_id(meeting_id, durable_hash, descriptor, now, job_id)
                conn.execute(
                    """INSERT INTO intel_jobs (
                        job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                        transcript_hash,displaced_work,status,lifecycle_posture,
                        requested_at,updated_at,attempts,last_error
                    ) VALUES (?,?,?,?,?,?,'queued','queued',?,?,0,?)""",
                    (fresh_id, meeting_id, job_id, descriptor, durable_hash, work,
                     now, now, "Transcript changed; queued fresh immutable job."),
                )
                conn.execute(
                    """INSERT INTO intel_job_attempts (
                        meeting_id,job_id,origin_job_id,event_kind,attempt,outcome,error,created_at
                    ) VALUES (?,? ,NULL,'superseded',?,'superseded',?,?)""",
                    (meeting_id, job_id, int(row["attempts"]),
                     "Transcript changed before bound claim.", now),
                )
                return None
            # Phase-B Stop intentionally leaves a plain Meeting-keyed slug list
            # as its idempotent handoff row.  Immediately before C1 parent
            # admission, replace that legacy leaf with a linked descriptor that
            # freezes the concrete bookmark operations.  Thus Stop keeps its
            # one-row contract, while no bound parent is budgeted from mutable
            # bookmarks.
            try:
                legacy_payload = json.loads(str(row["displaced_work"] or "[]"))
            except (TypeError, ValueError):
                legacy_payload = None
            if isinstance(legacy_payload, list):
                frozen_work = _freeze_displaced_work(
                    conn, meeting_id, tuple(str(item) for item in legacy_payload),
                )
                frozen_descriptor = _work_descriptor_sha256(
                    meeting_id, str(row["transcript_hash"]), frozen_work,
                )
                conn.execute(
                    """UPDATE intel_jobs SET status='superseded',
                       lifecycle_posture='superseded',updated_at=?,
                       last_error='Bound descriptor frozen from legacy Stop handoff.'
                       WHERE job_id=? AND status='queued'""",
                    (now, job_id),
                )
                frozen_job_id = _job_id(
                    meeting_id, str(row["transcript_hash"]), frozen_descriptor,
                    now, job_id,
                )
                conn.execute(
                    """INSERT INTO intel_jobs (
                        job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                        transcript_hash,displaced_work,status,lifecycle_posture,
                        requested_at,updated_at,attempts,last_error
                    ) VALUES (?,?,?,?,?,?,'queued','queued',?,?,0,?)""",
                    (
                        frozen_job_id, meeting_id, job_id, frozen_descriptor,
                        str(row["transcript_hash"]), frozen_work, now, now,
                        "Bound descriptor frozen from legacy Stop handoff.",
                    ),
                )
                # `prepare()` opens its own durable kernel-shell transaction.
                # Publish the replacement before releasing this claim epoch so it
                # can see the exact frozen descriptor it is about to bind.
                conn.commit()
                job_id = frozen_job_id
                row = conn.execute(
                    "SELECT * FROM intel_jobs WHERE job_id=?", (job_id,),
                ).fetchone()
                if row is None:
                    return None
            # C2 adds no mutable host/config planning at execution time.  Before
            # the bundle is prepared, replace a pre-C2 queued descriptor with one
            # that names every routed installed plugin's exact registry revision
            # and closed result schema.  A claimed legacy row never reaches here.
            if not _frozen_plugin_members(row):
                try:
                    plugin_members, plugin_route = _plan_installed_plugin_members(
                        conn, meeting_id,
                    )
                except Exception as exc:
                    # An unknown/non-exact plugin can never be smuggled through
                    # as a runtime string.  Make the queued admission refusal
                    # terminal and ledgered before the worker reports progress.
                    from ..services.errors import ServiceError

                    conn.rollback()
                    refusal = ServiceError(
                        "meeting_deferred_plugin_plan_invalid",
                        f"Installed plugin planning refused: {type(exc).__name__}",
                    )
                    setattr(
                        refusal,
                        "_holdspeak_queue_advanced",
                        self.settle_bound_claim_refusal(job_id, refusal),
                    )
                    raise refusal from None
                frozen_work = _freeze_displaced_work(
                    conn,
                    meeting_id,
                    _displaced_work(row),
                    plugin_members=plugin_members,
                    plugin_route=plugin_route,
                )
                frozen_descriptor = _work_descriptor_sha256(
                    meeting_id, str(row["transcript_hash"]), frozen_work,
                )
                conn.execute(
                    """UPDATE intel_jobs SET status='superseded',
                       lifecycle_posture='superseded',updated_at=?,
                       last_error='Installed plugin membership frozen for bound claim.'
                       WHERE job_id=? AND status='queued'""",
                    (now, job_id),
                )
                planned_job_id = _job_id(
                    meeting_id, str(row["transcript_hash"]), frozen_descriptor,
                    now, job_id,
                )
                conn.execute(
                    """INSERT INTO intel_jobs (
                        job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                        transcript_hash,displaced_work,status,lifecycle_posture,
                        requested_at,updated_at,attempts,last_error
                    ) VALUES (?,?,?,?,?,?,'queued','queued',?,?,0,?)""",
                    (
                        planned_job_id, meeting_id, job_id, frozen_descriptor,
                        str(row["transcript_hash"]), frozen_work, now, now,
                        "Installed plugin membership frozen for bound claim.",
                    ),
                )
                conn.commit()
                job_id = planned_job_id
                row = conn.execute(
                    "SELECT * FROM intel_jobs WHERE job_id=?", (job_id,),
                ).fetchone()
                if row is None:
                    return None
            job = self._job_from_row(row)
            command_ids = {
                "claim_id": _claim_id(job_id),
                "parent_command_id": _bound_command_id(job_id, "parent"),
                "bundle_command_id": _bound_command_id(job_id, "bundle"),
            }
            prepare = getattr(bind, "prepare", None)
            if callable(prepare):
                # Kernel shell admission has its own journal transaction.  Release
                # this selection epoch before that admission, then reacquire the
                # exact queued row before any binding write.  A losing racer gets
                # no parent-run/bundle/member rows and cannot become an executor.
                conn.rollback()
                try:
                    prepare(job, command_ids)
                except Exception as exc:
                    setattr(exc, "_holdspeak_queue_advanced", self.settle_bound_claim_refusal(job_id, exc))
                    raise
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute(
                    """SELECT j.* FROM intel_jobs j JOIN meetings m ON m.id=j.meeting_id
                       WHERE j.job_id=? AND j.status='queued'
                         AND m.capture_status IN ('finalized','recovered')
                         AND m.route_fence_pending=0
                         AND NOT EXISTS (SELECT 1 FROM intel_jobs owner
                             WHERE owner.meeting_id=j.meeting_id
                               AND owner.work_descriptor_sha256=j.work_descriptor_sha256
                               AND owner.status IN ('claimed','running'))
                         AND NOT EXISTS (SELECT 1 FROM intel_jobs predecessor
                             LEFT JOIN kernel_receipts receipt
                               ON receipt.operation_id=predecessor.parent_operation_id
                             WHERE predecessor.job_id=j.origin_job_id
                               AND predecessor.parent_operation_id IS NOT NULL
                               AND receipt.operation_id IS NULL)""",
                    (job_id,),
                ).fetchone()
                if row is None:
                    discard = getattr(bind, "discard", None)
                    if callable(discard):
                        conn.rollback()
                        discard(job_id)
                    return None
                job = self._job_from_row(row)
                refreshed_hash = _durable_transcript_hash(conn, meeting_id)
                if refreshed_hash != str(row["transcript_hash"]):
                    work = str(row["displaced_work"])
                    descriptor = _work_descriptor_sha256(meeting_id, refreshed_hash, work)
                    conn.execute(
                        """UPDATE intel_jobs SET status='superseded',
                            lifecycle_posture='superseded',updated_at=?,
                            last_error='Transcript changed before bound claim.'
                            WHERE job_id=? AND status='queued'""",
                        (now, job_id),
                    )
                    fresh_id = _job_id(meeting_id, refreshed_hash, descriptor, now, job_id)
                    conn.execute(
                        """INSERT INTO intel_jobs (
                            job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                            transcript_hash,displaced_work,status,lifecycle_posture,
                            requested_at,updated_at,attempts,last_error
                        ) VALUES (?,?,?,?,?,?,'queued','queued',?,?,0,?)""",
                        (fresh_id, meeting_id, job_id, descriptor, refreshed_hash, work,
                         now, now, "Transcript changed; queued fresh immutable job."),
                    )
                    conn.execute(
                        """INSERT INTO intel_job_attempts (
                            meeting_id,job_id,event_kind,attempt,outcome,error,created_at
                        ) VALUES (?,?,'superseded',?,'superseded',?,?)""",
                        (meeting_id, job_id, int(row["attempts"]),
                         "Transcript changed before route binding.", now),
                    )
                    conn.commit()
                    discard = getattr(bind, "discard", None)
                    if callable(discard):
                        discard(job_id)
                    return None
            try:
                binding = dict(bind(conn, job, command_ids))
            except Exception as exc:
                # The real binder restores its pending shell before raising.  The
                # claim writer must release first so its sole discard owner can
                # terminalize that shell, then append the visible refusal truth.
                discard = getattr(bind, "discard", None)
                conn.rollback()
                if callable(discard):
                    discard(job_id)
                setattr(exc, "_holdspeak_queue_advanced", self.settle_bound_claim_refusal(job_id, exc))
                raise
            required = {"parent_operation_id", "bundle_id", "bundle_sha256"}
            if set(binding) != required or not all(str(binding[key]).strip() for key in required):
                raise ValueError("bound queue claim returned invalid parent/bundle references")
            lease_token = "intel_executor_" + uuid.uuid4().hex
            lease_expires_at = time.time() + BOUND_EXECUTOR_LEASE_SECONDS
            result = conn.execute(
                """UPDATE intel_jobs SET status='claimed',lifecycle_posture='claimed',
                    claim_id=?,parent_operation_id=?,bundle_id=?,bundle_sha256=?,
                    executor_lease_token=?,executor_lease_epoch=1,
                    executor_lease_expires_at=?,attempts=attempts+1,updated_at=?,last_error=NULL
                    WHERE job_id=? AND status='queued'""",
                (command_ids["claim_id"], str(binding["parent_operation_id"]),
                 str(binding["bundle_id"]), str(binding["bundle_sha256"]), lease_token,
                 lease_expires_at, now, job_id),
            )
            if result.rowcount != 1:
                return None
            conn.execute(
                """INSERT INTO intel_job_attempts (
                    meeting_id,job_id,claim_id,parent_operation_id,bundle_id,event_kind,
                    attempt,outcome,error,retry_at,created_at
                ) VALUES (?,?,?,?,?,'claim',?,'claimed',NULL,NULL,?)""",
                (meeting_id, job_id, command_ids["claim_id"],
                 str(binding["parent_operation_id"]), str(binding["bundle_id"]),
                 int(row["attempts"]) + 1, now),
            )
            conn.execute(
                """UPDATE meetings SET intel_status='running',
                    intel_status_detail='Claimed deferred meeting intelligence.',
                    sync_modified_at=?,updated_at=datetime('now') WHERE id=?""",
                (now, meeting_id),
            )
            bound_row = conn.execute("SELECT * FROM intel_jobs WHERE job_id=?", (job_id,)).fetchone()
            return self._job_from_row(bound_row) if bound_row is not None else None

    @staticmethod
    def _bound_executor_row_in_transaction(
        conn: Any, *, job_id: str, executor_lease_token: str, executor_lease_epoch: int
    ) -> Any | None:
        """Return the one currently authoritative C1 executor inside a writer epoch."""
        return conn.execute(
            """SELECT * FROM intel_jobs WHERE job_id=? AND executor_lease_token=?
               AND executor_lease_epoch=? AND status IN ('claimed','running')
               AND executor_lease_expires_at>?""",
            (job_id, executor_lease_token, int(executor_lease_epoch), time.time()),
        ).fetchone()

    @staticmethod
    def supersede_bound_intel_job_in_transaction(
        conn: Any,
        *,
        job_id: str,
        executor_lease_token: str,
        executor_lease_epoch: int,
        reason: str,
        event_kind: str,
    ) -> str | None:
        """Fence one currently owned bound job and queue its immutable successor."""
        old = IntelRepository._bound_executor_row_in_transaction(
            conn, job_id=job_id, executor_lease_token=executor_lease_token,
            executor_lease_epoch=executor_lease_epoch,
        )
        if old is None:
            return None
        meeting_id = str(old["meeting_id"])
        durable_hash = _durable_transcript_hash(conn, meeting_id)
        if durable_hash == str(old["transcript_hash"]):
            return None
        now = datetime.now().isoformat()
        if conn.execute(
            """UPDATE intel_jobs SET status='superseded',lifecycle_posture='superseded',
               updated_at=?,last_error=? WHERE job_id=? AND executor_lease_token=?
               AND executor_lease_epoch=? AND status IN ('claimed','running')
               AND executor_lease_expires_at>?""",
            (now, reason, job_id, executor_lease_token, int(executor_lease_epoch), time.time()),
        ).rowcount != 1:
            return None
        work = str(old["displaced_work"])
        descriptor = _work_descriptor_sha256(meeting_id, durable_hash, work)
        fresh_id = _job_id(meeting_id, durable_hash, descriptor, now, job_id)
        successor_status, successor_posture = _successor_posture(old)
        conn.execute(
            """INSERT INTO intel_jobs (
                job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                transcript_hash,displaced_work,status,lifecycle_posture,
                requested_at,updated_at,attempts,last_error
            ) VALUES (?,?,?,?,?,?,?,?,?,?,0,?)""",
            (fresh_id, meeting_id, job_id, descriptor, durable_hash, work,
             successor_status, successor_posture, now, now, reason),
        )
        conn.execute(
            """INSERT INTO intel_job_attempts (
                meeting_id,job_id,origin_job_id,claim_id,parent_operation_id,bundle_id,
                event_kind,attempt,outcome,error,retry_at,created_at
            ) VALUES (?,?,?,?,?,?,? ,?,'superseded',?,NULL,?)""",
            (
                meeting_id, job_id, str(old["origin_job_id"] or "") or None,
                str(old["claim_id"] or "") or None,
                str(old["parent_operation_id"] or "") or None,
                str(old["bundle_id"] or "") or None, event_kind,
                int(old["attempts"]), reason, now,
            ),
        )
        conn.execute(
            """INSERT INTO intel_job_attempts (
                meeting_id,job_id,origin_job_id,event_kind,attempt,outcome,error,retry_at,created_at
            ) VALUES (?,?,?,'supersession_link',0,'queued',?,NULL,?)""",
            (meeting_id, fresh_id, job_id, reason, now),
        )
        conn.execute(
            """UPDATE meetings SET intel_status='queued',intel_status_detail=?,
               intel_completed_at=NULL,sync_modified_at=?,updated_at=datetime('now') WHERE id=?""",
            (reason, now, meeting_id),
        )
        return fresh_id

    def bound_executor_held(self, job: IntelJob) -> bool:
        """Read the exact durable bearer; false is a fencing-loss signal."""
        if not job.job_id or not job.executor_lease_token or not job.executor_lease_epoch:
            return False
        with self._connection() as conn:
            return self._bound_executor_row_in_transaction(
                conn, job_id=str(job.job_id), executor_lease_token=str(job.executor_lease_token),
                executor_lease_epoch=int(job.executor_lease_epoch),
            ) is not None

    def supersede_bound_intel_job(
        self, job: IntelJob, *, reason: str, event_kind: str
    ) -> str | None:
        """Run a bearer-fenced staging transition in one writer transaction."""
        if not job.job_id or not job.executor_lease_token or not job.executor_lease_epoch:
            return None
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                fresh = self.supersede_bound_intel_job_in_transaction(
                    conn, job_id=str(job.job_id), executor_lease_token=str(job.executor_lease_token),
                    executor_lease_epoch=int(job.executor_lease_epoch), reason=reason,
                    event_kind=event_kind,
                )
                conn.commit()
                return fresh
            except Exception:
                conn.rollback()
                raise

    def complete_bound_intel_job(self, job: IntelJob) -> bool:
        """Terminalize only the exact current C1 bearer and append completion truth."""
        if not job.job_id or not job.executor_lease_token or not job.executor_lease_epoch:
            return False
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = self._bound_executor_row_in_transaction(
                conn, job_id=str(job.job_id), executor_lease_token=str(job.executor_lease_token),
                executor_lease_epoch=int(job.executor_lease_epoch),
            )
            if row is None:
                conn.rollback()
                return False
            if _durable_transcript_hash(conn, str(row["meeting_id"])) != str(row["transcript_hash"]):
                self.supersede_bound_intel_job_in_transaction(
                    conn, job_id=str(job.job_id), executor_lease_token=str(job.executor_lease_token),
                    executor_lease_epoch=int(job.executor_lease_epoch),
                    reason="Transcript changed before bound completion publication.",
                    event_kind="completion_fence_superseded",
                )
                conn.commit()
                return False
            changed = conn.execute(
                """UPDATE intel_jobs SET status='succeeded',lifecycle_posture='terminal',updated_at=?
                   WHERE job_id=? AND executor_lease_token=? AND executor_lease_epoch=?
                     AND status IN ('claimed','running') AND executor_lease_expires_at>?""",
                (now, str(job.job_id), str(job.executor_lease_token),
                 int(job.executor_lease_epoch), time.time()),
            ).rowcount
            if changed:
                conn.execute(
                    """UPDATE meetings SET intel_status='ready',intel_status_detail='Meeting intelligence ready.',
                       intel_completed_at=?,sync_modified_at=?,updated_at=datetime('now') WHERE id=?""",
                    (now, now, str(row["meeting_id"])),
                )
                conn.execute(
                    """INSERT INTO intel_job_attempts (
                        meeting_id,job_id,origin_job_id,claim_id,parent_operation_id,bundle_id,
                        event_kind,attempt,outcome,error,retry_at,created_at
                    ) VALUES (?,?,?,?,?,?, 'completion',?,'succeeded',NULL,NULL,?)""",
                    (
                        str(row["meeting_id"]), str(job.job_id),
                        str(row["origin_job_id"] or "") or None,
                        str(row["claim_id"] or "") or None,
                        str(row["parent_operation_id"] or "") or None,
                        str(row["bundle_id"] or "") or None,
                        int(row["attempts"]), now,
                    ),
                )
            conn.commit()
            return bool(changed)

    def settle_bound_execution(
        self,
        job: IntelJob,
        *,
        error: str,
        terminal_outcome: str | None = None,
        retry_at: datetime | None = None,
        max_attempts: int = 0,
    ) -> bool:
        """Settle a C1 execution failure only while its exact bearer is current.

        This owns the queue row, Meeting glass, and attempt ledger in the same
        writer transaction.  A stale worker therefore cannot mint a retry,
        terminalize the replacement owner, or leave misleading receipt history.
        """
        if not job.job_id or not job.executor_lease_token or not job.executor_lease_epoch:
            return False
        now = datetime.now()
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            old = self._bound_executor_row_in_transaction(
                conn, job_id=str(job.job_id), executor_lease_token=str(job.executor_lease_token),
                executor_lease_epoch=int(job.executor_lease_epoch),
            )
            if old is None:
                conn.rollback()
                return False
            meeting_id = str(old["meeting_id"])
            attempt = int(old["attempts"])
            terminal = terminal_outcome is not None or (max_attempts > 0 and attempt >= max_attempts)
            if terminal:
                outcome = str(terminal_outcome or "terminal_failure")
                detail = error if terminal_outcome else (
                    f"Deferred intel failed after {attempt} attempt(s): {error}"
                )
                changed = conn.execute(
                    """UPDATE intel_jobs SET status='failed',lifecycle_posture='terminal',
                       updated_at=?,last_error=? WHERE job_id=? AND executor_lease_token=?
                       AND executor_lease_epoch=? AND status IN ('claimed','running')
                       AND executor_lease_expires_at>?""",
                    (now.isoformat(), detail, str(job.job_id), str(job.executor_lease_token),
                     int(job.executor_lease_epoch), time.time()),
                ).rowcount
                if changed:
                    conn.execute(
                        """UPDATE meetings SET intel_status='error',intel_status_detail=?,
                           intel_completed_at=NULL,sync_modified_at=?,updated_at=datetime('now')
                           WHERE id=?""",
                        (detail, now.isoformat(), meeting_id),
                    )
                    conn.execute(
                        """INSERT INTO intel_job_attempts (
                            meeting_id,job_id,event_kind,attempt,outcome,error,retry_at,created_at
                        ) VALUES (?,?,'attempt',?,?,?,NULL,?)""",
                        (meeting_id, str(job.job_id), attempt, outcome, detail, now.isoformat()),
                    )
                conn.commit()
                return bool(changed)

            if retry_at is None:
                conn.rollback()
                return False
            retry_at_iso = retry_at.isoformat()
            retry_label = retry_at.replace(microsecond=0).isoformat()
            detail = (
                f"Deferred intel attempt {attempt}/{max_attempts} failed: {error} "
                f"Retrying at {retry_label}."
            )
            changed = conn.execute(
                """UPDATE intel_jobs SET status='failed',lifecycle_posture='terminal',
                    updated_at=?,last_error=? WHERE job_id=? AND executor_lease_token=?
                    AND executor_lease_epoch=? AND status IN ('claimed','running')
                    AND executor_lease_expires_at>?""",
                (now.isoformat(), error, str(job.job_id), str(job.executor_lease_token),
                 int(job.executor_lease_epoch), time.time()),
            ).rowcount
            if changed != 1:
                conn.rollback()
                return False
            successor_id = _job_id(
                meeting_id, str(old["transcript_hash"]), str(old["work_descriptor_sha256"]),
                retry_at_iso, str(job.job_id),
            )
            successor_status, successor_posture = _successor_posture(old)
            conn.execute(
                """INSERT INTO intel_jobs (
                    job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                    transcript_hash,displaced_work,status,lifecycle_posture,
                    requested_at,updated_at,attempts,last_error
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (successor_id, meeting_id, str(job.job_id), str(old["work_descriptor_sha256"]),
                 str(old["transcript_hash"]), str(old["displaced_work"]),
                 successor_status, successor_posture, retry_at_iso, now.isoformat(), attempt, error),
            )
            conn.execute(
                """INSERT INTO intel_job_attempts (
                    meeting_id,job_id,origin_job_id,claim_id,parent_operation_id,bundle_id,
                    event_kind,attempt,outcome,error,retry_at,created_at
                ) VALUES (?,?,?,?,?,?, 'attempt',?,'scheduled_retry',?,?,?)""",
                (meeting_id, str(job.job_id), str(old["origin_job_id"] or "") or None,
                 str(old["claim_id"] or "") or None, str(old["parent_operation_id"] or "") or None,
                 str(old["bundle_id"] or "") or None, attempt, error, retry_at_iso, now.isoformat()),
            )
            conn.execute(
                """INSERT INTO intel_job_attempts (
                    meeting_id,job_id,origin_job_id,claim_id,parent_operation_id,bundle_id,
                    event_kind,attempt,outcome,error,retry_at,created_at
                ) VALUES (?,?,?,?,?,?, 'retry_linkage',?,'queued',?,?,?)""",
                (meeting_id, successor_id, str(job.job_id), str(old["claim_id"] or "") or None,
                 str(old["parent_operation_id"] or "") or None, str(old["bundle_id"] or "") or None,
                 attempt, error, retry_at_iso, now.isoformat()),
            )
            conn.execute(
                """UPDATE meetings SET intel_status='queued',intel_status_detail=?,
                    intel_completed_at=NULL,sync_modified_at=?,updated_at=datetime('now') WHERE id=?""",
                (detail, now.isoformat(), meeting_id),
            )
            conn.commit()
            return True

    def settle_bound_claim_refusal(self, job_id: str, error: Exception) -> bool:
        """Make a refused pre-claim selection durably visible and non-spinning.

        Explicit assignment/policy refusals are terminal.  Unclassified
        infrastructure faults remain retryable, but move out of the immediate
        due set and exhaust a small bounded admission budget.
        """
        from datetime import timedelta
        from ..kernel.model import KernelRefused
        from ..services.errors import ServiceError

        now = datetime.now()
        detail = f"Bound route refusal: {type(error).__name__}: {error}"
        terminal = isinstance(error, (ServiceError, KernelRefused))
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM intel_jobs WHERE job_id=? AND status='queued'",
                (job_id,),
            ).fetchone()
            if row is None:
                conn.rollback()
                return False
            admission_attempt = int(row["attempts"]) + 1
            if not terminal and admission_attempt >= 3:
                terminal = True
                detail += " Admission infrastructure retry budget exhausted."
            if terminal:
                changed = conn.execute(
                    """UPDATE intel_jobs SET status='failed',lifecycle_posture='terminal',
                       attempts=?,updated_at=?,last_error=?
                       WHERE job_id=? AND status='queued'""",
                    (admission_attempt, now.isoformat(), detail, job_id),
                ).rowcount
                if changed:
                    conn.execute(
                        """UPDATE meetings SET intel_status='error',intel_status_detail=?,
                           intel_completed_at=NULL,sync_modified_at=?,updated_at=datetime('now')
                           WHERE id=?""",
                        (detail, now.isoformat(), str(row["meeting_id"])),
                    )
                    outcome, retry_at = "refused", None
                else:
                    outcome, retry_at = "refused", None
            else:
                retry_at_value = now + timedelta(seconds=min(60, 5 * (2 ** (admission_attempt - 1))))
                changed = conn.execute(
                    """UPDATE intel_jobs SET attempts=?,requested_at=?,updated_at=?,last_error=?
                       WHERE job_id=? AND status='queued'""",
                    (admission_attempt, retry_at_value.isoformat(), now.isoformat(), detail, job_id),
                ).rowcount
                if changed:
                    conn.execute(
                        """UPDATE meetings SET intel_status='queued',intel_status_detail=?,
                           sync_modified_at=?,updated_at=datetime('now') WHERE id=?""",
                        (detail, now.isoformat(), str(row["meeting_id"])),
                    )
                outcome, retry_at = "scheduled_retry", retry_at_value.isoformat()
            if changed:
                conn.execute(
                    """INSERT INTO intel_job_attempts (
                        meeting_id,job_id,event_kind,attempt,outcome,error,retry_at,created_at
                    ) VALUES (?,?, 'refusal', ?,?,?,?,?)""",
                    (str(row["meeting_id"]), job_id, admission_attempt, outcome,
                     detail, retry_at, now.isoformat()),
                )
            conn.commit()
            return bool(changed)

    def promote_successors_after_parent_terminal(
        self, parent_operation_id: str, *, executor_job: IntelJob | None = None
    ) -> int:
        """Promote reserved direct successors only after a durable parent receipt.

        The receipt check is repeated inside the queue writer transaction.  This
        makes a process loss or injected close failure leave the successor safely
        reserved rather than creating a second execution owner.
        """
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if executor_job is not None:
                if not (
                    executor_job.job_id and executor_job.executor_lease_token
                    and executor_job.executor_lease_epoch
                ):
                    conn.rollback()
                    return 0
                owner = conn.execute(
                    """SELECT 1 FROM intel_jobs WHERE job_id=? AND parent_operation_id=?
                       AND executor_lease_token=? AND executor_lease_epoch=?
                       AND status IN ('claimed','running','succeeded','superseded','failed')
                       AND executor_lease_expires_at>?""",
                    (str(executor_job.job_id), parent_operation_id,
                     str(executor_job.executor_lease_token),
                     int(executor_job.executor_lease_epoch), time.time()),
                ).fetchone()
                if owner is None:
                    conn.rollback()
                    return 0
            receipt = conn.execute(
                "SELECT 1 FROM kernel_receipts WHERE operation_id=? LIMIT 1",
                (parent_operation_id,),
            ).fetchone()
            if receipt is None:
                conn.rollback()
                return 0
            rows = conn.execute(
                """SELECT job_id,meeting_id,attempts FROM intel_jobs
                   WHERE origin_job_id=(SELECT job_id FROM intel_jobs WHERE parent_operation_id=?)
                     AND status='reserved' AND lifecycle_posture='awaiting_parent_terminal'""",
                (parent_operation_id,),
            ).fetchall()
            for row in rows:
                conn.execute(
                    """UPDATE intel_jobs SET status='queued',lifecycle_posture='queued',
                       updated_at=? WHERE job_id=? AND status='reserved'
                       AND lifecycle_posture='awaiting_parent_terminal'""",
                    (now, str(row["job_id"])),
                )
                conn.execute(
                    """INSERT INTO intel_job_attempts (
                        meeting_id,job_id,event_kind,attempt,outcome,error,retry_at,created_at
                    ) VALUES (?,?,'successor_promoted',?,'queued',NULL,NULL,?)""",
                    (str(row["meeting_id"]), str(row["job_id"]), int(row["attempts"]), now),
                )
            conn.commit()
            return len(rows)

    def promote_receipted_bound_successors(self) -> int:
        """Recover successors stranded after their old parent receipt committed.

        Parent close and queue promotion use separate durable stores.  A process
        can die in the small interval between them, so ordinary queue recovery
        scans every reserved direct successor whose predecessor has already
        earned its receipt.  The one writer transaction makes this idempotent:
        only the winning reserved→queued transition receives an event.
        """
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            rows = conn.execute(
                """SELECT successor.job_id,successor.meeting_id,successor.attempts
                   FROM intel_jobs successor
                   JOIN intel_jobs predecessor
                     ON predecessor.job_id=successor.origin_job_id
                   JOIN kernel_receipts receipt
                     ON receipt.operation_id=predecessor.parent_operation_id
                   WHERE successor.status='reserved'
                     AND successor.lifecycle_posture='awaiting_parent_terminal'
                     AND predecessor.parent_operation_id IS NOT NULL"""
            ).fetchall()
            promoted = 0
            for row in rows:
                result = conn.execute(
                    """UPDATE intel_jobs SET status='queued',lifecycle_posture='queued',
                       updated_at=? WHERE job_id=? AND status='reserved'
                       AND lifecycle_posture='awaiting_parent_terminal'""",
                    (now, str(row["job_id"])),
                )
                if result.rowcount != 1:
                    continue
                promoted += 1
                conn.execute(
                    """INSERT INTO intel_job_attempts (
                        meeting_id,job_id,event_kind,attempt,outcome,error,retry_at,created_at
                    ) VALUES (?,?,'successor_promoted',?,'queued',NULL,NULL,?)""",
                    (str(row["meeting_id"]), str(row["job_id"]), int(row["attempts"]), now),
                )
            conn.commit()
            return promoted

    def requeue_claimed_intel_job(
        self,
        meeting_id: str,
        *,
        transcript_hash: str,
        reason: str,
        displaced_work: Sequence[str],
    ) -> bool:
        """Supersede a running owner and enqueue a linked immutable refresh.

        This replaces the old owner-release mutation.  A running descriptor is
        never made queued again, so recovery cannot create a second executor.
        """
        now = datetime.now().isoformat()
        with self._connection() as conn:
            work = _freeze_displaced_work(conn, meeting_id, displaced_work)
            descriptor = _work_descriptor_sha256(meeting_id, transcript_hash, work)
            old = conn.execute(
                """SELECT * FROM intel_jobs WHERE meeting_id=?
                   AND status IN ('running','claimed')
                   ORDER BY requested_at DESC LIMIT 1""",
                (meeting_id,),
            ).fetchone()
            if old is None:
                return False
            result = conn.execute(
                """UPDATE intel_jobs SET status='superseded',
                    lifecycle_posture='superseded',updated_at=?,last_error=?
                    WHERE job_id=? AND status IN ('running','claimed')""",
                (now, reason, str(old["job_id"])),
            )
            if result.rowcount != 1:
                return False
            job_id = _job_id(
                meeting_id, transcript_hash, descriptor, now, str(old["job_id"]),
            )
            successor_status, successor_posture = _successor_posture(old)
            conn.execute(
                """INSERT INTO intel_jobs (
                    job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                    transcript_hash,displaced_work,status,lifecycle_posture,
                    requested_at,updated_at,attempts,last_error
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (job_id, meeting_id, str(old["job_id"]), descriptor,
                 transcript_hash, work, successor_status, successor_posture,
                 now, now, int(old["attempts"]), reason),
            )
            conn.execute(
                """UPDATE meetings SET intel_status='queued',intel_status_detail=?,
                    intel_completed_at=NULL,sync_modified_at=?,updated_at=datetime('now')
                   WHERE id=?""",
                (reason, now, meeting_id),
            )
        return True

    def retry_intel_job(
        self,
        meeting_id: str,
        error: str,
        *,
        retry_at: datetime,
        attempt: int,
        max_attempts: int,
    ) -> None:
        """Terminalize the owner and schedule one linked fresh queue job."""
        now = datetime.now().isoformat()
        retry_at_iso = retry_at.isoformat()
        retry_label = retry_at.replace(microsecond=0).isoformat()
        detail = (
            f"Deferred intel attempt {attempt}/{max_attempts} failed: {error} "
            f"Retrying at {retry_label}."
        )
        with self._connection() as conn:
            old = conn.execute(
                """SELECT * FROM intel_jobs WHERE meeting_id=?
                   AND status IN ('running','claimed')
                   ORDER BY requested_at DESC LIMIT 1""",
                (meeting_id,),
            ).fetchone()
            if old is None:
                return
            if conn.execute(
                """UPDATE intel_jobs SET status='failed',lifecycle_posture='terminal',
                    updated_at=?,last_error=? WHERE job_id=?
                    AND status IN ('running','claimed')""",
                (now, error, str(old["job_id"])),
            ).rowcount != 1:
                return
            job_id = _job_id(
                meeting_id, str(old["transcript_hash"]),
                str(old["work_descriptor_sha256"]), retry_at_iso, str(old["job_id"]),
            )
            successor_status, successor_posture = _successor_posture(old)
            conn.execute(
                """INSERT INTO intel_jobs (
                    job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                    transcript_hash,displaced_work,status,lifecycle_posture,
                    requested_at,updated_at,attempts,last_error
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (job_id, meeting_id, str(old["job_id"]),
                 str(old["work_descriptor_sha256"]), str(old["transcript_hash"]),
                 str(old["displaced_work"]), successor_status, successor_posture,
                 retry_at_iso, now, int(attempt), error),
            )
            conn.execute(
                """INSERT INTO intel_job_attempts (
                    meeting_id,job_id,origin_job_id,claim_id,parent_operation_id,bundle_id,
                    event_kind,attempt,outcome,error,retry_at,created_at
                ) VALUES (?,?,?,?,?,?, 'retry_linkage',?,'queued',?,?,?)""",
                (meeting_id, job_id, str(old["job_id"]),
                 str(old["claim_id"] or "") or None,
                 str(old["parent_operation_id"] or "") or None,
                 str(old["bundle_id"] or "") or None,
                 int(attempt), error, retry_at_iso, now),
            )
            conn.execute(
                """UPDATE meetings SET intel_status='queued',intel_status_detail=?,
                    intel_completed_at=NULL,sync_modified_at=?,updated_at=datetime('now')
                   WHERE id=?""",
                (detail, now, meeting_id),
            )

    def complete_intel_job(self, meeting_id: str) -> None:
        """Retain completed job history while removing it from ordinary readers."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """UPDATE intel_jobs SET status='succeeded',lifecycle_posture='terminal',
                    updated_at=? WHERE meeting_id=? AND status IN ('running','claimed')""",
                (now, meeting_id),
            )

    @staticmethod
    def _job_from_row(row: Any) -> IntelJob:
        """Convert an intel-job row, with optional Meeting context."""
        keys = set(row.keys())
        return IntelJob(
            meeting_id=row["meeting_id"],
            status=row["status"],
            transcript_hash=row["transcript_hash"],
            requested_at=datetime.fromisoformat(row["requested_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            attempts=int(row["attempts"]),
            last_error=row["last_error"],
            meeting_title=row["meeting_title"] if "meeting_title" in keys else None,
            started_at=(
                datetime.fromisoformat(row["meeting_started_at"])
                if "meeting_started_at" in keys and row["meeting_started_at"]
                else None
            ),
            intel_status_detail=(
                row["intel_status_detail"] if "intel_status_detail" in keys else None
            ),
            displaced_work=_displaced_work(row),
            frozen_bookmark_timestamps=_frozen_bookmark_timestamps(row),
            frozen_bookmark_operations=_frozen_bookmark_operations(row),
            frozen_plugin_members=_frozen_plugin_members(row),
            frozen_plugin_route=_frozen_plugin_route(row),
            job_id=(str(row["job_id"]) if "job_id" in keys else None),
            origin_job_id=(
                str(row["origin_job_id"])
                if "origin_job_id" in keys and row["origin_job_id"] else None
            ),
            work_descriptor_sha256=(
                str(row["work_descriptor_sha256"])
                if "work_descriptor_sha256" in keys else None
            ),
            claim_id=(str(row["claim_id"]) if "claim_id" in keys and row["claim_id"] else None),
            parent_operation_id=(
                str(row["parent_operation_id"])
                if "parent_operation_id" in keys and row["parent_operation_id"] else None
            ),
            bundle_id=(str(row["bundle_id"]) if "bundle_id" in keys and row["bundle_id"] else None),
            bundle_sha256=(
                str(row["bundle_sha256"])
                if "bundle_sha256" in keys and row["bundle_sha256"] else None
            ),
            executor_lease_token=(
                str(row["executor_lease_token"])
                if "executor_lease_token" in keys and row["executor_lease_token"] else None
            ),
            executor_lease_epoch=(
                int(row["executor_lease_epoch"])
                if "executor_lease_epoch" in keys and row["executor_lease_epoch"] else 0
            ),
            executor_lease_expires_at=(
                float(row["executor_lease_expires_at"])
                if "executor_lease_expires_at" in keys and row["executor_lease_expires_at"] is not None else None
            ),
            lifecycle_posture=(
                str(row["lifecycle_posture"])
                if "lifecycle_posture" in keys and row["lifecycle_posture"] else None
            ),
        )

    def get_intel_job(self, meeting_id: str) -> Optional[IntelJob]:
        """Load one deferred-intelligence job with its Meeting context."""
        with self._connection() as conn:
            row = conn.execute(
                _CURRENT_LINEAGE_CTE + """
                SELECT
                    j.*,
                    m.title AS meeting_title,
                    m.started_at AS meeting_started_at,
                    m.intel_status_detail AS intel_status_detail
                FROM current_jobs j
                JOIN meetings m ON m.id = j.meeting_id
                WHERE j.meeting_id = ? AND j.current_rank=1
                  AND j.status IN ('reserved','queued','claimed','running','failed')
                LIMIT 1
                """,
                (meeting_id,),
            ).fetchone()
        return self._job_from_row(row) if row is not None else None

    def list_intel_jobs(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> list[IntelJob]:
        """List deferred intelligence jobs with meeting context."""
        with self._connection() as conn:
            historical = bool(status and status in _TERMINAL_JOB_STATUSES)
            if historical:
                query = """
                    SELECT j.*,m.title AS meeting_title,m.started_at AS meeting_started_at,
                        m.intel_status_detail AS intel_status_detail
                    FROM intel_jobs j JOIN meetings m ON m.id=j.meeting_id
                    WHERE j.status=?
                """
                params: list[Any] = [status]
            else:
                query = _CURRENT_LINEAGE_CTE + """
                    SELECT j.*,m.title AS meeting_title,m.started_at AS meeting_started_at,
                        m.intel_status_detail AS intel_status_detail
                    FROM current_jobs j JOIN meetings m ON m.id=j.meeting_id
                    WHERE j.current_rank=1
                      AND j.status IN ('reserved','queued','claimed','running','failed')
                """
                params = []
                if status and status != "all":
                    query += " AND j.status = ?"
                    params.append(status)

            query += """
                ORDER BY CASE j.status WHEN 'running' THEN 0 WHEN 'claimed' THEN 1
                    WHEN 'queued' THEN 2 WHEN 'reserved' THEN 3 WHEN 'failed' THEN 4 ELSE 5 END,
                    j.requested_at ASC LIMIT ?
            """
            params.append(limit)

            return [self._job_from_row(row) for row in conn.execute(query, params)]

    def get_intel_queue_summary(self) -> IntelQueueSummary:
        """Return aggregate telemetry for deferred-intel queue state."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                _CURRENT_LINEAGE_CTE + """
                SELECT COUNT(*) AS total_jobs,
                    SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) AS queued_jobs,
                    SUM(CASE WHEN status IN ('claimed','running') THEN 1 ELSE 0 END) AS running_jobs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_jobs,
                    SUM(CASE WHEN status = 'queued' AND requested_at <= ? THEN 1 ELSE 0 END) AS queued_due_jobs,
                    SUM(CASE WHEN status = 'queued' AND requested_at > ? THEN 1 ELSE 0 END) AS scheduled_retry_jobs
                FROM current_jobs
                WHERE current_rank=1
                  AND status IN ('reserved','queued','claimed','running','failed')
                """,
                (now_iso, now_iso),
            ).fetchone()

            next_row = conn.execute(
                _CURRENT_LINEAGE_CTE + """
                SELECT MIN(requested_at) AS next_retry_at
                FROM current_jobs
                WHERE current_rank=1 AND status = 'queued'
                  AND requested_at > ?
                  AND last_error IS NOT NULL
                """,
                (now_iso,),
            ).fetchone()

        next_retry_at = None
        if next_row is not None and next_row["next_retry_at"]:
            next_retry_at = datetime.fromisoformat(next_row["next_retry_at"])

        return IntelQueueSummary(
            total_jobs=int(row["total_jobs"] or 0),
            queued_jobs=int(row["queued_jobs"] or 0),
            running_jobs=int(row["running_jobs"] or 0),
            failed_jobs=int(row["failed_jobs"] or 0),
            queued_due_jobs=int(row["queued_due_jobs"] or 0),
            scheduled_retry_jobs=int(row["scheduled_retry_jobs"] or 0),
            next_retry_at=next_retry_at,
        )

    def record_intel_job_attempt(
        self,
        meeting_id: str,
        *,
        attempt: int,
        outcome: str,
        error: Optional[str] = None,
        retry_at: Optional[datetime] = None,
    ) -> None:
        """Append an intel-attempt history event."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            job = conn.execute(
                _CURRENT_LINEAGE_CTE + """
                SELECT job_id FROM current_jobs
                WHERE meeting_id=? AND current_rank=1 LIMIT 1
                """,
                (meeting_id,),
            ).fetchone()
            conn.execute(
                """INSERT INTO intel_job_attempts (
                    meeting_id,job_id,event_kind,attempt,outcome,error,retry_at,created_at
                ) VALUES (?, ?, 'attempt', ?, ?, ?, ?, ?)""",
                (meeting_id, str(job["job_id"]) if job is not None else None,
                 int(attempt), str(outcome), error,
                 retry_at.isoformat() if retry_at else None, now),
            )

    def list_intel_job_attempts(self, meeting_id: str, *, limit: int = 5) -> list[IntelJobAttempt]:
        """Return most recent deferred-intel attempt events for one meeting."""
        bounded_limit = max(1, min(int(limit), 50))
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT meeting_id,job_id,event_kind,attempt,outcome,error,retry_at,created_at
                FROM intel_job_attempts
                WHERE meeting_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (meeting_id, bounded_limit),
            ).fetchall()

        return [
            IntelJobAttempt(
                meeting_id=row["meeting_id"],
                attempt=int(row["attempt"]),
                outcome=row["outcome"],
                error=row["error"],
                retry_at=(datetime.fromisoformat(row["retry_at"]) if row["retry_at"] else None),
                created_at=datetime.fromisoformat(row["created_at"]),
                job_id=(str(row["job_id"]) if row["job_id"] else None),
                event_kind=str(row["event_kind"]),
            )
            for row in rows
        ]

    def fail_intel_job(self, meeting_id: str, error: str) -> None:
        """Mark a deferred intelligence job as failed."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE intel_jobs
                SET status = 'failed', lifecycle_posture = 'terminal',
                    updated_at = ?, last_error = ?
                WHERE meeting_id = ? AND status IN ('running','claimed')
                """,
                (now, error, meeting_id),
            )
            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'error',
                    intel_status_detail = ?,
                    intel_completed_at = NULL,
                    sync_modified_at = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (error, now, meeting_id),
            )

    def mark_intel_job_partial(self, meeting_id: str, detail: str) -> None:
        """Retain completed analysis while marking routed work incomplete."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE intel_jobs
                SET status = 'failed', lifecycle_posture = 'terminal',
                    updated_at = ?, last_error = ?
                WHERE meeting_id = ? AND status IN ('running','claimed')
                """,
                (now, detail, meeting_id),
            )
            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'partial',
                    intel_status_detail = ?,
                    intel_completed_at = NULL,
                    sync_modified_at = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (detail, now, meeting_id),
            )

    def requeue_intel_job(self, meeting_id: str, *, reason: Optional[str] = None) -> bool:
        """Requeue deferred intelligence processing for a meeting."""
        return self.request_intel_retry(meeting_id, reason=reason) == "queued"

    def request_intel_retry(
        self,
        meeting_id: str,
        *,
        reason: Optional[str] = None,
    ) -> str:
        """Atomically requeue remaining Meeting intelligence.

        Returns ``queued``, ``missing``, ``empty``, ``running``, or ``ready``.
        A running job is never overwritten by a manual action, and a completed
        Meeting is not silently processed again through a route named Retry.
        """
        now = datetime.now().isoformat()
        detail = reason or MANUAL_INTEL_RETRY_REASON
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            meeting = conn.execute(
                "SELECT intel_status FROM meetings WHERE id = ?",
                (meeting_id,),
            ).fetchone()
            if meeting is None:
                return "missing"

            segment_rows = conn.execute(
                """
                SELECT text, speaker, start_time, end_time
                FROM segments
                WHERE meeting_id = ?
                ORDER BY start_time, id
                """,
                (meeting_id,),
            ).fetchall()
            if not segment_rows:
                return "empty"

            # Select the newest lineage leaf *including terminal rows*.  A retry
            # success must suppress its failed ancestor before Retry decides this
            # Meeting is unfinished.
            current_job = conn.execute(
                _CURRENT_LINEAGE_CTE + """
                SELECT * FROM current_jobs
                WHERE meeting_id=? AND current_rank=1
                LIMIT 1
                """,
                (meeting_id,),
            ).fetchone()
            if self._is_unsettled_stop_reservation_in_transaction(conn, current_job):
                return "reserved"
            if current_job is not None and current_job["status"] in {"running", "claimed"}:
                return "running"
            if current_job is None or current_job["status"] in {"succeeded", "skipped"}:
                if meeting["intel_status"] == "ready":
                    return "ready"

            transcript_payload = "\n".join(
                (
                    f"{float(row['start_time']):.3f}|{float(row['end_time']):.3f}|"
                    f"{row['speaker']}|{row['text']}"
                )
                for row in segment_rows
            )
            transcript_hash = hashlib.sha256(
                transcript_payload.encode("utf-8")
            ).hexdigest()
            has_analysis = bool(
                conn.execute(
                    "SELECT 1 FROM intel_snapshots WHERE meeting_id = ? LIMIT 1",
                    (meeting_id,),
                ).fetchone()
            )
            retry_detail = (
                ROUTED_INTEL_RETRY_REASON
                if meeting["intel_status"] == "partial"
                and has_analysis
                and current_job is not None
                and current_job["transcript_hash"] == transcript_hash
                else detail
            )
            displaced_work = (
                str(current_job["displaced_work"])
                if current_job is not None else "[]"
            )
            descriptor = _work_descriptor_sha256(
                meeting_id, transcript_hash, displaced_work,
            )
            origin_job_id = str(current_job["job_id"]) if current_job is not None else None
            if current_job is not None:
                conn.execute(
                    """UPDATE intel_jobs SET status='superseded',
                       lifecycle_posture='superseded',updated_at=? WHERE job_id=?
                       AND status NOT IN ('running','claimed')""",
                    (now, origin_job_id),
                )
            job_id = _job_id(
                meeting_id, transcript_hash, descriptor, now, origin_job_id,
            )
            successor_status, successor_posture = (
                _successor_posture(current_job) if current_job is not None else ("queued", "queued")
            )
            conn.execute(
                """INSERT INTO intel_jobs (
                    job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                    transcript_hash,displaced_work,status,lifecycle_posture,
                    requested_at,updated_at,attempts,last_error
                ) VALUES (?,?,?,?,?,?,?,?,?,?,0,?)""",
                (job_id, meeting_id, origin_job_id, descriptor, transcript_hash,
                 displaced_work, successor_status, successor_posture, now, now, retry_detail),
            )
            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'queued',
                    intel_status_detail = ?,
                    intel_requested_at = COALESCE(intel_requested_at, ?),
                    intel_completed_at = NULL,
                    sync_modified_at = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (retry_detail, now, now, meeting_id),
            )
        return "queued"

    def skip_remaining_intel(self, meeting_id: str) -> str:
        """Retain completed Meeting work and skip only non-running remainder.

        Returns ``skipped``, ``missing``, ``running``, or ``ready``. The owner
        decision is recorded in the same transaction as the queue/status change.
        ``intel_completed_at`` stays empty because Skip is not completion.
        """
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            meeting = conn.execute(
                "SELECT intel_status FROM meetings WHERE id = ?",
                (meeting_id,),
            ).fetchone()
            if meeting is None:
                return "missing"

            job = conn.execute(
                _CURRENT_LINEAGE_CTE + """
                SELECT * FROM current_jobs
                WHERE meeting_id=? AND current_rank=1 LIMIT 1
                """,
                (meeting_id,),
            ).fetchone()
            if self._is_unsettled_stop_reservation_in_transaction(conn, job):
                return "reserved"
            if job is not None and job["status"] in {"running", "claimed"}:
                return "running"
            if (job is None or job["status"] in {"succeeded", "skipped"}) and meeting["intel_status"] == "ready":
                return "ready"
            if (job is None or job["status"] == "skipped") and meeting["intel_status"] == "skipped":
                return "skipped"

            segment_count = int(
                conn.execute(
                    "SELECT COUNT(*) FROM segments WHERE meeting_id = ?",
                    (meeting_id,),
                ).fetchone()[0]
            )
            has_analysis = bool(
                conn.execute(
                    "SELECT 1 FROM intel_snapshots WHERE meeting_id = ? LIMIT 1",
                    (meeting_id,),
                ).fetchone()
            )
            artifact_count = int(
                conn.execute(
                    "SELECT COUNT(*) FROM artifacts WHERE meeting_id = ?",
                    (meeting_id,),
                ).fetchone()[0]
            )
            retained = [
                f"{segment_count} transcript "
                f"{'segment' if segment_count == 1 else 'segments'}"
            ]
            if has_analysis:
                retained.append("summary, topics, and action items")
            if artifact_count:
                retained.append(
                    f"{artifact_count} {'artifact' if artifact_count == 1 else 'artifacts'}"
                )
            detail = (
                f"Meeting saved. Retained: {', '.join(retained)}. "
                "Remaining intelligence skipped."
            )

            conn.execute(
                """UPDATE intel_jobs SET status='skipped',lifecycle_posture='terminal',
                    updated_at=? WHERE meeting_id=?
                    AND status NOT IN ('running','claimed','succeeded','superseded','skipped')""",
                (now, meeting_id),
            )
            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'skipped',
                    intel_status_detail = ?,
                    intel_completed_at = NULL,
                    sync_modified_at = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (detail, now, meeting_id),
            )
            conn.execute(
                """INSERT INTO intel_job_attempts (
                    meeting_id,job_id,event_kind,attempt,outcome,error,retry_at,created_at
                ) VALUES (?, ?, 'attempt', ?, 'skipped', NULL, NULL, ?)""",
                (meeting_id, str(job["job_id"]) if job is not None else None,
                 int(job["attempts"]) if job is not None else 0, now),
            )
        return "skipped"

    def update_meeting_intel_status(
        self,
        meeting_id: str,
        *,
        status: str,
        detail: Optional[str] = None,
        requested_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        """Update persisted intel status for a meeting."""
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE meetings
                SET intel_status = ?,
                    intel_status_detail = ?,
                    intel_requested_at = COALESCE(?, intel_requested_at),
                    intel_completed_at = ?,
                    sync_modified_at = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    status,
                    detail,
                    requested_at.isoformat() if requested_at else None,
                    completed_at.isoformat() if completed_at else None,
                    datetime.now().isoformat(),
                    meeting_id,
                ),
            )
