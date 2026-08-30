"""Dashboard Door MCP twin over the transport-neutral DoorService."""
from __future__ import annotations

from typing import Any

from holdspeak.config import Config
from holdspeak.db import get_database
from holdspeak.mcp.families import people
from holdspeak.principals import Principal
from holdspeak.services.door_service import DoorService
from holdspeak.services.errors import ServiceError
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.refinement_thought_service import RefinementThoughtService


TOOLS: list[dict[str, Any]] = [
    {
        "name": "door.get",
        "description": "Read the Dashboard Door aggregate projection.",
        "inputSchema": {
            "$id": "holdspeak://mcp/door.get@1",
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "door.add_item",
        "description": "Add an action item to the Dashboard Door. Creates a follow-through card with the given task, optional owner, and optional due date.",
        "inputSchema": {
            "$id": "holdspeak://mcp/door.add_item@1",
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Action item task description.",
                },
                "owner": {
                    "type": "string",
                    "description": "Optional accountable owner.",
                },
                "due": {
                    "type": "string",
                    "description": "Optional ISO-8601 due date.",
                },
                "source_type": {
                    "type": "string",
                    "enum": ["meeting", "thread"],
                    "description": "Source kind (default: thread when invoked from chat).",
                },
                "source_ref": {
                    "type": "string",
                    "description": "Source reference (e.g. thread:<id>).",
                },
            },
            "required": ["task"],
            "additionalProperties": False,
        },
    },
]


def _service() -> DoorService:
    """Compose the same Door authorities as the web application edge.

    MCP's People capability is an encrypted disclosure boundary.  When it is
    explicitly disabled, leaving the overlay absent preserves Follow-Through's
    ordinary safe-empty behavior; otherwise the People family's production
    encrypted-store composition supplies the overlay (or its unavailable
    authority state, never a plaintext substitute).
    """
    db = get_database()
    people_projection = None if people.access_mode() == "off" else people.build_people_service()
    return DoorService(
        FollowThroughService(db, people_projection=people_projection),
        RefinementThoughtService(db),
        db.scheduled_recordings,
        db.calendar_events,
        db=db,
        config_loader=Config.load,
    )


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Dispatch Door read and write commands."""
    if name == "door.get":
        if arguments:
            raise ServiceError(
                "door_request_invalid",
                "Door request has an invalid request shape.",
                context={"status": 400},
            )
        return _service().get(principal)
    if name == "door.add_item":
        task = str(arguments.get("task") or "")
        kwargs: dict[str, Any] = {"task": task}
        if "owner" in arguments:
            kwargs["owner"] = str(arguments["owner"])
        if "due" in arguments:
            kwargs["due"] = str(arguments["due"])
        kwargs["source_type"] = str(arguments.get("source_type", "thread"))
        if "source_ref" in arguments:
            kwargs["source_ref"] = str(arguments["source_ref"])
        return _service().add_item(principal, **kwargs)
    raise LookupError(name)


__all__ = ["TOOLS", "dispatch"]
