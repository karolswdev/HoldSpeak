"""The capability run receipts (``/api/invocations``) on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Two reads of
``InvocationService``: the list the capability pullout shows and one receipt
(the desk projection of a run names it as its ``source_api``).
``web/routes/primitives/invocations.py`` produces the routes and
``mcp/families/declared.py`` the tools. A read is evidence, MCP and HTTP
only (``thread_modes._family_reads``); a launched agent reads them.
Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from holdspeak.operations import _CONTRACT_REFUSALS, Admission, OperationDescriptor

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_READ = Admission("exempt", "A read: computation without effect (Article XI.5).")

INVOCATION_OPERATIONS: tuple[OperationDescriptor, ...] = (
    OperationDescriptor(
        name="invocation.list", version=1,
        description="List the capability runs, newest first: each run's capability, engine, state and times.",
        args_schema={"type": "object"}, principal=_PRINCIPAL, effect="read", result="{invocations: [...]}",
        refusals=_CONTRACT_REFUSALS, completion="synchronous; nothing changes",
        exposure=("http:GET /api/invocations", "mcp:invocation.list"),
        service="invocation_service", method="list", admission=_READ,
        call=lambda s, p, a: {"invocations": s.list(p, limit=int(a.get("limit") or 100))},
        http=("GET", "/api/invocations"), handler="api_list_invocations",
        tool_schema={"type": "object", "properties": {
            "limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Default 100."}},
            "required": [], "additionalProperties": False},
        thread="evidence_read",
    ),
    OperationDescriptor(
        name="invocation.get", version=1,
        description="Read one capability run: its receipt, state, engine and result.",
        args_schema={"type": "object"}, principal=_PRINCIPAL, effect="read", result="{invocation: {...}}",
        refusals=_CONTRACT_REFUSALS + ("NotFound: unknown invocation",), completion="synchronous; nothing changes",
        exposure=("http:GET /api/invocations/{invocation_id}", "mcp:invocation.get"),
        service="invocation_service", method="get", admission=_READ,
        call=lambda s, p, a: {"invocation": s.get(p, str(a.get("invocation_id") or ""))},
        http=("GET", "/api/invocations/{invocation_id}"), handler="api_get_invocation",
        tool_schema={"type": "object", "properties": {"invocation_id": {"type": "string", "minLength": 1}},
                     "required": ["invocation_id"], "additionalProperties": False},
        thread="evidence_read",
    ),
)

__all__ = ["INVOCATION_OPERATIONS"]
