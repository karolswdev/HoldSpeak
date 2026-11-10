"""ST7 Settings page proof in a real browser.

The old directory and wing glass is parked beside this file.  This proof
covers the settled one page at the two required sizes, including the legacy
Quiet hours entry point and the real heartbeat write.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import re

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="Settings page glass needs Playwright")

TOKEN = "st7-settings-page"
HEIGHT = {1440: 900, 393: 852}


def _open_page(page: Any, base: str, *, scope: str = "") -> Any:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    page.evaluate(
        """(scope) => sessionStorage.setItem(
          "hs.desk.staged-surface-open",
          JSON.stringify({key: "configure-settings", scope})
        )""",
        scope,
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator("#surface-settings [data-testid='settings-page']").wait_for(timeout=10_000)
    return page.locator("#surface-settings [data-testid='settings-page']")


def _assert_page_shape(page: Any, width: int) -> None:
    settings = page.locator("#surface-settings [data-testid='settings-page']")
    # The rail and pane order agree; no second hand-kept section inventory.
    assert settings.locator("[data-settings-section]").evaluate_all(
        "els => els.map(el => el.getAttribute('data-settings-section'))"
    ) == settings.locator("nav [data-rail-id]").evaluate_all(
        "els => els.map(el => el.getAttribute('data-rail-id'))"
    )
    geometry = settings.evaluate(
        """el => {
          const body = el.closest('.desk-surface-body');
          const index = el.querySelector('nav[aria-label="Settings sections"]').getBoundingClientRect();
          return {
            width: el.getBoundingClientRect().width,
            index: {x: index.x, width: index.width},
            documentOverflow: document.documentElement.scrollWidth > window.innerWidth,
            bodyOverflow: !!body && body.scrollWidth > body.clientWidth + 1,
          };
        }"""
    )
    assert geometry["width"] > 0, (width, geometry)
    assert not geometry["documentOverflow"], (width, geometry)
    assert not geometry["bodyOverflow"], (width, geometry)
    # One rail. At a narrow width it is hidden while a pane is open (Back shows it).
    assert settings.locator("nav[aria-label='Settings sections']").count() == 1
    assert page.get_by_role("tab").count() == 0
    assert page.get_by_role("button", name="Open Speak").count() == 0


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_settings_page_order_anchor_and_saved_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = evidence_dir("settings-page-st7")
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": HEIGHT[width]},
                reduced_motion="reduce",
            )
            page.on("pageerror", lambda error: errors.append(str(error)))
            settings = _open_page(page, base, scope="rhythm::quiet-hours")
            _settle(page)
            _assert_page_shape(page, width)

            # ST7 producer proof: the Settings page button opens the real
            # Engines host, and the hub records its canonical application and
            # surface id. Close it before exercising the Settings write.
            # Narrow: a pane opened by a scope returns where it came from (window
            # grammar): Settings does not hold the window's Back, so it closes the
            # window. Reopen Settings from the desk and choose This Mac on its rail.
            if width == 393:
                assert page.locator("#surface-settings [data-testid=settings-back]").count() == 0
                page.locator("#surface-settings .desk-gadget-close").click()
                page.locator("#surface-settings").wait_for(state="detached", timeout=10_000)
                _api(page, "POST", "/api/desk/windows/surface-settings/open", {}, token=TOKEN)
            settings.get_by_test_id("settings-index-engines").click()
            engine_window = page.locator("#surface-settings")
            engine_window.get_by_role("grid", name="Jobs", exact=True).wait_for(timeout=15_000)
            rows = _api(page, "GET", "/api/desk/windows", token=TOKEN)["windows"]
            engine_row = next(row for row in rows if row["id"] == "surface-settings")
            assert engine_row["app"] == "configure-settings", engine_row
            page.screenshot(path=str(shots / f"settings-engines-{width}.png"), full_page=False)
            _api(page, "POST", "/api/desk/windows/surface-settings/close", {}, token=TOKEN)
            engine_window.wait_for(state="detached", timeout=10_000)

            # Restore the legacy entry after visiting another category.
            _open_page(page, base, scope="rhythm::quiet-hours")
            notices = page.locator("[data-settings-section='notices']")
            notices.wait_for()
            anchor = notices.locator(".gadget-row[data-highlight]")
            anchor.wait_for(timeout=10_000)
            index_notice = settings.get_by_test_id("settings-index-notices")
            assert index_notice.get_attribute("aria-current") == "true"

            increase = page.get_by_role("button", name="Increase Quiet from", exact=True)
            increase.scroll_into_view_if_needed()
            before = int(page.get_by_role("spinbutton", name="Quiet from", exact=True).input_value())
            probe = increase.evaluate(
                """el => {
                  const r = el.getBoundingClientRect();
                  const p = [r.left + r.width / 2, r.top + r.height / 2];
                  const hit = document.elementFromPoint(p[0], p[1]);
                  return {rect: r.toJSON(), hit: hit === el || el.contains(hit)};
                }"""
            )
            assert probe["rect"]["width"] > 0 and probe["rect"]["height"] > 0, probe
            assert probe["hit"], (width, probe)
            increase.click()
            page.locator(".pref-status-bar").get_by_text(re.compile(r"^saved\b", re.I)).wait_for(timeout=10_000)
            saved = _api(page, "GET", "/api/settings/heartbeat", token=TOKEN)
            assert saved["quiet_hours"]["start"] == (before + 1) % 24, saved
            page.screenshot(path=str(shots / f"settings-page-{width}.png"), full_page=False)
            assert errors == [], errors
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(240)
def test_settings_palette_quiet_hours_opens_lit_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": HEIGHT[1440]}, reduced_motion="reduce")
            _open_page(page, base)
            page.get_by_role("button", name="Search ⌘K").click()
            search = page.get_by_role("combobox", name="Find, open or ask")
            search.fill("Quiet hours")
            option = page.locator('[id="desk-palette-option-settings:quiet-hours"]')
            option.wait_for(timeout=10_000)
            option.click()
            page.locator("[data-settings-section='notices'] .gadget-row[data-highlight]").wait_for(timeout=10_000)
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(240)
def test_builder_tools_preference_persists_between_two_browsers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings owns Builder tools; another browser reads the same hub value."""
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = evidence_dir("settings-page-st7")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            desktop = browser.new_page(viewport={"width": 1440, "height": HEIGHT[1440]}, reduced_motion="reduce")
            phone = browser.new_page(viewport={"width": 393, "height": HEIGHT[393]}, has_touch=True, is_mobile=True, reduced_motion="reduce")
            builder_puts: list[str | None] = []
            desktop.on(
                "request",
                lambda request: builder_puts.append(request.post_data)
                if request.method == "PUT" and request.url.endswith("/api/settings")
                else None,
            )

            desktop_settings = _open_page(desktop, base, scope="this-mac")
            switch = desktop.get_by_role("checkbox", name="Builder tools", exact=True)
            assert switch.is_checked() is False
            switch.check()
            desktop.wait_for_timeout(1_200)
            desktop.get_by_text(re.compile(r"^saved\b", re.I)).wait_for(timeout=10_000)
            saved = _api(desktop, "GET", "/api/settings", token=TOKEN)
            assert any('"builder_tools":true' in (payload or "") for payload in builder_puts), builder_puts
            assert saved.get("ui", {}).get("builder_tools") is True, saved
            desktop.screenshot(path=str(shots / "builder-tools-on-1440.png"), full_page=False)

            phone_settings = _open_page(phone, base, scope="this-mac")
            phone_switch = phone.get_by_role("checkbox", name="Builder tools", exact=True)
            assert phone_switch.is_checked() is True
            phone.locator(".desk-tools-launch").first.tap()
            search = phone.get_by_role("combobox", name="Find, open or ask")
            search.fill("Processes")
            phone.get_by_role("option", name="Processes App", exact=True).wait_for(timeout=10_000)
            phone.screenshot(path=str(shots / "builder-tools-search-393.png"), full_page=False)
            search.press("Escape")

            phone_switch.uncheck()
            phone.wait_for_timeout(1_200)
            phone.get_by_text(re.compile(r"^saved\b", re.I)).wait_for(timeout=10_000)
            cleared = _api(phone, "GET", "/api/settings", token=TOKEN)
            assert cleared.get("ui", {}).get("builder_tools") is False, cleared
            desktop.reload(wait_until="load")
            _normal_chair(desktop)
            _open_page(desktop, base, scope="this-mac")
            assert desktop.get_by_role("checkbox", name="Builder tools", exact=True).is_checked() is False
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_engines_pane_chain_editor_library_and_old_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Every assignment write is on this rig's isolated DB, with fake CLIs."""
    from playwright.sync_api import sync_playwright, expect
    from tests.fixtures.fake_agent_cli import install_fake_agent_clis

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    fake_bin = install_fake_agent_clis(tmp_path / "bin", names=("codex", "gemini"))
    monkeypatch.setenv("PATH", f"{fake_bin}:/usr/bin:/bin")
    monkeypatch.setenv("HOLDSPEAK_CLI_ENGINES", "on")
    shots = evidence_dir("engines-settings-native")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": HEIGHT[width]}, reduced_motion="reduce")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            _open_page(page, base, scope="engines")
            entries = []
            for preset in ("codex", "gemini"):
                added = _api(page, "POST", "/api/inference/model-library/connect-cli-engine", {"draft": {
                    "request_id": f"browser-{preset}", "profile_id": f"agent-{preset}",
                    "expected_profile_revision": 0, "preset": preset}}, token=TOKEN)
                provider = added["provider"]
                entries.append({"profile_id": provider["profile_id"], "profile_revision": provider["profile_revision"]})
            _api(page, "POST", "/api/inference/assignments/set", {
                "command_id": "browser-isolated-chain", "scope": {"kind": "global"},
                "expected_revision": 0, "entries": entries}, token=TOKEN)
            # /models is an old door to this same Settings pane.
            page.goto(f"{base}/models?token={TOKEN}", wait_until="load")
            row = page.get_by_test_id("settings-job-summaries")
            expect(row.get_by_role("combobox")).to_have_value("inherit", timeout=15_000)
            assert page.locator("#surface-engines").count() == 0
            assert row.locator("button").count() == 0
            choice = page.get_by_role("combobox", name="Everything else engines", exact=True)
            expect(choice.locator("option:checked")).to_have_text("Codex, then Gemini CLI")
            _settle(page)
            page.screenshot(path=str(shots / f"assignments-{width}.png"))
            choice.select_option("order")
            editor = page.get_by_role("region", name="Everything else: engine order", exact=True)
            expect(editor).to_contain_text("Codex")
            page.screenshot(path=str(shots / f"editor-{width}.png"))
            with page.expect_request(lambda request: request.url.endswith("/api/concierge/probe") and request.method == "POST") as probe:
                editor.get_by_role("button", name="Try it", exact=True).click()
            assert probe.value.post_data_json["expectedProfileIds"] == ["agent-codex", "agent-gemini"]
            expect(editor.locator("output")).to_contain_text("Completed", timeout=15_000)
            editor.get_by_text("Gemini CLI", exact=True).click()
            editor.get_by_role("button", name="Move up", exact=True).click()
            expect(page.get_by_test_id("settings-engines-receipt")).to_contain_text("Gemini CLI, then Codex")
            roster = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            global_row = next(item for item in roster["rows"] if item["id"] == "global")
            assert [entry["profile_id"] for entry in global_row["assignment"]["entries"]] == ["agent-gemini", "agent-codex"]
            editor.get_by_role("button", name="Close", exact=True).click()
            page.get_by_role("button", name="Model library", exact=True).click()
            library = page.get_by_test_id("settings-engines-library")
            expect(library.get_by_test_id("settings-engine-agent-codex")).to_be_visible()
            _settle(page)
            page.screenshot(path=str(shots / f"library-{width}.png"))
            library.get_by_role("button", name="Add an engine", exact=True).click()
            library.get_by_test_id("runson-kind-lan").click()
            expect(library.get_by_role("textbox", name="Server address", exact=True)).to_be_visible()
            assert errors == [], errors
            browser.close()
    finally:
        server.stop()
