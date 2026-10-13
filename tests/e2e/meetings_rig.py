"""A meeting saved by the real producer, for the browser rigs.

The desk sweep (tests/e2e/test_desk_sweep.py) seeds with it, and so does the
Meetings glass (tests/e2e/test_meetings_glass.py). It lived in the PHILO-17
meeting-window glass, now parked (tests/e2e/_parked/test_philo17_meeting_window_glass.py).
"""
from __future__ import annotations

from datetime import datetime, timedelta


def _save_meeting(meeting_id: str, title: str, hours_ago: float, intel_status: str) -> None:
    """A meeting saved by the real producer (MeetingState -> save_meeting)."""
    from holdspeak.db import get_database
    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    start = (datetime.now() - timedelta(hours=hours_ago)).replace(microsecond=0)
    get_database().meetings.save_meeting(MeetingState(
        id=meeting_id, started_at=start, ended_at=start + timedelta(minutes=30), title=title,
        segments=[TranscriptSegment(text="We move the cutover to Friday.", speaker="Me", start_time=1.0, end_time=4.0),
                  TranscriptSegment(text="Agreed.", speaker="Avery", start_time=4.0, end_time=5.0)],
        intel_status=intel_status))
