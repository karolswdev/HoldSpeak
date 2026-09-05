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
    if state == DISPLAY_NOT_CONFIGURED:
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
    ) -> None:
        self._github = github_adapter
        self._jira = jira_adapter
        self._confluence = confluence_adapter
        self._config_loader = config_loader
        self._inference_assignment = inference_assignment_service

    # ── Public API ────────────────────────────────────────────────────

    def list_tools(self, principal: Principal) -> dict[str, Any]:
        """Return ``{"tools": [...]}``: one entry per known tool."""
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
        """Recheck a provider and return its refreshed tool entry."""
        if provider_id == "github":
            return self._recheck_github(principal)
        if provider_id == "jira":
            return self._recheck_jira(principal, ref=ref)
        if provider_id == "confluence":
            return self._confluence_entry(principal)
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
            "egress_host": None,
        }

    # ── GitHub ────────────────────────────────────────────────────────

    def _github_entry(self, principal: Principal) -> dict[str, Any]:
        if self._github is None:
            return self._not_configured_entry("github")

        status = self._github.connection_status(principal)
        wire_state = status.get("state", "")
        display_state = _map_github_state(wire_state)

        login = status.get("display", {}).get("account")
        account: dict[str, Any] | None = {"login": login} if login else None

        recovery_hint = status.get("display", {}).get("recovery_hint")
        if not recovery_hint and display_state == DISPLAY_UNAVAILABLE:
            recovery_hint = status.get("error_detail")

        return {
            "provider_id": "github",
            "state": display_state,
            "account": account,
            "next_action": _next_action_for_state(display_state, "github"),
            "recovery_hint": recovery_hint,
            "error_detail": status.get("error_detail") if display_state not in (DISPLAY_CONNECTED,) else None,
            "last_checked_at": datetime.now(timezone.utc).isoformat(),
            "egress_host": "github.com",
        }

    def _recheck_github(self, principal: Principal) -> dict[str, Any]:
        """Re-probe GitHub and return the refreshed entry."""
        return self._github_entry(principal)

    # ── Jira ──────────────────────────────────────────────────────────

    def _jira_entry(self, principal: Principal) -> dict[str, Any]:
        if self._jira is None:
            return self._not_configured_entry("jira")

        connections = self._jira.list_connections(principal)

        if not connections:
            # Zero connections: check if acli is installed
            import shutil

            if shutil.which("acli") is None:
                return {
                    "provider_id": "jira",
                    "state": DISPLAY_UNAVAILABLE,
                    "account": None,
                    "next_action": {"kind": "install", "label": "Install"},
                    "recovery_hint": "pip install acli",
                    "error_detail": "Atlassian CLI (acli) is not installed",
                    "last_checked_at": datetime.now(timezone.utc).isoformat(),
                    "egress_host": None,
                    "connections": [],
                }
            return {
                "provider_id": "jira",
                "state": DISPLAY_OWNER_ACTION_REQUIRED,
                "account": None,
                "next_action": {"kind": "add_account", "label": "Add account"},
                "recovery_hint": "acli jira auth login --site <site> --email <email> --token",
                "error_detail": None,
                "last_checked_at": datetime.now(timezone.utc).isoformat(),
                "egress_host": None,
                "connections": [],
            }

        # Build per-connection entries
        conn_entries: list[dict[str, Any]] = []
        best_state = DISPLAY_OWNER_ACTION_REQUIRED
        best_account: dict[str, Any] | None = None
        best_recovery: str | None = None
        best_error: str | None = None
        best_egress: str | None = None

        for c in connections:
            wire_state = c.get("state", "")
            display = _map_jira_state(wire_state)
            ref = c.get("external_connection_ref", c.get("connection_ref", ""))
            site, email = "", ""
            if "|" in ref:
                parts = ref.split("|", 1)
                site, email = parts[0], parts[1]

            # Normalize recovery_hint from Jira's recovery.command
            recovery = None
            if display == DISPLAY_OWNER_ACTION_REQUIRED:
                recovery = f"acli jira auth login --site {site} --email {email} --token"

            conn_entry = {
                "connection_ref": ref,
                "state": display,
                "account": {"site": site, "email": email},
                "recovery_hint": recovery,
            }
            conn_entries.append(conn_entry)

            # Track the best (most-connected) state for the aggregate
            if display == DISPLAY_CONNECTED:
                best_state = DISPLAY_CONNECTED
                if best_account is None:
                    best_account = {"site": site, "email": email}
                best_egress = site
            elif display == DISPLAY_OWNER_ACTION_REQUIRED and best_state != DISPLAY_CONNECTED:
                best_state = DISPLAY_OWNER_ACTION_REQUIRED
                if best_recovery is None:
                    best_recovery = recovery
            elif display == DISPLAY_DEGRADED and best_state not in (DISPLAY_CONNECTED, DISPLAY_OWNER_ACTION_REQUIRED):
                best_state = DISPLAY_DEGRADED
                best_error = c.get("last_error_detail", c.get("error_detail"))

        # Summary: use first connected, else first with recovery
        if best_account is None and conn_entries:
            first = conn_entries[0]
            best_account = first["account"]
            best_recovery = first.get("recovery_hint")

        return {
            "provider_id": "jira",
            "state": best_state,
            "account": best_account,
            "next_action": _next_action_for_state(best_state, "jira"),
            "recovery_hint": best_recovery,
            "error_detail": best_error,
            "last_checked_at": datetime.now(timezone.utc).isoformat(),
            "egress_host": best_egress,
            "connections": conn_entries,
        }

    def _recheck_jira(
        self,
        principal: Principal,
        *,
        ref: str | None = None,
    ) -> dict[str, Any]:
        """Recheck Jira connections and return the refreshed entry.

        If ``ref`` is given, recheck THAT specific connection only.
        Otherwise recheck ALL connections.
        """
        if self._jira is None:
            return self._not_configured_entry("jira")

        if ref:
            # Recheck one specific connection
            self._jira.connection_status(principal, ref)
        else:
            # Recheck every connection
            connections = self._jira.list_connections(principal)
            for c in connections:
                c_ref = c.get("external_connection_ref", c.get("connection_ref", ""))
                if c_ref:
                    try:
                        self._jira.connection_status(principal, c_ref)
                    except Exception:
                        pass  # degraded: continue checking others

        return self._jira_entry(principal)

    # ── Confluence (HS-174-07) ──────────────────────────────────────────

    def _confluence_entry(self, principal: Principal) -> dict[str, Any]:
        """Build the Confluence tool entry from the adapter, mirroring Jira."""
        if self._confluence is None:
            return self._not_configured_entry("confluence")

        try:
            readiness = self._confluence.readiness(principal) if hasattr(self._confluence, "readiness") else {}
        except Exception:
            readiness = {}

        # readiness.connections is an int count; get the actual rows.
        try:
            connections = self._confluence.list_connections(principal) if hasattr(self._confluence, "list_connections") else []
        except Exception:
            connections = []
        if not connections:
            return {
                "provider_id": "confluence",
                "state": DISPLAY_NOT_CONFIGURED,
                "account": None,
                "next_action": {"kind": "setup", "label": "Set up"},
                "recovery_hint": "acli confluence auth login --site <site> --email <email> --token",
                "error_detail": None,
                "last_checked_at": readiness.get("checked_at"),
                "egress_host": None,
                "connections": [],
            }

        # Map each connection to a sub-row (same grammar as Jira)
        sub_rows: list[dict[str, Any]] = []
        overall_state = DISPLAY_NOT_CONFIGURED
        overall_egress = None
        for conn in connections:
            state = conn.get("state", "not_configured")
            display = _map_jira_state(state)  # reuse the Jira state mapper
            site = conn.get("site", "")
            email = conn.get("email", "")
            ref = conn.get("connection_ref", f"{site}|{email}")
            sub_rows.append({
                "connection_ref": ref,
                "state": display,
                "account": {"site": site, "email": email},
                "recovery_hint": conn.get("recovery_hint", f"acli confluence auth login --site {site} --email {email} --token"),
                "error_detail": conn.get("error_detail"),
                "egress_host": site,
            })
            if display == "connected":
                overall_state = "connected"
                overall_egress = site

        first = connections[0] if connections else {}
        return {
            "provider_id": "confluence",
            "state": overall_state,
            "account": {"site": first.get("site", ""), "email": first.get("email", "")},
            "next_action": None,
            "recovery_hint": None,
            "error_detail": None,
            "last_checked_at": readiness.get("checked_at"),
            "egress_host": overall_egress,
            "connections": sub_rows,
        }

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

        return {
            "provider_id": "models",
            "state": DISPLAY_CONNECTED if assigned > 0 else DISPLAY_NOT_CONFIGURED,
            "account": {"assigned": assigned, "total": total},
            "next_action": {"kind": "open_module", "label": "Open Models"},
            "recovery_hint": None,
            "error_detail": None,
            "last_checked_at": None,
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
            "egress_host": None,
        }
