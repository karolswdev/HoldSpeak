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

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional


_ENVELOPE_TASK_PREFIX = "envelope:"

from .base import BaseRepository
from .models import MeshRelayJob

DEFAULT_DEADLINE_SECONDS = 120


def _iso(dt: datetime) -> str:
    return dt.isoformat()


class MeshRelayRepository(BaseRepository):
    """CRUD + lifecycle for `mesh_relay_jobs` and `mesh_workers`."""

    table = "mesh_relay"

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
        envelope: Optional[dict[str, Any]] = None,
        deadline_seconds: int = DEFAULT_DEADLINE_SECONDS,
        destination_node_id: str = "",
        destination_generation: int = 0,
        now: Optional[datetime] = None,
    ) -> MeshRelayJob:
        """Queue one run for ONE node.

        HS-131-16: the destination is bound by STABLE IDENTITY and by the exact
        credential generation that was live at enqueue, not by the human-readable
        name alone. A rotate, revoke, or re-pair therefore cannot let a
        replacement credential claim work addressed to its predecessor — the
        claim below matches both persisted values or finds nothing.
        """
        now = now or datetime.now()
        # v52 has no dedicated relay-envelope column. The queue is hub-local,
        # so preserve the transport-only metadata in its existing opaque task
        # field rather than changing the persisted schema contract.
        stored_task_kind = task_kind
        if envelope is not None:
            stored_task_kind = _ENVELOPE_TASK_PREFIX + json.dumps(
                envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True
            )
        job = MeshRelayJob(
            id=f"relay_{uuid.uuid4().hex[:12]}",
            node=str(node or "").strip(),
            task_kind=task_kind,
            envelope=envelope,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model_hint=model_hint,
            status="queued",
            deadline_at=_iso(now + timedelta(seconds=max(1, int(deadline_seconds)))),
            created_at=_iso(now),
            destination_node_id=str(destination_node_id or ""),
            destination_generation=int(destination_generation or 0),
        )
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO mesh_relay_jobs (
                    id, node, task_kind, system_prompt, user_prompt,
                    temperature, max_tokens, model_hint, status,
                    deadline_at, created_at,
                    destination_node_id, destination_generation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id, job.node, stored_task_kind, job.system_prompt,
                    job.user_prompt, job.temperature, job.max_tokens,
                    job.model_hint, job.status, job.deadline_at, job.created_at,
                    job.destination_node_id, job.destination_generation,
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

    def claim_signed(
        self,
        *,
        node_name: str,
        node_id: str,
        generation: int,
        claim_nonce: str,
        authorize: Any,
        now: Optional[datetime] = None,
    ) -> Optional[tuple[MeshRelayJob, dict[str, Any]]]:
        """The authenticated claim: ONE transaction, or no offer at all.

        Everything that decides whether authority exists — the still-queued row,
        its stable destination identity, its enqueue-time credential generation,
        the live hub warrant and operation, and the signature itself — happens
        inside one ``BEGIN IMMEDIATE`` critical section that ends in a guarded
        ``queued → running`` transition. Two concurrent pollers therefore produce
        at most one signed offer, and a revocation that wins the race prevents an
        offer rather than racing it.

        ``authorize`` receives the re-read job AND this transaction's own
        connection, and returns the signed offer envelope or ``None`` to refuse.
        Refusing leaves the row queued and untouched.

        Repair R2.10: the liveness stamp, the deadline sweep, the re-read row,
        and every authority read the callback performs all run on THIS
        connection. A nested repository checkout would open a second connection
        and therefore decide against a second snapshot — which is exactly the
        election this transaction exists to settle.
        """
        now = now or datetime.now()
        node_name = str(node_name or "").strip()
        if not node_name or not str(node_id or "").strip():
            return None
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            # Liveness is stamped for the EXACT authenticated identity and
            # generation: a poll under generation 1 is not evidence that
            # generation 2 is alive (repair R8).
            self._touch_worker_on(
                conn, node_name, node_id=node_id, generation=generation, now=now
            )
            # An expiry that lands first is an outcome, not a race we paper over
            # — and it lands inside the same election as the claim itself.
            self._expire_overdue_on(conn, now)
            row = conn.execute(
                """
                SELECT * FROM mesh_relay_jobs
                WHERE node = ? AND status = 'queued'
                  AND destination_node_id = ? AND destination_generation = ?
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (node_name, str(node_id), int(generation)),
            ).fetchone()
            if row is None:
                return None
            job = self._to_job(row)
            signed = authorize(job, conn)
            if not isinstance(signed, dict):
                return None
            cursor = conn.execute(
                """
                UPDATE mesh_relay_jobs
                SET status = 'running', claimed_at = ?, claimed_by_node_id = ?,
                    claimed_generation = ?, claim_nonce = ?, dispatch_offer_json = ?
                WHERE id = ? AND status = 'queued'
                """,
                (
                    _iso(now), str(node_id), int(generation), str(claim_nonce),
                    json.dumps(signed, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=True),
                    job.id,
                ),
            )
            if cursor.rowcount == 0:  # pragma: no cover - guarded by the lock
                return None
        job.status = "running"
        job.claimed_at = _iso(now)
        job.claimed_by_node_id = str(node_id)
        job.claimed_generation = int(generation)
        job.claim_nonce = str(claim_nonce)
        job.dispatch_offer = signed
        return job, signed

    def proof(self, job_id: str) -> Optional[dict[str, Any]]:
        """The relay proof row settlement revalidates against. No deadline sweep.

        Deliberately does NOT expire overdue jobs: the exact-duplicate settlement
        path is read-only and must return the original outcome even long after
        the hub operation closed.
        """
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT id, status, result, error, task_kind, claimed_by_node_id,
                       claimed_generation, claim_nonce, dispatch_offer_json,
                       worker_terminal_json, destination_node_id,
                       destination_generation
                FROM mesh_relay_jobs WHERE id = ?
                """,
                (str(job_id),),
            ).fetchone()
        return self._proof_of(row) if row is not None else None

    _PROOF_FIELDS = (
        "id", "status", "result", "error", "claimed_by_node_id",
        "claimed_generation", "claim_nonce", "dispatch_offer_json",
        "worker_terminal_json", "destination_node_id", "destination_generation",
    )

    @classmethod
    def _proof_of(cls, row: Any) -> dict[str, Any]:
        """The relay proof projection, from a row read either way.

        Carries the hub's own kernel envelope so that first settlement can check
        live authority inside its transaction (repair R6). This projection is
        hub-local: the worker's wire projection is a different, much smaller
        thing and never includes any of it.
        """
        keys = set(row.keys())
        proof: dict[str, Any] = {
            name: row[name] for name in cls._PROOF_FIELDS if name in keys
        }
        for field, raw in (
            ("dispatch_offer", proof.get("dispatch_offer_json")),
            ("worker_terminal", proof.get("worker_terminal_json")),
        ):
            try:
                proof[field] = json.loads(raw) if raw else None
            except (TypeError, ValueError):
                proof[field] = None
        proof["envelope"] = cls._envelope_of(row["task_kind"] if "task_kind" in keys else "")
        return proof

    @staticmethod
    def _envelope_of(stored_task_kind: Any) -> Optional[dict[str, Any]]:
        value = str(stored_task_kind or "")
        if not value.startswith(_ENVELOPE_TASK_PREFIX):
            return None
        try:
            envelope = json.loads(value.removeprefix(_ENVELOPE_TASK_PREFIX))
        except (TypeError, ValueError):
            return None
        return envelope if isinstance(envelope, dict) else None

    def settle_first(
        self,
        job_id: str,
        *,
        node_id: str,
        generation: int,
        decide: Any,
        now: Optional[datetime] = None,
    ) -> Any:
        """The FIRST terminal settlement: one election, one transaction.

        Everything that decides whether a worker's terminal report may be
        accepted — the stored relay proof, the exact-duplicate comparison, the
        signature and MAC and cohort checks, the hub's own still-live warrant and
        absolute deadline — happens inside ONE ``BEGIN IMMEDIATE`` critical
        section that ends in the guarded ``running → terminal`` update (repair
        R6). Anything that commits first therefore wins outright: a cancellation,
        a revocation, an expiry, or a competing report leaves this transaction
        with nothing to update, and the guarded ``WHERE`` is what says so.

        ``decide`` receives the proof row AND this transaction's own connection,
        and returns either ``None`` — the read-only duplicate path, which changes
        nothing — or the terminal fields to write. It refuses by raising; the
        transaction rolls back untouched.

        Repair R2.10: the deadline sweep, the proof load, the duplicate/conflict
        comparison, and every live-authority read the callback performs all run
        on THIS connection, so first settlement is one election against one
        snapshot rather than a decision assembled from several.
        """
        now = now or datetime.now()
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            # An expiry that lands first is an outcome, not a race we paper over.
            self._expire_overdue_on(conn, now)
            row = conn.execute(
                "SELECT * FROM mesh_relay_jobs WHERE id = ?", (str(job_id),)
            ).fetchone()
            verdict = decide(self._proof_of(row) if row is not None else None, conn)
            if verdict is None:
                return None
            status = str(verdict.get("status") or "")
            if status not in {"completed", "failed"}:  # pragma: no cover - guard
                return None
            cursor = conn.execute(
                """
                UPDATE mesh_relay_jobs
                SET status = ?, result = ?, error = ?, completed_at = ?,
                    worker_terminal_json = ?
                WHERE id = ? AND status = 'running'
                  AND claimed_by_node_id = ? AND claimed_generation = ?
                """,
                (
                    status,
                    str(verdict.get("result") or ""),
                    (str(verdict.get("error") or "") or None),
                    _iso(now),
                    json.dumps(verdict.get("worker_terminal") or {}, sort_keys=True,
                               separators=(",", ":"), ensure_ascii=True),
                    str(job_id), str(node_id), int(generation),
                ),
            )
            if cursor.rowcount == 0:
                return False
        return verdict

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

    def touch_worker(
        self,
        node: str,
        *,
        node_id: str = "",
        generation: int = 0,
        now: Optional[datetime] = None,
    ) -> None:
        """Stamp one node's poll, together with the identity that polled.

        HS-131-16 (repair R8): liveness belongs to an exact
        ``(node_id, credential_generation)``, not to a name. The row records who
        actually authenticated, so a rotate immediately makes the previous
        generation stop looking live and cannot inherit its predecessor's poll.
        """
        now = now or datetime.now()
        with self._connection() as conn:
            self._touch_worker_on(
                conn, node, node_id=node_id, generation=generation, now=now
            )

    @staticmethod
    def _touch_worker_on(
        conn: Any,
        node: str,
        *,
        node_id: str = "",
        generation: int = 0,
        now: Optional[datetime] = None,
    ) -> None:
        """:meth:`touch_worker` on a caller-supplied connection (repair R2.10)."""
        conn.execute(
            """
            INSERT INTO mesh_workers (node, last_seen, node_id, credential_generation)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(node) DO UPDATE SET
                last_seen = excluded.last_seen,
                node_id = excluded.node_id,
                credential_generation = excluded.credential_generation
            """,
            (
                str(node or "").strip(), _iso(now or datetime.now()),
                str(node_id or ""), int(generation or 0),
            ),
        )

    def node_live(
        self,
        node_id: str,
        generation: int,
        window_seconds: int = 15,
        *,
        now: Optional[datetime] = None,
    ) -> bool:
        """Is THIS credential polling right now?

        Keyed and queried by the exact ``(node_id, credential_generation)`` pair,
        and bounded on both sides: ``0 <= age <= window``. A future timestamp is
        not liveness either — a clock that ran backwards on the hub cannot make a
        silent node look alive.
        """
        node_id = str(node_id or "").strip()
        if not node_id or int(generation or 0) < 1:
            return False
        now = now or datetime.now()
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT last_seen FROM mesh_workers
                WHERE node_id = ? AND credential_generation = ?
                """,
                (node_id, int(generation)),
            ).fetchone()
        if row is None:
            return False
        try:
            last_seen = datetime.fromisoformat(row["last_seen"])
        except (TypeError, ValueError):
            return False
        age = (now - last_seen).total_seconds()
        return 0 <= age <= max(1, int(window_seconds))

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

    def list_workers(self) -> dict[str, datetime]:
        """Every node that has EVER served, with its last poll time."""
        with self._connection() as conn:
            rows = conn.execute("SELECT node, last_seen FROM mesh_workers").fetchall()
        out: dict[str, datetime] = {}
        for row in rows:
            try:
                out[row["node"]] = datetime.fromisoformat(row["last_seen"])
            except (TypeError, ValueError):
                continue
        return out

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
        with self._connection() as conn:
            self._expire_overdue_on(conn, now)

    @staticmethod
    def _expire_overdue_on(conn: Any, now: datetime) -> None:
        """:meth:`_expire_overdue` on a caller-supplied connection (repair R2.10).

        The claim and settlement elections run it INSIDE their own transaction,
        so the deadline that decides the outcome is read and applied against the
        same snapshot the guarded transition commits against.
        """
        now_iso = _iso(now)
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
        stored_task_kind = str(row["task_kind"] or "llm")
        envelope = None
        if stored_task_kind.startswith(_ENVELOPE_TASK_PREFIX):
            try:
                envelope = json.loads(stored_task_kind.removeprefix(_ENVELOPE_TASK_PREFIX))
            except (TypeError, ValueError):
                envelope = None
        keys = row.keys()
        offer = None
        if "dispatch_offer_json" in keys:
            try:
                offer = json.loads(row["dispatch_offer_json"] or "") or None
            except (TypeError, ValueError):
                offer = None
        return MeshRelayJob(
            id=row["id"],
            node=row["node"],
            task_kind="llm" if envelope is not None else stored_task_kind,
            envelope=envelope,
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
            destination_node_id=str(row["destination_node_id"] or "") if "destination_node_id" in keys else "",
            destination_generation=int(row["destination_generation"] or 0) if "destination_generation" in keys else 0,
            claimed_by_node_id=str(row["claimed_by_node_id"] or "") if "claimed_by_node_id" in keys else "",
            claimed_generation=int(row["claimed_generation"] or 0) if "claimed_generation" in keys else 0,
            claim_nonce=str(row["claim_nonce"] or "") if "claim_nonce" in keys else "",
            dispatch_offer=offer,
        )
