"""IntelRepository — the deferred-intel jobs/attempts queue.

Extracted verbatim from core.py in Phase 31 (HS-31-02). Intel *snapshots* live
with MeetingRepository (embedded in MeetingState); this repo owns the queue:
intel_jobs, intel_job_attempts, and meeting intel-status updates.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Optional, Any, Callable, Mapping, Sequence

from ..logging_config import get_logger
from .base import BaseRepository
from .models import IntelJob, IntelQueueSummary, IntelJobAttempt

log = get_logger("db.intel")

def _displaced_work(row: Any) -> tuple[str, ...]:
    """The structured displaced-work slugs on one intel_jobs row (HS-131-08)."""
    if "displaced_work" not in set(row.keys()):
        return ()
    try:
        parsed = json.loads(str(row["displaced_work"] or "[]"))
    except ValueError:
        return ()
    if not isinstance(parsed, list):
        return ()
    return tuple(str(item) for item in parsed if str(item).strip())


MANUAL_INTEL_RETRY_REASON = "Retry remaining requested."
ROUTED_INTEL_RETRY_REASON = "Retry remaining routed intelligence requested."

_ACTIVE_JOB_STATUSES = ("reserved", "queued", "claimed", "running", "failed")
_TERMINAL_JOB_STATUSES = ("succeeded", "superseded", "skipped")


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
            "displaced_work": work if isinstance(work, list) else [],
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
                )
        return self._enqueue_intel_job_in_transaction(
            conn,
            meeting_id,
            transcript_hash=transcript_hash,
            reason=reason,
            displaced_work=displaced_work,
        )

    @staticmethod
    def _enqueue_intel_job_in_transaction(
        conn: Any,
        meeting_id: str,
        *,
        transcript_hash: str,
        reason: Optional[str],
        displaced_work: Sequence[str],
    ) -> str:
        """Create or refresh one immutable descriptor without reclaiming an owner.

        A matching queued row is idempotent.  A changed descriptor terminalizes
        the old non-running row and receives a fresh linked job ID; a running
        owner is deliberately left untouched (the Phase-B race fence).
        """
        now = datetime.now().isoformat()
        work = json.dumps(
            [str(item) for item in displaced_work if str(item).strip()],
            separators=(",", ":"),
        )
        descriptor = _work_descriptor_sha256(meeting_id, transcript_hash, work)
        current = conn.execute(
            """SELECT * FROM intel_jobs WHERE meeting_id=?
               AND status IN ('reserved','queued','claimed','running','failed')
               ORDER BY CASE status WHEN 'running' THEN 0 WHEN 'claimed' THEN 1
               WHEN 'queued' THEN 2 WHEN 'reserved' THEN 3 ELSE 4 END,
               requested_at DESC LIMIT 1""",
            (meeting_id,),
        ).fetchone()
        if current is not None and str(current["status"]) in {"running", "claimed"}:
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

    def get_bound_claimed_intel_job(self) -> Optional[IntelJob]:
        """Recover one committed C1 bound owner without granting a new claim."""
        with self._connection() as conn:
            row = conn.execute(
                """SELECT * FROM intel_jobs WHERE status IN ('claimed','running')
                   AND parent_operation_id IS NOT NULL AND bundle_id IS NOT NULL
                   AND bundle_sha256 IS NOT NULL AND claim_id IS NOT NULL
                   ORDER BY requested_at ASC LIMIT 1"""
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
                    conn.execute("BEGIN IMMEDIATE")
                    conn.execute(
                        """INSERT INTO intel_job_attempts (
                            meeting_id,job_id,event_kind,attempt,outcome,error,created_at
                        ) VALUES (?,?,'refusal',?,'refused',?,?)""",
                        (meeting_id, job_id, int(row["attempts"]),
                         f"Bound route refusal: {type(exc).__name__}: {exc}", now),
                    )
                    conn.commit()
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
                               AND owner.status IN ('claimed','running'))""",
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
                if not callable(discard):
                    raise
                conn.rollback()
                discard(job_id)
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    """INSERT INTO intel_job_attempts (
                        meeting_id,job_id,event_kind,attempt,outcome,error,created_at
                    ) VALUES (?,?,'refusal',?,'refused',?,?)""",
                    (meeting_id, job_id, int(row["attempts"]),
                     f"Bound route refusal: {type(exc).__name__}: {exc}", now),
                )
                conn.commit()
                raise
            required = {"parent_operation_id", "bundle_id", "bundle_sha256"}
            if set(binding) != required or not all(str(binding[key]).strip() for key in required):
                raise ValueError("bound queue claim returned invalid parent/bundle references")
            result = conn.execute(
                """UPDATE intel_jobs SET status='claimed',lifecycle_posture='claimed',
                    claim_id=?,parent_operation_id=?,bundle_id=?,bundle_sha256=?,
                    attempts=attempts+1,updated_at=?,last_error=NULL
                    WHERE job_id=? AND status='queued'""",
                (command_ids["claim_id"], str(binding["parent_operation_id"]),
                 str(binding["bundle_id"]), str(binding["bundle_sha256"]), now, job_id),
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
    def supersede_bound_intel_job_in_transaction(
        conn: Any,
        *,
        job_id: str,
        reason: str,
        event_kind: str,
    ) -> str | None:
        """Fence one bound owner and queue a linked immutable successor.

        The caller already owns the publication/claim transaction.  A historical
        result remains durable evidence, but an old descriptor is never retargeted
        and is never made runnable again.
        """
        old = conn.execute("SELECT * FROM intel_jobs WHERE job_id=?", (job_id,)).fetchone()
        if old is None:
            return None
        status = str(old["status"])
        if status == "superseded":
            successor = conn.execute(
                "SELECT job_id FROM intel_jobs WHERE origin_job_id=? ORDER BY requested_at DESC LIMIT 1",
                (job_id,),
            ).fetchone()
            return str(successor["job_id"]) if successor is not None else None
        if status not in {"queued", "claimed", "running"}:
            return None
        meeting_id = str(old["meeting_id"])
        durable_hash = _durable_transcript_hash(conn, meeting_id)
        if durable_hash == str(old["transcript_hash"]):
            return None
        now = datetime.now().isoformat()
        if conn.execute(
            """UPDATE intel_jobs SET status='superseded',lifecycle_posture='superseded',
               updated_at=?,last_error=? WHERE job_id=? AND status IN ('queued','claimed','running')""",
            (now, reason, job_id),
        ).rowcount != 1:
            return None
        work = str(old["displaced_work"])
        descriptor = _work_descriptor_sha256(meeting_id, durable_hash, work)
        fresh_id = _job_id(meeting_id, durable_hash, descriptor, now, job_id)
        conn.execute(
            """INSERT INTO intel_jobs (
                job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                transcript_hash,displaced_work,status,lifecycle_posture,
                requested_at,updated_at,attempts,last_error
            ) VALUES (?,?,?,?,?,?,'queued','queued',?,?,0,?)""",
            (fresh_id, meeting_id, job_id, descriptor, durable_hash, work, now, now, reason),
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

    def supersede_bound_intel_job(
        self, job_id: str, *, reason: str, event_kind: str
    ) -> str | None:
        """Run a staging fence for one bound job in its own transaction."""
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                fresh = self.supersede_bound_intel_job_in_transaction(
                    conn, job_id=job_id, reason=reason, event_kind=event_kind,
                )
                conn.commit()
                return fresh
            except Exception:
                conn.rollback()
                raise

    def complete_bound_intel_job(self, job_id: str) -> bool:
        """Terminalize exactly the bound owner and append completion truth."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM intel_jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                conn.rollback()
                return False
            if _durable_transcript_hash(conn, str(row["meeting_id"])) != str(row["transcript_hash"]):
                self.supersede_bound_intel_job_in_transaction(
                    conn,
                    job_id=job_id,
                    reason="Transcript changed before bound completion publication.",
                    event_kind="completion_fence_superseded",
                )
                conn.commit()
                return False
            changed = conn.execute(
                """UPDATE intel_jobs SET status='succeeded',lifecycle_posture='terminal',updated_at=?
                   WHERE job_id=? AND status IN ('claimed','running')""",
                (now, job_id),
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
                        str(row["meeting_id"]), job_id,
                        str(row["origin_job_id"] or "") or None,
                        str(row["claim_id"] or "") or None,
                        str(row["parent_operation_id"] or "") or None,
                        str(row["bundle_id"] or "") or None,
                        int(row["attempts"]), now,
                    ),
                )
            conn.commit()
            return bool(changed)

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
        work = json.dumps(
            [str(item) for item in displaced_work if str(item).strip()],
            separators=(",", ":"),
        )
        descriptor = _work_descriptor_sha256(meeting_id, transcript_hash, work)
        with self._connection() as conn:
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
            conn.execute(
                """INSERT INTO intel_jobs (
                    job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                    transcript_hash,displaced_work,status,lifecycle_posture,
                    requested_at,updated_at,attempts,last_error
                ) VALUES (?,?,?,?,?,?,'queued','queued',?,?,?,?)""",
                (job_id, meeting_id, str(old["job_id"]), descriptor,
                 transcript_hash, work, now, now, int(old["attempts"]), reason),
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
            conn.execute(
                """INSERT INTO intel_jobs (
                    job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                    transcript_hash,displaced_work,status,lifecycle_posture,
                    requested_at,updated_at,attempts,last_error
                ) VALUES (?,?,?,?,?,?,'queued','queued',?,?,?,?)""",
                (job_id, meeting_id, str(old["job_id"]),
                 str(old["work_descriptor_sha256"]), str(old["transcript_hash"]),
                 str(old["displaced_work"]), retry_at_iso, now, int(attempt), error),
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
            lifecycle_posture=(
                str(row["lifecycle_posture"])
                if "lifecycle_posture" in keys and row["lifecycle_posture"] else None
            ),
        )

    def get_intel_job(self, meeting_id: str) -> Optional[IntelJob]:
        """Load one deferred-intelligence job with its Meeting context."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT
                    j.*,
                    m.title AS meeting_title,
                    m.started_at AS meeting_started_at,
                    m.intel_status_detail AS intel_status_detail
                FROM intel_jobs j
                JOIN meetings m ON m.id = j.meeting_id
                WHERE j.meeting_id = ?
                  AND j.status IN ('reserved','queued','claimed','running','failed')
                ORDER BY CASE j.status WHEN 'running' THEN 0 WHEN 'claimed' THEN 1
                    WHEN 'queued' THEN 2 WHEN 'reserved' THEN 3 ELSE 4 END,
                    j.requested_at DESC
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
                query = """
                    WITH current_jobs AS (
                        SELECT j.*, ROW_NUMBER() OVER (
                            PARTITION BY j.meeting_id
                            ORDER BY CASE j.status WHEN 'running' THEN 0 WHEN 'claimed' THEN 1
                                WHEN 'queued' THEN 2 WHEN 'reserved' THEN 3 ELSE 4 END,
                                j.requested_at DESC
                        ) AS current_rank
                        FROM intel_jobs j
                        WHERE j.status IN ('reserved','queued','claimed','running','failed')
                    )
                    SELECT j.*,m.title AS meeting_title,m.started_at AS meeting_started_at,
                        m.intel_status_detail AS intel_status_detail
                    FROM current_jobs j JOIN meetings m ON m.id=j.meeting_id
                    WHERE j.current_rank=1
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
                """
                WITH current_jobs AS (
                    SELECT *, ROW_NUMBER() OVER (
                        PARTITION BY meeting_id
                        ORDER BY CASE status WHEN 'running' THEN 0 WHEN 'claimed' THEN 1
                            WHEN 'queued' THEN 2 WHEN 'reserved' THEN 3 ELSE 4 END,
                            requested_at DESC
                    ) AS current_rank
                    FROM intel_jobs
                    WHERE status IN ('reserved','queued','claimed','running','failed')
                )
                SELECT COUNT(*) AS total_jobs,
                    SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) AS queued_jobs,
                    SUM(CASE WHEN status IN ('claimed','running') THEN 1 ELSE 0 END) AS running_jobs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_jobs,
                    SUM(CASE WHEN status = 'queued' AND requested_at <= ? THEN 1 ELSE 0 END) AS queued_due_jobs,
                    SUM(CASE WHEN status = 'queued' AND requested_at > ? THEN 1 ELSE 0 END) AS scheduled_retry_jobs
                FROM current_jobs WHERE current_rank=1
                """,
                (now_iso, now_iso),
            ).fetchone()

            next_row = conn.execute(
                """
                SELECT MIN(requested_at) AS next_retry_at
                FROM intel_jobs
                WHERE status = 'queued'
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
                """SELECT job_id FROM intel_jobs WHERE meeting_id=?
                   AND status IN ('reserved','queued','claimed','running','failed')
                   ORDER BY CASE status WHEN 'running' THEN 0 WHEN 'claimed' THEN 1
                       WHEN 'queued' THEN 2 WHEN 'reserved' THEN 3 ELSE 4 END,
                       requested_at DESC LIMIT 1""",
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

            current_job = conn.execute(
                """SELECT * FROM intel_jobs WHERE meeting_id=?
                   AND status IN ('reserved','queued','claimed','running','failed')
                   ORDER BY CASE status WHEN 'running' THEN 0 WHEN 'claimed' THEN 1
                       WHEN 'queued' THEN 2 WHEN 'reserved' THEN 3 ELSE 4 END,
                       requested_at DESC LIMIT 1""",
                (meeting_id,),
            ).fetchone()
            if current_job is not None and current_job["status"] in {"running", "claimed"}:
                return "running"
            if current_job is None and meeting["intel_status"] == "ready":
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
            conn.execute(
                """INSERT INTO intel_jobs (
                    job_id,meeting_id,origin_job_id,work_descriptor_sha256,
                    transcript_hash,displaced_work,status,lifecycle_posture,
                    requested_at,updated_at,attempts,last_error
                ) VALUES (?,?,?,?,?,?,'queued','queued',?,?,0,?)""",
                (job_id, meeting_id, origin_job_id, descriptor, transcript_hash,
                 displaced_work, now, now, retry_detail),
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
                """SELECT * FROM intel_jobs WHERE meeting_id=?
                   AND status IN ('reserved','queued','claimed','running','failed')
                   ORDER BY CASE status WHEN 'running' THEN 0 WHEN 'claimed' THEN 1
                       WHEN 'queued' THEN 2 WHEN 'reserved' THEN 3 ELSE 4 END,
                       requested_at DESC LIMIT 1""",
                (meeting_id,),
            ).fetchone()
            if job is not None and job["status"] in {"running", "claimed"}:
                return "running"
            if job is None and meeting["intel_status"] == "ready":
                return "ready"
            if job is None and meeting["intel_status"] == "skipped":
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
