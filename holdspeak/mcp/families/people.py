"""People family -- shared-intent-only MCP capability.

People content lives in a separately encrypted sidecar.  MCP is a disclosure
boundary, not merely another in-process caller, so this family never exposes
leader-private material.  HS-139-08: enabled by default (was off) per the
ledger-not-gate ruling; the owner can restrict via
``HOLDSPEAK_MCP_PEOPLE_ACCESS=read`` or ``=off``.
"""
from __future__ import annotations

import os
from typing import Any, Mapping

from holdspeak.people import PeopleOperation, PeoplePolicy, Visibility, production_people_store
from holdspeak.principals import Principal
from holdspeak.services.people_service import (
    OwnerAliasTaken,
    PeopleService,
    PeopleServiceError,
    SeriesAlreadyLinked,
    UnavailablePeopleStore,
)

ACCESS_ENV = "HOLDSPEAK_MCP_PEOPLE_ACCESS"
_ACCESS_MODES = frozenset({"off", "read", "write"})
_SHARED = "shared_intent"


def _tool(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required or [],
            "additionalProperties": False,
        },
    }


_BOUNDARY = (
    "PEOPLE DISCLOSURE: local-owner access defaults to write; set "
    "HOLDSPEAK_MCP_PEOPLE_ACCESS=read or =off to restrict it. "
    "Only shared-intent material crosses MCP. Leader-private prep is never returned. "
)

