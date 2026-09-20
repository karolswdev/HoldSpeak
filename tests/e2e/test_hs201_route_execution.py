"""HS-201-03: execute only the route disclosed before a Meeting run.

These tests exercise the production queue binder, route controller, kernel, and
drainer over SQLite.  The only runtime seams are endpoint discovery and the
provider leaf that receives the admitted deployment's ``cloud_model``.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from holdspeak.intel import ActionItem, IntelResult
from holdspeak.kernel.provider_signals import ProviderPermanentNoGeneration
from holdspeak.kernel.runtime import _configure
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder
from holdspeak.services.meeting_route_projection import project_route
from holdspeak.services.model_library_service import ModelLibraryApplicationService
from holdspeak.services.model_profile_service import ModelProfileService
from tests.unit.test_hs201_route_contract import OWNER
from tests.unit.test_model_library_providers import _draft, _library
from tests.unit.test_phase143_inference_assignments import _result_claim


pytestmark = pytest.mark.timeout(90, method="signal")


def _meeting(db: Any, meeting_id: str) -> MeetingState:
    meeting = MeetingState(
        id=meeting_id,
        title="Execution fence fixture",
        started_at=datetime(2026, 9, 19, 9, 0, 0),
        ended_at=datetime(2026, 9, 19, 9, 30, 0),
        capture_status="finalized",
        transcription_status="final",
        segments=[
            TranscriptSegment(
                "We agreed to preserve the disclosed route.",
                "Me",
                0.0,
                5.0,
            )
        ],
    )
    db.meetings.save_meeting(meeting)
    return meeting


def _provider(library: ModelLibraryApplicationService, profile_id: str, host: str) -> int:
    """Add one real Model Library endpoint and qualify its immutable revision."""
    library.define_endpoint(
        OWNER,
        _draft(
            request_id=f"hs201-{profile_id}",
            profile_id=profile_id,
            provider_family="private_endpoint",
            endpoint=f"http://{host}:8080/v1",
            requires_key=False,
            model=profile_id,
        ),
        None,
    )
    db = library._db
    profiles = ModelProfileService(db)
    current = profiles.get_profile(OWNER, profile_id)
    claims = [
        "language",
        "structured_output",
        _result_claim("meeting.deferred_analysis"),
    ]
    material = {"claims": claims, "revision": "hs201-fixture-v1"}
    manifest = {
        **material,
        "sha256": "sha256:" + hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }
    revised = profiles.create_profile(
        OWNER,
        {
            "profile_id": profile_id,
            "expected_revision": int(current["revision"]),
            "label": current["label"],
            "provider_family": current["provider_family"],
            "runtime_family": current["runtime_family"],
            "model_or_artifact_identity": current["model_or_artifact_identity"],
            "supported_modalities": list(current["supported_modalities"]),
            "context_support": current["context_support"],
            "tokenizer_template_requirements": current["tokenizer_template_requirements"],
            "capability_manifest": manifest,
            "safe_presentation": current["safe_presentation"],
        },
    )
    binding = profiles.get_binding(OWNER, f"binding-{profile_id}")
    with db._connection() as conn:
        readiness = conn.execute(
            """SELECT readiness_observation_id
               FROM model_profile_binding_revisions
               WHERE binding_id=? AND revision=?""",
            (str(binding["binding_id"]), int(binding["revision"])),
        ).fetchone()
    assert readiness is not None
    profiles.bind_profile(
        OWNER,
        {
            "binding_id": str(binding["binding_id"]),
            "profile_id": profile_id,
            "profile_revision": int(revised["revision"]),
            "deployment_head_id": str(binding["deployment_head_id"]),
            "expected_binding_revision": int(binding["revision"]),
            "expected_deployment_configuration_revision": int(
                binding["deployment_configuration_revision"]
            ),
            "expected_deployment_revision_id": str(binding["deployment_revision_id"]),
            "enabled": True,
            "readiness_observation_id": str(readiness["readiness_observation_id"]),
        },
    )
    return int(revised["revision"])


def _assign(db: Any, profile_ids: list[str], *, expected_revision: int) -> dict[str, Any]:
    with db._connection() as conn:
        revisions = {
            profile_id: int(
                conn.execute(
                    "SELECT MAX(revision) FROM model_profile_revisions WHERE profile_id=?",
                    (profile_id,),
                ).fetchone()[0]
            )
            for profile_id in profile_ids
        }
    return InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "hs201-route-" + "-".join(profile_ids) + f"-{expected_revision}",
            "expected_revision": expected_revision,
            "scope": {
                "kind": "capability",
                "capability_id": "meeting.deferred_analysis",
            },
            "entries": [
                {"profile_id": profile_id, "profile_revision": revisions[profile_id]}
                for profile_id in profile_ids
            ],
        },
    )


def _rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Compose one real database/broker from the canonical endpoint fixture."""
    import holdspeak.db as hsdb

    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    library = _library(tmp_path, store_path=tmp_path / "keys.json")
    db = library._db
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *args, **kwargs: db)
    return db, library, _configure(db)


