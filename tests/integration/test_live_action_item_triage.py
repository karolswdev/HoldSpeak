"""HS-132-02 — a live meeting is a living board: triage reaches the session.

The three PATCH verbs (`/api/action-items/{id}`, `/review`, `/edit`) ask the
live session first and fall through to the saved meeting when no live session
owns the item. These tests pin that resolution order, prove a live change
survives the meeting's save, and cover the stop refusal's honest status.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Optional
from unittest.mock import MagicMock

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.requires_meeting]

from holdspeak.db.core import Database  # noqa: E402
from holdspeak.intel import ActionItem  # noqa: E402
from holdspeak.meeting_session import IntelSnapshot, MeetingState  # noqa: E402
from holdspeak.meeting_session.mutations import MeetingMutationsMixin  # noqa: E402
from holdspeak.principals import UNAUTHENTICATED  # noqa: E402
from holdspeak.services.errors import NotFound  # noqa: E402
from holdspeak.services.meeting_service import (  # noqa: E402
    ActionItemTriageUnavailable,
    MeetingService,
)
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402


class _ArchiveSpy:
    """The narrow persisted-action-item surface, recording every touch."""

    meetings = property(lambda self: self)

    def __init__(self, *, found: bool = True) -> None:
        self.found = found
        self.calls: list[tuple[str, Any]] = []

    def update_action_item_status(self, item_id: str, status: str) -> bool:
        self.calls.append(("status", (item_id, status)))
        return self.found

    def update_action_item_review_state(self, item_id: str, review_state: str) -> bool:
        self.calls.append(("review", (item_id, review_state)))
        return self.found

    def edit_action_item(self, item_id: str, *, task: str, owner: Any, due: Any) -> bool:
        self.calls.append(("edit", (item_id, task, owner, due)))
        return self.found

    def get_action_item(self, item_id: str) -> Any:
        self.calls.append(("get", item_id))
        return None


def _service(archive: _ArchiveSpy, **triage: Any) -> MeetingService:
    service = MeetingService(archive)  # type: ignore[arg-type]
    if triage:
        service.bind_live_triage(**triage)
    return service


class TestLiveFirstResolutionOrder:
    def test_live_session_serves_the_verb_and_the_archive_is_untouched(self):
        archive = _ArchiveSpy()
        live = MagicMock(return_value={"id": "a-1", "status": "done"})
        result = _service(archive, on_update=live).update_action_item(
            UNAUTHENTICATED, "a-1", {"status": "done"}
        )
        assert result == {"success": True, "action_item": {"id": "a-1", "status": "done"}}
        live.assert_called_once_with("a-1", "done")
        assert archive.calls == []

    def test_review_and_edit_reach_the_live_session_with_their_arguments(self):
        archive = _ArchiveSpy()
        review = MagicMock(return_value={"id": "a-1", "review_state": "accepted"})
        edit = MagicMock(return_value={"id": "a-1", "task": "Edited"})
        service = _service(archive, on_review=review, on_edit=edit)

        service.review_action_item(UNAUTHENTICATED, "a-1", {"review_state": "ACCEPTED"})
        service.edit_action_item(
            UNAUTHENTICATED, "a-1", {"task": " Edited ", "owner": "Me", "due": "Friday"}
        )

        review.assert_called_once_with("a-1", "accepted")
        edit.assert_called_once_with("a-1", task="Edited", owner="Me", due="Friday")
        assert archive.calls == []

    def test_falls_through_to_the_saved_meeting_when_no_live_session_owns_it(self):
        archive = _ArchiveSpy(found=True)
        live = MagicMock(return_value=None)
        _service(archive, on_update=live).update_action_item(
            UNAUTHENTICATED, "saved-1", {"status": "dismissed"}
        )
        live.assert_called_once_with("saved-1", "dismissed")
        assert archive.calls[0] == ("status", ("saved-1", "dismissed"))

    def test_saved_meetings_still_work_with_no_live_session_bound_at_all(self):
        archive = _ArchiveSpy(found=True)
        service = _service(archive)
        service.update_action_item(UNAUTHENTICATED, "saved-1", {"status": "done"})
        service.review_action_item(UNAUTHENTICATED, "saved-1", {"review_state": "accepted"})
        service.edit_action_item(UNAUTHENTICATED, "saved-1", {"task": "Task"})
        assert [call[0] for call in archive.calls if call[0] != "get"] == [
            "status",
            "review",
            "edit",
        ]

    def test_validation_runs_before_the_live_session_is_asked(self):
        archive = _ArchiveSpy()
        live = MagicMock(return_value={"id": "a-1"})
        service = _service(archive, on_update=live, on_review=live, on_edit=live)

        for call in (
            lambda: service.update_action_item(UNAUTHENTICATED, "a-1", {"status": "nope"}),
            lambda: service.review_action_item(UNAUTHENTICATED, "a-1", {"review_state": "approved"}),
            lambda: service.edit_action_item(UNAUTHENTICATED, "a-1", {"task": "   "}),
        ):
            with pytest.raises(Exception) as caught:
                call()
            assert caught.value.code == "validation_error"
        live.assert_not_called()
        assert archive.calls == []

    def test_unknown_item_is_not_found_when_a_live_session_could_have_owned_it(self):
        archive = _ArchiveSpy(found=False)
        with pytest.raises(NotFound):
            _service(archive, on_update=MagicMock(return_value=None)).update_action_item(
                UNAUTHENTICATED, "ghost", {"status": "done"}
            )

    def test_unknown_item_with_no_live_handler_reports_the_verb_unwired(self):
        archive = _ArchiveSpy(found=False)
        with pytest.raises(ActionItemTriageUnavailable):
            _service(archive).update_action_item(UNAUTHENTICATED, "ghost", {"status": "done"})

    def test_a_failing_live_session_is_never_swallowed_into_an_archive_write(self):
        archive = _ArchiveSpy()
        live = MagicMock(side_effect=RuntimeError("session exploded"))
        with pytest.raises(RuntimeError):
            _service(archive, on_update=live).update_action_item(
                UNAUTHENTICATED, "a-1", {"status": "done"}
            )
        assert archive.calls == []


class _LiveMeeting(MeetingMutationsMixin):
    """A meeting session reduced to the state its mutations act on."""

    def __init__(self, state: MeetingState) -> None:
        self._lock = threading.RLock()
        self._state = state

    def _emit_broadcast(self, *_a: Any, **_k: Any) -> None:
        return None


def _live_meeting() -> _LiveMeeting:
    items = [
        ActionItem(task="Task 1", owner="Me", id="item-001"),
        ActionItem(task="Task 2", owner="Remote", id="item-002"),
    ]
    state = MeetingState(
        id="meeting-live-1",
        started_at=datetime(2026, 8, 15, 10, 0, 0),
        ended_at=datetime(2026, 8, 15, 10, 30, 0),
        title="Live board",
        intel=IntelSnapshot(timestamp=60.0, topics=["Topic A"], action_items=items, summary="S"),
    )
    return _LiveMeeting(state)


def _server_for(meeting: _LiveMeeting) -> MeetingWebServer:
    def edit(item_id: str, *, task: str, owner: Optional[str], due: Optional[str]) -> Any:
        return meeting.edit_action_item(item_id, task=task, owner=owner, due=due)

    return MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=lambda: meeting._state.to_dict(),
            on_update_action_item=meeting.update_action_item,
            on_update_action_item_review=meeting.update_action_item_review,
            on_edit_action_item=edit,
        ),
        host="127.0.0.1",
    )


class TestLiveTriageSurvivesTheSave:
    def test_triage_during_the_meeting_lands_in_the_session_and_in_the_save(self, tmp_path):
        meeting = _live_meeting()
        client = TestClient(_server_for(meeting).app)

        assert client.patch("/api/action-items/item-001", json={"status": "done"}).status_code == 200
        assert client.patch(
            "/api/action-items/item-002/edit",
            json={"task": "Rewritten live", "owner": "", "due": "Friday"},
        ).status_code == 200

        # Visible in the session the meeting is still running against.
        session_items = {item.id: item for item in meeting._state.intel.action_items}
        assert session_items["item-001"].status == "done"
        assert session_items["item-002"].task == "Rewritten live"
        assert session_items["item-002"].review_state == "accepted"

        # ...and it survives the meeting's save.
        db = Database(tmp_path / "saved.db")
        db.meetings.save_meeting(meeting._state)
        saved_done = db.meetings.get_action_item("item-001")
        saved_edit = db.meetings.get_action_item("item-002")
        assert saved_done.status == "done"
        assert saved_done.completed_at is not None
        assert saved_edit.task == "Rewritten live"
        assert saved_edit.owner is None
        assert saved_edit.due == "Friday"
        assert saved_edit.review_state == "accepted"


class TestStopWithoutALiveMeeting:
    def test_refusal_answers_a_conflict_not_a_server_fault(self):
        """HS-132-01 made the refusal honest by name; it rode a 500 until now."""

        def no_active_meeting() -> dict[str, object]:
            raise RuntimeError("No active meeting")

        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=MagicMock(),
                on_stop=MagicMock(return_value={"status": "stopping_runtime"}),
                on_meeting_stop=no_active_meeting,
                get_state=lambda: None,
            ),
            host="127.0.0.1",
        )
        client = TestClient(server.app)

        for path in ("/api/meeting/stop", "/api/stop"):
            response = client.post(path)
            assert response.status_code == 409, path
            assert "No active meeting" in response.json()["error"], path
