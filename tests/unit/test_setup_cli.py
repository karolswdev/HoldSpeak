from __future__ import annotations

from types import SimpleNamespace

from holdspeak.commands import setup


def test_setup_yes_prints_each_failed_outcome_and_returns_failure(monkeypatch, capsys) -> None:
    answers = iter([
        {"rows": [{"id": "speech", "label": "Speech", "state": "found", "action": "speech"}]},
        {
            "state": "does_not_work",
            "success": False,
            "results": [{"id": "speech", "label": "Speech", "state": "does_not_work", "reason": "Try again."}],
        },
    ])
    monkeypatch.setattr(setup, "_tool_call", lambda _name, _arguments: next(answers))

    assert setup.run_setup_command(SimpleNamespace(yes=True)) == 1
    output = capsys.readouterr().out
    assert "Speech: Found" in output
    assert "Speech: Does not work · Try again." in output


def test_setup_yes_keeps_pending_distinct_from_success(monkeypatch, capsys) -> None:
    answers = iter([
        {"rows": [{"id": "speech", "label": "Speech", "state": "found", "action": "speech"}]},
        {
            "state": "pending",
            "success": False,
            "results": [{"id": "speech", "label": "Speech", "state": "pending", "reason": "Still working."}],
        },
    ])
    monkeypatch.setattr(setup, "_tool_call", lambda _name, _arguments: next(answers))

    assert setup.run_setup_command(SimpleNamespace(yes=True)) == 0
    assert "Speech: Working · Still working." in capsys.readouterr().out


def test_setup_yes_reaches_real_hub_accounts_calendar_and_native_agent_bindings(
    tmp_path, monkeypatch, capsys,
) -> None:
    """Only provider/native CLI and EventKit leaves are simulated."""
    import json
    import shutil
    from holdspeak import config as config_module
    from holdspeak.db import reset_database
    from holdspeak.runtime import composition
    from holdspeak.mcp import server as mcp_server
    import holdspeak.services.onboarding_service as onboarding_module
    from tests.unit.test_onboarding_backends import _home, _runner, FakeMac
    from tests.unit.test_onboarding_agents import _seat
    from tests.unit.test_philo9_b1_connections import _boot

    home = _home(tmp_path)
    calls = []
    runner = _runner(calls)
    hub = _boot(tmp_path, monkeypatch, runner, runner)
    try:
        onboarding = _seat(hub, home, "claude", "codex", "tmux", "gh", "acli")
        onboarding._connections._gh_hosts_file = lambda: home / ".config" / "gh" / "hosts.yml"
        onboarding._jira._registry_path = home / ".config" / "acli" / "jira_config.yaml"
        onboarding._macos = FakeMac("full_access", [{
            "id": "work", "title": "Work calendar", "account": "Work", "kind": "CalDAV",
        }])
        onboarding._refresh = lambda: None
        monkeypatch.setattr(onboarding_module, "trust_codex_hooks", lambda **_: {"state": "trusted"})
        monkeypatch.setattr(onboarding_module, "_codex_launch_hooks_stamped", lambda _home: True)
        # The inventory's PATH scan must stay on the rig, too.
        monkeypatch.setattr(shutil, "which", lambda *_a, **_k: None)
        service = hub.root.operations.target("setup.status")
        service._home = lambda: home
        service._local_ai = SimpleNamespace(status=lambda _principal: {"state": "ready", "speech": {"ready": True}})

        monkeypatch.setattr(mcp_server, "discover_hub", lambda: object())
        def forward(request, _connection):
            response = hub.client.post("/api/mcp", json=request)
            assert response.status_code == 200, response.text
            return response.json()
        monkeypatch.setattr(mcp_server, "forward_to_hub", forward)

        before = setup._tool_call("setup.status", {})
        actionable = [row["id"] for row in before["rows"] if row.get("action") and row["state"] == "found"]
        assert any(row.startswith("connection:github:") for row in actionable), actionable
        assert any(row.startswith("connection:jira:") for row in actionable), actionable
        assert any(row.startswith("connection:confluence:") for row in actionable), actionable
        assert "calendar:eventkit:work" in actionable and "agents" in actionable
        assert setup.run_setup_command(SimpleNamespace(yes=True)) == 0
        output = capsys.readouterr().out
        assert "Use everything found" in output
        assert "Does not work" not in output.split("Use everything found", 1)[1], output
        after = setup._tool_call("setup.status", {})
        by_id = {row["id"]: row for row in after["rows"]}
        assert all(by_id[row_id]["state"] == "works" for row_id in actionable), after
        assert any(source.url == "eventkit:work" for source in config_module.Config.load().calendar.sources)
        assert "mcpServers" in json.loads((home / ".claude.json").read_text())
        assert "mcp_servers.holdspeak" in (home / ".codex" / "config.toml").read_text()
        assert (home / ".claude" / "skills" / "holdspeak" / "SKILL.md").is_file()
        assert (home / ".agents" / "skills" / "holdspeak" / "SKILL.md").is_file()
        assert any(argv[:3] == ["gh", "auth", "status"] for argv in calls)
        assert any(argv[:3] == ["acli", "jira", "auth"] for argv in calls)
        assert any(argv[:3] == ["acli", "confluence", "auth"] for argv in calls)
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))
