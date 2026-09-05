"""ConfluenceProviderAdapter -- the V0 acli Confluence provider for Project Room Watches.

HS-174-07.  Mirrors ``JiraProviderAdapter`` (jira_provider.py) in shape
and reuses its PROV-009 error codes and SRS SS6 states by import.

THE MULTI-ACCOUNT ANSWER: acli keeps ONE global current account.  Every
HoldSpeak read is ``switch --site S --email E`` then ``auth status``
under ONE process-wide cross-process lock (the switch-and-verify law).
The lock is SHARED with Jira: both products use the same ``acli`` binary
and the same global account state.

THE CRITICAL GAP: ``acli confluence`` has NO ``page list`` or ``page search``
command.  V0 watches BLOG POSTS via ``blog list --space-id`` and PAGES BY
KNOWN ID via ``page view --id`` (IDs from meeting mentions, suggested
sources, or manual entry).  No full-space page sweep.  A query asking for
page listing gets a typed ``unsupported_by_cli`` error, never a silent
empty snapshot.

Connection identity: **(site, email)** serialized as ``site|email``
(the ``|`` separator is not legal in either an Atlassian site host or
an email address, so it is unambiguous).  Each combination is one row
in ``watch_provider_connections`` with ``provider_id="confluence"`` and
``external_connection_ref="site|email"``.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import subprocess
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from holdspeak.connector_packs import acli_confluence
from holdspeak.connector_runtime import PermissionGate
from holdspeak.principals import Principal
from holdspeak.services.errors import ServiceError, ValidationError

# Reuse the typed PROV-009 error codes and SRS states from github_provider
# (single source of truth -- never copy).
from holdspeak.services.github_provider import (
    CODE_AUTH_REQUIRED,
    CODE_QUERY_INVALID,
    CODE_SCOPE_DENIED,
    CODE_UNAVAILABLE,
    DISCOVERY_FAILED,
    DISCOVERY_PARTIAL,
    DISCOVERY_READY,
    DISCOVERY_UNKNOWN,
    STATE_CONNECTED,
    STATE_DEGRADED,
    STATE_DISCONNECTED,
    STATE_OWNER_ACTION_REQUIRED,
    STATE_UNAVAILABLE,
)

# Reuse the shared cross-process lock from jira_provider so both
# products serialize their switch-and-verify sequences.
from holdspeak.services.jira_provider import (
    _ACLI_LOCK,
    _is_account_not_found,
    _is_unauthenticated,
    _normalize_site,
    _parse_acli_auth_status,
    _parse_connection_ref,
    connection_ref,
)

_log = logging.getLogger(__name__)

Runner = Callable[..., subprocess.CompletedProcess[str]]

PROVIDER_ID = "confluence"
TRANSPORT = "connector_pack"

# Typed error code for the critical gap: no page list/search.
CODE_UNSUPPORTED_BY_CLI = "unsupported_by_cli"

_CAPABILITIES: dict[str, bool] = {
    "discover": True,
    "read": True,
    "subscribe": False,
    "effect": False,
}

_CAPABILITY_HASH = hashlib.sha256(
    json.dumps(_CAPABILITIES, sort_keys=True).encode()
).hexdigest()[:12]

_CAPABILITY_REVISION = 1

# -- Connection ref separator -----------------------------------------
CONNECTION_REF_SEP = "|"

# Install recovery command template.
_INSTALL_COMMAND = "brew tap atlassian/homebrew-acli && brew install acli"


class ConfluenceProviderAdapter:
    """V0 Atlassian CLI (acli) Confluence provider adapter (read-only).

    Takes the same ``runner`` seam as ``JiraProviderAdapter``: tests inject
    a fake; production defaults to ``subprocess.run`` via the admitted
    ``PermissionGate.run_read_subprocess`` path.
    """

    def __init__(
        self,
        db: Any = None,
        *,
        runner: Runner | None = None,
    ) -> None:
        self._db = db
        self._runner = runner

    # -- Manifest (PROV-001, PROV-007) ---------------------------------

    def manifest(self) -> dict[str, Any]:
        """Versioned capability manifest. The hash changes iff capabilities do."""
        return {
            "provider_id": PROVIDER_ID,
            "transport": TRANSPORT,
            "capabilities": dict(_CAPABILITIES),
            "version": _CAPABILITY_HASH,
            "revision": _CAPABILITY_REVISION,
            "requires_cli": "acli",
        }

    # -- Admitted subprocess seam ---------------------------------------

    def _run_acli(
        self,
        command: list[str],
        principal: Principal,
        *,
        timeout: float = acli_confluence.DEFAULT_TIMEOUT_SECONDS,
    ) -> subprocess.CompletedProcess[str]:
        """Single admitted subprocess entry point for all acli CLI calls.

        Routes through ``PermissionGate.run_read_subprocess`` -- the same
        kernel-admitted path ``JiraProviderAdapter`` uses for ``acli jira``.
        """
        return PermissionGate(acli_confluence.MANIFEST).run_read_subprocess(
            command,
            principal=principal,
            runner=self._runner,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
        )

    # -- Connection identity -------------------------------------------

    @staticmethod
    def normalize_site(site: str) -> str:
        """Normalize a site string to canonical ``<slug>.atlassian.net`` form."""
        return _normalize_site(site)

    @staticmethod
    def connection_ref(site: str, email: str) -> str:
        """Build the ``site|email`` connection ref from normalized parts."""
        return connection_ref(site, email)

    def _connection_id(self, ref: str) -> str:
        """DB primary key for a Confluence connection row."""
        return f"wpc_{PROVIDER_ID}_{ref}"

    # -- Connection CRUD -----------------------------------------------

    def list_connections(self, principal: Principal) -> list[dict[str, Any]]:
        """Return all ``watch_provider_connections`` rows for provider_id='confluence'."""
        if self._db is None:
            return []
        return self._db.automations.list_provider_connections(provider_id=PROVIDER_ID)

    def add_connection(
        self,
        principal: Principal,
        site: str,
        email: str,
    ) -> dict[str, Any]:
        """Upsert a Confluence connection row for (site, email).

        Idempotent: if a row with the same ref already exists, returns it
        unchanged.  New rows start in state ``disconnected`` (not yet checked).
        NO secret is ever stored (PROV-004).
        """
        norm_site = _normalize_site(site)
        email_lower = email.strip().lower()
        if not email_lower or "@" not in email_lower:
            raise ValidationError("A valid email address is required")

        ref = connection_ref(norm_site, email_lower)
        cid = self._connection_id(ref)

        if self._db is None:
            return {
                "provider_id": PROVIDER_ID,
                "connection_ref": ref,
                "state": STATE_DISCONNECTED,
            }

        repo = self._db.automations
        existing = repo.get_provider_connection(cid)
        if existing:
            return existing

        manifest_data = self.manifest()
        repo.create_provider_connection(
            connection_id=cid,
            provider_id=PROVIDER_ID,
            transport=TRANSPORT,
            external_connection_ref=ref,
            state=STATE_DISCONNECTED,
            capability_manifest_json=json.dumps(manifest_data["capabilities"]),
            capability_revision=manifest_data["revision"],
            discovery_state=DISCOVERY_UNKNOWN,
        )
        return repo.get_provider_connection(cid) or {}

    # -- Connection status (PROV-003, PROV-004) -------------------------

    def connection_status(
        self,
        principal: Principal,
        connection_ref_str: str,
        *,
        recheck: bool = True,
    ) -> dict[str, Any]:
        """Probe one Confluence connection under the switch-and-verify lock.

        1. ``acli confluence auth switch --site S --email E``
        2. ``acli confluence auth status``
        3. Parse the status read-back and verify site+email match.

        All under ``_ACLI_LOCK`` so concurrent callers cannot interleave
        switch commands across jira AND confluence.
        """
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)

        # Binary-presence -> unavailable (NOT readiness)
        if self._runner is None and shutil.which("acli") is None:
            result: dict[str, Any] = {
                "state": STATE_UNAVAILABLE,
                "provider_id": PROVIDER_ID,
                "connection_ref": canonical_ref,
                "account": {"site": site, "email": email},
                "error_code": CODE_UNAVAILABLE,
                "error_detail": "Atlassian CLI (acli) is not installed",
                "recovery": {
                    "command": _INSTALL_COMMAND,
                    "hint": "Install acli to connect to Confluence",
                },
                "capability_manifest": dict(_CAPABILITIES),
                "capability_revision": _CAPABILITY_REVISION,
                "discovery_state": DISCOVERY_UNKNOWN,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            self._persist_connection(canonical_ref, result)
            return result

        with _ACLI_LOCK:
            return self._probe_under_lock(principal, site, email, canonical_ref)

    def _probe_under_lock(
        self,
        principal: Principal,
        site: str,
        email: str,
        ref: str,
    ) -> dict[str, Any]:
        """Execute the switch-then-status sequence (must hold ``_ACLI_LOCK``)."""
        now_iso = datetime.now(timezone.utc).isoformat()

        # Step 1: switch
        try:
            switch_result = self._run_acli(
                ["acli", "confluence", "auth", "switch", "--site", site, "--email", email],
                principal,
                timeout=10.0,
            )
        except Exception as exc:
            result: dict[str, Any] = {
                "state": STATE_DEGRADED,
                "provider_id": PROVIDER_ID,
                "connection_ref": ref,
                "account": {"site": site, "email": email},
                "error_code": CODE_UNAVAILABLE,
                "error_detail": f"acli auth switch failed: {str(exc)[:500]}",
                "recovery": None,
                "capability_manifest": dict(_CAPABILITIES),
                "capability_revision": _CAPABILITY_REVISION,
                "discovery_state": DISCOVERY_UNKNOWN,
                "checked_at": now_iso,
            }
            self._persist_connection(ref, result)
            return result

        switch_combined = (switch_result.stdout or "") + "\n" + (switch_result.stderr or "")

        if switch_result.returncode != 0:
            if _is_account_not_found(switch_combined) or _is_unauthenticated(switch_combined):
                login_cmd = (
                    f"acli confluence auth login --site {site} --email {email} --token"
                )
                result = {
                    "state": STATE_OWNER_ACTION_REQUIRED,
                    "provider_id": PROVIDER_ID,
                    "connection_ref": ref,
                    "account": {"site": site, "email": email},
                    "error_code": CODE_AUTH_REQUIRED,
                    "error_detail": "Not authenticated; run the login command",
                    "recovery": {
                        "command": login_cmd,
                        "hint": "Authenticate with your Atlassian API token",
                    },
                    "capability_manifest": dict(_CAPABILITIES),
                    "capability_revision": _CAPABILITY_REVISION,
                    "discovery_state": DISCOVERY_UNKNOWN,
                    "checked_at": now_iso,
                }
                self._persist_connection(ref, result)
                return result

            result = {
                "state": STATE_DEGRADED,
                "provider_id": PROVIDER_ID,
                "connection_ref": ref,
                "account": {"site": site, "email": email},
                "error_code": CODE_UNAVAILABLE,
                "error_detail": f"acli auth switch failed: {switch_combined.strip()[:500]}",
                "recovery": None,
                "capability_manifest": dict(_CAPABILITIES),
                "capability_revision": _CAPABILITY_REVISION,
                "discovery_state": DISCOVERY_UNKNOWN,
                "checked_at": now_iso,
            }
            self._persist_connection(ref, result)
            return result

        # Step 2: status read-back
        try:
            status_result = self._run_acli(
                ["acli", "confluence", "auth", "status"],
                principal,
                timeout=10.0,
            )
        except Exception as exc:
            result = {
                "state": STATE_DEGRADED,
                "provider_id": PROVIDER_ID,
                "connection_ref": ref,
                "account": {"site": site, "email": email},
                "error_code": CODE_UNAVAILABLE,
                "error_detail": f"acli auth status failed: {str(exc)[:500]}",
                "recovery": None,
                "capability_manifest": dict(_CAPABILITIES),
                "capability_revision": _CAPABILITY_REVISION,
                "discovery_state": DISCOVERY_UNKNOWN,
                "checked_at": now_iso,
            }
            self._persist_connection(ref, result)
            return result

        status_combined = (status_result.stdout or "") + "\n" + (status_result.stderr or "")

        if status_result.returncode != 0:
            if _is_unauthenticated(status_combined):
                login_cmd = (
                    f"acli confluence auth login --site {site} --email {email} --token"
                )
                result = {
                    "state": STATE_OWNER_ACTION_REQUIRED,
                    "provider_id": PROVIDER_ID,
                    "connection_ref": ref,
                    "account": {"site": site, "email": email},
                    "error_code": CODE_AUTH_REQUIRED,
                    "error_detail": "Not authenticated; run the login command",
                    "recovery": {
                        "command": login_cmd,
                        "hint": "Authenticate with your Atlassian API token",
                    },
                    "capability_manifest": dict(_CAPABILITIES),
                    "capability_revision": _CAPABILITY_REVISION,
                    "discovery_state": DISCOVERY_UNKNOWN,
                    "checked_at": now_iso,
                }
                self._persist_connection(ref, result)
                return result

            result = {
                "state": STATE_DEGRADED,
                "provider_id": PROVIDER_ID,
                "connection_ref": ref,
                "account": {"site": site, "email": email},
                "error_code": CODE_UNAVAILABLE,
                "error_detail": f"acli auth status non-zero: {status_combined.strip()[:500]}",
                "recovery": None,
                "capability_manifest": dict(_CAPABILITIES),
                "capability_revision": _CAPABILITY_REVISION,
                "discovery_state": DISCOVERY_UNKNOWN,
                "checked_at": now_iso,
            }
            self._persist_connection(ref, result)
            return result

        # Step 3: Parse and verify read-back
        parsed = _parse_acli_auth_status(status_combined, site, email)

        if not parsed.get("match"):
            result = {
                "state": STATE_DEGRADED,
                "provider_id": PROVIDER_ID,
                "connection_ref": ref,
                "account": {"site": site, "email": email},
                "error_code": CODE_SCOPE_DENIED,
                "error_detail": parsed.get("detail", "read-back mismatch"),
                "recovery": None,
                "capability_manifest": dict(_CAPABILITIES),
                "capability_revision": _CAPABILITY_REVISION,
                "discovery_state": DISCOVERY_UNKNOWN,
                "checked_at": now_iso,
            }
            self._persist_connection(ref, result)
            return result

        # Connected!
        result = {
            "state": STATE_CONNECTED,
            "provider_id": PROVIDER_ID,
            "connection_ref": ref,
            "account": {"site": site, "email": email},
            "error_code": None,
            "error_detail": None,
            "recovery": None,
            "capability_manifest": dict(_CAPABILITIES),
            "capability_revision": _CAPABILITY_REVISION,
            "discovery_state": DISCOVERY_UNKNOWN,
            "checked_at": now_iso,
            "last_connected_at": now_iso,
        }
        self._persist_connection(ref, result)
        return result

    # -- Persistence ----------------------------------------------------

    def _persist_connection(self, ref: str, result: dict[str, Any]) -> None:
        """Write connection state to watch_provider_connections.

        PROV-004: no credential/token material in the row or any log line.
        """
        if self._db is None:
            return
        repo = self._db.automations
        now_iso = result.get("checked_at") or datetime.now(timezone.utc).isoformat()
        cid = self._connection_id(ref)
        manifest_data = self.manifest()

        existing = repo.get_provider_connection(cid)
        if existing:
            repo.update_provider_connection(
                cid,
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
            )
        else:
            repo.create_provider_connection(
                connection_id=cid,
                provider_id=PROVIDER_ID,
                transport=TRANSPORT,
                external_connection_ref=ref,
                state=result["state"],
                capability_manifest_json=json.dumps(manifest_data["capabilities"]),
                capability_revision=manifest_data["revision"],
                discovery_state=DISCOVERY_UNKNOWN,
            )
            repo.update_provider_connection(
                cid,
                last_checked_at=now_iso,
                last_connected_at=now_iso if result["state"] == STATE_CONNECTED else None,
                last_error_code=result.get("error_code") or "",
                last_error_detail=result.get("error_detail") or "",
            )

    # -- Readiness (SETFLOW-005) ----------------------------------------

    def readiness(self, principal: Principal) -> dict[str, Any]:
        """Provider-level readiness projection (persisted rows + which only).

        NEVER runs acli -- computed from DB rows and ``shutil.which`` only.
        """
        if self._runner is None and shutil.which("acli") is None:
            return {
                "state": "unavailable",
                "connections": 0,
                "connected": 0,
                "recovery": {
                    "command": _INSTALL_COMMAND,
                    "hint": "Install acli to connect to Confluence",
                },
            }

        connections = self.list_connections(principal)
        connected_count = sum(
            1 for c in connections if c.get("state") == STATE_CONNECTED
        )

        if connected_count > 0:
            return {
                "state": "connected",
                "connections": len(connections),
                "connected": connected_count,
            }

        return {
            "state": "partial",
            "connections": len(connections),
            "connected": 0,
        }

    # -- Switch-and-verify helper ----------------------------------------

    def _with_account(
        self,
        principal: Principal,
        connection_ref_str: str,
        fn: Callable[[str, str], Any],
    ) -> Any:
        """Execute *fn(site, email)* under the switch-and-verify lock.

        1. Parse the connection ref.
        2. Acquire ``_ACLI_LOCK``.
        3. ``acli confluence auth switch --site S --email E``.
        4. ``acli confluence auth status`` -- parse and verify the read-back.
        5. If the read-back matches, call ``fn(site, email)`` and return
           its result.  If any step fails, return a typed error dict.

        The caller's *fn* runs INSIDE the lock, so it may call
        ``_run_acli`` without re-switching.  *fn* must NOT release the
        lock.
        """
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)

        # Binary-presence check
        if self._runner is None and shutil.which("acli") is None:
            return {
                "state": DISCOVERY_FAILED,
                "error_code": CODE_UNAVAILABLE,
                "error_detail": "Atlassian CLI (acli) is not installed",
                "connection_ref": canonical_ref,
                "items": [],
                "cursor": None,
            }

        with _ACLI_LOCK:
            # Step 1: switch
            try:
                switch_result = self._run_acli(
                    ["acli", "confluence", "auth", "switch",
                     "--site", site, "--email", email],
                    principal,
                    timeout=10.0,
                )
            except Exception as exc:
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_UNAVAILABLE,
                    "error_detail": f"acli auth switch failed: {str(exc)[:500]}",
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            switch_combined = (
                (switch_result.stdout or "")
                + "\n"
                + (switch_result.stderr or "")
            )

            if switch_result.returncode != 0:
                if _is_account_not_found(switch_combined) or _is_unauthenticated(switch_combined):
                    return {
                        "state": DISCOVERY_FAILED,
                        "error_code": CODE_AUTH_REQUIRED,
                        "error_detail": "Not authenticated; run the login command",
                        "connection_ref": canonical_ref,
                        "items": [],
                        "cursor": None,
                    }
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_UNAVAILABLE,
                    "error_detail": f"acli auth switch failed: {switch_combined.strip()[:500]}",
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            # Step 2: status read-back
            try:
                status_result = self._run_acli(
                    ["acli", "confluence", "auth", "status"],
                    principal,
                    timeout=10.0,
                )
            except Exception as exc:
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_UNAVAILABLE,
                    "error_detail": f"acli auth status failed: {str(exc)[:500]}",
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            status_combined = (
                (status_result.stdout or "")
                + "\n"
                + (status_result.stderr or "")
            )

            if status_result.returncode != 0:
                if _is_unauthenticated(status_combined):
                    return {
                        "state": DISCOVERY_FAILED,
                        "error_code": CODE_AUTH_REQUIRED,
                        "error_detail": "Not authenticated",
                        "connection_ref": canonical_ref,
                        "items": [],
                        "cursor": None,
                    }
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_UNAVAILABLE,
                    "error_detail": f"acli auth status non-zero: {status_combined.strip()[:500]}",
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            # Step 3: verify read-back
            parsed = _parse_acli_auth_status(status_combined, site, email)
            if not parsed.get("match"):
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_SCOPE_DENIED,
                    "error_detail": parsed.get("detail", "read-back mismatch"),
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            # Step 4: delegate -- still under the lock
            return fn(site, email)

    # -- Discovery (spaces) --------------------------------------------

    def discover(
        self,
        principal: Principal,
        connection_ref_str: str,
        *,
        kind: str = "spaces",
        query: str = "",
        cursor: int | None = None,
        limit: int = 30,
    ) -> dict[str, Any]:
        """Enumerate Confluence resources (spaces).

        Mirrors ``JiraProviderAdapter.discover`` in envelope shape.
        """
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)

        if kind == "spaces":
            return self._discover_spaces(
                principal, connection_ref_str,
                query=query, cursor=cursor, limit=limit,
            )
        else:
            return {
                "state": DISCOVERY_FAILED,
                "error_code": CODE_QUERY_INVALID,
                "error_detail": f"Unknown discover kind: {kind!r}",
                "connection_ref": canonical_ref,
                "items": [],
                "cursor": None,
            }

    def _discover_spaces(
        self,
        principal: Principal,
        connection_ref_str: str,
        *,
        query: str = "",
        cursor: int | None = None,
        limit: int = 30,
    ) -> dict[str, Any]:
        """kind=spaces: ``acli confluence space list --json --limit N``."""
        capped_limit = max(1, min(int(limit), 100))
        offset = max(0, int(cursor or 0))
        fetch_count = offset + capped_limit

        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)

        def _run(s: str, e: str) -> dict[str, Any]:
            command = [
                "acli", "confluence", "space", "list",
                "--json", "--limit", str(fetch_count),
            ]
            try:
                completed = self._run_acli(command, principal, timeout=15.0)
            except Exception as exc:
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_UNAVAILABLE,
                    "error_detail": str(exc)[:500],
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            if completed.returncode != 0:
                detail = ((completed.stderr or "") + "\n" + (completed.stdout or "")).strip()[:500]
                code = CODE_AUTH_REQUIRED if _is_unauthenticated(detail) else CODE_UNAVAILABLE
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": code,
                    "error_detail": detail,
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            try:
                rows = json.loads(completed.stdout or "[]")
            except json.JSONDecodeError:
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": "acli returned invalid JSON",
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            if not isinstance(rows, list):
                rows_list: list[Any] = []
                # Confluence space list may return {"results": [...]}
                if isinstance(rows, dict) and isinstance(rows.get("results"), list):
                    rows_list = rows["results"]
                else:
                    return {
                        "state": DISCOVERY_FAILED,
                        "error_code": CODE_QUERY_INVALID,
                        "error_detail": "acli returned non-array",
                        "connection_ref": canonical_ref,
                        "items": [],
                        "cursor": None,
                    }
                rows = rows_list

            # Offset-based cursor
            paged = rows[offset:]

            # Client-side filter on key/name (case-insensitive substring)
            if query:
                q_lower = query.lower()
                paged = [
                    r for r in paged
                    if isinstance(r, dict) and (
                        q_lower in str(r.get("key", "")).lower()
                        or q_lower in str(r.get("name", "")).lower()
                    )
                ]

            items: list[dict[str, Any]] = []
            for row in paged[:capped_limit]:
                if not isinstance(row, dict):
                    continue
                items.append({
                    "id": str(row.get("id", "")),
                    "key": row.get("key", ""),
                    "name": row.get("name", ""),
                    "type": row.get("type", ""),
                    "status": row.get("status", ""),
                })

            has_more = len(paged) > capped_limit
            next_cursor = offset + capped_limit if has_more else None

            if not items and not rows:
                state = DISCOVERY_PARTIAL
            else:
                state = DISCOVERY_READY

            return {
                "state": state,
                "error_code": None,
                "error_detail": None,
                "connection_ref": canonical_ref,
                "items": items,
                "cursor": next_cursor,
                "query": query or None,
            }

        return self._with_account(principal, connection_ref_str, _run)

    # -- Validate scope (space key) ------------------------------------

    def validate_scope(
        self,
        principal: Principal,
        connection_ref_str: str,
        space_key: str,
    ) -> dict[str, Any]:
        """ONE bounded read proving space existence + access.

        ``acli confluence space view --key K --json``.
        """
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)

        def _run(s: str, e: str) -> dict[str, Any]:
            command = [
                "acli", "confluence", "space", "view",
                "--key", space_key, "--json",
            ]
            try:
                completed = self._run_acli(command, principal, timeout=15.0)
            except Exception as exc:
                return {
                    "valid": False,
                    "space": None,
                    "error_code": CODE_UNAVAILABLE,
                    "error_detail": str(exc)[:500],
                    "connection_ref": canonical_ref,
                }

            if completed.returncode != 0:
                detail = ((completed.stderr or "") + "\n" + (completed.stdout or "")).strip()[:500]
                return {
                    "valid": False,
                    "space": None,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": detail,
                    "connection_ref": canonical_ref,
                }

            try:
                obj = json.loads(completed.stdout or "{}")
            except json.JSONDecodeError:
                return {
                    "valid": False,
                    "space": None,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": "acli returned invalid JSON",
                    "connection_ref": canonical_ref,
                }

            return {
                "valid": True,
                "space": {
                    "id": str(obj.get("id", "")),
                    "key": obj.get("key", ""),
                    "name": obj.get("name", ""),
                    "type": obj.get("type", ""),
                    "status": obj.get("status", ""),
                },
                "error_code": None,
                "error_detail": None,
                "connection_ref": canonical_ref,
            }

        return self._with_account(principal, connection_ref_str, _run)

    # -- Snapshot: recent_blogs ----------------------------------------

    def fetch_recent_blogs(
        self,
        principal: Principal,
        connection_ref_str: str,
        *,
        space_id: str,
        limit: int = 25,
    ) -> dict[str, Any]:
        """Fetch recent blog posts in a space via ``blog list --space-id``.

        Returns the discovery-envelope shape with normalized entities.
        """
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)
        capped_limit = max(1, min(int(limit), 100))

        def _run(s: str, e: str) -> dict[str, Any]:
            command = [
                "acli", "confluence", "blog", "list",
                "--space-id", space_id,
                "--json", "--limit", str(capped_limit),
            ]
            try:
                completed = self._run_acli(command, principal, timeout=15.0)
            except Exception as exc:
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_UNAVAILABLE,
                    "error_detail": str(exc)[:500],
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            if completed.returncode != 0:
                detail = ((completed.stderr or "") + "\n" + (completed.stdout or "")).strip()[:500]
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": detail,
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            stdout = (completed.stdout or "").strip()
            if not stdout:
                return {
                    "state": DISCOVERY_READY,
                    "error_code": None,
                    "error_detail": None,
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            try:
                raw = json.loads(stdout)
            except json.JSONDecodeError:
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": "acli returned invalid JSON",
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            blogs = raw if isinstance(raw, list) else (
                raw.get("results", []) if isinstance(raw, dict) else []
            )

            items = self._normalize_blog_entities(blogs, s)
            return {
                "state": DISCOVERY_READY,
                "error_code": None,
                "error_detail": None,
                "connection_ref": canonical_ref,
                "items": items,
                "cursor": None,
            }

        return self._with_account(principal, connection_ref_str, _run)

    # -- Snapshot: pages_by_id -----------------------------------------

    def fetch_pages_by_id(
        self,
        principal: Principal,
        connection_ref_str: str,
        *,
        page_ids: list[str],
    ) -> dict[str, Any]:
        """Fetch pages by known IDs via ``page view --id`` for each.

        Returns the discovery-envelope shape with normalized entities.
        """
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)

        if not page_ids:
            return {
                "state": DISCOVERY_READY,
                "error_code": None,
                "error_detail": None,
                "connection_ref": canonical_ref,
                "items": [],
                "cursor": None,
            }

        def _run(s: str, e: str) -> dict[str, Any]:
            items: list[dict[str, Any]] = []
            for page_id in page_ids:
                command = [
                    "acli", "confluence", "page", "view",
                    "--id", str(page_id), "--json",
                ]
                try:
                    completed = self._run_acli(command, principal, timeout=15.0)
                except Exception:
                    continue

                if completed.returncode != 0:
                    continue

                try:
                    obj = json.loads(completed.stdout or "{}")
                except json.JSONDecodeError:
                    continue

                if isinstance(obj, dict) and obj.get("id"):
                    items.append(self._normalize_page_entity(obj, s))

            return {
                "state": DISCOVERY_READY,
                "error_code": None,
                "error_detail": None,
                "connection_ref": canonical_ref,
                "items": items,
                "cursor": None,
            }

        return self._with_account(principal, connection_ref_str, _run)

    # -- The critical gap: page listing is unsupported ------------------

    def fetch_page_listing(
        self,
        principal: Principal,
        connection_ref_str: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Return a typed ``unsupported_by_cli`` error.

        ``acli confluence`` has NO ``page list`` or ``page search`` command.
        This method exists so callers get an honest error, never a silent
        empty snapshot.
        """
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)
        return {
            "state": DISCOVERY_FAILED,
            "error_code": CODE_UNSUPPORTED_BY_CLI,
            "error_detail": (
                "acli confluence has no 'page list' or 'page search' command; "
                "use 'recent_blogs' for blog posts or 'pages_by_id' for known page IDs"
            ),
            "connection_ref": canonical_ref,
            "items": [],
            "cursor": None,
        }

    # -- Entity normalization ------------------------------------------

    @staticmethod
    def _normalize_blog_entities(
        blogs: list[Any], site: str,
    ) -> list[dict[str, Any]]:
        """Normalize raw acli blog list objects to the HoldSpeak entity shape."""
        items: list[dict[str, Any]] = []
        for blog in blogs:
            if not isinstance(blog, dict):
                continue
            # Extract author -- may be nested or flat
            author_raw = blog.get("authorId") or blog.get("author") or ""
            if isinstance(author_raw, dict):
                author = author_raw.get("email") or author_raw.get("displayName") or ""
            else:
                author = str(author_raw)

            # Extract space key
            space_key = ""
            space_id = str(blog.get("spaceId", ""))
            space_raw = blog.get("space")
            if isinstance(space_raw, dict):
                space_key = space_raw.get("key", "")

            # Labels
            labels_raw = blog.get("labels") or []
            if isinstance(labels_raw, list):
                labels = [
                    (lb.get("name") or lb.get("label") or str(lb))
                    if isinstance(lb, dict) else str(lb)
                    for lb in labels_raw
                ]
            else:
                labels = []

            # Build URL
            url = blog.get("url") or blog.get("_links", {}).get("webui", "")
            if not url and site:
                blog_id = blog.get("id", "")
                if blog_id:
                    url = f"https://{site}/wiki/blog/{blog_id}"

            items.append({
                "id": str(blog.get("id", "")),
                "key": "",
                "title": blog.get("title", ""),
                "url": url,
                "status": blog.get("status", "current"),
                "space_key": space_key,
                "space_id": space_id,
                "author": author,
                "updated_at": blog.get("version", {}).get("createdAt", "")
                    if isinstance(blog.get("version"), dict)
                    else blog.get("updatedAt", blog.get("updated_at", "")),
                "created_at": blog.get("createdAt", blog.get("created_at", "")),
                "labels": labels,
                "entity_type": "blog",
            })
        return items

    @staticmethod
    def _normalize_page_entity(
        page: dict[str, Any], site: str,
    ) -> dict[str, Any]:
        """Normalize a single raw acli page view object to the entity shape."""
        author_raw = page.get("authorId") or page.get("author") or ""
        if isinstance(author_raw, dict):
            author = author_raw.get("email") or author_raw.get("displayName") or ""
        else:
            author = str(author_raw)

        space_key = ""
        space_id = str(page.get("spaceId", ""))
        space_raw = page.get("space")
        if isinstance(space_raw, dict):
            space_key = space_raw.get("key", "")

        labels_raw = page.get("labels") or []
        if isinstance(labels_raw, list):
            labels = [
                (lb.get("name") or lb.get("label") or str(lb))
                if isinstance(lb, dict) else str(lb)
                for lb in labels_raw
            ]
        else:
            labels = []

        url = page.get("url") or page.get("_links", {}).get("webui", "")
        if not url and site:
            page_id = page.get("id", "")
            if page_id:
                url = f"https://{site}/wiki/pages/{page_id}"

        return {
            "id": str(page.get("id", "")),
            "key": "",
            "title": page.get("title", ""),
            "url": url,
            "status": page.get("status", "current"),
            "space_key": space_key,
            "space_id": space_id,
            "author": author,
            "updated_at": page.get("version", {}).get("createdAt", "")
                if isinstance(page.get("version"), dict)
                else page.get("updatedAt", page.get("updated_at", "")),
            "created_at": page.get("createdAt", page.get("created_at", "")),
            "labels": labels,
            "entity_type": "page",
        }
