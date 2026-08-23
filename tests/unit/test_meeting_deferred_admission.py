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
from holdspeak.meeting_session.deferred_admission import (
    CONTRACT_DEFERRED_ANALYSIS,
    CONTRACT_PLUGIN_PREFIX,
    JOB_DEADLINE_SECONDS,
    PARENT_KIND,
    QUEUE_SERVICE_IDENTITY,
    job_child_budget,
)
from holdspeak.meeting_session.intel_plan import (
    CAPABILITY_DEFERRED_ANALYSIS,
    MeetingIntelRefused,
    SESSION_CLOSED,
)
from holdspeak.meeting_session.models import Bookmark
from holdspeak.plugins.host import PluginRunResult, build_idempotency_key
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

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
                plugin_version="1.0.0",
                status="success",
                idempotency_key=build_idempotency_key(
                    meeting_id=meeting_id, window_id=window_id,
                    plugin_id=plugin_id, transcript_hash=transcript_hash,
                ),
                duration_ms=3.0,
                output={"summary": f"{plugin_id} said something", "confidence_hint": 0.9},
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
    capabilities = (
        "meeting.deferred_analysis",
        "meeting.bookmark_label",
        "meeting.auto_title",
    )
    _profile(
        db,
        "deferred-queue-model",
        claims=("language", "structured_output", *(_result_claim(item) for item in capabilities)),
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
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls: _Cfg))
    monkeypatch.setattr(
        "holdspeak.intel_queue.get_intel_runtime_status", lambda *a, **k: (True, "ready")
    )
    monkeypatch.setattr("holdspeak.intel_queue._routed_plugin_host", lambda enabled: host if enabled else None)
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
    legacy_claimed: bool = True,
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


def test_bound_claim_executes_stored_service_member_and_completes_ledger(tmp_path, monkeypatch):
    """C1c never calls the legacy admission path for a C1b-bound claim."""
    db, _broker, _engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-bound-worker", legacy_claimed=False)
    from holdspeak.meeting_session.deferred_admission import DeferredIntelJob
    from holdspeak.intel_queue import process_next_intel_job

    monkeypatch.setattr(
        DeferredIntelJob,
        "admit",
        classmethod(lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("legacy admit"))),
    )
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


def test_bound_claim_replaces_legacy_stop_handoff_with_frozen_descriptor(tmp_path, monkeypatch):
    """The Phase-B handoff list persists until C1 freezes its actual operations."""
    db, _broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
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
    assert len(rows) == 2
    assert rows[0]["job_id"] == original["job_id"]
    assert rows[0]["status"] == "superseded"
    assert rows[1]["origin_job_id"] == original["job_id"]
    assert rows[1]["parent_operation_id"]
    descriptor = json.loads(rows[1]["displaced_work"])
    assert descriptor["bookmark_operations"] == [
        {"id": 1, "timestamp": 0.25}, {"id": 2, "timestamp": 0.5},
    ]


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
    # while the converted V3 job is claimed; neither may create another leaf.
    assert replay("repeated Stop") == claimed.job_id
    assert replay("repeated recovery") == claimed.job_id
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM intel_jobs WHERE meeting_id=?", (state.id,)
        ).fetchone()[0] == 2

    assert process_next_intel_job() is True
    ready = db.meetings.get_meeting(state.id)
    assert ready is not None and ready.intel_status == "ready"
    # Replaying Stop/recovery after V3 completion preserves the terminal leaf,
    # ready glass, and its single physical analysis.
    assert replay("Stop after ready") == claimed.job_id
    assert replay("recovery after ready") == claimed.job_id
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT status FROM intel_jobs WHERE meeting_id=? ORDER BY requested_at,job_id",
            (state.id,),
        ).fetchall()
    assert [row["status"] for row in rows] == ["superseded", "succeeded"]
    assert db.meetings.get_meeting(state.id).intel_status == "ready"
    assert len(engine.analyzed) == 1


