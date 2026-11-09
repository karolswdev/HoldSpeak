"""The verbs of the delivery runtime (``/api/delivery``) on ``DeliveryService``, on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one verb
once: its call, its HTTP method and path, and its MCP tool schema.
``web/routes/delivery_declared.py`` produces the routes and ``mcp/families/declared.py``
the tools from these rows, both through ``OperationRegistry.invoke``.

A read is ``thread="evidence_read"`` and stays MCP and HTTP only (the seeded
thread palettes do not grow, ``services/thread_modes.py``); a write is
``thread="effect_proposal"``. A launched agent reads these reads and never
calls these writes (``services/conductor_launch.py`` derives both rules from
the rows). Imported only through ``holdspeak.operations`` (it imports this module).

These verbs keep hand-written routes: the node link (``node/hello``,
``node/heartbeat``: node-token traffic), the verbs that spawn an agent or a
process (``factory/launch``, ``prs/.../send-agent``, ``terminal/commands``),
the verbs that post to GitHub (``prs/.../propose``, ``prs/proposals/.../decide``),
the review draft (a model call through the engine door) and the NDJSON
terminal stream (``terminal/live``).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + ("a typed delivery refusal (its code, and the HTTP status and body in its context)",)
_ID = {"type": "string", "minLength": 1}
_TEXT = {"type": "string"}


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        write: bool = False, owner_only: bool = False, properties: Optional[Mapping[str, Any]] = None,
        required: tuple[str, ...] = (), blocking_io: bool = False, web_call: Optional[Call] = None,
        result: str = "the DeliveryService answer, as the route answered it") -> OperationDescriptor:
    """One verb of ``delivery_service``; its tool requires the path's ids and ``required``."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    tool = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result=result, refusals=_REFUSALS,
        completion="synchronous; a write is one desk_changed frame on the hub bus",
        exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"), service="delivery_service", method=method,
        owner_only=owner_only or write, blocking_io=blocking_io, call=call, web_call=web_call, http=http,
        handler=handler, tool_schema=tool, thread="effect_proposal" if write else "evidence_read",
    )


