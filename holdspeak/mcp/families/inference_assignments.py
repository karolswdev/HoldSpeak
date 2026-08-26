"""Owner Inference Assignment MCP twins over the canonical assignment service."""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal
from holdspeak.services.errors import ValidationError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService


def _schema(
    name: str, properties: dict[str, Any], required: list[str], *, description: str
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "$id": f"holdspeak://mcp/{name}@1",
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


_ID = {"type": "string", "minLength": 1, "maxLength": 192}
_SCOPE = {
    "oneOf": [
        {
            "type": "object", "properties": {"kind": {"const": "global"}},
            "required": ["kind"], "additionalProperties": False,
        },
        {
            "type": "object", "properties": {"kind": {"const": "group"}, "group_id": _ID},
            "required": ["kind", "group_id"], "additionalProperties": False,
        },
        {
            "type": "object", "properties": {"kind": {"const": "capability"}, "capability_id": _ID},
            "required": ["kind", "capability_id"], "additionalProperties": False,
        },
        {
            "type": "object",
            "properties": {
                "kind": {"const": "subject"},
                "subject_kind": {"type": "string", "enum": ["thought", "workbench", "agent", "recipe", "project"]},
                "subject_id": _ID,
                "capability_id": _ID,
            },
            "required": ["kind", "subject_kind", "subject_id", "capability_id"],
            "additionalProperties": False,
        },
        {
            "type": "object",
            "properties": {"kind": {"const": "invocation"}, "invocation_id": _ID, "capability_id": _ID},
            "required": ["kind", "invocation_id", "capability_id"], "additionalProperties": False,
        },
    ]
}
_ENTRY = {
    "type": "object",
    "properties": {"profile_id": {"type": "string", "pattern": "^[a-z][a-z0-9_-]{0,95}$"}, "profile_revision": {"type": ["integer", "null"], "minimum": 1}},
    "required": ["profile_id"],
    "additionalProperties": False,
}
_EDITOR = {"scope": _SCOPE, "capability_id": _ID}
_CLEAR_OPTIONAL = {
    "invocation_id": _ID,
    "subject_kind": {"type": "string", "enum": ["thought", "workbench", "agent", "recipe", "project"]},
    "subject_id": _ID,
}


TOOLS: list[dict[str, Any]] = [
    _schema("inference_assignment.summary", {}, [], description="Read the owner Assignment summary."),
    _schema(
        "inference_assignment.editor", _EDITOR, ["scope", "capability_id"],
        description="Read one server-decided, assignment-safe editor projection.",
    ),
    _schema(
        "inference_assignment.set",
        {
            "command_id": _ID,
            "expected_revision": {"type": "integer", "minimum": 0},
            "scope": _SCOPE,
            "entries": {"type": "array", "items": _ENTRY, "minItems": 1, "maxItems": 4},
            "retry_policy_id": {"type": ["string", "null"], "maxLength": 192},
        },
        ["command_id", "expected_revision", "scope", "entries"],
        description="CAS-set an ordered assignment chain. Exact command replay returns its original receipt.",
    ),
    _schema(
        "inference_assignment.preview_use_default", _EDITOR, ["scope", "capability_id"],
        description="Preview the server-resolved default before a bound clear operation.",
    ),
    _schema(
        "inference_assignment.clear",
        {
            "command_id": _ID,
            "expected_revision": {"type": "integer", "minimum": 1},
            "scope": _SCOPE,
            "capability_id": _ID,
            **_CLEAR_OPTIONAL,
        },
        ["command_id", "expected_revision", "scope", "capability_id"],
        description="CAS-clear an assignment. Exact command replay returns its original receipt.",
    ),
]


def _service() -> InferenceAssignmentService:
    """Compose the same frozen broker foundation as web startup."""
    db = get_database()
    broker = _configure(db)
    return InferenceAssignmentService(
        db,
        registry=broker.inference_capability_registry,
        tool_capability_foundation=getattr(
            getattr(broker, "tool_turn_foundation", None), "_foundation", None
        ),
    )


def _closed(arguments: dict[str, Any], allowed: set[str], *, required: set[str]) -> None:
    if set(arguments) - allowed or not required.issubset(arguments):
        raise ValidationError("Assignment request has an invalid shape", code="inference_assignment_invalid")


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Dispatch only closed assignment commands after owner authority."""
    service = _service()
    # Do this before looking at command arguments so non-owners cannot use a
    # malformed or private-looking body as an oracle, matching HTTP.
    service._require_owner(principal)
    if name == "inference_assignment.summary":
        _closed(arguments, set(), required=set())
        return service.assignment_summary(principal)
    if name == "inference_assignment.editor":
        _closed(arguments, {"scope", "capability_id"}, required={"scope", "capability_id"})
        return service.assignment_editor_projection(principal, arguments)
    if name == "inference_assignment.set":
        _closed(
            arguments,
            {"command_id", "expected_revision", "scope", "entries", "retry_policy_id"},
            required={"command_id", "expected_revision", "scope", "entries"},
        )
        return service.set_assignment(principal, arguments)
    if name == "inference_assignment.preview_use_default":
        # This is the one assignment route with an HTTP transport-shape guard.
        # Preserve its exact public refusal rather than exposing a service-only
        # validation distinction through MCP.
        if set(arguments) != {"scope", "capability_id"}:
            raise ValidationError(
                "Use default preview has an invalid request shape.",
                code="inference_assignment_request_invalid",
            )
        return service.preview_use_default(
            principal, scope=arguments["scope"], capability_id=arguments["capability_id"],
        )
    if name == "inference_assignment.clear":
        _closed(
            arguments,
            {"command_id", "expected_revision", "scope", "capability_id", *_CLEAR_OPTIONAL},
            required={"command_id", "expected_revision", "scope", "capability_id"},
        )
        return service.clear_assignment(principal, arguments)
    raise LookupError(name)


__all__ = ["TOOLS", "dispatch"]