def test_bound_claim_commit_recovers_exact_owner_without_second_egress(tmp_path, monkeypatch):
    """Startup recovery adopts the committed C1b IDs instead of re-resolving."""
    db, broker, _engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-bound-recovery", legacy_claimed=False)
    from holdspeak.intel_queue import process_next_intel_job
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claimed is not None and claimed.parent_operation_id and claimed.bundle_id
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
    assert parent["definition_ref"] == f"meeting:{state.id}:deferred:1"
    assert parent["state"] == "SUCCEEDED"
    with db._connection() as conn:
        operation = dict(conn.execute(
            "SELECT * FROM kernel_operations WHERE operation_id=?", (parent["operation_id"],)
        ).fetchone())
    assert operation["principal_kind"] == "service"
    assert operation["principal_identity"] == QUEUE_SERVICE_IDENTITY
    assert operation["name"] == PARENT_KIND

    # A FRESH plan: its revision is the plan hash, its envelope is finite, and its
    # budget is 1 base + one per planned plugin + the declared retry allowance.
    snapshot = json.loads(parent["input_json"])
    assert snapshot["plan_sha256"] == parent["definition_revision"]
    assert snapshot["queue_attempt"] == 1
    assert set(snapshot["capabilities"]) == {
        CAPABILITY_DEFERRED_ANALYSIS,
        "plugin:requirements_extractor",
        "plugin:risk_heatmap",
        "plugin:unrouted_plugin",
    }
    assert parent["child_budget"] == job_child_budget(3) == 6
    assert parent["deadline_at"] - snapshot["deadline_at"] == pytest.approx(0.0, abs=1)
    assert JOB_DEADLINE_SECONDS == 30 * 60

    # Base analysis + EACH executed plugin = one trusted child.
    children = _children(db, parent["operation_id"])
    assert len(children) == 3
    assert [request.definition_origin.contract for request in requests] == [
        CONTRACT_DEFERRED_ANALYSIS,
        f"{CONTRACT_PLUGIN_PREFIX}requirements_extractor",
        f"{CONTRACT_PLUGIN_PREFIX}risk_heatmap",
    ]
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
    assert [request.definition_origin.contract for request in requests] == [
        CONTRACT_DEFERRED_ANALYSIS,
        f"{CONTRACT_PLUGIN_PREFIX}requirements_extractor",
    ]
    assert db.meetings.get_meeting(state.id).intel_status == "ready"


def test_each_queue_retry_admits_a_new_job_parent(tmp_path, monkeypatch):
    db, broker, engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr("holdspeak.intel_queue._routed_plugin_host", lambda enabled: None)
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
    # Continue the historical crash-recovery specimen through its legacy owner.
    assert db.intel.claim_next_intel_job(include_scheduled=True) is not None

    engine.error = None
    assert process_next_intel_job(include_scheduled=True) is True

    parents = _parents(db, PARENT_KIND)
    assert len(parents) == 2, "a retry must be a NEW job parent, never a reopened epoch"
    assert parents[0]["operation_id"] != parents[1]["operation_id"]
    assert parents[0]["execution_epoch"] == parents[1]["execution_epoch"] == 1
    assert parents[0]["state"] == "FAILED" and parents[1]["state"] == "SUCCEEDED"
    assert json.loads(parents[1]["input_json"])["queue_attempt"] == 2
    assert db.meetings.get_meeting(state.id).intel_status == "ready"


