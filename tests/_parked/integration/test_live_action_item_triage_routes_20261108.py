"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_live_action_item_triage.py``: TestLiveTriageSurvivesTheSave. Not collected.
"""
from __future__ import annotations
"""HS-132-02 — a live meeting is a living board: triage reaches the session.

The three PATCH verbs (`/api/action-items/{id}`, `/review`, `/edit`) ask the
live session first and fall through to the saved meeting when no live session
owns the item. These tests pin that resolution order, prove a live change
survives the meeting's save, and cover the stop refusal's honest status.
"""


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

    def __init__(self, *, found: bool = True, db: Database | None = None) -> None:
        self.found = found
        self.calls: list[tuple[str, Any]] = []
        # A saved-meeting write marks the Needs You aggregate dirty through
        # ``db._connection()``. The spy has no connection of its own: a test
        # that reaches that write passes a real ``Database``.
        self._db = db

    def _connection(self) -> Any:
        assert self._db is not None, "this path writes the plain DB: pass a real Database"
        return self._db._connection()

    def dirty_marker(self) -> Any:
        with self._connection() as conn:
            return conn.execute(
                "SELECT attention_state FROM desk_projection_state "
                "WHERE projection_id = 'needs_you_aggregate'"
            ).fetchone()

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
        # Betterment D0 (docs/internal/betterment/daily/RECIPE.md, D0): the save
        # reads the said due against the meeting's day (Sat 15 Aug -> Fri 21 Aug)
        # and keeps the said words beside the date.
        assert saved_edit.due == "2026-08-21"
        with db._connection() as conn:
            said = conn.execute("SELECT due_said FROM action_items WHERE id = 'item-002'").fetchone()[0]
        assert said == "Friday"
        assert saved_edit.review_state == "accepted"


