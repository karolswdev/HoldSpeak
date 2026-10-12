"""The meeting summary tests: one file for the service (merged from phase-named files, 2026-10-12)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import holdspeak.db as hsdb
from holdspeak.commands import doctor
from holdspeak.commands.doctor import _check_trust_destinations
from holdspeak.config import Config
from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.profile_key_store import ProfileKeyStore
from holdspeak.services.concierge_service import (
    apply,
    assign_summary,
    detect,
    propose,
    summary_assignment_projection,
)
from holdspeak.services.inference_acquisition_service import (
    InferenceAcquisitionApplicationService,
)
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.services.meeting_route_projection import project_route
from holdspeak.services.model_library_service import ModelLibraryApplicationService
from holdspeak.services.model_profile_service import ModelProfileService
from holdspeak.services.profile_key_service import ProfileKeyService
from holdspeak.services.profile_service import ProfileService
from holdspeak.setup_status import _trust_block
from tests.unit.test_hs201_route_contract import OWNER as OWNER_egress
from tests.unit.test_hs201_route_contract import assign_summary as assign_summary_egress
from tests.unit.test_meeting_deferred_admission import _queue_rig
from tests.unit.test_mesh_liveness_surfaces import _modern_mesh_summary_assignment
from tests.unit.test_model_library_providers import OWNER, _draft, _library
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

# ── from test_hs201_summary_producer.py: HS-201-05 producer identity fences. ──
#
# These tests keep the Concierge's detected profile reference tied to the
# canonical Model Library producer.  A legacy endpoint row may still be shown,
# but it does not carry an invented immutable revision into a summary gesture.


def test_detect_carries_the_model_library_revision_from_the_producer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Connect and reconnect the same canonical profile, then detect it."""
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    library = _library(tmp_path, store_path=tmp_path / "profile-keys.json")
    assignments_before = library.assignment_heads(OWNER)
    first = library.define_endpoint(
        OWNER,
        _draft(
            request_id="producer-r1",
            profile_id="producer-main",
            provider_family="openai_compatible",
            requires_key=False,
        ),
        None,
    )
    second = library.define_endpoint(
        OWNER,
        {
            **_draft(
                request_id="producer-r2",
                profile_id="producer-main",
                provider_family="openai_compatible",
                label="Fixture v2",
                requires_key=False,
            ),
            "expected_profile_revision": 1,
        },
        None,
    )

    assert first["provider"]["profile_id"] == "producer-main"
    assert first["provider"]["profile_revision"] == 1
    assert second["provider"]["profile_id"] == "producer-main"
    assert second["provider"]["profile_revision"] == 2

    result = detect(db=library._db, home=tmp_path / "home")
    rows = [row for row in result["engines"] if row.get("profileId") == "producer-main"]
    assert len(rows) == 1
    assert rows[0]["profileId"] == second["provider"]["profile_id"]
    assert rows[0]["profileRevision"] == second["provider"]["profile_revision"]
    assert library.assignment_heads(OWNER) == assignments_before


def test_detect_does_not_invent_revision_for_a_legacy_endpoint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """A v1 endpoint has no immutable revision to pass to assignment CAS."""
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    db = Database(tmp_path / "legacy-endpoint.db")
    ProfileService(db).create_profile(
        Principal(PrincipalKind.OWNER, "legacy-producer-owner"),
        {
            "id": "legacy-endpoint",
            "name": "Legacy endpoint",
            "kind": "openAICompatible",
            "base_url": "http://127.0.0.1:9000/v1",
            "model": "fixture",
            "requires_key": False,
        },
    )

    result = detect(db=db, home=tmp_path / "home")
    row = next(row for row in result["engines"] if row.get("profileId") == "legacy-endpoint")
    assert row["profileId"] == "legacy-endpoint"
    assert "profileRevision" not in row