def test_a_returned_error_result_fails_the_base_child_and_keeps_the_queue_vocabulary(tmp_path, monkeypatch):
    """A RETURNED provider error closes its child `failed`, sanitized, and retries.

    The queue's failure vocabulary is unchanged: it still reads the returned
    result's ``.error`` for the owner-facing reason, and the job still takes its
    existing retry path. What changes is the receipt — an attempt the domain
    calls failed can no longer be journaled as `succeeded`.
    """
    db, broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr("holdspeak.intel_queue._routed_plugin_host", lambda enabled: None)
    monkeypatch.setattr(_Cfg.meeting, "intent_router_enabled", False, raising=False)
    state = _queued_meeting(db, "m-error-result")

    from holdspeak.intel_queue import process_next_intel_job

    engine.error = f"the endpoint echoed {SENTINEL}"
    assert process_next_intel_job() is True

    parent = _parents(db, PARENT_KIND)[0]
    assert parent["state"] == "FAILED"
    children = _children(db, parent["operation_id"])
    assert len(children) == 1, "one frozen entry means exactly one attempt"
    receipt = broker.store.receipt(children[0]["operation_id"])
    assert receipt["outcome"] == "failed"
    assert [request.definition_origin.contract for request in requests] == [
        CONTRACT_DEFERRED_ANALYSIS
    ]

    # The queue's own path is untouched: retried, with the provider's reason.
    job = db.intel.get_intel_job(state.id)
    assert job is not None and job.status == "queued" and job.attempts == 1
    assert SENTINEL in str(job.last_error)
    meeting = db.meetings.get_meeting(state.id)
    assert meeting.intel is None and meeting.intel_status != "ready"

    # ...and the sanitized receipt carries no provider text at all.
    for table in ("kernel_receipts", "kernel_operations", "kernel_journal"):
        for row in _rows(db, table):
            assert SENTINEL not in json.dumps(row, default=str)


def test_cancelling_the_job_parent_mid_plugin_writes_no_run_and_no_artifact(tmp_path, monkeypatch):
    db, broker, _engine, host, _requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor",), chain=("requirements_extractor",),
    )
    state = _queued_meeting(db, "m-cancel")

    jobs: list[Any] = []
    from holdspeak.meeting_session.deferred_admission import DeferredIntelJob

    real_admit = DeferredIntelJob.admit

    def capture(cls_db, **kwargs):
        job = real_admit(cls_db, **kwargs)
        jobs.append(job)
        return job

    monkeypatch.setattr(DeferredIntelJob, "admit", classmethod(lambda cls, d, **k: capture(d, **k)))

    def cancel_mid_plugin(plugin_id: str) -> None:
        jobs[0].cancel()

    host.on_execute = cancel_mid_plugin

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    # The provider really ran, and nothing it produced crossed the boundary.
    assert host.executed == ["requirements_extractor"]
    assert _rows(db, "plugin_runs") == []
    assert db.plugins.list_artifacts(state.id) == []
    for stage in _rows(db, "kernel_projection_stages"):
        if str(stage["kind"]) == "meeting-plugin-result":
            assert str(stage["state"]) == "DISCARDED", dict(stage)
    # The job is honestly unresolved, never Ready.
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed.intel_status != "ready"
    assert refreshed.intel_completed_at is None


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
    plugin_requests = [
        request for request in requests
        if request.definition_origin.contract.startswith(CONTRACT_PLUGIN_PREFIX)
    ]
    assert len(plugin_requests) == 1
    # The revision the child NAMES is the revision whose engine ran the plugin:
    # the plan's frozen entry for that plugin capability, and the same revision
    # the base-analysis child used (one placement, one engine).
    parent = _parents(db, PARENT_KIND)[0]
    frozen = json.loads(parent["input_json"])["capabilities"]
    assert plugin_requests[0].deployment_revision == frozen["plugin:requirements_extractor"][0]
    assert plugin_requests[0].deployment_revision == requests[0].deployment_revision
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


def test_the_plugin_provider_call_runs_inside_the_admitted_child_dispatch(tmp_path, monkeypatch):
    """D2: cancelling the job parent mid-plugin cannot publish the plugin's work."""
    db, broker, engine, host, _requests = _queue_rig(
        tmp_path, monkeypatch,
        plugins=("requirements_extractor",), chain=("requirements_extractor",),
    )
    state = _queued_meeting(db, "m-inside")

    jobs: list[Any] = []
    from holdspeak.meeting_session.deferred_admission import DeferredIntelJob

    real_admit = DeferredIntelJob.admit
    monkeypatch.setattr(
        DeferredIntelJob, "admit",
        classmethod(lambda cls, d, **k: jobs.append(real_admit(d, **k)) or jobs[-1]),
    )

    observed: dict[str, Any] = {}

    def observe_then_cancel(plugin_id: str) -> None:
        # While the plugin is executing, its own admitted child is OPEN (no
        # receipt yet) — proof the provider work happens inside the dispatch.
        with db._connection() as conn:
            observed["open"] = [
                dict(row) for row in conn.execute(
                    """SELECT o.native_id FROM kernel_operations o
                       LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id
                       WHERE o.parent_operation_id=? AND o.name='inference.invoke'
                         AND r.operation_id IS NULL""",
                    (jobs[0].parent.operation_id,),
                )
            ]
        observed["engine_bound"] = host.bound_engines[-1] is engine
        jobs[0].cancel()

    host.on_execute = observe_then_cancel

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    assert len(observed["open"]) == 1, observed
    assert observed["engine_bound"] is True
    # Cancelled inside its own dispatch: nothing the plugin produced is durable.
    assert _rows(db, "plugin_runs") == []
    assert db.plugins.list_artifacts(state.id) == []
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed.intel_status != "ready"