TOOLS: list[dict[str, Any]] = [
    _tool(
        "people.readiness",
        "Read the content-free People MCP capability and encrypted-store readiness. "
        "This never initializes the store or returns relationship data.",
        {},
    ),
    _tool(
        "people.relationship.list",
        _BOUNDARY + "List active relationship metadata from the encrypted People store.",
        {},
    ),
    _tool(
        "people.relationship.get",
        _BOUNDARY
        + "Get one relationship with only shared-intent 1:1s, agenda items, requests, and commitments.",
        {"relationship_id": {"type": "string", "description": "Opaque relationship identifier."}},
        ["relationship_id"],
    ),
    _tool(
        "people.grounding.get",
        _BOUNDARY
        + "Build a source-preserving grounding bundle from manual shared-intent notes, open requests, commitments, and 1:1s. It does not invoke a model.",
        {"relationship_id": {"type": "string", "description": "Opaque relationship identifier."}},
        ["relationship_id"],
    ),
    _tool(
        "people.relationship.create",
        _BOUNDARY
        + "Create a direct-report relationship. Requires write capability; setup and archive remain Desk-only.",
        {
            "display_name": {"type": "string"},
            "relationship_kind": {"type": "string", "enum": ["direct_report", "peer", "extended"]},
            "role_context": {"type": "string"},
            "timezone": {"type": "string"},
            "cadence": {"type": "string"},
        },
        ["display_name"],
    ),
    _tool(
        "people.one_on_one.create",
        _BOUNDARY
        + "Create a notes-only shared-intent 1:1. Private prep, recording, transcripts, and inference are unavailable.",
        {
            "relationship_id": {"type": "string"},
            "agenda": {"type": "string", "description": "Optional shared 1:1 heading or agenda."},
        },
        ["relationship_id"],
    ),
    _tool(
        "people.agenda.add",
        _BOUNDARY + "Add one shared-intent agenda item to a notes-only 1:1.",
        {
            "session_id": {"type": "string"},
            "body": {"type": "string"},
            "rolled_from_id": {"type": "string", "description": "Optional open agenda item to roll forward atomically."},
        },
        ["session_id", "body"],
    ),
    _tool(
        "people.note.create",
        _BOUNDARY
        + "Create a durable manual shared-intent grounding note. The note is encrypted at rest and is not indexed or submitted to a model.",
        {
            "relationship_id": {"type": "string"},
            "topic": {"type": "string"},
            "body": {"type": "string"},
        },
        ["relationship_id", "body"],
    ),
    _tool(
        "people.request.create",
        _BOUNDARY + "Record a shared-intent request. It remains distinct from a commitment until explicitly accepted.",
        {"relationship_id": {"type": "string"}, "body": {"type": "string"}},
        ["relationship_id", "body"],
    ),
    _tool(
        "people.request.accept",
        _BOUNDARY
        + "Explicitly accept one shared-intent request as a manager commitment. Private requests are refused.",
        {
            "request_id": {"type": "string"},
            "body": {"type": "string", "description": "Optional explicit commitment wording."},
        },
        ["request_id"],
    ),
    _tool(
        "people.commitment.transition",
        _BOUNDARY
        + "Apply done, dismiss, or reopen to a shared-intent manager commitment in the encrypted authority.",
        {
            "commitment_id": {"type": "string"},
            "verb": {"type": "string", "enum": ["done", "dismiss", "reopen"]},
        },
        ["commitment_id", "verb"],
    ),
    _tool(
        "people.one_on_one.brief",
        _BOUNDARY
        + "Compute a read-time 1:1 preparation brief for a relationship. "
        "Returns open shared-intent commitments, agenda items, grounding note count, "
        "the last linked meetings with their open action items, decision records, "
        "and the count of un-linked meetings in the window. "
        "Never persists any data. Leader-private items are never returned.",
        {"relationship_id": {"type": "string", "description": "Opaque relationship identifier."}},
        ["relationship_id"],
    ),
    _tool(
        "people.calendar.link",
        _BOUNDARY
        + "Link a recurring calendar series to a relationship. The link is encrypted owner-selected evidence. "
        "Invariant P1: a series already linked to another person refuses with series_already_linked.",
        {
            "relationship_id": {"type": "string", "description": "Opaque relationship identifier."},
            "uid": {"type": "string", "description": "Calendar event UID (series-level)."},
            "source_id": {"type": "string", "description": "Calendar source identifier."},
            "label": {"type": "string", "description": "Event title at link time (owner-selected evidence)."},
        },
        ["relationship_id", "uid", "source_id"],
    ),
    _tool(
        "people.calendar.unlink",
        _BOUNDARY
        + "Remove a calendar series link from a relationship. Idempotent.",
        {
            "relationship_id": {"type": "string", "description": "Opaque relationship identifier."},
            "uid": {"type": "string", "description": "Calendar event UID (series-level)."},
            "source_id": {"type": "string", "description": "Calendar source identifier."},
        },
        ["relationship_id", "uid", "source_id"],
    ),
    _tool(
        "people.owner_alias.link",
        _BOUNDARY
        + "Link an owner-string alias to a relationship. The alias maps a free-text owner string "
        "from action items to this person. Invariant P2: an alias held by another person refuses "
        "with owner_alias_taken. Reserved strings (Me, Remote, you) are refused.",
        {
            "relationship_id": {"type": "string", "description": "Opaque relationship identifier."},
            "alias": {"type": "string", "description": "The exact owner string to map."},
        },
        ["relationship_id", "alias"],
    ),
    _tool(
        "people.owner_alias.unlink",
        _BOUNDARY
        + "Remove an owner-string alias from a relationship. Idempotent.",
        {
            "relationship_id": {"type": "string", "description": "Opaque relationship identifier."},
            "alias": {"type": "string", "description": "The owner string alias to remove."},
        },
        ["relationship_id", "alias"],
    ),
    # HS-172-04: resolve a Watch identity to a People relationship.
    _tool(
        "people.resolve",
        _BOUNDARY
        + "Resolve a Watch identity string (GitHub login, Jira display name) to a People "
        "relationship. Returns ONLY the opaque relationship id -- never the name or alias "
        "(Article III). Returns null when no match.",
        {
            "identity": {"type": "string", "description": "The identity string to resolve (e.g. a GitHub login or Jira display name)."},
        },
        ["identity"],
    ),
]


def access_mode(environ: Mapping[str, str] | None = None) -> str:
    """Return the process-boundary capability, refusing unknown values.

    HS-139-08: default is "write" (was "off"). The owner ruling (ledger-not-gate)
    opens the MCP People capability for the local owner process. The env var
    overrides when set explicitly.
    """
    env = os.environ if environ is None else environ
    value = str(env.get(ACCESS_ENV) or "write").strip().lower()
    if value not in _ACCESS_MODES:
        raise PeopleServiceError("people_mcp_access_invalid")
    return value


def build_people_service() -> PeopleService:
    """Compose the same encrypted authority as the web surface, without fallback."""
    try:
        return PeopleService(production_people_store())
    except Exception:
        return PeopleService(UnavailablePeopleStore())


def readiness(principal: Principal) -> dict[str, Any]:
    """Return a content-free capability/readiness view without implicit setup."""
    mode = access_mode()
    if mode == "off":
        return {
            "access": "disabled",
            "disclosure": "shared_intent_only",
            "store": "not_opened",
            "reason_code": "people_mcp_access_disabled",
        }
    result = dict(build_people_service().readiness(principal))
    result.update({"access": mode, "disclosure": "shared_intent_only"})
    return result


