"""HS-168-02: ConnectionsService -- ONE readiness shape over existing adapters.

The faces and MCP twins READ this shape; NO face ever derives "connected"
on its own.  The service delegates to the existing adapters (GitHub, Jira,
calendar config, inference assignments) and normalizes their answers into
a single ``tool entry`` shape per D6.

No new authority: the adapters store state; this service only projects.
No credential ever crosses the response (Article III).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from holdspeak.principals import Principal
from holdspeak.services.github_provider import (
    STATE_CONNECTED as GH_CONNECTED,
    STATE_DEGRADED as GH_DEGRADED,
    STATE_DISCONNECTED as GH_DISCONNECTED,
    STATE_OWNER_ACTION_REQUIRED as GH_OWNER_ACTION,
    STATE_UNAVAILABLE as GH_UNAVAILABLE,
)
from holdspeak.services.jira_provider import (
    STATE_CONNECTED as JIRA_CONNECTED,
    STATE_DEGRADED as JIRA_DEGRADED,
    STATE_DISCONNECTED as JIRA_DISCONNECTED,
    STATE_OWNER_ACTION_REQUIRED as JIRA_OWNER_ACTION,
    STATE_UNAVAILABLE as JIRA_UNAVAILABLE,
)


# ── The five display states the face reads (D6 mapping) ──────────────
# Wire constants from both adapters are mapped into these.

DISPLAY_CONNECTED = "connected"
DISPLAY_OWNER_ACTION_REQUIRED = "owner_action_required"
DISPLAY_UNAVAILABLE = "unavailable"
DISPLAY_DEGRADED = "degraded"
DISPLAY_NOT_CONFIGURED = "not_configured"
# PHILO-9-02 B1: a remote row no probe has checked yet (no stored time).
DISPLAY_NEVER_CHECKED = "never_checked"
# PHILO-15 B31: no probe stored yet, but gh's own sign-in file names an
# active login.  The first-run card and Settings › Connections both read this
# one entry, so they say the same thing at the same time.
DISPLAY_SIGNED_IN = "signed_in"

# Map from adapter wire states to the display states (D6).
# disconnected AND owner_action_required both carry a recovery hint;
# the fold opens for both.
_GITHUB_STATE_MAP: dict[str, str] = {
    GH_CONNECTED: DISPLAY_CONNECTED,
    GH_DISCONNECTED: DISPLAY_OWNER_ACTION_REQUIRED,
    GH_OWNER_ACTION: DISPLAY_OWNER_ACTION_REQUIRED,
    GH_UNAVAILABLE: DISPLAY_UNAVAILABLE,
    GH_DEGRADED: DISPLAY_DEGRADED,
}

_JIRA_STATE_MAP: dict[str, str] = {
    JIRA_CONNECTED: DISPLAY_CONNECTED,
    JIRA_DISCONNECTED: DISPLAY_OWNER_ACTION_REQUIRED,
    JIRA_OWNER_ACTION: DISPLAY_OWNER_ACTION_REQUIRED,
    JIRA_UNAVAILABLE: DISPLAY_UNAVAILABLE,
    JIRA_DEGRADED: DISPLAY_DEGRADED,
}


def _map_github_state(wire_state: str) -> str:
    return _GITHUB_STATE_MAP.get(wire_state, DISPLAY_DEGRADED)


def _map_jira_state(wire_state: str) -> str:
    return _JIRA_STATE_MAP.get(wire_state, DISPLAY_DEGRADED)


def _age_seconds(checked_at: str | None) -> int | None:
    """Whole seconds since a stored ISO check time (``None`` when unknown)."""
    if not checked_at:
        return None
    try:
        then = datetime.fromisoformat(str(checked_at))
    except ValueError:
        return None
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    return max(0, int((datetime.now(timezone.utc) - then).total_seconds()))


def _split_ref(ref: str) -> tuple[str, str]:
    if "|" in ref:
        site, email = ref.split("|", 1)
        return site, email
    return "", ""


# Aggregate order for a provider with several rows: the best row names the card.
_SUMMARY_ORDER = (
    DISPLAY_CONNECTED,
    DISPLAY_SIGNED_IN,
    DISPLAY_OWNER_ACTION_REQUIRED,
    DISPLAY_DEGRADED,
    DISPLAY_UNAVAILABLE,
    DISPLAY_NEVER_CHECKED,
)


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """One provider summary from its per-row entries (all stored reads)."""
    best = min(
        rows,
        key=lambda r: _SUMMARY_ORDER.index(r["state"]) if r["state"] in _SUMMARY_ORDER else len(_SUMMARY_ORDER),
    )
    times = [r["last_checked_at"] for r in rows if r.get("last_checked_at")]
    connected = [r for r in rows if r["state"] == DISPLAY_CONNECTED]
    return {
        "state": best["state"],
        "account": (connected[0] if connected else rows[0])["account"],
        "recovery_hint": None if connected else best.get("recovery_hint"),
        "error_detail": best.get("error_detail") if best["state"] == DISPLAY_DEGRADED else None,
        "last_checked_at": max(times) if times else None,
        "egress_host": connected[0]["egress_host"] if connected else None,
    }


def _next_action_for_state(
    state: str, provider_id: str,
) -> dict[str, str]:
    """Compute the next_action entry for a tool."""
    if state == DISPLAY_CONNECTED:
        return {"kind": "recheck", "label": "Recheck"}
    if state == DISPLAY_OWNER_ACTION_REQUIRED:
        if provider_id == "github":
            return {"kind": "sign_in", "label": "Sign in"}
        if provider_id == "jira":
            return {"kind": "add_account", "label": "Add account"}
        return {"kind": "sign_in", "label": "Sign in"}
    if state == DISPLAY_UNAVAILABLE:
        return {"kind": "install", "label": "Install"}
    if state in (DISPLAY_NOT_CONFIGURED, DISPLAY_NEVER_CHECKED, DISPLAY_SIGNED_IN):
        return {"kind": "recheck", "label": "Recheck"}
    # degraded
    return {"kind": "recheck", "label": "Recheck"}


class ConnectionsService:
    """ONE readiness projection over the existing adapters (D6).

    Takes the principal from the route; never stores new state.
    """

    def __init__(
        self,
        *,
        github_adapter: Any | None = None,
        jira_adapter: Any | None = None,
        confluence_adapter: Any | None = None,
        config_loader: Callable[[], Any] | None = None,
        inference_assignment_service: Any | None = None,
        gh_hosts_file: Callable[[], Any] | None = None,
    ) -> None:
        self._github = github_adapter
        # PHILO-15 B31: where gh keeps its sign-in file (a callable, read at
        # each list; tests inject a path).  Default: gh's own lookup order.
        self._gh_hosts_file = gh_hosts_file
        self._jira = jira_adapter
        self._confluence = confluence_adapter
        self._config_loader = config_loader
        self._inference_assignment = inference_assignment_service

    # ── Public API ────────────────────────────────────────────────────

    def list_tools(self, principal: Principal) -> dict[str, Any]:
        """Return ``{"tools": [...]}``: one entry per known tool.

        PHILO-9-02 B1: a cached read.  GitHub, Jira and Confluence return the
        state the last real probe stored, each row with its own
        ``last_checked_at`` and ``checked_age_seconds``; a row with no stored
        check is ``never_checked``.  No ``gh``/``acli``/network call happens
        here: the probe lives only in :meth:`recheck`.  Calendar and Models
        are live local reads with no check time.
        """
        tools: list[dict[str, Any]] = []
        tools.append(self._github_entry(principal))
        tools.append(self._jira_entry(principal))
        tools.append(self._confluence_entry(principal))
        tools.append(self._calendar_entry())
        tools.append(self._models_entry(principal))
        return {"tools": tools}

    def recheck(
        self,
        principal: Principal,
        provider_id: str,
        *,
        ref: str | None = None,
    ) -> dict[str, Any]:
        """Probe a provider (egress), store the result, return its cached entry."""
        if provider_id == "github":
            return self._recheck_github(principal, hostname=ref)
        if provider_id == "jira":
            return self._recheck_jira(principal, ref=ref)
        if provider_id == "confluence":
            return self._recheck_confluence(principal, ref=ref)
        if provider_id == "calendar":
            return self._calendar_entry()
        if provider_id == "models":
            return self._models_entry(principal)
        return {
            "provider_id": provider_id,
            "state": DISPLAY_NOT_CONFIGURED,
            "account": None,
            "next_action": {"kind": "recheck", "label": "Recheck"},
            "recovery_hint": None,
            "error_detail": f"Unknown provider: {provider_id}",
            "last_checked_at": None,
            "checked_age_seconds": None,
            "egress_host": None,
        }

    # ── GitHub ────────────────────────────────────────────────────────

    def _github_entry(self, principal: Principal) -> dict[str, Any]:
        """The stored GitHub state (no ``gh`` call)."""
        if self._github is None:
            return self._not_configured_entry("github")

        status = self._github.stored_status(principal)
        if status is None:
            signed_in = self._github_file_sign_in()
            if signed_in is not None:
                return signed_in
            return {
                "provider_id": "github",
                "state": DISPLAY_NEVER_CHECKED,
                "account": None,
                "next_action": _next_action_for_state(DISPLAY_NEVER_CHECKED, "github"),
                "recovery_hint": None,
                "error_detail": None,
                "last_checked_at": None,
                "checked_age_seconds": None,
                "egress_host": "github.com",
            }

        display_state = _map_github_state(status.get("state", ""))
        # The stored row keeps no login (the probe's account name is not a
        # column), so the cached read names no account.
        login = status.get("display", {}).get("account")
        account: dict[str, Any] | None = {"login": login} if login else None

        recovery_hint = status.get("display", {}).get("recovery_hint")
        if not recovery_hint and display_state == DISPLAY_UNAVAILABLE:
            recovery_hint = status.get("error_detail")

        checked_at = status.get("last_checked_at")
        return {
            "provider_id": "github",
            "state": display_state,
            "account": account,
            "next_action": _next_action_for_state(display_state, "github"),
            "recovery_hint": recovery_hint,
            "error_detail": status.get("error_detail") if display_state not in (DISPLAY_CONNECTED,) else None,
            "last_checked_at": checked_at,
            "checked_age_seconds": _age_seconds(checked_at),
            "egress_host": "github.com",
        }

    def _github_file_sign_in(self) -> dict[str, Any] | None:
        """PHILO-15 B31: the active login in gh's ``hosts.yml`` (a file read; no ``gh``, no network).

        The time is the file's own write time: when gh last stored a sign-in.
        github.com wins over other hosts, as the connector's egress host is
        github.com.
        """
        from .onboarding_service import _gh_account_ref, gh_hosts_path, read_gh_accounts

        try:
            path = self._gh_hosts_file() if self._gh_hosts_file is not None else gh_hosts_path()
        except Exception:
            return None
        if path is None:
            return None
        active = [row for row in read_gh_accounts(path) if row.get("active")]
        if not active:
            return None
        row = next((r for r in active if r["host"] == "github.com"), active[0])
        try:
            written = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        except OSError:
            written = None
        return {
            "provider_id": "github",
            "state": DISPLAY_SIGNED_IN,
            "account": {"login": _gh_account_ref(row["host"], row["login"])},
            "next_action": _next_action_for_state(DISPLAY_SIGNED_IN, "github"),
            "recovery_hint": None,
            "error_detail": None,
            "last_checked_at": written,
            "checked_age_seconds": _age_seconds(written),
            "checked_by": "gh_file",
            "egress_host": "github.com",
        }

    def _recheck_github(self, principal: Principal, *, hostname: str | None = None) -> dict[str, Any]:
        """Probe GitHub (``gh auth status``, one host when named; stored), return the cached entry."""
        if self._github is not None:
            if hostname:
                self._github.connection_status(principal, hostname=hostname)
            else:
                self._github.connection_status(principal)
        return self._github_entry(principal)

    # ── Jira ──────────────────────────────────────────────────────────

    def _jira_entry(self, principal: Principal) -> dict[str, Any]:
        """The stored Jira rows (no ``acli`` call)."""
        if self._jira is None:
            return self._not_configured_entry("jira")

        connections = self._jira.list_connections(principal)

        if not connections:
            # Zero connections.  ``shutil.which`` is a local PATH lookup
            # (no subprocess): the binary-missing hint stays.
            import shutil

            if shutil.which("acli") is None:
                return {
                    "provider_id": "jira",
                    "state": DISPLAY_UNAVAILABLE,
                    "account": None,
                    "next_action": {"kind": "install", "label": "Install"},
                    "recovery_hint": "pip install acli",
                    "error_detail": "Atlassian CLI (acli) is not installed",
                    "last_checked_at": None,
                    "checked_age_seconds": None,
                    "egress_host": None,
                    "connections": [],
                }
            return {
                "provider_id": "jira",
                "state": DISPLAY_NEVER_CHECKED,
                "account": None,
                "next_action": {"kind": "add_account", "label": "Add account"},
                "recovery_hint": "acli jira auth login --site <site> --email <email> --token",
                "error_detail": None,
                "last_checked_at": None,
                "checked_age_seconds": None,
                "egress_host": None,
                "connections": [],
            }

        conn_entries: list[dict[str, Any]] = []
        for c in connections:
            ref = c.get("external_connection_ref", c.get("connection_ref", ""))
            site, email = _split_ref(ref)
            checked_at = c.get("last_checked_at") or None
            display = _map_jira_state(c.get("state", "")) if checked_at else DISPLAY_NEVER_CHECKED
            recovery = None
            if display == DISPLAY_OWNER_ACTION_REQUIRED:
                recovery = f"acli jira auth login --site {site} --email {email} --token"
            conn_entries.append({
                "connection_ref": ref,
                "state": display,
                "account": {"site": site, "email": email},
                "recovery_hint": recovery,
                "error_detail": (c.get("last_error_detail") or None) if display == DISPLAY_DEGRADED else None,
                "last_checked_at": checked_at,
                "checked_age_seconds": _age_seconds(checked_at),
                "egress_host": site,
            })

        summary = _summarize(conn_entries)
        return {
            "provider_id": "jira",
            "state": summary["state"],
            "account": summary["account"],
            "next_action": _next_action_for_state(summary["state"], "jira"),
            "recovery_hint": summary["recovery_hint"],
            "error_detail": summary["error_detail"],
            "last_checked_at": summary["last_checked_at"],
            "checked_age_seconds": _age_seconds(summary["last_checked_at"]),
            "egress_host": summary["egress_host"],
            "connections": conn_entries,
        }

    def _recheck_jira(
        self,
        principal: Principal,
        *,
        ref: str | None = None,
    ) -> dict[str, Any]:
        """Probe Jira (one ref, or every stored row), return the cached entry."""
        if self._jira is None:
            return self._not_configured_entry("jira")
        self._probe_rows(self._jira, principal, ref)
        return self._jira_entry(principal)

    # ── Confluence (HS-174-07) ──────────────────────────────────────────

    def _confluence_entry(self, principal: Principal) -> dict[str, Any]:
        """The stored Confluence rows (no ``acli`` call), same grammar as Jira."""
        if self._confluence is None:
            return self._not_configured_entry("confluence")

        try:
            connections = self._confluence.list_connections(principal)
        except Exception:
            connections = []
        if not connections:
            return {
                "provider_id": "confluence",
                "state": DISPLAY_NEVER_CHECKED,
                "account": None,
                "next_action": {"kind": "setup", "label": "Set up"},
                "recovery_hint": "acli confluence auth login --site <site> --email <email> --token",
                "error_detail": None,
                "last_checked_at": None,
                "checked_age_seconds": None,
                "egress_host": None,
                "connections": [],
            }

        sub_rows: list[dict[str, Any]] = []
        for conn in connections:
            ext_ref = str(conn.get("external_connection_ref", ""))
            if "|" in ext_ref:
                site, email = _split_ref(ext_ref)
            else:
                site = conn.get("site", "")
                email = conn.get("email", "")
            ref = ext_ref or f"{site}|{email}"
            checked_at = conn.get("last_checked_at") or None
            display = _map_jira_state(conn.get("state", "")) if checked_at else DISPLAY_NEVER_CHECKED
            sub_rows.append({
                "connection_ref": ref,
                "state": display,
                "account": {"site": site, "email": email},
                "recovery_hint": f"acli confluence auth login --site {site} --email {email} --token",
                "error_detail": (conn.get("last_error_detail") or None) if display == DISPLAY_DEGRADED else None,
                "last_checked_at": checked_at,
                "checked_age_seconds": _age_seconds(checked_at),
                "egress_host": site,
            })

        summary = _summarize(sub_rows)
        return {
            "provider_id": "confluence",
            "state": summary["state"],
            "account": summary["account"],
            "next_action": None,
            "recovery_hint": None,
            "error_detail": None,
            "last_checked_at": summary["last_checked_at"],
            "checked_age_seconds": _age_seconds(summary["last_checked_at"]),
            "egress_host": summary["egress_host"],
            "connections": sub_rows,
        }

    def _recheck_confluence(
        self,
        principal: Principal,
        *,
        ref: str | None = None,
    ) -> dict[str, Any]:
        """Probe Confluence (one ref, or every stored row), return the cached entry.

        ``connection_status`` runs ``acli confluence auth switch`` + ``status``
        under the shared acli lock and stores the state and time.
        """
        if self._confluence is None:
            return self._not_configured_entry("confluence")
        self._probe_rows(self._confluence, principal, ref)
        return self._confluence_entry(principal)

    @staticmethod
    def _probe_rows(adapter: Any, principal: Principal, ref: str | None) -> None:
        """Probe one ref, or every stored row (a failure degrades, the rest run)."""
        if ref:
            adapter.connection_status(principal, ref)
            return
        for c in adapter.list_connections(principal):
            c_ref = c.get("external_connection_ref", c.get("connection_ref", ""))
            if c_ref:
                try:
                    adapter.connection_status(principal, c_ref)
                except Exception:
                    pass  # degraded: continue checking others

    # ── Calendar ──────────────────────────────────────────────────────

    def _calendar_entry(self) -> dict[str, Any]:
        configured = False
        source_count = 0
        if self._config_loader is not None:
            try:
                from holdspeak.config.integrations import validate_calendar_subscription

                config = self._config_loader()
                for source in config.calendar.sources:
                    if source.enabled and validate_calendar_subscription(source.url):
                        source_count += 1
                configured = source_count > 0
            except Exception:
                pass

        if configured:
            return {
                "provider_id": "calendar",
                "state": DISPLAY_CONNECTED,
                "account": {"sources": source_count},
                "next_action": {"kind": "open_module", "label": "Sources"},
                "recovery_hint": None,
                "error_detail": None,
                "last_checked_at": None,
                "checked_age_seconds": None,
                "egress_host": None,
            }
        return {
            "provider_id": "calendar",
            "state": DISPLAY_NOT_CONFIGURED,
            "account": None,
            "next_action": {"kind": "open_module", "label": "Set up"},
            "recovery_hint": None,
            "error_detail": None,
            "last_checked_at": None,
            "checked_age_seconds": None,
            "egress_host": None,
        }

    # ── Models ────────────────────────────────────────────────────────

    def _models_entry(self, principal: Principal) -> dict[str, Any]:
        assigned = 0
        total = 7  # The bounded seven-row roster
        if self._inference_assignment is not None:
            try:
                summary = self._inference_assignment.assignment_summary(principal)
                # assignment_summary returns:
                #   {"schema": "...", "rows": [...], "task_overrides": [...], ...}
                # The 7 rows are the bounded owner roster (1 global + 6 groups).
                rows = summary.get("rows", [])
                total = len(rows)
                assigned = sum(1 for r in rows if r.get("status") == "assigned")
            except Exception:
                pass
        # PHILO-15 B33: a summary route through the default (or a capability
        # pick) runs on an engine even with no group row "assigned"; the row
        # said Unassigned while summaries ran on the LAN box.
        summary_host: str | None = None
        try:
            from ..db import get_database
            from .meeting_route_projection import summary_engine_fact

            fact = summary_engine_fact(get_database())
            if fact.get("engine_set"):
                summary_host = str(fact.get("host") or "") or None
        except Exception:
            pass

        return {
            "provider_id": "models",
            "state": DISPLAY_CONNECTED if (assigned > 0 or summary_host) else DISPLAY_NOT_CONFIGURED,
            "account": {"assigned": assigned, "total": total, "summary_host": summary_host},
            "next_action": {"kind": "open_module", "label": "Open Models"},
            "recovery_hint": None,
            "error_detail": None,
            "last_checked_at": None,
            "checked_age_seconds": None,
            "egress_host": None,
        }

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _not_configured_entry(provider_id: str) -> dict[str, Any]:
        return {
            "provider_id": provider_id,
            "state": DISPLAY_NOT_CONFIGURED,
            "account": None,
            "next_action": {"kind": "recheck", "label": "Recheck"},
            "recovery_hint": None,
            "error_detail": None,
            "last_checked_at": None,
            "checked_age_seconds": None,
            "egress_host": None,
        }
