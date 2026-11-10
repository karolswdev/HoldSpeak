"""The paired devices' sync and the mesh inbox on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``calls_operations.py`` is. Each row states one verb of
``SyncService`` or ``MeshService`` once; ``web/routes/sync.py`` and
``web/routes/mesh.py`` produce the routes, ``mcp/families/declared.py`` the
tools. These routes are the OWNER's at the edge (``principals.required_right``).

The discovery row is public and served by MeshService. Only the relay HTTP
transports stay hand-written: they hold the node credential derived by the
edge (request.state.node_credential), pass it through the registry as held
input, and keep the service's node identity and generation checks unchanged.
The relay rows have no MCP tool and add no desk-change frame on a poll.

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
_REFUSALS = _CONTRACT_REFUSALS + ("NotFound: unknown artifact", "ValidationError", "ConflictError",
    "mesh_node_authentication_required", "mesh_node_identity_mismatch")
_ID = {"type": "string", "minLength": 1}


def _op(name: str, service: str, method: str, http: tuple[str, str], handler: str, call: Call,
        description: str, *, write: bool = False, tool: bool = True,
        properties: Optional[Mapping[str, Any]] = None, held: tuple[str, ...] = (),
        strict: bool = False, quiet: bool = False) -> OperationDescriptor:
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    schema = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
              "required": ids, "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema=schema if strict else {"type": "object"}, principal=("the edge-authenticated node, with its credential held outside JSON" if "credential" in held else _ANY),
        effect="write" if write else "read", result=f"the {service} answer", refusals=_REFUSALS,
        completion="synchronous; a write is one desk_changed frame on the hub bus" if write else "synchronous",
        exposure=(f"http:{http[0]} {http[1]}",) + ((f"mcp:{name}",) if tool else ()),
        service=service, method=method, call=call, http=http, handler=handler,
        tool_schema=schema if tool else None, held=held, announces_changes=quiet,
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
    _op("mesh.info", "mesh_service", "info", ("GET", "/api/mesh/info"), "api_mesh_info",
        lambda s, p, a: s.info(p),
        "HTTP-only public discovery: an iPad reads the hub name, version and token requirement.", tool=False),
    _op("mesh.relay.claim", "mesh_service", "claim_relay", ("POST", "/api/mesh/relay/claim"),
        "api_mesh_relay_claim", lambda s, p, a: s.claim_relay(p, a.get("payload") or {}, credential=a["credential"]),
        "HTTP-only node callback: claim relay work with the edge-held node credential. Agents refuse.",
        write=True, tool=False, held=("credential",), strict=True, quiet=True,
        properties={"payload": {"type": "object"}}),
    _op("mesh.relay.complete", "mesh_service", "complete_relay", ("POST", "/api/mesh/relay/{job_id}/complete"),
        "api_mesh_relay_complete",
        lambda s, p, a: s.complete_relay(p, a["job_id"], a.get("payload") or {}, credential=a["credential"]),
        "HTTP-only node callback: settle relay work with the edge-held node credential. Agents refuse.",
        write=True, tool=False, held=("credential",), strict=True, quiet=True,
        properties={"payload": {"type": "object"}}),
    _op("mesh.relay.fail", "mesh_service", "fail_relay", ("POST", "/api/mesh/relay/{job_id}/fail"),
        "api_mesh_relay_fail",
        lambda s, p, a: s.fail_relay(p, a["job_id"], a.get("payload") or {}, credential=a["credential"]),
        "HTTP-only node callback: record a relay failure with the edge-held node credential. Agents refuse.",
        write=True, tool=False, held=("credential",), strict=True, quiet=True,
        properties={"payload": {"type": "object"}}),
    _op("mesh.inbox", "mesh_service", "list_inbox", ("GET", "/api/mesh/inbox"), "api_mesh_inbox",
        lambda s, p, a: s.list_inbox(p),
        "Read the mesh inbox: the queued intelligence and plugin jobs and the proposals that wait for a press."),
)

__all__ = ["DEVICE_OPERATIONS"]
