"""PHILO-3-02 summary detail projections from the real queue producer.

The queue, admission and provider boundary stay real in these fences.  Only
the provider engine is substituted through the existing queue rig.  The tests
exercise the same MeetingService and MeetingIntelService reads used by the
Arrival, including the current lineage leaf after a scheduled retry.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
import shutil
from types import SimpleNamespace
from typing import Any

from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.meeting_import import import_meeting
from holdspeak.deployment_revisions import DeploymentRevision
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.services.meeting_route_projection import project_route
from holdspeak.services.meeting_service import MeetingService
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.model_profile_service import ModelProfileService
from tests.unit.test_meeting_deferred_admission import _queue_rig
from tests.unit.test_phase143_inference_assignments import _manifest, _result_claim


OWNER = Principal(PrincipalKind.OWNER, "summary-detail-owner")
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "philo3_summary_wire.json"


def _meeting(db: Any, meeting_id: str) -> MeetingState:
    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 10, 9, 0, 0),
        ended_at=datetime(2026, 8, 10, 9, 30, 0),
        title="Architecture boundary review",
        tags=["architecture"],
        segments=[
            TranscriptSegment(
                text="We will ship the boundary change on Tuesday.",
                speaker="Me",
                start_time=0.0,
                end_time=5.0,
            )
        ],
    )
    db.meetings.save_meeting(state)
    return state


def _admit(db: Any, meeting_id: str) -> dict[str, Any]:
    route = project_route(db, invocation_id=f"meeting:{meeting_id}")
    return MeetingIntelService(db).run_intelligence(
        OWNER, meeting_id, expected_selection_hash=route["selection_hash"]
    )


def _reads(db: Any, meeting_id: str) -> dict[str, Any]:
    meeting = MeetingService(db)
    recovery = MeetingIntelService(db)
    return {
        "list": meeting.list_meetings(OWNER)["meetings"][0],
        "detail": meeting.get_meeting(OWNER, meeting_id),
        "recovery": recovery.get_recovery(OWNER, meeting_id),
    }


def _imported_meeting(
    db: Any, source: Path, *, meeting_id: str
) -> MeetingState:
    """Persist the same real WAV/import producer used by every fixture state."""

    class _ImportTranscriber:
        def transcribe(self, _audio: Any, **_kwargs: Any) -> str:
            return "We will ship the boundary change on Tuesday."

    imported = import_meeting(
        source,
        db=db,
        transcriber=_ImportTranscriber(),
        config=SimpleNamespace(
            meeting=SimpleNamespace(intel_enabled=True, intel_deferred_enabled=True)
        ),
        title="Architecture boundary review",
        tags=["architecture"],
        started_at=datetime(2026, 8, 10, 9, 0, 0),
        meeting_id=meeting_id,
    )
    return imported.state


def _change_summary_assignment_to_endpoint(db: Any, monkeypatch: Any) -> None:
    """Use the real profile/assignment producer to change the current host.

    The queue job already froze and executed the local route.  This creates a
    compatible endpoint profile, probes it through the profile service seam,
    binds it, and changes only the durable capability assignment afterward.
    The next planned route therefore comes from persisted assignment state and
    can be compared with the old receipt.
    """
    profile_id = "summary-cloud-after-run"
    artifact_id = f"artifact-{profile_id}"
    deployment_id = f"head-{profile_id}"
    destination_id = "summary-cloud"
    capability = "meeting.deferred_analysis"
    claims = (
        "language",
        "structured_output",
        "meeting_plugin",
        _result_claim(capability),
    )
    manifest = _manifest(*claims)
    profiles = ModelProfileService(db)
    profiles.create_profile(
        OWNER,
        {
            "profile_id": profile_id,
            "expected_revision": 0,
            "label": "Summary cloud after run",
            "provider_family": "endpoint",
            "runtime_family": "openai_compatible_v1",
            "model_or_artifact_identity": artifact_id,
            "supported_modalities": ["language", "text"],
            "context_support": "bounded",
            "tokenizer_template_requirements": {},
            "capability_manifest": manifest,
            "safe_presentation": {"summary": "Fixture endpoint"},
        },
    )
    db.profiles.upsert(
        profile_id=destination_id,
        name="Summary cloud endpoint",
        kind="openAICompatible",
        base_url="https://cloud.example/v1",
        model="summary-cloud-model",
        requires_key=False,
    )
    deployment = DeploymentRevision.from_artifact(
        destination_id=destination_id,
        engine="openai_compatible",
        model="summary-cloud-model",
        runtime_id="openai_compatible_v1",
        runtime_revision="1",
        artifact_id=artifact_id,
        manifest_sha256="sha256:" + "1" * 64,
        format="gguf",
        architecture="openai-compatible",
        context_ceiling=32768,
        capability_sha256=str(manifest["sha256"]),
        kind="external_service",
        boundary="external_service",
        endpoint="https://cloud.example/v1",
    )
    db.deployment_revisions.upsert(deployment)
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO inference_model_artifacts
               (artifact_id,format,source_kind,source_repository,source_revision,
                manifest_json,manifest_sha256,installed_bytes,state,local_locator,
                created_at,verified_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                artifact_id,
                "gguf",
                "fixture",
                "fixture",
                "r1",
                json.dumps(manifest, sort_keys=True),
                deployment.manifest_sha256,
                1,
                "verified",
                "cloud.example/v1",
                "2026-08-21T00:00:00Z",
                "2026-08-21T00:00:00Z",
            ),
        )
        conn.execute(
            """INSERT INTO inference_deployments
               (deployment_id,destination_id,runtime_id,runtime_revision,artifact_id,
                model_identity,context_ceiling,recommended_context,capability_json,
                capability_sha256,execution_revision_id,configuration_revision,active,
                created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                deployment_id,
                destination_id,
                deployment.runtime_id,
                deployment.runtime_revision,
                artifact_id,
                deployment.model,
                deployment.context_ceiling,
                deployment.context_ceiling,
                json.dumps(manifest, sort_keys=True),
                manifest["sha256"],
                deployment.id,
                1,
                1,
                "2026-08-21T00:00:00Z",
                "2026-08-21T00:00:00Z",
            ),
        )
    monkeypatch.setattr(
        "holdspeak.services.profile_service.ProfileService.probe_inference_target",
        lambda *_args, **_kwargs: {"reachable": True, "latency_ms": 1, "models": []},
    )
    observation = profiles.probe_profile(
        OWNER,
        {
            "profile_id": profile_id,
            "profile_revision": 1,
            "deployment_head_id": deployment_id,
            "expected_deployment_configuration_revision": 1,
            "expected_deployment_revision_id": deployment.id,
        },
    )
    profiles.bind_profile(
        OWNER,
        {
            "binding_id": f"binding-{profile_id}",
            "profile_id": profile_id,
            "profile_revision": 1,
            "deployment_head_id": deployment_id,
            "expected_binding_revision": 0,
            "expected_deployment_configuration_revision": 1,
            "expected_deployment_revision_id": deployment.id,
            "enabled": True,
            "readiness_observation_id": observation["observation_id"],
        },
    )
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "summary-route-change-after-run",
            "expected_revision": 1,
            "scope": {"kind": "capability", "capability_id": capability},
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        },
    )


