"""Persistence for the Project Steward ledger (HS-163-01, STW-001).

Tables: steward_policies, steward_runs, steward_steps, steward_commands.
Named-column inserts, gets, lists, and conn-accepting *_in_transaction
variants (the house pattern from HS-162-01).

Run lifecycle (STW-001): a run is durable BEFORE asynchronous work begins.
STW-002: at most one active run per project (DB-level partial unique index).
STW-005: step records carry idempotency_key + expected/observed state JSON
for reconcile-by-key before any replay.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

from .base import BaseRepository


class ActiveRunExistsError(Exception):
    """Raised when STW-002 prevents a second active run for the same project."""


# ── Policy ─────────────────────────────────────────────────────────────

class StewardPolicyRepository(BaseRepository):
    """Steward policy: per-Project effect eligibility, bounds, flags."""

    table = "steward_policies"

    # -- insert --

    def insert_policy(
        self,
        *,
        policy_id: str,
        project_id: str,
        eligible_effect_kinds_json: str = "[]",
        yolo_flags_json: str = "{}",
        max_retries: int = 3,
        max_actions_per_run: int = 10,
        cooldown_seconds: int = 0,
        bounds_json: str = "{}",
        enabled: int = 1,
        unattended_enabled: int = 0,
        nudge_template: str = "",
    ) -> None:
        with self._connection() as conn:
            self._insert_policy(
                conn,
                policy_id=policy_id,
                project_id=project_id,
                eligible_effect_kinds_json=eligible_effect_kinds_json,
                yolo_flags_json=yolo_flags_json,
                max_retries=max_retries,
                max_actions_per_run=max_actions_per_run,
                cooldown_seconds=cooldown_seconds,
                bounds_json=bounds_json,
                enabled=enabled,
                unattended_enabled=unattended_enabled,
                nudge_template=nudge_template,
            )

    def insert_policy_in_transaction(
        self,
        conn: Any,
        *,
        policy_id: str,
        project_id: str,
        eligible_effect_kinds_json: str = "[]",
        yolo_flags_json: str = "{}",
        max_retries: int = 3,
        max_actions_per_run: int = 10,
        cooldown_seconds: int = 0,
        bounds_json: str = "{}",
        enabled: int = 1,
        unattended_enabled: int = 0,
        nudge_template: str = "",
    ) -> None:
        self._insert_policy(
            conn,
            policy_id=policy_id,
            project_id=project_id,
            eligible_effect_kinds_json=eligible_effect_kinds_json,
            yolo_flags_json=yolo_flags_json,
            max_retries=max_retries,
            max_actions_per_run=max_actions_per_run,
            cooldown_seconds=cooldown_seconds,
            bounds_json=bounds_json,
            enabled=enabled,
            unattended_enabled=unattended_enabled,
            nudge_template=nudge_template,
        )

    @staticmethod
    def _insert_policy(
        conn: Any,
        *,
        policy_id: str,
        project_id: str,
        eligible_effect_kinds_json: str,
        yolo_flags_json: str,
        max_retries: int,
        max_actions_per_run: int,
        cooldown_seconds: int,
        bounds_json: str,
        enabled: int,
        unattended_enabled: int,
        nudge_template: str,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn.execute(
            """INSERT INTO steward_policies
               (id, project_id, eligible_effect_kinds_json, yolo_flags_json,
                max_retries, max_actions_per_run, cooldown_seconds,
                bounds_json, enabled, unattended_enabled, nudge_template,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(policy_id).strip(),
                str(project_id).strip(),
                eligible_effect_kinds_json,
                yolo_flags_json,
                int(max_retries),
                int(max_actions_per_run),
                int(cooldown_seconds),
                bounds_json,
                int(enabled),
                int(unattended_enabled),
                nudge_template,
                now_iso,
                now_iso,
            ),
        )

    # -- get / list --

    def get_policy(self, policy_id: str) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            return self._get_policy(conn, policy_id)

    def get_policy_in_transaction(
        self, conn: Any, policy_id: str
    ) -> Optional[dict[str, Any]]:
        return self._get_policy(conn, policy_id)

    @staticmethod
    def _get_policy(conn: Any, policy_id: str) -> Optional[dict[str, Any]]:
        row = conn.execute(
            "SELECT * FROM steward_policies WHERE id = ?",
            (str(policy_id).strip(),),
        ).fetchone()
        return dict(row) if row else None

    def get_policy_for_project(
        self, project_id: str
    ) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            return self._get_policy_for_project(conn, project_id)

    def get_policy_for_project_in_transaction(
        self, conn: Any, project_id: str
    ) -> Optional[dict[str, Any]]:
        return self._get_policy_for_project(conn, project_id)

    @staticmethod
    def _get_policy_for_project(
        conn: Any, project_id: str
    ) -> Optional[dict[str, Any]]:
        row = conn.execute(
            "SELECT * FROM steward_policies WHERE project_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (str(project_id).strip(),),
        ).fetchone()
        return dict(row) if row else None

    # -- update --

    def update_policy(
        self,
        policy_id: str,
        *,
        eligible_effect_kinds_json: Optional[str] = None,
        yolo_flags_json: Optional[str] = None,
        max_retries: Optional[int] = None,
        max_actions_per_run: Optional[int] = None,
        cooldown_seconds: Optional[int] = None,
        bounds_json: Optional[str] = None,
        enabled: Optional[int] = None,
        unattended_enabled: Optional[int] = None,
        nudge_template: Optional[str] = None,
    ) -> None:
        with self._connection() as conn:
            self._update_policy(
                conn,
                policy_id=policy_id,
                eligible_effect_kinds_json=eligible_effect_kinds_json,
                yolo_flags_json=yolo_flags_json,
                max_retries=max_retries,
                max_actions_per_run=max_actions_per_run,
                cooldown_seconds=cooldown_seconds,
                bounds_json=bounds_json,
                enabled=enabled,
                unattended_enabled=unattended_enabled,
                nudge_template=nudge_template,
            )

    def update_policy_in_transaction(
        self,
        conn: Any,
        policy_id: str,
        *,
        eligible_effect_kinds_json: Optional[str] = None,
        yolo_flags_json: Optional[str] = None,
        max_retries: Optional[int] = None,
        max_actions_per_run: Optional[int] = None,
        cooldown_seconds: Optional[int] = None,
        bounds_json: Optional[str] = None,
        enabled: Optional[int] = None,
        unattended_enabled: Optional[int] = None,
        nudge_template: Optional[str] = None,
    ) -> None:
        self._update_policy(
            conn,
            policy_id=policy_id,
            eligible_effect_kinds_json=eligible_effect_kinds_json,
            yolo_flags_json=yolo_flags_json,
            max_retries=max_retries,
            max_actions_per_run=max_actions_per_run,
            cooldown_seconds=cooldown_seconds,
            bounds_json=bounds_json,
            enabled=enabled,
            unattended_enabled=unattended_enabled,
            nudge_template=nudge_template,
        )

    @staticmethod
    def _update_policy(
        conn: Any,
        *,
        policy_id: str,
        eligible_effect_kinds_json: Optional[str],
        yolo_flags_json: Optional[str],
        max_retries: Optional[int],
        max_actions_per_run: Optional[int],
        cooldown_seconds: Optional[int],
        bounds_json: Optional[str],
        enabled: Optional[int],
        unattended_enabled: Optional[int],
        nudge_template: Optional[str],
    ) -> None:
        updates: list[str] = []
        params: list[Any] = []
        if eligible_effect_kinds_json is not None:
            updates.append("eligible_effect_kinds_json = ?")
            params.append(eligible_effect_kinds_json)
        if yolo_flags_json is not None:
            updates.append("yolo_flags_json = ?")
            params.append(yolo_flags_json)
        if max_retries is not None:
            updates.append("max_retries = ?")
            params.append(int(max_retries))
        if max_actions_per_run is not None:
            updates.append("max_actions_per_run = ?")
            params.append(int(max_actions_per_run))
        if cooldown_seconds is not None:
            updates.append("cooldown_seconds = ?")
            params.append(int(cooldown_seconds))
        if bounds_json is not None:
            updates.append("bounds_json = ?")
            params.append(bounds_json)
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(int(enabled))
        if unattended_enabled is not None:
            updates.append("unattended_enabled = ?")
            params.append(int(unattended_enabled))
        if nudge_template is not None:
            updates.append("nudge_template = ?")
            params.append(nudge_template)
        if not updates:
            return
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        updates.append("updated_at = ?")
        params.append(now_iso)
        params.append(str(policy_id).strip())
        conn.execute(
            f"UPDATE steward_policies SET {', '.join(updates)} WHERE id = ?",
            params,
        )


