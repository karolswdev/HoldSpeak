"""The paired devices' sync and the mesh inbox on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``calls_operations.py`` is. Each row states one verb of
``SyncService`` or ``MeshService`` once; ``web/routes/sync.py`` and
``web/routes/mesh.py`` produce the routes, ``mcp/families/declared.py`` the
tools. These routes are the OWNER's at the edge (``principals.required_right``).

Kept hand-written, and why (``web/routes/mesh.py``): ``GET /api/mesh/info``
(the public discovery answer; no token, no service), and the three relay legs
(``/api/mesh/relay/*``): a NODE protocol whose principal and credential the
edge derives from a node token (``request.state.node_credential``), never
from arguments, as the phone's device-token routes are (#2051).

No tool, and why:

- ``sync.push``: a device's change set, merged into the desk; the iPad's sync
  is its caller.

Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor

Call = Callable[[Any, Any, dict[str, Any]], Any]

_ANY = "derived by the transport (HTTP edge right OWNER; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + ("NotFound: unknown artifact", "ValidationError", "ConflictError")
_ID = {"type": "string", "minLength": 1}


def _op(name: str, service: str, method: str, http: tuple[str, str], handler: str, call: Call,
        description: str, *, write: bool = False, tool: bool = True,
        properties: Optional[Mapping[str, Any]] = None) -> OperationDescriptor:
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    schema = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
              "required": ids, "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_ANY,
        effect="write" if write else "read", result=f"the {service} answer", refusals=_REFUSALS,
        completion="synchronous; a write is one desk_changed frame on the hub bus" if write else "synchronous",
        exposure=(f"http:{http[0]} {http[1]}",) + ((f"mcp:{name}",) if tool else ()),
        service=service, method=method, call=call, http=http, handler=handler,
        tool_schema=schema if tool else None,
        # A read is evidence (MCP and HTTP only: thread_modes._MCP_ONLY); a write a proposal.
        thread=("effect_proposal" if write else "evidence_read") if tool else None,
    )


def _limit(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 50


DEVICE_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("sync.artifact.get", "sync_service", "get_artifact", ("GET", "/api/artifacts/{artifact_id}"),
        "api_get_artifact", lambda s, p, a: s.get_artifact(p, str(a.get("artifact_id") or "")),
        "Read one cited plugin output (an artifact) without changing its review or list state."),
    _op("sync.pull", "sync_service", "pull", ("GET", "/api/sync/pull"), "api_sync_pull",
        lambda s, p, a: s.pull(p, limit=_limit(a.get("limit", 50))),
        "Read the desk's change set for a device: the latest meetings and artifacts (limit 1 to 500, default 50).",
        properties={"limit": {"type": "integer", "minimum": 1, "maximum": 500}}),
    _op("sync.push", "sync_service", "push", ("POST", "/api/sync/push"), "api_sync_push",
        lambda s, p, a: s.push(p, dict(a)),
        "Merge a device's change set into the desk.", write=True, tool=False),
    _op("mesh.inbox", "mesh_service", "list_inbox", ("GET", "/api/mesh/inbox"), "api_mesh_inbox",
        lambda s, p, a: s.list_inbox(p),
        "Read the mesh inbox: the queued intelligence and plugin jobs and the proposals that wait for a press."),
)

__all__ = ["DEVICE_OPERATIONS"]
