"""AG14: the hand automation sentence as rendered on the real desk."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir
from .test_automation_glass import _new_automation, _object_edit

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
                _new_automation(page)
                # The starters are cards in the Automations window's pane.
                chooser = page.locator("[id='surface-workbenches']")
                chooser.get_by_role("button", name="Create", exact=True).wait_for(timeout=45_000)
                with page.expect_response(
                    lambda response: response.url.endswith("/api/workbenches")
                    and response.request.method == "POST"
                ) as created:
                    chooser.get_by_role("button", name="Create", exact=True).click()
                workbench = created.value.json()["workbench"]
                workbench_id = workbench["id"]
                chooser.get_by_test_id("automation-setup").wait_for()
                chooser.get_by_role("button", name="Cancel", exact=True).click()
                chooser.locator(f'[data-object-id="{workbench_id}"]').dblclick()
                window = page.get_by_test_id("automation-window")
                window.wait_for(timeout=45_000)
                _settle(page)

                _object_edit(page, window, "Do")
                form = window.get_by_test_id("automation-setup")
                form.get_by_role("combobox",name="Do kind",exact=True).select_option("hand_to_agent")
                form.get_by_role("textbox",name="Agent brief").fill("Complete the action and report the result.")
                with page.expect_response(lambda response: response.url.endswith(f"/api/workbenches/{workbench_id}") and response.request.method == "PUT") as do_saved:
                    form.get_by_role("button",name="Save",exact=True).click()
                assert do_saved.value.request.post_data_json["do_kind"] == "hand_to_agent"
                window.get_by_test_id("automation-summary").wait_for()
                _object_edit(page, window, "With")
                engine = window.get_by_role("combobox",name="With",exact=True)
                engine.select_option("claude-default")
                review = window.get_by_role("combobox",name="Review by",exact=True)
                review.select_option("codex")
                page.screenshot(path=str(SHOTS / f"do-with-review-{width}-open.png"))
                with page.expect_response(lambda response: response.url.endswith(f"/api/workbenches/{workbench_id}") and response.request.method == "PUT") as saved:
                    window.get_by_role("button",name="Save",exact=True).click()
                assert saved.value.ok, saved.value.text()
                assert saved.value.request.post_data_json["review_by"] == "codex"
                window.get_by_test_id("automation-summary").wait_for()
                page.screenshot(path=str(SHOTS / f"do-with-review-{width}-closed.png"))
                row = _api(page, "GET", f"/api/workbenches/{workbench_id}", token=TOKEN)["workbench"]
                assert row["do_kind"] == "hand_to_agent"
                assert row["agent_profile"] == "claude-default"
                assert row["review_by"] == "codex"
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.stop()
