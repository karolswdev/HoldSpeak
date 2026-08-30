"""HS-131-08 Part B: the stop handoff and the admitted deferred queue job.

Sol Amendment 2 is the spine of this file: ``stop()`` CANCELS the live
``meeting.session`` parent and then durably enqueues the work it displaced —
final analysis, bookmark labels, auto-title, routed plugins — before it returns,
and the meeting never reports readiness while that job is outstanding.

Each claimed queue job then admits ONE short-lived
``meeting.deferred-intel-job`` parent under the narrow queue-worker service
principal, over a freshly frozen plan; the base analysis and every executed
routed plugin are trusted ``inference.invoke@1`` children of it, and every
durable plugin/artifact write is gated on the winning child receipt.

Only the provider engine and the plugin registry are faked; the plan, the
parents, the runner, the projections, the materializer, and the receipts are all
production code.
"""

from __future__ import annotations

import json
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import pytest

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.intel import ActionItem, IntelResult
from holdspeak.kernel.runtime import _configure
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.meeting_session.deferred_bound import PARENT_KIND, QUEUE_SERVICE_IDENTITY
from holdspeak.services.meeting_deferred_queue_binding import JOB_DEADLINE_SECONDS
from holdspeak.meeting_session.intel_plan import (
    MeetingIntelRefused,
    SESSION_CLOSED,
)
from holdspeak.meeting_session.models import Bookmark
from holdspeak.plugins.host import PluginRunResult, build_idempotency_key
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_fallback_controller import INFERENCE_FALLBACK_AUTHORITY
from holdspeak.services.inference_parent_route_bundle_service import InferenceParentRouteBundleService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
from tests.unit.test_phase143_inference_fallback_controller import _broker_child

pytestmark = pytest.mark.timeout(90, method="signal")

OWNER = Principal(PrincipalKind.OWNER, "meeting-owner")
SENTINEL = "PINEAPPLEQUARTERLYSECRET"


# --------------------------------------------------------------------- fakes


class FakeIntel:
    """The one faked seam: the engine the admitted deployment revision builds."""

    active_provider = "test-provider"
    active_model = "test-model"

    def __init__(self) -> None:
        self.analyzed: list[str] = []
        self.titles: list[str] = []
        self.labels: list[dict[str, str]] = []
        self.completions: list[dict[str, Any]] = []
        self.stream_gate: threading.Event | None = None
        self.entered = threading.Event()
        self.error: str | None = None
        self.result = IntelResult(
            topics=["Budget"],
            action_items=[ActionItem(task="Send the deck", owner="Me")],
            summary="The team reviewed the budget.",
            raw_response="{}",
        )

    def _result(self) -> IntelResult:
        if self.error is None:
            return self.result
        return IntelResult(topics=[], action_items=[], summary="", raw_response="", error=self.error)

    def analyze(self, transcript: str, *, stream: bool = False) -> Any:
        self.analyzed.append(transcript)
        if not stream:
            return self._result()

        def generate() -> Iterator[Any]:
            self.entered.set()
            if self.stream_gate is not None:
                # A window that never comes back on its own: stop() must cancel it.
                self.stream_gate.wait(30.0)
            yield '{"topics":'
            yield self._result()

        return generate()

    def generate_bookmark_label_with_context(self, *, local_context: str, meeting_summary: str) -> str:
        self.labels.append({"context": local_context, "summary": meeting_summary})
        return "Budget decision"

    def generate_title(self, transcript: str) -> str:
        self.titles.append(transcript)
        return "Quarterly budget review"

    def _chat_completion_text(self, messages: Any, *, temperature: float, max_tokens: int) -> str:
        """The seam a routed plugin's admitted handle dispatches on (HS-131-14)."""
        self.completions.append({"messages": messages, "max_tokens": max_tokens})
        return "{}"


class FakeHost:
    """The plugin registry seam: declares capabilities and executes the chain."""

    def __init__(self, plugins: tuple[str, ...]) -> None:
        self._plugins = list(plugins)
        self.executed: list[str] = []
        self.dispatches: list[Any] = []
        self.on_execute: Any = None
        # The engines the admitted path issued a handle over, in order.
        self.bound_engines: list[Any] = []
        # Every handle this host issued, and whether it was released on exit.
        self.issued: list[Any] = []

    def list_plugins(self) -> list[str]:
        return list(self._plugins)

    def get_plugin(self, plugin_id: str) -> Any:
        if plugin_id not in self._plugins:
            return None
        from holdspeak.inference_capabilities import process_inference_capability_registry

        version = process_inference_capability_registry().require(
            f"meeting.plugin.{plugin_id}"
        ).plugin_definition_revision
        return type("FrozenFakePlugin", (), {"id": plugin_id, "version": version})()

    @contextmanager
    def issued_dispatch(self, engine: Any, cancellation: Any = None) -> Any:
        """The admitted seam: ONE handle per plugin child, released on exit.

        HS-131-14 — the host holds no engine and no handle between runs; the
        handle is issued over the admitted child's engine + cancellation signal
        and travels into exactly the invocation it authorizes.
        """
        from holdspeak.plugins.intelligence import _issue_plugin_dispatch

        self.bound_engines.append(engine)
        handle = _issue_plugin_dispatch(engine=engine, cancellation=cancellation)
        self.issued.append(handle)
        try:
            yield handle
        finally:
            handle.release()

    def execute_chain(
        self,
        chain: list[str],
        *,
        context: dict[str, Any],
        meeting_id: str,
        window_id: str,
        transcript_hash: str,
        timeout_seconds: float | None = None,
        defer_heavy: bool = True,
        dispatch: Any = None,
    ) -> list[PluginRunResult]:
        self.dispatches.append(dispatch)
        results: list[PluginRunResult] = []
        for plugin_id in chain:
            self.executed.append(plugin_id)
            if self.on_execute is not None:
                self.on_execute(plugin_id)
            results.append(PluginRunResult(
                plugin_id=plugin_id,
                plugin_version=str(self.get_plugin(plugin_id).version),
                status="success",
                idempotency_key=build_idempotency_key(
                    meeting_id=meeting_id, window_id=window_id,
                    plugin_id=plugin_id, transcript_hash=transcript_hash,
                ),
                duration_ms=3.0,
                output={
                    "summary": f"{plugin_id} said something",
                    "confidence_hint": 0.9,
                    "active_intents": [],
                },
            ))
        return results


class _Cfg:
    class meeting:  # noqa: N801 - config shape
        intent_router_enabled = True
        routing_profile = "balanced"


class _Route:
    def __init__(self, chain: tuple[str, ...]) -> None:
        self._chain = list(chain)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": "balanced",
            "threshold": 0.5,
            "active_intents": ["architecture"],
            "intent_scores": {"architecture": 0.9},
            "plugin_chain": list(self._chain),
        }


# ----------------------------------------------------------------------- rigs


def _assign_deferred_queue_routes(db: Database) -> None:
    """Give the SERVICE queue its exact saved assignments, never ambient fallback."""
    from holdspeak.inference_capabilities import process_inference_capability_registry

    capabilities = (
        "meeting.deferred_analysis",
        "meeting.bookmark_label",
        "meeting.auto_title",
        *(
            capability_id
            for capability_id in process_inference_capability_registry().capability_ids
            if capability_id.startswith("meeting.plugin.")
        ),
    )
    _profile(
        db,
        "deferred-queue-model",
        claims=("language", "structured_output", "meeting_plugin", *(_result_claim(item) for item in capabilities)),
        modalities=("language", "text"),
    )
    assignments = InferenceAssignmentService(db)
    for ordinal, capability in enumerate(capabilities, 1):
        assignments.set_assignment(
            OWNER,
            {
                "command_id": f"deferred-queue-assignment-{ordinal}",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": capability},
                "entries": [{"profile_id": "deferred-queue-model", "profile_revision": 1}],
            },
        )


def _observe(broker: Any, monkeypatch) -> list[Any]:
    requests: list[Any] = []
    real_invoke = broker.inference_runner.invoke

    def observed(request, *args, **kwargs):
        requests.append(request)
        return real_invoke(request, *args, **kwargs)

    monkeypatch.setattr(broker.inference_runner, "invoke", observed)
    return requests


def _session_rig(tmp_path: Path, monkeypatch, *, engine: Any = None):
    """A real database + broker + MeetingSession with a fake provider."""
    db = Database(tmp_path / "meeting.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *a, **k: db)
    broker = _configure(db)
    engine = engine if engine is not None else FakeIntel()

    # HS-131-13: the pinned `this_machine` branch builds `MeetingIntel` from the
    # FROZEN revision, so the double goes on the engine class the real path ends at.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.meeting_session.session.MeetingRecorder", _FakeRecorder)
    monkeypatch.setattr("holdspeak.meeting_capture_journal.MeetingCaptureJournal", _FakeJournal)
    # HS-131-17: the session imports no engine class and runs no provider
    # preflight. Live readiness is read off the FROZEN placement, so the honest
    # way to make the `this_machine` leg reachable is to give it a model file.
    model = tmp_path / "local-meeting-intel.gguf"
    model.write_bytes(b"gguf")
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path", lambda: str(model)
    )
    requests = _observe(broker, monkeypatch)

    from holdspeak.meeting_session import MeetingSession

    class _Transcriber:
        model_name = "test-model"

        def transcribe(self, *args: Any, **kwargs: Any) -> str:
            return ""

    session = MeetingSession(
        _Transcriber(),  # type: ignore[arg-type]
        intel_enabled=True,
        intel_deferred_enabled=True,
        principal=OWNER,
    )
    return db, broker, session, engine, requests


def _queue_rig(tmp_path: Path, monkeypatch, *, plugins: tuple[str, ...] = (), chain: tuple[str, ...] = ()):
    """A real database + broker + a queued meeting, with the queue's seams faked."""
    db = Database(tmp_path / "queue.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *a, **k: db)
    _assign_deferred_queue_routes(db)
    broker = _configure(db)
    engine = FakeIntel()
    host = FakeHost(plugins)

    # HS-131-13: same reason as `_session_rig` — the frozen-revision local branch
    # constructs the engine class directly and reads no configured default.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: host)
    monkeypatch.setattr(
        "holdspeak.plugins.router.preview_route_from_transcript",
        lambda **kwargs: _Route(chain),
    )
    requests = _observe(broker, monkeypatch)
    return db, broker, engine, host, requests


class _FakeRecorder:
    def __init__(self, **kwargs: Any) -> None:
        self.started = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> tuple[list[Any], list[Any]]:
        return [], []

    def get_pending_chunks(self, since: float = 0.0) -> tuple[list[Any], list[Any]]:
        return [], []

    def get_pending_device_chunks(self) -> list[Any]:
        return []


class _FakeJournal:
    def __init__(self, meeting_id: str) -> None:
        self.meeting_id = meeting_id

    def append(self, *args: Any, **kwargs: Any) -> None:
        return None

    def finalize(self) -> None:
        return None

    def mark_recoverable(self, reason: str) -> None:
        return None


def _queued_meeting(
    db: Database,
    meeting_id: str,
    *,
    text: str = "we shipped the fix",
    title: str = "Deferred meeting",
    bookmarks: tuple[float, ...] = (),
    displaced_work: tuple[str, ...] = (),
    legacy_claimed: bool = False,
    legacy_stop_handoff: bool = False,
) -> MeetingState:
    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 10, 9, 0, 0),
        ended_at=datetime(2026, 8, 10, 9, 30, 0),
        title=title,
        tags=["architecture"],
        segments=[TranscriptSegment(text=text, speaker="Me", start_time=0.0, end_time=5.0)],
        bookmarks=[Bookmark(timestamp=stamp, label="Bookmark") for stamp in bookmarks],
    )
    db.meetings.save_meeting(state)
    db.intel.enqueue_intel_job(
        meeting_id,
        transcript_hash=state.transcript_hash(),
        reason="stop handoff",
        displaced_work=displaced_work,
        legacy_displaced_work=legacy_stop_handoff,
    )
    # This fixture can model a process loss after the historical Meeting-keyed
    # claim. C1c keeps that owner on its legacy executor; only a C1b bound claim
    # is eligible for the new stored-ID worker.
    if legacy_claimed:
        assert db.intel.claim_next_intel_job() is not None
    return state


