"""GitHubProviderAdapter -- the V0 gh CLI provider for Project Room Watches.

HS-161-01. Implements the SS11 provider adapter protocol subset P2a needs:
manifest, connection_status, discover, validate_repo, snapshot; and
(Betterment MCP M6) pr_get, one pull request.

THE KERNEL ANSWER: production gh calls reach the kernel through
``PermissionGate(github_cli.MANIFEST).run_read_subprocess()``, which validates
the principal (OWNER + READ right) and manifest permission (``shell:exec``)
before calling the injected runner (default: ``subprocess.run``).  This is the
SAME admitted path ``GitHubWatchSource`` (watch_sources.py:69) has used since
HS-11-04.  The effect fence classifies these call sites as "mandatory
authenticated owner read" in ``_MIGRATED_CALLS`` (test_kernel_effect_fence.py).
``run_read_subprocess`` is deliberately lighter than ``execute_subprocess``
(which routes through ``run_subprocess_operation`` for consequential-write
kernel receipts): read-only probes check principal + permission but do not
produce a full kernel operation record.  This adapter RIDES the existing path.
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

from holdspeak.db.automations import redact_source_error
from holdspeak.connector_packs import github_cli
from holdspeak.connector_runtime import PermissionGate
from holdspeak.kernel.subprocess_exec import LOCAL_OWNER
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError

_log = logging.getLogger(__name__)

Runner = Callable[..., subprocess.CompletedProcess[str]]

PROVIDER_ID = "github"
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

# PROV-009 typed error codes
CODE_UNAVAILABLE = "unavailable"
CODE_AUTH_REQUIRED = "authentication_required"
CODE_CAPABILITY_MISSING = "capability_missing"
CODE_SCOPE_DENIED = "scope_denied"
CODE_RATE_LIMITED = "rate_limited"
CODE_QUERY_INVALID = "query_invalid"

# Connection states (SRS SS6)
STATE_CONNECTED = "connected"
STATE_DISCONNECTED = "disconnected"
STATE_OWNER_ACTION_REQUIRED = "owner_action_required"
STATE_UNAVAILABLE = "unavailable"
STATE_DEGRADED = "degraded"

# Discovery states (SRS SS6)
DISCOVERY_UNKNOWN = "unknown"
DISCOVERY_READY = "ready"
DISCOVERY_PARTIAL = "partial"
DISCOVERY_FAILED = "failed"


def _parse_gh_auth_login(output: str) -> str:
    """Extract the authenticated account login from gh auth status output.

    Handles multiple gh CLI output variants:
      - "Logged in to github.com account USERNAME (keyring)"
      - "Logged in to github.com as USERNAME"
    """
    for pattern in (
        r"[Ll]ogged\s+in\s+to\s+\S+\s+account\s+(\S+)",
        r"[Ll]ogged\s+in\s+to\s+\S+\s+as\s+(\S+)",
    ):
        match = re.search(pattern, output)
        if match:
            return match.group(1).strip("()")
    return ""


def _repo_id(row: dict[str, Any]) -> str:
    """Build the stable owner/name ID from a gh repo list JSON row."""
    owner = row.get("owner", {})
    login = owner.get("login", "") if isinstance(owner, dict) else str(owner)
    name = row.get("name", "")
    if login and name:
        return f"{login}/{name}"
    return ""


class GitHubProviderAdapter:
    """V0 GitHub CLI provider adapter (SS11 protocol subset).

    Takes the same ``runner`` seam as ``GitHubWatchSource``: tests inject a
    fake; production defaults to ``subprocess.run`` via the admitted
    ``PermissionGate.run_read_subprocess`` path.
    """

    def __init__(
        self,
        *,
        db: Any = None,
        runner: Runner | None = None,
    ) -> None:
        self._db = db
        self._runner = runner

    # ── Manifest (PROV-001, PROV-007) ────────────────────────────────

    def manifest(self) -> dict[str, Any]:
        """Versioned capability manifest. The hash changes iff capabilities do."""
        return {
            "provider_id": PROVIDER_ID,
            "transport": TRANSPORT,
            "capabilities": dict(_CAPABILITIES),
            "version": _CAPABILITY_HASH,
            "revision": _CAPABILITY_REVISION,
        }

    # ── Admitted subprocess seam ─────────────────────────────────────

    def _run_gh(
        self,
        command: list[str],
        principal: Principal,
        *,
        timeout: float = github_cli.DEFAULT_TIMEOUT_SECONDS,
    ) -> subprocess.CompletedProcess[str]:
        """Single admitted subprocess entry point for all gh CLI calls.

        Routes through ``PermissionGate.run_read_subprocess`` -- the same
        kernel-admitted path that ``GitHubWatchSource.snapshot`` uses
        (watch_sources.py:69).  The effect fence classifies this call site
        as "mandatory authenticated owner read".
        """
        return PermissionGate(github_cli.MANIFEST).run_read_subprocess(
            command,
            principal=principal,
            runner=self._runner,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
        )

    # ── Readiness (cheap, no probe) ────────────────────────────────

    def readiness(self, principal: Principal) -> dict[str, Any]:
        """Provider-level readiness from persisted row + which only.

        NEVER runs ``gh`` -- reads the DB row written by
        ``connection_status``.  One-liner parity with
        ``JiraProviderAdapter.readiness``.
        """
        if self._runner is None and shutil.which("gh") is None:
            return {"state": "unavailable", "connections": 0, "connected": 0}
        if self._db is None:
            return {"state": "partial", "connections": 0, "connected": 0}
        row = self._db.automations.get_provider_connection(self._connection_id())
        if row and row.get("state") == STATE_CONNECTED:
            return {"state": "connected", "connections": 1, "connected": 1}
        return {"state": "partial", "connections": 1 if row else 0, "connected": 0}

    def stored_status(self, principal: Principal) -> dict[str, Any] | None:
        """The last probe's stored result, or ``None`` if never checked.

        PHILO-9-02 B1: the cached read behind ``connection.list``.  NEVER
        runs ``gh``: it reads the row ``connection_status`` persisted.  The
        binary-presence check is ``shutil.which`` (a local PATH lookup, no
        subprocess), the same fast path ``connection_status`` takes.
        """
        row = (
            self._db.automations.get_provider_connection(self._connection_id())
            if self._db is not None else None
        )
        checked_at = (row or {}).get("last_checked_at") or None
        # PHILO-9-02 B1 (Codex Astra r1 finding 7): a stored check answers
        # with the state that check stored; only a never-checked row reads
        # the local binary check (no subprocess either way).
        if not (row and checked_at) and self._runner is None and shutil.which("gh") is None:
            return {
                "state": STATE_UNAVAILABLE,
                "error_code": CODE_UNAVAILABLE,
                "error_detail": "GitHub CLI (gh) is not installed",
                "display": {},
                "last_checked_at": checked_at,
            }
        if not row or not checked_at:
            return None
        state = str(row.get("state") or "")
        return {
            "state": state,
            "error_code": row.get("last_error_code") or None,
            "error_detail": row.get("last_error_detail") or None,
            "display": (
                {"recovery_hint": "gh auth login"}
                if state == STATE_OWNER_ACTION_REQUIRED
                else {"account": row.get("external_connection_ref")}
                if state == STATE_CONNECTED and row.get("external_connection_ref") else {}
            ),
            "last_checked_at": checked_at,
        }

    # ── Connection status (PROV-003, PROV-004) ───────────────────────

    def _connection_id(self) -> str:
        return f"wpc_{PROVIDER_ID}"

    def connection_status(self, principal: Principal, *, hostname: str | None = None) -> dict[str, Any]:
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

    # ── Discovery (PROV-006) ─────────────────────────────────────────

    def discover(
        self,
        principal: Principal,
        *,
        query: str | None = None,
        cursor: int | None = None,
        limit: int = 30,
    ) -> dict[str, Any]:
        """Enumerate accessible repositories via ``gh repo list``.

        Bounded, paginated (offset cursor), stable-ID'd (owner/name).
        Partial/error pages degrade typed, never crash.
        """
        capped_limit = max(1, min(int(limit), 100))
        offset = max(0, int(cursor or 0))
        fetch_count = offset + capped_limit

        command = [
            "gh", "repo", "list",
            "--json", "name,owner,visibility",
            "--limit", str(fetch_count),
        ]

        try:
            completed = self._run_gh(command, principal, timeout=15.0)
        except Exception as exc:
            return {
                "state": DISCOVERY_FAILED,
                "error_code": CODE_UNAVAILABLE,
                "error_detail": redact_source_error(exc)[:500],
                "items": [],
                "cursor": None,
            }

        if completed.returncode != 0:
            detail = redact_source_error(completed.stderr or "").strip()[:500]
            error_code = _classify_gh_error(detail)
            return {
                "state": DISCOVERY_FAILED,
                "error_code": error_code,
                "error_detail": detail,
                "items": [],
                "cursor": None,
            }

        try:
            rows = json.loads(completed.stdout or "[]")
        except json.JSONDecodeError:
            return {
                "state": DISCOVERY_FAILED,
                "error_code": CODE_QUERY_INVALID,
                "error_detail": "GitHub CLI returned invalid JSON",
                "items": [],
                "cursor": None,
            }

        if not isinstance(rows, list):
            return {
                "state": DISCOVERY_FAILED,
                "error_code": CODE_QUERY_INVALID,
                "error_detail": "GitHub CLI returned non-array",
                "items": [],
                "cursor": None,
            }

        # Offset-based cursor over the fetched result
        paged = rows[offset:]

        # Client-side search filter
        if query:
            q_lower = query.lower()
            paged = [r for r in paged if isinstance(r, dict) and q_lower in _repo_id(r).lower()]

        items: list[dict[str, Any]] = []
        for row in paged[:capped_limit]:
            if not isinstance(row, dict):
                continue
            rid = _repo_id(row)
            if rid:
                items.append({
                    "id": rid,
                    "name": row.get("name", ""),
                    "visibility": row.get("visibility", ""),
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
            "items": items,
            "cursor": next_cursor,
        }

    # ── Typed repo fallback (SS8.1) ──────────────────────────────────

    def validate_repo(
        self, principal: Principal, owner_repo: str,
    ) -> dict[str, Any]:
        """ONE bounded real read proving repository existence + access."""
        clean = owner_repo.strip()
        if "/" not in clean or clean.startswith("/") or clean.endswith("/"):
            return {
                "valid": False,
                "error_code": CODE_QUERY_INVALID,
                "error_detail": "Repository must be owner/name",
            }

        command = [
            "gh", "pr", "list",
            "-R", clean,
            "--limit", "1",
            "--json", "number",
        ]

        try:
            completed = self._run_gh(command, principal, timeout=10.0)
        except Exception as exc:
            return {
                "valid": False,
                "error_code": CODE_UNAVAILABLE,
                "error_detail": redact_source_error(exc)[:500],
            }

        if completed.returncode == 0:
            return {"valid": True, "error_code": None, "error_detail": None}

        detail = redact_source_error(completed.stderr or "").strip()[:500]
        error_code = _classify_gh_error(detail)
        if "not found" in detail.lower() or "404" in detail:
            error_code = CODE_SCOPE_DENIED
        return {
            "valid": False,
            "error_code": error_code,
            "error_detail": detail or f"Repository validation failed: {clean}",
        }

    # ── One pull request (MCP M6) ────────────────────────────────────

    def pr_get(
        self, principal: Principal, *, owner_repo: str = "", number: int | None = None, url: str = "",
    ) -> dict[str, Any]:
        """ONE bounded read of a pull request: what it is, its files and the
        reviews it asks for (``gh pr view --json``).

        The review starter's agent reads the PR it is about (Betterment MCP
        M6). A provider read is work for every caller the MCP gate admitted
        (``mcp/tool_authority.py``: reads of his connected providers post
        nothing of his), and ``gh`` runs under his own sign-in, so an agent's
        read runs as his local read. Nothing is written."""
        repo, pr_number = _pr_target(owner_repo=owner_repo, number=number, url=url)
        command = [
            "gh", "pr", "view", str(pr_number),
            "-R", repo,
            "--json", PR_VIEW_FIELDS,
        ]
        reader = principal if principal.kind is PrincipalKind.OWNER else LOCAL_OWNER
        try:
            completed = self._run_gh(command, reader, timeout=15.0)
        except Exception as exc:
            raise ServiceError(
                CODE_UNAVAILABLE, f"GitHub could not be read: {redact_source_error(exc)[:300]}",
                context={"status": 503},
            ) from exc
        if completed.returncode != 0:
            detail = redact_source_error(completed.stderr or "").strip()[:500]
            code = _classify_gh_error(detail)
            if "could not resolve" in detail.lower():  # gh's words for no such PR or repo
                code = CODE_SCOPE_DENIED
            raise ServiceError(
                code, detail or f"Pull request {repo}#{pr_number} could not be read",
                context={"status": 404 if code == CODE_SCOPE_DENIED else 503},
            )
        try:
            row = json.loads(completed.stdout or "{}")
        except ValueError as exc:
            raise ServiceError(CODE_UNAVAILABLE, "gh answered something that is not JSON",
                               context={"status": 502}) from exc
        return pr_from_gh(row, repo)

    # ── Snapshot (delegates to existing GitHubWatchSource) ────────────

    def snapshot(
        self, principal: Principal, spec: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """DELEGATE to the existing GitHubWatchSource -- zero forked logic."""
        from holdspeak.services.watch_sources import fetch_watch_snapshot

        return fetch_watch_snapshot(
            principal,
            connector_id="gh",
            query_kind=spec.get("query_kind", "pull_requests"),
            query=spec.get("query", {}),
            github_runner=self._runner,
        )


# ── Module-level helpers ─────────────────────────────────────────────

#: The fields ``pr_get`` asks ``gh pr view --json`` for.
PR_VIEW_FIELDS = (
    "number,title,body,url,state,isDraft,author,baseRefName,headRefName,"
    "additions,deletions,changedFiles,files,reviewRequests"
)
#: A PR body longer than this is cut (the agent reads the files for the rest).
PR_BODY_LIMIT = 8000
_PR_URL = re.compile(r"github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)")


def _pr_target(*, owner_repo: str, number: int | None, url: str) -> tuple[str, int]:
    """``(owner/name, number)`` from a PR URL, or from the repository and number."""
    from holdspeak.services.errors import ValidationError

    found = _PR_URL.search(str(url or ""))
    if found:
        return found.group(1), int(found.group(2))
    repo = str(owner_repo or "").strip()
    if "/" not in repo or repo.startswith("/") or repo.endswith("/") or not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        raise ValidationError("Name the pull request: its URL, or owner_repo (owner/name) and number")
    try:
        pr_number = int(number) if number is not None else 0
    except (TypeError, ValueError):
        pr_number = 0
    if pr_number < 1:
        raise ValidationError("number must be the pull request's number (1 or more)")
    return repo, pr_number


def _review_request_name(request: Any) -> str:
    if not isinstance(request, dict):
        return ""
    return str(request.get("login") or request.get("slug") or request.get("name") or "")


def pr_from_gh(row: dict[str, Any], repo: str) -> dict[str, Any]:
    """The ``provider.github_pr_get`` answer from one ``gh pr view --json`` row."""
    body = str(row.get("body") or "")
    files = [
        {"path": str(f.get("path") or ""), "additions": int(f.get("additions") or 0),
         "deletions": int(f.get("deletions") or 0)}
        for f in row.get("files") or [] if isinstance(f, dict) and f.get("path")
    ]
    author = row.get("author") if isinstance(row.get("author"), dict) else {}
    return {
        "repository": repo,
        "number": int(row.get("number") or 0),
        "title": str(row.get("title") or ""),
        "url": str(row.get("url") or ""),
        "state": str(row.get("state") or "").lower(),
        "draft": bool(row.get("isDraft")),
        "author": str(author.get("login") or ""),
        "base": str(row.get("baseRefName") or ""),
        "head": str(row.get("headRefName") or ""),
        "body": body[:PR_BODY_LIMIT],
        "body_cut": len(body) > PR_BODY_LIMIT,
        "changed_files": int(row.get("changedFiles") or len(files)),
        "additions": int(row.get("additions") or 0),
        "deletions": int(row.get("deletions") or 0),
        "files": files,
        "review_requests": [n for n in (_review_request_name(r) for r in row.get("reviewRequests") or []) if n],
    }


def _is_unauthenticated(text: str) -> bool:
    """Detect the unauthenticated state from gh auth status output."""
    lower = text.lower()
    return "not logged in" in lower or (
        "authentication" in lower and "failed" not in lower
    )


def _classify_gh_error(detail: str) -> str:
    """Map a gh stderr snippet to a PROV-009 typed code."""
    lower = detail.lower()
    if "not logged in" in lower or "authentication" in lower:
        return CODE_AUTH_REQUIRED
    if "not found" in lower or "404" in lower:
        return CODE_SCOPE_DENIED
    if "rate limit" in lower or "403" in lower:
        return CODE_RATE_LIMITED
    if "scope" in lower or "permission" in lower:
        return CODE_SCOPE_DENIED
    return CODE_UNAVAILABLE
