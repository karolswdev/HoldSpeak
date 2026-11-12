# PARKED 2026-11-12: Programs own execution and run history.
class _ParkedBody:
    def cancel_latest_run(self, principal: Principal, workbench_id: str, run_id: str = "") -> dict[str, Any]:
        """Cancel this automation's run that is still running (the newest, or
        ``run_id``). The kernel cancels only a run its caller started."""
        self._require_workbench(workbench_id)
        query = "SELECT id, parent_operation_id FROM workbench_runs WHERE workbench_id=? AND status='running'"
        params: list[Any] = [workbench_id]
        if run_id:
            query += " AND id=?"
            params.append(run_id)
        with self._db._connection() as conn:
            row = conn.execute(query + " ORDER BY started_at DESC LIMIT 1", params).fetchone()
        if row is None or not row["parent_operation_id"]:
            raise ConflictError("Nothing is running for this automation")
        disposition = self.cancel_run(principal, str(row["parent_operation_id"]))
        return {"run_id": str(row["id"]), "disposition": disposition}

    async def run(self, principal: Principal, workbench_id: str, *, memory_enabled: bool = True,
                  request_id: str | None = None,
                  source_event: dict[str, str] | None = None,
                  item_ids: list[str] | None = None) -> dict[str, Any]:
        """Run the automation now (Run now, ``workbench.run``, ``automation.run``).

        2026-11-08: an automation with an instruction runs as a Program of
        one prompt step (``automation_runs.run_as_program``); this call waits
        for its answer, which goes where ``output_target`` says. An old queue
        (an agent and no instruction of its own) is refused: it is set up as
        a program. An agent hand and a Program automation run as before
        (their ``item_ids``: a hand's Re-run)."""
        from . import automation_runs

        wb = self._require_workbench(workbench_id)
        native = str(getattr(wb, "do_kind", "run") or "run") in NATIVE_DO_KINDS
        if not native and not item_ids and not source_event:
            if automation_runs.runs_as_program(wb):
                import asyncio

                from . import engine_door
                from .program_prompt import JOB
                from holdspeak.kernel.runtime import _service

                try:  # no engine is a state he repairs: the named refusal, before any Program is made
                    engine_door.engine_for(_service(), JOB, subject=("workbench", str(wb.id)))
                except engine_door.EngineDoorError as exc:
                    raise ServiceError("no_assignment", exc.detail, context={"status": 409}) from None
                ran = await asyncio.to_thread(
                    automation_runs.run_as_program, self._db, principal, wb, wait=True,
                    key=f"request:{request_id}" if request_id else None)
                delivered = automation_runs.program_delivery(self._db, ran["program_id"])
                self._changed("workbench", str(wb.id), "update")
                return {**ran, **({"deliveries": [delivered]} if delivered else {})}
            if automation_runs.effective_instruction(self._db, wb)[1] == "agent":
                raise ServiceError(
                    "set_up_as_program", "Programs run this queue now: set it up as a program.",
                    context={"status": 409})
            return {"error": f"The automation {wb.name} has nothing to do yet: write what it should do."}
        # A hand or a Program automation (the item queue is parked: the
        # runner refuses any other run as set_up_as_program).
        from holdspeak.kernel.runtime import _service
        from holdspeak.services.workbench_runner import WorkbenchRunner

        result = await WorkbenchRunner(self._db, _service()).run(
            principal, workbench_id, memory_enabled=memory_enabled,
            request_id=request_id, source_event=source_event,
            item_ids=item_ids,
        )
        return self._deliver(principal, result)

    def _deliver(self, principal: Principal, result: Any) -> Any:
        """Send each new occurrence result to its output target (Betterment A2)."""
        if not isinstance(result, dict) or not result.get("run_id"):
            return result
        from .automation_runs import deliver_run

        deliveries = deliver_run(self._db, principal, result)
        if deliveries:
            result = {**result, "deliveries": deliveries}
            self._changed("workbench", str(self._run_workbench_id(result["run_id"]) or ""), "update")
        return result

    def _run_workbench_id(self, run_id: str) -> str | None:
        with self._db._connection() as conn:
            row = conn.execute("SELECT workbench_id FROM workbench_runs WHERE id=?", (run_id,)).fetchone()
        return str(row["workbench_id"]) if row is not None else None

    def cancel_run(self, principal: Principal, parent_operation_id: str) -> str:
        """Cancel exactly the authenticated parent, never a Workbench lookup."""
        from holdspeak.kernel.runtime import _service
        return _service().parent_run_controller.cancel_by_operation_id(principal, parent_operation_id)

    def list_runs(self, principal: Principal, workbench_id: str) -> list[dict[str, Any]]:
        from .automation_runs import program_run_rows

        # 2026-11-08: a run is a Program of one prompt step; earlier runs are workbench_runs rows.
        rows = [r.to_dict() for r in self._db.workbench_runs.list_for_workbench(workbench_id)]
        rows.extend(program_run_rows(self._db, workbench_id))
        return sorted(rows, key=lambda row: str(row.get("started_at") or ""), reverse=True)