def _parents(db: Database, kind: str = "") -> list[dict[str, Any]]:
    query = "SELECT * FROM kernel_parent_runs"
    parameters: tuple[Any, ...] = ()
    if kind:
        query += " WHERE kind=?"
        parameters = (kind,)
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(query + " ORDER BY created_at", parameters)]


def _children(db: Database, parent_operation_id: str) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM kernel_operations WHERE parent_operation_id=? AND name='inference.invoke' ORDER BY created_at",
            (parent_operation_id,),
        )]


def _rows(db: Database, table: str) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(f"SELECT * FROM {table}")]


def _add_segment(session: Any, text: str, start: float) -> None:
    session._state.segments.append(
        TranscriptSegment(text=text, speaker="Me", start_time=start, end_time=start + 5.0)
    )


# ------------------------------------------------- Amendment 2: the stop handoff






def test_a_closed_live_session_is_never_revived(tmp_path, monkeypatch):
    _db, _broker, session, engine, requests = _session_rig(tmp_path, monkeypatch)
    session.start()
    _add_segment(session, "Something worth summarizing", 0.0)
    session.stop()
    before = len(requests)

    with pytest.raises(MeetingIntelRefused) as refusal:
        session._admitted_auto_title("Anything at all")
    assert refusal.value.reason == SESSION_CLOSED
    assert engine.titles == []
    assert len(requests) == before


# --------------------------------------------- the admitted deferred queue job


def _saved_stop_meeting(db: Database, meeting_id: str) -> MeetingState:
    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 10, 9, 0, 0),
        ended_at=datetime(2026, 8, 10, 9, 30, 0),
        title="Deferred meeting",
        segments=[TranscriptSegment(
            text="we shipped the fix", speaker="Me", start_time=0.0, end_time=5.0,
        )],
    )
    db.meetings.save_meeting(state)
    return state


def _live_stop_bundle(
    broker: Any,
    state: MeetingState,
    provider: Any,
    *,
    route_specs: tuple[dict[str, str], ...] | None = None,
):
    bundles = InferenceParentRouteBundleService(
        broker,
        broker.inference_adoption_service,
        handoff_evidence_providers=(provider,),
    )
    started = bundles.start(
        OWNER,
        command_id=f"c3-live-bundle:{state.id}",
        parent_kind="meeting.session",
        definition_ref=f"meeting:{state.id}:intel",
        definition_revision="c3-test",
        input_snapshot={"meeting_id": state.id},
        deadline_at=2_000_000_000.0,
        routes=route_specs or ({
            "key": "deferred-analysis",
            "capability_id": "meeting.deferred_analysis",
            "invocation_id": state.id,
        },),
    )
    return bundles, started


def test_stop_handoff_post_commit_cancels_do_not_serially_delay_stop(tmp_path, monkeypatch):
    """Four slow provider cancels cannot hold the already-fenced Stop response."""
    db, broker, _engine, _host, _requests = _queue_rig(
        tmp_path,
        monkeypatch,
        plugins=("requirements_extractor",),
        chain=("requirements_extractor",),
    )
    state = _saved_stop_meeting(db, "m-c3-stop-latency")
    provider = db.intel.stop_handoff_provider(
        meeting_id=state.id,
        transcript_hash=state.transcript_hash(),
        displaced_work=("final-analysis",),
        reason="stop_handoff",
    )
    route_specs = (
        {"key": "analysis", "capability_id": "meeting.deferred_analysis", "invocation_id": state.id},
        {"key": "bookmark", "capability_id": "meeting.bookmark_label", "invocation_id": state.id},
        {"key": "title", "capability_id": "meeting.auto_title", "invocation_id": state.id},
        {"key": "plugin", "capability_id": "meeting.plugin.requirements_extractor", "invocation_id": state.id},
    )
    bundles, started = _live_stop_bundle(
        broker, state, provider, route_specs=route_specs,
    )
    controller = broker.inference_adoption_service.controller
    for member in started["bundle"]["members"]:
        capability = member["capability_id"]
        admitted = broker.inference_adoption_service.admit_on_frozen_route(
            OWNER,
            command_id=f"c3-latency-admit:{member['key']}",
            route_plan_id=member["route_plan_id"],
            capability_id=capability,
            operation_id=f"c3-latency-operation:{member['key']}",
            payload={"transcript": "we shipped the fix"},
            reserved_output_tokens=16,
        )
        reservation = controller.reserve_next_attempt(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"c3-latency-reserve:{member['key']}",
            execution_id=admitted["execution"]["id"],
        )["reservation"]
        controller.claim_reservation(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"claim-{reservation['attempt_id']}",
            reservation=reservation,
        )
        child_id = _broker_child(broker, reservation, suffix=f"c3-latency-{member['key']}")
        controller.bind_admitted_child(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"bind-{reservation['attempt_id']}",
            attempt_id=reservation["attempt_id"],
            child_operation_id=child_id,
        )
        controller.mark_dispatch_intent(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"dispatch-{reservation['attempt_id']}",
            attempt_id=reservation["attempt_id"],
        )

    completed: list[str] = []
    all_cancelled = threading.Event()

    def slow_cancel(invocation_id: str) -> str:
        time.sleep(0.2)
        completed.append(invocation_id)
        if len(completed) == 4:
            all_cancelled.set()
        return "delayed"

    monkeypatch.setattr(broker.inference_runner, "cancel", slow_cancel)
    began = time.monotonic()
    effect = bundles.request_stop_handoff(
        OWNER,
        command_id=f"meeting-stop:{state.id}",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id=provider.id,
        planning_reference=db.intel.stop_handoff_planning_reference(state.id),
    )
    elapsed = time.monotonic() - began

    assert effect["state"] == "pending_physical_settlement"
    # Serial cancellation would be roughly 800ms; the Stop response is only the
    # durable fence/reservation transaction and stays below the hero-action bar.
    assert elapsed < 0.5
    assert all_cancelled.wait(timeout=2.0)
    assert len(completed) == 4


def test_stop_provider_known_settlement_activates_normal_bound_queue_claim(tmp_path, monkeypatch):
    """C3 activates the production reservation only into C1's ordinary claim."""
    db, broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    state = _saved_stop_meeting(db, "m-c3-known")
    provider = db.intel.stop_handoff_provider(
        meeting_id=state.id,
        transcript_hash=state.transcript_hash(),
        displaced_work=("final-analysis",),
        reason="stop_handoff",
    )
    bundles, started = _live_stop_bundle(broker, state, provider)

    effect = bundles.request_stop_handoff(
        OWNER,
        command_id=f"meeting-stop:{state.id}",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id=provider.id,
        planning_reference=db.intel.stop_handoff_planning_reference(state.id),
    )
    assert effect["state"] == "committed"
    with db._connection() as conn:
        reserved = conn.execute(
            "SELECT status,lifecycle_posture FROM intel_jobs WHERE job_id=?",
            (effect["evidence_ref"],),
        ).fetchone()
        events = conn.execute(
            "SELECT event_kind,outcome FROM intel_job_attempts WHERE job_id=? ORDER BY id",
            (effect["evidence_ref"],),
        ).fetchall()
    assert reserved is not None and tuple(reserved) == ("queued", "queued")
    assert [tuple(event) for event in events] == [
        ("handoff_reserved", "reserved"), ("handoff_activated", "activated"),
    ]

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    assert engine.analyzed and requests
    with db._connection() as conn:
        # The activated evidence row entered the real C1/C2 descriptor and bundle
        # claim machinery; this is not a direct provider execution route.
        claim = conn.execute(
            """SELECT parent_operation_id,bundle_id,event_kind FROM intel_job_attempts
                 WHERE meeting_id=? AND event_kind='claim'""",
            (state.id,),
        ).fetchone()
    assert claim is not None and claim["parent_operation_id"] and claim["bundle_id"]


def test_settled_stop_handoff_skipped_by_owner_never_unknown_recovers(tmp_path, monkeypatch):
    """A valid post-settlement Skip remains terminal queue truth."""
    db, broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _saved_stop_meeting(db, "m-c3-settled-skip")
    provider = db.intel.stop_handoff_provider(
        meeting_id=state.id,
        transcript_hash=state.transcript_hash(),
        displaced_work=("final-analysis",),
        reason="stop_handoff",
    )
    bundles, started = _live_stop_bundle(broker, state, provider)
    effect = bundles.request_stop_handoff(
        OWNER,
        command_id=f"meeting-stop:{state.id}",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id=provider.id,
        planning_reference=db.intel.stop_handoff_planning_reference(state.id),
    )
    assert effect["state"] == "committed"
    assert db.intel.skip_remaining_intel(state.id) == "skipped"
    assert db.intel.admit_unknown_stop_handoff_recoveries() == 0
    with db._connection() as conn:
        skipped = conn.execute(
            "SELECT status,lifecycle_posture FROM intel_jobs WHERE job_id=?",
            (effect["evidence_ref"],),
        ).fetchone()
        descendants = conn.execute(
            "SELECT COUNT(*) FROM intel_jobs WHERE origin_job_id=?",
            (effect["evidence_ref"],),
        ).fetchone()[0]
    assert skipped is not None and tuple(skipped) == ("skipped", "terminal")
    assert descendants == 0