def _produce_summary_wire_cases(tmp_path: Path, monkeypatch: Any) -> dict[str, Any]:
    """Mint every fixture case through the real import/service/queue producers."""
    cases: dict[str, Any] = {}

    imported_dir = tmp_path / "imported_off"
    imported_dir.mkdir(parents=True, exist_ok=True)
    imported_db, _broker, _engine, _host, _requests = _queue_rig(
        imported_dir, monkeypatch
    )
    source = imported_dir / "philo3_architect_meeting.wav"
    shutil.copyfile(
        Path(__file__).resolve().parents[1] / "fixtures" / "philo3_architect_meeting.wav",
        source,
    )

    imported = _imported_meeting(
        imported_db, source, meeting_id="m-philo3-summary"
    )
    cases["imported_off"] = _reads(imported_db, imported.id)

    def _queue_case(name: str, action: Any) -> None:
        case_dir = tmp_path / name
        case_dir.mkdir(parents=True, exist_ok=True)
        db, broker, engine, _host, _requests = _queue_rig(case_dir, monkeypatch)
        imported_source = case_dir / "philo3_architect_meeting.wav"
        shutil.copyfile(source, imported_source)
        state = _imported_meeting(
            db, imported_source, meeting_id="m-philo3-summary"
        )
        action(db, broker, engine, state)
        cases[name] = _reads(db, state.id)

    def _running(db: Any, broker: Any, _engine: Any, state: MeetingState) -> None:
        _admit(db, state.id)
        from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

        assert db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))

    def _success(db: Any, _broker: Any, _engine: Any, state: MeetingState) -> None:
        _admit(db, state.id)
        from holdspeak.intel_queue import process_next_intel_job

        assert process_next_intel_job()
        _change_summary_assignment_to_endpoint(db, monkeypatch)

    def _retry(db: Any, _broker: Any, engine: Any, state: MeetingState) -> None:
        _admit(db, state.id)
        engine.error = "provider unavailable"
        from holdspeak.intel_queue import process_next_intel_job

        assert process_next_intel_job(retry_base_seconds=60)
        with db._connection() as conn:
            conn.execute(
                "UPDATE intel_jobs SET requested_at=? WHERE meeting_id=? AND status='queued'",
                ("2020-01-01T00:00:00", state.id),
            )

    def _terminal_failure(
        db: Any, _broker: Any, engine: Any, state: MeetingState
    ) -> None:
        _admit(db, state.id)
        engine.error = "recorded provider failure at the endpoint boundary"
        from holdspeak.intel_queue import process_next_intel_job

        assert process_next_intel_job(retry_max_attempts=1)

    _queue_case("running", _running)
    _queue_case("success", _success)
    _queue_case("retry", _retry)
    _queue_case("terminal_failure", _terminal_failure)
    return cases


