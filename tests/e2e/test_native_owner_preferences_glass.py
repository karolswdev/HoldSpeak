"""P08 Settings You: real desk receipts, retained edits, and local specimen."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from .glass_infra import _api, _boot, _ensure_build, _normal_chair
from .test_desk_sweep import TARGET_JS

pytest.importorskip("playwright.sync_api", reason="P08 glass needs Playwright")

TOKEN = "native-owner-preferences"
HEIGHT = {1440: 900, 393: 852}
SHOTS = "native-preferences-wave2"


def _isolated_boot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    # DeliveryRegistry freezes this path at import, before _boot changes HOME.
    # Override it before starting this test's hub so no later rig reads our DB.
    import holdspeak.delivery.registry as registry_module

    monkeypatch.setattr(
        registry_module, "DEFAULT_REGISTRY_PATH",
        tmp_path / "home" / ".holdspeak" / "delivery_sources.json",
    )
    return _boot(tmp_path, monkeypatch, token=TOKEN)


def _open_settings(page: Any, base: str) -> Any:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    page.evaluate(
        """() => sessionStorage.setItem('hs.desk.staged-surface-open',
          JSON.stringify({key:'configure-settings', scope:'you'}))"""
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    you = page.locator("#surface-settings [data-settings-section='you']")
    you.get_by_test_id("settings-owner-name").get_by_role("textbox").wait_for(timeout=15_000)
    return you


def _status(you: Any, field: str) -> str:
    # Window grammar 2026-10-24: no pill per field; the field keeps its word.
    return (you.get_by_test_id(f"settings-owner-{field}").get_attribute("data-save-state") or "").upper()


def _bar(page: Any) -> str:
    return page.locator("#surface-settings .pref-status-bar").inner_text()


def _wait_saved(page: Any, field: str, scope: str = "") -> None:
    page.wait_for_function(
        "([scope, field]) => document.querySelector(`${scope} [data-testid=settings-owner-${field}]`)"
        "?.getAttribute('data-save-state') === 'Saved'",
        arg=[scope, field], timeout=10_000,
    )


def _section(page: Any, section: str) -> None:
    """Choose a category; at a narrow width the pane's Back shows the rail first."""
    back = page.locator("#surface-settings [data-testid=settings-back]")
    if back.is_visible():
        back.click()
    page.get_by_test_id(f"settings-index-{section}").click()


def _target_check(page: Any, selector: str) -> None:
    assert page.evaluate(TARGET_JS, selector) == [], page.evaluate(TARGET_JS, selector)