# ── Runs ───────────────────────────────────────────────────────────────

class StewardRunRepository(BaseRepository):
    """Steward runs: durable before async (STW-001), one active per project (STW-002)."""

    table = "steward_runs"

    # -- insert --

    def insert_run(
        self,
        *,
        run_id: str,
        project_id: str,
        policy_id: Optional[str] = None,
        state: str = "queued",
        phase: str = "observe",
        requested_by: str = "",
        watermark: str = "",
    ) -> None:
        with self._connection() as conn:
            self._insert_run(
                conn,
                run_id=run_id,
                project_id=project_id,
                policy_id=policy_id,
                state=state,
                phase=phase,
                requested_by=requested_by,
                watermark=watermark,
            )

    def insert_run_in_transaction(
        self,
        conn: Any,
        *,
        run_id: str,
        project_id: str,
        policy_id: Optional[str] = None,
        state: str = "queued",
        phase: str = "observe",
        requested_by: str = "",
        watermark: str = "",
    ) -> None:
        self._insert_run(
            conn,
            run_id=run_id,
            project_id=project_id,
            policy_id=policy_id,
            state=state,
            phase=phase,
            requested_by=requested_by,
            watermark=watermark,
        )

    @staticmethod
    def _insert_run(
        conn: Any,
        *,
        run_id: str,
        project_id: str,
        policy_id: Optional[str],
        state: str,
        phase: str,
        requested_by: str,
        watermark: str,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            conn.execute(
                """INSERT INTO steward_runs
                   (id, project_id, policy_id, state, phase,
                    requested_by, watermark, summary_json,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, '{}', ?, ?)""",
                (
                    str(run_id).strip(),
                    str(project_id).strip(),
                    policy_id,
                    state,
                    phase,
                    requested_by,
                    watermark,
                    now_iso,
                    now_iso,
                ),
            )
        except sqlite3.IntegrityError as exc:
            msg = str(exc)
            if (
                "steward_runs.project_id" in msg
                or "uq_steward_runs_one_active_per_project" in msg
            ):
                raise ActiveRunExistsError(
                    f"Project {project_id} already has an active run"
                ) from exc
            raise

    # -- get / list --

    def get_run(self, run_id: str) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            return self._get_run(conn, run_id)

    def get_run_in_transaction(
        self, conn: Any, run_id: str
    ) -> Optional[dict[str, Any]]:
        return self._get_run(conn, run_id)

    @staticmethod
    def _get_run(conn: Any, run_id: str) -> Optional[dict[str, Any]]:
        row = conn.execute(
            "SELECT * FROM steward_runs WHERE id = ?",
            (str(run_id).strip(),),
        ).fetchone()
        return dict(row) if row else None

    def get_active_run(
        self, project_id: str
    ) -> Optional[dict[str, Any]]:
        """Return the active run for a project, or None."""
        with self._connection() as conn:
            return self._get_active_run(conn, project_id)

    def get_active_run_in_transaction(
        self, conn: Any, project_id: str
    ) -> Optional[dict[str, Any]]:
        return self._get_active_run(conn, project_id)

    @staticmethod
    def _get_active_run(
        conn: Any, project_id: str
    ) -> Optional[dict[str, Any]]:
        row = conn.execute(
            "SELECT * FROM steward_runs WHERE project_id = ? "
            "AND state IN ('queued', 'running', 'stopping') "
            "ORDER BY created_at DESC LIMIT 1",
            (str(project_id).strip(),),
        ).fetchone()
        return dict(row) if row else None

    def list_all_active_runs(self) -> list[dict[str, Any]]:
        """All runs in active states across projects (STW-009 recovery)."""
        with self._connection() as conn:
            return self._list_all_active_runs(conn)

    def list_all_active_runs_in_transaction(self, conn: Any) -> list[dict[str, Any]]:
        return self._list_all_active_runs(conn)

    @staticmethod
    def _list_all_active_runs(conn: Any) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT * FROM steward_runs "
            "WHERE state IN ('queued', 'running', 'stopping') "
            "ORDER BY created_at"
        ).fetchall()
        return [dict(r) for r in rows]

    def list_runs(
        self,
        project_id: str,
        *,
        state: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with self._connection() as conn:
            return self._list_runs(conn, project_id, state=state, limit=limit)

    def list_runs_in_transaction(
        self,
        conn: Any,
        project_id: str,
        *,
        state: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return self._list_runs(conn, project_id, state=state, limit=limit)

    @staticmethod
    def _list_runs(
        conn: Any,
        project_id: str,
        *,
        state: Optional[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        clauses = ["project_id = ?"]
        params: list[Any] = [str(project_id).strip()]
        if state is not None:
            clauses.append("state = ?")
            params.append(state)
        params.append(max(1, int(limit)))
        rows = conn.execute(
            f"SELECT * FROM steward_runs "
            f"WHERE {' AND '.join(clauses)} "
            f"ORDER BY created_at DESC LIMIT ?",
            tuple(params),
        ).fetchall()
        return [dict(r) for r in rows]

    # -- update state/phase --

    def update_run_state(
        self,
        run_id: str,
        *,
        state: str,
        phase: Optional[str] = None,
        summary_json: Optional[str] = None,
    ) -> None:
        with self._connection() as conn:
            self._update_run_state(
                conn,
                run_id=run_id,
                state=state,
                phase=phase,
                summary_json=summary_json,
            )

    def update_run_state_in_transaction(
        self,
        conn: Any,
        run_id: str,
        *,
        state: str,
        phase: Optional[str] = None,
        summary_json: Optional[str] = None,
    ) -> None:
        self._update_run_state(
            conn,
            run_id=run_id,
            state=state,
            phase=phase,
            summary_json=summary_json,
        )

    @staticmethod
    def _update_run_state(
        conn: Any,
        *,
        run_id: str,
        state: str,
        phase: Optional[str],
        summary_json: Optional[str],
    ) -> None:
        updates = ["state = ?"]
        params: list[Any] = [state]
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if phase is not None:
            updates.append("phase = ?")
            params.append(phase)
        if summary_json is not None:
            updates.append("summary_json = ?")
            params.append(summary_json)
        if state == "running":
            updates.append("started_at = COALESCE(started_at, ?)")
            params.append(now_iso)
        if state in ("completed", "failed", "interrupted"):
            updates.append("completed_at = ?")
            params.append(now_iso)
        updates.append("updated_at = ?")
        params.append(now_iso)
        params.append(str(run_id).strip())
        conn.execute(
            f"UPDATE steward_runs SET {', '.join(updates)} WHERE id = ?",
            params,
        )

    # -- stop request --

    def request_stop(self, run_id: str) -> None:
        with self._connection() as conn:
            self._request_stop(conn, run_id)

    def request_stop_in_transaction(self, conn: Any, run_id: str) -> None:
        self._request_stop(conn, run_id)

    @staticmethod
    def _request_stop(conn: Any, run_id: str) -> None:
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn.execute(
            "UPDATE steward_runs "
            "SET state = 'stopping', stop_requested_at = ?, updated_at = ? "
            "WHERE id = ? AND state IN ('queued', 'running')",
            (now_iso, now_iso, str(run_id).strip()),
        )


# ── Steps ──────────────────────────────────────────────────────────────

class StewardStepRepository(BaseRepository):
    """Steward steps: the STW-005 reconciliation substrate."""

    table = "steward_steps"

    # -- insert --

    def insert_step(
        self,
        *,
        step_id: str,
        run_id: str,
        phase: str = "",
        seq: int = 0,
        state: str = "pending",
        effect_kind: str = "",
        idempotency_key: str = "",
        expected_state_json: str = "{}",
    ) -> None:
        with self._connection() as conn:
            self._insert_step(
                conn,
                step_id=step_id,
                run_id=run_id,
                phase=phase,
                seq=seq,
                state=state,
                effect_kind=effect_kind,
                idempotency_key=idempotency_key,
                expected_state_json=expected_state_json,
            )

    def insert_step_in_transaction(
        self,
        conn: Any,
        *,
        step_id: str,
        run_id: str,
        phase: str = "",
        seq: int = 0,
        state: str = "pending",
        effect_kind: str = "",
        idempotency_key: str = "",
        expected_state_json: str = "{}",
    ) -> None:
        self._insert_step(
            conn,
            step_id=step_id,
            run_id=run_id,
            phase=phase,
            seq=seq,
            state=state,
            effect_kind=effect_kind,
            idempotency_key=idempotency_key,
            expected_state_json=expected_state_json,
        )

    @staticmethod
    def _insert_step(
        conn: Any,
        *,
        step_id: str,
        run_id: str,
        phase: str,
        seq: int,
        state: str,
        effect_kind: str,
        idempotency_key: str,
        expected_state_json: str,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn.execute(
            """INSERT INTO steward_steps
               (id, run_id, phase, seq, state, effect_kind,
                idempotency_key, expected_state_json, observed_state_json,
                receipt_json, error_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}', '{}', NULL, ?, ?)""",
            (
                str(step_id).strip(),
                str(run_id).strip(),
                phase,
                int(seq),
                state,
                effect_kind,
                idempotency_key,
                expected_state_json,
                now_iso,
                now_iso,
            ),
        )

    # -- get / list --

    def get_step(self, step_id: str) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            return self._get_step(conn, step_id)

    def get_step_in_transaction(
        self, conn: Any, step_id: str
    ) -> Optional[dict[str, Any]]:
        return self._get_step(conn, step_id)

    @staticmethod
    def _get_step(conn: Any, step_id: str) -> Optional[dict[str, Any]]:
        row = conn.execute(
            "SELECT * FROM steward_steps WHERE id = ?",
            (str(step_id).strip(),),
        ).fetchone()
        return dict(row) if row else None

    def get_step_by_idempotency_key(
        self, idempotency_key: str
    ) -> Optional[dict[str, Any]]:
        """Reconcile-by-key lookup (STW-005)."""
        with self._connection() as conn:
            return self._get_step_by_idempotency_key(conn, idempotency_key)

    def get_step_by_idempotency_key_in_transaction(
        self, conn: Any, idempotency_key: str
    ) -> Optional[dict[str, Any]]:
        return self._get_step_by_idempotency_key(conn, idempotency_key)

    @staticmethod
    def _get_step_by_idempotency_key(
        conn: Any, idempotency_key: str
    ) -> Optional[dict[str, Any]]:
        row = conn.execute(
            "SELECT * FROM steward_steps WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        return dict(row) if row else None

    def list_steps(
        self,
        run_id: str,
        *,
        phase: Optional[str] = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        with self._connection() as conn:
            return self._list_steps(conn, run_id, phase=phase, limit=limit)

    def list_steps_in_transaction(
        self,
        conn: Any,
        run_id: str,
        *,
        phase: Optional[str] = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        return self._list_steps(conn, run_id, phase=phase, limit=limit)

    @staticmethod
    def _list_steps(
        conn: Any,
        run_id: str,
        *,
        phase: Optional[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        clauses = ["run_id = ?"]
        params: list[Any] = [str(run_id).strip()]
        if phase is not None:
            clauses.append("phase = ?")
            params.append(phase)
        params.append(max(1, int(limit)))
        rows = conn.execute(
            f"SELECT * FROM steward_steps "
            f"WHERE {' AND '.join(clauses)} "
            f"ORDER BY seq ASC LIMIT ?",
            tuple(params),
        ).fetchall()
        return [dict(r) for r in rows]

    # -- update (complete / record observed) --

    def interrupt_pending_steps(self, run_id: str) -> None:
        """Mark a run's pending/running steps interrupted (STW-009)."""
        with self._connection() as conn:
            self._interrupt_pending_steps(conn, run_id)

    def interrupt_pending_steps_in_transaction(self, conn: Any, run_id: str) -> None:
        self._interrupt_pending_steps(conn, run_id)

    @staticmethod
    def _interrupt_pending_steps(conn: Any, run_id: str) -> None:
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn.execute(
            "UPDATE steward_steps "
            "SET state = 'interrupted', updated_at = ?, completed_at = ? "
            "WHERE run_id = ? AND state IN ('pending', 'running')",
            (now_iso, now_iso, str(run_id).strip()),
        )

    def update_step(
        self,
        step_id: str,
        *,
        state: Optional[str] = None,
        observed_state_json: Optional[str] = None,
        receipt_json: Optional[str] = None,
        error_json: Optional[str] = None,
    ) -> None:
        with self._connection() as conn:
            self._update_step(
                conn,
                step_id=step_id,
                state=state,
                observed_state_json=observed_state_json,
                receipt_json=receipt_json,
                error_json=error_json,
            )

    def update_step_in_transaction(
        self,
        conn: Any,
        step_id: str,
        *,
        state: Optional[str] = None,
        observed_state_json: Optional[str] = None,
        receipt_json: Optional[str] = None,
        error_json: Optional[str] = None,
    ) -> None:
        self._update_step(
            conn,
            step_id=step_id,
            state=state,
            observed_state_json=observed_state_json,
            receipt_json=receipt_json,
            error_json=error_json,
        )

    @staticmethod
    def _update_step(
        conn: Any,
        *,
        step_id: str,
        state: Optional[str],
        observed_state_json: Optional[str],
        receipt_json: Optional[str],
        error_json: Optional[str],
    ) -> None:
        updates: list[str] = []
        params: list[Any] = []
        if state is not None:
            updates.append("state = ?")
            params.append(state)
        if observed_state_json is not None:
            updates.append("observed_state_json = ?")
            params.append(observed_state_json)
        if receipt_json is not None:
            updates.append("receipt_json = ?")
            params.append(receipt_json)
        if error_json is not None:
            updates.append("error_json = ?")
            params.append(error_json)
        if not updates:
            return
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if state in ("completed", "failed", "skipped"):
            updates.append("completed_at = ?")
            params.append(now_iso)
        updates.append("updated_at = ?")
        params.append(now_iso)
        params.append(str(step_id).strip())
        conn.execute(
            f"UPDATE steward_steps SET {', '.join(updates)} WHERE id = ?",
            params,
        )


# ── Commands ───────────────────────────────────────────────────────────

class StewardCommandRepository(BaseRepository):
    """Steward command records: replay substrate."""

    table = "steward_commands"

    def insert_command(
        self,
        *,
        command_id: str,
        run_id: str,
        step_id: Optional[str] = None,
        command_kind: str = "",
        payload_json: str = "{}",
        result_json: str = "{}",
    ) -> None:
        with self._connection() as conn:
            self._insert_command(
                conn,
                command_id=command_id,
                run_id=run_id,
                step_id=step_id,
                command_kind=command_kind,
                payload_json=payload_json,
                result_json=result_json,
            )

    def insert_command_in_transaction(
        self,
        conn: Any,
        *,
        command_id: str,
        run_id: str,
        step_id: Optional[str] = None,
        command_kind: str = "",
        payload_json: str = "{}",
        result_json: str = "{}",
    ) -> None:
        self._insert_command(
            conn,
            command_id=command_id,
            run_id=run_id,
            step_id=step_id,
            command_kind=command_kind,
            payload_json=payload_json,
            result_json=result_json,
        )

    @staticmethod
    def _insert_command(
        conn: Any,
        *,
        command_id: str,
        run_id: str,
        step_id: Optional[str],
        command_kind: str,
        payload_json: str,
        result_json: str,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn.execute(
            """INSERT INTO steward_commands
               (id, run_id, step_id, command_kind,
                payload_json, result_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(command_id).strip(),
                str(run_id).strip(),
                step_id,
                command_kind,
                payload_json,
                result_json,
                now_iso,
            ),
        )

    def list_commands(
        self,
        run_id: str,
        *,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        with self._connection() as conn:
            return self._list_commands(conn, run_id, limit=limit)

    def list_commands_in_transaction(
        self,
        conn: Any,
        run_id: str,
        *,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        return self._list_commands(conn, run_id, limit=limit)

    @staticmethod
    def _list_commands(
        conn: Any,
        run_id: str,
        *,
        limit: int,
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT * FROM steward_commands "
            "WHERE run_id = ? ORDER BY created_at ASC LIMIT ?",
            (str(run_id).strip(), max(1, int(limit))),
        ).fetchall()
        return [dict(r) for r in rows]
