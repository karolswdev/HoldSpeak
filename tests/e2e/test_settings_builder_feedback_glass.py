"""Owner's Settings and Automation builder reports, on real Firefox glass."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows
from .test_ui_feedback_glass import _save_feedback

TOKEN = "settings-builder-feedback"
SHOTS = evidence_dir("settings-builder-feedback")


def _contained(window: Any) -> None:
    assert window.evaluate("""el => {
      const body = el.querySelector('.desk-surface-body');
      const r = el.getBoundingClientRect();
      return r.left >= -1 && r.right <= innerWidth + 1
        && (!body || body.scrollWidth <= body.clientWidth + 1)
        && document.documentElement.scrollWidth <= innerWidth;
    }"""), window.bounding_box()


def _selection_has_ink(button: Any) -> None:
    facts = button.evaluate("""el => {
      const probe = document.createElement('span');
      probe.hidden = true; probe.style.color = 'var(--wb-sel)'; el.append(probe);
      const expected = getComputedStyle(probe).color; probe.remove();
      return {actual: getComputedStyle(el).backgroundColor, expected};
    }""")
    assert facts["actual"] == facts["expected"], facts


def _capture(page: Any, window: Any, width: int, stem: str) -> dict[str, Any]:
    window.locator("button[aria-label^='Give feedback on ']").click()
    page.locator("[data-ui-feedback]").get_by_text("RECORDING", exact=True).wait_for()
    page.wait_for_timeout(1200)
    report = _save_feedback(page, width, shot_stem=stem,
                            window_id=str(window.get_attribute("id")), draft=None)
    page.locator("[data-ui-feedback]").get_by_role("button", name="Done", exact=True).click()
    page.locator("[data-ui-feedback]").wait_for(state="hidden")
    return report


@pytest.mark.e2e
@pytest.mark.parametrize("width", [1440, 393])
def test_reported_settings_categories_and_guided_builder_in_firefox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from playwright.sync_api import sync_playwright
    from holdspeak.intel.cli_engine import CLI_ENGINES_ENV
    from tests.fixtures.fake_agent_cli import install_fake_agent_clis, path_with

    # Only devices/agent executables are simulated. All UI reads and writes
    # use this rig's private Hub and DB; no owner preferences are copied.
    bins = install_fake_agent_clis(tmp_path / "bin")
    monkeypatch.setenv("PATH", path_with(bins))
    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    monkeypatch.setenv(CLI_ENGINES_ENV, "on")
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.primitive_service import PrimitiveService

    PrimitiveService(get_database()).create_note(
        Principal(PrincipalKind.OWNER, "glass"), note_id="wizard-source",
        title="Platform checkpoint", body_markdown="Keep the rollback checkpoint.", tags=[],
    )
    try:
        with sync_playwright() as pw:
            browser = pw.firefox.launch(headless=True, firefox_user_prefs={
                "media.navigator.streams.fake": True,
                "media.navigator.permission.disabled": True,
                "media.autoplay.default": 0,
                "media.autoplay.block-webaudio": False,
            })
            try:
                page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852},
                                        device_scale_factor=1, reduced_motion="reduce")
                page.set_default_timeout(30_000)
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                clear_hub_windows(page, TOKEN)
                _api(page, "POST", "/api/desk/windows/surface-settings/open", {}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                settings = page.locator("[id='surface-settings'][data-layer='window']")
                settings.get_by_role("textbox", name="Your name", exact=True).wait_for()
                assert settings.locator("[data-settings-section]:visible").count() == 1
                assert settings.locator("[data-settings-section]:visible").get_attribute("data-settings-section") == "you"
                _selection_has_ink(settings.get_by_test_id("settings-index-you"))
                for image in settings.locator(".settings-page-index img").all():
                    page.wait_for_function("el => el.complete && el.naturalWidth > 0", arg=image.element_handle())
                assert settings.locator(".settings-page-index img").count() == 8
                # A real category press blurs and commits an alias. It must still
                # be present when the owner returns to You.
                alias = settings.get_by_test_id("settings-owner-aliases").get_by_role("textbox")
                alias.fill("Architect draft")
                settings.get_by_test_id("settings-index-speak").click()
                assert not settings.get_by_role("textbox", name="Your name", exact=True).is_visible()
                assert settings.locator("[data-settings-section]:visible").count() == 1
                settings.get_by_test_id("settings-index-you").click()
                settings.get_by_test_id("settings-owner-aliases").get_by_text("Architect draft", exact=True).wait_for()
                _settle(page)
                _contained(settings)
                page.screenshot(path=str(SHOTS / f"settings-you-{width}.png"))
                report = _capture(page, settings, width, "settings-categories")
                assert report["context"]["owner"]["window_id"] == "surface-settings"

                settings.get_by_test_id("settings-index-speak").click()
                language = settings.get_by_role("combobox", name="Language", exact=True)
                language.click()
                popup = page.get_by_role("listbox", name="Language", exact=True)
                popup.wait_for()
                _contained(settings)
                page.screenshot(path=str(SHOTS / f"settings-dropdown-{width}.png"))
                popup.get_by_role("option", name="English (en)", exact=True).click()
                page.wait_for_function("""async token => {
                  const r = await fetch('/api/settings', {headers:{'X-HoldSpeak-Token':token}});
                  return (await r.json()).model.language === 'en';
                }""", arg=TOKEN)
                assert language.input_value() == "en"
                settings.locator(".desk-gadget-close").click()

                page.get_by_role("button", name="Go", exact=True).first.click()
                page.locator("nav[aria-label='Go menu']").get_by_role("menuitem", name="Automations").first.click()
                page.get_by_test_id("automation-new").click()
                with page.expect_response(lambda response: response.url.endswith("/api/workbenches")
                                          and response.request.method == "POST") as created:
                    page.get_by_role("region", name="New Automation", exact=True).get_by_test_id("automation-starter-scratch").click()
                workbench_id = created.value.json()["workbench"]["id"]
                automation = page.locator(f"[id='workbench:{workbench_id}'][data-layer='window']")
                setup = automation.get_by_test_id("automation-setup")
                setup.wait_for()
                assert automation.get_by_test_id("automation-run-now").is_disabled()
                assert not automation.get_by_test_id("automation-newest").is_visible()
                draft = "Draft an update from the platform checkpoint."
                setup.get_by_role("textbox", name="What it does", exact=True).fill(draft)
                _selection_has_ink(setup.get_by_test_id("automation-setup-step-do"))
                _settle(page)
                _contained(automation)
                page.screenshot(path=str(SHOTS / f"automation-do-{width}.png"))
                report = _capture(page, automation, width, "automation-wizard")
                assert any(field.get("value") == draft for field in report["context"]["fields"])
                setup.get_by_test_id("automation-setup-next").click()
                setup.get_by_role("textbox", name="Find by name").wait_for()
                setup.get_by_test_id("automation-setup-back").click()
                assert setup.get_by_role("textbox", name="What it does", exact=True).input_value() == draft
                setup.get_by_test_id("automation-setup-next").click()
                setup.get_by_role("textbox", name="Find by name").fill("Platform")
                setup.get_by_role("button", name="Add Platform checkpoint", exact=True).click()
                setup.get_by_role("button", name="Remove Platform checkpoint", exact=True).wait_for()
                setup.get_by_test_id("automation-setup-next").click()
                setup.get_by_role("button", name="Add Claude Code", exact=True).click()
                setup.get_by_text("In use", exact=True).wait_for()
                page.screenshot(path=str(SHOTS / f"automation-with-{width}.png"))
                setup.get_by_test_id("automation-setup-next").click()
                setup.get_by_role("button", name="Only when I press Run now", exact=True).wait_for()
                setup.get_by_test_id("automation-setup-next").click()
                setup.get_by_role("button", name="Put it in Needs you", exact=True).click()
                setup.get_by_test_id("automation-setup-done").click()
                setup.wait_for(state="hidden")
                saved = _api(page, "GET", f"/api/workbenches/{workbench_id}", token=TOKEN)["workbench"]
                assert saved["instruction"] == draft
                assert saved["output_target"] == "needs_you"
                assert "note:wizard-source" in saved["sources"]
                assert saved["assignment_summary"]["chain"] == ["Claude Code"], saved
                assert saved["assignment_summary"]["profile_id"], saved
                assert not saved.get("last_run"), saved
                _contained(automation)
                page.screenshot(path=str(SHOTS / f"automation-finished-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.stop()