def test_stop_provider_unknown_dispatch_keeps_reservation_and_fresh_admits(tmp_path, monkeypatch):
    """Unknown physical disposition never activates the old job, even on restart."""
    db, broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    state = _saved_stop_meeting(db, "m-c3-unknown")
    provider = db.intel.stop_handoff_provider(
        meeting_id=state.id,
        transcript_hash=state.transcript_hash(),
        displaced_work=("final-analysis",),
        reason="stop_handoff",
    )
    bundles, started = _live_stop_bundle(broker, state, provider)
    route = started["bundle"]["members"][0]
    admitted = broker.inference_adoption_service.admit_on_frozen_route(
        OWNER,
        command_id=f"c3-live-child:{state.id}",
        route_plan_id=route["route_plan_id"],
        capability_id="meeting.deferred_analysis",
        operation_id=f"c3-live-child-operation:{state.id}",
        payload={"transcript": "we shipped the fix"},
        reserved_output_tokens=16,
    )
    controller = broker.inference_adoption_service.controller
    reservation = controller.reserve_next_attempt(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"c3-live-reserve:{state.id}",
        execution_id=admitted["execution"]["id"],
    )["reservation"]
    controller.claim_reservation(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"claim-{reservation['attempt_id']}",
        reservation=reservation,
    )
    child_id = _broker_child(broker, reservation, suffix="c3-unknown")
    controller.bind_admitted_child(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"bind-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
        child_operation_id=child_id,
    )
    controller.mark_dispatch_intent(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"dispatch-{reservation['attempt_id']}",
        attempt_id=reservation["attempt_id"],
    )
    effect = bundles.request_stop_handoff(
        OWNER,
        command_id=f"meeting-stop:{state.id}",
        bundle_id=started["bundle"]["id"],
        evidence_provider_id=provider.id,
        planning_reference=db.intel.stop_handoff_planning_reference(state.id),
    )
    assert effect["state"] == "pending_physical_settlement"

    # A provider-owned reserve is not ordinary queue work: neither generic
    # recovery verb may rewrite it while the live route can still egress, and the
    # existing recovery glass must not advertise those verbs.
    from holdspeak.services.meeting_intel_service import MeetingIntelService

    recovery_service = MeetingIntelService(db)
    recovery_before_settlement = recovery_service.get_recovery(None, state.id)
    assert recovery_before_settlement["actions"] == {"retry": False, "skip": False}
    assert db.intel.request_intel_retry(state.id) == "reserved"
    assert db.intel.skip_remaining_intel(state.id) == "reserved"
    from holdspeak.services.errors import ConflictError

    with pytest.raises(ConflictError, match="awaiting Stop settlement") as retry_refused:
        recovery_service.retry_recovery(OWNER, state.id)
    with pytest.raises(ConflictError, match="awaiting Stop settlement") as skip_refused:
        recovery_service.skip_recovery(OWNER, state.id)
    assert retry_refused.value.code == skip_refused.value.code == "reserved"
    with db._connection() as conn:
        reserved = conn.execute(
            "SELECT status,lifecycle_posture FROM intel_jobs WHERE job_id=?",
            (effect["evidence_ref"],),
        ).fetchone()
        assert reserved is not None and tuple(reserved) == ("reserved", "reserved")
        assert conn.execute(
            "SELECT COUNT(*) FROM intel_jobs WHERE origin_job_id=?",
            (effect["evidence_ref"],),
        ).fetchone()[0] == 0

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is False
    assert requests == []

    controller.reconcile_dispatch_intent(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id=f"c3-live-reconcile:{state.id}",
        attempt_id=reservation["attempt_id"],
    )

    from holdspeak.intel_queue import process_next_intel_job

    # Fresh service construction at the ordinary queue boundary observes the
    # durable terminal, leaves the original reserve inert, and writes both
    # sides of the unknown-recovery ledger before any fresh egress is possible.
    assert process_next_intel_job() is True
    with db._connection() as conn:
        old = conn.execute(
            "SELECT status,lifecycle_posture FROM intel_jobs WHERE job_id=?",
            (effect["evidence_ref"],),
        ).fetchone()
        fresh = conn.execute(
            """SELECT job_id,origin_job_id,status,displaced_work FROM intel_jobs
                 WHERE origin_job_id=?""",
            (effect["evidence_ref"],),
        ).fetchone()
        ledger = conn.execute(
            """SELECT job_id,origin_job_id,event_kind,outcome FROM intel_job_attempts
                 WHERE meeting_id=? AND event_kind IN
                     ('handoff_outcome_unknown','handoff_unknown_recovery')
                 ORDER BY id""",
            (state.id,),
        ).fetchall()
    assert old is not None and tuple(old) == ("reserved", "reserved")
    assert fresh is not None and fresh["status"] == "queued"
    assert json.loads(fresh["displaced_work"])["recovery_origin_job_id"] == effect["evidence_ref"]
    assert [tuple(event) for event in ledger] == [
        (effect["evidence_ref"], None, "handoff_outcome_unknown", "reserved"),
        (fresh["job_id"], effect["evidence_ref"], "handoff_unknown_recovery", "queued"),
    ]
    assert requests == []

    # A second worker turn performs the normal C1 claim and bound execution only
    # for the fresh lineage leaf; restart/reconcile cannot double-activate it.
    assert process_next_intel_job() is True
    assert engine.analyzed and len(requests) == 1
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM intel_job_attempts WHERE job_id=? AND event_kind='handoff_activated'",
            (effect["evidence_ref"],),
        ).fetchone()[0] == 0


def test_bound_claim_executes_stored_service_member_and_completes_ledger(tmp_path, monkeypatch):
    """C1c never calls the legacy admission path for a C1b-bound claim."""
    db, _broker, _engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-bound-worker", legacy_claimed=False)
    from holdspeak.intel_queue import process_next_intel_job
    assert process_next_intel_job() is True
    job = db.intel.get_intel_job(state.id)
    assert job is None
    saved = db.meetings.get_meeting(state.id)
    assert saved is not None and saved.intel is not None
    with db._connection() as conn:
        event = conn.execute(
            "SELECT outcome FROM intel_job_attempts WHERE meeting_id=? AND event_kind='completion'",
            (state.id,),
        ).fetchone()
        bound = conn.execute(
            "SELECT parent_operation_id,bundle_id FROM intel_jobs WHERE meeting_id=?",
            (state.id,),
        ).fetchone()
    assert event is not None and event["outcome"] == "succeeded"
    assert bound is not None and bound["parent_operation_id"] and bound["bundle_id"]
    assert requests


def test_pre_c_unbound_claim_is_cut_over_inert_and_only_a_fresh_descriptor_can_bind(tmp_path, monkeypatch):
    """A restart/HTTP drain fences an unknown v1 owner before any egress."""
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder
    from holdspeak.services.meeting_intel_service import MeetingIntelService

    db, broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-pre-c-cutover", legacy_claimed=True)
    with db._connection() as conn:
        old = dict(conn.execute(
            "SELECT job_id,origin_job_id,displaced_work,attempts,claim_id FROM intel_jobs WHERE meeting_id=?",
            (state.id,),
        ).fetchone())

    # The normal process route performs the one transactional compatibility fence.
    assert process_next_intel_job() is True
    other = Database(db.db_path)
    assert other.intel.cut_over_legacy_unbound_intel_jobs() == 0
    assert process_next_intel_job() is False
    assert engine.analyzed == [] and requests == []
    with db._connection() as conn:
        fenced = dict(conn.execute(
            "SELECT job_id,origin_job_id,displaced_work,attempts,claim_id,status,lifecycle_posture,last_error FROM intel_jobs WHERE job_id=?",
            (old["job_id"],),
        ).fetchone())
        event = dict(conn.execute(
            "SELECT event_kind,outcome,error FROM intel_job_attempts WHERE job_id=? ORDER BY created_at DESC LIMIT 1",
            (old["job_id"],),
        ).fetchone())
    for field in ("job_id", "origin_job_id", "displaced_work", "attempts", "claim_id"):
        assert fenced[field] == old[field]
    assert fenced["status"] == "inert"
    assert fenced["lifecycle_posture"] == "compatibility_cutover"
    assert event == {
        "event_kind": "compatibility_cutover",
        "outcome": "inert",
        "error": "pre_c_unbound_execution_compatibility_cutover",
    }

    # Actual recovery-glass paths have no Retry/Skip side door and do not advertise one.
    service = MeetingIntelService(db)
    assert db.intel.request_intel_retry(state.id) == "reserved"
    assert db.intel.skip_remaining_intel(state.id) == "reserved"
    recovery = service.get_recovery(OWNER, state.id)
    assert recovery["actions"] == {"retry": False, "skip": False}

    # Explicit recovery mints a distinct descriptor. It reaches only the ordinary
    # binder (current assignment/policy) and never turns the inert source claimable.
    fresh_id = db.intel.admit_compatibility_cutover_recovery(str(old["job_id"]))
    assert fresh_id
    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claimed is not None and claimed.parent_operation_id and claimed.bundle_id
    with db._connection() as conn:
        fresh = conn.execute(
            "SELECT origin_job_id,status FROM intel_jobs WHERE job_id=?", (fresh_id,)
        ).fetchone()
        old_status = conn.execute(
            "SELECT status,lifecycle_posture FROM intel_jobs WHERE job_id=?", (old["job_id"],)
        ).fetchone()
    assert fresh is not None and fresh["origin_job_id"] == old["job_id"]
    assert old_status is not None and tuple(old_status) == ("inert", "compatibility_cutover")
    assert engine.analyzed == [] and requests == []


def test_bound_claim_replaces_legacy_stop_handoff_with_frozen_descriptor(tmp_path, monkeypatch):
    """C2 adds immutable installed-plugin authority to C1's frozen handoff."""
    db, _broker, _engine, _host, _requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor",), chain=("requirements_extractor",),
    )
    state = _queued_meeting(
        db,
        "m-bound-legacy-stop",
        bookmarks=(0.25, 0.5),
        displaced_work=("bookmark-labels",),
        legacy_claimed=False,
        legacy_stop_handoff=True,
    )
    from holdspeak.intel_queue import process_next_intel_job

    with db._connection() as conn:
        original = conn.execute(
            "SELECT job_id,displaced_work,status FROM intel_jobs WHERE meeting_id=?",
            (state.id,),
        ).fetchone()
    assert original is not None
    assert original["status"] == "queued"
    assert original["displaced_work"] == '["bookmark-labels"]'

    assert process_next_intel_job() is True

    with db._connection() as conn:
        rows = conn.execute(
            """SELECT job_id,origin_job_id,status,displaced_work,parent_operation_id
               FROM intel_jobs WHERE meeting_id=? ORDER BY requested_at,job_id""",
            (state.id,),
        ).fetchall()
    assert len(rows) == 3
    by_id = {row["job_id"]: row for row in rows}
    legacy = by_id[original["job_id"]]
    c1 = next(row for row in rows if row["origin_job_id"] == legacy["job_id"])
    c2 = next(row for row in rows if row["origin_job_id"] == c1["job_id"])
    assert legacy["status"] == "superseded"
    assert c1["status"] == "superseded"
    assert c2["parent_operation_id"]
    descriptor = json.loads(c2["displaced_work"])
    assert descriptor["bookmark_operations"] == [
        {"id": 1, "timestamp": 0.25}, {"id": 2, "timestamp": 0.5},
    ]
    assert descriptor["plugin_members"]
    assert all(member["capability_id"].startswith("meeting.plugin.") for member in descriptor["plugin_members"])


def test_stop_and_recovery_replays_preserve_v3_handoff_leaf(tmp_path, monkeypatch):
    """Legacy Stop/recovery descriptors cannot reopen their V3 descendant."""
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    db, broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(
        db, "m-v3-handoff-replay", bookmarks=(0.5,),
        displaced_work=("bookmark-labels",), legacy_claimed=False,
        legacy_stop_handoff=True,
    )
    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claimed is not None and claimed.parent_operation_id

    def replay(reason: str) -> str:
        return db.intel.enqueue_intel_job(
            state.id,
            transcript_hash=state.transcript_hash(),
            reason=reason,
            displaced_work=("bookmark-labels",),
            legacy_displaced_work=True,
        )

    # The separate Stop and recovery entry paths both replay the historical list
    # while the converted C2 job is claimed; neither may create another leaf.
    assert replay("repeated Stop") == claimed.job_id
    assert replay("repeated recovery") == claimed.job_id
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM intel_jobs WHERE meeting_id=?", (state.id,)
        ).fetchone()[0] == 3
        # This test models a process loss after conversion/claim; a live lease
        # must not be adopted, while a stale one preserves stored-ID recovery.
        conn.execute(
            "UPDATE intel_jobs SET executor_lease_expires_at=0 WHERE job_id=?",
            (claimed.job_id,),
        )

    assert process_next_intel_job() is True
    ready = db.meetings.get_meeting(state.id)
    assert ready is not None and ready.intel_status == "ready"
    # Replaying Stop/recovery after C2 completion preserves the terminal leaf,
    # ready glass, and its single physical analysis.
    assert replay("Stop after ready") == claimed.job_id
    assert replay("recovery after ready") == claimed.job_id
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT status FROM intel_jobs WHERE meeting_id=? ORDER BY requested_at,job_id",
            (state.id,),
        ).fetchall()
    assert sorted(row["status"] for row in rows) == ["succeeded", "superseded", "superseded"]
    assert db.meetings.get_meeting(state.id).intel_status == "ready"
    assert len(engine.analyzed) == 1


