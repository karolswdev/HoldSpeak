"""Mesh-edge relay queue + worker liveness (HS-85-01).

The hub-local run queue behind the mesh edge: a run addressed to a node
waits here until that node's worker claims it, executes it on its own
provider, and posts the result back. Liveness is born from the worker's
polling — every claim call stamps the node's ``last_seen``; there is no
other heartbeat on the mesh.

Rows are HUB-LOCAL by design (never a synced kind): prompts move only
between the hub and the executing node, the same trust posture as the
deferred-intel rows that hold transcripts.

Deadlines are enforced lazily on read: any queued/running job past its
``deadline_at`` flips to ``failed`` with a named reason the moment anything
looks at the queue — a dead worker can strand a run for at most its
deadline, never forever.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional

from .base import BaseRepository
from .models import MeshRelayJob

DEFAULT_DEADLINE_SECONDS = 120


def _iso(dt: datetime) -> str:
    return dt.isoformat()


class MeshRelayRepository(BaseRepository):
    """CRUD + lifecycle for `mesh_relay_jobs` and `mesh_workers`."""

    # ── enqueue / read ───────────────────────────────────────────────────

    def enqueue(
        self,
        *,
        node: str,
        user_prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_hint: str = "",
        task_kind: str = "llm",
        deadline_seconds: int = DEFAULT_DEADLINE_SECONDS,
        now: Optional[datetime] = None,
    ) -> MeshRelayJob:
        now = now or datetime.now()
        job = MeshRelayJob(
            id=f"relay_{uuid.uuid4().hex[:12]}",
            node=str(node or "").strip(),
            task_kind=task_kind,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model_hint=model_hint,
            status="queued",
            deadline_at=_iso(now + timedelta(seconds=max(1, int(deadline_seconds)))),
            created_at=_iso(now),
        )
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO mesh_relay_jobs (
                    id, node, task_kind, system_prompt, user_prompt,
                    temperature, max_tokens, model_hint, status,
                    deadline_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id, job.node, job.task_kind, job.system_prompt,
                    job.user_prompt, job.temperature, job.max_tokens,
                    job.model_hint, job.status, job.deadline_at, job.created_at,
                ),
            )
        return job

    def get(self, job_id: str, *, now: Optional[datetime] = None) -> Optional[MeshRelayJob]:
        """Read a job, enforcing deadline expiry first."""
        now = now or datetime.now()
        self._expire_overdue(now)
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM mesh_relay_jobs WHERE id = ?", (job_id,)
            ).fetchone()
        return self._to_job(row) if row is not None else None

    # ── the node wire ────────────────────────────────────────────────────

    def claim_next(self, node: str, *, now: Optional[datetime] = None) -> Optional[MeshRelayJob]:
        """The worker's poll: stamp liveness, expire the overdue, claim the
        oldest queued job addressed to THIS node (or None)."""
        now = now or datetime.now()
        node = str(node or "").strip()
        if not node:
            return None
        self.touch_worker(node, now=now)
        self._expire_overdue(now)
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM mesh_relay_jobs
                WHERE node = ? AND status = 'queued'
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (node,),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE mesh_relay_jobs SET status = 'running', claimed_at = ? WHERE id = ?",
                (_iso(now), row["id"]),
            )
        return self.get(row["id"], now=now)

    def complete(self, job_id: str, *, result: str, now: Optional[datetime] = None) -> bool:
        """The worker posts the run's answer. False when the job is not in a
        completable state (already expired/failed — the answer arrived late)."""
        now = now or datetime.now()
        self._expire_overdue(now)
        with self._connection() as conn:
            cur = conn.execute(
                """
                UPDATE mesh_relay_jobs
                SET status = 'completed', result = ?, completed_at = ?
                WHERE id = ? AND status IN ('queued', 'running')
                """,
                (result, _iso(now), job_id),
            )
        return cur.rowcount > 0

    def fail(self, job_id: str, *, error: str, now: Optional[datetime] = None) -> bool:
        """The worker reports the node-side failure, verbatim."""
        now = now or datetime.now()
        with self._connection() as conn:
            cur = conn.execute(
                """
                UPDATE mesh_relay_jobs
                SET status = 'failed', error = ?, completed_at = ?
                WHERE id = ? AND status IN ('queued', 'running')
                """,
                (str(error or "node reported failure"), _iso(now), job_id),
            )
        return cur.rowcount > 0

    # ── worker liveness ──────────────────────────────────────────────────

    def touch_worker(self, node: str, *, now: Optional[datetime] = None) -> None:
        now = now or datetime.now()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO mesh_workers (node, last_seen) VALUES (?, ?)
                ON CONFLICT(node) DO UPDATE SET last_seen = excluded.last_seen
                """,
                (str(node or "").strip(), _iso(now)),
            )

    def worker_last_seen(self, node: str) -> Optional[datetime]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT last_seen FROM mesh_workers WHERE node = ?",
                (str(node or "").strip(),),
            ).fetchone()
        if row is None:
            return None
        try:
            return datetime.fromisoformat(row["last_seen"])
        except (TypeError, ValueError):
            return None

    def live_nodes(
        self, window_seconds: int = 15, *, now: Optional[datetime] = None
    ) -> dict[str, datetime]:
        """Nodes whose worker polled within the window — the ONLY liveness
        truth the mesh has."""
        now = now or datetime.now()
        floor = _iso(now - timedelta(seconds=max(1, int(window_seconds))))
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT node, last_seen FROM mesh_workers WHERE last_seen >= ?",
                (floor,),
            ).fetchall()
        out: dict[str, datetime] = {}
        for row in rows:
            try:
                out[row["node"]] = datetime.fromisoformat(row["last_seen"])
            except (TypeError, ValueError):
                continue
        return out

    # ── hygiene ──────────────────────────────────────────────────────────

    def _expire_overdue(self, now: datetime) -> None:
        """Queued and claimed-but-abandoned jobs both fail at their deadline,
        with the reason naming what happened — never a silent hang."""
        now_iso = _iso(now)
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE mesh_relay_jobs
                SET status = 'failed',
                    error = 'node ' || node || ' never claimed the run before its deadline',
                    completed_at = ?
                WHERE status = 'queued' AND deadline_at <= ?
                """,
                (now_iso, now_iso),
            )
            conn.execute(
                """
                UPDATE mesh_relay_jobs
                SET status = 'failed',
                    error = 'node ' || node || ' claimed the run but never completed it before its deadline',
                    completed_at = ?
                WHERE status = 'running' AND deadline_at <= ?
                """,
                (now_iso, now_iso),
            )

    def _to_job(self, row) -> MeshRelayJob:
        return MeshRelayJob(
            id=row["id"],
            node=row["node"],
            task_kind=row["task_kind"],
            system_prompt=row["system_prompt"],
            user_prompt=row["user_prompt"],
            temperature=row["temperature"],
            max_tokens=row["max_tokens"],
            model_hint=row["model_hint"],
            status=row["status"],
            result=row["result"],
            error=row["error"],
            deadline_at=row["deadline_at"],
            created_at=row["created_at"],
            claimed_at=row["claimed_at"],
            completed_at=row["completed_at"],
        )
