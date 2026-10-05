"""The macOS Calendar app as a calendar source (EventKit; owner ruling 2026-10-05).

"Strong defaults, batteries included": a Mac user already has his calendars in
Calendar.app (iCloud, Google, Exchange accounts added in System Settings).
HoldSpeak reads them through EventKit, the system's own calendar API, with the
macOS Calendars permission.  No file under ``~/Library/Calendars`` is read.

The permission rules:

* :func:`access_state` reads the permission and never prompts.  Boot,
  detection and the conductor only ever call this.
* :func:`request_access` shows the macOS prompt.  Only the owner's explicit
  call reaches it (``POST /api/onboarding/calendar/macos/access``).
* Without full access, :func:`list_calendars` returns nothing and
  :func:`read_calendar_ics` raises ``calendar_source_permission``.

A source is stored as ``eventkit:<calendarIdentifier>`` in
``calendar.sources``.  The ingest conductor reads it through
:func:`read_calendar_ics`, which renders the next days of that calendar as
ICS bytes, so the one ICS parser and projection serve it like any feed.  No
network request is made by HoldSpeak; the system syncs the accounts.

EventKit is loaded through PyObjC's core (installed on macOS with ``pynput``,
a base dependency) by bundle path; no extra framework wrapper is needed.  The
two completion-block signatures are registered here.
"""
from __future__ import annotations

import re
import sys
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from .logging_config import get_logger

log = get_logger("macos_calendar")

SCHEME = "eventkit:"
EVENTKIT_PATH = "/System/Library/Frameworks/EventKit.framework"
ENTITY_EVENT = 0  # EKEntityTypeEvent

#: EKAuthorizationStatus -> the state the API returns.
STATES = {
    0: "not_determined",
    1: "restricted",
    2: "denied",
    3: "full_access",
    4: "write_only",
}
#: EKCalendarType -> kind.
CALENDAR_KINDS = {0: "local", 1: "caldav", 2: "exchange", 3: "subscription", 4: "birthday"}

_MEETING_LINK = re.compile(
    r"https://[^\s<>\"']*(?:zoom\.us|teams\.microsoft\.com|meet\.google\.com|webex\.com|whereby\.com)[^\s<>\"']*",
    re.IGNORECASE,
)

_lock = threading.Lock()
_classes: Optional[dict[str, Any]] = None
_store: Any = None


def _eventkit() -> Optional[dict[str, Any]]:
    """The EventKit classes, or None off macOS or without PyObjC."""
    global _classes
    if sys.platform != "darwin":
        return None
    with _lock:
        if _classes is not None:
            return _classes or None
        try:
            import objc
            from Foundation import NSBundle, NSDate

            bundle = NSBundle.bundleWithPath_(EVENTKIT_PATH)
            if bundle is None or not bundle.load():
                _classes = {}
                return None
            completion = {
                "callable": {
                    "retval": {"type": b"v"},
                    "arguments": {0: {"type": b"^v"}, 1: {"type": b"Z"}, 2: {"type": b"@"}},
                }
            }
            for selector, index in (
                (b"requestFullAccessToEventsWithCompletion:", 2),
                (b"requestAccessToEntityType:completion:", 3),
            ):
                objc.registerMetaDataForSelector(
                    b"EKEventStore", selector, {"arguments": {index: completion}},
                )
            _classes = {
                "EKEventStore": objc.lookUpClass("EKEventStore"),
                "NSDate": NSDate,
            }
        except Exception as exc:  # pragma: no cover - environment-dependent
            log.info("EventKit is not available: %s", exc)
            _classes = {}
            return None
        return _classes


def available() -> bool:
    return _eventkit() is not None


def access_state() -> str:
    """The Calendars permission for this process.  Never prompts."""
    kit = _eventkit()
    if kit is None:
        return "unavailable"
    try:
        status = int(kit["EKEventStore"].authorizationStatusForEntityType_(ENTITY_EVENT))
    except Exception as exc:  # pragma: no cover - environment-dependent
        log.info("EventKit status read failed: %s", exc)
        return "unavailable"
    return STATES.get(status, "unknown")


def _event_store() -> Any:
    global _store
    kit = _eventkit()
    if kit is None:
        return None
    if _store is None:
        _store = kit["EKEventStore"].alloc().init()
    return _store


def request_access(timeout: float = 120.0) -> str:
    """Show the macOS Calendars prompt (the owner's explicit call only).

    Returns the state after his answer, or ``"pending"`` when he has not
    answered within ``timeout`` seconds.
    """
    store = _event_store()
    if store is None:
        return "unavailable"
    if access_state() in {"full_access", "restricted", "denied"}:
        return access_state()
    answered = threading.Event()

    def _done(granted: bool, error: Any) -> None:
        if error is not None:
            log.info("Calendars permission request answered with an error: %s", error)
        answered.set()

    if store.respondsToSelector_(b"requestFullAccessToEventsWithCompletion:"):
        store.requestFullAccessToEventsWithCompletion_(_done)
    else:  # macOS 13 and older
        store.requestAccessToEntityType_completion_(ENTITY_EVENT, _done)
    if not answered.wait(timeout):
        return "pending"
    global _store
    _store = None  # a fresh store sees the new permission
    return access_state()


