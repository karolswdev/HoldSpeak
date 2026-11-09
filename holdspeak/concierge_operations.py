"""The Engines window's verbs on the one declared contract (2026-11-09, ops/connections).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``). Each row states one ``ConciergeService`` verb once
(``services/concierge_service.py``): ``web/routes/concierge.py`` produces the
routes and ``mcp/families/declared.py`` the tools. The hand-written MCP family
(``mcp/families/_parked/concierge.py``) and the route bodies it mirrored are
parked: one implementation.

Every row is owner only (the routes always were; the old MCP twin was not).
The reads are evidence. A probe reaches an engine (a LAN box, a cloud key with
``generate``, a real request with ``task``), a download fetches a model and a
LAN look scans his private network: egress, his press. The engine set and the
summary selection change the system: config, his press. Retry runs a job
again on his assigned route: his work.
"""
from __future__ import annotations

from typing import Any

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor

_OWNER = "derived by the transport (HTTP auth middleware; MCP auth resolver); owner only"
_REFUSALS = _CONTRACT_REFUSALS + ("owner_required", "concierge_unavailable")


def _row(name: str, method: str, http: tuple[str, str], handler: str, call: Any, description: str, *,
         result: str, write: bool = False, authority: str = "work", press: bool = False, tool: Any = None,
         status: int = 200, refusals: tuple[str, ...] = (), properties: dict[str, Any] | None = None,
         completion: str = "synchronous") -> OperationDescriptor:
    return OperationDescriptor(
        name=name, version=1, description=description,
        # The arguments are checked by the service, which refuses with its own codes (concierge_*_invalid);
        # ``properties`` only types a query string (``?fresh=1``).
        args_schema={"type": "object", "properties": dict(properties or {})}, principal=_OWNER,
        effect="write" if write else "read", result=result, refusals=_REFUSALS + refusals, completion=completion,
        exposure=(f"http:{http[0]} {http[1]}",) + ((f"mcp:{name}",) if tool is not None else ()),
        service="concierge_service", method=method, owner_only=True, owner_press=press, blocking_io=True,
        call=call, http=http, http_status=status, handler=handler, tool_schema=tool, authority=authority,
        thread=("effect_proposal" if write or press else "evidence_read") if tool is not None else None,
    )


def _tool(properties: dict[str, Any] | None = None, required: tuple[str, ...] = ()) -> dict[str, Any]:
    return {"type": "object", "properties": dict(properties or {}), "required": list(required),
            "additionalProperties": False}


_ENGINE_ID = {"type": "string", "minLength": 1, "maxLength": 256}
_PROBE = {
    "engineId": {**_ENGINE_ID, "description": "The engine to reach: engines[].id from concierge.detect."},
    "generate": {"type": "boolean", "description": "A cloud engine: one explicit one-token request (cost: 1 token)."},
    "task": {"type": "boolean", "description": "One real request through the assigned route of capabilityId."},
    "capabilityId": {"type": "string", "description": "With task: the capability whose route is probed."},
    "expectedProfileIds": {"type": "array", "items": {"type": "string"},
                           "description": "With task: the profiles the route must resolve to."},
    "confirmOffMachine": {"type": "boolean", "description": "With task: allow a route that leaves this Mac."},
}
_ROWS = {"type": "array", "minItems": 1, "items": {
    "type": "object", "required": ["group"],
    "properties": {"group": {"type": "string"}, "engineId": {"type": ["string", "null"]}, "state": {"type": "string"}},
}}
_SELECTION = {
    "commandId": {"type": "string", "minLength": 1, "description": "The press's idempotency key."},
    "expectedAssignmentRevision": {"type": "integer", "minimum": 0},
    "profileId": {"type": "string", "minLength": 1},
    "profileRevision": {"type": "integer", "minimum": 1},
    "setDefault": {"type": "boolean", "description": "Also make it the Default for AI work, once, when none exists."},
}
_P = "/api/concierge"

