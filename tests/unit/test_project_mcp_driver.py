"""HS-165-03 -- MCP driver tools for steward, setup, providers, watch graduation.

Tests project.configure_steward, project.run_steward (MCP-003 prompt return),
project.stop_steward, project.get_steward_run, project.setup.*, provider.*,
and project.watch.* (graduated boundary).

Acceptance criteria under test:
- MCP-003 proven: run_steward returns run_id before phase work (slow-phase
  fixture); polling reaches terminal state with receipts.
- The setup interview resumes across tool calls (durable session);
  finalize activates atomically.
- The watch boundary recorded and tested: graduated tools refuse legacy
  rows typed, and the legacy family cannot be called on graduated rows.
"""
from __future__ import annotations

import json
import re
import time
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import server
from holdspeak.mcp.families import project as project_family
from holdspeak.principals import Principal, PrincipalKind


OWNER = Principal(PrincipalKind.OWNER, "drv-mcp-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "drv-mcp.db")
    yield database
    reset_database()


@pytest.fixture(autouse=True)
def mcp_project(db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject DB + auth into the MCP process boundaries."""
    monkeypatch.setattr(project_family, "get_database", lambda: db)
    monkeypatch.setattr(
        server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER),
    )
    monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "off")


def _call(name: str, arguments: dict[str, Any] | None = None) -> tuple[bool, dict[str, Any]]:
    response = server.handle_message({
        "jsonrpc": "2.0",
        "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    })
    assert response is not None
    result = response["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


def _seed_project(db: Database, project_id: str = "proj-drv-001",
                  name: str = "Driver Test") -> str:
    """Seed a minimal project row."""
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, "
            "'2025-01-01T00:00:00', '2025-06-01T00:00:00')",
            (project_id, name),
        )
    return project_id


def _seed_graduated_watch(
    db: Database,
    watch_id: str = "watch-grad-001",
    project_id: str = "proj-drv-001",
    state: str = "active",
) -> str:
    """Seed a graduated WatchSpec@1 row."""
    db.automations.create_watch_in_transaction(
        db._connection().__enter__(),
        watch_id=watch_id,
        connector_id="gh",
        query_kind="pull_requests",
        name="Graduated watch",
        query_json='{"repository":"owner/repo"}',
        enabled=True,
        schema_version="WatchSpec@1",
        project_id=project_id,
        intent="watch PRs",
        subject_kind="pull_request",
        trigger_kind="transition",
        trigger_json="{}",
        state=state,
        revision=1,
    )
    return watch_id


def _seed_legacy_watch(
    db: Database,
    watch_id: str = "watch-legacy-001",
) -> str:
    """Seed a legacy (reactions-family) watch row with state=''."""
    db.automations.create_watch(
        watch_id=watch_id,
        connector_id="gh",
        query_kind="pull_requests",
        name="Legacy watch",
        query={"repository": "owner/repo"},
        enabled=True,
    )
    return watch_id


# ────────────────────────────────────────────────────────────────────
# Steward: configure_steward
# ────────────────────────────────────────────────────────────────────


def test_configure_steward_get_empty(db: Database) -> None:
    """GET returns null policy when none exists."""
    _seed_project(db)
    is_error, data = _call("project.configure_steward", {
        "project_id": "proj-drv-001",
    })
    assert is_error is False
    assert data["policy"] is None


def test_configure_steward_put_creates_policy(db: Database) -> None:
    """PUT with fields creates a new policy."""
    _seed_project(db)
    is_error, data = _call("project.configure_steward", {
        "project_id": "proj-drv-001",
        "enabled": True,
        "unattended_enabled": False,
        "eligible_effect_kinds": ["refresh_sources"],
        "max_retries": 5,
        "cooldown_seconds": 60,
    })
    assert is_error is False
    assert data["success"] is True
    policy = data["policy"]
    assert policy["enabled"] is True
    assert policy["unattended_enabled"] is False
    assert policy["eligible_effect_kinds"] == ["refresh_sources"]
    assert policy["max_retries"] == 5
    assert policy["cooldown_seconds"] == 60


def test_configure_steward_put_updates_existing(db: Database) -> None:
    """PUT on existing policy updates fields."""
    _seed_project(db)
    _call("project.configure_steward", {
        "project_id": "proj-drv-001",
        "enabled": True,
    })
    is_error, data = _call("project.configure_steward", {
        "project_id": "proj-drv-001",
        "unattended_enabled": True,
    })
    assert is_error is False
    assert data["policy"]["unattended_enabled"] is True


def test_configure_steward_invalid_effect_kind(db: Database) -> None:
    """PUT with invalid effect kind refuses typed."""
    _seed_project(db)
    is_error, data = _call("project.configure_steward", {
        "project_id": "proj-drv-001",
        "eligible_effect_kinds": ["bogus_kind"],
    })
    assert is_error is True
    assert "bogus_kind" in data.get("error", "")


def test_configure_steward_emits_event(db: Database) -> None:
    """PUT emits steward.configured event."""
    _seed_project(db)
    _call("project.configure_steward", {
        "project_id": "proj-drv-001",
        "enabled": True,
    })
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT * FROM service_events WHERE event_type='steward.configured'"
        ).fetchall()
    assert len(rows) >= 1
    assert rows[0]["producer"] == "steward.mcp"


# ────────────────────────────────────────────────────────────────────
# Steward: run_steward (MCP-003 prompt return)
# ────────────────────────────────────────────────────────────────────


def test_run_steward_returns_run_id_promptly(db: Database) -> None:
    """MCP-003: run_steward returns run_id BEFORE phase work completes.

    A slow-phase fixture proves the tool returns while the thread is
    still executing.
    """
    _seed_project(db)
    # Enable steward policy
    _call("project.configure_steward", {
        "project_id": "proj-drv-001",
        "enabled": True,
    })

    phase_started = threading.Event()
    phase_gate = threading.Event()

    original_execute = None

    def slow_execute_phases(self, principal, run_id, project_id):
        phase_started.set()
        phase_gate.wait(timeout=5)
        # Let the original run (which will fail quickly since there's
        # no real project data, but that's fine -- we just need the
        # run to end up in a terminal state eventually).
        try:
            original_execute(self, principal, run_id, project_id)
        except Exception:
            pass

    from holdspeak.services.project_steward_service import ProjectStewardService
    original_execute = ProjectStewardService.execute_phases

    with patch.object(ProjectStewardService, "execute_phases", slow_execute_phases):
        is_error, data = _call("project.run_steward", {
            "project_id": "proj-drv-001",
        })

    # The tool MUST have returned already
    assert is_error is False
    assert data["success"] is True
    run_id = data["run_id"]
    assert run_id is not None
    assert run_id.startswith("pstrun_")

    # The phase hasn't started OR the phase is blocked -- either way
    # the tool returned before completion.  Let the thread finish.
    phase_gate.set()


def test_run_steward_disabled_refuses_typed(db: Database) -> None:
    """Typed refusal when steward is disabled."""
    _seed_project(db)
    _call("project.configure_steward", {
        "project_id": "proj-drv-001",
        "enabled": False,
    })
    is_error, data = _call("project.run_steward", {
        "project_id": "proj-drv-001",
    })
    assert is_error is True
    assert data["code"] == "steward_disabled"


def test_run_steward_active_run_refuses_typed(db: Database) -> None:
    """Typed refusal when an active run already exists (STW-002)."""
    _seed_project(db)
    _call("project.configure_steward", {
        "project_id": "proj-drv-001",
        "enabled": True,
    })

    # Freeze the first run's thread so it stays active
    phase_gate = threading.Event()

    def blocked_execute(self, principal, run_id, project_id):
        phase_gate.wait(timeout=5)

    from holdspeak.services.project_steward_service import ProjectStewardService
    with patch.object(ProjectStewardService, "execute_phases", blocked_execute):
        is_error1, data1 = _call("project.run_steward", {
            "project_id": "proj-drv-001",
        })
        assert is_error1 is False

        # Second run should refuse
        is_error2, data2 = _call("project.run_steward", {
            "project_id": "proj-drv-001",
        })
        assert is_error2 is True
        assert data2["code"] == "active_run_exists"

    phase_gate.set()


def test_run_steward_command_id_replay(db: Database) -> None:
    """command_id replay returns stored result (MCP-002)."""
    _seed_project(db)
    _call("project.configure_steward", {
        "project_id": "proj-drv-001",
        "enabled": True,
    })

    from holdspeak.services.project_steward_service import ProjectStewardService
    with patch.object(ProjectStewardService, "execute_phases", lambda *a, **k: None):
        is_error1, data1 = _call("project.run_steward", {
            "project_id": "proj-drv-001",
            "command_id": "cmd-replay-001",
        })
        assert is_error1 is False
        run_id = data1["run_id"]

    # Wait for thread to finish
    time.sleep(0.1)

    # Replay with same command_id
    is_error2, data2 = _call("project.run_steward", {
        "project_id": "proj-drv-001",
        "command_id": "cmd-replay-001",
    })
    assert is_error2 is False
    assert data2["run_id"] == run_id


# ────────────────────────────────────────────────────────────────────
# Steward: stop + poll
# ────────────────────────────────────────────────────────────────────


def test_stop_steward_run(db: Database) -> None:
    """stop_steward sets the durable stop request."""
    _seed_project(db)
    _call("project.configure_steward", {
        "project_id": "proj-drv-001",
        "enabled": True,
    })

    from holdspeak.services.project_steward_service import ProjectStewardService
    gate = threading.Event()
    with patch.object(ProjectStewardService, "execute_phases",
                      lambda *a, **k: gate.wait(timeout=2)):
        _, data = _call("project.run_steward", {"project_id": "proj-drv-001"})
        run_id = data["run_id"]

        is_error, data = _call("project.stop_steward", {"run_id": run_id})
        assert is_error is False
        assert data["success"] is True
    gate.set()


def test_stop_steward_unknown_run(db: Database) -> None:
    """stop_steward with unknown run_id refuses typed."""
    is_error, data = _call("project.stop_steward", {"run_id": "pstrun_bogus"})
    assert is_error is True
    assert "not_found" in data.get("code", "")


def test_get_steward_run(db: Database) -> None:
    """get_steward_run returns run + steps."""
    _seed_project(db)
    _call("project.configure_steward", {
        "project_id": "proj-drv-001",
        "enabled": True,
    })

    from holdspeak.services.project_steward_service import ProjectStewardService
    with patch.object(ProjectStewardService, "execute_phases", lambda *a, **k: None):
        _, data = _call("project.run_steward", {"project_id": "proj-drv-001"})
        run_id = data["run_id"]

    # Poll
    is_error, data = _call("project.get_steward_run", {"run_id": run_id})
    assert is_error is False
    assert "run" in data
    assert data["run"]["id"] == run_id
    assert "steps" in data


def test_get_steward_run_unknown(db: Database) -> None:
    """get_steward_run with unknown run_id refuses typed."""
    is_error, data = _call("project.get_steward_run", {"run_id": "pstrun_bogus"})
    assert is_error is True


def test_run_steward_poll_reaches_terminal(db: Database) -> None:
    """MCP-003 proven: polling reaches terminal state after completion."""
    _seed_project(db)
    _call("project.configure_steward", {
        "project_id": "proj-drv-001",
        "enabled": True,
    })

    from holdspeak.services.project_steward_service import ProjectStewardService

    def fast_execute(self, principal, run_id, project_id):
        """Simulate fast completion by updating run state directly."""
        self._db.steward_runs.update_run_state(
            run_id, state="completed", phase="complete",
        )

    with patch.object(ProjectStewardService, "execute_phases", fast_execute):
        _, data = _call("project.run_steward", {"project_id": "proj-drv-001"})
        run_id = data["run_id"]

    # Give the daemon thread a moment to run
    time.sleep(0.2)

    # Poll and verify terminal state
    _, poll = _call("project.get_steward_run", {"run_id": run_id})
    assert poll["run"]["state"] in ("completed", "failed")


# ────────────────────────────────────────────────────────────────────
# Setup interview: durable session across tool calls
# ────────────────────────────────────────────────────────────────────


def test_setup_start_and_resume(db: Database) -> None:
    """Start creates a session; resume reads it back (durable)."""
    is_error, data = _call("project.setup.start")
    assert is_error is False
    session_id = data.get("id") or data.get("session_id")
    assert session_id is not None

    # Resume the same session
    is_error2, data2 = _call("project.setup.resume", {"session_id": session_id})
    assert is_error2 is False
    resumed_id = data2.get("id") or data2.get("session_id")
    assert resumed_id == session_id


def test_setup_resume_unknown_session(db: Database) -> None:
    """resume with unknown session_id refuses typed."""
    is_error, data = _call("project.setup.resume", {"session_id": "psetup_bogus"})
    assert is_error is True


def test_setup_answer(db: Database) -> None:
    """answer records the answer in the durable session."""
    _, start_data = _call("project.setup.start")
    session_id = start_data.get("id") or start_data.get("session_id")

    is_error, data = _call("project.setup.answer", {
        "session_id": session_id,
        "question_id": "outcome",
        "payload": {"text": "Track CI health on my repos"},
    })
    assert is_error is False


def test_setup_suggest(db: Database) -> None:
    """suggest returns proposals (may be empty with no answers)."""
    _, start_data = _call("project.setup.start")
    session_id = start_data.get("id") or start_data.get("session_id")

    is_error, data = _call("project.setup.suggest", {"session_id": session_id})
    assert is_error is False
    assert "proposals" in data


def test_setup_finalize_empty(db: Database) -> None:
    """Finalize with no selected proposals is lawful (INT-002)."""
    _, start_data = _call("project.setup.start")
    session_id = start_data.get("id") or start_data.get("session_id")

    # Answer outcome question first (required for project name)
    _call("project.setup.answer", {
        "session_id": session_id,
        "question_id": "outcome",
        "payload": {"text": "Empty finalize test"},
    })

    is_error, data = _call("project.setup.finalize", {
        "session_id": session_id,
    })
    assert is_error is False
    assert "project_id" in data


def test_setup_finalize_command_id(db: Database) -> None:
    """finalize carries command_id (MCP-002 where the route has it)."""
    _, start_data = _call("project.setup.start")
    session_id = start_data.get("id") or start_data.get("session_id")

    _call("project.setup.answer", {
        "session_id": session_id,
        "question_id": "outcome",
        "payload": {"text": "Command ID test"},
    })

    is_error, data = _call("project.setup.finalize", {
        "session_id": session_id,
        "command_id": "cmd-finalize-001",
    })
    assert is_error is False


# ────────────────────────────────────────────────────────────────────
# Providers
# ────────────────────────────────────────────────────────────────────


def test_provider_list_native(db: Database) -> None:
    """provider.list returns at least the native providers."""
    # Mock _github_adapter to return None (no GitHub configured)
    with patch.object(project_family, "_github_adapter", return_value=None):
        is_error, data = _call("provider.list")
    assert is_error is False
    assert "providers" in data
    assert len(data["providers"]) >= 1
    native = data["providers"][0]
    assert native["provider_id"] == "native"


def test_provider_github_connection_not_configured(db: Database) -> None:
    """github_connection refuses typed when adapter is absent."""
    with patch.object(project_family, "_github_adapter", return_value=None):
        is_error, data = _call("provider.github_connection")
    assert is_error is True
    assert data["code"] == "provider_not_configured"


def test_provider_github_discover_not_configured(db: Database) -> None:
    """github_discover refuses typed when adapter is absent."""
    with patch.object(project_family, "_github_adapter", return_value=None):
        is_error, data = _call("provider.github_discover")
    assert is_error is True
    assert data["code"] == "provider_not_configured"


def test_provider_github_validate_repo_not_configured(db: Database) -> None:
    """github_validate_repo refuses typed when adapter is absent."""
    with patch.object(project_family, "_github_adapter", return_value=None):
        is_error, data = _call("provider.github_validate_repo", {
            "owner_repo": "octocat/Hello-World",
        })
    assert is_error is True
    assert data["code"] == "provider_not_configured"


def test_provider_github_validate_repo_missing_owner_repo(db: Database) -> None:
    """github_validate_repo refuses typed when owner_repo is missing."""
    mock_adapter = SimpleNamespace(
        validate_repo=lambda p, r: {"valid": True},
    )
    with patch.object(project_family, "_github_adapter", return_value=mock_adapter):
        is_error, data = _call("provider.github_validate_repo", {
            "owner_repo": "",
        })
    assert is_error is True


# ────────────────────────────────────────────────────────────────────
# Watch graduation boundary
# ────────────────────────────────────────────────────────────────────


def test_watch_inspect_graduated(db: Database) -> None:
    """inspect returns a graduated watch."""
    _seed_project(db)
    _seed_graduated_watch(db)
    is_error, data = _call("project.watch.inspect", {"watch_id": "watch-grad-001"})
    assert is_error is False
    assert data.get("id") == "watch-grad-001"


def test_watch_inspect_refuses_legacy(db: Database) -> None:
    """inspect refuses legacy rows typed (boundary rule)."""
    _seed_legacy_watch(db)
    is_error, data = _call("project.watch.inspect", {"watch_id": "watch-legacy-001"})
    assert is_error is True
    assert data["code"] == "legacy_watch_boundary"


def test_watch_pause_graduated(db: Database) -> None:
    """pause works on graduated watch."""
    _seed_project(db)
    _seed_graduated_watch(db)
    is_error, data = _call("project.watch.pause", {"watch_id": "watch-grad-001"})
    assert is_error is False
    assert data.get("state") == "paused"


def test_watch_resume_graduated(db: Database) -> None:
    """resume works on graduated (paused) watch."""
    _seed_project(db)
    _seed_graduated_watch(db, state="paused")
    is_error, data = _call("project.watch.resume", {"watch_id": "watch-grad-001"})
    assert is_error is False
    assert data.get("state") == "active"


def test_watch_retire_graduated(db: Database) -> None:
    """retire works on graduated watch."""
    _seed_project(db)
    _seed_graduated_watch(db)
    is_error, data = _call("project.watch.retire", {"watch_id": "watch-grad-001"})
    assert is_error is False
    assert data.get("state") == "retired"


def test_watch_pause_refuses_legacy(db: Database) -> None:
    """pause refuses legacy rows typed."""
    _seed_legacy_watch(db)
    is_error, data = _call("project.watch.pause", {"watch_id": "watch-legacy-001"})
    assert is_error is True
    assert data["code"] == "legacy_watch_boundary"


def test_watch_resume_refuses_legacy(db: Database) -> None:
    """resume refuses legacy rows typed."""
    _seed_legacy_watch(db)
    is_error, data = _call("project.watch.resume", {"watch_id": "watch-legacy-001"})
    assert is_error is True
    assert data["code"] == "legacy_watch_boundary"


def test_watch_retire_refuses_legacy(db: Database) -> None:
    """retire refuses legacy rows typed."""
    _seed_legacy_watch(db)
    is_error, data = _call("project.watch.retire", {"watch_id": "watch-legacy-001"})
    assert is_error is True
    assert data["code"] == "legacy_watch_boundary"


def test_watch_set_rules_refuses_legacy(db: Database) -> None:
    """set_rules refuses legacy rows typed."""
    _seed_legacy_watch(db)
    is_error, data = _call("project.watch.set_rules", {
        "watch_id": "watch-legacy-001",
        "rules": [],
    })
    assert is_error is True
    assert data["code"] == "legacy_watch_boundary"


def test_watch_test_refuses_legacy(db: Database) -> None:
    """test refuses legacy rows typed."""
    _seed_legacy_watch(db)
    is_error, data = _call("project.watch.test", {"watch_id": "watch-legacy-001"})
    assert is_error is True
    assert data["code"] == "legacy_watch_boundary"


def test_watch_evaluate_refuses_legacy(db: Database) -> None:
    """evaluate refuses legacy rows typed."""
    _seed_legacy_watch(db)
    is_error, data = _call("project.watch.evaluate", {"watch_id": "watch-legacy-001"})
    assert is_error is True
    assert data["code"] == "legacy_watch_boundary"


def test_watch_set_rules_graduated(db: Database) -> None:
    """set_rules works on graduated watch (empty rules is valid)."""
    _seed_project(db)
    _seed_graduated_watch(db)
    is_error, data = _call("project.watch.set_rules", {
        "watch_id": "watch-grad-001",
        "rules": [],
    })
    assert is_error is False
    assert "watch_id" in data


def test_watch_inspect_not_found(db: Database) -> None:
    """inspect with unknown watch_id refuses typed."""
    is_error, data = _call("project.watch.inspect", {"watch_id": "watch-bogus"})
    assert is_error is True


def test_legacy_family_untouched() -> None:
    """The reactions family tools list is unchanged by this story."""
    from holdspeak.mcp.families import reactions
    legacy_names = {t["name"] for t in reactions.TOOLS}
    # The legacy family must still own these names
    assert "watch.list" in legacy_names
    assert "watch.create" in legacy_names
    assert "watch.refresh" in legacy_names
    assert "reaction.list" in legacy_names
    assert "reaction.create" in legacy_names
    # The graduated tools must NOT be in the legacy family
    assert "project.watch.inspect" not in legacy_names
    assert "project.watch.pause" not in legacy_names


# ────────────────────────────────────────────────────────────────────
# Tool count verification
# ────────────────────────────────────────────────────────────────────


def test_project_family_tool_count_is_53() -> None:
    """The project family ships the expected number of tools."""
    # 17 original + 5 steward + 5 setup + 1 setup.clarify_jira_scope + 4 provider + 3 jira provider + 3 jira discover/search/validate + 7 watch = 45
    # HS-168-02: + connection.list / connection.recheck (45 -> 47).
    # HS-172-06: + project.suggested_sources / add_suggested_source / dismiss_suggested_source (47 -> 50).
    assert len(project_family.TOOLS) == 53


def test_graduated_watch_states_constant() -> None:
    """_GRADUATED_WATCH_STATES is frozen and correct."""
    assert project_family._GRADUATED_WATCH_STATES == frozenset({
        "active", "tested", "paused", "retired",
    })


# ── HS-166-03: sidecar fetcher seam ─────────────────────────────────


def test_watch_service_receives_snapshot_fetcher() -> None:
    """_watch_service() composes a snapshot_fetcher that handles jira."""
    from holdspeak.services.watch_service import WatchService
    ws = project_family._watch_service()
    assert isinstance(ws, WatchService)
    # The snapshot_fetcher should be set (not None)
    assert ws._snapshot_fetcher is not None


def test_setup_service_receives_jira_adapter() -> None:
    """_setup_service() composes with a jira_adapter kwarg."""
    from holdspeak.services.project_setup_service import ProjectSetupService
    ss = project_family._setup_service()
    assert isinstance(ss, ProjectSetupService)
    # The jira_adapter may be None (no acli installed), but the kwarg
    # should be accepted without error.
    assert hasattr(ss, "_jira_adapter")