def list_calendars() -> list[dict[str, Any]]:
    """Every event calendar Calendar.app shows (needs full access)."""
    if access_state() != "full_access":
        return []
    store = _event_store()
    out: list[dict[str, Any]] = []
    for calendar in store.calendarsForEntityType_(ENTITY_EVENT) or []:
        try:
            kind = CALENDAR_KINDS.get(int(calendar.type()), "other")
            source = calendar.source()
            out.append({
                "id": str(calendar.calendarIdentifier()),
                "title": str(calendar.title() or ""),
                "account": str(source.title() or "") if source is not None else "",
                "kind": kind,
            })
        except Exception as exc:  # one odd calendar never hides the rest
            log.debug("calendar skipped: %s", exc)
    out.sort(key=lambda c: (c["kind"] == "birthday", c["account"].lower(), c["title"].lower()))
    return out


def _to_utc(nsdate: Any) -> datetime:
    return datetime.fromtimestamp(float(nsdate.timeIntervalSince1970()), tz=timezone.utc)


def _meeting_url(event: Any) -> str:
    url = event.URL()
    if url is not None:
        text = str(url.absoluteString() or "")
        if text.lower().startswith("https://"):
            return text
    for text in (event.location(), event.notes()):
        match = _MEETING_LINK.search(str(text or ""))
        if match:
            return match.group(0)
    return ""


def events_as_ics(events: list[dict[str, Any]], *, calendar_name: str = "") -> bytes:
    """Render event dicts (``uid``, ``title``, ``start``, ``end``, ...) as ICS bytes."""
    from icalendar import Calendar, Event, vCalAddress

    cal = Calendar()
    cal.add("prodid", "-//HoldSpeak//macOS Calendar//EN")
    cal.add("version", "2.0")
    if calendar_name:
        cal.add("x-wr-calname", calendar_name)
    for item in events:
        event = Event()
        event.add("uid", item["uid"])
        event.add("dtstart", item["start"])
        event.add("dtend", item["end"])
        event.add("summary", item.get("title") or "")
        if item.get("location"):
            event.add("location", item["location"])
        if item.get("url"):
            event.add("url", item["url"])
        for email in item.get("attendees") or ():
            event.add("attendee", vCalAddress(f"mailto:{email}"), encode=0)
        cal.add_component(event)
    return cal.to_ical()


def read_calendar_ics(source: str, *, now: Optional[datetime] = None, days: int = 15) -> bytes:
    """One ``eventkit:<id>`` source as ICS bytes: the next ``days`` days."""
    from .calendar_ingest_conductor import CalendarSourceError

    calendar_id = str(source or "")[len(SCHEME):].strip()
    if not calendar_id:
        raise CalendarSourceError("calendar_source_invalid")
    state = access_state()
    if state == "unavailable":
        raise CalendarSourceError("calendar_source_unavailable")
    if state != "full_access":
        raise CalendarSourceError("calendar_source_permission")
    kit = _eventkit()
    store = _event_store()
    calendar = store.calendarWithIdentifier_(calendar_id)
    if calendar is None:
        raise CalendarSourceError("calendar_source_missing")
    start = (now or datetime.now(timezone.utc)) - timedelta(days=1)
    end = start + timedelta(days=days + 1)
    ns_date = kit["NSDate"]
    predicate = store.predicateForEventsWithStartDate_endDate_calendars_(
        ns_date.dateWithTimeIntervalSince1970_(start.timestamp()),
        ns_date.dateWithTimeIntervalSince1970_(end.timestamp()),
        [calendar],
    )
    events: list[dict[str, Any]] = []
    for event in store.eventsMatchingPredicate_(predicate) or []:
        try:
            if bool(event.isAllDay()):
                continue  # the ICS parser skips date-only events too
            uid = str(event.calendarItemExternalIdentifier() or event.eventIdentifier() or "")
            if not uid:
                continue
            attendees = []
            for participant in event.attendees() or []:
                url = participant.URL()
                text = str(url.absoluteString() or "") if url is not None else ""
                if text.lower().startswith("mailto:"):
                    attendees.append(text[7:].lower())
            events.append({
                "uid": uid,
                "title": str(event.title() or ""),
                "start": _to_utc(event.startDate()),
                "end": _to_utc(event.endDate()),
                "location": str(event.location() or ""),
                "url": _meeting_url(event),
                "attendees": attendees,
            })
        except Exception as exc:  # one odd event never hides the rest
            log.debug("event skipped: %s", exc)
    return events_as_ics(events, calendar_name=str(calendar.title() or ""))