# ------------------------------------- D3: the displaced work actually executes


def test_a_stop_displaced_job_runs_the_bookmark_and_title_children(tmp_path, monkeypatch):
    from holdspeak.meeting_session.deferred_admission import (
        CONTRACT_AUTO_TITLE,
        CONTRACT_BOOKMARK_LABEL,
    )
    from holdspeak.meeting_session.intel_plan import (
        CAPABILITY_AUTO_TITLE,
        CAPABILITY_BOOKMARK_LABEL,
        DISPLACED_AUTO_TITLE,
        DISPLACED_BOOKMARK_LABELS,
        DISPLACED_FINAL_ANALYSIS,
    )

    db, broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr("holdspeak.intel_queue._routed_plugin_host", lambda enabled: None)
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

    # The displaced capabilities are FROZEN in this job's plan and each displaced
    # dispatch is one trusted child of the job parent.
    parent = _parents(db, PARENT_KIND)[0]
    snapshot = json.loads(parent["input_json"])
    assert {CAPABILITY_BOOKMARK_LABEL, CAPABILITY_AUTO_TITLE} <= set(snapshot["capabilities"])
    assert snapshot["displaced_work"] == list(job.displaced_work)
    assert [request.definition_origin.contract for request in requests] == [
        CONTRACT_DEFERRED_ANALYSIS, CONTRACT_BOOKMARK_LABEL, CONTRACT_AUTO_TITLE,
    ]
    assert len(_children(db, parent["operation_id"])) == 3
    assert engine.labels and engine.titles

    # The outputs landed through receipt-gated materializers, in the DB.
    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed.title == "Quarterly budget review"
    assert [bookmark.label for bookmark in refreshed.bookmarks] == ["Budget decision"]
    kinds = {
        str(row["kind"]): str(row["state"]) for row in _rows(db, "kernel_projection_stages")
    }
    assert kinds["meeting-deferred-bookmark-label"] == "PUBLISHED"
    assert kinds["meeting-deferred-auto-title"] == "PUBLISHED"
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
    monkeypatch.setattr("holdspeak.intel_queue._routed_plugin_host", lambda enabled: None)
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
    from holdspeak.meeting_session.intel_plan import (
        CAPABILITY_AUTO_TITLE,
        CAPABILITY_BOOKMARK_LABEL,
    )

    db, _broker, engine, _host, requests = _queue_rig(tmp_path, monkeypatch)
    monkeypatch.setattr("holdspeak.intel_queue._routed_plugin_host", lambda enabled: None)
    monkeypatch.setattr(_Cfg.meeting, "intent_router_enabled", False, raising=False)
    state = _queued_meeting(db, "m-normal", title="", bookmarks=(2.0,))

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True

    parent = _parents(db, PARENT_KIND)[0]
    snapshot = json.loads(parent["input_json"])
    assert snapshot["displaced_work"] == []
    assert set(snapshot["capabilities"]) == {CAPABILITY_DEFERRED_ANALYSIS}
    assert CAPABILITY_BOOKMARK_LABEL not in snapshot["capabilities"]
    assert CAPABILITY_AUTO_TITLE not in snapshot["capabilities"]
    assert [request.definition_origin.contract for request in requests] == [
        CONTRACT_DEFERRED_ANALYSIS
    ]
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
