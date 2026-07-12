"""HS-80-01/02/03 — the persisted-meeting plugin-run seam (the Phase-67 F-05 fix).

Imported/saved meetings finally run the routed plugin chain: one full-transcript
window, per-plugin run records, and synthesized typed artifacts — persisted the
same way the live windowed path persists them. These tests run the REAL router,
REAL PluginHost + builtin registry, and a REAL tmp Database; only the LLM is
stubbed (`build_configured_meeting_intel`, the standing pattern).
"""
from __future__ import annotations

from datetime import datetime

import pytest

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.meeting_plugins import run_meeting_plugin_chain
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.plugins.host import PluginRunResult, build_idempotency_key


ARCH_TRANSCRIPT = [
    ("Alex", "Architecture review for the write path. We decided to adopt an "
             "event sourced append log with hourly snapshots and defer sharding."),
    ("Mara", "Action item: I will implement a snapshot reconstruction property "
             "test that proves snapshot plus log tail rebuilds exact balances."),
    ("Priya", "Action item: I own the zero downtime migration plan. Risk: the "
              "reconciliation job may read stale snapshots during cutover."),
]


class _FakeIntel:
    active_provider = "local"

    def __init__(self):
        self.calls = []

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        self.calls.append(user_prompt)
        return "- Decision: adopt event sourcing with hourly snapshots\n- Defer sharding"


@pytest.fixture
def env(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    # intel_queue binds get_database at module level (the Phase-63 patch-target
    # rule): patch where it is LOOKED UP, not where it lives.
    monkeypatch.setattr("holdspeak.intel_queue.get_database", lambda *a, **k: db)
    fake = _FakeIntel()
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_configured_meeting_intel", lambda: fake
    )
    yield db, fake
    reset_database()


def _saved_meeting(db, meeting_id="m80", tags=("architecture",)):
    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 7, 4, 10, 0, 0),
        ended_at=datetime(2026, 7, 4, 10, 30, 0),
        title="Scaling the write path",
        tags=list(tags),
        segments=[
            TranscriptSegment(text=text, speaker=speaker,
                              start_time=float(i * 60), end_time=float(i * 60 + 50))
            for i, (speaker, text) in enumerate(ARCH_TRANSCRIPT)
        ],
    )
    db.meetings.save_meeting(state)
    return db.meetings.get_meeting(meeting_id)


def test_saved_meeting_gets_window_runs_and_artifacts(env) -> None:
    db, _ = env
    meeting = _saved_meeting(db)

    summary = run_meeting_plugin_chain(db, meeting, profile="architect")

    # The route ran under the requested profile with a real chain.
    assert summary["profile"] == "architect"
    assert summary["window_id"] == "m80:full"
    assert summary["plugin_chain"], "the architect profile routes a non-empty chain"

    # Plugin runs persisted for the window (the live path's own record shape).
    runs = db.plugins.list_plugin_runs("m80", limit=100)
    assert runs, "plugin runs must persist"
    assert {r.window_id for r in runs} == {"m80:full"}

    # The window itself persisted with the profile + intents.
    windows = db.plugins.list_intent_windows("m80")
    assert any(w.window_id == "m80:full" and w.profile == "architect" for w in windows)

    # TYPED ARTIFACTS exist — the F-05 fix in one assertion.
    artifacts = db.plugins.list_artifacts("m80")
    assert artifacts, "an imported/saved meeting must synthesize typed artifacts"
    assert summary["artifacts_saved"] == len(artifacts)


def test_rerun_is_idempotent_not_duplicating(env) -> None:
    db, _ = env
    meeting = _saved_meeting(db, meeting_id="m81")

    first = run_meeting_plugin_chain(db, meeting, profile="architect")
    again = run_meeting_plugin_chain(db, meeting, profile="architect")

    # The unchanged transcript dedups at the host (same idempotency keys) and
    # artifact synthesis upserts — no growth on the second pass.
    assert len(db.plugins.list_artifacts("m81")) == first["artifacts_saved"]
    assert any(s == "deduped" for s in again["plugin_statuses"].values()), (
        "an unchanged rerun must dedup, not re-execute"
    )


