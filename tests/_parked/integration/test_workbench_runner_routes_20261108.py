"""HS-143-10 Slice 3 — production Workbench frozen-route adoption."""
from __future__ import annotations

import asyncio
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.workbench_runner import WorkbenchRunner
from tests.unit.test_workbench_runner_migration import _setup_runner

OWNER = Principal(PrincipalKind.OWNER, "workbench-owner")


def _route_profiles(db, parent_operation_id: str) -> list[str]:
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT DISTINCT entry.profile_id
               FROM inference_route_attempts attempt
               JOIN inference_route_executions execution ON execution.id=attempt.execution_id
               JOIN inference_operation_route_request_plans operation ON operation.id=execution.operation_plan_id
               JOIN inference_route_plan_entries entry ON entry.plan_id=operation.route_plan_id
                AND entry.route_leg_ordinal=attempt.route_leg_ordinal
               JOIN kernel_operations child ON child.operation_id=attempt.child_operation_id
              WHERE child.parent_operation_id=? ORDER BY entry.profile_id""",
            (parent_operation_id,),
        ).fetchall()
    return [str(row["profile_id"]) for row in rows]


def test_workbench_parent_freezes_legacy_primary_for_item_and_memory_then_later_run_sees_edit(tmp_path: Path, monkeypatch) -> None:
    db, broker, workbench, items, state = _setup_runner(tmp_path, monkeypatch)
    state["block_call"] = 1
    replacement = db.profiles.upsert(
        profile_id="replacement-profile", name="Replacement", kind="openAICompatible",
        base_url="http://replacement", model="replacement-model",
    )
    runner = WorkbenchRunner(db, broker)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: asyncio.run(runner.run(OWNER, workbench.id)))
        assert state["entered"].wait(5)
        assignments = InferenceAssignmentService(db)
        scope = {"kind": "subject", "subject_kind": "workbench", "subject_id": workbench.id, "capability_id": "workbench.item"}
        current = assignments.get_assignment(OWNER, scope)
        assignments.set_assignment(OWNER, {
            "command_id": "workbench-next-run-edit", "expected_revision": current["revision"], "scope": scope,
            "entries": [{"profile_id": f"legacy-{replacement.id}"}],
        })
        state["release"].set()
        first = future.result(timeout=10)

    assert _route_profiles(db, first["parent_operation_id"]) == [f"legacy-{workbench.profile_id}"]
    with db._connection() as conn:
        bundle = conn.execute("SELECT 1 FROM inference_parent_route_bundles WHERE parent_operation_id=?", (first["parent_operation_id"],)).fetchone()
    assert bundle is not None

    db.workbench_items.upsert(item_id="later-item", workbench_id=workbench.id, title="Later", body="later input")
    second = asyncio.run(runner.run(OWNER, workbench.id, memory_enabled=False))
    assert _route_profiles(db, second["parent_operation_id"]) == [f"legacy-{replacement.id}"]
