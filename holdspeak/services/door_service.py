"""The Dashboard Door's composed, transport-neutral read model."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, time, timedelta, timezone
from typing import Any, Callable

from ..config.integrations import validate_calendar_subscription
from ..db.calendar_events import CalendarEvent, CalendarEventRepository
from ..db.scheduled_recordings import ScheduledRecording, ScheduledRecordingRepository
from .follow_through_service import FollowThroughCard, FollowThroughService
from .refinement_thought_service import RefinementThoughtService


class DoorService:
    def __init__(
        self,
        follow_through_service: FollowThroughService,
        refinement_thought_service: RefinementThoughtService,
        scheduled_recordings: ScheduledRecordingRepository,
        calendar_events: CalendarEventRepository,
        *,
        clock: Callable[[], datetime] | None = None,
        config_loader: Callable[[], Any] | None = None,
    ) -> None:
        self._follow_through_service = follow_through_service
        self._refinement_thought_service = refinement_thought_service
        self._scheduled_recordings = scheduled_recordings
        self._calendar_events = calendar_events
        self._clock = clock or (lambda: datetime.now().astimezone())
        self._config_loader = config_loader

    def get(self, principal: Any) -> dict[str, Any]:
        now = self._clock()
        if now.tzinfo is None:
            now = now.astimezone()
        now_utc = now.astimezone(timezone.utc)
        board = self._follow_through_service.board(principal)
        projected_board = {
            "now": [self._follow_through_card(card) for card in board.now],
            "waiting": [self._follow_through_card(card) for card in board.waiting],
            "unassigned": [self._follow_through_card(card) for card in board.unassigned],
            "overdue": [self._follow_through_card(card) for card in board.overdue],
            "active": self._active_thoughts(principal),
        }
        upcoming = self._upcoming(now_utc)
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
            "calendar_configured": self._calendar_configured(),
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
    def _follow_through_card(card: FollowThroughCard) -> dict[str, Any]:
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
        # HS-147-01: build an index of armed calendar_event_id -> schedule_id
        # so _calendar_event_item can project armed_schedule_id without N+1.
        armed_index: dict[str, str] = {}
        for recording in enabled_recordings:
            if recording.calendar_event_id:
                armed_index[recording.calendar_event_id] = recording.id
                # HS-147-02 ruling: a linked schedule whose event row is on
                # the rail would render the same intent twice — the event row
                # wears ARMED and carries armed_schedule_id, so the schedule
                # row is suppressed. If the event has left the projection the
                # schedule row still shows (honest pending work, never hidden).
                if recording.calendar_event_id in event_ids:
                    continue
            if recording.next_fire_at is None or recording.next_fire_at < now.timestamp():
                continue
            upcoming.append(self._scheduled_recording_item(recording))
        upcoming.extend(
            self._calendar_event_item(event, armed_index=armed_index)
            for event in events
        )
        return sorted(upcoming, key=lambda item: (item["starts_at"], item["source"], item["id"]))

    @staticmethod
    def _scheduled_recording_item(recording: ScheduledRecording) -> dict[str, Any]:
        starts_at = datetime.fromtimestamp(recording.next_fire_at or 0, tz=timezone.utc)
        ends_at = starts_at + timedelta(minutes=recording.duration_minutes)
        return {
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

    @staticmethod
    def _calendar_event_item(
        event: CalendarEvent,
        *,
        armed_index: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Map the persisted projection into Story 01's reserved timeline row.

        HS-146-04: source_id and source_label are projected so the rail can
        render provenance chips when >1 distinct source is configured.

        HS-147-01: armed_schedule_id is projected when a live event-linked
        schedule exists (the read side; story 02 renders the chip).
        """
        item: dict[str, Any] = {
            "id": event.id,
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
            schedule_id = armed_index.get(event.id)
            if schedule_id:
                item["armed_schedule_id"] = schedule_id
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
