"""HS-168-02: ConnectionsService -- ONE readiness shape from DRIVEN adapters.

Tests the four+one display states, the Jira ledger with 0/1/2 connections,
the calendar flag, models summary, recovery_hint normalization, and recheck
delegation.  Monkeypatches the adapter's probe/subprocess, never hand-seeds
connections rows (the 163 phantom-fixture law).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.connections_service import (
    ConnectionsService,
    DISPLAY_CONNECTED,
    DISPLAY_DEGRADED,
    DISPLAY_NOT_CONFIGURED,
    DISPLAY_OWNER_ACTION_REQUIRED,
    DISPLAY_UNAVAILABLE,
)

OWNER = Principal(PrincipalKind.OWNER, "test-conn-owner")


# ── Fake adapters ───────────────────────────────────────────────────


def _gh_adapter(state: str, **extra: Any) -> MagicMock:
    """Build a fake GitHub adapter that returns a fixed connection_status."""
    adapter = MagicMock()
    result: dict[str, Any] = {"state": state, "display": {}, **extra}
    adapter.connection_status.return_value = result
    return adapter


def _jira_adapter(
    connections: list[dict[str, Any]] | None = None,
) -> MagicMock:
    """Build a fake Jira adapter with fixed list_connections / connection_status."""
    adapter = MagicMock()
    adapter.list_connections.return_value = connections or []

    def _conn_status(principal: Any, ref: str, **kw: Any) -> dict[str, Any]:
        for c in connections or []:
            c_ref = c.get("external_connection_ref", c.get("connection_ref", ""))
            if c_ref == ref:
                return c
        return {"state": "disconnected"}

    adapter.connection_status.side_effect = _conn_status
    return adapter


# ── GitHub state mapping ─────────────────────────────────────────────


class TestGitHubStates:
    def test_connected(self) -> None:
        gh = _gh_adapter("connected", display={"account": "karolswdev"})
        svc = ConnectionsService(github_adapter=gh)
        result = svc.list_tools(OWNER)
        gh_tool = next(t for t in result["tools"] if t["provider_id"] == "github")
        assert gh_tool["state"] == DISPLAY_CONNECTED
        assert gh_tool["account"] == {"login": "karolswdev"}
        assert gh_tool["egress_host"] == "github.com"

    def test_disconnected_maps_to_owner_action_required(self) -> None:
        gh = _gh_adapter("disconnected", display={"recovery_hint": "gh auth login"})
        svc = ConnectionsService(github_adapter=gh)
        result = svc.list_tools(OWNER)
        gh_tool = next(t for t in result["tools"] if t["provider_id"] == "github")
        assert gh_tool["state"] == DISPLAY_OWNER_ACTION_REQUIRED
        assert gh_tool["recovery_hint"] == "gh auth login"

    def test_owner_action_required_maps_directly(self) -> None:
        gh = _gh_adapter("owner_action_required", display={"recovery_hint": "gh auth login"})
        svc = ConnectionsService(github_adapter=gh)
        result = svc.list_tools(OWNER)
        gh_tool = next(t for t in result["tools"] if t["provider_id"] == "github")
        assert gh_tool["state"] == DISPLAY_OWNER_ACTION_REQUIRED

    def test_unavailable(self) -> None:
        gh = _gh_adapter("unavailable", error_detail="GitHub CLI (gh) is not installed")
        svc = ConnectionsService(github_adapter=gh)
        result = svc.list_tools(OWNER)
        gh_tool = next(t for t in result["tools"] if t["provider_id"] == "github")
        assert gh_tool["state"] == DISPLAY_UNAVAILABLE
        assert gh_tool["next_action"]["kind"] == "install"
        # recovery_hint should surface the error_detail when unavailable
        assert "not installed" in (gh_tool["recovery_hint"] or "")

    def test_degraded(self) -> None:
        gh = _gh_adapter("degraded", error_detail="timeout")
        svc = ConnectionsService(github_adapter=gh)
        result = svc.list_tools(OWNER)
        gh_tool = next(t for t in result["tools"] if t["provider_id"] == "github")
        assert gh_tool["state"] == DISPLAY_DEGRADED

    def test_not_configured(self) -> None:
        svc = ConnectionsService(github_adapter=None)
        result = svc.list_tools(OWNER)
        gh_tool = next(t for t in result["tools"] if t["provider_id"] == "github")
        assert gh_tool["state"] == DISPLAY_NOT_CONFIGURED


# ── Jira ledger ──────────────────────────────────────────────────────


class TestJiraLedger:
    def test_zero_connections(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Zero connections: not_configured or owner_action_required depending on acli."""
        ja = _jira_adapter([])
        svc = ConnectionsService(jira_adapter=ja)
        # Monkeypatch shutil.which to say acli is missing
        import holdspeak.services.connections_service as cs_mod
        import shutil
        monkeypatch.setattr(shutil, "which", lambda x: None)
        result = svc.list_tools(OWNER)
        jira_tool = next(t for t in result["tools"] if t["provider_id"] == "jira")
        assert jira_tool["state"] == DISPLAY_UNAVAILABLE

    def test_one_connected(self) -> None:
        ja = _jira_adapter([
            {
                "state": "connected",
                "external_connection_ref": "example.atlassian.net|user@example.com",
            },
        ])
        svc = ConnectionsService(jira_adapter=ja)
        result = svc.list_tools(OWNER)
        jira_tool = next(t for t in result["tools"] if t["provider_id"] == "jira")
        assert jira_tool["state"] == DISPLAY_CONNECTED
        assert jira_tool["account"]["site"] == "example.atlassian.net"
        assert jira_tool["account"]["email"] == "user@example.com"
        assert jira_tool["egress_host"] == "example.atlassian.net"

    def test_two_connections_mixed(self) -> None:
        """Two connections: one connected, one disconnected."""
        ja = _jira_adapter([
            {
                "state": "connected",
                "external_connection_ref": "a.atlassian.net|a@a.com",
            },
            {
                "state": "disconnected",
                "external_connection_ref": "b.atlassian.net|b@b.com",
            },
        ])
        svc = ConnectionsService(jira_adapter=ja)
        result = svc.list_tools(OWNER)
        jira_tool = next(t for t in result["tools"] if t["provider_id"] == "jira")
        # Best state is connected (from the first)
        assert jira_tool["state"] == DISPLAY_CONNECTED
        # connections list carries both
        assert len(jira_tool["connections"]) == 2
        assert jira_tool["connections"][0]["state"] == DISPLAY_CONNECTED
        assert jira_tool["connections"][1]["state"] == DISPLAY_OWNER_ACTION_REQUIRED

    def test_not_configured(self) -> None:
        svc = ConnectionsService(jira_adapter=None)
        result = svc.list_tools(OWNER)
        jira_tool = next(t for t in result["tools"] if t["provider_id"] == "jira")
        assert jira_tool["state"] == DISPLAY_NOT_CONFIGURED

    def test_recovery_hint_normalization(self) -> None:
        """Jira's recovery.command becomes the one recovery_hint string."""
        ja = _jira_adapter([
            {
                "state": "owner_action_required",
                "external_connection_ref": "x.atlassian.net|x@x.com",
            },
        ])
        svc = ConnectionsService(jira_adapter=ja)
        result = svc.list_tools(OWNER)
        jira_tool = next(t for t in result["tools"] if t["provider_id"] == "jira")
        assert jira_tool["state"] == DISPLAY_OWNER_ACTION_REQUIRED
        assert "acli jira auth login" in jira_tool["recovery_hint"]
        assert "x.atlassian.net" in jira_tool["recovery_hint"]