_D = "/api/delivery"
_PR = _D + "/prs/{source_id}/{number}"
DELIVERY_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("delivery.snapshot", "snapshot", ("GET", _D + "/snapshot"), "api_delivery_snapshot",
        lambda s, p, a: s.snapshot(p),
        "Read the delivery snapshot: every registered source with its freshness. The snapshot is cached; "
        "a read does not run dw or gh.", blocking_io=True),
    _op("delivery.sources", "sources", ("GET", _D + "/sources"), "api_delivery_sources",
        lambda s, p, a: s.sources(p), "List the registered delivery sources with their labels and status."),
    _op("delivery.source_register", "register_source", ("POST", _D + "/sources"), "api_delivery_register_source",
        lambda s, p, a: s.register_source(p, a.get("path"), a.get("label")),
        "Register a delivery source by its path. The hub resolves and validates the path.", write=True,
        properties={"path": _ID, "label": _TEXT}, required=("path",), blocking_io=True),
    _op("delivery.attempts", "list_attempts", ("GET", _D + "/attempts"), "api_delivery_list_attempts",
        lambda s, p, a: s.list_attempts(p, a.get("source_id", ""), a.get("project", ""), a.get("story_id", ""),
                                        a.get("session_id", ""), a.get("active_only", False)),
        "List the work attempts with their state and origin. Filter by source, project, story or session.",
        properties={"source_id": _TEXT, "project": _TEXT, "story_id": _TEXT, "session_id": _TEXT,
                    "active_only": {"type": "boolean"}}, blocking_io=True),
    _op("delivery.attempt_create", "create_attempt", ("POST", _D + "/attempts"), "api_delivery_create_attempt",
        lambda s, p, a: s.create_attempt(p, a.get("source_id"), a.get("worktree_id"), a.get("project"),
                                         a.get("story_id"), a.get("session_id"), a.get("node_id"),
                                         a.get("target_id")),
        "Attach a work attempt to a story by hand. A session that has a live attempt is refused.", write=True,
        properties={"source_id": _ID, "worktree_id": _ID, "project": _ID, "story_id": _ID, "session_id": _TEXT,
                    "node_id": _TEXT, "target_id": _TEXT},
        required=("source_id", "worktree_id", "project", "story_id")),
    _op("delivery.story_dossier", "story_dossier", ("GET", _D + "/stories/{project}/{story}/dossier"),
        "api_story_dossier", lambda s, p, a: s.story_dossier(p, a.get("project"), a.get("story"), a.get("source", "")),
        "Read the evidence dossier of one story. Give source to read one source only.",
        properties={"source": _TEXT}, blocking_io=True),
    _op("delivery.phase_dossier", "phase_dossier", ("GET", _D + "/phases/{project}/{phase}/dossier"),
        "api_phase_dossier", lambda s, p, a: s.phase_dossier(p, a.get("project"), a.get("phase"), a.get("source", "")),
        "Read the evidence dossier of one phase: its story dossiers and the final summary. Metadata only.",
        properties={"source": _TEXT}, blocking_io=True),
    _op("delivery.evidence_asset", "evidence_asset", ("GET", _D + "/evidence/{bundle_id}/{asset_id}"),
        "api_evidence_asset",
        lambda s, p, a: s.evidence_asset_wire(p, a.get("bundle_id"), a.get("asset_id")),
        "Read one evidence file that the bundle manifest names, as base64 with its media type.",
        web_call=lambda s, p, a: s.evidence_asset(p, a.get("bundle_id"), a.get("asset_id")), blocking_io=True,
        result="the asset bytes and its manifest member (HTTP: the file; MCP: base64)"),
    _op("delivery.prs", "pr_rows", ("GET", _D + "/prs"), "api_delivery_prs", lambda s, p, a: s.pr_rows(p),
        "List the cached pull requests of the registered sources, with their freshness."),
    _op("delivery.prs_refresh", "refresh_prs", ("POST", _D + "/prs/refresh"), "api_delivery_prs_refresh",
        lambda s, p, a: s.refresh_prs(p, a.get("source_id")),
        "Read the pull requests from GitHub again, for one source or for all sources.", write=True,
        properties={"source_id": _TEXT}, blocking_io=True),
    _op("delivery.pr_diff", "pr_diff", ("GET", _PR + "/diff"), "api_delivery_pr_diff",
        lambda s, p, a: s.pr_diff(p, a.get("source_id"), a.get("number")),
        "Read the local diff of one pull request. If it is not local, the answer says so.", blocking_io=True),
    _op("delivery.pr_fetch", "fetch_pr", ("POST", _PR + "/fetch"), "api_delivery_pr_fetch",
        lambda s, p, a: s.fetch_pr(p, a.get("source_id"), a.get("number")),
        "Fetch the head of one pull request from GitHub, so that its diff is local.", write=True,
        blocking_io=True),
    _op("delivery.nodes", "nodes", ("GET", _D + "/nodes"), "api_delivery_nodes", lambda s, p, a: s.nodes(p),
        "List the delivery nodes with their liveness and the time each was last seen."),
    # The terminal reads are owner-only, as the HTTP edge holds them: they
    # show what the owner's terminals show.
    _op("delivery.terminal_sessions", "terminal_sessions", ("GET", _D + "/terminal/sessions"),
        "api_terminal_sessions", lambda s, p, a: s.terminal_sessions(p),
        "List the local terminal sessions from the live tmux panes.", owner_only=True, blocking_io=True),
    _op("delivery.terminal_read", "terminal_read", ("POST", _D + "/terminal/subscriptions"),
        "api_terminal_subscribe",
        lambda s, p, a: s.terminal_read(p, a.get("target_id"), a.get("target_generation"),
                                        a.get("resume_sequence"), a.get("last_hash")),
        "Read the output of one terminal target: a snapshot, the new output after resume_sequence, "
        "or a typed absence.", owner_only=True,
        properties={"target_id": _ID, "target_generation": _ID, "resume_sequence": {"type": "integer"},
                    "last_hash": _TEXT}, required=("target_id", "target_generation"), blocking_io=True),
    _op("delivery.factory_profiles", "factory_profiles", ("GET", _D + "/factory/profiles"),
        "api_factory_profiles", lambda s, p, a: s.factory_profiles(p),
        "List the agent profiles that this node can launch."),
    _op("delivery.factory_discover", "factory_discover", ("GET", _D + "/factory/discover"),
        "api_factory_discover", lambda s, p, a: s.factory_discover(p),
        "List the agent panes and sessions as targets. The read first binds new story claims.",
        blocking_io=True),
)

__all__ = ["DELIVERY_OPERATIONS"]
