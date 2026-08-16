"""Plugin-job family — MCP tools for the PluginJobService surface."""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database, get_observer
from holdspeak.principals import Principal
from holdspeak.services.plugin_job_service import PluginJobService

TOOLS: list[dict[str, Any]] = [
    {
        "name": "plugin_job.list",
        "description": "List deferred plugin jobs by status. Queue processing is unavailable from the MCP sidecar.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["all", "queued", "running", "failed", "completed"],
                    "description": "Job status filter (default 'all').",
                },
                "meeting_id": {"type": "string", "description": "Optional meeting filter."},
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 500,
                    "description": "Maximum jobs (default 200).",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "plugin_job.summary",
        "description": "Read aggregate plugin job statistics: total, queued, running, failed counts and next retry time.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "plugin_job.retry",
        "description": "Re-queue a failed or completed plugin job for immediate retry. Refuses running jobs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "integer", "description": "Numeric job identifier."},
            },
            "required": ["job_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "plugin_job.cancel",
        "description": "Mark a non-running plugin job as completed (cancels it). Refuses running jobs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "integer", "description": "Numeric job identifier."},
            },
            "required": ["job_id"],
            "additionalProperties": False,
        },
    },
]

_NAMES = {t["name"] for t in TOOLS}


def _service() -> PluginJobService:
    """Construct PluginJobService per spec: db + observer."""
    return PluginJobService(db=get_database(), observer=get_observer())


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    if name not in _NAMES:
        raise LookupError(name)

    svc = _service()

    if name == "plugin_job.list":
        status = arguments.get("status", "all")
        meeting_id = arguments.get("meeting_id")
        limit = arguments.get("limit", 200)
        return svc.list(principal, status=status, meeting_id=meeting_id, limit=limit)

    if name == "plugin_job.summary":
        return svc.summary(principal)

    if name == "plugin_job.retry":
        job_id = arguments.get("job_id")
        if not isinstance(job_id, int):
            raise ValueError("job_id is required and must be an integer")
        return svc.retry(principal, job_id)

    # plugin_job.cancel
    job_id = arguments.get("job_id")
    if not isinstance(job_id, int):
        raise ValueError("job_id is required and must be an integer")
    return svc.cancel(principal, job_id)