# ── Calendar ─────────────────────────────────────────────────────────


class TestCalendar:
    def test_configured(self) -> None:
        class FakeSource:
            enabled = True
            url = "https://calendar.google.com/calendar/ical/test/basic.ics"

        class FakeCalendar:
            sources = [FakeSource()]

        class FakeConfig:
            calendar = FakeCalendar()

        svc = ConnectionsService(config_loader=lambda: FakeConfig())
        result = svc.list_tools(OWNER)
        cal = next(t for t in result["tools"] if t["provider_id"] == "calendar")
        assert cal["state"] == DISPLAY_CONNECTED
        assert cal["account"]["sources"] == 1

    def test_not_configured(self) -> None:
        svc = ConnectionsService(config_loader=None)
        result = svc.list_tools(OWNER)
        cal = next(t for t in result["tools"] if t["provider_id"] == "calendar")
        assert cal["state"] == DISPLAY_NOT_CONFIGURED


# ── Models ───────────────────────────────────────────────────────────


class TestModels:
    def test_with_assignments(self) -> None:
        ias = MagicMock()
        ias.assignment_summary.return_value = {
            "schema": "InferenceAssignmentSummary@1",
            "rows": [
                {"id": "global", "status": "assigned"},
                {"id": "thinking", "status": "assigned"},
                {"id": "chat", "status": "no_assignment"},
                {"id": "dictation", "status": "assigned"},
                {"id": "observe", "status": "no_assignment"},
                {"id": "compose", "status": "no_assignment"},
                {"id": "refine", "status": "no_assignment"},
            ],
            "task_overrides": [],
            "issue_count": 0,
        }
        svc = ConnectionsService(inference_assignment_service=ias)
        result = svc.list_tools(OWNER)
        models = next(t for t in result["tools"] if t["provider_id"] == "models")
        assert models["state"] == DISPLAY_CONNECTED
        assert models["account"]["assigned"] == 3
        assert models["account"]["total"] == 7

    def test_without_service(self) -> None:
        svc = ConnectionsService()
        result = svc.list_tools(OWNER)
        models = next(t for t in result["tools"] if t["provider_id"] == "models")
        assert models["state"] == DISPLAY_NOT_CONFIGURED
        assert models["account"]["assigned"] == 0


