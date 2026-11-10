# PARKED 2026-11-09 (door/meeting-kernel): the claim no longer freezes a route
# plan with a retry policy; the engine door has no retry policy (one retry on the
# next engine of the chain, the same for every job). A changed assignment between
# prepare and claim is still refused before any model call when the run gesture
# disclosed a chain (``selection_drift``, tests/integration/test_hs201_route_execution.py).
# Moved from tests/unit/test_intel_queue.py.

import pytest

from tests.unit.test_intel_queue import *  # noqa: F401,F403
from tests.unit.test_intel_queue import _bound_claim_db  # noqa: F401


def test_real_binder_policy_flip_between_prepare_and_claim_refuses_shell(tmp_path) -> None:
    """A changed route policy cannot repurpose the pre-admitted parent budget."""
    from dataclasses import replace

    from holdspeak.inference_capabilities import (
        InferenceCapabilityRegistry,
        process_inference_capability_registry,
    )
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.errors import ConflictError
    from holdspeak.services.inference_assignment_service import (
        InferenceAssignmentService,
    )
    from holdspeak.services.inference_parent_route_bundle_service import (
        InferenceParentRouteBundleService,
    )
    from holdspeak.services.inference_route_plan_service import (
        InferenceRoutePlanService,
    )
    from holdspeak.services.meeting_deferred_queue_binding import (
        MeetingDeferredQueueBinder,
    )
    from tests.unit.test_phase143_inference_assignments import (
        OWNER,
        _profile,
        _result_claim,
    )

    db, meeting = _bound_claim_db(tmp_path, "bound-policy-race.db")
    current = process_inference_capability_registry()
    original = current.require("meeting.deferred_analysis")
    default = current.retry_policy(original.default_retry_policy_id)
    alternate = replace(
        default,
        id="retry.meeting-deferred.race",
        permitted_capability_ids=("meeting.deferred_analysis",),
        total_physical_attempts=int(default.total_physical_attempts) + 1,
        sha256="",
    )
    capability = replace(
        original,
        permitted_retry_policy_ids=(original.default_retry_policy_id, alternate.id),
        schema_sha256="",
    )
    registry = InferenceCapabilityRegistry.compose(
        capabilities=tuple(
            capability if item.id == capability.id else item
            for item in current._capabilities.values()
        ),
        retry_policies=(*current._retry_policies.values(), alternate),
    )
    capabilities = (
        "meeting.deferred_analysis",
        *(
            capability_id
            for capability_id in current.capability_ids
            if capability_id.startswith("meeting.plugin.")
        ),
    )
    _profile(
        db,
        "policy-race-model",
        claims=(
            "language",
            "structured_output",
            "meeting_plugin",
            *(_result_claim(item) for item in capabilities),
        ),
        modalities=("language", "text"),
    )
    assignments = InferenceAssignmentService(db, registry=registry)
    body = {
        "scope": {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
        "entries": [{"profile_id": "policy-race-model", "profile_revision": 1}],
    }
    assignments.set_assignment(
        OWNER,
        {"command_id": "policy-race-default", "expected_revision": 0, **body},
    )
    for ordinal, plugin_capability in enumerate(capabilities[1:], 1):
        assignments.set_assignment(
            OWNER,
            {
                "command_id": f"policy-race-plugin-{ordinal}",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": plugin_capability},
                "entries": [{"profile_id": "policy-race-model", "profile_revision": 1}],
            },
        )
    broker = _configure(db)
    bundles = InferenceParentRouteBundleService(broker, broker.inference_adoption_service)
    bundles._plans = InferenceRoutePlanService(db, registry=registry)

    class PolicyFlipBinder(MeetingDeferredQueueBinder):
        def prepare(self, job, command_ids):  # type: ignore[no-untyped-def]
            super().prepare(job, command_ids)
            assignments.set_assignment(
                OWNER,
                {
                    "command_id": "policy-race-flipped",
                    "expected_revision": 1,
                    **body,
                    "retry_policy_id": alternate.id,
                },
            )

    with pytest.raises(ConflictError) as refused:
        db.intel.claim_next_intel_job_bound(PolicyFlipBinder(broker, bundles=bundles))
    assert refused.value.code == "inference_parent_route_bundle_integrity_invalid"

    job = db.intel.get_intel_job(meeting.id)
    assert job is not None and job.status == "failed" and job.claim_id is None
    assert db.meetings.get_meeting(meeting.id).intel_status == "error"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_parent_runs").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_parent_route_bundles").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_parent_route_bundle_members").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM intel_job_attempts WHERE job_id=? AND event_kind='claim'",
            (job.job_id,),
        ).fetchone()[0] == 0
        refusal_event = conn.execute(
            "SELECT outcome FROM intel_job_attempts WHERE job_id=? AND event_kind='refusal'",
            (job.job_id,),
        ).fetchone()
        shell = conn.execute(
            """SELECT o.operation_id,o.state,r.outcome FROM kernel_operations o
               LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id
               WHERE o.principal_identity='meeting-intel-queue'
                 AND o.name='meeting.deferred-intel-job'"""
        ).fetchone()
    assert refusal_event is not None and refusal_event["outcome"] == "refused"
    assert shell is not None and shell["state"] == "refused" and shell["outcome"] == "refused"
