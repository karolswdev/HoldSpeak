"""The Walk's and the briefing page's verbs on the one declared contract (2026-11-09, ops/projects).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one
``WalkService`` or ``BriefingService`` verb once: its call, its HTTP method and
path, and its MCP tool schema. ``mcp/families/declared.py`` produces the tools.

The token routes are a security surface. The token is the only authority on
``/api/w/{token}`` and ``/api/b/{token}``: the service checks it (hash, expiry,
revocation) in ``WalkService._by_token`` and ``BriefingService._package`` and
refuses an unknown one (``walk_not_found``, ``page_expired``), on every
transport. The HTTP handlers stay hand-written in ``web/routes/walks.py`` and
``web/routes/briefing.py``: the per-address miss limit and the body bound run
BEFORE the service, then the handler invokes the declared row. The owner rows
(``walk.create``, ``walk.read``, ``briefing.revoke``) are ``owner_only``: the
registry refuses any other principal before the service runs, and
``BriefingService._require_owner`` still refuses one itself.

Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_TOKEN_PRINCIPAL = ("none: the page token in the arguments is the only authority; the service checks its hash, "
                    "expiry and revocation")
_TOKEN = {"type": "string", "minLength": 1, "description": "The page token: the last segment of the page link."}
_ID = {"type": "string", "minLength": 1}


def _op(name: str, service: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        write: bool = False, properties: Optional[Mapping[str, Any]] = None, required: tuple[str, ...] = (),
        principal: str = _PRINCIPAL, owner_only: bool = False, authority: str = "work",
        announces: bool = False, status: int = 200, refusals: tuple[str, ...] = (), result: str = "") -> OperationDescriptor:
    """One verb; its tool requires the path's ids and ``required``. A non-work tool is never a thread tool."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    tool = {"type": "object", "properties": {**{key: (_TOKEN if key == "token" else _ID) for key in ids},
                                             **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=principal,
        effect="write" if write else "read", result=result or f"the {service} answer",
        refusals=_CONTRACT_REFUSALS + refusals,
        completion="synchronous" + ("; a write is one desk_changed frame on the hub bus" if write else ""),
        exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"), service=service, method=method,
        owner_only=owner_only, announces_changes=announces, call=call, http=http, http_status=status,
        handler=handler, tool_schema=tool, authority=authority,
        thread=None if authority != "work" else ("effect_proposal" if write else "evidence_read"),
    )


_WALK_REFUSALS = ("WalkRefused walk_not_found: an unknown token or walk id",
                  "WalkRefused walk_invalid: a script that is not a walk")
_PAGE_REFUSALS = ("BriefingRefused page_expired: an unknown, expired or revoked token",
                  "BriefingRefused pane_unknown", "BriefingRefused answered_already")

