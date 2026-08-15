"""HS-38-04 — actuator proposals surface from the routing pipeline.

The MIR pipeline calls `on_proposal` with each persisted proposal, and
`record_actuator_proposal` returns that record.

HS-131-17 deleted the session-side half of this file. `MeetingSession` used to
carry an `_emit_actuator_proposal` callback for the dormant post-stop routing
branch it ran itself; both the branch and the callback are gone, so the two tests
that only exercised that callback went with them. The live proposal broadcast
that reaches the dashboard today comes from the aftercare/actuator services
(`tests/integration/test_actuator_presence_broadcasts.py`), which are untouched.
"""

from __future__ import annotations

from datetime import datetime

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.plugins.contracts import PluginRun
from holdspeak.plugins.host import PluginHost
from holdspeak.plugins.persistence import record_actuator_proposal


# ──────────────── 1. record_actuator_proposal returns the record ───────


def _db(tmp_path) -> Database:
    db = Database(tmp_path / "live.db")
    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="t", segments=[])
    )
    return db


def _proposed_run(*, window_id="w1", key="k1") -> PluginRun:
    return PluginRun(
        plugin_id="webhook_post_actuator",
        plugin_version="0.1.0",
        window_id=window_id,
        meeting_id="m1",
        profile="balanced",
        status="proposed",
        idempotency_key=key,
        started_at=0.0,
        finished_at=0.1,
        duration_ms=100.0,
        output={
            "target": "webhook",
            "action": "post_message",
            "preview": "POST a meeting update to hooks.example.test",
            "payload": {"url": "https://hooks.example.test/x", "body": {"text": "hi"}},
            "reversible": False,
            "required_capabilities": ["actuator"],
        },
    )


def test_record_actuator_proposal_returns_persisted_record(tmp_path) -> None:
    db = _db(tmp_path)
    record = record_actuator_proposal(db, _proposed_run())

    assert record is not None
    assert record.id
    assert record.status == "proposed"
    assert record.target == "webhook"
    # It is durably persisted (the saved-meeting surface reads the same row).
    assert db.actuators.get_proposal(record.id).id == record.id


# ──────────── 2. The pipeline invokes on_proposal per proposed run ─────


def _meeting_with_segments() -> MeetingState:
    return MeetingState(
        id="m1",
        started_at=datetime(2026, 6, 4, 10, 0, 0),
        ended_at=datetime(2026, 6, 4, 11, 0, 0),
        title="Pipeline test",
        segments=[
            TranscriptSegment(
                text="Sprint milestone owner deadline planning for the release.",
                speaker="Me",
                start_time=0.0,
                end_time=12.0,
            ),
        ],
    )


def test_pipeline_calls_on_proposal_for_proposed_runs(tmp_path, monkeypatch) -> None:
    import holdspeak.plugins.pipeline as pipeline_mod

    db = _db(tmp_path)
    state = _meeting_with_segments()

    # Force a single `proposed` run out of dispatch (actuators aren't in any
    # chain by default; this isolates the on_proposal wiring from routing).
    def _fake_dispatch_window(host, score, *, window, **kwargs):
        return [_proposed_run(window_id=window.window_id, key=f"k-{window.window_id}")]

    monkeypatch.setattr(pipeline_mod, "dispatch_window", _fake_dispatch_window)

    seen: list[object] = []
    result = pipeline_mod.process_meeting_state(
        state,
        PluginHost(default_timeout_seconds=1.0),
        db=db,
        threshold=0.4,
        on_proposal=seen.append,
    )

    assert result.errors == []
    assert len(seen) >= 1
    # on_proposal receives the persisted proposal record (durable + read-back).
    assert all(getattr(r, "status", None) == "proposed" for r in seen)
    assert db.actuators.get_proposal(seen[0].id).id == seen[0].id


def test_pipeline_without_on_proposal_still_persists(tmp_path, monkeypatch) -> None:
    """The callback is optional — default (no on_proposal) is the byte-identical
    Phase-37 behavior: the proposal persists, nothing broadcasts."""
    import holdspeak.plugins.pipeline as pipeline_mod

    db = _db(tmp_path)
    monkeypatch.setattr(
        pipeline_mod,
        "dispatch_window",
        lambda host, score, *, window, **kwargs: [
            _proposed_run(window_id=window.window_id, key=f"k-{window.window_id}")
        ],
    )

    result = pipeline_mod.process_meeting_state(
        _meeting_with_segments(),
        PluginHost(default_timeout_seconds=1.0),
        db=db,
        threshold=0.4,
    )
    assert result.errors == []
    assert db.actuators.list_proposals("m1")  # persisted, no callback needed


def test_on_proposal_failure_does_not_abort_persistence(tmp_path, monkeypatch) -> None:
    import holdspeak.plugins.pipeline as pipeline_mod

    db = _db(tmp_path)
    monkeypatch.setattr(
        pipeline_mod,
        "dispatch_window",
        lambda host, score, *, window, **kwargs: [
            _proposed_run(window_id=window.window_id, key=f"k-{window.window_id}")
        ],
    )

    def _boom(_record):
        raise RuntimeError("observer down")

    result = pipeline_mod.process_meeting_state(
        _meeting_with_segments(),
        PluginHost(default_timeout_seconds=1.0),
        db=db,
        threshold=0.4,
        on_proposal=_boom,
    )

    # The proposal still persisted; the callback failure is recorded, not raised.
    assert db.actuators.list_proposals("m1")
    assert any("on_proposal" in e for e in result.errors)