def _no_global_saved_for_you(page: Any) -> None:
    """While a You field is unsaved, the bar never says Saved for it."""
    # Case matters: "Not saved" is the honest refusal, "Saved …" the receipt.
    assert "Saved" not in _bar(page), _bar(page)


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_real_settings_you_edit_alias_and_section_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """The field, hub writer, keyboard, and section return agree on one value."""
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    shots = evidence_dir(SHOTS)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": HEIGHT[width]},
                has_touch=width == 393, is_mobile=width == 393,
                reduced_motion="reduce",
            )
            page.on("pageerror", lambda error: errors.append(str(error)))
            you = _open_settings(page, base)
            if width == 393:
                # A pane opened by a scope returns where it came from (window
                # grammar): the window's Back closes Settings, no settings-back.
                # Reopen it from the desk and reach You from the rail, so the
                # section returns below run the rail's Back.
                assert page.locator("#surface-settings [data-testid=settings-back]").count() == 0
                page.locator("#surface-settings .desk-gadget-close").click()
                page.locator("#surface-settings").wait_for(state="detached", timeout=10_000)
                _api(page, "POST", "/api/desk/windows/surface-settings/open", {}, token=TOKEN)
                page.get_by_test_id("settings-index-you").click()
                you.get_by_test_id("settings-owner-name").get_by_role("textbox").wait_for(timeout=15_000)
            name = you.get_by_test_id("settings-owner-name").get_by_role("textbox")
            aliases = you.get_by_test_id("settings-owner-aliases").get_by_role("textbox")
            name.fill("Karol Architect")
            assert _status(you, "name") == "EDITED"
            _no_global_saved_for_you(page)
            assert _api(page, "GET", "/api/settings", token=TOKEN).get("owner", {}).get("name") != "Karol Architect"
            _wait_saved(page, "name")
            assert _api(page, "GET", "/api/settings", token=TOKEN)["owner"]["name"] == "Karol Architect"
            page.locator("#surface-settings .pref-status-bar").get_by_text("Saved just now").wait_for(timeout=10_000)

            aliases.fill("Ari")
            assert _status(you, "aliases") == "EDITED"
            assert "Ari" not in _api(page, "GET", "/api/settings", token=TOKEN)["owner"]["aliases"]
            aliases.press("Enter")
            you.get_by_test_id("settings-owner-aliases").get_by_text("Ari", exact=True).wait_for()
            _wait_saved(page, "aliases")
            assert "Ari" in _api(page, "GET", "/api/settings", token=TOKEN)["owner"]["aliases"]

            # Leaving the section while raw alias text is in the field must
            # commit it through the same writer, then show it on return.
            aliases.fill("Architect Alias")
            assert _status(you, "aliases") == "EDITED"
            _section(page, "speak")
            _section(page, "you")
            you.get_by_test_id("settings-owner-aliases").get_by_text("Architect Alias", exact=True).wait_for()
            _wait_saved(page, "aliases")
            assert "Architect Alias" in _api(page, "GET", "/api/settings", token=TOKEN)["owner"]["aliases"]

            name.fill("Karol Return")
            assert _status(you, "name") == "EDITED"
            _no_global_saved_for_you(page)
            _section(page, "speak")
            assert "SAVED" in _bar(page).upper()
            _section(page, "you")
            name = you.get_by_test_id("settings-owner-name").get_by_role("textbox")
            assert name.input_value() == "Karol Return"
            _wait_saved(page, "name")
            assert _api(page, "GET", "/api/settings", token=TOKEN)["owner"]["name"] == "Karol Return"
            if width == 393:
                _target_check(page, "#surface-settings [data-settings-section='you']")
            page.screenshot(path=str(shots / f"settings-you-{width}.png"), full_page=False)
            assert not errors, errors
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(240)
def test_settings_you_refusal_retains_name_then_retry_saves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two named revision refusals leave the current draft and a live Retry."""
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    shots = evidence_dir(SHOTS)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
            you = _open_settings(page, base)
            original = _api(page, "GET", "/api/settings", token=TOKEN)
            revision = original.get("_revision")
            attempts: list[str] = []

            def refuse_first_two(route: Any) -> None:
                attempts.append(route.request.post_data or "")
                if len(attempts) <= 2:
                    route.fulfill(status=409, content_type="application/json", body=(
                        '{"error":"Revision changed","revision":"' + str(revision) + '"}'
                    ))
                else:
                    route.continue_()

            page.route("**/api/settings", lambda route: refuse_first_two(route)
                       if route.request.method == "PUT" else route.continue_())
            name = you.get_by_test_id("settings-owner-name").get_by_role("textbox")
            name.fill("Karol Retained")
            page.get_by_role("button", name="Retry", exact=True).wait_for(timeout=10_000)
            assert _status(you, "name") == "NOT SAVED"
            _no_global_saved_for_you(page)
            assert name.input_value() == "Karol Retained"
            assert _api(page, "GET", "/api/settings", token=TOKEN).get("owner", {}).get("name") != "Karol Retained"
            page.screenshot(path=str(shots / "settings-you-refused-1440.png"), full_page=False)
            page.get_by_role("button", name="Retry", exact=True).click()
            _wait_saved(page, "name")
            assert len(attempts) >= 3, attempts
            assert _api(page, "GET", "/api/settings", token=TOKEN)["owner"]["name"] == "Karol Retained"
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(240)
def test_settings_you_newer_edit_waits_for_old_ack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A held real first PUT cannot label the newer local edit Saved."""
    from playwright.async_api import async_playwright

    async def run() -> None:
        _ensure_build()
        server, base = _isolated_boot(tmp_path, monkeypatch)
        gate = asyncio.Event()
        latest_gate = asyncio.Event()
        first_started = asyncio.Event()
        latest_started = asyncio.Event()
        writes: list[str] = []
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch()
                page = await browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
                await page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                await page.evaluate("""async token => {const r=await fetch('/api/setup/onboarding',
                  {method:'PUT',headers:{authorization:`Bearer ${token}`,'content-type':'application/json'},
                   body:JSON.stringify({disposition:'completed'})}); if(!r.ok) throw Error(r.status)}""", TOKEN)
                await page.evaluate("""() => sessionStorage.setItem('hs.desk.staged-surface-open',
                  JSON.stringify({key:'configure-settings',scope:'you'}))""")
                await page.reload(wait_until="load")
                chair = page.locator(".chair")
                await chair.wait_for()
                if await chair.evaluate("el => el.classList.contains('chair-first-value')"):
                    await page.get_by_role("button", name="Continue later").click()
                await page.locator(".chair:not(.chair-first-value)").wait_for()
                you = page.locator("#surface-settings [data-settings-section='you']")
                name = you.get_by_test_id("settings-owner-name").get_by_role("textbox")
                await name.wait_for(timeout=15_000)

                async def hold_first(route: Any) -> None:
                    if route.request.method != "PUT":
                        await route.continue_()
                        return
                    writes.append(route.request.post_data or "")
                    if len(writes) == 1:
                        first_started.set()
                        await gate.wait()
                    elif len(writes) == 2:
                        latest_started.set()
                        await latest_gate.wait()
                    await route.continue_()

                await page.route("**/api/settings", hold_first)
                await name.fill("Karol First")
                await asyncio.wait_for(first_started.wait(), timeout=10)
                row = you.get_by_test_id("settings-owner-name")
                assert await row.get_attribute("data-save-state") == "Saving"
                assert "Saving" in await page.locator("#surface-settings .pref-status-bar").inner_text()
                assert "SAVED" not in (await page.locator("#surface-settings .pref-status-bar").inner_text()).upper()
                await name.fill("Karol Latest")
                assert await row.get_attribute("data-save-state") == "Edited"
                assert "SAVED" not in (await page.locator("#surface-settings .pref-status-bar").inner_text()).upper()
                gate.set()
                await asyncio.wait_for(latest_started.wait(), timeout=10)
                assert await name.input_value() == "Karol Latest"
                assert await row.get_attribute("data-save-state") == "Saving"
                interim = await page.evaluate("""async token => (await (await fetch('/api/settings',
                  {headers:{authorization:`Bearer ${token}`}})).json())""", TOKEN)
                assert interim["owner"]["name"] == "Karol First", (interim["owner"], writes)
                latest_gate.set()
                await page.wait_for_function(
                    "() => document.querySelector('[data-testid=settings-owner-name]')?.getAttribute('data-save-state') === 'Saved'",
                    timeout=15_000,
                )
                assert await name.input_value() == "Karol Latest"
                settings = await page.evaluate("""async token => (await (await fetch('/api/settings',
                  {headers:{authorization:`Bearer ${token}`}})).json())""", TOKEN)
                assert settings["owner"]["name"] == "Karol Latest", (settings["owner"], writes)
                assert len(writes) >= 2, writes
                await browser.close()
        finally:
            gate.set()
            latest_gate.set()
            server.stop()

    asyncio.run(run())


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_components_settings_you_uses_local_writer_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Components renders the same field pattern through fixture-only IO."""
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    shots = evidence_dir(SHOTS)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": HEIGHT[width]},
                has_touch=width == 393, is_mobile=width == 393,
                reduced_motion="reduce",
            )
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            page.goto(f"{base}/design/components?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            if width == 393:
                # #1521: on a narrow surface the Components rail is the first
                # view; the Forms group opens with Back.
                page.get_by_test_id("reference-group-forms").click()
            reference = page.get_by_test_id("reference-owner-preferences")
            reference.wait_for(timeout=15_000)
            state = page.get_by_role("combobox", name="Example state")
            assert state.input_value() == "saved"
            assert "Local specimen" in reference.get_by_test_id("settings-status").inner_text()
            writes: list[str] = []
            page.on("request", lambda request: writes.append(request.post_data or "")
                    if request.method == "PUT" and request.url.endswith("/api/settings") else None)

            state.select_option("edited")
            reference.get_by_test_id("settings-owner-name").get_by_role("textbox").wait_for()
            assert _status(reference, "name") == "EDITED"
            state.select_option("saving")
            reference.get_by_role("button", name="Complete local write").wait_for()
            assert _status(reference, "name") == "SAVING"
            reference.get_by_role("button", name="Complete local write").click()
            _wait_saved(page, "name", "[data-testid=reference-owner-preferences]")
            state.select_option("refused")
            reference.get_by_role("button", name="Retry", exact=True).wait_for(timeout=10_000)
            assert _status(reference, "name") == "NOT SAVED"
            assert reference.get_by_test_id("settings-owner-name").get_by_role("textbox").input_value() == "Karol A"
            page.screenshot(path=str(shots / f"components-settings-refused-{width}.png"), full_page=False)
            reference.get_by_role("button", name="Retry", exact=True).click()
            _wait_saved(page, "name", "[data-testid=reference-owner-preferences]")
            assert reference.get_by_test_id("settings-owner-name").get_by_role("textbox").input_value() == "Karol A"
            state.select_option("retried")
            _wait_saved(page, "name", "[data-testid=reference-owner-preferences]")
            assert not writes, writes
            if width == 393:
                _target_check(page, "[data-testid='reference-owner-preferences']")
            page.screenshot(path=str(shots / f"components-settings-{width}.png"), full_page=False)
            assert not errors, errors
            browser.close()
    finally:
        server.stop()
