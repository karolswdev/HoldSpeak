"""JiraProviderAdapter -- the V0 acli Jira provider for Project Room Watches.

HS-166-01.  Mirrors ``GitHubProviderAdapter`` (github_provider.py) in shape
and reuses its PROV-009 error codes and SRS SS6 states by import.

THE MULTI-ACCOUNT ANSWER: acli keeps ONE global current account.  Every
HoldSpeak read is ``switch --site S --email E`` then ``auth status``
under ONE process-wide ``threading.RLock`` (the switch-and-verify law).
The status read-back is parsed tolerantly: if the site or email in the
output does not match what was switched TO, the result is a typed error
(CODE_SCOPE_DENIED-class) with state ``degraded``, never a silent wrong
read.

THE KERNEL ANSWER: production acli calls reach the kernel through
``PermissionGate(acli_jira.MANIFEST).run_read_subprocess()`` -- the same
admitted path ``GitHubProviderAdapter`` uses for ``gh``.

Connection identity: **(site, email)** serialized as ``site|email``
(the ``|`` separator is not legal in either an Atlassian site host or
an email address, so it is unambiguous).  Each combination is one row
in ``watch_provider_connections`` with ``provider_id="jira"`` and
``external_connection_ref="site|email"``.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import subprocess
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from holdspeak.connector_packs import acli_jira
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
    DISCOVERY_UNKNOWN,
    STATE_CONNECTED,
    STATE_DEGRADED,
    STATE_DISCONNECTED,
    STATE_OWNER_ACTION_REQUIRED,
    STATE_UNAVAILABLE,
)

_log = logging.getLogger(__name__)

Runner = Callable[..., subprocess.CompletedProcess[str]]

PROVIDER_ID = "jira"
TRANSPORT = "connector_pack"

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

# ── The switch-and-verify lock ──────────────────────────────────────
# Module-level RLock.  acli's ``current_profile`` is a PROCESS-GLOBAL
# setting: ``acli jira auth switch`` changes which site+email every
# subsequent command targets.  Two concurrent HoldSpeak callers (the
# conductor's evaluate_due, a web discover) interleaving ``switch``
# calls would read the wrong site.  This lock serializes every
# switch-then-read sequence so a status read-back always matches the
# preceding switch.

_ACLI_LOCK = threading.RLock()

# ── Connection ref separator ────────────────────────────────────────
# ``|`` is illegal in both Atlassian site hosts and email addresses,
# making the serialization ``site|email`` unambiguous and splittable.
CONNECTION_REF_SEP = "|"

# Install recovery command template.
_INSTALL_COMMAND = "brew tap atlassian/homebrew-acli && brew install acli"


def _normalize_site(raw: str) -> str:
    """Normalize a site input to ``<slug>.atlassian.net``.

    Accepts:
      - ``"mysite"`` -> ``"mysite.atlassian.net"``
      - ``"mysite.atlassian.net"`` -> ``"mysite.atlassian.net"``
      - ``"https://mysite.atlassian.net/"`` -> ``"mysite.atlassian.net"``
      - ``"https://mysite.atlassian.net"`` -> ``"mysite.atlassian.net"``

    Raises ``ValidationError`` on anything else (empty, non-atlassian
    domains, malformed).
    """
    cleaned = raw.strip().lower()
    if not cleaned:
        raise ValidationError("site is required")

    # Strip protocol prefix
    cleaned = re.sub(r"^https?://", "", cleaned)
    # Strip trailing slashes
    cleaned = cleaned.rstrip("/")

    # Already fully qualified?
    if cleaned.endswith(".atlassian.net"):
        slug = cleaned[: -len(".atlassian.net")]
        if not slug or not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
            raise ValidationError(
                f"Invalid Atlassian site slug: {slug!r}",
                context={"error_code": CODE_QUERY_INVALID},
            )
        return cleaned

    # Bare slug: must be a valid subdomain label.
    if re.match(r"^[a-z0-9][a-z0-9-]*$", cleaned):
        return f"{cleaned}.atlassian.net"

    raise ValidationError(
        f"Cannot normalize site: {raw!r} (expected 'slug', "
        f"'slug.atlassian.net', or 'https://slug.atlassian.net/')",
        context={"error_code": CODE_QUERY_INVALID},
    )


def _parse_connection_ref(ref: str) -> tuple[str, str]:
    """Split ``site|email`` back into (site, email) with normalization.

    Normalizes the site through ``_normalize_site`` so caller-supplied
    refs (e.g. ``"https://x.atlassian.net/|user@example.com"``) resolve
    to the canonical row.  Raises on bad shape.
    """
    if CONNECTION_REF_SEP not in ref:
        raise ValidationError(
            f"Malformed connection ref: {ref!r}",
            context={"error_code": CODE_QUERY_INVALID},
        )
    site_raw, email = ref.split(CONNECTION_REF_SEP, 1)
    site = _normalize_site(site_raw)
    email = email.strip().lower()
    return site, email


def connection_ref(site: str, email: str) -> str:
    """Build the canonical ``site|email`` connection ref.

    Normalizes both parts: site through ``_normalize_site`` (so
    ``"https://x.atlassian.net/"`` and ``"x"`` and ``"x.atlassian.net"``
    all produce the same ref), email lowercased and stripped.
    """
    norm_site = _normalize_site(site)
    norm_email = email.strip().lower()
    return f"{norm_site}{CONNECTION_REF_SEP}{norm_email}"


def _is_unauthenticated(text: str) -> bool:
    """Return True if text looks like an acli auth-required error.

    Recorded shape (acli 1.3.36-stable, live):
      ``"\\u2717 Error: unauthorized: use 'acli jira auth login' to authenticate"``
    """
    lower = text.lower()
    return (
        "unauthorized" in lower
        or "use 'acli jira auth login'" in lower
    )


def _is_account_not_found(text: str) -> bool:
    """Return True if text is an acli "account not found" error.

    Recorded shape (acli 1.3.36-stable, live):
      ``"\\u2717 Error: account with email 'X' and site 'Y' not found, ..."``

    This is distinct from unauthenticated: acli does not even KNOW this
    (site, email) combination, so the user needs ``auth login``, not
    just ``auth switch``.
    """
    lower = text.lower()
    return "not found" in lower and ("account" in lower or "email" in lower)


def _parse_acli_auth_status(output: str, expected_site: str, expected_email: str) -> dict[str, Any]:
    """Parse ``acli jira auth status`` output for a connected account.

    Recorded shape (acli 1.3.36-stable, live, 2026-09-03):
      ``"\\u2713 Authenticated\\n  Site: mysite.atlassian.net\\n  Email: user@example.com\\n  Authentication Type: oauth\\n"``

    The parser is tolerant: it first tries the structured "Site:" / "Email:"
    lines, then falls back to scanning for an ``*.atlassian.net`` host and
    an email anywhere in the text.

    Returns:
      - ``{"match": True, "site": ..., "email": ..., "auth_type": ...}`` on success.
      - ``{"match": False, "site": ..., "email": ..., "detail": ...}``
        when the read-back names a different account.
      - ``{"match": False, "detail": "..."}`` when nothing parseable.
    """
    found_site: str | None = None
    found_email: str | None = None
    auth_type: str | None = None

    # Preferred: structured "Site:" and "Email:" lines (real acli shape)
    site_line = re.search(r"(?i)site:\s*(\S+)", output)
    email_line = re.search(r"(?i)email:\s*(\S+)", output)
    auth_line = re.search(r"(?i)authentication\s+type:\s*(\S+)", output)

    if site_line:
        found_site = site_line.group(1).lower().strip()
    if email_line:
        found_email = email_line.group(1).lower().strip()
    if auth_line:
        auth_type = auth_line.group(1).strip()

    # Fallback: scan for *.atlassian.net and email pattern anywhere
    if not found_site:
        m = re.search(r"([a-z0-9][a-z0-9-]*\.atlassian\.net)", output.lower())
        if m:
            found_site = m.group(1)
    if not found_email:
        m = re.search(r"[\w.+-]+@[\w.-]+\.\w+", output)
        if m:
            found_email = m.group(0).lower()

    if found_site and found_email:
        if found_site == expected_site.lower() and found_email == expected_email.lower():
            result: dict[str, Any] = {"match": True, "site": found_site, "email": found_email}
            if auth_type:
                result["auth_type"] = auth_type
            return result
        return {
            "match": False,
            "site": found_site,
            "email": found_email,
            "detail": (
                f"read-back mismatch: expected {expected_site}/{expected_email} "
                f"got {found_site}/{found_email}"
            ),
        }

    # Partial parse: one of the two was found.
    if found_site or found_email:
        if found_site and found_site != expected_site.lower():
            return {
                "match": False,
                "site": found_site,
                "email": found_email,
                "detail": (
                    f"read-back mismatch: expected site {expected_site} "
                    f"got {found_site}"
                ),
            }
        if found_email and found_email != expected_email.lower():
            return {
                "match": False,
                "site": found_site,
                "email": found_email,
                "detail": (
                    f"read-back mismatch: expected email {expected_email} "
                    f"got {found_email}"
                ),
            }
        result = {"match": True, "site": found_site or expected_site, "email": found_email or expected_email}
        if auth_type:
            result["auth_type"] = auth_type
        return result

    return {"match": False, "detail": f"Could not parse auth status output: {output[:200]}"}


class JiraProviderAdapter:
    """V0 Atlassian CLI (acli) Jira provider adapter (SS11 protocol subset).

    Takes the same ``runner`` seam as ``GitHubProviderAdapter``: tests inject
    a fake; production defaults to ``subprocess.run`` via the admitted
    ``PermissionGate.run_read_subprocess`` path.
    """

    def __init__(
        self,
        db: Any = None,
        *,
        runner: Runner | None = None,
        registry_path: Path | None = None,
    ) -> None:
        self._db = db
        self._runner = runner
        self._registry_path = registry_path or Path.home() / ".config" / "acli" / "jira_config.yaml"

    # ── Manifest (PROV-001, PROV-007) ────────────────────────────────

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

    # ── Admitted subprocess seam ─────────────────────────────────────

    def _run_acli(
        self,
        command: list[str],
        principal: Principal,
        *,
        timeout: float = acli_jira.DEFAULT_TIMEOUT_SECONDS,
    ) -> subprocess.CompletedProcess[str]:
        """Single admitted subprocess entry point for all acli CLI calls.

        Routes through ``PermissionGate.run_read_subprocess`` -- the same
        kernel-admitted path ``GitHubProviderAdapter`` uses for ``gh``.
        """
        return PermissionGate(acli_jira.MANIFEST).run_read_subprocess(
            command,
            principal=principal,
            runner=self._runner,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
        )

    # ── Connection identity ──────────────────────────────────────────

    @staticmethod
    def normalize_site(site: str) -> str:
        """Normalize a site string to canonical ``<slug>.atlassian.net`` form."""
        return _normalize_site(site)

    @staticmethod
    def connection_ref(site: str, email: str) -> str:
        """Build the ``site|email`` connection ref from normalized parts."""
        return connection_ref(site, email)

    def _connection_id(self, ref: str) -> str:
        """DB primary key for a Jira connection row."""
        return f"wpc_{PROVIDER_ID}_{ref}"

    # ── Connection CRUD ──────────────────────────────────────────────

    def list_connections(self, principal: Principal) -> list[dict[str, Any]]:
        """Return all ``watch_provider_connections`` rows for provider_id='jira'."""
        if self._db is None:
            return []
        return self._db.automations.list_provider_connections(provider_id=PROVIDER_ID)

    def add_connection(
        self,
        principal: Principal,
        site: str,
        email: str,
    ) -> dict[str, Any]:
        """Upsert a Jira connection row for (site, email).

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

    def remove_connection(
        self,
        principal: Principal,
        connection_ref_str: str,
    ) -> bool:
        """Remove a Jira connection row.  Returns True if deleted, False if absent."""
        if self._db is None:
            return False
        site, email = _parse_connection_ref(connection_ref_str)
        cid = self._connection_id(connection_ref(site, email))
        repo = self._db.automations
        existing = repo.get_provider_connection(cid)
        if not existing:
            return False
        with repo._connection() as conn:
            conn.execute("DELETE FROM watch_provider_connections WHERE id=?", (cid,))
        return True

    # ── Connection status (PROV-003, PROV-004) ───────────────────────

    def connection_status(
        self,
        principal: Principal,
        connection_ref_str: str,
        *,
        recheck: bool = True,
    ) -> dict[str, Any]:
        """Probe one Jira connection under the switch-and-verify lock.

        1. ``acli jira auth switch --site S --email E``
        2. ``acli jira auth status``
        3. Parse the status read-back and verify site+email match.

        All under ``_ACLI_LOCK`` so concurrent callers cannot interleave
        switch commands.
        """
        site, email = _parse_connection_ref(connection_ref_str)
        # Reconstruct the canonical ref from normalized parts so all
        # persistence and return values use the same identity.
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
                    "hint": "Install acli to connect to Jira",
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
                ["acli", "jira", "auth", "switch", "--site", site, "--email", email],
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

        # If switch fails: either acli does not know this account ("not found")
        # or the user is unauthenticated.  Both → owner_action_required.
        if switch_result.returncode != 0:
            if _is_account_not_found(switch_combined) or _is_unauthenticated(switch_combined):
                login_cmd = (
                    f"acli jira auth login --site {site} --email {email} --token"
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

            # Non-auth failure on switch
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
                ["acli", "jira", "auth", "status"],
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

        # Unauthenticated?
        if status_result.returncode != 0:
            if _is_unauthenticated(status_combined):
                login_cmd = (
                    f"acli jira auth login --site {site} --email {email} --token"
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

            # Non-auth failure
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
            # Read-back mismatch -> typed error, degraded
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

    # ── Persistence ──────────────────────────────────────────────────

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

    # ── Readiness (SETFLOW-005) ──────────────────────────────────────

    def readiness(self, principal: Principal) -> dict[str, Any]:
        """Provider-level readiness projection (persisted rows + which only).

        - ``unavailable``: acli binary not found.
        - ``partial``: acli present, zero connected rows (SETFLOW-005).
        - ``connected``: at least one connection in ``connected`` state.

        NEVER runs acli -- computed from DB rows and ``shutil.which`` only.
        """
        if self._runner is None and shutil.which("acli") is None:
            return {
                "state": "unavailable",
                "connections": 0,
                "connected": 0,
                "recovery": {
                    "command": _INSTALL_COMMAND,
                    "hint": "Install acli to connect to Jira",
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

    # ── Known accounts (acli registry) ───────────────────────────────

    def known_accounts(self, principal: Principal) -> list[dict[str, Any]]:
        """Parse acli's account registry to enumerate accounts it already knows.

        Reads ``~/.config/acli/jira_config.yaml`` (path overridable via
        constructor kwarg ``registry_path``).  Returns a list of
        ``{site, email, display_name, auth_type, ref, current}`` dicts.
        ``cloud_id`` and ``account_id`` are opaque and never surfaced.

        Tolerant: missing file, empty profiles, unparsable YAML all
        return ``[]`` with no exception.
        """
        import yaml

        path = self._registry_path
        result: list[dict[str, Any]] = []

        try:
            if not path.exists():
                return result
            raw = path.read_text(encoding="utf-8")
            data = yaml.safe_load(raw)
            if not isinstance(data, dict):
                return result
        except Exception as exc:
            _log.debug("Could not read acli registry at %s: %s", path, exc)
            return result

        current_profile = data.get("current_profile", "")
        profiles = data.get("profiles") or []
        if not isinstance(profiles, list):
            return result

        for p in profiles:
            if not isinstance(p, dict):
                continue
            site = str(p.get("site", "")).strip()
            email = str(p.get("email", "")).strip().lower()
            if not site or not email:
                continue

            # Build the opaque identity for "is this the current profile?"
            cloud_id = str(p.get("cloud_id", ""))
            account_id = str(p.get("account_id", ""))
            profile_key = f"{cloud_id}:{account_id}" if cloud_id and account_id else ""

            ref = connection_ref(site, email)
            result.append({
                "site": site,
                "email": email,
                "display_name": str(p.get("display_name", "")),
                "auth_type": str(p.get("auth_type", "")),
                "ref": ref,
                "current": profile_key == current_profile and bool(current_profile),
            })

        return result
