"""HS-38-04 — live in-meeting actuator proposals + broadcast.

When an actuator proposes during a (finalizing) meeting, the proposal is surfaced
**live**: the MIR pipeline calls `on_proposal`, the `MeetingSession` turns that into
an `actuator_proposed` broadcast, and the dashboard shows it in a pending-actions
panel (approve/reject reuses the Phase-37 decision endpoint — no execution here).

These tests pin the two backend contracts:
  1. the broadcast payload is **read-only** — id + lifecycle + preview only, never
     the egress `payload`/`result`/`error`;
  2. the pipeline invokes `on_proposal` with the persisted proposal for each
     `proposed` run (and `record_actuator_proposal` returns that record).
"""

from __future__ import annotations

import types
from datetime import datetime

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingSession, MeetingState, TranscriptSegment
from holdspeak.plugins.contracts import PluginRun
from holdspeak.plugins.host import PluginHost
from holdspeak.plugins.persistence import record_actuator_proposal


class _FakeTranscriber:
    def transcribe(self, audio) -> str:  # pragma: no cover - unused
        _ = audio
        return ""


# ──────────────────── 1. The broadcast is read-only ───────────────────


def test_emit_actuator_proposal_broadcasts_read_only_view() -> None:
    events: list[tuple[str, object]] = []
    session = MeetingSession(
        transcriber=_FakeTranscriber(),
        on_broadcast=lambda mt, data: events.append((mt, data)),
    )

    record = types.SimpleNamespace(
        id="p1",
        meeting_id="m1",
        plugin_id="github_issue_actuator",
        status="proposed",
        target="github",
        action="create_issue",
        preview="Open a GitHub issue in acme/app",
        reversible=False,
        created_at=datetime(2026, 6, 4, 12, 0, 0),
        # The egress source-of-truth + execution fields — must NOT be broadcast.
        payload={"repo": "acme/app", "title": "secret"},
        result={"url": "x"},
        error=None,
    )

    session._emit_actuator_proposal(record)

    assert len(events) == 1
    message_type, data = events[0]
    assert message_type == "actuator_proposed"
    assert data == {
        "id": "p1",
        "meeting_id": "m1",
        "plugin_id": "github_issue_actuator",
        "status": "proposed",
        "target": "github",
        "action": "create_issue",
        "preview": "Open a GitHub issue in acme/app",
        "reversible": False,
        "created_at": "2026-06-04T12:00:00",  # serialized for json.dumps on the wire
    }
    # The egress payload (and result/error) never reach a live client.
    assert "payload" not in data
    assert "result" not in data
    assert "error" not in data


def test_emit_without_observer_is_silent() -> None:
    session = MeetingSession(transcriber=_FakeTranscriber())  # no on_broadcast
    record = types.SimpleNamespace(
        id="p1", meeting_id="m1", plugin_id="a", status="proposed",
        target="webhook", action="post_message", preview="x", reversible=False,
        created_at=None,
    )
    session._emit_actuator_proposal(record)  # no observer → no-op, no raise


# ──────────────── 2. record_actuator_proposal returns the record ───────


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


# ──────────── 3. The pipeline invokes on_proposal per proposed run ─────


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
