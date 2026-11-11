"""Owner's Settings and Automation builder reports, on real Firefox glass."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from .test_automation_glass import _new_automation, _object_edit
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows, wait_for_hub
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


def _selection_has_ink(
    button: Any,
    *,
    background_token: str = "--wb-sel",
    border_token: str | None = None,
    aria_current: str | None = None,
    aria_pressed: str | None = None,
) -> None:
    border_expression = "null" if border_token is None else repr(border_token)
    facts = button.evaluate("""el => {
      const probe = document.createElement('span');
      probe.hidden = true;
      probe.style.color = `var(%s)`;
      el.append(probe);
      const expected = getComputedStyle(probe).color;
      const border = %s;
      const expectedBorder = border ? (() => {
        probe.style.color = `var(${border})`;
        return getComputedStyle(probe).color;
      })() : null;
      const cs = getComputedStyle(el);
      const result = {
        actual: cs.backgroundColor,
        expected,
        actualBorder: cs.borderTopColor,
        expectedBorder,
        ariaCurrent: el.getAttribute('aria-current'),
        ariaPressed: el.getAttribute('aria-pressed'),
      };
      probe.remove();
      return result;
    }""" % (background_token, border_expression))
    assert facts["actual"] == facts["expected"], facts
    if border_token is not None:
        assert facts["actualBorder"] == facts["expectedBorder"], facts
    if aria_current is not None:
        assert facts["ariaCurrent"] == aria_current, facts
    if aria_pressed is not None:
        assert facts["ariaPressed"] == aria_pressed, facts


def _capture(page: Any, window: Any, width: int, stem: str) -> dict[str, Any]:
    page.evaluate("window.__feedbackAudioSeconds = 0")
    window.locator("button[aria-label^='Give feedback on ']").click()
    page.locator("[data-ui-feedback]").get_by_text("Recording", exact=True).wait_for()
    page.wait_for_function("window.__feedbackAudioSeconds >= 0.12", timeout=30_000)
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
                page.add_init_script("""(() => {
                  const NativeNode = window.AudioWorkletNode;
                  window.AudioWorkletNode = class extends NativeNode {
                    constructor(context, name, options) {
                      super(context, name, options);
                      if (name === 'holdspeak-capture') {
                        this.port.addEventListener('message', event => {
                          window.__feedbackAudioSeconds = (window.__feedbackAudioSeconds || 0)
                            + event.data.length / context.sampleRate;
                        });
                        this.port.start();
                      }
                    }
                  };
                })()""")
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

                def section(name: str) -> None:
                    # Window grammar: at a narrow width the rail is the first
                    # view and the pane's Back returns to it.
                    back = settings.get_by_test_id("settings-back")
                    if back.is_visible():
                        back.click()
                    settings.get_by_test_id(f"settings-index-{name}").click()

                if width == 393:
                    settings.get_by_test_id("settings-index-you").wait_for()
                    assert not settings.get_by_role("textbox", name="Your name", exact=True).is_visible()
                    page.screenshot(path=str(SHOTS / f"settings-rail-{width}.png"))
                    section("you")
                    # One Back: the window's title-bar Back returns the pane to the rail.
                    back = settings.get_by_test_id("settings-back")
                    assert back.count() == 1 and "desk-gadget-close" in (back.get_attribute("class") or "")
                settings.get_by_role("textbox", name="Your name", exact=True).wait_for()
                assert settings.locator("[data-settings-section]:visible").count() == 1
                assert settings.locator("[data-settings-section]:visible").get_attribute("data-settings-section") == "you"
                you_row = settings.get_by_test_id("settings-index-you")
                assert you_row.get_attribute("aria-current") == "true"
                if width == 1440:
                    _selection_has_ink(you_row, aria_current="true")
                for image in settings.locator(".surface-rail img").all():
                    page.wait_for_function("el => el.complete && el.naturalWidth > 0", arg=image.element_handle())
                assert settings.locator(".surface-rail img").count() == settings.locator("[data-settings-section]").count()
                # A real category press blurs and commits an alias. It must still
                # be present when the owner returns to You.
                alias = settings.get_by_test_id("settings-owner-aliases").get_by_role("textbox")
                alias.fill("Architect draft")
                section("speak")
                assert not settings.get_by_role("textbox", name="Your name", exact=True).is_visible()
                assert settings.locator("[data-settings-section]:visible").count() == 1
                section("you")
                settings.get_by_test_id("settings-owner-aliases").get_by_text("Architect draft", exact=True).wait_for()
                _settle(page)
                _contained(settings)
                page.screenshot(path=str(SHOTS / f"settings-you-{width}.png"))
                report = _capture(page, settings, width, "settings-categories")
                assert report["context"]["owner"]["window_id"] == "surface-settings"

                section("speak")
                language = settings.get_by_role("combobox", name="Language", exact=True)
                language.click()
                popup = page.get_by_role("listbox", name="Language", exact=True)
                popup.wait_for()
                _contained(settings)
                page.screenshot(path=str(SHOTS / f"settings-dropdown-{width}.png"))
                popup.get_by_role("option", name="English (en)", exact=True).click()
                wait_for_hub(page, "/api/settings",
                             lambda payload: (payload.get("model") or {}).get("language") == "en", token=TOKEN)
                assert language.input_value() == "en"
                settings.locator(".desk-gadget-close").click()

                page.get_by_role("button", name="Go", exact=True).first.click()
                page.locator("nav[aria-label='Go menu']").get_by_role("menuitem", name="Automations").first.click()
                _new_automation(page)
                with page.expect_response(lambda response: response.url.endswith("/api/workbenches")
                                          and response.request.method == "POST") as created:
                    page.get_by_role("button", name="Create", exact=True).click()
                workbench_id = created.value.json()["workbench"]["id"]
                app = page.locator("#surface-workbenches")
                app.get_by_test_id("automation-setup").wait_for()
                app.get_by_role("button", name="Cancel", exact=True).click()
                app.locator(f'[data-object-id="{workbench_id}"]').dblclick()
                automation = page.locator(f"[id='workbench:{workbench_id}']")
                automation.get_by_test_id("automation-summary").wait_for()
                assert automation.get_by_test_id("automation-run-now").is_disabled()
                assert not automation.get_by_test_id("automation-reading").is_visible()
                draft = "Draft an update from the platform checkpoint."
                _object_edit(page, automation, "Do")
                editor = page.get_by_test_id("automation-setup")
                editor.get_by_role("textbox", name="What it does", exact=True).fill(draft)
                editor.get_by_role("button",name="Save",exact=True).click()
                editor.wait_for(state="hidden")
                # Every part uses the same editor for a new and a saved automation.
                _object_edit(page, automation, "Do")
                assert page.get_by_role("textbox", name="What it does", exact=True).input_value() == draft
                page.get_by_role("button", name="Cancel", exact=True).click()
                _settle(page)
                _contained(automation)
                page.screenshot(path=str(SHOTS / f"automation-do-{width}.png"))
                report = _capture(page, automation, width, "automation-summary")
                assert draft.removesuffix(".") in report["context"]["owner"]["window_text"]
                _object_edit(page, automation, "About")
                automation.get_by_role("textbox", name="Find by name").fill("Platform")
                automation.get_by_role("row",name="Platform checkpoint",exact=True).dblclick()
                automation.get_by_role("checkbox",name="Platform checkpoint",exact=True).wait_for()
                automation.get_by_role("button",name="Done",exact=True).click()
                _object_edit(page, automation, "With")
                automation.get_by_role("combobox",name="With",exact=True).select_option(label="Add Claude Code")
                automation.get_by_role("button",name="Save",exact=True).click()
                automation.get_by_test_id("automation-summary").wait_for()
                page.screenshot(path=str(SHOTS / f"automation-with-{width}.png"))
                _object_edit(page, automation, "When")
                automation.get_by_role("combobox",name="When",exact=True).select_option("manual")
                automation.get_by_role("button",name="Save",exact=True).click()
                automation.get_by_test_id("automation-summary").wait_for()
                _object_edit(page, automation, "Put it in")
                automation.get_by_role("combobox",name="Put it in",exact=True).select_option("needs_you")
                automation.get_by_role("button",name="Save",exact=True).click()
                automation.get_by_test_id("automation-summary").wait_for()
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
