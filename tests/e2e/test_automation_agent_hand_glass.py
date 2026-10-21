"""AG14: the hand automation sentence as rendered on the real desk."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the hand automation glass needs Playwright")
pytestmark = [pytest.mark.e2e]

TOKEN = "automation-agent-hand-glass"
SHOTS = evidence_dir("automation-agent-hand")
SIZES = {1440: 900, 393: 852}


def _install_native_agent_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Seed only this rig's private files with successful native readiness."""
    monkeypatch.setenv("HOLDSPEAK_AGENT_STATE", "on")
    home = tmp_path / "home"
    from holdspeak import coder_gate
    from holdspeak.agent_context import codex_trust
    from holdspeak.agent_context.hooks import install_agent_hooks
    from holdspeak.agent_context.native_binding import resolve_server_command
    from holdspeak.agent_skill import install_skill
    from holdspeak.services.onboarding_service import agent_hook_template

    install_agent_hooks(home / ".claude" / "settings.json", agent_hook_template("claude"))
    install_agent_hooks(home / ".codex" / "hooks.json", agent_hook_template("codex"))
    install_skill(home / ".claude", "claude")
    install_skill(home / ".agents", "codex")
    server_command = resolve_server_command()
    assert server_command
    (home / ".claude" / ".claude.json").write_text(json.dumps({
        "mcpServers": {
            "holdspeak": {"type": "stdio", "command": server_command, "args": [], "env": {}},
        },
    }), encoding="utf-8")
    (home / ".codex" / "config.toml").write_text(
        f"[mcp_servers.holdspeak]\ncommand = {server_command!r}\n", encoding="utf-8",
    )
    flags = coder_gate.codex_hook_flags(coder_gate.spawn_prefix())
    codex_trust.write_trust_stamp(flags, home / ".holdspeak" / "codex_hook_trust.json")


@pytest.mark.parametrize("width", [1440, 393])
def test_hand_automation_do_with_review_controls_are_real_and_saved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        _install_native_agent_state(tmp_path, monkeypatch)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": width, "height": SIZES[width]},
                device_scale_factor=1,
                has_touch=width < 720,
                reduced_motion="reduce",
            )
            page = context.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)[:240]))
            try:
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.get_by_role("button", name="Go", exact=True).first.click()
                go = page.locator("nav[aria-label='Go menu']")
                go.wait_for(timeout=45_000)
                go.get_by_role("menuitem", name="Automations").first.evaluate("el => el.click()")
                page.get_by_test_id("automation-new").wait_for(timeout=45_000)
                page.get_by_test_id("automation-new").click()
                chooser = page.get_by_role("region", name="New Automation")
                chooser.wait_for(timeout=45_000)
                with page.expect_response(
                    lambda response: response.url.endswith("/api/workbenches")
                    and response.request.method == "POST"
                ) as created:
                    chooser.get_by_test_id("automation-starter-scratch").click()
                workbench = created.value.json()["workbench"]
                workbench_id = workbench["id"]
                window = page.get_by_test_id("automation-window")
                window.wait_for(timeout=45_000)
                _settle(page)

                # Scratch now opens the guided builder. Complete its real Do
                # write and the remaining steps before testing saved-summary
                # editing and native agent admission below.
                setup = page.get_by_test_id("automation-setup")
                setup.get_by_role("textbox", name="What it does", exact=True).fill("Complete the action.")
                for _ in range(4):
                    setup.get_by_test_id("automation-setup-next").click()
                setup.get_by_test_id("automation-setup-done").click()
                setup.wait_for(state="hidden")

                do_line = page.get_by_test_id("automation-line-do")
                with_line = page.get_by_test_id("automation-line-with")
                review_line = page.get_by_test_id("automation-line-review")
                do_line.get_by_role("button").first.click()
                do_editor = page.get_by_test_id("automation-do-editor")
                do_editor.get_by_role("button", name="Hand to an agent", exact=True).click()
                do_editor.get_by_role("textbox", name="Agent brief").fill(
                    "Complete the action and report the result."
                )
                with page.expect_response(
                    lambda response: response.url.endswith(f"/api/workbenches/{workbench_id}")
                    and response.request.method == "PUT"
                ) as do_saved:
                    do_editor.get_by_test_id("automation-do-save").click()
                assert (do_saved.value.request.post_data_json or {}).get("do_kind") == "hand_to_agent"
                do_line.get_by_text("Hand to an agent", exact=False).wait_for(timeout=10_000)

                with_line.get_by_role("button").first.click()
                native_editor = page.get_by_test_id("automation-native-with-editor")
                native_editor.wait_for(timeout=10_000)
                native_rows = native_editor.get_by_test_id("automation-native-agent").all_text_contents()
                assert all(any(label in row for row in native_rows) for label in ("Claude Code", "Codex CLI", "pi"))
                with page.expect_response(
                    lambda response: response.url.endswith(f"/api/workbenches/{workbench_id}/engine")
                    and response.request.method == "PUT"
                ) as with_saved:
                    native_editor.get_by_role("button", name="Use Claude Code", exact=True).click()
                assert (with_saved.value.request.post_data_json or {}).get("profile_id") == "claude-default"
                with_line.locator(".automation-line-press-value").get_by_text("Claude Code", exact=True).wait_for(timeout=10_000)
                assert "claude-default" not in with_line.locator(".automation-line-press-value").inner_text()

                page.screenshot(path=str(SHOTS / f"do-with-review-{width}-closed.png"))
                review_line.get_by_role("button").first.click()
                editor = page.get_by_test_id("automation-review-editor")
                editor.wait_for(timeout=10_000)
                editor.get_by_role("button", name="Codex", exact=True).wait_for(timeout=10_000)
                assert {"None", "Codex", "Claude Code", "pi"}.issubset(
                    set(editor.get_by_role("button").all_text_contents())
                )
                page.screenshot(path=str(SHOTS / f"do-with-review-{width}-open.png"))

                with page.expect_response(
                    lambda response: response.url.endswith(f"/api/workbenches/{workbench_id}")
                    and response.request.method == "PUT"
                ) as saved:
                    editor.get_by_role("button", name="Codex", exact=True).click()
                assert saved.value.ok, saved.value.text()
                assert (saved.value.request.post_data_json or {}).get("review_by") == "codex"
                page.get_by_test_id("automation-line-review").get_by_text("Codex CLI", exact=True).wait_for(timeout=10_000)
                row = _api(page, "GET", f"/api/workbenches/{workbench_id}", token=TOKEN)["workbench"]
                assert row["do_kind"] == "hand_to_agent"
                assert row["agent_profile"] == "claude-default"
                assert row["review_by"] == "codex"
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.stop()
