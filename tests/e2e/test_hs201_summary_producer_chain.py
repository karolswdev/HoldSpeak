"""HS-201-05: the real Model Library producer stays on one summary route.

HS-201-10 extends the chain to the IMPORT door: with a summary engine
already selected, a real import must leave the chain cold — nothing queued,
no provider contacted, no receipt — until the owner's gesture carries the
disclosed selection hash.
"""
from __future__ import annotations

import os
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


LAN_ENGINE = "http://192.168.1.43:8080/v1"


def _lan_engine_model() -> str | None:
    """The model the owner's LAN llama.cpp serves, or None when unreachable.

    The rehearsal ran on that box. A sandboxed or CI runner cannot see the
    LAN at all, so this answers None there and the walk uses the controlled
    stub instead — and either way the run PRINTS which engine served it.
    """
    import json as _json
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen("http://192.168.1.43:8080/health", timeout=3) as r:
            if r.status != 200:
                return None
        with urllib.request.urlopen(f"{LAN_ENGINE}/models", timeout=5) as r:
            payload = _json.loads(r.read().decode())
    except (urllib.error.URLError, OSError, ValueError):
        return None
    rows = payload.get("data") or []
    return str(rows[0].get("id")) if rows else None


@pytest.mark.parametrize("engine_kind", ["stub", "lan"])
def test_import_asks_for_no_summary_and_the_gesture_runs_the_frozen_producer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, engine_kind: str,
) -> None:
    """HS-201-10 — the same producer chain, entered through Import.

    The rehearsal's defect 2: `_persist_import` enqueued a job with only a
    transcript hash, so the producer ran with no disclosed route and no
    receipt. Here the REAL import runs with a summary engine already
    selected, and the chain stays cold until the owner's gesture — which
    carries the disclosed selection hash and leaves a receipt naming the
    host that was contacted.
    """
    from datetime import datetime, timedelta
    from types import SimpleNamespace

    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.meeting_import import import_meeting
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.meeting_intel_service import MeetingIntelService
    from tests.unit.test_meeting_deferred_admission import FakeHost, FakeIntel, _Route

    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "core_path_smoke_16k.wav"
    lan_model = _lan_engine_model() if engine_kind == "lan" else None
    if engine_kind == "lan" and lan_model is None:
        pytest.skip(
            "the owner's LAN engine at 192.168.1.43:8080 is not reachable from "
            "this runner; the `stub` leg proves the same chain"
        )
    if engine_kind == "stub":
        monkeypatch.setattr(
            "holdspeak.setup_runtime.discover_endpoint_models",
            lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
        )
    library = _library(tmp_path, store_path=tmp_path / "import-keys.json")
    db = library._db
    endpoint_draft = (
        _draft(
            request_id="import-producer",
            profile_id="import-producer",
            provider_family="openai_compatible",
            requires_key=False,
        )
        if engine_kind == "stub"
        else _draft(
            request_id="import-producer-lan",
            profile_id="import-producer-lan",
            provider_family="openai_compatible",
            label="LAN llama.cpp",
            model=lan_model or "",
            endpoint=LAN_ENGINE,
            requires_key=False,
        )
    )
    print(f"ENGINE {engine_kind} endpoint={endpoint_draft.get('endpoint')} "
          f"model={endpoint_draft.get('model')}")
    producer = library.define_endpoint(OWNER, endpoint_draft, None)
    client = _client(db, tmp_path / "home")
    selection = client.post(
        "/api/concierge/summary-selection",
        json={
            "commandId": f"import-producer-summary-{engine_kind}",
            "expectedAssignmentRevision": 0,
            "profileId": producer["provider"]["profile_id"],
            "profileRevision": producer["provider"]["profile_revision"],
        },
    )
    assert selection.status_code == 200, selection.text
    assert selection.json()["status"] == "succeeded"

    monkeypatch.setattr("holdspeak.db.get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr(
        "holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: FakeHost(())
    )
    monkeypatch.setattr(
        "holdspeak.plugins.router.preview_route_from_transcript", lambda **kw: _Route(())
    )
    broker = _configure(db)
    assert broker is not None

    # An engine IS selected for summaries, and the audio is real. The only
    # stand-in is the transcriber (no Whisper in a rig) and the provider
    # object, which is watched: any use of it is a contact.
    # The `stub` leg watches a controlled provider object; the `lan` leg
    # leaves the REAL provider stack alone, so the frozen route dispatches
    # to the owner's own llama.cpp and the receipt names it.
    engine = FakeIntel()
    if engine_kind == "stub":
        monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kw: engine)
        monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)

    source = tmp_path / "core_path_smoke_16k.wav"
    source.write_bytes(fixture.read_bytes())
    old = (datetime.now() - timedelta(days=108)).timestamp()
    os.utime(source, (old, old))

    class _Transcriber:
        def transcribe(self, audio, **_admission):
            return "The quick brown fox jumps over the lazy dog."

    imported = import_meeting(
        source,
        db=db,
        transcriber=_Transcriber(),
        config=SimpleNamespace(
            meeting=SimpleNamespace(intel_enabled=True, intel_deferred_enabled=True)
        ),
        title="Imported standup",
    )
    meeting_id = imported.state.id

    # ── cold: nothing queued, nothing drained, nobody contacted ──
    assert imported.intel_job_enqueued is False
    assert db.intel.list_intel_jobs() == []
    assert db.intel.get_latest_intel_job(meeting_id) is None
    assert process_next_intel_job(retry_max_attempts=1) is False
    if engine_kind == "stub":
        assert engine.analyzed == []
    assert db.intel.get_run_receipt(meeting_id) is None
    with db._connection() as conn:
        attempts = conn.execute(
            "SELECT COUNT(*) AS n FROM inference_route_attempts"
        ).fetchone()
    assert attempts["n"] == 0, dict(attempts)
    # …and the import is dated now, with a final transcript.
    saved = db.meetings.get_meeting(meeting_id)
    assert saved.started_at > datetime.now() - timedelta(minutes=10)
    assert saved.transcription_status == "complete"

    # ── the gesture: the disclosed selection, and only then a provider ──
    route = project_route(db, invocation_id=f"meeting:{meeting_id}")
    assert route["status"] == "ready", route
    MeetingIntelService(db).run_intelligence(
        Principal(PrincipalKind.OWNER, "hs201-owner"),
        meeting_id,
        expected_selection_hash=route["selection_hash"],
    )
    assert process_next_intel_job(retry_max_attempts=1) is True
    if engine_kind == "stub":
        assert engine.analyzed, "the gesture never reached the producer"

    receipt = db.intel.get_run_receipt(meeting_id)
    assert receipt is not None
    assert receipt["outcome"] == "succeeded", receipt
    assert receipt["selection_hash"] == route["selection_hash"], receipt
    assert receipt["attempts"], receipt
    assert receipt["attempts"][0]["host"] == route["legs"][0]["host"], receipt
    produced = db.meetings.get_meeting(meeting_id)
    assert produced.intel is not None
    if engine_kind == "stub":
        assert produced.intel.summary == engine.result.summary
    else:
        # A real model wrote this. The words are its own; what this rig
        # asserts is that they exist and that the receipt names the host
        # the face disclosed BEFORE the click.
        assert produced.intel.summary.strip(), produced.intel
        assert receipt["attempts"][0]["host"] == "192.168.1.43", receipt
        print(f"LAN SUMMARY {produced.intel.summary!r}")
        print(f"LAN RECEIPT {receipt}")