def test_zero_frozen_bookmarks_omit_label_route_and_preserve_analysis(tmp_path, monkeypatch):
    """A deleted final bookmark cannot make C1's base summary route-integrity fail."""
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    db, broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(
        db, "m-zero-frozen-bookmarks", bookmarks=(0.5,),
        displaced_work=("bookmark-labels",), legacy_claimed=False,
        legacy_stop_handoff=True,
    )
    with db._connection() as conn:
        conn.execute("DELETE FROM bookmarks WHERE meeting_id=?", (state.id,))
    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claimed is not None and claimed.parent_operation_id and claimed.bundle_id
    with db._connection() as conn:
        members = conn.execute(
            "SELECT capability_id FROM inference_parent_route_bundle_members WHERE bundle_id=?",
            (claimed.bundle_id,),
        ).fetchall()
        budget = conn.execute(
            "SELECT child_budget FROM kernel_parent_runs WHERE operation_id=?",
            (claimed.parent_operation_id,),
        ).fetchone()[0]
        # Simulate process loss after the durable C1 claim; recovery must retain
        # stored-ID execution while the zero-operation route stays omitted.
        conn.execute(
            "UPDATE intel_jobs SET executor_lease_expires_at=0 WHERE job_id=?",
            (claimed.job_id,),
        )
    assert [member["capability_id"] for member in members] == ["meeting.deferred_analysis"]
    assert budget == 4
    assert process_next_intel_job() is True
    ready = db.meetings.get_meeting(state.id)
    assert ready is not None and ready.intel_status == "ready"
    assert len(engine.analyzed) == 1 and engine.labels == []
    assert "route_integrity" not in str(db.intel.get_intel_job(state.id))


def test_live_bound_executor_lease_excludes_background_http_and_cli_competitors(tmp_path, monkeypatch):
    """One live lease owns blocked egress across drain and independent connections."""
    from holdspeak.intel_queue import drain_intel_queue, process_next_intel_job

    db, _broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-live-executor-lease", legacy_claimed=False)
    entered = threading.Event()
    release = threading.Event()
    physical_calls = 0

    def blocked_analysis(transcript: str, *, stream: bool = False):
        nonlocal physical_calls
        assert stream is False
        physical_calls += 1
        entered.set()
        assert release.wait(timeout=3.0)
        return engine._result()

    monkeypatch.setattr(engine, "analyze", blocked_analysis)
    outcome: list[bool] = []
    worker = threading.Thread(target=lambda: outcome.append(process_next_intel_job()))
    worker.start()
    assert entered.wait(timeout=2.0)

    # HTTP/service drain in the same process and a CLI-shaped independent DB
    # connection both see the durable live bearer, not recoverable work.
    assert drain_intel_queue(max_jobs=1) == 0
    other = Database(db.db_path)
    with other._connection() as conn:
        live = conn.execute(
            "SELECT job_id FROM intel_jobs WHERE meeting_id=?", (state.id,)
        ).fetchone()
    assert live is not None
    assert other.intel.get_bound_claimed_intel_job() is None
    assert other.intel.take_over_stale_bound_executor(str(live["job_id"])) is None

    release.set()
    worker.join(timeout=3.0)
    assert not worker.is_alive() and outcome == [True]
    assert physical_calls == len(requests) == 1
    parents = _parents(db, PARENT_KIND)
    assert len(parents) == 1 and parents[0]["state"] == "SUCCEEDED"
    children = _children(db, parents[0]["operation_id"])
    assert len(children) == 1
    assert _broker.store.receipt(children[0]["operation_id"])["outcome"] == "succeeded"
    with db._connection() as conn:
        job = conn.execute("SELECT status FROM intel_jobs WHERE meeting_id=?", (state.id,)).fetchone()
        retries = conn.execute(
            """SELECT COUNT(*) FROM intel_job_attempts WHERE meeting_id=?
               AND event_kind IN ('scheduled_retry','retry')""",
            (state.id,),
        ).fetchone()[0]
        successors = conn.execute(
            "SELECT COUNT(*) FROM intel_jobs WHERE meeting_id=? AND origin_job_id IS NOT NULL",
            (state.id,),
        ).fetchone()[0]
    # C2's claim-planning descriptor replacement is one historical predecessor,
    # not a retry successor; no retry event or second executor was created.
    assert job["status"] == "succeeded" and retries == 0 and successors == 1


def test_stale_takeover_reconciles_only_its_own_execution(tmp_path, monkeypatch):
    """Recovering stale B cannot terminalize healthy in-flight A."""
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    db, broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state_b = _queued_meeting(
        db, "m-scoped-recovery-b", text="meeting-b stale transcript", legacy_claimed=False,
    )
    stale_b = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert stale_b is not None and stale_b.meeting_id == state_b.id
    state_a = _queued_meeting(
        db, "m-scoped-recovery-a", text="meeting-a healthy transcript", legacy_claimed=False,
    )
    entered, release = threading.Event(), threading.Event()
    physical_a = 0

    def analysis(transcript: str, *, stream: bool = False):
        nonlocal physical_a
        assert stream is False
        if "meeting-a healthy" in transcript:
            physical_a += 1
            entered.set()
            assert release.wait(timeout=5.0)
        return engine._result()

    monkeypatch.setattr(engine, "analyze", analysis)
    a_result: list[bool] = []
    worker_a = threading.Thread(target=lambda: a_result.append(process_next_intel_job()))
    worker_a.start()
    assert entered.wait(timeout=2.0)

    # B lost its process; a normal Process/CLI path adopts it while A's dispatch
    # is still live. Scoped recovery may inspect B only, never A's intent.
    with db._connection() as conn:
        conn.execute("UPDATE intel_jobs SET executor_lease_expires_at=0 WHERE job_id=?", (stale_b.job_id,))
    assert process_next_intel_job() is True
    with db._connection() as conn:
        a_execution = conn.execute(
            """SELECT execution.state FROM inference_route_executions execution
               JOIN inference_route_attempts attempt ON attempt.execution_id=execution.id
               JOIN kernel_operations child ON child.operation_id=attempt.child_operation_id
               WHERE child.parent_operation_id=(SELECT parent_operation_id FROM intel_jobs WHERE meeting_id=?)""",
            (state_a.id,),
        ).fetchone()
    assert a_execution is not None and a_execution["state"] == "active"

    release.set()
    worker_a.join(timeout=5.0)
    assert not worker_a.is_alive() and a_result == [True] and physical_a == 1
    with db._connection() as conn:
        a_job = conn.execute("SELECT status FROM intel_jobs WHERE meeting_id=?", (state_a.id,)).fetchone()
        snapshots = conn.execute(
            "SELECT COUNT(*) FROM intel_snapshots WHERE meeting_id=?", (state_a.id,)
        ).fetchone()[0]
        retries = conn.execute(
            "SELECT COUNT(*) FROM intel_job_attempts WHERE meeting_id=? AND outcome='scheduled_retry'",
            (state_a.id,),
        ).fetchone()[0]
        successors = conn.execute(
            "SELECT COUNT(*) FROM intel_jobs WHERE meeting_id=? AND origin_job_id IS NOT NULL",
            (state_a.id,),
        ).fetchone()[0]
    assert a_job["status"] == "succeeded"
    assert snapshots == 1 and retries == 0 and successors == 1


def test_bound_executor_heartbeat_exception_fails_closed(tmp_path, monkeypatch):
    """A renewal exception is an ownership loss, not a dead silent thread."""
    from holdspeak.intel_queue import _BoundExecutorLease
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    db, broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    _queued_meeting(db, "m-heartbeat-renewal-exception", legacy_claimed=False)
    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claimed is not None
    failed = threading.Event()
    calls = 0

    def renewal(job):
        nonlocal calls
        calls += 1
        if calls == 1:
            return True
        failed.set()
        raise RuntimeError("simulated SQLite renewal failure")

    monkeypatch.setattr(db.intel, "renew_bound_executor_lease", renewal)
    monkeypatch.setattr("holdspeak.intel_queue.BOUND_EXECUTOR_HEARTBEAT_SECONDS", 0.01)
    lease = _BoundExecutorLease(db, claimed)
    assert lease.start() is True
    assert failed.wait(timeout=2.0)
    assert lease.lost is True
    assert lease.held() is False
    lease.close()


def test_stale_executor_cannot_publish_or_settle_after_epoch_takeover(tmp_path, monkeypatch):
    """Epoch one may return from model work, but epoch two alone owns effects."""
    from holdspeak.intel_queue import _process_bound_intel_job
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    db, broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-stale-effect-fence", legacy_claimed=False)
    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claimed is not None
    entered, release = threading.Event(), threading.Event()
    physical_calls = 0

    def blocked_analysis(transcript: str, *, stream: bool = False):
        nonlocal physical_calls
        assert stream is False
        physical_calls += 1
        entered.set()
        assert release.wait(timeout=5.0)
        return engine._result()

    monkeypatch.setattr(engine, "analyze", blocked_analysis)
    first_result: list[bool] = []
    first = threading.Thread(target=lambda: first_result.append(_process_bound_intel_job(
        db, claimed, broker, on_meeting_ready=None, retry_base_seconds=1,
        retry_max_seconds=1, retry_max_attempts=4,
    )))
    first.start()
    assert entered.wait(timeout=2.0)

    # Simulate laptop suspension: the still-blocked epoch-one worker loses its
    # bearer, while another process wins the durable epoch-two takeover.
    with db._connection() as conn:
        conn.execute("UPDATE intel_jobs SET executor_lease_expires_at=0 WHERE job_id=?", (claimed.job_id,))
    adopted = Database(db.db_path).intel.take_over_stale_bound_executor(str(claimed.job_id))
    assert adopted is not None and adopted.executor_lease_epoch == 2
    release.set()
    first.join(timeout=5.0)
    assert not first.is_alive() and first_result == [False]

    # The stale result has a real child receipt, but no projection, Meeting
    # mutation, queue transition, parent close, successor, or retry evidence.
    with db._connection() as conn:
        stale_stage = conn.execute(
            "SELECT state,final_result_json FROM kernel_projection_stages"
        ).fetchone()
        job = conn.execute(
            "SELECT status,executor_lease_epoch FROM intel_jobs WHERE job_id=?", (claimed.job_id,)
        ).fetchone()
        snapshot_count = conn.execute(
            "SELECT COUNT(*) FROM intel_snapshots WHERE meeting_id=?", (state.id,)
        ).fetchone()[0]
        successors = conn.execute(
            "SELECT COUNT(*) FROM intel_jobs WHERE origin_job_id=?", (claimed.job_id,)
        ).fetchone()[0]
        retries = conn.execute(
            "SELECT COUNT(*) FROM intel_job_attempts WHERE job_id=? AND outcome='scheduled_retry'",
            (claimed.job_id,),
        ).fetchone()[0]
    assert stale_stage is not None and stale_stage["state"] == "DISCARDED"
    assert "executor_lease_lost" in str(stale_stage["final_result_json"])
    assert job["status"] in {"claimed", "running"} and job["executor_lease_epoch"] == 2
    assert snapshot_count == successors == retries == 0
    parent = _parents(db, PARENT_KIND)[0]
    assert parent["state"] == "OPEN" and not broker.store.receipt(parent["operation_id"])

    # Epoch two replays the earned child result through its new fencing token;
    # it does not issue a second physical call, and it alone settles the parent.
    assert _process_bound_intel_job(
        db, adopted, broker, on_meeting_ready=None, retry_base_seconds=1,
        retry_max_seconds=1, retry_max_attempts=4,
    ) is True
    assert physical_calls == 1
    parent = _parents(db, PARENT_KIND)[0]
    assert parent["state"] == "SUCCEEDED" and broker.store.receipt(parent["operation_id"])
    with db._connection() as conn:
        final = conn.execute("SELECT status FROM intel_jobs WHERE job_id=?", (claimed.job_id,)).fetchone()
        assert conn.execute("SELECT COUNT(*) FROM intel_snapshots WHERE meeting_id=?", (state.id,)).fetchone()[0] == 1
    assert final["status"] == "succeeded"