def test_old_v1_manifest_stays_incompatible_while_producer_mints_v2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """The baseline v1 manifest cannot route; a real reconnect mints v2."""
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    library = _library(tmp_path / "reconnect", store_path=tmp_path / "reconnect-keys.json")
    # Baseline setup uses the producer's prior language-only profile body. It
    # stands in for a persisted v1 row; no profile qualification is performed.
    current_body = ModelLibraryApplicationService._profile_body

    def old_profile_body(draft: dict[str, object]) -> dict[str, object]:
        body = current_body(draft)
        evidence = {"revision": "model-library-provider-v1", "claims": ["language"]}
        return {
            **body,
            "supported_modalities": ["language"],
            "capability_manifest": {
                **evidence,
                "sha256": "sha256:" + hashlib.sha256(
                    json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            },
        }

    monkeypatch.setattr(ModelLibraryApplicationService, "_profile_body", staticmethod(old_profile_body))
    first = library.define_endpoint(
        OWNER,
        _draft(
            request_id="reconnect-v1",
            profile_id="reconnect-producer",
            provider_family="openai_compatible",
            requires_key=False,
        ),
        None,
    )
    with library._db._connection() as conn:
        old_row = dict(conn.execute(
            "SELECT revision,sha256,capability_manifest_json FROM model_profile_revisions WHERE profile_id=? AND revision=1",
            ("reconnect-producer",),
        ).fetchone())
    monkeypatch.setattr(ModelLibraryApplicationService, "_profile_body", staticmethod(current_body))
    old = assign_summary(
        assignment_service=InferenceAssignmentService(library._db),
        principal=OWNER,
        db=library._db,
        profile_id=first["provider"]["profile_id"],
        profile_revision=first["provider"]["profile_revision"],
        expected_assignment_revision=0,
        command_id="old-v1-summary",
    )
    assert old["status"] == "partial"
    assert old["result"]["code"] == "inference_assignment_incompatible"

    second = library.define_endpoint(
        OWNER,
        {
            **_draft(
                request_id="reconnect-v2",
                profile_id="reconnect-producer",
                provider_family="openai_compatible",
                requires_key=False,
            ),
            "expected_profile_revision": 1,
            "label": "Reconnected v2",
        },
        None,
    )
    assert second["provider"]["profile_revision"] == 2
    with library._db._connection() as conn:
        new_row = dict(conn.execute(
            "SELECT revision,sha256,capability_manifest_json FROM model_profile_revisions WHERE profile_id=? AND revision=1",
            ("reconnect-producer",),
        ).fetchone())
    assert new_row == old_row
    profile = library._profiles.get_profile(OWNER, second["provider"]["profile_id"])
    assert profile["capability_manifest"]["revision"] == "model-library-enforced-results-v3"
    assert any(
        claim.startswith("result_schema:")
        for claim in profile["capability_manifest"]["claims"]
    )
    fresh = assign_summary(
        assignment_service=InferenceAssignmentService(library._db),
        principal=OWNER,
        db=library._db,
        profile_id=second["provider"]["profile_id"],
        profile_revision=second["provider"]["profile_revision"],
        expected_assignment_revision=0,
        command_id="new-v2-summary",
    )
    assert fresh["status"] == "succeeded"


def test_manifest_result_schema_claim_excludes_unexecuted_provider_families(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Anthropic, paired, and future families retain language-only claims."""
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    # These families are deliberately checked at the producer mint seam only:
    # existing provider tests cover their readiness/binding refusals, while
    # this fence proves no unsupported family receives the Meeting claim.
    for family in ("anthropic", "future_backend", "paired_device"):
        body = ModelLibraryApplicationService._profile_body(
            {
                "profile_id": f"excluded-{family}",
                "expected_profile_revision": 0,
                "label": "Excluded family",
                "provider_family": family,
                "model": "fixture",
            }
        )
        assert body["supported_modalities"] == ["language"]
        manifest = body["capability_manifest"]
        assert not any(
            str(claim).startswith("result_schema:")
            for claim in manifest["claims"]
        )


def test_summary_apply_refuses_a_profile_without_an_immutable_revision(
    tmp_path: Path,
) -> None:
    """The Meetings gesture must not turn a v1 endpoint into ``@1``."""
    db = Database(tmp_path / "legacy-summary.db")
    db.profiles.upsert(
        profile_id="legacy-endpoint",
        name="Legacy endpoint",
        kind="openAICompatible",
        base_url="http://127.0.0.1:9000/v1",
        model="fixture",
        requires_key=False,
    )

    result = apply(
        rows=[{"group": "meetings", "engineId": "lan:legacy", "state": "READY"}],
        engines=[
            {
                "id": "lan:legacy",
                "kind": "lan",
                "profileId": "legacy-endpoint",
                "state": "READY",
            }
        ],
        assignment_service=InferenceAssignmentService(db),
        principal=OWNER,
        db=db,
    )

    assert result["results"] == [
        {
            "group": "meetings",
            "capabilityId": "meeting.deferred_analysis",
            "state": "FAILED",
            "code": "concierge_summary_profile_revision_missing",
            "token": "NO MODEL RECORD",
            "plainReason": "This engine has no immutable model profile revision.",
        }
    ]


# ── from test_hs201_summary_assignment.py: HS-201-05 acceptance fences for the summary selection seam. ──
#
# The tests exercise the existing profile and assignment authorities.  The
# summary gesture must select one real profile revision for the exact deferred
# meeting capability, leave speech alone, and return one truthful visible
# result when the compare-and-set or compatibility check fails.


OWNER_assignment = Principal(PrincipalKind.OWNER, "hs201-summary-owner")


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
    current = profiles.get_profile(OWNER_assignment, profile_id)
    profiles.create_profile(
        OWNER_assignment,
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
        OWNER_assignment,
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
        OWNER_assignment,
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
        OWNER_assignment,
        {
            "command_id": "speech-before-summary",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "speech.transcribe"},
            "entries": [{"profile_id": "speech-profile", "profile_revision": 1}],
        },
    )

    result = assign_summary(
        assignment_service=assignments,
        principal=OWNER_assignment,
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
        OWNER_assignment, {"kind": "capability", "capability_id": "meeting.deferred_analysis"}
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
        OWNER_assignment, {"kind": "capability", "capability_id": "speech.transcribe"}
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
        principal=OWNER_assignment,
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
        principal=OWNER_assignment,
    )
    assert empty["status"] == "unassigned"
    assert empty["capabilityId"] == "meeting.deferred_analysis"
    assert empty["profileId"] is None

    assign_summary(
        assignment_service=assignments,
        principal=OWNER_assignment,
        db=db,
        profile_id="summary-profile",
        profile_revision=1,
        expected_assignment_revision=0,
        command_id="summary-projection-one",
    )
    projection = summary_assignment_projection(
        assignment_service=assignments,
        principal=OWNER_assignment,
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
        principal=OWNER_assignment,
        db=db,
        profile_id="summary-one",
        profile_revision=1,
        expected_assignment_revision=0,
        command_id="summary-conflict-seed",
    )

    result = assign_summary(
        assignment_service=assignments,
        principal=OWNER_assignment,
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
        OWNER_assignment, {"kind": "capability", "capability_id": "meeting.deferred_analysis"}
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
        principal=OWNER_assignment,
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
            OWNER_assignment,
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
    from holdspeak.kernel.runtime import _configure
    from holdspeak.meeting_session.deferred_bound import QUEUE_SERVICE_IDENTITY
    from holdspeak.services.meeting_deferred_queue_binding import (
        MeetingDeferredQueueBinder,
    )
    from tests.unit.test_meeting_deferred_admission import (
        _assign_deferred_queue_routes,
        _queued_meeting,
    )
    from tests.unit.test_meeting_deferred_admission import (
        _profile as _queue_profile,
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
        principal=OWNER_assignment,
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
        OWNER_assignment,
        {
            "command_id": "existing-speech-assignment",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "speech.transcribe"},
            "entries": [{"profile_id": "existing-speech", "profile_revision": 1}],
        },
    )
    before = _assignment_table_bytes(db)
    result = library.define_endpoint(
        OWNER_assignment,
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


# ── from test_hs201_summary_doctor.py: HS-201 follow-up: doctor names the exact assigned summary route. ──


@pytest.fixture
def summary_db(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "summary-doctor.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    yield db
    reset_database()


def test_doctor_names_assigned_summary_route_and_ignores_legacy_pointer(summary_db) -> None:
    _modern_mesh_summary_assignment(summary_db)
    config = SimpleNamespace(
        meeting=SimpleNamespace(
            # This pointer is legacy state. The SERVICE assignment above is
            # the route that a Meeting summary actually uses.
            intel_enabled=True,
            intel_provider="cloud",
            intel_cloud_model="legacy-model",
            intel_cloud_api_key_env="LEGACY_KEY",
            intel_cloud_base_url="https://legacy.example.test/v1",
            intel_profile_id="legacyprofile",
        ),
        dictation=SimpleNamespace(
            pipeline=SimpleNamespace(enabled=False),
            runtime=SimpleNamespace(profile_id=None),
        ),
    )

    check = doctor._check_runtime_profiles(config)

    assert check.status == "PASS"
    assert "Meeting summary: profile 'Pocket 4B' (mesh node 'walk-edge')" in check.detail
    assert "Live analysis is off for Record." in check.detail
    assert "legacyprofile" not in check.detail


def test_doctor_quietly_names_unavailable_summary(summary_db) -> None:
    config = SimpleNamespace(
        meeting=SimpleNamespace(intel_profile_id="legacyprofile"),
        dictation=SimpleNamespace(
            pipeline=SimpleNamespace(enabled=False),
            runtime=SimpleNamespace(profile_id=None),
        ),
    )

    check = doctor._check_runtime_profiles(config)

    assert check.status == "PASS"
    assert "Meeting summary: unavailable (no assignment)" in check.detail
    assert "Live analysis is off for Record." in check.detail
    assert "legacyprofile" not in check.detail


def test_doctor_trust_inventory_uses_the_assigned_summary_route(summary_db) -> None:
    _modern_mesh_summary_assignment(summary_db)
    config = Config()
    config.meeting.intel_profile_id = "legacyprofile"

    check = _check_trust_destinations(config)

    assert check.status == "WARN"
    assert "Meeting summary" in check.detail


# ── from test_hs201_summary_egress.py: HS-201 follow-up: trust reports the assigned summary route. ──


def _meeting_db(tmp_path) -> Database:
    db = Database(tmp_path / "summary-egress.db")
    db.meetings.save_meeting(
        MeetingState(
            id="summary-egress-meeting",
            title="Summary egress",
            started_at=datetime.now(),
            segments=[TranscriptSegment("Ship the report.", "Me", 0.0, 1.0)],
        )
    )
    return db


def _cloud_profile(db: Database, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use the production Model Library producer with a stubbed probe leaf."""
    from holdspeak.services.inference_acquisition_service import (
        InferenceAcquisitionApplicationService,
    )
    from holdspeak.services.inference_setup_service import (
        InferenceSetupApplicationService,
    )
    from holdspeak.services.model_library_service import ModelLibraryApplicationService

    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    monkeypatch.setattr(
        "holdspeak.profile_key_store.resolve_profile_key",
        lambda *_args, **_kwargs: None,
    )
    setup = InferenceSetupApplicationService(
        db, config_provider=Config, home_provider=lambda: tmp_path / "home"
    )
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=tmp_path / "custody", home_provider=lambda: tmp_path / "home"
    )
    ModelLibraryApplicationService(
        db, setup_service=setup, acquisition_service=acquisition
    ).define_endpoint(
        OWNER_egress,
        {
            "request_id": "summary-cloud-define",
            "profile_id": "summary-cloud",
            "expected_profile_revision": 0,
            "label": "Summary Cloud",
            "provider_family": "openai_compatible",
            "model": "uat-never-invoked",
            "endpoint": "https://api.openai.com/v1",
            "requires_key": False,
        },
        None,
    )


def test_summary_display_enriches_project_route_without_changing_public_route(tmp_path, monkeypatch) -> None:
    from holdspeak.services.meeting_route_projection import summary_route_display

    db = _meeting_db(tmp_path)
    _profile(
        db,
        "summary-local",
        claims=("language", "structured_output", _result_claim("meeting.deferred_analysis")),
        modalities=("language", "text"),
    )
    _cloud_profile(db, tmp_path, monkeypatch)
    assign_summary_egress(db, ["summary-local", "summary-cloud"])

    public = project_route(db, invocation_id="summary-egress")
    display = summary_route_display(db)

    assert public["legs"][0].keys() == {
        "ordinal", "host", "boundary", "profile_id", "profile_revision", "deployment_revision_id"
    }
    assert public["legs"][1]["host"] == "api.openai.com"
    assert display["selection_hash"] == public["selection_hash"]
    assert display["legs"][0]["profile_label"] == "Summary Local"
    assert display["legs"][1]["profile_label"] == "Summary Cloud"
    assert display["legs"][1]["node"] == ""
    assert set(display["legs"][1]) == set(public["legs"][1]) | {"profile_label", "node"}
    assert set(public["legs"][1]) == {
        "ordinal", "host", "boundary", "profile_id", "profile_revision", "deployment_revision_id"
    }


def test_trust_reports_assigned_summary_route_even_when_legacy_intel_is_off(tmp_path, monkeypatch) -> None:
    db = _meeting_db(tmp_path)
    _profile(
        db,
        "summary-local",
        claims=("language", "structured_output", _result_claim("meeting.deferred_analysis")),
        modalities=("language", "text"),
    )
    _cloud_profile(db, tmp_path, monkeypatch)
    assign_summary_egress(db, ["summary-local", "summary-cloud"])

    config = Config()
    config.meeting.intel_enabled = False
    trust = _trust_block(config, database=db)
    meeting = next(row for row in trust["destinations"] if row["id"] == "meeting_intel")

    assert "api.openai.com" in trust["configured_endpoints"]
    assert trust["transcript_egress"] == "configured"
    assert meeting["enabled"] is True
    assert meeting["name"] == "Meeting summary"
    assert meeting["destination"] == "This device -> api.openai.com"
    assert meeting["authority_basis"] == "Assigned summary route"


def test_legacy_cloud_fields_without_assignment_do_not_claim_summary(tmp_path) -> None:
    from holdspeak.services.meeting_route_projection import summary_route_display

    db = _meeting_db(tmp_path)
    config = Config()
    config.meeting.intel_enabled = True
    config.meeting.intel_provider = "cloud"
    config.meeting.intel_cloud_base_url = "https://api.openai.com/v1"

    trust = _trust_block(config, database=db)
    meeting = next(row for row in trust["destinations"] if row["id"] == "meeting_intel")

    assert trust["transcript_egress"] == "none"
    assert "api.openai.com" not in trust["configured_endpoints"]
    assert meeting["enabled"] is False
    assert meeting["destination"] == "Summary route unavailable"
    assert meeting["name"] == "Meeting summary"
    assert meeting["boundary"] == "unavailable"
    assert summary_route_display(db)["status"] == "unavailable"


# ── from test_philo3_summary_counts.py: PHILO-3-02: the Queue HUD count follows the current queue leaf. ──


OWNER_counts = Principal(PrincipalKind.OWNER, "summary-count-owner")


@pytest.fixture()
def runtime_queue_frames():
    from holdspeak.intel_queue_conductor import set_broadcast

    frames: list[tuple[str, dict[str, Any]]] = []
    set_broadcast(lambda event, frame: frames.append((event, frame)))
    try:
        yield frames
    finally:
        set_broadcast(None)


def _meeting(db: Any, meeting_id: str) -> MeetingState:
    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 10, 9, 0, 0),
        ended_at=datetime(2026, 8, 10, 9, 30, 0),
        title="Summary count fence",
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
        OWNER_counts, meeting_id, expected_selection_hash=route["selection_hash"]
    )


