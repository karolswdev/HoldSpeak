"""The actual aggregate agent producer reaches Setup at both desk sizes.

Only the native CLI runner and Codex hook-trust leaves are simulated. The
HTTP authority, admitted operation, configuration writes, readiness readback
and browser consumer are production paths in a disposable HOME.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from playwright.sync_api import expect, sync_playwright

from .glass_infra import _boot, _ensure_build


@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_setup_keeps_the_failed_agent_when_the_next_binding_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int,
) -> None:
    from holdspeak.runtime import composition
    import holdspeak.services.onboarding_service as onboarding
    from tests.unit.test_onboarding_agents import _seat
    from tests._evidence import evidence_dir

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token="setup-agent-binding")
    try:
        home = tmp_path / "native-agents"
        home.mkdir()
        foreign = {"type": "stdio", "command": "another-mcp", "args": [], "env": {}}
        native_config = home / ".claude.json"
        native_config.write_text(json.dumps({"mcpServers": {"holdspeak": foreign}}))
        monkeypatch.setattr(onboarding, "trust_codex_hooks", lambda **_: {"state": "trusted"})
        monkeypatch.setattr(onboarding, "_codex_launch_hooks_stamped", lambda _home: True)
        _seat(SimpleNamespace(root=composition.current()), home, "claude", "codex")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(f"{base}/?token=setup-agent-binding", wait_until="load")
            face = page.get_by_test_id("setup-face")
            face.wait_for(timeout=30_000)
            # Window grammar (2026-10-24): Setup is a dense list of readiness
            # rows; a press selects the Agents row and its one verb sits in the
            # status bar; the selected row's bindings read under the list.
            row = face.get_by_test_id("setup-row").filter(has_text="Agents")
            expect(row).to_have_count(1)
            row.get_by_role("button").first.click()
            verb = face.get_by_test_id("setup-row-verb")
            expect(verb).to_have_text("Let my agents use HoldSpeak")
            pane = face.get_by_test_id("setup-selection")
            requests = []
            page.on("request", lambda request: requests.append(request.post_data_json)
                    if request.url.endswith("/api/onboarding/agents/use") else None)
            with page.expect_response(lambda response: response.url.endswith("/api/onboarding/agents/use")
                                      and response.request.method == "POST") as response:
                verb.click()
            body = response.value.json()
            assert requests == [{"agents": ["claude", "codex"]}], requests
            assert body["state"] == "degraded" and body["success"] is False, body
            assert [(r["agent"], r["ok"]) for r in body["results"]] == [("claude", False), ("codex", True)]
            codex_result = body["results"][1]["used"]
            assert codex_result["agent"] == "codex"
            assert codex_result["mcp"]["state"] == "installed"
            assert codex_result["skill"].endswith("/.agents/skills/holdspeak/SKILL.md")
            codex_config = home / ".codex" / "config.toml"
            codex_hooks = home / ".codex" / "hooks.json"
            codex_skill = home / ".agents" / "skills" / "holdspeak" / "SKILL.md"
            assert "mcp_servers.holdspeak" in codex_config.read_text()
            assert codex_hooks.is_file()
            assert codex_skill.is_file()
            expect(row.get_by_test_id("setup-row-state")).to_have_text("Failed")
            expect(row).to_contain_text("Claude Code:")
            expect(pane).to_contain_text("hooks")
            expect(pane).to_contain_text("tools")
            expect(pane).to_contain_text("skill")
            expect(face).not_to_contain_text("mcp_name_taken")
            expect(face).not_to_contain_text(str(home))
            expect(row).not_to_contain_text("Ready")
            expect(face.get_by_role("button", name="Let my agents use HoldSpeak", exact=True)).to_be_visible()
            expect(pane.get_by_text("Codex · uses your desk", exact=True)).to_be_visible()
            codex = pane.get_by_text("Codex · uses your desk", exact=True).locator("..").locator("..")
            with page.expect_response(lambda response: response.url.endswith("/api/onboarding/agents/stop")
                                      and response.request.method == "POST") as stopped:
                codex.get_by_role("button", name="Stop using my desk", exact=True).click()
            assert stopped.value.ok, stopped.value.text()
            assert json.loads(native_config.read_text())["mcpServers"]["holdspeak"] == foreign
            assert "mcp_servers.holdspeak" not in codex_config.read_text()
            assert not json.loads(codex_hooks.read_text()).get("hooks")
            assert not codex_skill.exists()
            expect(face.get_by_text("Codex · uses your desk", exact=True)).to_have_count(0)
            shots = evidence_dir("setup-agent-binding")
            (shots / f"mixed-result-{width}.json").write_text(json.dumps(body, indent=2) + "\n")
            row.scroll_into_view_if_needed()
            page.screenshot(path=str(shots / f"mixed-result-{width}.png"))
            browser.close()
    finally:
        server.stop()