def test_stale_bound_executor_takeover_cas_allows_one_cross_connection_owner(tmp_path, monkeypatch):
    """Two independent repositories can adopt one stale owner exactly once."""
    from concurrent.futures import ThreadPoolExecutor
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    db, broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-cross-process-lease", legacy_claimed=False)
    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claimed is not None and claimed.job_id
    with db._connection() as conn:
        conn.execute(
            "UPDATE intel_jobs SET executor_lease_expires_at=0 WHERE job_id=?",
            (claimed.job_id,),
        )
    other = Database(db.db_path)
    with ThreadPoolExecutor(max_workers=2) as workers:
        adopted = list(workers.map(
            lambda repo: repo.intel.take_over_stale_bound_executor(str(claimed.job_id)),
            (db, other),
        ))
    winners = [job for job in adopted if job is not None]
    assert len(winners) == 1
    assert winners[0].executor_lease_epoch == 2
    assert other.intel.get_bound_claimed_intel_job() is None


def test_bound_claim_commit_recovers_exact_owner_without_second_egress(tmp_path, monkeypatch):
    """Startup recovery adopts the committed C1b IDs instead of re-resolving."""
    db, broker, _engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-bound-recovery", legacy_claimed=False)
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claimed is not None and claimed.parent_operation_id and claimed.bundle_id
    # Process loss leaves the first bearer unrenewed. Only a stale durable lease
    # may be adopted for stored-ID recovery.
    with db._connection() as conn:
        conn.execute(
            "UPDATE intel_jobs SET executor_lease_expires_at=0 WHERE job_id=?",
            (claimed.job_id,),
        )
    assert process_next_intel_job() is True
    assert process_next_intel_job() is False
    with db._connection() as conn:
        claims = conn.execute("SELECT COUNT(*) FROM intel_job_attempts WHERE job_id=? AND event_kind='claim'", (claimed.job_id,)).fetchone()[0]
    assert claims == 1
    assert len(requests) == 1
    assert db.meetings.get_meeting(state.id).intel is not None


def test_bound_publication_fence_supersedes_stale_result(tmp_path, monkeypatch):
    """A stale elected analysis remains evidence but cannot overwrite Meeting state."""
    db, broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-bound-publication", legacy_claimed=False)
    from holdspeak.intel_queue import process_next_intel_job

    real_finalize = broker.projection_stager.finalize
    changed = False

    def mutate_before_finalize(invocation_id: str):
        nonlocal changed
        if not changed:
            changed = True
            with db._connection() as conn:
                conn.execute("UPDATE segments SET text='changed before publication' WHERE meeting_id=?", (state.id,))
        return real_finalize(invocation_id)

    monkeypatch.setattr(broker.projection_stager, "finalize", mutate_before_finalize)
    assert process_next_intel_job() is True
    assert db.meetings.get_meeting(state.id).intel is None
    with db._connection() as conn:
        old = conn.execute("SELECT status FROM intel_jobs WHERE meeting_id=? ORDER BY requested_at LIMIT 1", (state.id,)).fetchone()
        fresh = conn.execute("SELECT status FROM intel_jobs WHERE meeting_id=? ORDER BY requested_at DESC LIMIT 1", (state.id,)).fetchone()
        event = conn.execute("SELECT outcome FROM intel_job_attempts WHERE meeting_id=? AND event_kind='publication_fence_superseded'", (state.id,)).fetchone()
    assert old is not None and old["status"] == "superseded"
    assert fresh is not None and fresh["status"] == "queued"
    assert event is not None and event["outcome"] == "superseded"


def test_bound_deferred_kernel_refusal_is_terminal_with_one_attempt(tmp_path, monkeypatch):
    """FX4 applies to the deferred-shaped SERVICE route as well."""
    db, _broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-bound-refusal", legacy_claimed=False)
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.kernel.model import KernelRefused

    def refuse(*_args, **_kwargs):
        raise KernelRefused("deferred_refused")

    monkeypatch.setattr(engine, "analyze", refuse)
    assert process_next_intel_job() is True
    job = db.intel.get_intel_job(state.id)
    assert job is not None and job.status == "failed" and job.attempts == 1
    with db._connection() as conn:
        events = conn.execute(
            "SELECT outcome FROM intel_job_attempts WHERE meeting_id=? AND outcome='refused'",
            (state.id,),
        ).fetchall()
    assert len(events) == 1
    assert len(requests) == 1


def test_bound_retry_success_hides_failed_ancestor_from_all_ordinary_readers(tmp_path, monkeypatch):
    """A terminal retry successor owns the lineage, never its failed ancestor."""
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-bound-lineage", legacy_claimed=False)
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.services.meeting_intel_service import MeetingIntelService

    engine.error = "transient provider failure"
    assert process_next_intel_job(retry_base_seconds=1, retry_max_seconds=1) is True
    with db._connection() as conn:
        successor = conn.execute(
            "SELECT job_id FROM intel_jobs WHERE meeting_id=? AND status='queued'",
            (state.id,),
        ).fetchone()
        assert successor is not None
        conn.execute(
            "UPDATE intel_jobs SET requested_at=? WHERE job_id=?",
            (datetime.now().isoformat(), str(successor["job_id"])),
        )
    engine.error = None
    assert process_next_intel_job(retry_base_seconds=1, retry_max_seconds=1) is True

    # The counsel's five ordinary-reader assertions.
    assert db.intel.get_intel_job(state.id) is None
    summary = db.intel.get_intel_queue_summary()
    assert summary.failed_jobs == summary.queued_jobs == summary.running_jobs == 0
    desk = db.projections.list(limit=200)["projections"]
    assert not any(row["source_kind"] == "intel_job" and row["attention_state"] == "needs_attention" for row in desk)
    recovery = MeetingIntelService(db).get_recovery(None, state.id)
    assert recovery["state"] == "ready" and recovery["visible"] is False
    assert db.intel.request_intel_retry(state.id) == "ready"


def test_bound_bookmark_operations_are_frozen_and_budgeted_per_instance(tmp_path, monkeypatch):
    """More labels than one policy allowance, plus a physical retry, stays lawful."""
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    timestamps = (0.25, 0.5, 1.0, 1.5, 2.0, 2.5)
    state = _queued_meeting(
        db, "m-bound-bookmark-budget", bookmarks=timestamps,
        displaced_work=("bookmark-labels",), legacy_claimed=False,
    )
    from holdspeak.intel_queue import process_next_intel_job

    frozen = db.intel.get_intel_job(state.id)
    assert frozen is not None and len(frozen.frozen_bookmark_operations) == len(timestamps)
    original = engine.generate_bookmark_label_with_context
    physical_calls = 0

    def retry_once(**kwargs):  # type: ignore[no-untyped-def]
        nonlocal physical_calls
        physical_calls += 1
        if physical_calls == 1:
            # Typed invalid output is retryable by the frozen route controller,
            # so the next provider call is a second physical attempt under this
            # same bounded parent rather than a fresh queue job.
            return None
        return original(**kwargs)

    monkeypatch.setattr(engine, "generate_bookmark_label_with_context", retry_once)
    # The first physical provider call fails; its frozen-route retry settles
    # under the same parent and then every remaining frozen label executes.
    assert process_next_intel_job() is True
    assert physical_calls == len(timestamps) + 1
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed is not None and refreshed.intel_status == "ready"
    assert [bookmark.label for bookmark in refreshed.bookmarks] == ["Budget decision"] * len(timestamps)
    parent = _parents(db, PARENT_KIND)[0]
    # Every label gets its own four-attempt allowance, as does base analysis.
    assert int(parent["child_budget"]) == 4 * (1 + len(timestamps))
    assert "parent_child_budget_exhausted" not in json.dumps(_rows(db, "kernel_receipts"))


def test_bound_bookmark_labels_preserve_duplicate_timestamp_identities(tmp_path, monkeypatch):
    """Two frozen rows at one timestamp receive their own earned labels."""
    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(
        db, "m-bound-duplicate-bookmarks", bookmarks=(0.5, 0.5),
        displaced_work=("bookmark-labels",), legacy_claimed=False,
    )
    from holdspeak.intel_queue import process_next_intel_job

    labels = iter(("First decision", "Second decision"))
    monkeypatch.setattr(
        engine, "generate_bookmark_label_with_context",
        lambda **_kwargs: next(labels),
    )
    assert process_next_intel_job() is True
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT id,label FROM bookmarks WHERE meeting_id=? ORDER BY id", (state.id,)
        ).fetchall()
    assert [row["label"] for row in rows] == ["First decision", "Second decision"]


def test_bound_bookmark_publication_skips_deleted_frozen_identity(tmp_path, monkeypatch):
    """A replacement at the same timestamp cannot inherit deleted work output."""
    db, broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(
        db, "m-bound-replaced-bookmark", bookmarks=(0.5,),
        displaced_work=("bookmark-labels",), legacy_claimed=False,
    )
    from holdspeak.intel_queue import process_next_intel_job

    with db._connection() as conn:
        original_id = conn.execute(
            "SELECT id FROM bookmarks WHERE meeting_id=?", (state.id,)
        ).fetchone()[0]
    finalize = broker.projection_stager.finalize
    finalizations = 0

    def delete_then_finalize(invocation_id):  # type: ignore[no-untyped-def]
        nonlocal finalizations
        finalizations += 1
        # Analysis finalizes first; delete the concrete frozen target immediately
        # before the bookmark child's staged publication commits.
        if finalizations == 2:
            with db._connection() as conn:
                conn.execute("DELETE FROM bookmarks WHERE id=?", (original_id,))
                conn.execute(
                    "INSERT INTO bookmarks (meeting_id,timestamp,label) VALUES (?,?,?)",
                    (state.id, 0.5, "Replacement"),
                )
        return finalize(invocation_id)

    monkeypatch.setattr(broker.projection_stager, "finalize", delete_then_finalize)
    assert process_next_intel_job() is True
    assert len(engine.labels) == 1
    with db._connection() as conn:
        replacement = conn.execute(
            "SELECT id,label FROM bookmarks WHERE meeting_id=?", (state.id,)
        ).fetchone()
        published = conn.execute(
            """SELECT final_result_json FROM kernel_projection_stages
               WHERE kind='meeting-bound-deferred-bookmark-label'"""
        ).fetchone()
    assert replacement is not None and replacement["id"] != original_id
    assert replacement["label"] == "Replacement"
    assert published is not None and json.loads(published["final_result_json"])["publication"] == "skipped"