def test_terminal_failure_is_not_still_queued_in_runtime_frame(
    tmp_path, monkeypatch, runtime_queue_frames
):
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-summary-count-failed")
    _admit(db, state.id)

    from holdspeak.intel_queue import build_runtime_queue_frame, process_next_intel_job

    assert build_runtime_queue_frame(db)["queued"] == 1
    engine.error = "provider unavailable"
    assert process_next_intel_job(retry_max_attempts=1) is True

    frame = build_runtime_queue_frame(db)
    assert frame["queued"] == 0
    assert frame["failed"] == 1

    emitted = [
        frame for event, frame in runtime_queue_frames if event == "runtime_queue"
    ]
    assert emitted
    assert emitted[-1]["queued"] == 0
    assert emitted[-1]["failed"] == 1

    summary = MeetingIntelService(db).queue_summary(OWNER_counts)
    assert summary["queued_jobs"] == 0
    assert summary["failed_jobs"] == 1


def test_scheduled_retry_is_counted_as_queued_and_retrying(
    tmp_path, monkeypatch, runtime_queue_frames
):
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-philo3-summary-count-retry")
    _admit(db, state.id)

    from holdspeak.intel_queue import build_runtime_queue_frame, process_next_intel_job

    engine.error = "provider unavailable"
    assert process_next_intel_job(retry_base_seconds=60) is True

    frame = build_runtime_queue_frame(db)
    assert frame["queued"] == 1
    assert frame["failed"] == 0
    assert frame["scheduled_retries"] == 1

    emitted = [
        frame for event, frame in runtime_queue_frames if event == "runtime_queue"
    ]
    assert emitted
    assert emitted[-1]["queued"] == 1
    assert emitted[-1]["failed"] == 0
    assert emitted[-1]["scheduled_retries"] == 1

    summary = MeetingIntelService(db).queue_summary(OWNER_counts)
    assert summary["queued_jobs"] == 1
    assert summary["failed_jobs"] == 0
    assert summary["scheduled_retry_jobs"] == 1


