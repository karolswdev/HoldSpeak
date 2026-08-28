"""Dashboard Door MCP twin over the transport-neutral DoorService."""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database
from holdspeak.mcp.families import people
from holdspeak.principals import Principal
from holdspeak.services.door_service import DoorService
from holdspeak.services.errors import ServiceError
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.refinement_thought_service import RefinementThoughtService


TOOLS: list[dict[str, Any]] = [{
    "name": "door.get",
    "description": "Read the Dashboard Door aggregate projection.",
    "inputSchema": {
        "$id": "holdspeak://mcp/door.get@1",
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
}]


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
    )


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Dispatch the sole closed Door read command."""
    if name != "door.get":
        raise LookupError(name)
    if arguments:
        raise ServiceError(
            "door_request_invalid",
            "Door request has an invalid request shape.",
            context={"status": 400},
        )
    return _service().get(principal)


__all__ = ["TOOLS", "dispatch"]
