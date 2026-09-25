"""HS-174-02: Streamable HTTP transport for MCP (POST /api/mcp).

JSON-RPC in -> handle_message_for_principal -> JSON-RPC out.

**How the composition actually works (HS-200-45).** This docstring used to
claim the route composed "on the web runtime's LIVE services (never the
sidecar's bare serve() instances)". That was false: the route received
``ctx: WebContext``, handed the message to ``handle_message_for_principal``,
and ``tools.dispatch`` rebuilt every service from ``get_database()`` -- bare,
with no broadcast. The context was received and unused for dispatch.

It is true now, and by a different mechanism than "the route passes ctx
along". ``MeetingWebServer._create_app`` installs its composed services as the
process's ONE composition root
(``holdspeak/runtime/composition.py``); ``tools.dispatch`` and every MCP family
read that root. So this route needs to pass nothing: the dispatch it calls
resolves the same ``PrimitiveService`` (with ``on_changed`` bound to the bus),
the same ``MeetingService`` (with its lifecycle callbacks), and the same
``Database`` handle that the hub's HTTP routes use. A ``desk.create`` over this
route therefore puts a ``desk_changed`` frame on ``/ws``, exactly as the
equivalent ``POST /api/notes`` does.

Principal derivation per D3:
- Loopback + owner token -> OWNER (unrestricted).
- Loopback + agent credential -> AGENT (palette from credential).
- Non-loopback + owner token -> 403 (Article XI:4, per-route guard C5).
- Non-loopback + agent credential -> AGENT (palette from credential).
- No match -> 401.

**The enable flag governs the REMOTE listener, not the local transport
(HS-200-45 R3).** ``remote.streamable_http_enabled`` is the owner's switch for
letting *agent credentials from elsewhere* in. A loopback request bearing the
owner's own token is not remote access -- it is the hub's own local transport,
the one the stdio sidecar proxies into so that the sidecar never has to open
the database itself. Refusing that with 404 while the flag is off would leave
the sidecar no lawful path and push it straight back to being a second writer.
So: a loopback OWNER is admitted with the flag off; everything else still needs
the flag on.

Settings routes:
- GET  /api/settings/remote        -> current remote config + credential list
- PUT  /api/settings/remote        -> update enabled/bind_host
- POST /api/settings/remote/credentials -> issue a new credential
- DELETE /api/settings/remote/credentials/{id} -> revoke (the credential's
  LIVE desk grant first, durably, with its own receipt; PHILO-7-02)
- PUT    /api/settings/remote/delegations/{identity} -> delegation.grant
- DELETE /api/settings/remote/delegations/{identity} -> delegation.revoke

PHILO-7-02 (R1): the owner's desk delegation grant rides the credential ledger.
``GET /api/settings/remote`` carries, per credential, ``delegation``: the
grant's EFFECTIVE state ``{state, grant_id, expires_at}`` (``state`` LIVE,
EXPIRED or REVOKED; ``null`` = never granted), computed with the kernel's own
time-aware rule, never the stored state alone; and ``delegations``: the same
projection, with ``identity``, for every identity that has a grant row (LIVE or
historical) and NO credential row. Both are read whatever the remote switch
says: the switch governs transport, not authority.
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from ...logging_config import get_logger
from ...principals import (
    AgentCredentialStore,
    PrincipalKind,
    UNAUTHENTICATED,
)
from ...services.observer import _origin, _caller, _caller_identity
from ...web_auth import is_loopback_host
from ..context import WebContext

log = get_logger("web.routes.mcp_http")

# HS-174 C5: the per-route loopback guard applies ONLY to POST /api/mcp.
# The owner's browser over the tailnet keeps its session through the
# existing _web_auth_gate middleware on all other routes.


def build_mcp_http_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["mcp-http"])

    def _get_credential_store(request: Request) -> AgentCredentialStore:
        return getattr(request.app.state, "agent_credentials", AgentCredentialStore())

    def _remote_enabled(request: Request) -> bool:
        store = getattr(request.app.state, "_remote_settings", None)
        if store is None:
            return False
        return bool(store.get("enabled", False))

    # ── POST /api/mcp ──────────────────────────────────────────────
    @router.post("/api/mcp")
    async def mcp_http_endpoint(request: Request) -> JSONResponse:
        """Streamable HTTP transport for MCP JSON-RPC.

        Long-running contract (MCP-003): project.run_steward returns
        run_id promptly; the client polls project.get_steward_run(run_id).
        Terminal states: completed, failed, cancelled.  A credential
        expiring mid-run returns 403 on the poll; the run continues on
        the hub.
        """
        principal_probe = getattr(request.state, "principal", UNAUTHENTICATED)
        probe_host = request.client.host if request.client else "unknown"
        loopback_owner = (
            principal_probe.kind is PrincipalKind.OWNER
            and is_loopback_host(probe_host)
        )

        # Gate: return 404 when the REMOTE transport is not enabled. A loopback
        # OWNER is the hub's own local transport (HS-200-45 R3) and passes with
        # the flag off -- the stdio sidecar proxies through here rather than
        # opening the database as a second writer.
        if not _remote_enabled(request) and not loopback_owner:
            return JSONResponse(
                {"error": "streamable_http_not_enabled"},
                status_code=404,
            )

        # Counsel-on-built 174, condition 1: a credential never rides the
        # URL on this route (query strings land in access, proxy and
        # history logs), whatever principal the middleware derived from
        # it.  The runner sends ``Authorization: Bearer``.
        if request.query_params.get("token"):
            return JSONResponse(
                {"error": "token_in_query_refused",
                 "detail": "send the credential as Authorization: Bearer"},
                status_code=401,
            )

        principal = getattr(request.state, "principal", UNAUTHENTICATED)

        # HS-174 C5: per-route loopback guard -- OWNER from non-loopback
        # is refused on this route only.
        client_host = request.client.host if request.client else "unknown"
        if principal.kind is PrincipalKind.OWNER and not is_loopback_host(client_host):
            return JSONResponse(
                {
                    "error": "owner_refused_remote",
                    "detail": "OWNER principal is not accepted on the remote MCP path (XI:4).",
                },
                status_code=403,
            )

        # Unauthenticated -> 401.
        if principal.kind is PrincipalKind.NONE:
            return JSONResponse(
                {"error": "unauthenticated"},
                status_code=401,
            )

        # Derive palette from the credential (if AGENT).
        palette: frozenset[str] | None = None
        credential_store = _get_credential_store(request)
        # The middleware already derived the principal; to get the palette
        # we need to re-derive the credential from the token.
        from ...web_auth import extract_request_token
        token = extract_request_token(
            authorization=request.headers.get("authorization"),
            header_token=request.headers.get("x-holdspeak-token"),
            query_token=None,
        )
        cred = credential_store.derive_credential(token) if token else None
        if cred and cred.palette is not None:
            palette = cred.palette

        # Parse JSON-RPC request body.
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
                status_code=200,
            )
        if not isinstance(body, dict):
            return JSONResponse(
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}},
                status_code=200,
            )

        # HS-174-04: tag origin BEFORE dispatch (H3: before returning, not after).
        from ...mcp.server import handle_message_for_principal

        is_remote = not is_loopback_host(client_host)
        origin_value = "remote" if is_remote else "local"
        identity_label = cred.principal.identity if cred else principal.identity

        origin_token = _origin.set(origin_value)
        caller_token = _caller.set(client_host)
        identity_token = _caller_identity.set(identity_label)
        try:
            response = handle_message_for_principal(body, principal, palette=palette)
        finally:
            _origin.reset(origin_token)
            _caller.reset(caller_token)
            _caller_identity.reset(identity_token)

        if response is None:
            # Notification (no response expected). A bare Response: a
            # JSONResponse(None) serialises the literal ``null`` into a 204,
            # and uvicorn raises "Response content longer than Content-Length"
            # on every sidecar handshake (HS-200-45 counsel P1-1).
            return Response(status_code=204)
        return JSONResponse(content=response, status_code=200)

    # ── GET /api/settings/remote ───────────────────────────────────
    @router.get("/api/settings/remote")
    async def get_remote_settings(request: Request) -> JSONResponse:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        if principal.kind is not PrincipalKind.OWNER:
            return JSONResponse({"error": "owner_required"}, status_code=403)

        store = getattr(request.app.state, "_remote_settings", None) or {}
        cred_store = _get_credential_store(request)
        now_mono = time.monotonic()
        now_epoch = time.time()

        # HS-174-02: reverse-map resolved palette frozensets to names.
        from ...mcp.palettes import PALETTE_NAMES, resolve_palette
        _palette_reverse: dict[frozenset[str], str] = {}
        for _pn in PALETTE_NAMES:
            try:
                _palette_reverse[resolve_palette(_pn)] = _pn
            except Exception:
                pass

        credentials = []
        listed = cred_store.list_credentials()
        from ...services import desk_delegation

        grants = desk_delegation.views([c.principal.identity for c in listed])
        for c in listed:
            # Convert monotonic timestamps to epoch seconds for the face.
            expires_epoch = now_epoch + (c.expires_at - now_mono)
            last_used_epoch = (
                now_epoch + (c.last_used_at - now_mono)
                if c.last_used_at is not None
                else None
            )
            # Palette: return the name if it maps to a known palette.
            palette_name = _palette_reverse.get(c.palette, None) if c.palette else None
            credentials.append({
                "id": c.id,
                "identity": c.principal.identity,
                "palette": palette_name or (sorted(c.palette) if c.palette else None),
                "expires_at": expires_epoch,
                "last_used_at": last_used_epoch,
                "active": c.expires_at > now_mono,
                # PHILO-7-02: the grant's effective state (null: never granted).
                "delegation": grants["by_identity"].get(c.principal.identity),
            })

        return JSONResponse({
            "enabled": bool(store.get("enabled", False)),
            "bind_host": store.get("bind_host"),
            "port": store.get("port"),
            "credentials": credentials,
            "delegations": grants["orphans"],
            "active_count": cred_store.count_active(),
            "total_count": len(credentials),
        })

    # ── PUT /api/settings/remote ───────────────────────────────────
    @router.put("/api/settings/remote")
    async def update_remote_settings(request: Request) -> JSONResponse:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        if principal.kind is not PrincipalKind.OWNER:
            return JSONResponse({"error": "owner_required"}, status_code=403)

        body = await request.json()
        store = getattr(request.app.state, "_remote_settings", None)
        if store is None:
            store = {}
            request.app.state._remote_settings = store

        if "enabled" in body:
            store["enabled"] = bool(body["enabled"])
        if "bind_host" in body:
            store["bind_host"] = str(body["bind_host"] or "")
        if "port" in body:
            store["port"] = int(body["port"])

        return JSONResponse({"success": True, **store})

    # ── POST /api/settings/remote/credentials ──────────────────────
    @router.post("/api/settings/remote/credentials")
    async def issue_credential(request: Request) -> JSONResponse:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        if principal.kind is not PrincipalKind.OWNER:
            return JSONResponse({"error": "owner_required"}, status_code=403)

        body = await request.json()
        identity = str(body.get("identity") or "").strip()
        if not identity:
            return JSONResponse(
                {"error": "identity_required"},
                status_code=400,
            )

        from ...mcp.palettes import PALETTE_NAMES, resolve_palette
        palette_name = str(body.get("palette") or "PROJECT").strip().upper()
        if palette_name not in PALETTE_NAMES:
            return JSONResponse(
                {"error": "unknown_palette", "valid": list(PALETTE_NAMES)},
                status_code=400,
            )

        ttl_seconds = float(body.get("ttl_seconds", 43_200.0))

        try:
            palette_set = resolve_palette(palette_name)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

        cred_store = _get_credential_store(request)
        credential = cred_store.issue(
            identity,
            ttl_seconds=ttl_seconds,
            palette=palette_set,
        )

        return JSONResponse({
            "token": credential.token,  # plaintext, shown ONCE
            "id": credential.id,
            "identity": credential.principal.identity,
            "palette": palette_name,
            "expires_at": credential.expires_at,
        })

    # ── DELETE /api/settings/remote/credentials/{id} ───────────────
    @router.delete("/api/settings/remote/credentials/{credential_id}")
    async def revoke_credential(request: Request, credential_id: str) -> JSONResponse:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        if principal.kind is not PrincipalKind.OWNER:
            return JSONResponse({"error": "owner_required"}, status_code=403)

        cred_store = _get_credential_store(request)
        # PHILO-7-02 (invariant 5, durable first): resolve the identity WITHOUT
        # removing anything; revoke its LIVE desk grant with its own receipt;
        # only then remove the credential. A kernel refusal leaves it in place.
        identity = cred_store.identity_for_id(credential_id)
        if identity is None:
            return JSONResponse(
                {"error": "credential_not_found"},
                status_code=404,
            )
        from ...services import desk_delegation
        from ...services.errors import ServiceError

        try:
            grant = desk_delegation.revoke_for_credential(principal, identity)
        except ServiceError as exc:
            return JSONResponse({"error": exc.code, "detail": exc.detail, **exc.context},
                                status_code=int(exc.context.get("status") or 409))
        revoked = cred_store.revoke_by_id(credential_id)
        if not revoked:
            return JSONResponse(
                {"error": "credential_not_found", "grant_revoked": grant is not None, **(grant or {})},
                status_code=404,
            )
        return JSONResponse({"success": True, "revoked": credential_id,
                             "grant_revoked": grant is not None, **(grant or {})})

    # ── PUT/DELETE /api/settings/remote/delegations/{identity} ─────
    # PHILO-7-02 (R1): the owner's desk delegation grant. The edge right is
    # AGENT_SUBMIT (principals.required_right) so an agent's attempt reaches
    # the kernel and is refused there WITH a receipt (owner_principal_required).
    # The route never checks the owner itself: the kernel does.

    async def _delegation_body(request: Request) -> Any:
        raw = await request.body()
        if not raw.strip():
            return {}
        try:
            import json as _json

            return _json.loads(raw)
        except ValueError:
            return None  # an unreadable body: a non-object attempt

    def _delegation_response(result: dict[str, Any], status: int = 200) -> JSONResponse:
        return JSONResponse({"success": True, **result}, status_code=status)

    @router.put("/api/settings/remote/delegations/{identity}")
    async def grant_delegation(request: Request, identity: str) -> JSONResponse:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        from ...services import desk_delegation
        from ...services.errors import ServiceError

        body = await _delegation_body(request)
        try:
            return _delegation_response(desk_delegation.grant(principal, identity, body))
        except ServiceError as exc:
            return JSONResponse({"error": exc.code, "detail": exc.detail, **exc.context},
                                status_code=int(exc.context.get("status") or 409))

    @router.delete("/api/settings/remote/delegations/{identity}")
    async def revoke_delegation(request: Request, identity: str) -> JSONResponse:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        from ...services import desk_delegation
        from ...services.errors import ServiceError

        body = await _delegation_body(request)
        try:
            return _delegation_response(desk_delegation.revoke(principal, identity, "owner_revoked", body=body))
        except ServiceError as exc:
            return JSONResponse({"error": exc.code, "detail": exc.detail, **exc.context},
                                status_code=int(exc.context.get("status") or 409))

    return router