# ── from test_philo3_summary_rig.py: Focused PHILO-3-02 checks for the graph walker seams. ──


REPO = Path(__file__).resolve().parents[2]
RIG_PATH = REPO / "scripts/graph_walk.py"
SPEC = importlib.util.spec_from_file_location("philo3_summary_rig", RIG_PATH)
assert SPEC and SPEC.loader
rig = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rig)


class _Hub:
    def __init__(self, answers):
        self.answers = iter(answers)

    def api(self, method, path):
        return next(self.answers)


class _UploadHub:
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload

    def upload(self, method, path, wav, field, form=None):
        return self.status, self.payload


def test_import_completion_rejects_a_successful_but_malformed_payload(monkeypatch):
    monkeypatch.setattr(rig.time, "sleep", lambda _seconds: None)
    clock = iter([0.0, 0.0, 1.0, 1.0])
    monkeypatch.setattr(rig.time, "monotonic", lambda: next(clock))
    hub = _Hub([(200, {"id": "meeting-1", "segments": []})] * 2)
    result = rig.wait_for_fixture_completion(
        hub,
        {
            "method": "GET",
            "path": "/api/meetings/meeting-1",
            "fields": {
                "/transcription_status": "complete",
                "/duration": {"positive": True},
                "/segments": {"min_items": 1},
            },
            "timeout_s": 0.1,
            "poll_s": 0,
        },
        {},
    )
    assert result["matched"] is False
    assert result["payload"]["segments"] == []


