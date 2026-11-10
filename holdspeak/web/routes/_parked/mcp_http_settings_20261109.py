# Parked: remote settings now run through RemoteAccessService and declared operations.
from __future__ import annotations

class _ParkedBody:
    # ── GET /api/settings/remote ───────────────────────────────────
    @router.get("/api/settings/remote")
    def get_remote_settings(request: Request) -> JSONResponse:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        if principal.kind is not PrincipalKind.OWNER:
            return JSONResponse({"error": "owner_required"}, status_code=403)

        store = _remote_store()
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
        from ...services import desk_delegation, project_delegation

        grants = desk_delegation.views([c.principal.identity for c in listed])
        project_grants = project_delegation.views([c.principal.identity for c in listed])
        for c in listed:
            # Convert monotonic timestamps to epoch seconds for the face.
            expires_epoch = now_epoch + (c.expires_at - now_mono)
            last_used_epoch = (
                now_epoch + (c.last_used_at - now_mono)
                if c.last_used_at is not None
                else None
            )
            # Palette: the ISSUED name (PHILO-9-07, the DESK = ALL repair:
            # DESK resolves to every top-level tool, so the reverse map named
            # it ALL). The reverse map only for a credential issued unnamed.
            palette_name = c.palette_name or (_palette_reverse.get(c.palette, None) if c.palette else None)
            credentials.append({
                "id": c.id,
                "identity": c.principal.identity,
                "palette": palette_name or (sorted(c.palette) if c.palette else None),
                "expires_at": expires_epoch,
                "last_used_at": last_used_epoch,
                "active": c.expires_at > now_mono,
                # PHILO-7-02: the grant's effective state (null: never granted).
                "delegation": grants["by_identity"].get(c.principal.identity),
                # PHILO-9-07: one entry per project with any stored grant row,
                # projected to its effective state (absent: never granted).
                "project_delegations": project_grants["by_identity"].get(c.principal.identity, []),
            })

        return JSONResponse({
            "enabled": bool(store.get("enabled", False)),
            "bind_host": store.get("bind_host"),
            "port": store.get("port"),
            "credentials": credentials,
            "delegations": grants["orphans"],
            "project_delegations": project_grants["orphans"],
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
        patch: dict[str, Any] = {}
        if "enabled" in body:
            patch["enabled"] = bool(body["enabled"])
        if "bind_host" in body:
            patch["bind_host"] = str(body["bind_host"] or "")
        if "port" in body:
            patch["port"] = int(body["port"])

        store = _save_remote_settings(principal, patch)
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
            palette_name=palette_name,
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
    def revoke_credential(request: Request, credential_id: str) -> JSONResponse:
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
        from ...services import desk_delegation, project_delegation
        from ...services.errors import ServiceError

        try:
            grant = desk_delegation.revoke_for_credential(principal, identity)
            # PHILO-9-07: every LIVE project grant of the identity, durably
            # first too, each with its own receipt (credential_revoked).
            project_grants = project_delegation.revoke_for_credential(principal, identity)
        except ServiceError as exc:
            return JSONResponse({"error": exc.code, "detail": exc.detail, **exc.context},
                                status_code=int(exc.context.get("status") or 409))
        revoked = cred_store.revoke_by_id(credential_id)
        if not revoked and cred_store.revoke_pending(credential_id):
            # Conductor R2: refused at once, but the revoke is not written
            # yet; the same DELETE retries it.
            return JSONResponse(
                {"error": "credential_revoke_not_persisted", "retry": True,
                 "grant_revoked": grant is not None, **(grant or {}),
                 "project_grants_revoked": project_grants},
                status_code=503,
            )
        if not revoked:
            return JSONResponse(
                {"error": "credential_not_found", "grant_revoked": grant is not None, **(grant or {}),
                 "project_grants_revoked": project_grants},
                status_code=404,
            )
        return JSONResponse({"success": True, "revoked": credential_id,
                             "grant_revoked": grant is not None, **(grant or {}),
                             "project_grants_revoked": project_grants})

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

    # ── PUT/DELETE …/delegations/{identity}/projects/{project_id} ──
    # PHILO-9-07 (the Q2 ruling): the owner's project delegation grant.
    # The edge right is AGENT_SUBMIT (the same prefix as the desk grant), so an
    # agent's attempt is refused BY THE KERNEL with a receipt
    # (owner_principal_required). HTTP only: in no MCP palette.

    def _project_grant_error(exc: Any) -> JSONResponse:
        return JSONResponse({"error": exc.code, "detail": exc.detail, **exc.context},
                            status_code=int(exc.context.get("status") or 409))

    @router.put("/api/settings/remote/delegations/{identity}/projects/{project_id}")
    async def grant_project_delegation(request: Request, identity: str, project_id: str) -> JSONResponse:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        from ...services import project_delegation
        from ...services.errors import ServiceError

        body = await _delegation_body(request)
        try:
            return _delegation_response(project_delegation.grant(principal, identity, project_id, body))
        except ServiceError as exc:
            return _project_grant_error(exc)

    @router.delete("/api/settings/remote/delegations/{identity}/projects/{project_id}")
    async def revoke_project_delegation(request: Request, identity: str, project_id: str) -> JSONResponse:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        from ...services import project_delegation
        from ...services.errors import ServiceError

        body = await _delegation_body(request)
        try:
            return _delegation_response(project_delegation.revoke(
                principal, identity, project_id, "owner_revoked", body=None if body == {} else body))
        except ServiceError as exc:
            return _project_grant_error(exc)