_VOLATILE_ID_KEYS = {
    "id",
    "meeting_id",
    "job_id",
    "receipt_id",
    "operation_id",
    "selection_hash",
    "deployment_revision_id",
}


def _normalise_wire(value: Any, key: str = "") -> Any:
    """Ignore producer identities/times while retaining all state and route facts."""
    if isinstance(value, dict):
        return {name: _normalise_wire(item, name) for name, item in value.items()}
    if isinstance(value, list):
        return [_normalise_wire(item, key) for item in value]
    if isinstance(value, str):
        if key in _VOLATILE_ID_KEYS or key in {
            "requested_at",
            "updated_at",
            "created_at",
            "started_at",
            "ended_at",
            "completed_at",
            "sync_modified_at",
            "capture_checkpoint_at",
        }:
            return "<producer-volatile>"
        # The retry detail carries the due time inside a human-readable cause.
        # Preserve the cause and retry wording while ignoring only that clock.
        return re.sub(
            r"Retrying at \d{4}-\d{2}-\d{2}T[^.]+\.",
            "Retrying at <producer-volatile>.",
            value,
        )
    return value


def test_summary_wire_fixture_matches_real_producer_states(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """Keep the fixture equal to newly minted producer wires, ignoring identities."""
    fixture = json.loads(FIXTURE.read_text())
    assert fixture["schema"] == "PHILO-3-02-summary-wire@1"
    produced = _produce_summary_wire_cases(tmp_path / "producer", monkeypatch)
    expected_cases = [
        {"state": state, **wire} for state, wire in produced.items()
    ]
    assert _normalise_wire(fixture["cases"]) == _normalise_wire(expected_cases)
    cases = {case["state"]: case for case in fixture["cases"]}
    assert set(cases) == {
        "imported_off",
        "running",
        "success",
        "retry",
        "terminal_failure",
    }
    required_job_fields = {
        "status",
        "attempts",
        "requested_at",
        "updated_at",
        "last_error",
        "retry_scheduled",
        "next_retry_at",
    }
    for state, case in cases.items():
        assert case["list"]["id"] == case["detail"]["id"]
        assert case["list"]["intel_job"] == case["detail"]["intel_job"]
        job = case["detail"]["intel_job"]
        if state == "imported_off":
            assert job is None
            assert case["detail"]["intel_status"]["state"] == "disabled"
            continue
        assert set(job) == required_job_fields
        assert case["list"]["intel_status"] == {
            "running": "running",
            "success": "ready",
            "retry": "queued",
            "terminal_failure": "error",
        }[state]
    assert cases["running"]["detail"]["intel_job"]["status"] == "running"
    assert cases["success"]["detail"]["intel_job"]["status"] == "succeeded"
    success_route_host = cases["success"]["detail"]["planned_route"]["legs"][0]["host"]
    success_receipt_host = cases["success"]["detail"]["run_receipt"]["attempts"][0]["host"]
    assert success_route_host == "cloud.example"
    assert success_receipt_host == "same_device"
    assert success_route_host != success_receipt_host
    assert (
        cases["success"]["recovery"]["planned_route"]["legs"][0]["host"]
        == "cloud.example"
    )
    assert (
        cases["success"]["recovery"]["job"]["planned_route"]["legs"][0]["host"]
        == "same_device"
    )
    assert cases["retry"]["detail"]["intel_job"]["status"] == "retrying"
    assert cases["retry"]["detail"]["intel_job"]["retry_scheduled"] is True
    assert cases["terminal_failure"]["detail"]["intel_job"]["status"] == "failed"


def test_real_producer_projects_job_into_detail_list_and_recovery(
    tmp_path: Path, monkeypatch: Any
) -> None:
    db, _broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-detail-running")
    _admit(db, state.id)

    reads = _reads(db, state.id)
    for payload in (reads["list"], reads["detail"]):
        job = payload["intel_job"]
        assert job["status"] == "queued"
        assert job["attempts"] == 0
        assert job["requested_at"]
        assert job["updated_at"]
        assert job["last_error"] is None
        assert job["retry_scheduled"] is False
        assert job["next_retry_at"] is None

    recovery_job = reads["recovery"]["job"]
    assert recovery_job["status"] == "queued"
    assert recovery_job["attempts"] == 0
    assert recovery_job["last_error"] is None
    assert recovery_job["retry_scheduled"] is False
    assert recovery_job["next_retry_at"] is None


def test_real_producer_success_keeps_detail_and_recovery_job_projection(
    tmp_path: Path, monkeypatch: Any
) -> None:
    db, _broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-detail-success")
    _admit(db, state.id)

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    reads = _reads(db, state.id)
    assert reads["detail"]["intel"]["summary"]
    assert reads["detail"]["segments"]
    assert reads["detail"]["intel_status"]["state"] == "ready"
    assert reads["detail"]["intel_job"]["status"] == "succeeded"
    assert reads["detail"]["intel_job"]["last_error"] is None
    assert reads["recovery"]["job"]["status"] == "succeeded"


def test_scheduled_retry_projects_retrying_after_due_time_and_manual_enqueue_stays_queued(
    tmp_path: Path, monkeypatch: Any
) -> None:
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-detail-retry")
    _admit(db, state.id)
    engine.error = "provider unavailable"

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job(retry_base_seconds=60) is True
    with db._connection() as conn:
        conn.execute(
            "UPDATE intel_jobs SET requested_at=? WHERE meeting_id=? AND status='queued'",
            ("2020-01-01T00:00:00", state.id),
        )

    reads = _reads(db, state.id)
    producer_error = db.intel.get_latest_intel_job(state.id).last_error
    assert producer_error
    for payload in (reads["list"], reads["detail"]):
        job = payload["intel_job"]
        assert job["status"] == "retrying"
        assert job["attempts"] == 1
        assert job["last_error"] == producer_error
        assert job["retry_scheduled"] is True
        assert job["next_retry_at"] == "2020-01-01T00:00:00"
    recovery_job = reads["recovery"]["job"]
    assert recovery_job["status"] == "retrying"
    assert recovery_job["last_error"] == producer_error
    assert recovery_job["retry_scheduled"] is True

    # An intentional first/manual enqueue carries a reason in the durable row,
    # but it has no failed predecessor and must remain an ordinary QUEUED state.
    manual_db, _broker, _engine, _host, _requests = _queue_rig(
        tmp_path / "manual", monkeypatch
    )
    manual = _meeting(manual_db, "m-philo3-detail-manual")
    _admit(manual_db, manual.id)
    manual_job = _reads(manual_db, manual.id)["detail"]["intel_job"]
    assert manual_job["status"] == "queued"
    assert manual_job["last_error"] is None
    assert manual_job["retry_scheduled"] is False


def test_real_producer_terminal_failure_projects_failed_cause(
    tmp_path: Path, monkeypatch: Any
) -> None:
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-detail-failed")
    _admit(db, state.id)
    engine.error = "recorded provider failure at the endpoint boundary"

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job(retry_max_attempts=1) is True
    reads = _reads(db, state.id)
    producer_error = db.intel.get_latest_intel_job(state.id).last_error
    assert producer_error
    for payload in (reads["list"], reads["detail"]):
        job = payload["intel_job"]
        assert job["status"] == "failed"
        assert job["attempts"] == 1
        assert job["last_error"] == producer_error
        assert job["retry_scheduled"] is False
        assert job["next_retry_at"] is None
    recovery_job = reads["recovery"]["job"]
    assert recovery_job["status"] == "failed"
    assert recovery_job["last_error"] == producer_error
    assert reads["recovery"]["state"] == "failed"


def test_manual_retry_after_terminal_failure_has_no_retry_cause(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """A user retry is a fresh manual request, not an automatic scheduled retry."""
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-detail-manual-after-failure")
    route = project_route(db, invocation_id=f"meeting:{state.id}")
    _admit(db, state.id)
    engine.error = "provider permanently unavailable"

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job(retry_max_attempts=1) is True
    retry = MeetingIntelService(db).retry_recovery(
        OWNER,
        state.id,
        {"expected_selection_hash": route["selection_hash"]},
    )
    assert retry["success"] is True
    job = _reads(db, state.id)["detail"]["intel_job"]
    # The real producer parks this fresh manual leaf until its failed parent is
    # settled.  It is not an automatic scheduled retry and carries no copied
    # failure facts on the current leaf.
    assert job["status"] == "reserved"
    assert job["attempts"] == 0
    assert job["last_error"] is None
    assert job["retry_scheduled"] is False
    assert job["next_retry_at"] is None
