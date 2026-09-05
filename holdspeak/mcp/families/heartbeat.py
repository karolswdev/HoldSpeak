"""HS-171-02: Heartbeat family -- MCP tools for the heartbeat sweep."""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database, get_observer
from holdspeak.principals import Principal
from holdspeak.services.heartbeat_service import HeartbeatService
from holdspeak.services.watch_service import WatchService

TOOLS: list[dict[str, Any]] = [
    {
        "name": "heartbeat.status",
        "description": "Read the heartbeat sweep status: interval, quiet hours, last/next sweep timestamps, and whether the sweep is currently held.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "heartbeat.run_now",
        "description": "Run one heartbeat sweep immediately. Evaluates due watches, refreshes the needs-you aggregate, and returns the sweep receipt.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "heartbeat.set",
        "description": "Update heartbeat sweep settings. Accepts sweep_every_minutes, quiet_hours ({start, end}), notify (off|edge|every_sweep), and muted_projects.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sweep_every_minutes": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1440,
                    "description": "Sweep interval in minutes (default 15).",
                },
                "quiet_hours": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "integer", "minimum": 0, "maximum": 23},
                        "end": {"type": "integer", "minimum": 0, "maximum": 23},
                    },
                    "description": "Quiet hours window.",
                },
                "notify": {
                    "type": "string",
                    "enum": ["off", "edge", "every_sweep"],
                    "description": "Notification mode.",
                },
                "muted_projects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Project IDs to exclude from notification aggregates.",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "heartbeat.notify_test",
        "description": "Fire one test desktop notification (owner-only). Returns {fired: boolean}.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call. Raises LookupError for unowned names."""
    db = get_database()
    obs = get_observer()
    hb = HeartbeatService(db, observer=obs)

    if name == "heartbeat.status":
        settings = hb.get_settings()
        settings["held"] = hb.in_quiet_hours()
        return settings

    if name == "heartbeat.run_now":
        ws = WatchService(db, observer=obs)
        hb_with_ws = HeartbeatService(db, observer=obs, watch_service=ws)
        return hb_with_ws.run_sweep(principal)

    if name == "heartbeat.set":
        return hb.update_settings(arguments)

    if name == "heartbeat.notify_test":
        from holdspeak.desktop_notify import notify
        fired = notify("HoldSpeak", "Test notification from heartbeat")
        return {"fired": fired}

    raise LookupError(name)