def list_relationships(principal: Principal) -> list[dict[str, Any]]:
    _require_access(write=False)
    return build_people_service().list_relationships(principal)


def get_relationship(principal: Principal, relationship_id: str) -> dict[str, Any]:
    _require_access(write=False)
    detail = build_people_service().get_relationship(principal, relationship_id)
    return _shared_relationship(detail)


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route People tools through one capability gate and the People service."""
    if not any(tool["name"] == name for tool in TOOLS):
        raise LookupError(name)
    if name == "people.readiness":
        return readiness(principal)
    if name == "people.relationship.list":
        return list_relationships(principal)
    if name == "people.relationship.get":
        return get_relationship(principal, _required_id(arguments, "relationship_id"))
    if name == "people.grounding.get":
        detail = get_relationship(principal, _required_id(arguments, "relationship_id"))
        return _grounding_bundle(detail)
    if name == "people.one_on_one.brief":
        return one_on_one_brief(principal, _required_id(arguments, "relationship_id"))

    _require_access(write=True)
    service = build_people_service()
    if name == "people.relationship.create":
        return service.create_relationship(principal, {
            "display_name": arguments.get("display_name"),
            "role_context": arguments.get("role_context", ""),
            "timezone": arguments.get("timezone", ""),
            "cadence": arguments.get("cadence", ""),
            "relationship_kind": arguments.get("relationship_kind", "direct_report"),
        })
    if name == "people.one_on_one.create":
        value = service.create_one_on_one(
            principal,
            _required_id(arguments, "relationship_id"),
            {"agenda": arguments.get("agenda", ""), "private_prep": "", "visibility": _SHARED},
        )
        return _shared_session(value)
    if name == "people.agenda.add":
        payload = {"body": arguments.get("body"), "visibility": _SHARED}
        if "rolled_from_id" in arguments:
            payload["rolled_from_id"] = arguments["rolled_from_id"]
        return service.add_agenda_item(principal, _required_id(arguments, "session_id"), payload)
    if name == "people.note.create":
        return service.create_note(
            principal,
            _required_id(arguments, "relationship_id"),
            {"topic": arguments.get("topic", ""), "body": arguments.get("body"), "visibility": _SHARED},
        )
    if name == "people.request.create":
        return service.create_request(
            principal,
            _required_id(arguments, "relationship_id"),
            {"body": arguments.get("body"), "visibility": _SHARED},
        )
    if name == "people.request.accept":
        request_id = _required_id(arguments, "request_id")
        request = service.get_request(principal, request_id)
        _require_shared(request)
        payload = {"body": arguments["body"]} if "body" in arguments else None
        return service.accept_request(principal, request_id, payload)
    if name == "people.commitment.transition":
        commitment_id = _required_id(arguments, "commitment_id")
        commitment = service.get_commitment(principal, commitment_id)
        _require_shared(commitment)
        return service.transition(principal, f"people:{commitment_id}", str(arguments.get("verb") or ""))
    if name == "people.calendar.link":
        return service.link_calendar_series(
            principal,
            _required_id(arguments, "relationship_id"),
            _required_id(arguments, "uid"),
            _required_id(arguments, "source_id"),
            str(arguments.get("label") or ""),
        )
    if name == "people.calendar.unlink":
        return service.unlink_calendar_series(
            principal,
            _required_id(arguments, "relationship_id"),
            _required_id(arguments, "uid"),
            _required_id(arguments, "source_id"),
        )
    if name == "people.owner_alias.link":
        return service.link_owner_alias(
            principal,
            _required_id(arguments, "relationship_id"),
            str(arguments.get("alias") or ""),
        )
    if name == "people.owner_alias.unlink":
        return service.unlink_owner_alias(
            principal,
            _required_id(arguments, "relationship_id"),
            str(arguments.get("alias") or ""),
        )
    if name == "people.resolve":
        identity = str(arguments.get("identity") or "").strip()
        if not identity:
            return {"relationship_id": None}
        result = service.resolve_relationship_by_watch_identity(identity)
        rel = result.get("relationship")
        # Return ONLY the id -- never the name or alias (Article III).
        return {"relationship_id": rel.get("id") if rel else None}
    raise LookupError(name)


def _require_access(*, write: bool) -> str:
    mode = access_mode()
    if mode == "off":
        raise PeopleServiceError("people_mcp_access_disabled")
    if write and mode != "write":
        raise PeopleServiceError("people_mcp_write_required")
    return mode


def _required_id(arguments: dict[str, Any], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PeopleServiceError("people_mcp_identifier_required")
    return value.strip()


def _require_shared(record: dict[str, Any]) -> None:
    try:
        visibility = Visibility(str(record.get("visibility") or ""))
    except ValueError as exc:
        raise PeopleServiceError("people_mcp_private_record_refused") from exc
    if not PeoplePolicy.allows(visibility, PeopleOperation.MCP_WRITE):
        raise PeopleServiceError("people_mcp_private_record_refused")


def _shared_session(session: dict[str, Any]) -> dict[str, Any]:
    """Project a session without ever carrying its private-prep field."""
    result = {
        key: session.get(key)
        for key in ("id", "relationship_id", "visibility", "state", "created_at", "updated_at")
    }
    if isinstance(session.get("agenda"), str):
        result["agenda"] = session["agenda"]
    return result


def _shared_relationship(detail: dict[str, Any]) -> dict[str, Any]:
    result = {
        key: detail.get(key)
        for key in (
            "id", "display_name", "relationship_kind", "role_context", "timezone",
            "cadence", "project_refs", "calendar_links", "owner_aliases", "state", "created_at", "updated_at",
        )
    }
    sessions = []
    for session in detail.get("sessions") or []:
        if not isinstance(session, dict) or not _mcp_readable(session):
            continue
        projected = _shared_session(session)
        projected["agenda_items"] = [
            dict(item)
            for item in session.get("agenda") or []
            if isinstance(item, dict) and _mcp_readable(item)
        ]
        sessions.append(projected)
    result["sessions"] = sessions
    result["requests"] = [
        dict(item)
        for item in detail.get("requests") or []
        if isinstance(item, dict) and _mcp_readable(item)
    ]
    result["commitments"] = [
        dict(item)
        for item in detail.get("commitments") or []
        if isinstance(item, dict) and _mcp_readable(item)
    ]
    result["notes"] = [
        dict(item)
        for item in detail.get("notes") or []
        if isinstance(item, dict) and _mcp_readable(item)
    ]
    return result


def one_on_one_brief(principal: Principal, relationship_id: str) -> dict[str, Any]:
    """HS-149-04 F6: _require_access + shared_intent-only through _mcp_readable."""
    _require_access(write=False)
    service = build_people_service()
    # Cross-boundary: get the main DB for plaintext meeting data.
    try:
        from holdspeak.db import get_database
        db = get_database()
    except Exception:
        db = None
    brief = service.one_on_one_brief(principal, relationship_id, db=db)
    # F6: filter encrypted items to shared_intent only via _mcp_readable.
    brief["open_commitments"] = [
        item for item in brief.get("open_commitments") or []
        if isinstance(item, dict) and _mcp_readable(item)
    ]
    brief["agenda_items"] = [
        item for item in brief.get("agenda_items") or []
        if isinstance(item, dict) and _mcp_readable(item)
    ]
    # F7: policy disclosure block (grounding-bundle pattern).
    brief["policy"] = {
        "visibility": "shared_intent_only",
        "source": "manual",
        "inference": "client_owned",
        "employment_decisions": "prohibited",
    }
    return brief


def _grounding_bundle(detail: dict[str, Any]) -> dict[str, Any]:
    """Return explicit evidence, never an inferred assessment of a person."""
    return {
        "relationship": {
            key: detail.get(key)
            for key in ("id", "display_name", "relationship_kind", "role_context", "timezone", "cadence", "project_refs", "calendar_links", "owner_aliases")
        },
        "grounding": {
            "notes": list(detail.get("notes") or []),
            "open_requests": [item for item in detail.get("requests") or [] if item.get("state") == "requested"],
            "open_commitments": [item for item in detail.get("commitments") or [] if item.get("state") == "open"],
            "one_on_ones": list(detail.get("sessions") or []),
        },
        "policy": {
            "visibility": "shared_intent_only",
            "source": "manual",
            "inference": "client_owned",
            "employment_decisions": "prohibited",
        },
    }


def _mcp_readable(record: dict[str, Any]) -> bool:
    try:
        visibility = Visibility(str(record.get("visibility") or ""))
    except ValueError:
        return False
    return PeoplePolicy.allows(visibility, PeopleOperation.MCP_READ)
