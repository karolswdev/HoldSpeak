"""Local meeting-candidate extraction from activity records."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional
from urllib.parse import unquote

from .db import ActivityRecord

CALENDAR_CONNECTOR_ID = "calendar_activity"

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

DATE_TIME_RE = re.compile(
    r"\b(?P<date>\d{4}-\d{2}-\d{2})[T ]+"
    r"(?P<start>\d{1,2}:\d{2})"
    r"(?:\s*(?:-|to)\s*(?P<end>\d{1,2}:\d{2}))?\b",
    re.IGNORECASE,
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
    source_connector_id: str = CALENDAR_CONNECTOR_ID,
    limit: int = 50,
) -> list[ActivityMeetingCandidatePreview]:
    """Derive meeting-candidate previews from existing local activity records."""
    previews: list[ActivityMeetingCandidatePreview] = []
    for record in records:
        if not _is_calendar_record(record):
            continue
        title = _candidate_title(record)
        starts_at, ends_at = _candidate_time_hints(record)
        previews.append(
            ActivityMeetingCandidatePreview(
                title=title,
                starts_at=starts_at,
                ends_at=ends_at,
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


def _candidate_time_hints(record: ActivityRecord) -> tuple[Optional[datetime], Optional[datetime]]:
    text = f"{record.title or ''} {unquote(record.url or '')}"
    match = DATE_TIME_RE.search(text)
    if match is None:
        return None, None
    try:
        starts_at = datetime.fromisoformat(f"{match.group('date')}T{match.group('start')}:00")
        end_text = match.group("end")
        if not end_text:
            return starts_at, None
        ends_at = datetime.fromisoformat(f"{match.group('date')}T{end_text}:00")
        if ends_at < starts_at:
            ends_at += timedelta(days=1)
        return starts_at, ends_at
    except ValueError:
        return None, None
