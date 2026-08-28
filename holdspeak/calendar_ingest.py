"""Pure, bounded ICS parsing for the Calendar ingest projection (HS-144-02).

This module deliberately has no file, URL, database, or web dependency.  The
conductor added in the next slice decides when a successfully parsed result is
persisted and how structured skips become kernel receipts.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dateutil.rrule import rrulestr
from icalendar import Calendar


MAX_FEED_BYTES = 5 * 1024 * 1024
MAX_RAW_EVENTS = 2_000
MAX_PROJECTED_EVENTS = 4_000
MAX_OCCURRENCES_PER_MASTER = 128
HORIZON_DAYS = 14


@dataclass(frozen=True)
class CalendarEventCandidate:
    """One normalized calendar occurrence ready for projection persistence."""

    id: str
    uid: str
    title: str
    starts_at: str
    ends_at: str
    location: str | None
    meeting_url: str | None


@dataclass(frozen=True)
class CalendarEventSkip:
    """A content-free reason the conductor can turn into one refusal receipt."""

    event_ref: str
    reason: str


@dataclass(frozen=True)
class ParseResult:
    """A feed-level failure is distinct from recoverable individual skips."""

    events: tuple[CalendarEventCandidate, ...]
    skips: tuple[CalendarEventSkip, ...]
    feed_error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.feed_error is None


class _EventProblem(ValueError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def parse_calendar_bytes(
    raw: bytes,
    *,
    now: datetime,
    subscription_revision: str,
) -> ParseResult:
    """Parse one bounded ICS feed into UTC occurrence candidates.

    The function has one untrusted-input boundary: invalid bytes or an invalid
    calendar return ``feed_error``; one malformed VEVENT becomes a structured
    skip while its valid siblings remain usable.  No caller-visible exception
    is used to represent calendar data failure.
    """
    if not isinstance(raw, bytes):
        return ParseResult((), (), "calendar_feed_invalid_bytes")
    if len(raw) > MAX_FEED_BYTES:
        return ParseResult((), (), "calendar_feed_too_large")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return ParseResult((), (), "calendar_feed_invalid_utf8")
    try:
        calendar = Calendar.from_ical(raw)
    except Exception:
        return ParseResult((), (), "calendar_feed_parse_failed")
    if getattr(calendar, "name", "") != "VCALENDAR":
        return ParseResult((), (), "calendar_feed_not_vcalendar")

    window_start = _as_utc(now)
    window_end = window_start + timedelta(days=HORIZON_DAYS)
    candidates: list[CalendarEventCandidate] = []
    skips: list[CalendarEventSkip] = []
    try:
        events = calendar.walk("VEVENT")
    except Exception:
        return ParseResult((), (), "calendar_feed_component_walk_failed")

    for ordinal, event in enumerate(events):
        if ordinal >= MAX_RAW_EVENTS:
            skips.append(CalendarEventSkip("feed", "calendar_event_skipped_raw_event_cap"))
            break
        try:
            parsed_events, event_skips = _parse_event(
                event,
                ordinal=ordinal,
                window_start=window_start,
                window_end=window_end,
                subscription_revision=subscription_revision,
            )
        except Exception:
            # icalendar/dateutil property access can surface a malformed value
            # lazily.  Keep that component from taking down siblings or boot.
            event_ref = _event_ref(event, ordinal)
            parsed_events = []
            event_skips = [
                CalendarEventSkip(event_ref, "calendar_event_skipped_invalid_component")
            ]
        skips.extend(event_skips)
        remaining = MAX_PROJECTED_EVENTS - len(candidates)
        if remaining <= 0:
            skips.append(CalendarEventSkip("feed", "calendar_event_skipped_projection_cap"))
            break
        candidates.extend(parsed_events[:remaining])
        if len(parsed_events) > remaining:
            skips.append(CalendarEventSkip("feed", "calendar_event_skipped_projection_cap"))
            break

    return ParseResult(tuple(candidates), tuple(skips))


def _parse_event(
    event: Any,
    *,
    ordinal: int,
    window_start: datetime,
    window_end: datetime,
    subscription_revision: str,
) -> tuple[list[CalendarEventCandidate], list[CalendarEventSkip]]:
    event_ref = _event_ref(event, ordinal)
    if event.get("RECURRENCE-ID") is not None:
        return [], [
            CalendarEventSkip(
                event_ref, "calendar_event_skipped_unsupported_recurrence_override"
            )
        ]
    uid = str(event.get("UID") or "").strip()
    if not uid:
        return [], [CalendarEventSkip(event_ref, "calendar_event_skipped_invalid_uid")]

    try:
        starts_at = _property_datetime(event, "DTSTART", required=True)
        ends_at = _event_end(event, starts_at)
    except _EventProblem as exc:
        return [], [CalendarEventSkip(uid, exc.reason)]
    if ends_at <= starts_at:
        return [], [CalendarEventSkip(uid, "calendar_event_skipped_invalid_duration")]

    duration = ends_at.astimezone(timezone.utc) - starts_at.astimezone(timezone.utc)
    if duration <= timedelta(0):
        return [], [CalendarEventSkip(uid, "calendar_event_skipped_invalid_duration")]

    try:
        occurrences, recurrence_skips = _event_occurrences(
            event,
            starts_at=starts_at,
            window_start=window_start,
            window_end=window_end,
            event_ref=uid,
        )
    except _EventProblem as exc:
        return [], [CalendarEventSkip(uid, exc.reason)]

    title = str(event.get("SUMMARY") or "").strip()
    location = _optional_text(event, "LOCATION")
    meeting_url = _optional_text(event, "URL")
    output: list[CalendarEventCandidate] = []
    for occurrence in occurrences:
        utc_start = occurrence.astimezone(timezone.utc)
        if not (window_start <= utc_start < window_end):
            continue
        utc_end = utc_start + duration
        starts_iso = _utc_iso(utc_start)
        output.append(
            CalendarEventCandidate(
                id=_projection_id(subscription_revision, uid, starts_iso),
                uid=uid,
                title=title,
                starts_at=starts_iso,
                ends_at=_utc_iso(utc_end),
                location=location,
                meeting_url=meeting_url,
            )
        )
    return output, recurrence_skips


def _event_occurrences(
    event: Any,
    *,
    starts_at: datetime,
    window_start: datetime,
    window_end: datetime,
    event_ref: str,
) -> tuple[list[datetime], list[CalendarEventSkip]]:
    rrule = event.get("RRULE")
    rdate_values = _date_list_values(event, "RDATE")
    if rrule is None and not rdate_values:
        return [starts_at], []

    occurrences: list[datetime]
    if rrule is None:
        occurrences = [starts_at]
    else:
        frequency = _rrule_frequency(rrule)
        # Seconds/minutes rules can place an unbounded amount of work before
        # dateutil reaches a far-future ``now``. Meetings do not need this
        # granularity; refusing them is safer than a wall-clock timeout.
        if frequency in {"SECONDLY", "MINUTELY"}:
            raise _EventProblem("calendar_event_skipped_unsupported_rrule_frequency")
        try:
            rule_text = rrule.to_ical().decode("utf-8")
            rule = rrulestr(rule_text, dtstart=starts_at)
            occurrences = []
            for occurrence in rule.xafter(
                window_start, count=MAX_OCCURRENCES_PER_MASTER + 1, inc=True
            ):
                if occurrence >= window_end:
                    break
                occurrences.append(_require_aware_datetime(occurrence, "rrule"))
        except _EventProblem:
            raise
        except Exception as exc:
            raise _EventProblem("calendar_event_skipped_invalid_rrule") from exc

    try:
        rdates = _normalized_date_list(rdate_values, "rdate")
        exdates = set(_normalized_date_list(_date_list_values(event, "EXDATE"), "exdate"))
    except _EventProblem:
        raise

    occurrences.extend(rdates)
    unique = {
        value.astimezone(timezone.utc): value
        for value in occurrences
        if window_start <= value.astimezone(timezone.utc) < window_end
        and value.astimezone(timezone.utc) not in exdates
    }
    ordered = [unique[key] for key in sorted(unique)]
    skips: list[CalendarEventSkip] = []
    if len(ordered) > MAX_OCCURRENCES_PER_MASTER:
        ordered = ordered[:MAX_OCCURRENCES_PER_MASTER]
        skips.append(
            CalendarEventSkip(event_ref, "calendar_event_skipped_occurrence_cap")
        )
    return ordered, skips


def _rrule_frequency(rule: Any) -> str:
    try:
        values = rule.get("FREQ", [])
        value = values[0] if isinstance(values, list) and values else values
        return str(value or "").upper()
    except Exception:
        return ""


def _event_end(event: Any, starts_at: datetime) -> datetime:
    if event.get("DTEND") is not None:
        return _property_datetime(event, "DTEND", required=True)
    duration_property = event.get("DURATION")
    if duration_property is None:
        raise _EventProblem("calendar_event_skipped_invalid_dtend")
    duration = getattr(duration_property, "dt", None)
    if not isinstance(duration, timedelta):
        raise _EventProblem("calendar_event_skipped_invalid_duration")
    return starts_at + duration


def _property_datetime(event: Any, name: str, *, required: bool) -> datetime:
    value = event.get(name)
    if value is None:
        if required:
            raise _EventProblem(
                "calendar_event_skipped_invalid_dtstart"
                if name == "DTSTART"
                else "calendar_event_skipped_invalid_dtend"
            )
        raise _EventProblem("calendar_event_skipped_invalid_component")
    decoded = getattr(value, "dt", None)
    if isinstance(decoded, date) and not isinstance(decoded, datetime):
        raise _EventProblem("calendar_event_skipped_unsupported_date_only")
    if not isinstance(decoded, datetime):
        raise _EventProblem(
            "calendar_event_skipped_invalid_dtstart"
            if name == "DTSTART"
            else "calendar_event_skipped_invalid_dtend"
        )
    if decoded.tzinfo is None:
        tzid = str(getattr(value, "params", {}).get("TZID", "") or "").strip()
        if tzid:
            try:
                decoded = decoded.replace(tzinfo=ZoneInfo(tzid))
            except (ZoneInfoNotFoundError, ValueError) as exc:
                raise _EventProblem("calendar_event_skipped_unresolvable_tzid") from exc
        else:
            raise _EventProblem("calendar_event_skipped_floating_time")
    return decoded


def _date_list_values(event: Any, name: str) -> list[Any]:
    try:
        value = event.get(name)
    except Exception as exc:
        raise _EventProblem(f"calendar_event_skipped_invalid_{name.lower()}") from exc
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    flattened: list[Any] = []
    for item in values:
        dts = getattr(item, "dts", None)
        if dts is None:
            raise _EventProblem(f"calendar_event_skipped_invalid_{name.lower()}")
        flattened.extend(dts)
    return flattened


def _normalized_date_list(values: Iterable[Any], kind: str) -> list[datetime]:
    normalized: list[datetime] = []
    for value in values:
        decoded = getattr(value, "dt", None)
        if isinstance(decoded, date) and not isinstance(decoded, datetime):
            raise _EventProblem(f"calendar_event_skipped_invalid_{kind}")
        if not isinstance(decoded, datetime):
            raise _EventProblem(f"calendar_event_skipped_invalid_{kind}")
        try:
            normalized.append(_require_aware_datetime(decoded, kind).astimezone(timezone.utc))
        except _EventProblem:
            raise
    return normalized


def _require_aware_datetime(value: datetime, kind: str) -> datetime:
    if value.tzinfo is None:
        raise _EventProblem(f"calendar_event_skipped_invalid_{kind}")
    return value


def _optional_text(event: Any, name: str) -> str | None:
    value = event.get(name)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _event_ref(event: Any, ordinal: int) -> str:
    try:
        uid = str(event.get("UID") or "").strip()
    except Exception:
        uid = ""
    return uid or f"event:{ordinal + 1}"


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _projection_id(subscription_revision: str, uid: str, starts_at: str) -> str:
    digest = hashlib.sha256(
        f"{subscription_revision}\0{uid}\0{starts_at}".encode("utf-8")
    ).hexdigest()
    return f"ce_{digest}"
