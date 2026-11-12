# PARKED: host-bound checks and durable removal claims replace the ambiguous post-logout update.
from __future__ import annotations

from typing import Any

class _ParkedBody:
    def _connection_status(self, principal: Principal, *, hostname: str | None = None) -> dict[str, Any]:
        """Probe ``gh auth status`` and persist the typed result.

        ``hostname`` scopes the probe to one host (``--hostname``); the stored
        account then names that host unless it is github.com
        (``<host>:<login>``), so a check of one host never reads as another.

        PROV-003: readiness comes from the authenticated probe, never
        ``which gh`` alone.  The binary-presence check is only the
        "unavailable" fast path.
        """
        # Binary-presence → unavailable (NOT readiness)
        if self._runner is None and shutil.which("gh") is None:
            result: dict[str, Any] = {
                "state": STATE_UNAVAILABLE,
                "error_code": CODE_UNAVAILABLE,
                "error_detail": "GitHub CLI (gh) is not installed",
                "display": {},
            }
            self._persist_connection(result)
            return result

        # Real probe
        try:
            completed = self._run_gh(
                ["gh", "auth", "status", *(["--hostname", hostname] if hostname else [])],
                principal, timeout=10.0,
            )
        except Exception as exc:
            result = {
                "state": STATE_DEGRADED,
                "error_code": CODE_UNAVAILABLE,
                "error_detail": f"gh auth probe failed: {redact_source_error(exc)[:500]}",
                "display": {},
            }
            self._persist_connection(result)
            return result

        combined = (completed.stdout or "") + "\n" + (completed.stderr or "")

        if completed.returncode == 0:
            login = _parse_gh_auth_login(combined)
            if login and hostname and hostname != "github.com":
                login = f"{hostname}:{login}"
            result = {
                "state": STATE_CONNECTED,
                "error_code": None,
                "error_detail": None,
                "display": {"account": login} if login else {},
            }
        elif _is_unauthenticated(combined):
            result = {
                "state": STATE_OWNER_ACTION_REQUIRED,
                "error_code": CODE_AUTH_REQUIRED,
                "error_detail": "gh auth login",
                "display": {"recovery_hint": "gh auth login"},
            }
        else:
            result = {
                "state": STATE_DEGRADED,
                "error_code": CODE_UNAVAILABLE,
                "error_detail": redact_source_error(combined).strip()[:500],
                "display": {},
            }

        self._persist_connection(result)
        return result

    def _remove_connection(self, principal: Principal, connection_ref: str, expected_checked_at: str) -> dict[str, Any]:
        """Keep linked rows; removing sign-in makes their source require the owner."""
        from .credential_service import CredentialService
        from .errors import ConflictError, NotFound

        CredentialService._require_owner(principal)
        from .project_kernel import current
        handle = current()
        answer = {"removed": True, "provider": "github", "connection_ref": connection_ref}
        if handle is not None and handle.replay:
            return answer
        row = self._db.automations.get_provider_connection(self._connection_id())
        if row is None:
            raise NotFound("GitHub connection", connection_ref)
        if (not expected_checked_at or row["last_checked_at"] != expected_checked_at
                or not connection_ref or row["external_connection_ref"] != connection_ref):
            raise ConflictError("GitHub connection changed. Check it before removing it.",
                                code="github_connection_changed")
        host, login = connection_ref.split(":", 1) if ":" in connection_ref else ("github.com", connection_ref)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", host) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", login):
            raise ConflictError("Check the GitHub sign-in before removing it.", code="github_connection_changed")
        if self._credentials is None:
            from .errors import ServiceError
            raise ServiceError("github_credential_remove_failed", "The credential service is not available.",
                               context={"status": 503})
        self._credentials._remove_github_login(principal, host, login, runner=self._runner)
        with self._db._connection() as conn:
            conn.execute("UPDATE watch_provider_connections SET state=?, external_connection_ref='',"
                     " last_error_code=?, last_error_detail=?, last_checked_at=? WHERE id=?",
                     (STATE_OWNER_ACTION_REQUIRED, CODE_AUTH_REQUIRED, "Sign in again", utc_now_iso(),
                      self._connection_id()))
        return answer

    def _persist_connection(self, result: dict[str, Any]) -> None:
        """Write connection state to watch_provider_connections.

        PROV-004: no credential/token material in the row or any log line.
        """
        if self._db is None:
            return
        repo = self._db.automations
        now_iso = datetime.now(timezone.utc).isoformat()
        connection_id = self._connection_id()
        manifest_data = self.manifest()

        existing = repo.get_provider_connection(connection_id)
        if existing:
            repo.update_provider_connection(
                connection_id,
                state=result["state"],
                capability_manifest_json=json.dumps(manifest_data["capabilities"]),
                capability_revision=manifest_data["revision"],
                last_checked_at=now_iso,
                last_connected_at=(
                    now_iso
                    if result["state"] == STATE_CONNECTED
                    else existing.get("last_connected_at")
                ),
                last_error_code=result.get("error_code") or "",
                last_error_detail=result.get("error_detail") or "",
                external_connection_ref=(result.get("display") or {}).get("account") or "",
            )
        else:
            repo.create_provider_connection(
                connection_id=connection_id,
                provider_id=PROVIDER_ID,
                transport=TRANSPORT,
                state=result["state"],
                capability_manifest_json=json.dumps(manifest_data["capabilities"]),
                capability_revision=manifest_data["revision"],
                discovery_state=DISCOVERY_UNKNOWN,
            )
            repo.update_provider_connection(
                connection_id,
                last_checked_at=now_iso,
                last_connected_at=now_iso if result["state"] == STATE_CONNECTED else None,
                last_error_code=result.get("error_code") or "",
                last_error_detail=result.get("error_detail") or "",
                external_connection_ref=(result.get("display") or {}).get("account") or "",
            )
