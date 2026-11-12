"""A native Live read recorded through the real hub and runtime producer."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from types import SimpleNamespace
from typing import Any

from tests.integration.test_face_wire_fences import _ok, hub, wire  # noqa: F401


def native_live_state() -> dict:
    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.runtime.activity import RuntimeActivityMixin

    started = datetime.now(timezone.utc) - timedelta(seconds=47)
    state = MeetingState(
        id="m-caught", title="Ledger cutover sync", started_at=started, capture_status="recording",
        segments=[TranscriptSegment(text="I will move the backup job today.", speaker="Priya", start_time=41.0, end_time=46.5)],
        intel=IntelSnapshot(timestamp=47.0, action_items=[ActionItem(task="Move the backup job", owner="Priya")]),
    )
    # The real web-state producer, with only its device/session seam held quiet.
    runtime = RuntimeActivityMixin()
    runtime._active_meeting_session = lambda: SimpleNamespace(state=state, is_active=True)
    runtime.runtime_started_at = started
    runtime.runtime_url = ""
    runtime.state_lock = RLock()
    runtime.runtime_status = {}
    runtime._mir_controls_payload = lambda: {}
    return runtime._get_state()


def test_native_live_state(hub: Any, tmp_path: Path) -> None:
    hub.server.get_state.return_value = native_live_state()
    answer = _ok(hub.client.get("/api/state"))
    assert answer["meeting_active"] is True
    assert answer["intel"]["action_items"][0]["task"] == "Move the backup job"
    wire._fence("live.native-state", answer, tmp_path, str(hub.client.base_url), by="tests/integration/test_native_live_wire.py")


def test_native_live_actions(hub: Any, tmp_path: Path, monkeypatch: Any) -> None:
    """Real mutations, persistence and HTTP replies; capture is held at its edge."""
    from holdspeak.meeting_session import MeetingState, TranscriptSegment, IntelSnapshot
    from holdspeak.intel.models import ActionItem
    from holdspeak.runtime.activity import RuntimeActivityMixin
    from holdspeak.meeting_session.bookmarks import BookmarkViewsMixin
    from holdspeak.meeting_session.mutations import MeetingMutationsMixin
    from holdspeak.meeting_session.persistence import PersistenceMixin
    from holdspeak.runtime.meeting_glue import MeetingGlueMixin
    from holdspeak.runtime.meeting_stop import finish_meeting_stop

    for switch in ("HOLDSPEAK_PHONE", "HOLDSPEAK_TELEGRAM", "HOLDSPEAK_MIC_CHECK", "HOLDSPEAK_RECORDINGS"):
        monkeypatch.setenv(switch, "off")

    class QuietCapture(PersistenceMixin, MeetingMutationsMixin, BookmarkViewsMixin):
        intel_enabled = False
        intel_deferred_enabled = False
        _intel_live = False
        device_cleanup_error = None
        capture_process_exited = True
        _lock = RLock()
        _state = MeetingState(id="m-caught", title="Ledger cutover sync",
            started_at=datetime.now(timezone.utc) - timedelta(seconds=67), capture_status="recording",
            segments=[TranscriptSegment(text="I will move the backup job today.", speaker="Priya", start_time=41.0, end_time=46.5)])
        state = property(lambda self: self._state)
        is_active = property(lambda self: self._state.is_active)
        def _emit_broadcast(self, *_args: Any, **_kwargs: Any) -> None:
            pass
        def stop(self) -> Any:
            # No recorder exists in this rig. Only the physical capture edge
            # is held; the real save and runtime Stop producer run below.
            self._state.ended_at = datetime.now(timezone.utc)
            self._state.capture_status = "finalized"
            return self._state

    capture = QuietCapture()
    class QuietRuntime(MeetingGlueMixin, RuntimeActivityMixin):
        pass
    runtime = QuietRuntime()
    runtime.runtime_started_at = capture.state.started_at
    runtime.runtime_url = ""
    runtime._mir_controls_payload = lambda: {}
    runtime.meeting_session = capture
    runtime.meeting_lock = RLock()
    runtime.state_lock = RLock()
    runtime.runtime_status = {}
    runtime.recording_ticker = SimpleNamespace(stop=lambda: None)
    runtime.device_stats_cycle = {}
    runtime.voice_session = SimpleNamespace(release=lambda _owner: None)
    runtime._set_runtime_activity = lambda *_a, **_k: None
    runtime._flush_deferred_plugin_runs_to_db = lambda: {}
    runtime._persist_pending_mir_history = lambda _id: {}
    runtime._synthesize_and_persist_artifacts = lambda _id: {}
    runtime._associate_meeting_with_projects = lambda _id: {}
    hub.root.meeting_service.bind_lifecycle(
        on_start=lambda: capture.state.to_dict(),
        on_stop=lambda: finish_meeting_stop(runtime, capture, audio_owner="meeting"),
        on_bookmark=runtime._on_bookmark, on_update=runtime._on_update_meeting,
    )
    replies: dict[str, Any] = {"start": _ok(hub.client.post("/api/meeting/start")), "bookmarks": {}, "updates": {}}
    # Replay the transcript producer's real rows into the session; no recorder
    # or speech provider is constructed by this test.
    import json
    rows = json.loads((Path(__file__).resolve().parents[2] / "web/src/test/wire/live.segments.wire.json").read_text())["wire"]
    capture.state.segments = [TranscriptSegment(**row) for row in rows]
    capture.state.intel = IntelSnapshot(timestamp=67, action_items=[ActionItem(task="Move the backup job", owner="Priya")])
    hub.server.get_state.side_effect = runtime._get_state
    replies["state"] = _ok(hub.client.get("/api/state"))
    # The same persistence used by a recording checkpoint gives the running
    # meeting its row. Link it while the capture is still active.
    assert capture.is_active
    assert capture.save().database_saved
    project = _ok(hub.client.post("/api/projects", json={"name": "Payments ledger cutover"}))["project"]
    replies["projects"] = _ok(hub.client.get("/api/projects"))
    replies["project_link"] = _ok(hub.client.post(f"/api/projects/{project['id']}/meetings/m-caught"))
    replies["linked_projects"] = _ok(hub.client.get("/api/meetings/m-caught/projects"))
    assert any(row["project_id"] == project["id"] for row in replies["linked_projects"]["projects"])
    for label in ("The freeze date", "the decision", ""):
        replies["bookmarks"][label] = _ok(hub.client.post("/api/bookmark", json={"label": label}))
    for title in ("First name", "Ledger review", "Ledger cutover sync"):
        replies["updates"][title] = _ok(hub.client.patch("/api/meeting", json={"title": title, "tags": []}))
    replies["stop"] = _ok(hub.client.post("/api/meeting/stop"))
    assert replies["stop"]["save"]["database_saved"] is True
    assert replies["stop"]["save"]["json_saved"] is True
    stored = _ok(hub.client.get("/api/meetings/m-caught?include_parked=true"))
    assert stored["title"] == "Ledger cutover sync"
    assert any(row["label"] == "The freeze date" for row in stored["bookmarks"])
    replies["saved"] = stored
    from holdspeak.runtime.composition import notify_desk_changed
    notify_desk_changed("meeting", "m-caught", "update")
    replies["changed"] = next(data for kind, data in reversed(hub.frames) if kind == "desk_changed")
    next_capture = QuietCapture()
    next_capture._state = MeetingState(id="m-next", title="Next meeting", started_at=datetime.now(timezone.utc),
        capture_status="recording", segments=[TranscriptSegment(text="This belongs to the next meeting.", speaker="Me", start_time=0, end_time=1)])
    runtime.meeting_session = next_capture
    hub.root.meeting_service.bind_lifecycle(on_start=lambda: next_capture.state.to_dict())
    replies["next_start"] = _ok(hub.client.post("/api/meeting/start"))
    replies["next_state"] = _ok(hub.client.get("/api/state"))
    wire._fence("live.actions", replies, tmp_path, str(hub.client.base_url), by="tests/integration/test_native_live_wire.py")
