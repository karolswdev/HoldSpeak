"""The Dashboard Door's composed, transport-neutral read model."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, time, timedelta, timezone
from typing import Any, Callable

from ..db.scheduled_recordings import ScheduledRecording, ScheduledRecordingRepository
from .follow_through_service import FollowThroughCard, FollowThroughService
from .refinement_thought_service import RefinementThoughtService


class DoorService:
    def __init__(
        self,
        follow_through_service: FollowThroughService,
        refinement_thought_service: RefinementThoughtService,
        scheduled_recordings: ScheduledRecordingRepository,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._follow_through_service = follow_through_service
        self._refinement_thought_service = refinement_thought_service
        self._scheduled_recordings = scheduled_recordings
        self._clock = clock or (lambda: datetime.now().astimezone())

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
        return {
            "board": projected_board,
            "upcoming": upcoming,
            "counts": {
                "overdue": len(projected_board["overdue"]),
                "now": len(projected_board["now"]),
                "waiting": len(projected_board["waiting"]),
                "active": len(projected_board["active"]),
                "upcoming_today": self._upcoming_today(upcoming, now),
            },
        }

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
        for recording in self._scheduled_recordings.list_enabled():
            if recording.next_fire_at is None or recording.next_fire_at < now.timestamp():
                continue
            upcoming.append(self._scheduled_recording_item(recording))
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