def _engine_leaf(monkeypatch: pytest.MonkeyPatch, calls: list[str], failures: set[str]) -> None:
    class _Engine:
        active_provider = "fixture-provider"

        def __init__(self, profile_id: str):
            self.active_model = profile_id
            self.profile_id = profile_id

        def analyze(self, _transcript: str, *, stream: bool = False) -> IntelResult:
            assert stream is False
            calls.append(self.profile_id)
            if self.profile_id in failures:
                raise ProviderPermanentNoGeneration()
            return IntelResult(
                topics=["route"],
                action_items=[ActionItem(task="Keep the disclosed route", owner="Me")],
                summary=f"Generated by {self.profile_id}.",
                raw_response="{}",
            )

    def build(**kwargs: Any) -> _Engine:
        model = str(kwargs.get("cloud_model") or "")
        assert model
        return _Engine(model)

    # Private-endpoint revisions reach ``MeetingIntel`` with cloud_model equal
    # to the immutable profile model. No configured-engine fallback is patched.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", build)


def _child_operations(db: Any, parent_operation_id: str) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """SELECT * FROM kernel_operations
                   WHERE parent_operation_id=? AND name='inference.invoke'
                   ORDER BY created_at, operation_id""",
                (parent_operation_id,),
            ).fetchall()
        ]


def test_real_drainer_records_primary_failure_and_fallback_at_distinct_hosts_and_reopens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, library, _broker = _rig(tmp_path, monkeypatch)
    _provider(library, "execution-primary", "192.168.1.10")
    _provider(library, "execution-fallback", "192.168.1.11")
    _assign(db, ["execution-primary", "execution-fallback"], expected_revision=0)
    meeting = _meeting(db, "hs201-real-fallback")
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    assert [leg["host"] for leg in route["legs"]] == ["192.168.1.10", "192.168.1.11"]
    db.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash=meeting.transcript_hash(),
        reason="HS-201 execution fence",
        planned_route=route,
    )

    calls: list[str] = []
    _engine_leaf(monkeypatch, calls, {"execution-primary"})
    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    receipt = db.intel.get_run_receipt(meeting.id)
    assert receipt is not None
    receipt_job_id = str(receipt["job_id"])
    assert receipt_job_id
    assert receipt["selection_hash"] == route["selection_hash"]
    assert receipt["outcome"] == "succeeded"
    assert [(item["leg_ordinal"], item["host"], item["outcome"]) for item in receipt["attempts"]] == [
        (1, "192.168.1.10", "failed"),
        (2, "192.168.1.11", "succeeded"),
    ]
    assert calls == ["execution-primary", "execution-fallback"]

    job = db.intel.get_latest_intel_job(meeting.id)
    assert job is not None and job.job_id == receipt_job_id
    with db._connection() as conn:
        receipt_row = conn.execute(
            "SELECT parent_operation_id FROM intel_jobs WHERE job_id=?",
            (receipt_job_id,),
        ).fetchone()
    assert receipt_row is not None and receipt_row["parent_operation_id"]
    children = _child_operations(db, str(receipt_row["parent_operation_id"]))
    child_ids = {str(row["operation_id"]) for row in children}
    assert len(children) >= 2
    assert {str(item["operation_id"]) for item in receipt["attempts"]} <= child_ids
    assert all(
        str(row["parent_operation_id"]) == str(receipt_row["parent_operation_id"])
        for row in children
    )

    db_path = Path(db.db_path)
    db.close()
    reopened = type(db)(db_path)
    assert reopened.intel.get_run_receipt(meeting.id) == receipt
    assert reopened.intel.get_latest_intel_job(meeting.id).run_receipt == receipt
    reopened.close()


