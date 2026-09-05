"""HS-174-02: Streamable HTTP transport for MCP (POST /api/mcp).

JSON-RPC in -> handle_message_for_principal -> JSON-RPC out, composing on
the web runtime's LIVE services (never the sidecar's bare serve() instances).

Principal derivation per D3:
- Loopback + owner token -> OWNER (unrestricted).
- Loopback + agent credential -> AGENT (palette from credential).
- Non-loopback + owner token -> 403 (Article XI:4, per-route guard C5).
- Non-loopback + agent credential -> AGENT (palette from credential).
- No match -> 401.

The listener is opt-in: ``remote.streamable_http_enabled`` (off by default).
When off, the route returns 404.

Settings routes:
- GET  /api/settings/remote        -> current remote config + credential list
- PUT  /api/settings/remote        -> update enabled/bind_host
- POST /api/settings/remote/credentials -> issue a new credential
- DELETE /api/settings/remote/credentials/{id} -> revoke
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

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
        # Gate: return 404 when the transport is not enabled.
        if not _remote_enabled(request):
            return JSONResponse(
                {"error": "streamable_http_not_enabled"},
                status_code=404,
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
            query_token=request.query_params.get("token"),
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
            # Notification (no response expected).
            return JSONResponse(content=None, status_code=204)
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
        for c in cred_store.list_credentials():
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
            })

        return JSONResponse({
            "enabled": bool(store.get("enabled", False)),
            "bind_host": store.get("bind_host"),
            "port": store.get("port"),
            "credentials": credentials,
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
        revoked = cred_store.revoke_by_id(credential_id)
        if not revoked:
            return JSONResponse(
                {"error": "credential_not_found"},
                status_code=404,
            )
        return JSONResponse({"success": True, "revoked": credential_id})

    return router