def test_rerun_executes_only_unresolved_plugin_keys(env) -> None:
    """Retry remaining preserves successful runs and retries the failed key."""
    db, _ = env
    meeting = _saved_meeting(db, meeting_id="m81-partial")

    class _Host:
        def __init__(self, *, fail_first: bool):
            self.fail_first = fail_first
            self.calls = []

        def execute_chain(
            self,
            plugin_chain,
            *,
            context,
            meeting_id,
            window_id,
            transcript_hash,
            defer_heavy,
        ):
            _ = context, defer_heavy
            self.calls.append(list(plugin_chain))
            return [
                PluginRunResult(
                    plugin_id=plugin_id,
                    plugin_version="test",
                    status=(
                        "error"
                        if self.fail_first and index == 0
                        else "success"
                    ),
                    idempotency_key=build_idempotency_key(
                        meeting_id=meeting_id,
                        window_id=window_id,
                        plugin_id=plugin_id,
                        transcript_hash=transcript_hash,
                    ),
                    duration_ms=1.0,
                    output={} if not (self.fail_first and index == 0) else None,
                    error="timeout" if self.fail_first and index == 0 else None,
                )
                for index, plugin_id in enumerate(plugin_chain)
            ]

    first_host = _Host(fail_first=True)
    first = run_meeting_plugin_chain(
        db, meeting, profile="architect", host=first_host
    )
    failed_plugin = first_host.calls[0][0]
    assert first["plugin_statuses"][failed_plugin] == "error"

    retry_host = _Host(fail_first=False)
    retried = run_meeting_plugin_chain(
        db, meeting, profile="architect", host=retry_host
    )

    assert retry_host.calls == [[failed_plugin]]
    assert retried["plugin_statuses"][failed_plugin] == "success"
    assert all(
        status in {"success", "deduped"}
        for status in retried["plugin_statuses"].values()
    )


def test_override_intents_force_the_route(env) -> None:
    db, _ = env
    meeting = _saved_meeting(db, meeting_id="m82", tags=())

    summary = run_meeting_plugin_chain(
        db, meeting, profile="balanced",
        override_intents=["incident"], threshold=0.5,
    )
    assert "incident" in summary["active_intents"]


def test_empty_meeting_raises(env) -> None:
    db, _ = env
    state = MeetingState(id="m83", started_at=datetime(2026, 7, 4, 11, 0, 0), segments=[])
    db.meetings.save_meeting(state)
    meeting = db.meetings.get_meeting("m83")
    with pytest.raises(ValueError):
        run_meeting_plugin_chain(db, meeting, profile="balanced")


def test_deferred_intel_runs_the_chain_when_router_enabled(env, monkeypatch, tmp_path) -> None:
    """HS-80-02: the queue path — after base analyze, artifacts appear."""
    db, _ = env
    meeting = _saved_meeting(db, meeting_id="m84")
    db.intel.enqueue_intel_job(
        "m84", transcript_hash=meeting.transcript_hash(), reason="test import"
    )

    class _Cfg:
        class meeting:  # noqa: N801 - config shape
            intent_router_enabled = True
            mir_profile = "architect"

    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls: _Cfg))

    class _Analyze:
        error = None
        topics = ["write path"]
        action_items = []
        summary = "Adopt event sourcing."

    monkeypatch.setattr(
        "holdspeak.intel.engine.MeetingIntel.analyze",
        lambda self, transcript, stream=False: _Analyze(),
    )
    monkeypatch.setattr(
        "holdspeak.intel_queue.get_intel_runtime_status", lambda *a, **k: (True, "ready")
    )
    monkeypatch.setattr("holdspeak.intel.resolve_llm_capability", lambda cfg: True)

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job(db) is True

    refreshed = db.meetings.get_meeting("m84")
    assert refreshed.intel_status == "ready"
    assert "Meeting intelligence ready" in (refreshed.intel_status_detail or "")
    assert db.plugins.list_artifacts("m84"), "the import path must produce artifacts now"


