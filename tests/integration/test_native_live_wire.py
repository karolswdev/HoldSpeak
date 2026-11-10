"""A native Live read recorded through the real hub, with the product producer."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tests.integration.test_face_wire_fences import _ok, hub, wire  # noqa: F401


def test_native_live_state(hub: Any, tmp_path: Path) -> None:
    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    state = MeetingState(
        id="m-caught", title="Ledger cutover sync", started_at=datetime(2026, 11, 9, 18, tzinfo=timezone.utc),
        segments=[TranscriptSegment(text="I will move the backup job today.", speaker="Priya", start_time=41.0, end_time=46.5)],
        intel=IntelSnapshot(timestamp=47.0, action_items=[ActionItem(task="Move the backup job", owner="Priya")]),
    )
    hub.server.get_state.return_value = state.to_dict()
    answer = _ok(hub.client.get("/api/state"))
    assert answer["intel"]["action_items"][0]["task"] == "Move the backup job"
    wire._fence("live.native-state", answer, tmp_path, str(hub.client.base_url), by="tests/integration/test_native_live_wire.py")
