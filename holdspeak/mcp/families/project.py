"""Project Room MCP twin: read tools over ProjectService (MCP-001 parity)."""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database
from holdspeak.principals import Principal
from holdspeak.services.errors import ServiceError
from holdspeak.services.project_service import ProjectService


TOOLS: list[dict[str, Any]] = [
    {
        "name": "project.list",
        "description": "List all projects. Optionally include archived projects.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.list@1",
            "type": "object",
            "properties": {
                "include_archived": {
                    "type": "boolean",
                    "description": "Include archived projects (default false).",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.get",
        "description": "Get one project by id.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.get@1",
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "project.get_room",
        "description": "Get the coherent room projection for one project (identity, items, meetings, resources, changes, review).",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.get_room@1",
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project identifier.",
                },
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
]


def _service() -> ProjectService:
    """Compose the same ProjectService the web application edge uses."""
    db = get_database()
    return ProjectService(db)


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Dispatch project read tools (MCP-001: thin drivers over ProjectService)."""
    svc = _service()
    if name == "project.list":
        filters: dict[str, Any] = {}
        if arguments.get("include_archived"):
            filters["include_archived"] = True
        return {"projects": svc.list_projects(principal, filters)}
    if name == "project.get":
        project_id = str(arguments.get("project_id") or "")
        if not project_id:
            raise ServiceError(
                "project_request_invalid",
                "project_id is required.",
                context={"status": 400},
            )
        return svc.get_project(principal, project_id)
    if name == "project.get_room":
        project_id = str(arguments.get("project_id") or "")
        if not project_id:
            raise ServiceError(
                "project_request_invalid",
                "project_id is required.",
                context={"status": 400},
            )
        return svc.room(principal, project_id)
    raise LookupError(name)


__all__ = ["TOOLS", "dispatch"]
