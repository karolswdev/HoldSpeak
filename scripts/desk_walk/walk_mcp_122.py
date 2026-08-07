"""HS-122-11 service-layer MCP walk.

Run with:
    uv run python -m scripts.desk_walk.walk_mcp_122

This is deliberately transport-free: it gives each MCP-backed service one
fresh temporary database rather than starting the HTTP hub.
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

from holdspeak.db.core import Database
from holdspeak.mcp.tools import TOOLS, _dispatch_verb
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.meeting_service import MeetingService
from holdspeak.services.primitive_service import NotFound, PrimitiveService
from holdspeak.services.workbench_service import WorkbenchService


EXPECTED_TOOLS = {
    "desk.create",
    "desk.list",
    "desk.get",
    "desk.update",
    "desk.delete",
    "desk.verb",
    "workbench.run",
    "workbench.add_item",
    "meeting.list",
    "meeting.get",
}


def main() -> None:
    registered_tools = {tool["name"] for tool in TOOLS}
    assert registered_tools == EXPECTED_TOOLS, registered_tools

    with tempfile.TemporaryDirectory(prefix="holdspeak-mcp-walk-") as tempdir:
        db = Database(Path(tempdir) / "test.db")
        principal = Principal(PrincipalKind.OWNER, "walk")
        primitives = PrimitiveService(db)
        workbenches = WorkbenchService(db)
        meetings = MeetingService(db)

        # desk.create → desk.list → desk.get → desk.update → desk.delete
        note = primitives.create_note(
            principal,
            title="Architecture Decision",
            body_markdown="Use the service layer for every transport.",
            tags=["architecture"],
        )
        note_id = note["id"]
        assert primitives.get_note(principal, note_id)["title"] == "Architecture Decision"
        assert any(row["id"] == note_id for row in primitives.list_notes(principal))

        updated = primitives.update_note(
            principal, note_id, title="Architecture Decision Record"
        )
        assert updated["title"] == "Architecture Decision Record"
        assert primitives.delete_note(principal, note_id) is True
        try:
            primitives.get_note(principal, note_id)
        except NotFound:
            pass
        else:
            raise AssertionError("desk.delete left the note available")

        # desk.verb's UI-only result is intentionally state-free.
        ui_only = _dispatch_verb(
            {"verb_id": "desk.open"}, principal, primitives, workbenches
        )
        assert ui_only["status"] == "ui_only"
        assert ui_only["verb_id"] == "desk.open"

        # workbench.run is a service operation. Exercise its no-pending-work
        # receipt without an inference target, then add the MCP-backed item.
        workbench = workbenches.create_workbench(principal, name="Walk Workbench")
        with patch("holdspeak.db.get_database", return_value=db):
            run = asyncio.run(workbenches.run(principal, workbench["id"]))
        assert run == {"skipped": True, "reason": "no pending items"}

        item = workbenches.add_item(
            principal, workbench["id"], title="Review PR", body="Check the walk."
        )
        assert item["workbench_id"] == workbench["id"]
        assert item["title"] == "Review PR"

        # meeting.list is allowed to be empty; meeting.get must make a missing
        # record explicit rather than silently returning an empty payload.
        meeting_list = meetings.list_meetings(principal)
        assert meeting_list["meetings"] == []
        try:
            meetings.get_meeting(principal, meeting_id="meeting_missing")
        except NotFound as exc:
            assert exc.kind == "meeting"
            assert exc.id == "meeting_missing"
        else:
            raise AssertionError("meeting.get did not report a missing meeting")

    print("MCP service walk passed: 10 tools registered; CRUD, verb, workbench, and meeting paths verified.")


if __name__ == "__main__":
    main()
