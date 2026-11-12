# PARKED 2026-11-09: Programs own execution and run history.
class _ParkedBody:
    def create(
        self,
        *,
        run_id: str,
        workbench_id: str,
        started_at: Optional[str] = None,
    ) -> WorkbenchRunRecord:
        clean_id = str(run_id or "").strip()
        if not clean_id:
            raise ValueError("run id is required")
        now = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO workbench_runs (id, workbench_id, started_at)
                VALUES (?, ?, ?)
                """,
                (clean_id, str(workbench_id).strip(), started_at or now),
            )
        return self.get(clean_id)  # type: ignore[return-value]

    def complete(
        self,
        run_id: str,
        *,
        items_attempted: int = 0,
        items_completed: int = 0,
        items_failed: int = 0,
        mint_failures: int = 0,
        total_tokens: int = 0,
        egress_boundary: str = "",
        model: str = "",
        constitutional_context_revision: int = 0,
        constitutional_context_hash: str = "",
        skills_injected: Optional[list[str]] = None,
        status: str = "completed",
    ) -> Optional[WorkbenchRunRecord]:
        clean_id = str(run_id or "").strip()
        now = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE workbench_runs SET
                    completed_at = ?,
                    items_attempted = ?,
                    items_completed = ?,
                    items_failed = ?,
                    mint_failures = ?,
                    total_tokens = ?,
                    egress_boundary = ?,
                    model = ?,
                    constitutional_context_revision = ?,
                    constitutional_context_hash = ?,
                    skills_injected_json = ?,
                    status = ?
                WHERE id = ?
                """,
                (
                    now,
                    items_attempted,
                    items_completed,
                    items_failed,
                    mint_failures,
                    total_tokens,
                    egress_boundary,
                    model,
                    constitutional_context_revision,
                    constitutional_context_hash,
                    self._json_dumps(skills_injected or [], fallback="[]"),
                    status,
                    clean_id,
                ),
            )
        return self.get(clean_id)