CONCIERGE_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _row("concierge.detect", "detect", ("GET", f"{_P}/detect"), "get_detect",
         lambda s, p, a: s.detect(p, fresh=bool(a.get("fresh"))),
         "See every engine: LAN servers, agent CLIs on this Mac, local files, cloud keys, presets; each one's fit "
         "per group, the named repairs and the last press's outcome. No cloud key generates.",
         result="{engines, groups, summaryAssignment, repairs, lastApply, checkedAt}",
         properties={"fresh": {"type": "boolean", "description": "Check every endpoint now, not its last check."}},
         tool=_tool({"fresh": {"type": "boolean"}})),
    _row("concierge.propose", "propose", ("POST", f"{_P}/propose"), "post_propose",
         lambda s, p, a: s.propose(p),
         "Propose one engine set for the seven capability groups: READY only where the assignment authority "
         "serves the whole group.", result="{rows: [{group, engineId, state, ...}]}", tool=_tool()),
    _row("concierge.probe", "probe", ("POST", f"{_P}/probe"), "post_probe", lambda s, p, a: s.probe(p, dict(a)),
         "Reach one engine. A LAN or local engine always answers; a cloud engine only with generate:true; "
         "task:true sends one real request through the assigned route and names the model that served it.",
         result="{ok, latencyMs, model, egress, ...}, or the task probe's {served_by, boundary, ...}",
         refusals=("concierge_probe_invalid", "concierge_engine_not_found"), authority="egress", press=True,
         tool=_tool(_PROBE)),
    _row("concierge.apply", "apply", ("POST", f"{_P}/apply"), "post_apply", lambda s, p, a: s.apply(p, a.get("rows")),
         "Write the engine set for every group at once. A WAITING group that is not OFF refuses it.",
         result="{status, used, failedGroups, ...}", write=True, authority="config", press=True,
         refusals=("concierge_apply_invalid", "conflict"), tool=_tool({"rows": _ROWS}, ("rows",))),
    _row("concierge.summary_selection", "select_summary", ("POST", f"{_P}/summary-selection"),
         "post_summary_selection", lambda s, p, a: s.select_summary(p, dict(a)),
         "Select one summary engine for Meetings (the owner's one explicit press).",
         result="{status, summaryAssignment, defaultSet?}", write=True, authority="config", press=True,
         refusals=("concierge_summary_selection_invalid",),
         tool=_tool(_SELECTION, ("commandId", "expectedAssignmentRevision", "profileId", "profileRevision"))),
    _row("concierge.speech", "speech", ("GET", f"{_P}/speech"), "get_speech", lambda s, p, a: s.speech(p),
         "See the phone line's two speech models: their licences, size, state and each download's progress.",
         result="{rows: [{id, role, state, bytes, received, total}]}", tool=_tool()),
    _row("concierge.download", "download", ("POST", f"{_P}/download"), "post_download",
         lambda s, p, a: s.download(p, a.get("presetId")),
         "Start one preset download (a model, or a phone speech model). It answers with the job id and its progress.",
         result="{jobId, presetId, progress: {received, total}}", write=True, authority="egress", press=True,
         status=202, refusals=("concierge_download_invalid",),
         tool=_tool({"presetId": {"type": "string", "minLength": 1, "maxLength": 160}}, ("presetId",)),
         completion="asynchronous; GET /api/inference/acquisitions/{jobId}, or concierge.speech for a speech model"),
    # HTTP only: the Engines window's Find on this network, one look per press.
    # setup.lan (setup_operations.py) is the same look in Setup's shape.
    _row("concierge.discover_lan", "discover_lan", ("POST", f"{_P}/discover-lan"), "post_discover_lan",
         lambda s, p, a: s.discover_lan(p),
         "Look once on the owner's private network for engines that answer (/v1/models). It adds no engine.",
         result="{engines: [...], checkedAt}", authority="egress", press=True, refusals=("concierge_lan_refused",)),
    # HTTP only: the Retry press on a Needs-you engine row.
    _row("concierge.retry", "retry", ("POST", f"{_P}/retry"), "post_retry",
         lambda s, p, a: s.retry(p, a.get("kind"), a.get("key")),
         "Run one failed engine job again, through the engine door, by the caller that registered it.",
         result="{ok: true}", write=True, refusals=("concierge_retry_invalid", "no_retry"),),
)


__all__ = ["CONCIERGE_OPERATIONS"]