def test_import_completion_stops_at_a_final_failed_transcription(monkeypatch):
    """PHILO-15-03: a failed import is final; the rig stops, never waits 300 s."""
    monkeypatch.setattr(rig.time, "sleep", lambda _seconds: None)
    failed = {"id": "meeting-1", "transcription_status": "failed",
              "intel_status": {"state": "import_failed", "detail": "UNEXPECTED ERROR"}}
    hub = _Hub([(200, {"id": "meeting-1", "transcription_status": "active"}), (200, failed)])
    result = rig.wait_for_fixture_completion(
        hub,
        {
            "method": "GET",
            "path": "/api/meetings/meeting-1",
            "fields": {"/transcription_status": "complete"},
            "timeout_s": 300,
            "poll_s": 0,
        },
        {},
    )
    assert result["matched"] is False
    assert result["terminal"] == {"/transcription_status": "failed"}
    assert result["polls"] == 2
    assert "import_failed" in rig._terminal_note(result)


def test_import_completion_rejects_successful_nonobject_payloads(monkeypatch):
    """A 2xx list/string is not a completed meeting read."""
    monkeypatch.setattr(rig.time, "sleep", lambda _seconds: None)
    clock = iter([0.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    monkeypatch.setattr(rig.time, "monotonic", lambda: next(clock))
    hub = _Hub([(200, []), (200, "still working"), (200, "still working")])
    result = rig.wait_for_fixture_completion(
        hub,
        {
            "method": "GET",
            "path": "/api/meetings/meeting-1",
            "fields": {"/transcription_status": "complete"},
            "timeout_s": 0.1,
            "poll_s": 0,
        },
        {},
    )
    assert result["matched"] is False
    assert result["payload"] == "still working"


def test_fixture_boundary_enforces_declared_admission_status():
    with pytest.raises(rig.Blocked, match="wanted 202"):
        rig.run_step(
            {
                "kind": "fixture",
                "path": "tests/fixtures/philo3_architect_meeting.wav",
                "route": {"method": "POST", "path": "/api/meetings/import"},
                "expect_status": 202,
            },
            None,
            _UploadHub(201, {"meeting_id": "meeting-1"}),
            {"fixture_hashes": {}},
        )


def test_admission_response_requires_queued_state_and_job_identity():
    predicate = {
        "kind": "protocol_status",
        "method": "POST",
        "path": "/api/meetings/meeting-1/intelligence/run",
        "status": 200,
        "body_contains": '"state": "queued"',
        "body_fields": {"jobId": {"nonempty": True}},
    }
    good = {
        "trigger_response": {
            "method": "POST",
            "path": "/api/meetings/meeting-1/intelligence/run",
            "status": 200,
            "body": {"jobId": "job-1", "state": "queued"},
        }
    }
    ok, _reading = rig.check_predicate(predicate, {}, good)
    assert ok
    stale = {
        "trigger_response": {
            "method": "POST",
            "path": "/api/meetings/meeting-1/intelligence/run",
            "status": 200,
            "body": {"jobId": "job-old", "state": "claimed"},
        }
    }
    ok, _reading = rig.check_predicate(predicate, {}, stale)
    assert not ok
    missing_identity = {
        "trigger_response": {
            **good["trigger_response"],
            "body": {"state": "queued"},
        }
    }
    ok, _reading = rig.check_predicate(predicate, {}, missing_identity)
    assert not ok


def test_hit_target_requires_all_interior_points_and_phone_sized_control():
    before = {}
    after = {
        "target_present": True,
        "visible": True,
        "hit_test": {
            "viewport": {"width": 393, "height": 852},
            "rect": {"x": 20, "y": 40, "w": 120, "h": 44},
            "in_viewport": True,
            "all_owned": True,
            "samples": [{"owned": True}] * 9,
        },
    }
    ok, reading = rig.check_predicate(
        {"kind": "hit_target", "min_width": 44, "min_height": 44},
        before,
        after,
    )
    assert ok, reading


def test_hit_target_rejects_occlusion_short_control_and_out_of_viewport():
    base = {
        "target_present": True,
        "visible": True,
        "hit_test": {
            "viewport": {"width": 393, "height": 852},
            "rect": {"x": 20, "y": 40, "w": 120, "h": 44},
            "in_viewport": True,
            "all_owned": True,
            "samples": [{"owned": True}] * 9,
        },
    }
    for mutate in (
        lambda value: value["hit_test"].update(all_owned=False),
        lambda value: value["hit_test"]["rect"].update(h=43),
        lambda value: value["hit_test"].update(in_viewport=False),
    ):
        candidate = {
            "target_present": base["target_present"],
            "visible": base["visible"],
            "hit_test": {
                "viewport": dict(base["hit_test"]["viewport"]),
                "rect": dict(base["hit_test"]["rect"]),
                "in_viewport": base["hit_test"]["in_viewport"],
                "all_owned": base["hit_test"]["all_owned"],
                "samples": list(base["hit_test"]["samples"]),
            },
        }
        mutate(candidate)
        ok, _reading = rig.check_predicate(
            {"kind": "hit_target", "min_width": 44, "min_height": 44},
            {},
            candidate,
        )
        assert not ok


def test_phone_target_requires_44_pixels_without_changing_desktop_size():
    predicate = {"kind": "hit_target", "min_height": 24,
                 "min_height_by_viewport": {"393": 44}}
    observation = {
        "target_present": True, "visible": True,
        "hit_test": {"in_viewport": True, "all_owned": True,
                     "viewport": {"width": 393}, "rect": {"w": 97, "h": 24}},
    }
    assert not rig.check_predicate(predicate, {}, observation)[0]
    observation["hit_test"]["rect"]["h"] = 44
    assert rig.check_predicate(predicate, {}, observation)[0]
    observation["hit_test"]["viewport"]["width"] = 1440
    observation["hit_test"]["rect"]["h"] = 24
    assert rig.check_predicate(predicate, {}, observation)[0]


def test_scheduler_wait_keeps_a_producer_state_already_reached_in_setup(monkeypatch):
    clock = {"now": 0.0}
    monkeypatch.setattr(rig.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(rig.time, "sleep", lambda seconds: clock.update(now=clock["now"] + seconds))
    monkeypatch.setattr(rig, "snapshot", lambda *_args: {
        "protocol": {"payload": {"jobs": [{"status": "claimed"}]},
                     "payload_sha256": "claimed-state"},
    })
    result = rig.scheduler_wait(
        {"adapter": "scheduler-wait", "poll_s": 0.1, "max_wait_s": 0.2},
        {"completion_bound_s": 0.2, "expected": {
            "observe_at": "protocol: GET /api/intel/jobs",
            "predicate": {"kind": "protocol_field", "path": "/jobs/0/status",
                          "value": "claimed"},
        }}, None, _Hub([]), {"clock": {}},
    )
    assert result["polls"] == 0
    assert result["state_satisfied_at_entry"] is True


def test_restart_predicate_requires_summary_receipt_and_identity():
    after = {
        "protocol": {"payload": {"intel": {"summary": "kept"}}},
        "restart": {
            "summary_retained": True,
            "receipt_retained": True,
            "meeting_identity_retained": True,
        },
    }
    ok, reading = rig.check_predicate(
        {
            "kind": "protocol_field",
            "path": "/intel/summary",
            "value": "kept",
            "nonempty": True,
            "restart_required": True,
        },
        {},
        after,
    )
    assert ok, reading


def test_restart_predicate_rejects_each_missing_retention_flag_and_changed_summary():
    predicate = {
        "kind": "protocol_field",
        "path": "/intel/summary",
        "value": "kept",
        "nonempty": True,
        "restart_required": True,
    }
    for missing in ("summary_retained", "receipt_retained", "meeting_identity_retained"):
        restart = {
            "summary_retained": True,
            "receipt_retained": True,
            "meeting_identity_retained": True,
        }
        restart[missing] = False
        ok, _reading = rig.check_predicate(
            predicate,
            {},
            {"protocol": {"payload": {"intel": {"summary": "kept"}}},
             "restart": restart},
        )
        assert not ok

    ok, _reading = rig.check_predicate(
        predicate,
        {},
        {
            "protocol": {"payload": {"intel": {"summary": "changed"}}},
            "restart": {
                "summary_retained": True,
                "receipt_retained": True,
                "meeting_identity_retained": True,
            },
        },
    )
    assert not ok


def test_engine_replay_is_declared_only_by_the_failure_boundary():
    case = {
        "setup": [
            {
                "kind": "boundary",
                "substitute": "engine_reply",
                "reply": "tests/fixtures/philo3_summary_failure_reply.json",
            }
        ],
        "trigger": {"kind": "ui", "action": "click", "selector": "#run"},
    }
    assert rig.case_engine_replay(case) == "tests/fixtures/philo3_summary_failure_reply.json"


def test_optional_framing_keeps_raw_verdict_independent_and_names_scroll_failure(tmp_path):
    class Page:
        def locator(self, selector):
            raise RuntimeError('target disappeared after the raw observation')
    case = {'expected': {'frame_selector': '[data-testid=meeting-summary-text]'}}
    result = rig.capture_framed_view(Page(), case, None, tmp_path)
    assert result['done'] is False
    assert result['selector'] == '[data-testid=meeting-summary-text]'
    assert 'target disappeared' in result['error']
    assert not (tmp_path / 'framed.png').exists()
    assert rig.capture_framed_view(Page(), {'expected': {}}, None, tmp_path) is None