def test_claim_refusal_terminalizes_and_unbounded_drain_continues(tmp_path, monkeypatch):
    """One typed refusal cannot spin or starve the next claimable Meeting."""
    db, broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    first = _queued_meeting(db, "m-bound-refusal-drain", legacy_claimed=False)
    second = _queued_meeting(db, "m-bound-after-refusal", legacy_claimed=False)
    from holdspeak.intel_queue import drain_intel_queue
    from holdspeak.services.errors import ValidationError
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    class RefuseFirstBinder(MeetingDeferredQueueBinder):
        first = True

        def prepare(self, job, command_ids):  # type: ignore[no-untyped-def]
            if RefuseFirstBinder.first:
                RefuseFirstBinder.first = False
                raise ValidationError("exact SERVICE assignment missing", code="no_assignment")
            return super().prepare(job, command_ids)

    monkeypatch.setattr(
        "holdspeak.services.meeting_deferred_queue_binding.MeetingDeferredQueueBinder",
        RefuseFirstBinder,
    )
    assert drain_intel_queue(max_jobs=None) == 2
    refused = db.intel.get_intel_job(first.id)
    assert refused is not None and refused.status == "failed"
    assert db.meetings.get_meeting(second.id).intel_status == "ready"
    with db._connection() as conn:
        events = conn.execute(
            "SELECT COUNT(*) FROM intel_job_attempts WHERE meeting_id=? AND event_kind='refusal'",
            (first.id,),
        ).fetchone()[0]
    assert events == 1


def test_reserved_successor_never_claims_before_old_parent_receipt(tmp_path, monkeypatch):
    """Close failure and process loss leave the fresh retry reserved, never dual-owned."""
    from holdspeak.db import Database
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    db, broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-bound-successor-race", legacy_claimed=False)
    old = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert old is not None and old.parent_operation_id
    db.intel.retry_intel_job(
        state.id, "transient", retry_at=datetime.now(), attempt=1, max_attempts=4,
    )
    with db._connection() as conn:
        successor = conn.execute(
            "SELECT job_id,status FROM intel_jobs WHERE origin_job_id=?", (old.job_id,)
        ).fetchone()
    assert successor is not None and successor["status"] == "reserved"

    other = Database(db.db_path)
    assert other.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker)) is None
    real_close = broker.parent_run_controller.close
    monkeypatch.setattr(
        broker.parent_run_controller, "close",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("injected parent close failure")),
    )
    assert process_next_intel_job() is False
    assert other.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker)) is None
    with db._connection() as conn:
        assert conn.execute(
            "SELECT state FROM kernel_parent_runs WHERE operation_id=?", (old.parent_operation_id,)
        ).fetchone()[0] == "OPEN"
        assert conn.execute("SELECT status FROM intel_jobs WHERE job_id=?", (successor["job_id"],)).fetchone()[0] == "reserved"

    monkeypatch.setattr(broker.parent_run_controller, "close", real_close)
    assert process_next_intel_job() is True
    with db._connection() as conn:
        assert conn.execute(
            "SELECT 1 FROM kernel_receipts WHERE operation_id=?", (old.parent_operation_id,)
        ).fetchone() is not None
        assert conn.execute("SELECT status FROM intel_jobs WHERE job_id=?", (successor["job_id"],)).fetchone()[0] == "queued"
    claim = other.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claim is not None and claim.parent_operation_id != old.parent_operation_id


def test_receipted_successor_is_promoted_once_after_process_loss(tmp_path, monkeypatch):
    """A crash after close but before promotion cannot strand or double-run retry work."""
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.meeting_session.deferred_admission import BoundDeferredIntelJob
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    db, broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-receipted-successor", legacy_claimed=False)
    old = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert old is not None and old.parent_operation_id
    db.intel.retry_intel_job(
        state.id, "transient", retry_at=datetime.now(), attempt=1, max_attempts=4,
    )
    with db._connection() as conn:
        successor = conn.execute(
            "SELECT job_id,status FROM intel_jobs WHERE origin_job_id=?", (old.job_id,)
        ).fetchone()
    assert successor is not None and successor["status"] == "reserved"

    # Simulate process loss exactly after close writes its durable receipt.
    assert BoundDeferredIntelJob.reconstruct(db, old, broker=broker).close("failed")
    with db._connection() as conn:
        assert conn.execute(
            "SELECT 1 FROM kernel_receipts WHERE operation_id=?", (old.parent_operation_id,)
        ).fetchone() is not None
        assert conn.execute(
            "SELECT status FROM intel_jobs WHERE job_id=?", (successor["job_id"],)
        ).fetchone()[0] == "reserved"

    # Fresh queue recovery promotes exactly once, then the next iteration claims
    # and executes exactly one successor parent/analysis.
    assert process_next_intel_job() is True
    assert db.intel.promote_receipted_bound_successors() == 0
    with db._connection() as conn:
        assert conn.execute(
            "SELECT status FROM intel_jobs WHERE job_id=?", (successor["job_id"],)
        ).fetchone()[0] == "queued"
        assert conn.execute(
            "SELECT COUNT(*) FROM intel_job_attempts WHERE job_id=? AND event_kind='successor_promoted'",
            (successor["job_id"],),
        ).fetchone()[0] == 1
    assert process_next_intel_job() is True
    assert len(_parents(db, PARENT_KIND)) == 2
    assert len(engine.analyzed) == 1
    assert process_next_intel_job() is False


def test_claim_admits_one_job_parent_with_base_and_plugin_children(tmp_path, monkeypatch):
    db, broker, engine, host, requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor", "risk_heatmap", "unrouted_plugin"),
        chain=("requirements_extractor", "risk_heatmap"),
    )
    state = _queued_meeting(db, "m-deferred")

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    # ONE job parent, under the narrow queue-worker SERVICE principal.
    parents = _parents(db, PARENT_KIND)
    assert len(parents) == 1
    parent = parents[0]
    assert parent["definition_ref"].startswith(f"meeting:{state.id}:deferred:ij_")
    assert parent["state"] == "SUCCEEDED"
    with db._connection() as conn:
        operation = dict(conn.execute(
            "SELECT * FROM kernel_operations WHERE operation_id=?", (parent["operation_id"],)
        ).fetchone())
        job = dict(conn.execute(
            "SELECT job_id,parent_operation_id,bundle_id FROM intel_jobs WHERE meeting_id=?",
            (state.id,),
        ).fetchone())
    assert operation["principal_kind"] == "service"
    assert operation["principal_identity"] == QUEUE_SERVICE_IDENTITY
    assert operation["name"] == PARENT_KIND
    assert job["parent_operation_id"] == parent["operation_id"] and job["bundle_id"]

    # The only admission is the C1 descriptor/bundle: no fresh v1 plan exists.
    snapshot = json.loads(parent["input_json"])
    assert snapshot["schema"] == "MeetingDeferredIntelQueueParent@1"
    assert snapshot["job_id"] == job["job_id"]
    assert parent["child_budget"] > 0
    assert JOB_DEADLINE_SECONDS == 30 * 60

    # Base analysis + EACH executed plugin = one frozen-route child.
    children = _children(db, parent["operation_id"])
    assert len(children) == 3
    assert len(requests) == 3
    assert all(broker.store.receipt(row["operation_id"])["outcome"] == "succeeded" for row in children)
    # Route order was preserved, and the unrouted planned plugin ran nothing.
    assert host.executed == ["requirements_extractor", "risk_heatmap"]

    # The domain outcome is unchanged: base analysis, runs, artifacts, Ready.
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed is not None
    assert refreshed.intel is not None
    assert refreshed.intel.summary == "The team reviewed the budget."
    assert refreshed.intel_status == "ready"
    assert refreshed.intel_completed_at is not None
    assert {row["plugin_id"] for row in _rows(db, "plugin_runs")} == {
        "requirements_extractor", "risk_heatmap"
    }
    assert len(db.plugins.list_artifacts(state.id)) == 2
    assert db.intel.get_intel_job(state.id) is None


def test_a_deduped_plugin_admits_no_child(tmp_path, monkeypatch):
    db, _broker, _engine, host, requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor", "risk_heatmap"),
        chain=("requirements_extractor", "risk_heatmap"),
    )
    state = _queued_meeting(db, "m-dedup")
    window_id = f"{state.id}:full"
    transcript_hash = __import__("hashlib").sha256(
        f"Me: {state.segments[0].text}".encode()
    ).hexdigest()
    db.plugins.record_plugin_run(
        meeting_id=state.id, window_id=window_id, plugin_id="risk_heatmap",
        plugin_version="1.0.0", status="success",
        idempotency_key=build_idempotency_key(
            meeting_id=state.id, window_id=window_id,
            plugin_id="risk_heatmap", transcript_hash=transcript_hash,
        ),
        duration_ms=1.0, output={"summary": "already done"},
    )

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    parent = _parents(db, PARENT_KIND)[0]
    # Base analysis + the ONE remaining plugin. The deduped plugin issues no child.
    assert len(_children(db, parent["operation_id"])) == 2
    assert host.executed == ["requirements_extractor"]
    assert len(requests) == 2
    assert db.meetings.get_meeting(state.id).intel_status == "ready"


def test_each_queue_retry_admits_a_new_job_parent(tmp_path, monkeypatch):
    db, broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr(_Cfg.meeting, "intent_router_enabled", False, raising=False)
    state = _queued_meeting(db, "m-retry")

    from holdspeak.intel_queue import process_next_intel_job

    engine.error = "the provider refused"
    assert process_next_intel_job() is True
    first = _parents(db, PARENT_KIND)
    assert len(first) == 1
    assert first[0]["state"] == "FAILED"
    job = db.intel.get_intel_job(state.id)
    assert job is not None and job.status == "queued" and job.attempts == 1
    engine.error = None
    assert process_next_intel_job(include_scheduled=True) is True

    parents = _parents(db, PARENT_KIND)
    assert len(parents) == 2, "a retry must be a NEW job parent, never a reopened epoch"
    assert parents[0]["operation_id"] != parents[1]["operation_id"]
    assert parents[0]["execution_epoch"] == parents[1]["execution_epoch"] == 1
    assert parents[0]["state"] == "FAILED" and parents[1]["state"] == "SUCCEEDED"
    assert json.loads(parents[1]["input_json"])["schema"] == "MeetingDeferredIntelQueueParent@1"
    assert db.meetings.get_meeting(state.id).intel_status == "ready"


def test_a_returned_error_result_fails_the_base_child_and_keeps_the_queue_vocabulary(tmp_path, monkeypatch):
    """A RETURNED provider error closes its child `failed`, sanitized, and retries.

    The queue's failure vocabulary is unchanged: it still reads the returned
    result's ``.error`` for the owner-facing reason, and the job still takes its
    existing retry path. What changes is the receipt — an attempt the domain
    calls failed can no longer be journaled as `succeeded`.
    """
    db, broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr(_Cfg.meeting, "intent_router_enabled", False, raising=False)
    state = _queued_meeting(db, "m-error-result")

    from holdspeak.intel_queue import process_next_intel_job

    engine.error = f"the endpoint echoed {SENTINEL}"
    assert process_next_intel_job() is True

    parent = _parents(db, PARENT_KIND)[0]
    assert parent["state"] == "FAILED"
    children = _children(db, parent["operation_id"])
    assert children
    assert any(
        broker.store.receipt(child["operation_id"])["outcome"] == "failed"
        for child in children
    )
    assert len(requests) >= 1

    # The queue's own path is untouched: retried, with the provider's reason.
    job = db.intel.get_intel_job(state.id)
    assert job is not None and job.status == "queued" and job.attempts == 1
    assert SENTINEL not in str(job.last_error)
    meeting = db.meetings.get_meeting(state.id)
    assert meeting.intel is None and meeting.intel_status != "ready"

    # ...and the sanitized receipt carries no provider text at all.
    for table in ("kernel_receipts", "kernel_operations", "kernel_journal"):
        for row in _rows(db, table):
            assert SENTINEL not in json.dumps(row, default=str)