def test_assignment_drift_after_binder_prepare_refuses_before_provider_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, library, _broker = _rig(tmp_path, monkeypatch)
    _provider(library, "drift-primary", "192.168.1.20")
    _provider(library, "drift-new", "192.168.1.21")
    _assign(db, ["drift-primary"], expected_revision=0)
    meeting = _meeting(db, "hs201-assignment-drift")
    disclosed = project_route(db, invocation_id=f"meeting:{meeting.id}")
    db.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash=meeting.transcript_hash(),
        reason="HS-201 execution fence",
        planned_route=disclosed,
    )

    original_prepare = MeetingDeferredQueueBinder.prepare
    changed = False

    def prepare_then_change(self: Any, job: Any, command_ids: Any) -> None:
        nonlocal changed
        original_prepare(self, job, command_ids)
        if not changed:
            changed = True
            _assign(db, ["drift-new"], expected_revision=1)

    monkeypatch.setattr(MeetingDeferredQueueBinder, "prepare", prepare_then_change)
    calls: list[str] = []
    _engine_leaf(monkeypatch, calls, set())
    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    assert changed is True
    assert calls == []
    receipt = db.intel.get_run_receipt(meeting.id)
    assert receipt is not None
    receipt_job_id = str(receipt["job_id"])
    assert receipt_job_id
    assert receipt["selection_hash"] == disclosed["selection_hash"]
    assert receipt["outcome"] == "refused"
    assert receipt["attempts"] == []
    with db._connection() as conn:
        assert conn.execute(
            """SELECT COUNT(*) FROM kernel_operations
               WHERE name IN ('inference.invoke','meeting.deferred-intel-job')
                 AND state NOT IN ('succeeded','failed','refused','cancelled','indeterminate')"""
        ).fetchone()[0] == 0


def test_inconsistent_disclosure_missing_third_leg_refuses_all_provider_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, library, _broker = _rig(tmp_path, monkeypatch)
    profiles = ["undisclosed-one", "undisclosed-two", "undisclosed-three"]
    for index, profile_id in enumerate(profiles, 10):
        _provider(library, profile_id, f"192.168.1.{index}")
    _assign(db, profiles, expected_revision=0)
    meeting = _meeting(db, "hs201-undisclosed-third")
    full_route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    assert [leg["host"] for leg in full_route["legs"]] == [
        "192.168.1.10",
        "192.168.1.11",
        "192.168.1.12",
    ]
    disclosed = {**full_route, "legs": list(full_route["legs"][:2])}
    db.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash=meeting.transcript_hash(),
        reason="HS-201 execution fence",
        planned_route=disclosed,
    )

    calls: list[str] = []
    _engine_leaf(monkeypatch, calls, set())
    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    assert calls == []
    receipt = db.intel.get_run_receipt(meeting.id)
    assert receipt is not None
    receipt_job_id = str(receipt["job_id"])
    assert receipt_job_id
    assert receipt["outcome"] == "refused"
    assert receipt["attempts"] == []
