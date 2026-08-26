"""HS-143-10 Slice 3 — schedule terms are immutable route evidence."""
from __future__ import annotations

import asyncio
from pathlib import Path

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.schedule_delegation import ScheduleDelegationService
from holdspeak.services.workbench_runner import WorkbenchRunner
from tests.unit.test_schedule_delegations import OWNER, SCHEDULER, _rig


def _frozen_plan_id(db: object, delegation_id: str) -> str:
    with db._connection() as conn:  # type: ignore[attr-defined]
        row = conn.execute(
            "SELECT plan_id FROM inference_route_plan_commands WHERE command_id=?",
            (f"schedule-delegation-route-{delegation_id}",),
        ).fetchone()
    assert row is not None
    return str(row["plan_id"])


def _route_profile(db: object, plan_id: str) -> str:
    with db._connection() as conn:  # type: ignore[attr-defined]
        row = conn.execute(
            "SELECT profile_id FROM inference_route_plan_entries WHERE plan_id=? AND route_leg_ordinal=1",
            (plan_id,),
        ).fetchone()
    assert row is not None
    return str(row["profile_id"])


def test_schedule_fire_consumes_enabled_route_and_owner_reapproval_mints_later_route(
    tmp_path: Path, monkeypatch
) -> None:
    """A current assignment edit cannot retarget a live delegation's fire."""
    db, service, workbench_id = _rig(tmp_path)
    db.workbench_items.upsert(item_id="scheduled-item", workbench_id=workbench_id, title="Scheduled")
    replacement = db.profiles.upsert(
        profile_id="replacement", name="Replacement", kind="openAICompatible",
        base_url="http://replacement", model="replacement-model",
    )
    service.update_workbench(OWNER, workbench_id, schedule_enabled=True)
    enabled = ScheduleDelegationService(db).live(workbench_id)
    assert enabled is not None
    enabled_plan_id = _frozen_plan_id(db, str(enabled["id"]))
    assert _route_profile(db, enabled_plan_id) == "legacy-p"

    # This is a real canonical edit after enablement, not a SQL mutation. The
    # live delegation remains valid, while its already-frozen source route wins.
    assignments = InferenceAssignmentService(db)
    scope = {
        "kind": "subject", "subject_kind": "workbench", "subject_id": workbench_id,
        "capability_id": "workbench.item",
    }
    current = assignments.get_assignment(OWNER, scope)
    assignments.set_assignment(OWNER, {
        "command_id": "later-workbench-assignment", "expected_revision": current["revision"],
        "scope": scope, "entries": [{"profile_id": f"legacy-{replacement.id}"}],
    })

    class Engine:
        def run_prompt(self, **_kwargs: object) -> str:
            return "scheduled frozen output"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_kwargs: Engine()
    )
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)
    fired = asyncio.run(
        WorkbenchRunner(db, broker).run_scheduled(SCHEDULER, workbench_id, due_minute=140001)
    )
    with db._connection() as conn:
        parent = conn.execute(
            "SELECT input_json FROM kernel_parent_runs WHERE operation_id=?", (fired["parent_operation_id"],)
        ).fetchone()
        child = conn.execute(
            "SELECT target_ref FROM kernel_operations WHERE parent_operation_id=? AND name='inference.invoke'",
            (fired["parent_operation_id"],),
        ).fetchone()
        frozen = conn.execute(
            "SELECT deployment_revision_id FROM inference_route_plan_entries WHERE plan_id=? AND route_leg_ordinal=1",
            (enabled_plan_id,),
        ).fetchone()
    assert parent is not None and f'"route_plan_id":"{enabled_plan_id}"' in str(parent["input_json"])
    assert child is not None and frozen is not None
    assert child["target_ref"] == f"deployment-revision:{frozen['deployment_revision_id']}"

    # An explicit owner change revokes the old authority. Re-enable is a later
    # owner decision and therefore freezes a distinct source route.
    service.update_workbench(OWNER, workbench_id, profile_id=replacement.id)
    assert ScheduleDelegationService(db).live(workbench_id) is None
    service.update_workbench(OWNER, workbench_id, schedule_enabled=False)
    service.update_workbench(OWNER, workbench_id, schedule_enabled=True)
    amended = ScheduleDelegationService(db).live(workbench_id)
    assert amended is not None and amended["id"] != enabled["id"]
    amended_plan_id = _frozen_plan_id(db, str(amended["id"]))
    assert amended_plan_id != enabled_plan_id
    assert _route_profile(db, amended_plan_id) == f"legacy-{replacement.id}"