def test_deferred_intel_retains_base_analysis_when_routed_work_fails(
    env, monkeypatch
) -> None:
    """A routed failure stays partial and recoverable instead of becoming Ready."""
    db, _ = env
    meeting = _saved_meeting(db, meeting_id="m84-partial")
    db.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash=meeting.transcript_hash(),
        reason="test partial routing",
    )

    class _Cfg:
        class meeting:  # noqa: N801 - config shape
            intent_router_enabled = True
            mir_profile = "architect"

    class _Analyze:
        error = None
        topics = ["write path"]
        action_items = []
        summary = "Base analysis retained."

    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls: _Cfg))
    monkeypatch.setattr(
        "holdspeak.intel.engine.MeetingIntel.analyze",
        lambda self, transcript, stream=False: _Analyze(),
    )
    monkeypatch.setattr(
        "holdspeak.intel_queue.get_intel_runtime_status",
        lambda *a, **k: (True, "ready"),
    )
    monkeypatch.setattr(
        "holdspeak.meeting_plugins.run_meeting_plugin_chain",
        lambda *a, **k: {
            "plugin_statuses": {
                "requirements_extractor": "success",
                "risk_heatmap": "timeout",
            },
            "artifacts_saved": 1,
        },
    )

    from holdspeak.intel_queue import process_next_intel_job

    ready = []
    assert process_next_intel_job(db, on_meeting_ready=ready.append) is True

    retained = db.meetings.get_meeting(meeting.id)
    assert retained is not None
    assert retained.intel is not None
    assert retained.intel.summary == "Base analysis retained."
    assert retained.intel_status == "partial"
    assert retained.intel_completed_at is None
    assert "risk_heatmap (timeout)" in (retained.intel_status_detail or "")
    job = db.intel.get_intel_job(meeting.id)
    assert job is not None
    assert job.status == "failed"
    assert db.intel.list_intel_job_attempts(meeting.id)[0].outcome == "partial_failure"
    assert ready == []

    assert db.intel.request_intel_retry(meeting.id) == "queued"

    def fail_if_base_analysis_repeats(*_args, **_kwargs):
        raise AssertionError(
            "Retry remaining must not rerun completed base analysis"
        )

    monkeypatch.setattr(
        "holdspeak.intel.engine.MeetingIntel.analyze",
        fail_if_base_analysis_repeats,
    )
    monkeypatch.setattr(
        "holdspeak.meeting_plugins.run_meeting_plugin_chain",
        lambda *a, **k: {
            "plugin_statuses": {
                "requirements_extractor": "deduped",
                "risk_heatmap": "success",
            },
            "artifacts_saved": 1,
        },
    )

    assert process_next_intel_job(db, on_meeting_ready=ready.append) is True
    completed = db.meetings.get_meeting(meeting.id)
    assert completed is not None
    assert completed.intel_status == "ready"
    assert completed.intel is not None
    assert completed.intel.summary == "Base analysis retained."
    assert db.intel.get_intel_job(meeting.id) is None
    assert ready == [meeting.id]


def test_deferred_intel_skips_the_chain_when_router_disabled(env, monkeypatch) -> None:
    db, _ = env
    meeting = _saved_meeting(db, meeting_id="m85")
    db.intel.enqueue_intel_job(
        "m85", transcript_hash=meeting.transcript_hash(), reason="test import"
    )

    class _Cfg:
        class meeting:  # noqa: N801
            intent_router_enabled = False
            mir_profile = "balanced"

    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls: _Cfg))

    class _Analyze:
        error = None
        topics = []
        action_items = []
        summary = "s"

    monkeypatch.setattr(
        "holdspeak.intel.engine.MeetingIntel.analyze",
        lambda self, transcript, stream=False: _Analyze(),
    )
    monkeypatch.setattr(
        "holdspeak.intel_queue.get_intel_runtime_status", lambda *a, **k: (True, "ready")
    )

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job(db) is True
    assert not db.plugins.list_artifacts("m85"), "router off ⇒ byte-identical import"
