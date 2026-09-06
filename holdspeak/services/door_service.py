"""The Dashboard Door's composed, transport-neutral read model."""
from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from typing import TYPE_CHECKING, Any, Callable

from ..config.integrations import validate_calendar_subscription
from ..db.calendar_events import CalendarEvent, CalendarEventRepository
from ..db.scheduled_recordings import ScheduledRecording, ScheduledRecordingRepository
from .follow_through_service import FollowThroughBoard, FollowThroughCard, FollowThroughService
from .refinement_thought_service import RefinementThoughtService

if TYPE_CHECKING:
    from .people_service import PeopleService


class DoorService:
    def __init__(
        self,
        follow_through_service: FollowThroughService,
        refinement_thought_service: RefinementThoughtService,
        scheduled_recordings: ScheduledRecordingRepository,
        calendar_events: CalendarEventRepository,
        *,
        db: Any = None,
        clock: Callable[[], datetime] | None = None,
        config_loader: Callable[[], Any] | None = None,
        people_service: PeopleService | None = None,
        local_tz: tzinfo | None = None,
    ) -> None:
        self._follow_through_service = follow_through_service
        self._refinement_thought_service = refinement_thought_service
        self._scheduled_recordings = scheduled_recordings
        self._calendar_events = calendar_events
        self._db = db
        self._clock = clock or (lambda: datetime.now().astimezone())
        self._config_loader = config_loader
        self._people_service = people_service
        # HS-175 C8: the desk's clock. The hub's local zone by default
        # (``datetime.now().astimezone()``); injectable for the -06:00 tests.
        self._local_tz = local_tz

    def add_item(
        self,
        principal: Any,
        task: str,
        *,
        owner: str | None = None,
        due: str | None = None,
        source_type: str = "meeting",
        source_ref: str = "",
    ) -> dict[str, Any]:
        """Add an action item to the Door (HS-153-05).

        Returns the created action item as a dict.
        """
        if self._db is None:
            raise RuntimeError("DoorService requires a db for add_item")
        if not task or not task.strip():
            from .errors import ServiceError
            raise ServiceError(
                "door_add_item_invalid",
                "Task text must not be empty.",
                context={"status": 400},
            )
        item_id = "ai_" + uuid.uuid4().hex
        now = datetime.now().isoformat()
        delegated_at = now if owner else None
        with self._db._connection() as conn:
            conn.execute(
                """INSERT INTO action_items
                   (id, meeting_id, task, owner, due, status, review_state,
                    created_at, delegated_at, source_type, source_ref)
                   VALUES (?, NULL, ?, ?, ?, 'open', 'accepted', ?, ?, ?, ?)""",
                (
                    item_id,
                    task.strip(),
                    owner,
                    due,
                    now,
                    delegated_at,
                    source_type,
                    source_ref,
                ),
            )
        return {
            "id": item_id,
            "task": task.strip(),
            "owner": owner,
            "due": due,
            "status": "open",
            "source_type": source_type,
            "source_ref": source_ref,
        }

    def has_item_for_source(self, source_ref: str) -> bool:
        """True if any Door action item already references source_ref.

        The Steward's "lacking canonical follow-through" read (HS-163-03).
        """
        if self._db is None or not source_ref:
            return False
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM action_items WHERE source_ref = ? LIMIT 1",
                (source_ref,),
            ).fetchone()
        return row is not None

    def get(self, principal: Any) -> dict[str, Any]:
        now = self._clock()
        if now.tzinfo is None:
            now = now.astimezone()
        now_utc = now.astimezone(timezone.utc)
        board = self._follow_through_service.board(principal)
        # HS-150-02: resolve mapped owner strings to person labels.
        owner_person_index = self._build_owner_person_index(board)
        projected_board = {
            "now": [self._follow_through_card(card, owner_person_index=owner_person_index) for card in board.now],
            "waiting": [self._follow_through_card(card, owner_person_index=owner_person_index) for card in board.waiting],
            "unassigned": [self._follow_through_card(card, owner_person_index=owner_person_index) for card in board.unassigned],
            "overdue": [self._follow_through_card(card, owner_person_index=owner_person_index) for card in board.overdue],
            "active": self._active_thoughts(principal),
        }
        upcoming = self._upcoming(now_utc)
        has_calendar = self._calendar_configured()
        result: dict[str, Any] = {
            "board": projected_board,
            "upcoming": upcoming,
            "counts": {
                "overdue": len(projected_board["overdue"]),
                "now": len(projected_board["now"]),
                "waiting": len(projected_board["waiting"]),
                "active": len(projected_board["active"]),
                "upcoming_today": self._upcoming_today(upcoming, now),
            },
            "calendar_configured": has_calendar,
            "week": self._week_strip(now_utc, has_calendar),
        }
        # L2 (HS-149-01): carry the People store state so the Door never
        # renders a broken/locked/absent sidecar as silent emptiness.
        people_state = self._follow_through_service.people_store_state(principal)
        if people_state is not None:
            result["people_store_state"] = people_state
        return result

    def _calendar_configured(self) -> bool:
        """HS-146-01: True iff at least one enabled source passes validation."""
        if self._config_loader is None:
            return False
        try:
            config = self._config_loader()
            for source in config.calendar.sources:
                if source.enabled and validate_calendar_subscription(source.url):
                    return True
            return False
        except Exception:
            return False

    def _active_thoughts(self, principal: Any) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            page = self._refinement_thought_service.list_unfinished(
                principal, limit=50, cursor=cursor
            )
            items.extend(page["items"])
            cursor = page["next_cursor"]
            if cursor is None:
                break
        return [self._thought_card(item) for item in items]

    @staticmethod
    def _follow_through_card(
        card: FollowThroughCard,
        *,
        owner_person_index: dict[str, tuple[str, str]] | None = None,
    ) -> dict[str, Any]:
        result = asdict(card)
        if card.source == "action_item":
            result["target_ref"] = f"action_item:{card.id}"
            verbs = DoorService._action_verbs(card.id)
        elif card.source in {"cadence_loop", "decision"}:
            result["target_ref"] = f"cadence_loop:{card.id}"
            verbs = DoorService._cadence_verbs(card.id)
        elif card.source == "people_commitment":
            result["target_ref"] = card.target_ref
            verbs = DoorService._people_verbs(card.id)
        else:
            raise ValueError(f"Unknown follow-through card source: {card.source}")
        result["lawful_verbs"] = verbs
        # HS-150-02: person projection for mapped owner strings (additive;
        # unmapped cards byte-identical to today).
        if owner_person_index and card.owner:
            resolved = owner_person_index.get(card.owner)
            if resolved:
                label, rel_id = resolved
                result["person_label"] = label
                if rel_id:
                    result["person_relationship_id"] = rel_id
        return result

    @staticmethod
    def _action_verbs(card_id: str) -> list[dict[str, Any]]:
        verbs: list[dict[str, Any]] = []
        for verb in ("done", "dismiss", "snooze", "delegate"):
            descriptor: dict[str, Any] = {
                "name": "follow_through.complete",
                "arguments": {"card_id": card_id, "verb": verb},
            }
            if verb == "snooze":
                descriptor["required_arguments"] = ["payload.until"]
            elif verb == "delegate":
                descriptor["required_arguments"] = ["payload.to"]
            verbs.append(descriptor)
        return verbs

    @staticmethod
    def _cadence_verbs(loop_id: str) -> list[dict[str, Any]]:
        return [
            {
                "name": "cadence.set_status",
                "arguments": {"loop_id": loop_id, "status": status},
            }
            for status in ("closed", "killed")
        ]

    @staticmethod
    def _people_verbs(card_id: str) -> list[dict[str, Any]]:
        commitment_id = card_id.removeprefix("people:")
        return [
            {
                "name": "people.commitment.transition",
                "arguments": {"commitment_id": commitment_id, "verb": verb},
            }
            for verb in ("done", "dismiss")
        ]

    @staticmethod
    def _thought_card(item: dict[str, Any]) -> dict[str, Any]:
        thought_id = str(item["id"])
        aggregate_revision = item["aggregate_revision"]
        lifecycle_revision = item["lifecycle_revision"]
        return {
            "id": thought_id,
            "source": "thought",
            "target_ref": f"thought:{thought_id}",
            "open_ref": f"note:{item['working_note_id']}",
            "title": item["title"],
            "body_preview": item["body_preview"],
            "state": item["state"],
            "continuity_state": item["continuity_state"],
            "updated_at": item["updated_at"],
            "aggregate_revision": aggregate_revision,
            "lifecycle_revision": lifecycle_revision,
            "filing_status": item["filing_status"],
            "lawful_verbs": [
                {
                    "name": "thought.complete",
                    "arguments": {
                        "thought_id": thought_id,
                        "expected_aggregate_revision": aggregate_revision,
                        "expected_lifecycle_revision": lifecycle_revision,
                    },
                    "required_arguments": ["request_id"],
                }
            ],
        }

    def _upcoming(self, now: datetime) -> list[dict[str, Any]]:
        upcoming: list[dict[str, Any]] = []
        enabled_recordings = self._scheduled_recordings.list_enabled()
        now_iso = self._utc_iso(now)
        events = list(self._calendar_events.list_upcoming(now_iso))
        event_ids = {event.id for event in events}
        # HS-175-03: build an event info index for recording provenance.
        # Start from the upcoming events, then enrich with any calendar
        # events that event-born recordings reference but that have left
        # the upcoming projection (the orphan provenance fix).
        event_info: dict[str, dict[str, str]] = {}
        for event in events:
            event_info[event.id] = {
                "event_title": event.title,
                "source_label": event.source_label,
            }
        # HS-175-02-fix: resolve provenance for orphan recordings whose
        # event is no longer in list_upcoming (past events).
        orphan_event_ids = {
            r.calendar_event_id
            for r in enabled_recordings
            if r.calendar_event_id and r.born_from == "calendar_event"
            and r.calendar_event_id not in event_info
        }
        for eid in orphan_event_ids:
            past_event = self._calendar_events.get(eid)
            if past_event:
                event_info[eid] = {
                    "event_title": past_event.title,
                    "source_label": past_event.source_label,
                }
            else:
                # Event row is gone entirely; resolve source_label from
                # the recording's calendar_source_id via configured sources.
                rec = next(
                    (r for r in enabled_recordings if r.calendar_event_id == eid),
                    None,
                )
                source_label = ""
                if rec and rec.calendar_source_id and self._config_loader:
                    try:
                        config = self._config_loader()
                        for src in config.calendar.sources:
                            if src.id == rec.calendar_source_id:
                                source_label = src.label
                                break
                    except Exception:
                        pass
                event_info[eid] = {
                    "event_title": rec.title if rec else "",
                    "source_label": source_label,
                }
        # HS-147-01: build an index of armed calendar_event_id -> schedule info
        # so _calendar_event_item can project armed data without N+1.
        # HS-175-03: enriched to carry arms_at for the ARMS HH:MM token.
        armed_index: dict[str, dict[str, Any]] = {}
        for recording in enabled_recordings:
            if recording.calendar_event_id:
                armed_index[recording.calendar_event_id] = {
                    "recording_id": recording.id,
                    "arms_at": (
                        self._utc_iso(datetime.fromtimestamp(
                            recording.next_fire_at, tz=timezone.utc
                        ))
                        if recording.next_fire_at else None
                    ),
                    # HS-175 C2: the face withholds Cancel while capture runs
                    # (the honest verb is the meeting's Stop).
                    "state": recording.state,
                }
                # HS-147-02 ruling: a linked schedule whose event row is on
                # the rail would render the same intent twice — the event row
                # wears ARMED and carries armed_schedule_id, so the schedule
                # row is suppressed. If the event has left the projection the
                # schedule row still shows (honest pending work, never hidden).
                if recording.calendar_event_id in event_ids:
                    continue
            if recording.next_fire_at is None or recording.next_fire_at < now.timestamp():
                continue
            upcoming.append(self._scheduled_recording_item(
                recording, event_info=event_info,
            ))
        # HS-149-03: build a person label index for linked calendar series.
        # Memoize one resolve per distinct (uid, source_id) in the aggregate
        # build — CHEAP, never cached across requests.
        person_index = self._build_person_index(events)
        # HS-175-02: build event-to-Room project index for Room tokens.
        project_index = self._build_event_project_index()
        upcoming.extend(
            self._calendar_event_item(
                event, armed_index=armed_index, person_index=person_index,
                project_index=project_index,
            )
            for event in events
        )
        return sorted(upcoming, key=lambda item: (item["starts_at"], item["source"], item["id"]))

    def _build_owner_person_index(
        self, board: FollowThroughBoard,
    ) -> dict[str, tuple[str, str]]:
        """HS-150-02: resolve person labels for mapped owner strings on board cards.

        Returns a map from ``owner_string`` to ``(display_name, relationship_id)``
        for every mapped owner.  One ``resolve_relationship_by_owner`` call per
        distinct owner string -- memoized in-request only, never cached across
        requests.  The sidecar being unavailable silently produces no entry
        (the Door never blocks on the sidecar).
        """
        if self._people_service is None:
            return {}
        seen: dict[str, tuple[str, str] | None] = {}
        all_cards = list(board.now) + list(board.waiting) + list(board.unassigned) + list(board.overdue)
        for card in all_cards:
            if not card.owner or card.owner in seen:
                continue
            try:
                result = self._people_service.resolve_relationship_by_owner(card.owner)
            except Exception:
                seen[card.owner] = None
                continue
            if result.get("state") != "ready":
                seen[card.owner] = None
                continue
            rel = result.get("relationship")
            if rel is not None:
                name = str(rel.get("display_name") or "")
                rel_id = str(rel.get("id") or "")
                seen[card.owner] = (name, rel_id) if name else None
            else:
                seen[card.owner] = None
        return {k: v for k, v in seen.items() if v}

    def _build_person_index(
        self, events: list[CalendarEvent],
    ) -> dict[tuple[str, str], tuple[str, str]]:
        """HS-149-03/04: resolve person labels and relationship IDs for linked calendar series.

        Returns a map from ``(uid, source_id)`` to ``(display_name, relationship_id)``
        for every linked series.  One ``resolve_relationship_by_series`` call per
        distinct key — memoized in-request only, never cached across requests.
        The sidecar being unavailable or a series having no link silently
        produces no entry (the Door never blocks on the sidecar).
        """
        if self._people_service is None:
            return {}
        seen: dict[tuple[str, str], tuple[str, str] | None] = {}
        for event in events:
            key = (event.uid, event.source_id)
            if key in seen:
                continue
            try:
                result = self._people_service.resolve_relationship_by_series(
                    event.uid, event.source_id,
                )
            except Exception:
                seen[key] = None
                continue
            if result.get("state") != "ready":
                seen[key] = None
                continue
            rel = result.get("relationship")
            if rel is not None:
                name = str(rel.get("display_name") or "")
                rel_id = str(rel.get("id") or "")
                seen[key] = (name, rel_id) if name else None
            else:
                seen[key] = None
        return {k: v for k, v in seen.items() if v}

    def _build_event_project_index(self) -> dict[str, tuple[str, str]]:
        """HS-175-02: build event_id -> (project_id, project_name) index.

        Reads the calendar_event_projects join table.
        """
        if self._db is None:
            return {}
        try:
            return self._db.calendar_event_projects.build_event_project_index()
        except Exception:
            return {}

    def _to_local(self, value: datetime) -> datetime:
        """Convert one instant to the desk's local wall clock (HS-175 C8).

        Per instant, never a fixed offset: ``astimezone()`` with no argument
        asks the system zone for THAT instant, so a week that crosses a DST
        edge keeps every event on its true local day (counsel re-read,
        condition 4). An injected ``local_tz`` (the tests) is used the same
        way -- a ``ZoneInfo`` resolves per instant too.
        """
        if self._local_tz is not None:
            return value.astimezone(self._local_tz)
        return value.astimezone()

    def _local_midnight(self, day: date) -> datetime:
        """Local 00:00 of a calendar day as an aware datetime, built from the
        naive wall clock so the offset is the one in force ON that day."""
        naive = datetime.combine(day, time.min)
        if self._local_tz is not None:
            return naive.replace(tzinfo=self._local_tz)
        return naive.astimezone()

    def _local_zone(self) -> tzinfo:
        """The desk's local timezone as of now (HS-175 C8); only for callers
        that need a tzinfo -- the week arithmetic goes through ``_to_local`` /
        ``_local_midnight`` so it survives a DST edge."""
        if self._local_tz is not None:
            return self._local_tz
        return datetime.now().astimezone().tzinfo or timezone.utc

    def _local_week_bounds(self, now: datetime) -> tuple[datetime, datetime]:
        """Monday 00:00 and next Monday 00:00 of the CURRENT LOCAL week, as
        aware local datetimes. The strip, the THIS WEEK section and any
        other "this week" reader on the arrival share this boundary."""
        local_now = self._to_local(now)
        monday = local_now.date() - timedelta(days=local_now.weekday())
        return self._local_midnight(monday), self._local_midnight(monday + timedelta(days=7))

    @staticmethod
    def _parse_iso(value: str) -> datetime | None:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _week_strip(self, now: datetime, has_calendar: bool) -> dict[str, Any]:
        """HS-175-02: build the WEEK strip data for the Door.

        Returns {days: [{date, dow, count}], total, has_calendar, starts_at,
        ends_at} for the current LOCAL week (Mon-Sun; HS-175 C8 -- a Monday
        20:00 meeting at -06:00 is a MON dot, never a TUE one). ``starts_at``
        / ``ends_at`` are the week's bounds as UTC instants (ends_at is the
        exclusive next-Monday-00:00 local) so the face can bound its
        THIS WEEK section to the same week the strip draws (C9). Days are
        absent when no calendar source is connected; the bounds always ride.
        """
        monday_start, sunday_end = self._local_week_bounds(now)
        start_utc = monday_start.astimezone(timezone.utc).isoformat()
        end_utc = sunday_end.astimezone(timezone.utc).isoformat()
        if not has_calendar:
            return {
                "days": [], "total": 0, "has_calendar": False,
                "starts_at": start_utc, "ends_at": end_utc,
            }
        # Bucket by LOCAL date in Python: the repository's count_per_day
        # groups on the stored UTC date, which is the wrong day west of UTC
        # for any evening meeting.
        counts: dict[str, int] = {}
        for event in self._calendar_events.list_in_range(start_utc, end_utc):
            parsed = self._parse_iso(event.starts_at)
            if parsed is None:
                continue
            local_date = self._to_local(parsed).strftime("%Y-%m-%d")
            counts[local_date] = counts.get(local_date, 0) + 1
        dow_names = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        days: list[dict[str, Any]] = []
        total = 0
        for i in range(7):
            # Calendar-day arithmetic (not 24h steps): a DST edge inside the
            # week must not shift a day's date.
            date_str = (monday_start.date() + timedelta(days=i)).strftime("%Y-%m-%d")
            count = counts.get(date_str, 0)
            total += count
            days.append({
                "date": date_str,
                "dow": dow_names[i],
                "count": count,
            })
        return {
            "days": days, "total": total, "has_calendar": True,
            "starts_at": start_utc, "ends_at": end_utc,
        }

    @staticmethod
    def _scheduled_recording_item(
        recording: ScheduledRecording,
        *,
        event_info: dict[str, dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        starts_at = datetime.fromtimestamp(recording.next_fire_at or 0, tz=timezone.utc)
        ends_at = starts_at + timedelta(minutes=recording.duration_minutes)
        item: dict[str, Any] = {
            "id": recording.id,
            "source": "scheduled_recording",
            "target_ref": f"scheduled_recording:{recording.id}",
            "title": recording.title,
            "starts_at": DoorService._utc_iso(starts_at),
            "ends_at": DoorService._utc_iso(ends_at),
            "location": None,
            "meeting_url": None,
            "state": recording.state,
        }
        # HS-175-03: project provenance for event-born recordings.
        if recording.born_from == "calendar_event" and recording.calendar_event_id:
            info = (event_info or {}).get(recording.calendar_event_id)
            item["from"] = {
                "event_title": (info or {}).get("event_title", recording.title),
                "source_label": (info or {}).get("source_label", ""),
            }
        return item

    @staticmethod
    def _calendar_event_item(
        event: CalendarEvent,
        *,
        armed_index: dict[str, dict[str, Any]] | None = None,
        person_index: dict[tuple[str, str], tuple[str, str]] | None = None,
        project_index: dict[str, tuple[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Map the persisted projection into Story 01's reserved timeline row.

        HS-146-04: source_id and source_label are projected so the rail can
        render provenance chips when >1 distinct source is configured.

        HS-147-01: armed_schedule_id is projected when a live event-linked
        schedule exists (the read side; story 02 renders the chip).

        HS-149-03/04: uid is projected for the picker/link flow; person_label
        and person_relationship_id are projected (only-when-present) for linked
        calendar series.

        HS-175-02: project_id and project_name (Room link) projected when the
        event is matched to a Room via the calendar_event_projects join.
        """
        item: dict[str, Any] = {
            "id": event.id,
            "uid": event.uid,
            "source": "calendar_event",
            "target_ref": f"calendar_event:{event.id}",
            "title": event.title,
            "starts_at": event.starts_at,
            "ends_at": event.ends_at,
            "location": event.location,
            "meeting_url": event.meeting_url,
            "state": "scheduled",
            "source_id": event.source_id,
            "source_label": event.source_label,
        }
        if armed_index:
            armed_info = armed_index.get(event.id)
            if armed_info:
                item["armed_schedule_id"] = armed_info["recording_id"]
                item["armed"] = {
                    "recording_id": armed_info["recording_id"],
                    "arms_at": armed_info["arms_at"],
                    "state": armed_info.get("state", "idle"),
                }
        # HS-149-03/04: person_label + person_relationship_id projected
        # only when present — the armed_schedule_id only-when-present analogy.
        if person_index:
            resolved = person_index.get((event.uid, event.source_id))
            if resolved:
                label, rel_id = resolved
                item["person_label"] = label
                if rel_id:
                    item["person_relationship_id"] = rel_id
        # HS-175-02: project (Room) link projected only when present.
        if project_index:
            room = project_index.get(event.id)
            if room:
                item["project_id"] = room[0]
                item["project_name"] = room[1]
        return item

    @staticmethod
    def _upcoming_today(upcoming: list[dict[str, Any]], now: datetime) -> int:
        local_now = now.astimezone()
        day_start = datetime.combine(local_now.date(), time.min, tzinfo=local_now.tzinfo)
        next_day_start = datetime.combine(
            local_now.date() + timedelta(days=1), time.min, tzinfo=local_now.tzinfo
        )
        return sum(
            day_start
            <= datetime.fromisoformat(item["starts_at"].replace("Z", "+00:00")).astimezone(
                local_now.tzinfo
            )
            < next_day_start
            for item in upcoming
        )

    @staticmethod
    def _utc_iso(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
