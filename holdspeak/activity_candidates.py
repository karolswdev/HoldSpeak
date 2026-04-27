"""Local meeting-candidate extraction from activity records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from .db import ActivityRecord

CALENDAR_DOMAINS = frozenset(
    {
        "calendar.google.com",
        "meet.google.com",
        "outlook.live.com",
        "outlook.office.com",
        "outlook.office365.com",
        "teams.microsoft.com",
    }
)


@dataclass(frozen=True)
class ActivityMeetingCandidatePreview:
    """Preview of a meeting candidate derived from local activity only."""

    title: str
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    meeting_url: str
    source_activity_record_id: int
    source_connector_id: str
    confidence: float


def preview_calendar_meeting_candidates(
    records: Iterable[ActivityRecord],
    *,
    source_connector_id: str = "calendar_activity",
    limit: int = 50,
) -> list[ActivityMeetingCandidatePreview]:
    """Derive meeting-candidate previews from existing local activity records."""
    previews: list[ActivityMeetingCandidatePreview] = []
    for record in records:
        if not _is_calendar_record(record):
            continue
        title = _candidate_title(record)
        previews.append(
            ActivityMeetingCandidatePreview(
                title=title,
                starts_at=None,
                ends_at=None,
                meeting_url=record.url,
                source_activity_record_id=record.id,
                source_connector_id=source_connector_id,
                confidence=_candidate_confidence(record),
            )
        )
        if len(previews) >= max(1, min(int(limit), 500)):
            break
    return previews


def _is_calendar_record(record: ActivityRecord) -> bool:
    domain = str(record.domain or "").strip().lower()
    if domain in CALENDAR_DOMAINS:
        return True
    return any(domain.endswith(f".{candidate}") for candidate in CALENDAR_DOMAINS)


def _candidate_title(record: ActivityRecord) -> str:
    title = str(record.title or "").strip()
    if title:
        return title
    if "teams.microsoft.com" in record.domain:
        return "Microsoft Teams meeting"
    if "meet.google.com" in record.domain:
        return "Google Meet meeting"
    if "outlook" in record.domain:
        return "Outlook calendar event"
    return "Calendar event"


def _candidate_confidence(record: ActivityRecord) -> float:
    title = str(record.title or "").lower()
    if "meeting" in title or "calendar" in title:
        return 0.75
    if "teams.microsoft.com" in record.domain or "meet.google.com" in record.domain:
        return 0.7
    return 0.55