def test_an_executed_plugin_runs_on_the_engine_its_frozen_revision_built(tmp_path, monkeypatch):
    """D2: the plugin's provider work uses the ADMITTED engine, not its own."""
    db, _broker, engine, host, requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor",), chain=("requirements_extractor",),
    )
    _queued_meeting(db, "m-engine")

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    # The engine bound for the plugin execution IS the engine the child's frozen
    # deployment revision built (identity, not equality) — the same object the
    # admitted base analysis ran on.
    assert host.bound_engines and all(bound is engine for bound in host.bound_engines)
    assert len(host.bound_engines) == 1
    assert host.executed == ["requirements_extractor"]
    # The bound route executes exactly one plugin child after analysis; the
    # revision evidence lives in the durable bundle rather than a v1 plan.
    assert len(requests) == 2
    parent = _parents(db, PARENT_KIND)[0]
    with db._connection() as conn:
        members = conn.execute(
            "SELECT capability_id,route_plan_id FROM inference_parent_route_bundle_members WHERE bundle_id=(SELECT bundle_id FROM intel_jobs WHERE parent_operation_id=?)",
            (parent["operation_id"],),
        ).fetchall()
    assert any(row["capability_id"] == "meeting.plugin.requirements_extractor" for row in members)
    assert {row["plugin_id"] for row in _rows(db, "plugin_runs")} == {"requirements_extractor"}


def test_an_llm_plugin_with_no_admitted_handle_is_refused_by_name(tmp_path, monkeypatch):
    """An llm plugin never self-builds: with no handle it refuses, by name.

    HS-131-08 phrased this as "the engine cannot be injected"; HS-131-14 makes the
    seam per-invocation, so the honest statement is simpler — an `llm` plugin that
    was handed no admitted handle does no model work and says which rule refused.
    """
    from holdspeak.plugins.host import (
        PLUGIN_LLM_ENGINE_NOT_INJECTABLE,
        PluginEngineNotInjectable,
        PluginHost,
    )
    from holdspeak.plugins.intelligence import PLUGIN_DISPATCH_REQUIRED

    class _SelfBuilding:
        id = "self_builder"
        version = "1.0.0"
        required_capabilities = ["llm"]

        def run(self, context: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
            raise AssertionError("an unadmitted llm plugin must refuse before run()")

    host = PluginHost(enabled_capabilities={"llm"})
    host.register(_SelfBuilding())
    result = host.execute(
        "self_builder", context={"transcript": "t"}, meeting_id="m",
        window_id="m:full", transcript_hash="h",
    )
    assert result.status == "error"
    assert PLUGIN_DISPATCH_REQUIRED in str(result.error)
    # The host-seam refusal keeps its own name: a HOST that cannot be handed the
    # admitted child's engine at all (no `issued_dispatch`) is a different fault.
    assert PluginEngineNotInjectable("x").reason == PLUGIN_LLM_ENGINE_NOT_INJECTABLE


def test_c2_plugin_child_uses_frozen_member_and_inner_output(tmp_path, monkeypatch):
    """C2 executes one installed plugin as a bound routed child, not a run wrapper."""
    db, _broker, _engine, host, _requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor",), chain=("requirements_extractor",),
    )
    state = _queued_meeting(db, "m-c2-inner", legacy_claimed=False)
    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    parent = _parents(db, PARENT_KIND)[0]
    assert len(_children(db, parent["operation_id"])) == 2
    assert host.executed == ["requirements_extractor"]
    run = db.plugins.list_plugin_runs(state.id, limit=10)[0]
    assert run.plugin_id == "requirements_extractor"
    assert run.output == {
        "summary": "requirements_extractor said something",
        "confidence_hint": 0.9,
        "active_intents": [],
    }
    with db._connection() as conn:
        member = conn.execute(
            """SELECT capability_id FROM inference_parent_route_bundle_members
               WHERE bundle_id=(SELECT bundle_id FROM intel_jobs WHERE meeting_id=?
                                ORDER BY updated_at DESC LIMIT 1)
                 AND capability_id='meeting.plugin.requirements_extractor'""",
            (state.id,),
        ).fetchone()
    assert member is not None


def test_c2_plugin_revision_drift_refuses_without_plugin_child(tmp_path, monkeypatch):
    db, _broker, _engine, host, _requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor",), chain=("requirements_extractor",),
    )
    state = _queued_meeting(db, "m-c2-drift", legacy_claimed=False)
    host.get_plugin = lambda _plugin_id: None  # type: ignore[method-assign]
    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    parent = _parents(db, PARENT_KIND)[0]
    assert len(_children(db, parent["operation_id"])) == 1
    run = db.plugins.list_plugin_runs(state.id, limit=10)[0]
    assert run.status == "error" and "revision_drift" in str(run.error)
    with db._connection() as conn:
        outcome = conn.execute(
            "SELECT outcome FROM intel_job_attempts WHERE meeting_id=? ORDER BY id DESC LIMIT 1",
            (state.id,),
        ).fetchone()[0]
    assert outcome == "refused"


def test_c2_unknown_plugin_id_refuses_claim_without_any_child(tmp_path, monkeypatch):
    db, _broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-c2-unknown", legacy_claimed=False)
    monkeypatch.setattr(
        "holdspeak.plugins.router.preview_route_from_transcript",
        lambda **_kwargs: _Route(("not_installed",)),
    )
    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    assert _parents(db, PARENT_KIND) == []
    assert _rows(db, "kernel_operations") == []
    with db._connection() as conn:
        event = conn.execute(
            "SELECT outcome,error FROM intel_job_attempts WHERE meeting_id=? ORDER BY id DESC LIMIT 1",
            (state.id,),
        ).fetchone()
    assert event is not None and event["outcome"] == "refused"
    assert "plugin" in str(event["error"]).lower()


@pytest.mark.parametrize("gate", ["deduped", "fault"])
def test_c2_non_executed_plugin_gates_mint_no_child(tmp_path, monkeypatch, gate):
    db, _broker, _engine, host, _requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor",), chain=("requirements_extractor",),
    )
    state = _queued_meeting(db, f"m-c2-gate-{gate}", legacy_claimed=False)
    transcript_hash = __import__("hashlib").sha256(
        f"Me: {state.segments[0].text}".encode()
    ).hexdigest()
    key = build_idempotency_key(
        meeting_id=state.id, window_id=f"{state.id}:full",
        plugin_id="requirements_extractor", transcript_hash=transcript_hash,
    )
    if gate == "deduped":
        db.plugins.record_plugin_run(
            meeting_id=state.id, window_id=f"{state.id}:full",
            plugin_id="requirements_extractor", plugin_version="0.1.0",
            status="success", idempotency_key=key, duration_ms=0.0,
            output={"summary": "already", "confidence_hint": 0.0, "active_intents": []},
        )
    else:
        monkeypatch.setenv("HOLDSPEAK_FAULT", "intel.plugin:requirements_extractor")

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    parent = _parents(db, PARENT_KIND)[0]
    assert len(_children(db, parent["operation_id"])) == 1
    assert host.executed == []


def test_c2_persisted_disabled_plugin_skips_before_admission(tmp_path, monkeypatch):
    """The real bound host reads the saved setting before it can mint a child."""
    from holdspeak.config import Config, MeetingConfig
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.meeting_plugins import build_bound_meeting_plugin_host

    # Preserve the unpatched loader; `_queue_rig` deliberately substitutes a
    # lightweight Config facade for most queue tests.
    production_load = Config.load.__func__
    db, _broker, _engine, _host, _requests = _queue_rig(
        tmp_path,
        monkeypatch,
        plugins=(),
        chain=("requirements_extractor", "project_detector"),
    )
    config_path = tmp_path / "holdspeak.json"
    Config(meeting=MeetingConfig(disabled_plugins=["requirements_extractor"])).save(config_path)
    monkeypatch.setattr("holdspeak.config.core._active_config_file", lambda: config_path)
    monkeypatch.setattr(Config, "load", classmethod(production_load))
    # Restore the actual bound-host factory: it loads the persisted MeetingConfig
    # and builds registered production plugins rather than a synthetic host.
    monkeypatch.setattr(
        "holdspeak.meeting_plugins.build_bound_meeting_plugin_host",
        build_bound_meeting_plugin_host,
    )
    state = _queued_meeting(db, "m-c2-persisted-disabled", legacy_claimed=False)

    assert process_next_intel_job() is True
    parent = _parents(db, PARENT_KIND)[0]
    children = _children(db, parent["operation_id"])
    # Base analysis + the unaffected project detector. The disabled member has
    # no admitted child, so its frozen route allowance remains unused.
    assert len(children) == 2
    runs = {run.plugin_id: run for run in db.plugins.list_plugin_runs(state.id, limit=20)}
    assert runs["requirements_extractor"].status == "skipped"
    assert runs["requirements_extractor"].error == "disabled for this project"
    assert runs["requirements_extractor"].output is None
    assert runs["project_detector"].status == "success"
    assert all(
        artifact.plugin_id != "requirements_extractor"
        for artifact in db.plugins.list_artifacts(state.id)
    )
    assert db.meetings.get_meeting(state.id).intel_status == "ready"


# ------------------------------------- D3: the displaced work actually executes


def test_a_stop_displaced_job_runs_the_bookmark_and_title_children(tmp_path, monkeypatch):
    from holdspeak.meeting_session.intel_plan import (
        DISPLACED_AUTO_TITLE,
        DISPLACED_BOOKMARK_LABELS,
        DISPLACED_FINAL_ANALYSIS,
    )

    db, broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr(_Cfg.meeting, "intent_router_enabled", False, raising=False)
    state = _queued_meeting(
        db, "m-displaced",
        text="we agreed to cut the travel budget",
        title="",
        bookmarks=(2.0,),
        displaced_work=(
            DISPLACED_FINAL_ANALYSIS, DISPLACED_BOOKMARK_LABELS, DISPLACED_AUTO_TITLE,
        ),
    )
    job = db.intel.get_intel_job(state.id)
    assert job.displaced_work == (
        DISPLACED_FINAL_ANALYSIS, DISPLACED_BOOKMARK_LABELS, DISPLACED_AUTO_TITLE,
    )

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    # The displaced members are frozen in the C1 bundle and each dispatch is
    # one trusted child of the job parent.
    parent = _parents(db, PARENT_KIND)[0]
    snapshot = json.loads(parent["input_json"])
    assert snapshot["displaced_work"] == list(job.displaced_work)
    with db._connection() as conn:
        members = conn.execute(
            "SELECT capability_id FROM inference_parent_route_bundle_members WHERE bundle_id=(SELECT bundle_id FROM intel_jobs WHERE parent_operation_id=?)",
            (parent["operation_id"],),
        ).fetchall()
    assert {row["capability_id"] for row in members} >= {
        "meeting.deferred_analysis", "meeting.bookmark_label", "meeting.auto_title",
    }
    assert len(requests) == 3
    assert len(_children(db, parent["operation_id"])) == 3
    assert engine.labels and engine.titles

    # The outputs landed through receipt-gated materializers, in the DB.
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed.title == "Quarterly budget review"
    assert [bookmark.label for bookmark in refreshed.bookmarks] == ["Budget decision"]
    kinds = {
        str(row["kind"]): str(row["state"]) for row in _rows(db, "kernel_projection_stages")
    }
    assert kinds["meeting-bound-deferred-bookmark-label"] == "PUBLISHED"
    assert kinds["meeting-bound-deferred-auto-title"] == "PUBLISHED"
    # Only now is the meeting Ready.
    assert refreshed.intel_status == "ready"
    assert refreshed.intel_completed_at is not None
    assert db.intel.get_intel_job(state.id) is None


