"""The activity ledger's web verbs on the one declared contract (2026-11-09, ops/projects).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one verb of
the five activity services once: its call, its HTTP method and path, and its
MCP tool schema. ``web/routes/activity/*.py`` produce the routes and
``mcp/families/declared.py`` the tools from these rows, both through
``OperationRegistry.invoke``.

As in the meeting rows, the arguments schema is any object: the service
validates, as it did behind the hand-written routes; a GET's query values
arrive as text and the call reads them. The meeting-candidate start keeps a
hand-written route (it starts the live capture through the hub's callbacks)
that calls ``activity.meeting_candidate.get`` and
``activity.meeting_candidate.start`` for its service steps.
Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import ValidationError

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + ("NotFound: unknown connector or meeting candidate", "ValidationError")
_ID = {"type": "string", "minLength": 1}
_PROJECT = {"type": "string", "description": "Optional. Only the activity of this project."}


def _flag(value: Any, default: bool) -> bool:
    """A query flag (``?include_disabled=false``) or a JSON boolean."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"} if isinstance(value, str) else bool(value)


def _int(value: Any, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else default
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"expected a whole number, got {value!r}") from exc


def _text(value: Any) -> Optional[str]:
    return str(value) if value not in (None, "") else None


def _op(name: str, method: str, service: str, call: Call, description: str, *,
        http: Optional[tuple[str, str]] = None, handler: Optional[str] = None, write: bool = False,
        properties: Optional[Mapping[str, Any]] = None, required: tuple[str, ...] = (),
        owner_only: bool = False, authority: str = "work", result: str = "the activity service's answer",
        ) -> OperationDescriptor:
    """One verb of *service*; its tool requires the path's ids and ``required``."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")] if http else []
    tool = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    exposure = ((f"http:{http[0]} {http[1]}",) if http else ()) + (f"mcp:{name}",)
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result=result, refusals=_REFUSALS,
        completion="synchronous; a write is one desk_changed frame on the hub bus",
        exposure=exposure, service=service, method=method, call=call, http=http, handler=handler,
        tool_schema=tool, owner_only=owner_only, authority=authority,
        # A read is evidence, a write a proposed effect; the activity family is
        # MCP and HTTP only (thread_modes: the "activity." prefix), so no
        # palette grows. A config row is the owner's press: no thread class.
        thread=None if authority != "work" else ("effect_proposal" if write else "evidence_read"),
    )


def _settings(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    enabled, days = args.get("enabled"), args.get("retention_days")
    if enabled is not None and not isinstance(enabled, bool):
        raise ValidationError("enabled is true or false")
    return service.update_settings(principal, {"enabled": enabled,
                                               "retention_days": None if days is None else _int(days, 0)})


def _ingest(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    events = args.get("events")
    if not isinstance(events, list) or not all(isinstance(event, dict) for event in events):
        raise ValidationError("events is a list of event objects")
    return service.ingest_extension_events(principal, events)


def _start(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    meeting = args.get("meeting")
    if not isinstance(meeting, dict):
        meeting = {"id": str(args.get("meeting_id") or "")} if args.get("meeting_id") else None
    return service.start(principal, str(args.get("candidate_id") or ""), meeting, _text(args.get("warning")))


_LEDGER, _RULES, _ENRICH = "activity_ledger_service", "activity_rules_service", "activity_enrichment_service"
_CANDIDATES, _NUDGES = "activity_meeting_candidate_service", "activity_nudge_service"
_LIMIT = {"limit": {"type": "integer", "minimum": 1}}

ACTIVITY_OPERATIONS: tuple[OperationDescriptor, ...] = (
    # ── the ledger ────────────────────────────────────────────────────
    _op("activity.status", "status", _LEDGER, lambda s, p, a: s.status(p),
        "Read the activity ledger's state: the privacy settings, the browser history sources, the import "
        "checkpoints, the domain rules and the record count.",
        http=("GET", "/api/activity/status"), handler="status"),
    _op("activity.records", "list_records", _LEDGER,
        lambda s, p, a: s.list_records(p, _text(a.get("project_id")), _text(a.get("domain")),
                                       _text(a.get("entity_type")), _int(a.get("limit"), 100)),
        "List the activity records (the pages and work items seen), newest first.",
        http=("GET", "/api/activity/records"), handler="records",
        properties={"project_id": _PROJECT, "domain": {"type": "string"}, "entity_type": {"type": "string"}, **_LIMIT}),
    _op("activity.refresh", "refresh", _LEDGER, lambda s, p, a: s.refresh(p),
        "Import the browser history again now (local files only).",
        http=("POST", "/api/activity/refresh"), handler="refresh", write=True),
    _op("activity.settings.update", "update_settings", _LEDGER, _settings,
        "Turn activity tracking on or off and set how many days records are kept.",
        http=("PUT", "/api/activity/settings"), handler="settings", write=True, owner_only=True,
        authority="config",
        properties={"enabled": {"type": "boolean"}, "retention_days": {"type": "integer", "minimum": 0}}),
    _op("activity.records.delete", "delete_records", _LEDGER,
        lambda s, p, a: s.delete_records(p, _text(a.get("domain")), _text(a.get("project_id"))),
        "Delete activity records: all of them, or one domain's or one project's.",
        http=("DELETE", "/api/activity/records"), handler="delete_records", write=True, owner_only=True,
        properties={"domain": {"type": "string"}, "project_id": _PROJECT}),
    # ── the project rules ─────────────────────────────────────────────
    _op("activity.rule.list", "list", _RULES,
        lambda s, p, a: s.list(p, _flag(a.get("include_disabled"), True)),
        "List the rules that file activity records under a project.",
        http=("GET", "/api/activity/project-rules"), handler="list_rules",
        properties={"include_disabled": {"type": "boolean"}}),
    _op("activity.rule.delete", "delete", _RULES, lambda s, p, a: s.delete(p, str(a.get("rule_id") or "")),
        "Delete one activity project rule.",
        http=("DELETE", "/api/activity/project-rules/{rule_id}"), handler="delete", write=True),
    # ── enrichment ────────────────────────────────────────────────────
    _op("activity.connector.list", "list_connectors", _ENRICH, lambda s, p, a: s.list_connectors(p),
        "List the activity enrichment connectors with their state and the GitHub and Jira CLI status.",
        http=("GET", "/api/activity/enrichment/connectors"), handler="connectors"),
    _op("activity.extension.ingest", "ingest_extension_events", _ENRICH, _ingest,
        "Take the browser extension's activity events into the ledger.",
        http=("POST", "/api/activity/extension/events"), handler="ingest", write=True,
        properties={"events": {"type": "array", "items": {"type": "object"}}}, required=("events",)),
    _op("activity.connector.dry_run", "dry_run", _ENRICH,
        lambda s, p, a: s.dry_run(p, str(a.get("connector_id") or ""), _int(a.get("limit"), 25)),
        "Show what one enrichment connector would write, without writing it.",
        http=("GET", "/api/activity/enrichment/connectors/{connector_id}/dry-run"), handler="dry_run",
        properties=_LIMIT),
    _op("activity.briefing", "briefing", _ENRICH, lambda s, p, a: s.briefing(p),
        "Read the latest meeting-context briefing and its last run.",
        http=("GET", "/api/activity/briefing"), handler="briefing"),
    # ── meeting candidates ────────────────────────────────────────────
    _op("activity.meeting_candidate.list", "list", _CANDIDATES,
        lambda s, p, a: s.list(p, _text(a.get("source_connector_id")), _text(a.get("status")),
                               _int(a.get("limit"), 100)),
        "List the meetings the activity ledger found (calendar and meeting links) that could be recorded.",
        http=("GET", "/api/activity/meeting-candidates"), handler="list_candidates",
        properties={"source_connector_id": {"type": "string"}, "status": {"type": "string"}, **_LIMIT}),
    _op("activity.meeting_candidate.get", "candidate_for_start", _CANDIDATES,
        lambda s, p, a: s.candidate_for_start(p, str(a.get("candidate_id") or "")),
        "Read one meeting candidate.", properties={"candidate_id": _ID}, required=("candidate_id",)),
    _op("activity.meeting_candidate.start", "start", _CANDIDATES, _start,
        "Mark a meeting candidate as started by a meeting (meeting_id). POST "
        "/api/activity/meeting-candidates/{candidate_id}/start also starts the capture.",
        write=True, properties={"candidate_id": _ID, "meeting_id": _ID, "warning": {"type": "string"}},
        required=("candidate_id", "meeting_id")),
    # ── nudges ────────────────────────────────────────────────────────
    _op("activity.nudge.list", "list", _NUDGES,
        lambda s, p, a: s.list(p, _text(a.get("project_id")), _int(a.get("limit"), 3)),
        "List the activity nudges before a meeting: recent work items, each with its source.",
        http=("GET", "/api/activity/nudges"), handler="list_nudges", properties={"project_id": _PROJECT, **_LIMIT}),
    _op("activity.nudge.dismiss", "dismiss", _NUDGES, lambda s, p, a: s.dismiss(p, str(a.get("nudge_id") or "")),
        "Dismiss one activity nudge; it does not come back.",
        http=("POST", "/api/activity/nudges/{nudge_id}/dismiss"), handler="dismiss", write=True),
    _op("activity.nudge.select", "select", _NUDGES, lambda s, p, a: s.select(p, a.get("record_id")),
        "Select one activity record as the context of the next dictation.",
        http=("POST", "/api/activity/nudges/select"), handler="select", write=True,
        properties={"record_id": {"type": "integer"}}, required=("record_id",)),
)

__all__ = ["ACTIVITY_OPERATIONS"]
