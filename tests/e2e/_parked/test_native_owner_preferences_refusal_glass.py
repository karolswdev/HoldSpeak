# Parked: moved to settings.app.test.tsx (two recorded revision refusals, retained name, explicit Retry) and test_desk_settings.py::test_owner_name_refuses_stale_revisions_then_saves_current; no native browser behavior.
from pathlib import Path
from typing import Any
import pytest
from tests._evidence import evidence_dir
from tests.e2e.test_native_owner_preferences_glass import (
    _api, _ensure_build, _isolated_boot, _open_settings, _status,
    _no_global_saved_for_you, _wait_saved, SHOTS, TOKEN,
)

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