def test_the_meeting_is_not_ready_until_the_displaced_work_settles(tmp_path, monkeypatch):
    from holdspeak.meeting_session.intel_plan import (
        DISPLACED_AUTO_TITLE,
        DISPLACED_FINAL_ANALYSIS,
    )

    db, _broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr(_Cfg.meeting, "intent_router_enabled", False, raising=False)
    state = _queued_meeting(
        db, "m-displaced-fails", title="",
        displaced_work=(DISPLACED_FINAL_ANALYSIS, DISPLACED_AUTO_TITLE),
    )

    def explode(transcript: str) -> str:
        raise RuntimeError("the title endpoint refused")

    monkeypatch.setattr(engine, "generate_title", explode)

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    refreshed = db.meetings.get_meeting(state.id)
    # The base analysis is retained, but the meeting is NOT Ready and the job is
    # still outstanding: displaced work that did not settle blocks readiness.
    assert refreshed.intel is not None
    assert refreshed.intel_status != "ready"
    assert refreshed.intel_completed_at is None
    assert refreshed.title in (None, "")
    job = db.intel.get_intel_job(state.id)
    assert job is not None
    assert DISPLACED_AUTO_TITLE in job.displaced_work, "a retry must still know its displaced work"


def test_a_normal_deferred_job_runs_no_title_or_bookmark_children(tmp_path, monkeypatch):
    db, _broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr(_Cfg.meeting, "intent_router_enabled", False, raising=False)
    state = _queued_meeting(db, "m-normal", title="", bookmarks=(2.0,))

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    parent = _parents(db, PARENT_KIND)[0]
    snapshot = json.loads(parent["input_json"])
    assert snapshot["displaced_work"] == []
    with db._connection() as conn:
        members = conn.execute(
            "SELECT capability_id FROM inference_parent_route_bundle_members WHERE bundle_id=(SELECT bundle_id FROM intel_jobs WHERE parent_operation_id=?)",
            (parent["operation_id"],),
        ).fetchall()
    assert [row["capability_id"] for row in members] == ["meeting.deferred_analysis"]
    assert len(requests) == 1
    assert engine.titles == [] and engine.labels == []
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed.title in (None, "")
    assert [bookmark.label for bookmark in refreshed.bookmarks] == ["Bookmark"]
    assert refreshed.intel_status == "ready"


# ------------------------------------------- D4: no late ready around the stop




def test_no_transcript_material_reaches_the_kernel_journal_on_the_deferred_path(tmp_path, monkeypatch):
    db, _broker, engine, host, _requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor",), chain=("requirements_extractor",),
    )
    state = _queued_meeting(db, "m-journal", text=f"the revenue number is {SENTINEL}")

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    # A changed immutable descriptor gets a second job whose provider FAILS
    # with text quoting the transcript; a completed identical descriptor is not
    # silently re-enqueued.
    state.segments[0].text += " revised"
    db.meetings.save_meeting(state)
    db.intel.enqueue_intel_job(
        state.id, transcript_hash=state.transcript_hash(), reason="second pass"
    )

    def explode(transcript: str, *, stream: bool = False):
        raise RuntimeError(f"endpoint echoed: {transcript}")

    monkeypatch.setattr(engine, "analyze", explode)
    assert process_next_intel_job() is True

    # The provider really received the material...
    assert any(SENTINEL in text for text in engine.analyzed)
    # ...and no kernel row carries it.
    for table in ("kernel_operations", "kernel_receipts", "kernel_journal", "kernel_parent_runs"):
        rows = _rows(db, table)
        assert rows, table
        for row in rows:
            assert SENTINEL not in json.dumps(row, default=str), table
    outcomes = {str(row["outcome"]) for row in _rows(db, "kernel_receipts")}
    assert {"succeeded", "failed"} <= outcomes, outcomes


def test_stop_fences_live_bundle_before_return_and_rejects_late_ready(tmp_path, monkeypatch):
    """Stop acknowledgement closes admission and a late live status cannot win."""
    from holdspeak.meeting_session.models import TranscriptSegment
    from tests.unit.test_meeting_capture_durability import _routed_recovery_session, _parent_state

    db, _broker, session = _routed_recovery_session(tmp_path, monkeypatch)
    state = session.start()
    state.segments.append(TranscriptSegment("deferred aftercare", "Me", 0.0, 1.0))
    final = session.stop()
    assert _parent_state(db, session._route_bundle["id"]) != "OPEN"
    assert session._intel_closed is True
    assert final.intel_status == "queued"
    session._set_intel_status("ready", "late physical result")
    assert final.intel_status == "queued"
    assert "queued for deferred processing" in str(final.intel_status_detail).lower()


# ----------------------------------------------------------------- HS-151-03
# Plugin-assignment-skip tests: a plugin capability with NO assignment is
# excluded with a receipt at claim planning, not a terminal refusal.


def _assign_deferred_queue_routes_partial(
    db: Database,
    *,
    skip_plugin_ids: frozenset[str],
) -> None:
    """Like ``_assign_deferred_queue_routes`` but OMITS assignments for
    specific plugin capabilities, simulating a user who wired one model
    for core analysis but not for every installed plugin.
    """
    from holdspeak.inference_capabilities import process_inference_capability_registry

    all_capabilities = (
        "meeting.deferred_analysis",
        "meeting.bookmark_label",
        "meeting.auto_title",
        *(
            capability_id
            for capability_id in process_inference_capability_registry().capability_ids
            if capability_id.startswith("meeting.plugin.")
        ),
    )
    assigned = [
        c for c in all_capabilities
        if not any(c == f"meeting.plugin.{pid}" for pid in skip_plugin_ids)
    ]
    _profile(
        db,
        "deferred-queue-model",
        claims=(
            "language", "structured_output", "meeting_plugin",
            *(_result_claim(item) for item in assigned),
        ),
        modalities=("language", "text"),
    )
    assignments = InferenceAssignmentService(db)
    for ordinal, capability in enumerate(assigned, 1):
        assignments.set_assignment(
            OWNER,
            {
                "command_id": f"deferred-queue-assignment-{ordinal}",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": capability},
                "entries": [{"profile_id": "deferred-queue-model", "profile_revision": 1}],
            },
        )


def _queue_rig_partial_assignments(
    tmp_path: Path,
    monkeypatch,
    *,
    plugins: tuple[str, ...],
    chain: tuple[str, ...],
    skip_plugin_ids: frozenset[str],
):
    """Like ``_queue_rig`` but uses partial assignments (some plugins skipped)."""
    db = Database(tmp_path / "queue.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *a, **k: db)
    _assign_deferred_queue_routes_partial(db, skip_plugin_ids=skip_plugin_ids)
    broker = _configure(db)
    engine = FakeIntel()
    host = FakeHost(plugins)

    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: host)
    monkeypatch.setattr(
        "holdspeak.plugins.router.preview_route_from_transcript",
        lambda **kwargs: _Route(chain),
    )
    requests = _observe(broker, monkeypatch)
    return db, broker, engine, host, requests


def test_unassigned_plugin_excluded_with_receipt_core_analysis_succeeds(
    tmp_path, monkeypatch
):
    """HS-151-03: a plugin capability with NO assignment is skipped, not terminal.

    The MIR router routes ``project_detector`` and ``requirements_extractor``.
    Only ``requirements_extractor`` has an assignment. The claim should:
    - exclude ``project_detector`` with a ``plugin_chain_skipped`` receipt
    - freeze only ``requirements_extractor`` as a member
    - base analysis succeeds and meeting becomes ready
    """
    db, broker, engine, host, requests = _queue_rig_partial_assignments(
        tmp_path, monkeypatch,
        plugins=("project_detector", "requirements_extractor"),
        chain=("project_detector", "requirements_extractor"),
        skip_plugin_ids=frozenset({"project_detector"}),
    )
    state = _queued_meeting(db, "m-skip-plugin")

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    # The claim should succeed with base analysis + the ONE assigned plugin.
    parents = _parents(db, PARENT_KIND)
    assert len(parents) == 1
    parent = parents[0]
    assert parent["state"] == "SUCCEEDED"

    # Base analysis + requirements_extractor = 2 children (project_detector skipped).
    children = _children(db, parent["operation_id"])
    assert len(children) == 2
    assert len(requests) == 2
    assert host.executed == ["requirements_extractor"]

    # The meeting reaches ready.
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed is not None
    assert refreshed.intel_status == "ready"
    assert refreshed.intel is not None
    assert refreshed.intel.summary == "The team reviewed the budget."

    # The skipped plugin is recorded in the frozen descriptor.
    with db._connection() as conn:
        job = conn.execute(
            "SELECT displaced_work FROM intel_jobs WHERE meeting_id=?",
            (state.id,),
        ).fetchone()
    descriptor = json.loads(job["displaced_work"])
    route = descriptor.get("plugin_route", {})
    skipped = route.get("plugin_chain_skipped", [])
    assert len(skipped) == 1
    assert skipped[0]["plugin_id"] == "project_detector"
    assert skipped[0]["reason"] == "no_assignment"


def test_core_capability_missing_assignment_remains_terminal(
    tmp_path, monkeypatch
):
    """HS-151-03 Pin 3: core capabilities (meeting.deferred_analysis) missing
    an assignment remain a terminal refusal -- only meeting.plugin.* may skip.
    """
    # Create a rig with NO assignment for meeting.deferred_analysis itself.
    db = Database(tmp_path / "queue-core-missing.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *a, **k: db)
    # Assign only plugins, NOT core capabilities.
    from holdspeak.inference_capabilities import process_inference_capability_registry
    plugin_capabilities = [
        cid for cid in process_inference_capability_registry().capability_ids
        if cid.startswith("meeting.plugin.")
    ]
    all_to_assign = plugin_capabilities  # deliberately omit deferred_analysis
    _profile(
        db,
        "deferred-queue-model",
        claims=(
            "language", "structured_output", "meeting_plugin",
            *(_result_claim(item) for item in all_to_assign),
        ),
        modalities=("language", "text"),
    )
    assignments = InferenceAssignmentService(db)
    for ordinal, capability in enumerate(all_to_assign, 1):
        assignments.set_assignment(
            OWNER,
            {
                "command_id": f"core-missing-assignment-{ordinal}",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": capability},
                "entries": [{"profile_id": "deferred-queue-model", "profile_revision": 1}],
            },
        )
    broker = _configure(db)
    engine = FakeIntel()
    host = FakeHost(())
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr("holdspeak.meeting_plugins.build_bound_meeting_plugin_host", lambda: host)
    monkeypatch.setattr(
        "holdspeak.plugins.router.preview_route_from_transcript",
        lambda **kwargs: _Route(()),
    )
    state = _queued_meeting(db, "m-core-missing")

    from holdspeak.intel_queue import process_next_intel_job

    # The claim should fail -- core capability missing is terminal.
    result = process_next_intel_job()
    assert result is True  # progress was made (job settled as error)

    # Meeting should be in error, NOT ready.
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed is not None
    assert refreshed.intel_status == "error"