# ── Recheck delegation ──────────────────────────────────────────────


class TestRecheck:
    def test_github_recheck_delegates(self) -> None:
        gh = _gh_adapter("connected", display={"account": "test"})
        svc = ConnectionsService(github_adapter=gh)
        result = svc.recheck(OWNER, "github")
        assert result["state"] == DISPLAY_CONNECTED
        # connection_status was called (by list_tools -> _github_entry)
        assert gh.connection_status.called

    def test_jira_recheck_all_connections(self) -> None:
        ja = _jira_adapter([
            {
                "state": "connected",
                "external_connection_ref": "s1.atlassian.net|u1@x.com",
            },
            {
                "state": "disconnected",
                "external_connection_ref": "s2.atlassian.net|u2@x.com",
            },
        ])
        svc = ConnectionsService(jira_adapter=ja)
        result = svc.recheck(OWNER, "jira")
        # connection_status was called for each connection
        assert ja.connection_status.call_count >= 2

    def test_jira_recheck_specific_ref(self) -> None:
        ja = _jira_adapter([
            {
                "state": "connected",
                "external_connection_ref": "s.atlassian.net|u@x.com",
            },
        ])
        svc = ConnectionsService(jira_adapter=ja)
        result = svc.recheck(OWNER, "jira", ref="s.atlassian.net|u@x.com")
        # connection_status called once for the specific ref
        ja.connection_status.assert_called_once_with(OWNER, "s.atlassian.net|u@x.com")

    def test_unknown_provider(self) -> None:
        svc = ConnectionsService()
        result = svc.recheck(OWNER, "unknown_provider")
        assert result["state"] == DISPLAY_NOT_CONFIGURED


# ── Tool shape invariants ────────────────────────────────────────────


class TestShape:
    def test_all_five_tools_returned(self) -> None:
        svc = ConnectionsService()
        result = svc.list_tools(OWNER)
        ids = [t["provider_id"] for t in result["tools"]]
        assert ids == ["github", "jira", "confluence", "calendar", "models"]  # HS-174: Confluence is the third source

    def test_every_entry_has_required_fields(self) -> None:
        svc = ConnectionsService()
        result = svc.list_tools(OWNER)
        required = {"provider_id", "state", "account", "next_action",
                     "recovery_hint", "error_detail", "last_checked_at",
                     "egress_host"}
        for tool in result["tools"]:
            missing = required - set(tool.keys())
            assert not missing, f"{tool['provider_id']} missing {missing}"
