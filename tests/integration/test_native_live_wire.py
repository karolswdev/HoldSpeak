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
