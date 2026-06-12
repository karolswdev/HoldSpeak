"""Meeting session management for HoldSpeak (a package since HS-63-01).

The canonical import point is unchanged: every name that lived on the old
`meeting_session` module is re-exported here. `models` carries the pure
data layer; `session` carries the MeetingSession machinery.
"""

from .models import (
    Bookmark,
    IntelSnapshot,
    MeetingSaveResult,
    MeetingState,
    TranscriptSegment,
    _device_descriptor_to_dict,
    _iso_or_none,
)
from .session import MeetingSession

__all__ = [
    "Bookmark",
    "IntelSnapshot",
    "MeetingSaveResult",
    "MeetingSession",
    "MeetingState",
    "TranscriptSegment",
]
