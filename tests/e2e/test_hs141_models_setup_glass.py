"""HS-141 projected-model truth, migrated to Story 143's one Model Library glass.

The retired Phase-141 picker assigned the Thoughts pointer.  This successor
keeps its useful owner proof (server projection, one action seat, inert
selection, and two working widths) on the replacement availability surface.
The durable download/add walk remains in test_hs142_model_acquisition_glass.py.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="Model Library glass needs Playwright")
pytest.importorskip("fastapi.testclient", reason="Model Library glass needs web dependencies")

TOKEN = "hs141-models-setup-glass"


def _api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body]) => {
          const response = await fetch(path, {
            method,
            headers: {
              authorization: 'Bearer hs141-models-setup-glass',
              ...(body ? {'content-type': 'application/json'} : {}),
            },
            body: body ? JSON.stringify(body) : undefined,
          });
          return {status: response.status, payload: await response.json()};
        }""",
        [method, path, body],
    )
    assert result["status"] < 300, result
    return result["payload"]


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_models_setup_is_projected_truth_with_one_action_seat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from playwright.sync_api import sync_playwright
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    import holdspeak.services.inference_acquisition_service as acquisition_module
    import holdspeak.services.inference_setup_service as setup_module
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    existing_model = home / "Models" / "gguf" / "Qwen3-4B-Existing-Q6_K.gguf"
    existing_model.parent.mkdir(parents=True)
    existing_model.write_bytes(b"GGUF" + b"glass-existing-model")
    browser_cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    original_package_revision = setup_module._package_revision
    monkeypatch.setattr(
        setup_module,
        "_package_revision",
        lambda distribution, fallback: "0.3.34"
        if distribution == "llama-cpp-python"
        else original_package_revision(distribution, fallback),
    )
    monkeypatch.setattr(setup_module, "_package_available", lambda module: module == "llama_cpp")
    original_runtime_version = acquisition_module.importlib.metadata.version
    monkeypatch.setattr(
        acquisition_module.importlib.metadata,
        "version",
        lambda distribution: "0.3.34"
        if distribution == "llama-cpp-python"
        else original_runtime_version(distribution),
    )
    reset_database()

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
    )
    url = server.start()
    errors: list[str] = []
    console_errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            page.goto(f"{url}/profiles", wait_until="load")

            surface = page.locator(".model-library")
            surface.get_by_role("heading", name="Model Library", exact=True).wait_for(timeout=10_000)
            projection = _api(page, "GET", "/api/inference/model-library")
            before_settings = _api(page, "GET", "/api/settings")["thoughts"]["inference_target_id"]
            assert projection["schema"] == "ModelLibraryProjection@1"
            assert projection["rows"]
            assert str(home) not in str(projection)
            assert surface.get_by_role("tab", name="This device", exact=False).is_visible()
            assert surface.get_by_text("Models by job", exact=True).count() == 0
            assert surface.get_by_text("Runs on", exact=True).count() == 1

            surface.get_by_role("tab", name="This device", exact=False).click()
            group = surface.get_by_role("radiogroup", name="Model Library")
            group.wait_for()
            radios = group.get_by_role("radio")
            assert radios.count() >= 1
            assert radios.nth(0).is_checked()
            if radios.count() > 1:
                before = radios.nth(0).get_attribute("value")
                radios.nth(0).focus()
                radios.nth(0).press("ArrowRight")
                assert group.get_by_role("radio", checked=True).get_attribute("value") != before
            # Row selection only changes the displayed server projection; it
            # cannot reopen the retired Settings assignment writer.
            assert _api(page, "GET", "/api/settings")["thoughts"]["inference_target_id"] == before_settings

            action = surface.locator(".model-library-action-seat")
            assert action.count() == 1
            assert action.locator("button").count() <= 1
            assert surface.locator(".model-library-detail").get_attribute("aria-live") == "polite"
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            surface_body = page.locator(".desk-settings-window .desk-surface-body")
            if width == 393:
                for index in range(min(3, radios.count())):
                    box = radios.nth(index).locator("xpath=ancestor::label").bounding_box()
                    assert box and box["height"] >= 44
                action_box = action.bounding_box()
                assert action_box and action_box["x"] >= 0 and action_box["x"] + action_box["width"] <= width
            else:
                action_box = action.bounding_box()
                body_box = surface_body.bounding_box()
                assert action_box and body_box
                assert action_box["y"] >= body_box["y"]
                assert action_box["y"] + action_box["height"] <= body_box["y"] + body_box["height"]
            assert errors == []
            assert console_errors == []
            browser.close()
    finally:
        server.stop()
