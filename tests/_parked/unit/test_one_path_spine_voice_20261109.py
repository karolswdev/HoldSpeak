"""PARKED 20261109 (lane door/rest-park-waist) from tests/unit/test_one_path_spine.py: WorkbenchService.resolve_voice is parked (no product caller).
Not collected (tests/_parked/conftest.py). Restore with git revert.
"""
from __future__ import annotations
import asyncio
import contextlib
from dataclasses import dataclass
from typing import Any, Callable
import pytest
from holdspeak.db import Database, reset_database
from holdspeak.inference_targets import THIS_MACHINE_ID
from holdspeak.kernel.broker import Broker
from holdspeak.kernel.executor import ExecutorPlane
from holdspeak.kernel.inference_runner import InferenceRunner
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind


def _drive_voice(tmp_path, monkeypatch) -> SurfaceRun:
    from tests.unit.test_voice_resolve import OWNER as VOICE_OWNER
    from tests.unit.test_voice_resolve import _admitted_voice_rig

    db, service, broker, workbench_id = _admitted_voice_rig(tmp_path)

    class FakeIntel:
        def run_prompt(self, **_):
            return '{"zone_ids":["zone-a"]}'

    broker.inference_runner._engine_factory = lambda _revision, **_: FakeIntel()
    service.resolve_voice(VOICE_OWNER, workbench_id, "find Alpha", "voice-spine")
    return SurfaceRun(
        db, VOICE_OWNER, _parent_run_operation_id(db, "voice_reference_resolve"),
        db.workbenches.get(workbench_id).resolver_profile_id,
        parent_kind="voice_reference_resolve",
    )




@pytest.mark.parametrize("surface", ("voice",))  # 2026-11-08: the item queue (manual Workbench) is parked
def test_adopted_workbench_family_children_link_parent_route_operation_and_receipt(
    surface: str, tmp_path, monkeypatch
) -> None:
    """The Slice-3 callers retain one frozen route through the Runner receipt."""
    run = SURFACE_DRIVERS[surface](tmp_path, monkeypatch)
    children = _invoke_children(run.db, run.parent_operation_id)
    assert children
    for child in children:
        with run.db._connection() as conn:
            row = conn.execute(
                """SELECT attempt.child_operation_id,attempt.child_receipt_sha256,
                          execution.route_plan_id execution_route_id,
                          operation.route_plan_id operation_route_id,
                          member.route_plan_id parent_route_id
                     FROM inference_route_attempts attempt
                     JOIN inference_route_executions execution ON execution.id=attempt.execution_id
                     JOIN inference_operation_route_request_plans operation ON operation.id=execution.operation_plan_id
                     JOIN inference_parent_route_bundles bundle ON bundle.parent_operation_id=?
                     JOIN inference_parent_route_bundle_members member ON member.bundle_id=bundle.id
                    WHERE attempt.child_operation_id=?""",
                (run.parent_operation_id, child["operation_id"]),
            ).fetchone()
        assert row is not None, f"{surface}: child is missing frozen route evidence"
        assert row["child_operation_id"] == child["operation_id"]
        assert row["child_receipt_sha256"]
        assert row["parent_route_id"] == row["operation_route_id"] == row["execution_route_id"]


