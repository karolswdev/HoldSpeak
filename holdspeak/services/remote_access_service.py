"""Owner-only remote access, over the hub's settings, credential and grant stores."""

from __future__ import annotations
import time
from contextvars import ContextVar
from typing import Any
from holdspeak.config import Config
from holdspeak.principals import PrincipalKind, agent_credentials
from holdspeak.services.errors import ServiceError

# Transport context, never operation arguments or authority. The default is
# the hub's one credential store; HTTP may supply its app's store in a rig.
credential_store_context: ContextVar[Any] = ContextVar(
    "remote_credential_store", default=None
)


class RemoteAccessError(ServiceError):
    def __init__(self, payload: dict[str, Any], status: int) -> None:
        super().__init__(
            str(payload.get("error") or "remote_access_refused"),
            "Remote access request refused",
            context={"status": status, "response": payload},
        )


def _result(payload: dict[str, Any], status_code: int = 200) -> dict[str, Any]:
    if status_code >= 400:
        raise RemoteAccessError(payload, status_code)
    return payload


class RemoteAccessService:
    def __init__(self, settings: Any) -> None:
        self._settings = settings

    @staticmethod
    def _store() -> Any:
        return credential_store_context.get() or agent_credentials

    @staticmethod
    def _require_owner(principal: Any) -> None:
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise RemoteAccessError({"error": "owner_required"}, 403)

    def _remote_store(self) -> dict[str, Any]:
        """Read the durable config used by every remote surface."""
        remote = Config.load().remote
        return {
            "enabled": bool(remote.streamable_http_enabled),
            "bind_host": remote.bind_host,
            "port": remote.port,
        }

    def _save_remote_settings(
        self, principal: Any, patch: dict[str, Any]
    ) -> dict[str, Any]:
        """Use the composed settings operation for the durable write."""
        service = self._settings
        if service is None:
            raise RuntimeError(
                "SettingsService was not supplied at application composition"
            )
        remote_patch: dict[str, Any] = {}
        if "enabled" in patch:
            remote_patch["streamable_http_enabled"] = patch["enabled"]
        if "bind_host" in patch:
            remote_patch["bind_host"] = patch["bind_host"]
        if "port" in patch:
            remote_patch["port"] = patch["port"]
        service.update_settings(principal, {"remote": remote_patch})
        remote = Config.load().remote
        return {
            "enabled": bool(remote.streamable_http_enabled),
            "bind_host": remote.bind_host,
            "port": remote.port,
        }

    def get_remote_settings(self, principal: Any) -> dict[str, Any]:
        self._require_owner(principal)
        store = self._remote_store()
        cred_store = self._store()
        now_mono = time.monotonic()
        now_epoch = time.time()
        from holdspeak.mcp.palettes import PALETTE_NAMES, resolve_palette

        _palette_reverse: dict[frozenset[str], str] = {}
        for _pn in PALETTE_NAMES:
            try:
                _palette_reverse[resolve_palette(_pn)] = _pn
            except Exception:
                pass
        credentials = []
        listed = cred_store.list_credentials()
        from holdspeak.services import desk_delegation, project_delegation

        grants = desk_delegation.views([c.principal.identity for c in listed])
        project_grants = project_delegation.views(
            [c.principal.identity for c in listed]
        )
        for c in listed:
            expires_epoch = now_epoch + (c.expires_at - now_mono)
            last_used_epoch = (
                now_epoch + (c.last_used_at - now_mono)
                if c.last_used_at is not None
                else None
            )
            palette_name = c.palette_name or (
                _palette_reverse.get(c.palette, None) if c.palette else None
            )
            credentials.append(
                {
                    "id": c.id,
                    "identity": c.principal.identity,
                    "palette": palette_name
                    or (sorted(c.palette) if c.palette else None),
                    "expires_at": expires_epoch,
                    "last_used_at": last_used_epoch,
                    "active": c.expires_at > now_mono,
                    "delegation": grants["by_identity"].get(c.principal.identity),
                    "project_delegations": project_grants["by_identity"].get(
                        c.principal.identity, []
                    ),
                }
            )
        return _result(
            {
                "enabled": bool(store.get("enabled", False)),
                "bind_host": store.get("bind_host"),
                "port": store.get("port"),
                "credentials": credentials,
                "delegations": grants["orphans"],
                "project_delegations": project_grants["orphans"],
                "active_count": cred_store.count_active(),
                "total_count": len(credentials),
            }
        )

    def update_remote_settings(
        self, principal: Any, body: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_owner(principal)
        patch: dict[str, Any] = {}
        if "enabled" in body:
            patch["enabled"] = bool(body["enabled"])
        if "bind_host" in body:
            patch["bind_host"] = str(body["bind_host"] or "")
        if "port" in body:
            patch["port"] = int(body["port"])
        store = self._save_remote_settings(principal, patch)
        return _result({"success": True, **store})

    def issue_credential(self, principal: Any, body: dict[str, Any]) -> dict[str, Any]:
        self._require_owner(principal)
        identity = str(body.get("identity") or "").strip()
        if not identity:
            return _result({"error": "identity_required"}, status_code=400)
        from holdspeak.mcp.palettes import PALETTE_NAMES, resolve_palette

        palette_name = str(body.get("palette") or "PROJECT").strip().upper()
        if palette_name not in PALETTE_NAMES:
            return _result(
                {"error": "unknown_palette", "valid": list(PALETTE_NAMES)},
                status_code=400,
            )
        ttl_seconds = float(body.get("ttl_seconds", 43200.0))
        try:
            palette_set = resolve_palette(palette_name)
        except ValueError as exc:
            return _result({"error": str(exc)}, status_code=400)
        cred_store = self._store()
        credential = cred_store.issue(
            identity,
            ttl_seconds=ttl_seconds,
            palette=palette_set,
            palette_name=palette_name,
        )
        return _result(
            {
                "token": credential.token,
                "id": credential.id,
                "identity": credential.principal.identity,
                "palette": palette_name,
                "expires_at": credential.expires_at,
            }
        )

    def revoke_credential(self, principal: Any, credential_id: str) -> dict[str, Any]:
        self._require_owner(principal)
        cred_store = self._store()
        identity = cred_store.identity_for_id(credential_id)
        if identity is None:
            return _result({"error": "credential_not_found"}, status_code=404)
        from holdspeak.services import desk_delegation, project_delegation
        from holdspeak.services.errors import ServiceError

        try:
            grant = desk_delegation.revoke_for_credential(principal, identity)
            project_grants = project_delegation.revoke_for_credential(
                principal, identity
            )
        except ServiceError as exc:
            return _result(
                {"error": exc.code, "detail": exc.detail, **exc.context},
                status_code=int(exc.context.get("status") or 409),
            )
        revoked = cred_store.revoke_by_id(credential_id)
        if not revoked and cred_store.revoke_pending(credential_id):
            return _result(
                {
                    "error": "credential_revoke_not_persisted",
                    "retry": True,
                    "grant_revoked": grant is not None,
                    **(grant or {}),
                    "project_grants_revoked": project_grants,
                },
                status_code=503,
            )
        if not revoked:
            return _result(
                {
                    "error": "credential_not_found",
                    "grant_revoked": grant is not None,
                    **(grant or {}),
                    "project_grants_revoked": project_grants,
                },
                status_code=404,
            )
        return _result(
            {
                "success": True,
                "revoked": credential_id,
                "grant_revoked": grant is not None,
                **(grant or {}),
                "project_grants_revoked": project_grants,
            }
        )

    def _delegation_response(
        self, result: dict[str, Any], status: int = 200
    ) -> dict[str, Any]:
        return _result({"success": True, **result}, status_code=status)

    def grant_delegation(
        self, principal: Any, identity: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_owner(principal)
        from holdspeak.services import desk_delegation
        from holdspeak.services.errors import ServiceError

        try:
            return self._delegation_response(
                desk_delegation.grant(principal, identity, body)
            )
        except ServiceError as exc:
            return _result(
                {"error": exc.code, "detail": exc.detail, **exc.context},
                status_code=int(exc.context.get("status") or 409),
            )

    def revoke_delegation(
        self, principal: Any, identity: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_owner(principal)
        from holdspeak.services import desk_delegation
        from holdspeak.services.errors import ServiceError

        try:
            return self._delegation_response(
                desk_delegation.revoke(principal, identity, "owner_revoked", body=body)
            )
        except ServiceError as exc:
            return _result(
                {"error": exc.code, "detail": exc.detail, **exc.context},
                status_code=int(exc.context.get("status") or 409),
            )

    def _project_grant_error(self, exc: Any) -> dict[str, Any]:
        return _result(
            {"error": exc.code, "detail": exc.detail, **exc.context},
            status_code=int(exc.context.get("status") or 409),
        )

    def grant_project_delegation(
        self, principal: Any, identity: str, project_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_owner(principal)
        from holdspeak.services import project_delegation
        from holdspeak.services.errors import ServiceError

        try:
            return self._delegation_response(
                project_delegation.grant(principal, identity, project_id, body)
            )
        except ServiceError as exc:
            return self._project_grant_error(exc)

    def revoke_project_delegation(
        self, principal: Any, identity: str, project_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_owner(principal)
        from holdspeak.services import project_delegation
        from holdspeak.services.errors import ServiceError

        try:
            return self._delegation_response(
                project_delegation.revoke(
                    principal,
                    identity,
                    project_id,
                    "owner_revoked",
                    body=None if body == {} else body,
                )
            )
        except ServiceError as exc:
            return self._project_grant_error(exc)
