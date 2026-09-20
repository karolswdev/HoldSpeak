"""HS-201-05: the real Model Library producer stays on one summary route."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.kernel.runtime import _configure
from holdspeak.services.concierge_service import detect
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder
from holdspeak.services.meeting_route_projection import project_route
from holdspeak.web.context import WebContext
from holdspeak.web.routes.concierge import build_concierge_router
from tests.unit.test_meeting_deferred_admission import _queued_meeting
from tests.unit.test_model_library_providers import OWNER, _draft, _library


pytestmark = pytest.mark.timeout(90, method="signal")


class _Setup:
    def __init__(self, db: Any, home: Path) -> None:
        self._db = db
        self._home_provider = lambda: home


def _client(db: Any, home: Path) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next: Any) -> Any:
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(
        build_concierge_router(
            WebContext(
                get_state=lambda: {},
                inference_setup_service=_Setup(db, home),
                inference_assignment_service=InferenceAssignmentService(db),
            )
        )
    )
    return TestClient(app)


def test_model_library_producer_revision_survives_summary_route_and_queue_freeze(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Connect, detect, select over HTTP, project, and bind one exact revision."""
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    library = _library(tmp_path, store_path=tmp_path / "isolated-keys.json")
    db = library._db
    first = library.define_endpoint(
        OWNER,
        _draft(
            request_id="producer-chain-r1",
            profile_id="producer-chain",
            provider_family="openai_compatible",
            requires_key=False,
        ),
        None,
    )
    detected_r1 = next(item for item in detect(db=db, home=tmp_path / "home")["engines"] if item.get("profileId") == "producer-chain")
    assert detected_r1["profileRevision"] == first["provider"]["profile_revision"]

    second = library.define_endpoint(
        OWNER,
        {
            **_draft(
                request_id="producer-chain-r2",
                profile_id="producer-chain",
                provider_family="openai_compatible",
                label="Fixture v2",
                requires_key=False,
            ),
            "expected_profile_revision": 1,
        },
        None,
    )
    assert second["provider"]["profile_revision"] == 2
    detected = detect(db=db, home=tmp_path / "home")
    engine = next(item for item in detected["engines"] if item.get("profileId") == "producer-chain")
    assert engine["profileId"] == second["provider"]["profile_id"]
    assert engine["profileRevision"] == second["provider"]["profile_revision"]

    client = _client(db, tmp_path / "home")
    response = client.post(
        "/api/concierge/summary-selection",
        json={
            "commandId": "producer-chain-summary",
            "expectedAssignmentRevision": 0,
            "profileId": engine["profileId"],
            "profileRevision": engine["profileRevision"],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "succeeded"
    route = project_route(db, invocation_id="meeting:producer-chain")
    assert route["status"] == "ready"
    assert route["legs"] == [
        {
            **route["legs"][0],
            "profile_id": second["provider"]["profile_id"],
            "profile_revision": second["provider"]["profile_revision"],
            "host": "127.0.0.1",
        }
    ]
    assert not any(
        row["assignment_key"] == "capability:meeting.live_analysis"
        for row in library.assignment_heads(OWNER)["heads"]
    )

    broker = _configure(db)
    meeting = _queued_meeting(db, "producer-chain-meeting")
    db.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash=meeting.transcript_hash(),
        reason="HS-201 producer chain",
        planned_route=route,
    )
    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claimed is not None
    with db._connection() as conn:
        row = conn.execute(
            """SELECT e.profile_id,e.profile_revision,e.deployment_revision_id
               FROM inference_parent_route_bundle_members m
               JOIN inference_route_plan_entries e ON e.plan_id=m.route_plan_id
              WHERE m.bundle_id=? AND m.capability_id='meeting.deferred_analysis'""",
            (claimed.bundle_id,),
        ).fetchone()
    assert row is not None
    assert row["profile_id"] == second["provider"]["profile_id"]
    assert int(row["profile_revision"]) == second["provider"]["profile_revision"]
    assert str(row["deployment_revision_id"]) == route["legs"][0]["deployment_revision_id"]


def test_real_producer_bad_output_is_failed_with_contact_receipt_and_no_summary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """A malformed response fails the frozen producer leg before publication."""
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
    )
    library = _library(tmp_path, store_path=tmp_path / "bad-output-keys.json")
    db = library._db
    producer = library.define_endpoint(
        OWNER,
        _draft(
            request_id="producer-bad-output",
            profile_id="producer-bad-output",
            provider_family="openai_compatible",
            requires_key=False,
        ),
        None,
    )
    client = _client(db, tmp_path / "home")
    response = client.post(
        "/api/concierge/summary-selection",
        json={
            "commandId": "producer-bad-output-summary",
            "expectedAssignmentRevision": 0,
            "profileId": producer["provider"]["profile_id"],
            "profileRevision": producer["provider"]["profile_revision"],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "succeeded"
    route = project_route(db, invocation_id="meeting:producer-bad-output")
    assert route["status"] == "ready"

    monkeypatch.setattr("holdspeak.db.get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *args, **kwargs: db)
    broker = _configure(db)
    meeting = _queued_meeting(db, "producer-bad-output-meeting")
    db.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash=meeting.transcript_hash(),
        reason="HS-201 malformed producer output",
        planned_route=route,
    )
    class _BadProvider:
        active_provider = "fixture-provider"
        active_model = "producer-bad-output"

        def analyze(self, _transcript: str, *, stream: bool = False) -> Any:
            assert stream is False
            return {"summary": "partial must not publish", "topics": [], "action_items": "wrong"}

    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: _BadProvider())
    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job(retry_max_attempts=1) is True
    receipt = db.intel.get_run_receipt(meeting.id)
    assert receipt is not None
    assert receipt["outcome"] == "failed"
    assert receipt["attempts"]
    assert receipt["attempts"][0]["host"] == "127.0.0.1"
    assert receipt["attempts"][0]["outcome"] == "failed"
    assert db.intel.get_latest_intel_job(meeting.id).status == "failed"
    with db._connection() as conn:
        attempt = conn.execute(
            "SELECT disposition,send_phase,outcome FROM inference_route_attempts ORDER BY reserved_at DESC LIMIT 1"
        ).fetchone()
    assert attempt is not None
    assert attempt["disposition"] == "invalid_typed_output"
    assert attempt["send_phase"] == "provider_returned"
    assert attempt["outcome"] == "failed"
    saved = db.meetings.get_meeting(meeting.id)
    assert saved is not None
    assert saved.intel is None
