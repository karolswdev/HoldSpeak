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

# ── The switch-and-verify lock (HS-167-02: file lock) ──────────────
# acli's ``current_profile`` is a PROCESS-GLOBAL setting: ``acli jira
# auth switch`` changes which site+email every subsequent command
# targets.  The MCP sidecar runs in a SEPARATE process from the web
# server, so a per-process threading.RLock is not enough.  This lock
# uses ``fcntl.flock`` on a lockfile under the data dir the web server
# and the sidecar share, wrapped with in-process RLock semantics
# (reentrancy within one thread) and a bounded wait that raises a
# typed PROV-009-class error (never a hang).

import fcntl
import os
import time as _time

# Env-tunable bounded wait (seconds).  Default 10s.
_ACLI_LOCK_TIMEOUT = float(os.environ.get("HOLDSPEAK_ACLI_LOCK_TIMEOUT", "10"))

# Typed error code for lock timeout (PROV-009 class).
CODE_LOCK_TIMEOUT = "lock_timeout"


def _acli_lockfile_path() -> Path:
    """Return the lockfile path under the data dir shared by web + MCP."""
    from holdspeak.db.core import DEFAULT_DB_PATH
    return DEFAULT_DB_PATH.parent / ".acli.lock"


class _CrossProcessLock:
    """File-backed lock with in-process RLock reentrancy and bounded wait.

    On acquire:
      1. Acquire the in-process RLock (thread reentrancy).
      2. Acquire an exclusive flock on the lockfile (cross-process).
    On release: reverse order.

    If the flock cannot be acquired within ``timeout`` seconds, raises
    a ServiceError with ``CODE_LOCK_TIMEOUT``.
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self._rlock = threading.RLock()
        self._timeout = timeout
        self._fd: int | None = None

    def __enter__(self) -> "_CrossProcessLock":
        self._rlock.acquire()
        try:
            path = _acli_lockfile_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            self._fd = os.open(str(path), os.O_CREAT | os.O_RDWR)
            deadline = _time.monotonic() + self._timeout
            while True:
                try:
                    fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return self
                except (OSError, IOError):
                    if _time.monotonic() >= deadline:
                        os.close(self._fd)
                        self._fd = None
                        self._rlock.release()
                        raise ServiceError(
                            CODE_LOCK_TIMEOUT,
                            f"Could not acquire acli lock within {self._timeout}s "
                            "(another HoldSpeak process holds it)",
                            context={"status": 503},
                        )
                    _time.sleep(0.05)
        except ServiceError:
            raise
        except Exception:
            self._rlock.release()
            raise

    def __exit__(self, *exc: object) -> None:
        try:
            if self._fd is not None:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
                os.close(self._fd)
                self._fd = None
        finally:
            self._rlock.release()


_ACLI_LOCK = _CrossProcessLock(timeout=_ACLI_LOCK_TIMEOUT)

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
        if not found_site or not found_email:
            # Counsel S-3: a read-back that names neither site nor email
            # is NOT a match -- never fill the blanks from expectations.
            return {
                "match": False,
                "site": found_site,
                "email": found_email,
                "detail": "read-back incomplete: site or email not found in auth status",
            }
        result = {"match": True, "site": found_site, "email": found_email}
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

    # ── Switch-and-verify helper ────────────────────────────────────

    def _with_account(
        self,
        principal: Principal,
        connection_ref_str: str,
        fn: Callable[[str, str], Any],
    ) -> Any:
        """Execute *fn(site, email)* under the switch-and-verify lock.

        1. Parse the connection ref.
        2. Acquire ``_ACLI_LOCK``.
        3. ``acli jira auth switch --site S --email E``.
        4. ``acli jira auth status`` -- parse and verify the read-back.
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
                    ["acli", "jira", "auth", "switch",
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
                    ["acli", "jira", "auth", "status"],
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

    # ── Discovery (PROV-006) ────────────────────────────────────────

    # Jira's three fixed status categories (not invented -- Jira documents these).
    _JIRA_STATUS_CATEGORIES: list[dict[str, str]] = [
        {"key": "new", "name": "To Do"},
        {"key": "indeterminate", "name": "In Progress"},
        {"key": "done", "name": "Done"},
    ]

    def discover(
        self,
        principal: Principal,
        connection_ref_str: str,
        *,
        kind: str = "projects",
        query: str = "",
        project_key: str = "",
        cursor: int | None = None,
        limit: int = 30,
    ) -> dict[str, Any]:
        """Enumerate Jira resources (projects, issue_types, statuses).

        Mirrors ``GitHubProviderAdapter.discover`` in envelope shape.
        Every call runs under the switch-and-verify lock via ``_with_account``.
        """
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)

        if kind == "projects":
            return self._discover_projects(
                principal, connection_ref_str,
                query=query, cursor=cursor, limit=limit,
            )
        elif kind == "issue_types":
            pk = project_key or query
            if not pk:
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": "project_key is required for kind=issue_types",
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }
            return self._discover_issue_types(principal, connection_ref_str, pk)
        elif kind == "statuses":
            pk = project_key or query
            if not pk:
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": "project_key is required for kind=statuses",
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }
            return self._discover_statuses(principal, connection_ref_str, pk)
        else:
            return {
                "state": DISCOVERY_FAILED,
                "error_code": CODE_QUERY_INVALID,
                "error_detail": f"Unknown discover kind: {kind!r}",
                "connection_ref": canonical_ref,
                "items": [],
                "cursor": None,
            }

    def _discover_projects(
        self,
        principal: Principal,
        connection_ref_str: str,
        *,
        query: str = "",
        cursor: int | None = None,
        limit: int = 30,
    ) -> dict[str, Any]:
        """kind=projects: ``acli jira project list --json --limit N``."""
        capped_limit = max(1, min(int(limit), 100))
        offset = max(0, int(cursor or 0))
        fetch_count = offset + capped_limit

        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)

        def _run(s: str, e: str) -> dict[str, Any]:
            command = [
                "acli", "jira", "project", "list",
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
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": "acli returned non-array",
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

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
                lead = row.get("lead") or {}
                items.append({
                    "id": row.get("key", ""),
                    "key": row.get("key", ""),
                    "name": row.get("name", ""),
                    "project_id": str(row.get("id", "")),
                    "type": row.get("projectTypeKey", ""),
                    "style": row.get("style", ""),
                    "private": row.get("isPrivate", False),
                    "lead": lead.get("displayName") if isinstance(lead, dict) else None,
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

    def _discover_issue_types(
        self,
        principal: Principal,
        connection_ref_str: str,
        project_key: str,
    ) -> dict[str, Any]:
        """kind=issue_types: ``acli jira project view --key K --json``."""
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)

        def _run(s: str, e: str) -> dict[str, Any]:
            command = [
                "acli", "jira", "project", "view",
                "--key", project_key, "--json",
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

            try:
                project_obj = json.loads(completed.stdout or "{}")
            except json.JSONDecodeError:
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": "acli returned invalid JSON",
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            raw_types = project_obj.get("issueTypes") or []
            items: list[dict[str, Any]] = []
            for it in raw_types:
                if not isinstance(it, dict):
                    continue
                item: dict[str, Any] = {
                    "id": str(it.get("id", "")),
                    "name": it.get("name", ""),
                    "subtask": bool(it.get("subtask", False)),
                }
                if "hierarchyLevel" in it:
                    item["hierarchy_level"] = it["hierarchyLevel"]
                items.append(item)

            return {
                "state": DISCOVERY_READY,
                "error_code": None,
                "error_detail": None,
                "connection_ref": canonical_ref,
                "items": items,
                "cursor": None,
                "source": "enumerated",
            }

        return self._with_account(principal, connection_ref_str, _run)

    def _discover_statuses(
        self,
        principal: Principal,
        connection_ref_str: str,
        project_key: str,
    ) -> dict[str, Any]:
        """kind=statuses: derived from a bounded search."""
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)

        def _run(s: str, e: str) -> dict[str, Any]:
            command = [
                "acli", "jira", "workitem", "search",
                "--jql", f"project = {project_key}",
                "--fields", "key,status",
                "--json", "--limit", "200",
            ]
            try:
                completed = self._run_acli(command, principal, timeout=30.0)
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

            try:
                issues = json.loads(completed.stdout or "[]")
            except json.JSONDecodeError:
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": "acli returned invalid JSON",
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            if not isinstance(issues, list):
                issues = []

            # Extract distinct statuses
            seen: dict[str, dict[str, Any]] = {}
            for issue in issues:
                if not isinstance(issue, dict):
                    continue
                fields = issue.get("fields") or {}
                status = fields.get("status") or {}
                if not isinstance(status, dict):
                    continue
                sid = str(status.get("id", ""))
                if sid and sid not in seen:
                    cat = status.get("statusCategory") or {}
                    seen[sid] = {
                        "id": sid,
                        "name": status.get("name", ""),
                        "category": cat.get("key", "") if isinstance(cat, dict) else "",
                        "category_name": cat.get("name", "") if isinstance(cat, dict) else "",
                    }

            # Sort by category then name
            items = sorted(
                seen.values(),
                key=lambda s: (s.get("category", ""), s.get("name", "")),
            )

            return {
                "state": DISCOVERY_READY,
                "error_code": None,
                "error_detail": None,
                "connection_ref": canonical_ref,
                "items": items,
                "cursor": None,
                "source": "observed",
                "categories": [
                    {**c, "source": "static"}
                    for c in self._JIRA_STATUS_CATEGORIES
                ],
            }

        return self._with_account(principal, connection_ref_str, _run)

    # ── Search (PROV-006) ───────────────────────────────────────────

    # The fields acli search allows (THE SEARCH FIELD CAP).
    _SEARCH_ALLOWED_FIELDS = frozenset({
        "issuetype", "key", "assignee", "priority", "status",
        "summary", "labels", "reporter", "creator", "description",
    })

    # Default search fields for normalized items.
    _SEARCH_FIELDS = "key,summary,issuetype,status,assignee,priority,labels"

    def search(
        self,
        principal: Principal,
        connection_ref_str: str,
        *,
        jql: str,
        limit: int = 50,
        enrich: bool = False,
    ) -> dict[str, Any]:
        """Search Jira issues by JQL.

        JQL passes through VERBATIM (PROV-011).  Bad JQL returns
        ``query_invalid`` with acli's message verbatim.
        """
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)
        capped_limit = max(1, min(int(limit), 200))

        def _run(s: str, e: str) -> dict[str, Any]:
            command = [
                "acli", "jira", "workitem", "search",
                "--jql", jql,
                "--fields", self._SEARCH_FIELDS,
                "--json", "--limit", str(capped_limit),
            ]
            try:
                completed = self._run_acli(command, principal, timeout=30.0)
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
                detail = ((completed.stderr or "") + "\n" + (completed.stdout or "")).strip()
                # Strip the leading check-mark error prefix
                clean = re.sub(r"^[✗✘]\s*Error:\s*", "", detail).strip()[:500]
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": clean,
                    "connection_ref": canonical_ref,
                    "query_invalid": clean,
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
                    "calls": 1,
                }

            try:
                issues = json.loads(stdout)
            except json.JSONDecodeError:
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": "acli returned invalid JSON",
                    "connection_ref": canonical_ref,
                    "items": [],
                    "cursor": None,
                }

            if not isinstance(issues, list):
                issues = []

            items = self._normalize_search_items(issues, s)
            calls = 1

            # Enrich with workitem view for fields the search cap blocks
            if enrich:
                for item in items:
                    view_result = self._enrich_item(principal, item["key"])
                    if view_result is not None:
                        item.update(view_result)
                    calls += 1

            return {
                "state": DISCOVERY_READY,
                "error_code": None,
                "error_detail": None,
                "connection_ref": canonical_ref,
                "items": items,
                "cursor": None,
                "calls": calls,
            }

        return self._with_account(principal, connection_ref_str, _run)

    def _normalize_search_items(
        self, issues: list[Any], site: str,
    ) -> list[dict[str, Any]]:
        """Normalize raw acli search issue objects to the HoldSpeak shape."""
        items: list[dict[str, Any]] = []
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            fields = issue.get("fields") or {}
            status = fields.get("status") or {}
            status_cat = status.get("statusCategory") or {} if isinstance(status, dict) else {}
            issuetype = fields.get("issuetype") or {}
            assignee = fields.get("assignee")
            priority = fields.get("priority")
            key = issue.get("key", "")

            items.append({
                "key": key,
                "id": str(issue.get("id", "")),
                "summary": fields.get("summary", ""),
                "issue_type": issuetype.get("name", "") if isinstance(issuetype, dict) else "",
                "status": status.get("name", "") if isinstance(status, dict) else "",
                "status_category": status_cat.get("key", "") if isinstance(status_cat, dict) else "",
                "assignee": assignee.get("displayName") if isinstance(assignee, dict) else None,
                "assignee_id": assignee.get("accountId") if isinstance(assignee, dict) else None,
                "priority": priority.get("name") if isinstance(priority, dict) else None,
                "labels": fields.get("labels", []),
                "url": f"https://{site}/browse/{key}" if key else "",
            })
        return items

    def _enrich_item(
        self,
        principal: Principal,
        key: str,
    ) -> dict[str, Any] | None:
        """Enrich one item via ``acli jira workitem view KEY --fields ... --json``.

        Called INSIDE the lock (by ``_with_account``'s *fn*).
        Returns the enrichment fields or None on failure.
        """
        enrich_fields = "duedate,resolution,resolutiondate,updated,created,statuscategorychangedate,project"
        command = [
            "acli", "jira", "workitem", "view", key,
            "--fields", enrich_fields, "--json",
        ]
        try:
            completed = self._run_acli(command, principal, timeout=15.0)
        except Exception:
            return None

        if completed.returncode != 0:
            return None

        try:
            obj = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            return None

        fields = obj.get("fields") or {}
        project = fields.get("project") or {}
        return {
            "due_at": fields.get("duedate"),
            "resolution": (fields.get("resolution") or {}).get("name") if isinstance(fields.get("resolution"), dict) else fields.get("resolution"),
            "resolved_at": fields.get("resolutiondate"),
            "updated_at": fields.get("updated"),
            "created_at": fields.get("created"),
            "status_changed_at": fields.get("statuscategorychangedate"),
            "project_key": project.get("key") if isinstance(project, dict) else None,
        }

    def count(
        self,
        principal: Principal,
        connection_ref_str: str,
        *,
        jql: str,
    ) -> dict[str, Any]:
        """Count issues matching JQL via ``--count``."""
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)

        def _run(s: str, e: str) -> dict[str, Any]:
            command = [
                "acli", "jira", "workitem", "search",
                "--jql", jql, "--count",
            ]
            try:
                completed = self._run_acli(command, principal, timeout=15.0)
            except Exception as exc:
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_UNAVAILABLE,
                    "error_detail": str(exc)[:500],
                    "connection_ref": canonical_ref,
                    "count": None,
                }

            combined = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()

            if completed.returncode != 0:
                clean = re.sub(r"^[✗✘]\s*Error:\s*", "", combined).strip()[:500]
                return {
                    "state": DISCOVERY_FAILED,
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": clean,
                    "connection_ref": canonical_ref,
                    "query_invalid": clean,
                    "count": None,
                }

            # Parse "Number of work items in the search: N"
            m = re.search(r"Number of work items in the search:\s*(\d+)", combined)
            if m:
                return {
                    "state": DISCOVERY_READY,
                    "error_code": None,
                    "error_detail": None,
                    "connection_ref": canonical_ref,
                    "count": int(m.group(1)),
                }

            return {
                "state": DISCOVERY_FAILED,
                "error_code": CODE_QUERY_INVALID,
                "error_detail": f"Could not parse count output: {combined[:200]}",
                "connection_ref": canonical_ref,
                "count": None,
            }

        return self._with_account(principal, connection_ref_str, _run)

    # ── Validate scope (the validate_repo twin) ─────────────────────

    def validate_scope(
        self,
        principal: Principal,
        connection_ref_str: str,
        project_key: str,
    ) -> dict[str, Any]:
        """ONE bounded read proving project existence + access.

        ``acli jira project view --key K --json``.  The enumerated issue
        types ride along so the face needs no second call.
        """
        site, email = _parse_connection_ref(connection_ref_str)
        canonical_ref = connection_ref(site, email)

        def _run(s: str, e: str) -> dict[str, Any]:
            command = [
                "acli", "jira", "project", "view",
                "--key", project_key, "--json",
            ]
            try:
                completed = self._run_acli(command, principal, timeout=15.0)
            except Exception as exc:
                return {
                    "valid": False,
                    "project": None,
                    "issue_types": [],
                    "error_code": CODE_UNAVAILABLE,
                    "error_detail": str(exc)[:500],
                    "connection_ref": canonical_ref,
                }

            if completed.returncode != 0:
                detail = ((completed.stderr or "") + "\n" + (completed.stdout or "")).strip()[:500]
                return {
                    "valid": False,
                    "project": None,
                    "issue_types": [],
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": detail,
                    "connection_ref": canonical_ref,
                }

            try:
                obj = json.loads(completed.stdout or "{}")
            except json.JSONDecodeError:
                return {
                    "valid": False,
                    "project": None,
                    "issue_types": [],
                    "error_code": CODE_QUERY_INVALID,
                    "error_detail": "acli returned invalid JSON",
                    "connection_ref": canonical_ref,
                }

            # Extract issue types
            raw_types = obj.get("issueTypes") or []
            issue_types: list[dict[str, Any]] = []
            for it in raw_types:
                if not isinstance(it, dict):
                    continue
                item: dict[str, Any] = {
                    "id": str(it.get("id", "")),
                    "name": it.get("name", ""),
                    "subtask": bool(it.get("subtask", False)),
                }
                if "hierarchyLevel" in it:
                    item["hierarchy_level"] = it["hierarchyLevel"]
                issue_types.append(item)

            return {
                "valid": True,
                "project": {
                    "key": obj.get("key", ""),
                    "name": obj.get("name", ""),
                    "type": obj.get("projectTypeKey", ""),
                    "style": obj.get("style", ""),
                },
                "issue_types": issue_types,
                "error_code": None,
                "error_detail": None,
                "connection_ref": canonical_ref,
            }

        return self._with_account(principal, connection_ref_str, _run)
