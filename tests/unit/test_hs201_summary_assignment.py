"""HS-201-05 acceptance fences for the summary selection seam.

The tests exercise the existing profile and assignment authorities.  The
summary gesture must select one real profile revision for the exact deferred
meeting capability, leave speech alone, and return one truthful visible
result when the compare-and-set or compatibility check fails.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.config import Config
from holdspeak.profile_key_store import ProfileKeyStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.concierge_service import (
    assign_summary,
    propose,
    summary_assignment_projection,
)
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.model_profile_service import ModelProfileService
from holdspeak.services.model_library_service import ModelLibraryApplicationService
from holdspeak.services.profile_key_service import ProfileKeyService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim


OWNER = Principal(PrincipalKind.OWNER, "hs201-summary-owner")


def _summary_profile(db: Database, profile_id: str = "summary-profile") -> None:
    _profile(
        db,
        profile_id,
        claims=("language", _result_claim("meeting.deferred_analysis")),
    )


def _speech_profile(db: Database, profile_id: str = "speech-profile") -> None:
    _profile(
        db,
        profile_id,
        claims=("language", _result_claim("speech.transcribe")),
        modalities=("audio",),
    )


def _revise_profile_to_revision_two(db: Database, profile_id: str) -> None:
    profiles = ModelProfileService(db)
    current = profiles.get_profile(OWNER, profile_id)
    profiles.create_profile(
        OWNER,
        {
            "profile_id": profile_id,
            "expected_revision": 1,
            "label": f"{current['label']} v2",
            "provider_family": current["provider_family"],
            "runtime_family": current["runtime_family"],
            "model_or_artifact_identity": current["model_or_artifact_identity"],
            "supported_modalities": current["supported_modalities"],
            "context_support": current["context_support"],
            "tokenizer_template_requirements": current["tokenizer_template_requirements"],
            "capability_manifest": current["capability_manifest"],
            "safe_presentation": current["safe_presentation"],
        },
    )
    with db._connection() as conn:
        deployment = conn.execute(
            "SELECT deployment_id, execution_revision_id, configuration_revision FROM inference_deployments WHERE deployment_id=?",
            (f"head-{profile_id}",),
        ).fetchone()
    observation = profiles.probe_profile(
        OWNER,
        {
            "profile_id": profile_id,
            "profile_revision": 2,
            "deployment_head_id": f"head-{profile_id}",
            "expected_deployment_configuration_revision": int(deployment["configuration_revision"]),
            "expected_deployment_revision_id": str(deployment["execution_revision_id"]),
        },
    )
    with db._connection() as conn:
        conn.execute(
            "UPDATE model_profile_readiness_observations SET state='ready', reason_code='fixture_ready' WHERE observation_id=?",
            (observation["observation_id"],),
        )
    profiles.bind_profile(
        OWNER,
        {
            "binding_id": f"binding-{profile_id}",
            "profile_id": profile_id,
            "profile_revision": 2,
            "deployment_head_id": f"head-{profile_id}",
            "expected_binding_revision": 1,
            "expected_deployment_configuration_revision": int(deployment["configuration_revision"]),
            "expected_deployment_revision_id": str(deployment["execution_revision_id"]),
            "enabled": True,
            "readiness_observation_id": observation["observation_id"],
        },
    )


def test_summary_gesture_writes_exact_capability_with_real_profile_revision_and_preserves_speech(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "summary-assignment.db")
    _summary_profile(db)
    _revise_profile_to_revision_two(db, "summary-profile")
    _speech_profile(db)
    assignments = InferenceAssignmentService(db)
    speech_before = assignments.set_assignment(
        OWNER,
        {
            "command_id": "speech-before-summary",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "speech.transcribe"},
            "entries": [{"profile_id": "speech-profile", "profile_revision": 1}],
        },
    )

    result = assign_summary(
        assignment_service=assignments,
        principal=OWNER,
        db=db,
        profile_id="summary-profile",
        profile_revision=2,
        expected_assignment_revision=0,
        command_id="summary-gesture-one",
    )

    assert result["schema"] == "ConciergeSummaryAssignmentReceipt@1"
    assert result["status"] == "succeeded"
    assert result["result"]["state"] == "READY"
    assert result["result"]["profileRevision"] == 2
    summary = assignments.get_assignment(
        OWNER, {"kind": "capability", "capability_id": "meeting.deferred_analysis"}
    )
    assert summary["scope"] == {
        "kind": "capability",
        "capability_id": "meeting.deferred_analysis",
    }
    assert summary["entries"] == [
        {
            "ordinal": 1,
            "profile_id": "summary-profile",
            "profile_revision": 2,
            "profile_schema_version": 2,
            "label": "Summary Profile v2",
            "boundary": "local",
            "readiness": "ready",
        }
    ]
    speech_after = assignments.get_assignment(
        OWNER, {"kind": "capability", "capability_id": "speech.transcribe"}
    )
    assert speech_after["revision"] == speech_before["revision"]
    assert speech_after["scope"] == speech_before["scope"]
    assert speech_after["entries"] == speech_before["entries"]
    with db._connection() as conn:
        receipt = conn.execute(
            "SELECT state, operation_id FROM kernel_receipts WHERE receipt_id=?",
            (result["receipt"]["id"],),
        ).fetchone()
    assert receipt is not None
    assert receipt["state"] == "succeeded"


def test_summary_gesture_rejects_stale_profile_revision_after_profile_head_moves(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "summary-stale-profile.db")
    _summary_profile(db)
    _revise_profile_to_revision_two(db, "summary-profile")
    assignments = InferenceAssignmentService(db)

    result = assign_summary(
        assignment_service=assignments,
        principal=OWNER,
        db=db,
        profile_id="summary-profile",
        profile_revision=1,
        expected_assignment_revision=0,
        command_id="summary-stale-profile",
    )

    assert result["status"] == "partial"
    assert result["result"]["state"] == "FAILED"
    assert result["result"]["code"] == "inference_assignment_binding_missing"


def test_summary_projection_names_the_engine_that_service_will_run(tmp_path: Path) -> None:
    db = Database(tmp_path / "summary-projection.db")
    _summary_profile(db)
    assignments = InferenceAssignmentService(db)

    empty = summary_assignment_projection(
        assignment_service=assignments,
        principal=OWNER,
    )
    assert empty["status"] == "unassigned"
    assert empty["capabilityId"] == "meeting.deferred_analysis"
    assert empty["profileId"] is None

    assign_summary(
        assignment_service=assignments,
        principal=OWNER,
        db=db,
        profile_id="summary-profile",
        profile_revision=1,
        expected_assignment_revision=0,
        command_id="summary-projection-one",
    )
    projection = summary_assignment_projection(
        assignment_service=assignments,
        principal=OWNER,
    )
    assert projection == {
        "schema": "ConciergeSummaryAssignmentProjection@1",
        "capabilityId": "meeting.deferred_analysis",
        "status": "assigned",
        "assignmentRevision": 1,
        "profileId": "summary-profile",
        "profileRevision": 1,
        "label": "Summary Profile",
        "boundary": "local",
        "readiness": "ready",
    }


def test_summary_gesture_reports_revision_conflict_without_silent_success(tmp_path: Path) -> None:
    db = Database(tmp_path / "summary-conflict.db")
    _summary_profile(db, "summary-one")
    _summary_profile(db, "summary-two")
    assignments = InferenceAssignmentService(db)
    assign_summary(
        assignment_service=assignments,
        principal=OWNER,
        db=db,
        profile_id="summary-one",
        profile_revision=1,
        expected_assignment_revision=0,
        command_id="summary-conflict-seed",
    )

    result = assign_summary(
        assignment_service=assignments,
        principal=OWNER,
        db=db,
        profile_id="summary-two",
        profile_revision=1,
        expected_assignment_revision=0,
        command_id="summary-conflict-stale",
    )

    assert result["status"] == "conflict"
    assert result["result"]["state"] == "CONFLICT"
    assert result["result"]["code"] == "inference_assignment_revision_conflict"
    assert result["result"]["expectedAssignmentRevision"] == 0
    assert result["result"]["currentAssignmentRevision"] == 1
    current = assignments.get_assignment(
        OWNER, {"kind": "capability", "capability_id": "meeting.deferred_analysis"}
    )
    assert current["entries"][0]["profile_id"] == "summary-one"


def test_summary_gesture_reports_partial_failure_for_incompatible_text_profile(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "summary-incompatible.db")
    _profile(db, "text-only", claims=("language",))
    assignments = InferenceAssignmentService(db)

    result = assign_summary(
        assignment_service=assignments,
        principal=OWNER,
        db=db,
        profile_id="text-only",
        profile_revision=1,
        expected_assignment_revision=0,
        command_id="summary-incompatible-one",
    )

    assert result["status"] == "partial"
    assert result["result"]["state"] == "FAILED"
    assert result["result"]["code"] == "inference_assignment_incompatible"
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_heads WHERE assignment_key=?",
            ("capability:meeting.deferred_analysis",),
        ).fetchone()[0] == 0


def test_speech_assignment_cannot_use_text_only_profile(tmp_path: Path) -> None:
    db = Database(tmp_path / "speech-text-fence.db")
    _profile(db, "text-only", claims=("language",))
    assignments = InferenceAssignmentService(db)
    with pytest.raises(Exception) as refusal:
        assignments.set_assignment(
            OWNER,
            {
                "command_id": "speech-text-only",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "speech.transcribe"},
                "entries": [{"profile_id": "text-only", "profile_revision": 1}],
            },
        )
    assert getattr(refusal.value, "code", "") == "inference_assignment_incompatible"


def test_summary_proposal_never_offers_text_only_engine_to_speech() -> None:
    rows = propose(
        engines=[
            {
                "id": "local:whisper-text-only",
                "kind": "local",
                "name": "whisper-text-only",
                "host": "THIS DEVICE",
                "state": "READY",
                "profileId": "text-only",
                "profileRevision": 1,
                "audioCapable": False,
            }
        ]
    )["rows"]
    speech = next(row for row in rows if row["group"] == "speech_recognition")
    assert speech["state"] == "WAITING"
    assert speech["engineId"] is None


def test_summary_selection_then_real_queue_binder_freezes_selected_revision(
    tmp_path: Path,
) -> None:
    """The Concierge choice is the profile the SERVICE queue binds and freezes."""
    from holdspeak.meeting_session.deferred_bound import QUEUE_SERVICE_IDENTITY
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder
    from tests.unit.test_meeting_deferred_admission import (
        _assign_deferred_queue_routes,
        _profile as _queue_profile,
        _queued_meeting,
    )

    db = Database(tmp_path / "summary-binder.db")
    _assign_deferred_queue_routes(db)
    broker = _configure(db)
    _queue_profile(
        db,
        "selected-summary-profile",
        claims=("language", "structured_output", _result_claim("meeting.deferred_analysis")),
        modalities=("language", "text"),
    )
    _revise_profile_to_revision_two(db, "selected-summary-profile")
    assignments = InferenceAssignmentService(db)
    selected = assign_summary(
        assignment_service=assignments,
        principal=OWNER,
        db=db,
        profile_id="selected-summary-profile",
        profile_revision=2,
        expected_assignment_revision=1,
        command_id="summary-queue-selection",
    )
    assert selected["status"] == "succeeded"

    state = _queued_meeting(db, "hs201-summary-binder")
    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claimed is not None
    assert claimed.parent_operation_id and claimed.bundle_id

    with db._connection() as conn:
        operation = conn.execute(
            "SELECT principal_kind,principal_identity,name FROM kernel_operations WHERE operation_id=?",
            (claimed.parent_operation_id,),
        ).fetchone()
        frozen = conn.execute(
            """SELECT p.capability_id,e.profile_id,e.profile_revision
                 FROM inference_parent_route_bundle_members p
                 JOIN inference_route_plan_entries e ON e.plan_id=p.route_plan_id
                WHERE p.bundle_id=? AND p.capability_id=?""",
            (claimed.bundle_id, "meeting.deferred_analysis"),
        ).fetchone()
    assert operation is not None
    assert operation["principal_kind"] == "service"
    assert operation["principal_identity"] == QUEUE_SERVICE_IDENTITY
    assert operation["name"] == "meeting.deferred-intel-job"
    assert frozen is not None
    assert frozen["profile_id"] == "selected-summary-profile"
    assert int(frozen["profile_revision"]) == 2
    assert state.id == "hs201-summary-binder"


def _assignment_table_bytes(db: Database) -> bytes:
    """Capture every canonical assignment row, including historical revisions."""
    tables = (
        "inference_assignment_heads",
        "inference_assignment_revisions",
        "inference_assignments",
        "inference_assignment_commands",
        "inference_assignment_migrations",
    )
    snapshot: dict[str, list[tuple[object, ...]]] = {}
    with db._connection() as conn:
        for table in tables:
            rows = conn.execute(f"SELECT * FROM {table}").fetchall()
            snapshot[table] = [tuple(row) for row in rows]
    return json.dumps(snapshot, sort_keys=True, separators=(",", ":"), default=str).encode()


def test_model_library_connection_keeps_assignment_rows_byte_equivalent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Connecting a provider changes availability only; it cannot select a route."""
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    db = Database(tmp_path / "model-library-connection.db")
    setup = InferenceSetupApplicationService(
        db, config_provider=Config, home_provider=lambda: tmp_path / "home",
    )
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: tmp_path / "home",
    )
    library = ModelLibraryApplicationService(
        db,
        setup_service=setup,
        acquisition_service=acquisition,
        profile_key_service=ProfileKeyService(
            db, store=ProfileKeyStore(tmp_path / "keys" / "profile-keys.json"),
        ),
    )
    _speech_profile(db, "existing-speech")
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "existing-speech-assignment",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "speech.transcribe"},
            "entries": [{"profile_id": "existing-speech", "profile_revision": 1}],
        },
    )
    before = _assignment_table_bytes(db)
    result = library.define_endpoint(
        OWNER,
        {
            "request_id": "connection-without-selection",
            "profile_id": "connected-summary",
            "expected_profile_revision": 0,
            "label": "Fixture summary endpoint",
            "provider_family": "openai_compatible",
            "model": "fixture/summary",
            "endpoint": "http://127.0.0.1:9000/v1",
            "requires_key": True,
        },
        {"value": "fixture-key"},
    )
    assert result["receipt"]["assignments_unchanged"] is True
    assert _assignment_table_bytes(db) == before
