"""PARKED 20261108 (queue view park): WorkbenchService methods only the queue view reached.

Owner ruling 2026-11-08: every automation run is a Program (#2032/#2033). The
old queue view (WorkbenchWindow) is parked, and these methods had no caller
but its routes (parked in
holdspeak/web/routes/_parked/workbench_queue_view_routes_20261108.py).
Kept here, as text, in the order they stood in WorkbenchService:

- park_items, restore_items, retry_mint, list_skills, clear_memory,
  promote_memory, and the helper _validate_item_ids (only park_items and
  restore_items used it).

resolve_voice stays in the service (its route is parked): the kernel
placement tests drive it (tests/unit/test_voice_resolve.py,
tests/unit/test_one_path_spine.py, tests/integration/
test_inference_placement_adoption.py).

Not imported. Restore with git revert of the parking commit.
"""
# ruff: noqa
# fmt: off
PARKED = True

'''
    def park_items(
        self, principal: Principal, workbench_id: str, item_ids: list[str]
    ) -> dict[str, list[str]]:
        """Park a validated set atomically, or leave every item untouched."""
        _launch_own(principal, f"workbench:{workbench_id}")
        ids = self._validate_item_ids(item_ids)
        self._require_workbench(workbench_id)
        changed, reason, bad_ids = self._db.workbench_items.park_many(workbench_id, ids)
        self._raise_transition_error(reason, bad_ids, parked=True)
        for item_id in changed:
            self._changed("workbench_item", item_id, "park")
        return {"parked": changed}

    def restore_items(
        self, principal: Principal, workbench_id: str, item_ids: list[str]
    ) -> dict[str, list[str]]:
        """Restore a validated set atomically, or leave every item untouched."""
        _launch_own(principal, f"workbench:{workbench_id}")
        ids = self._validate_item_ids(item_ids)
        self._require_workbench(workbench_id)
        changed, reason, bad_ids = self._db.workbench_items.restore_many(workbench_id, ids)
        self._raise_transition_error(reason, bad_ids, parked=False)
        for item_id in changed:
            self._changed("workbench_item", item_id, "restore")
        return {"restored": changed}

    def retry_mint(self, principal: Principal, workbench_id: str, item_id: str) -> dict[str, Any]:
        _launch_own(principal, f"workbench:{workbench_id}")
        item = self._require_item(workbench_id, item_id)
        if item.status != "done" or not item.result:
            raise ValidationError("Item is not done or has no result")
        if item.result_artifact_id:
            return {"artifact_id": item.result_artifact_id, "created": False}

        wb = self._require_workbench(workbench_id)
        recipe = self._db.recipes.get(wb.recipe_id) if wb.recipe_id else None
        if recipe is None:
            raise ValidationError("No recipe assigned")
        # Retry is historical projection work: recover the completed item's
        # frozen route evidence instead of resolving today's placement.
        from types import SimpleNamespace
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT attempt.deployment_revision_id,attempt.boundary,plan.profile_id
                   FROM inference_route_attempts attempt
                   JOIN inference_route_executions execution ON execution.id=attempt.execution_id
                   JOIN inference_operation_route_request_plans operation ON operation.id=execution.operation_plan_id
                   JOIN inference_adoption_route_evidence evidence ON evidence.evidence_ref=operation.admission_evidence_ref
                   JOIN inference_adoption_material_snapshots material ON material.planning_reference=evidence.planning_reference
                   JOIN inference_route_plan_entries plan ON plan.plan_id=operation.route_plan_id
                    AND plan.route_leg_ordinal=attempt.route_leg_ordinal
                   JOIN kernel_operations child ON child.operation_id=attempt.child_operation_id
                  WHERE child.parent_operation_id IN (
                    SELECT parent_operation_id FROM workbench_runs WHERE workbench_id=?
                  )
                    AND json_extract(material.payload_json, '$.item_id')=?
                    AND json_extract(material.payload_json, '$.source_item_operation_id') IS NULL
                  ORDER BY attempt.terminal_at DESC LIMIT 1""",
                (workbench_id, item_id),
            ).fetchone()
        if row is None:
            raise ValidationError("No frozen route evidence found for this Workbench item")
        target = SimpleNamespace(boundary=str(row["boundary"]), model=str(row["profile_id"]).removeprefix("legacy-"))

        run_id = None
        with self._db._connection() as conn:
            existing = conn.execute(
                "SELECT source_run_id FROM artifacts WHERE source_item_id = ? LIMIT 1",
                (item_id,),
            ).fetchone()
            if existing and existing["source_run_id"]:
                run_id = existing["source_run_id"]
        if not run_id:
            runs = self._db.workbench_runs.list_for_workbench(workbench_id, limit=1)
            if not runs:
                raise ValidationError("No runs found for this automation")
            run_id = runs[0].id

        from holdspeak.workbench_conductor import _auto_mint_artifact
        artifact_id = _auto_mint_artifact(
            db=self._db, item=item, recipe=recipe, workbench=wb,
            run_id=run_id, target=target, output=item.result,
        )
        if not artifact_id:
            raise ServiceError("artifact_persist_failed", "Mint failed")
        return {"artifact_id": artifact_id, "created": True}

    def list_skills(
        self, principal: Principal, recipe_id: str | None = None
    ) -> list[dict[str, Any]]:
        skills = [skill.to_dict() for skill in self._db.skills.list()]
        if recipe_id is not None:
            skills = [skill for skill in skills if recipe_id in skill.get("recipe_ids", [])]
        return skills

    def clear_memory(self, principal: Principal, workbench_id: str) -> bool:
        _launch_own(principal, f"workbench:{workbench_id}")
        from holdspeak.workbench_memory import clear_memory
        clear_memory(workbench_id)
        return True

    def promote_memory(self, principal: Principal, workbench_id: str, index: int) -> dict[str, Any]:
        _launch_own(principal, f"workbench:{workbench_id}")
        from holdspeak.workbench_memory import read_memory
        entries = read_memory(workbench_id)
        if index < 0 or index >= len(entries):
            raise ValidationError("Invalid memory index")
        wb = self._db.workbenches.get(workbench_id)
        if not wb or not wb.recipe_id:
            raise ValidationError("Automation has no agent")
        entry = entries[index]
        skill = self._db.skills.upsert(
            skill_id=_new_id("skill"), title=f"Learned: {entry.get('content', '')[:60]}",
            body=entry.get("content", ""), source="agent-proposed", status="draft",
            recipe_ids=[wb.recipe_id], created_by=f"memory:{workbench_id}",
        )
        return skill.to_dict()

    @staticmethod
    def _validate_item_ids(item_ids: Any) -> list[str]:
        if not isinstance(item_ids, list) or not item_ids:
            raise ValidationError("item_ids must be a non-empty list")
        if any(not isinstance(item_id, str) or not item_id.strip() for item_id in item_ids):
            raise ValidationError("item_ids must contain non-empty strings")
        return list(dict.fromkeys(item_id.strip() for item_id in item_ids))
'''