WALK_OPERATIONS: tuple[OperationDescriptor, ...] = (
    OperationDescriptor(
        name="walk.known", version=1, description="Check the page token before the shell redirect or body read.",
        args_schema={"type": "object", "properties": {"token": _TOKEN}, "required": ["token"],
                     "additionalProperties": False}, principal=_TOKEN_PRINCIPAL, effect="read", result="boolean",
        refusals=_CONTRACT_REFUSALS, completion="synchronous; checks only the token hash",
        exposure=("http:GET /w/{token}", "http:POST /api/w/{token}/answer"),
        service="walk_service", method="known", call=lambda s, p, a: s.known(a.get("token")),
        http_only_reason="The page checks its token before a redirect or bounded body read; the token is its authority.",
    ),
    _op("walk.create", "walk_service", "create", ("POST", "/api/walks"), "api_walk_create",
        lambda s, p, a: s.create(a),
        "Store a guided walk (a title and its steps) and give its page token, once. The link is url_path.",
        write=True, owner_only=True, status=201,
        properties={"title": {"type": "string"}, "steps": {"type": "array", "items": {"type": "object"}}},
        required=("title", "steps"), refusals=_WALK_REFUSALS, result="{id, token, url_path}"),
    _op("walk.read", "walk_service", "read", ("GET", "/api/walks/{walk_id}"), "api_walk_read",
        lambda s, p, a: s.read(str(a.get("walk_id") or "")),
        "Read one walk: its script, its answers and the folder that holds the shots.",
        owner_only=True, refusals=_WALK_REFUSALS, result="the walk record, its answers and its directory"),
    _op("walk.page", "walk_service", "page", ("GET", "/api/w/{token}"), "api_walk_page",
        lambda s, p, a: s.page(a.get("token")),
        "Read the walk a page token opens: its title, its steps and the answers so far.",
        principal=_TOKEN_PRINCIPAL, refusals=_WALK_REFUSALS, result="{title, steps, answers}"),
    _op("walk.answer", "walk_service", "answer", ("POST", "/api/w/{token}/answer"), "api_walk_answer",
        lambda s, p, a: s.answer(a.get("token"), a.get("ref"), a.get("choice"), words=a.get("words"),
                                 window_png=a.get("window_png"), view=a.get("view")),
        "Answer one question of a walk: a choice, or words.", write=True, principal=_TOKEN_PRINCIPAL,
        properties={"ref": _ID, "choice": {"type": "string"}, "words": {"type": "string"},
                    "window_png": {"type": "string", "description": "Optional base64 PNG of the window."},
                    "view": {"type": "object"}},
        required=("ref", "choice"),
        refusals=_WALK_REFUSALS + ("WalkRefused walk_unknown_ask", "WalkRefused walk_unknown_choice"),
        result="{ref, choice, ...} as stored"),
    _op("briefing.read", "briefing_service", "read", ("GET", "/api/b/{token}"), "api_briefing_read",
        lambda s, p, a: s.read(a.get("token")),
        "Read the briefing page a token opens: the package, each item's state now and the Later times.",
        principal=_TOKEN_PRINCIPAL, refusals=_PAGE_REFUSALS, result="{package, items, later}"),
    _op("briefing.evidence", "briefing_service", "evidence", ("GET", "/api/b/{token}/evidence/{ref}/{pane}"),
        "api_briefing_evidence", lambda s, p, a: s.evidence(a.get("token"), a.get("ref"), a.get("pane")),
        "Read one evidence pane of one item on a briefing page.", principal=_TOKEN_PRINCIPAL,
        refusals=_PAGE_REFUSALS, result="{pane, kind: rows | code, ...}"),
    # The page's answer decides the owner's item: never a thread tool.
    _op("briefing.answer", "briefing_service", "answer", ("POST", "/api/b/{token}/answer"), "api_briefing_answer",
        lambda s, p, a: s.answer(a.get("token"), a.get("ref"), a.get("choice"), reason=a.get("reason"),
                                 later=a.get("later"), binding=a.get("binding")),
        "Answer one item on a briefing page through the item's own verb; Later records the next touch.",
        write=True, principal=_TOKEN_PRINCIPAL, authority="authority", announces=True,
        properties={"binding": {"type": ["object", "null"]}, "ref": _ID, "choice": {"type": "string"}, "reason": {"type": "string"},
                    "later": {"type": "string"}},
        required=("ref", "choice"), refusals=_PAGE_REFUSALS, result="{item}"),
    _op("briefing.revoke", "briefing_service", "revoke", ("POST", "/api/reach/packages/{package_id}/revoke"),
        "api_reach_package_revoke", lambda s, p, a: s.revoke(p, str(a.get("package_id") or "")),
        "End a briefing page now: its link reads nothing after this.", write=True, owner_only=True,
        authority="authority", announces=True,
        refusals=("BriefingRefused owner_only", "BriefingRefused package_unknown"), result="{id, revoked: true}"),
)

__all__ = ["WALK_OPERATIONS"]
