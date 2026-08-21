"""Isolated-HOME two-width glass for the owner-facing AI setup room."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="AI setup glass needs Playwright")
pytest.importorskip("fastapi.testclient", reason="AI setup glass needs web dependencies")

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
def test_models_setup_is_a_clear_owner_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    browser_cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
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

            heading = page.get_by_role("heading", name="Choose your AI", exact=True)
            heading.wait_for(timeout=10000)
            setup = page.locator(".models-setup")
            assert setup.get_by_text("This device", exact=True).is_visible()
            assert setup.get_by_text("Choose AI for each job", exact=True).is_visible()
            assert setup.get_by_text("Runs on", exact=True).count() == 0
            assert setup.get_by_role("button", name="SET UP THIS DEVICE", exact=True).is_visible()
            assert setup.get_by_role("button", name="USE HOSTED AI", exact=True).is_visible()
            assert setup.get_by_role("heading", name="OpenRouter Qwen presets", exact=True).is_visible()
            for choice in ["Quick Qwen", "Balanced Qwen", "Deep Qwen"]:
                assert setup.get_by_role("heading", name=choice, exact=True).is_visible()
            connections = setup.get_by_text("AI connections", exact=True).locator("xpath=ancestor::details")
            assert connections.get_attribute("open") is None
            page.screenshot(path=f"/tmp/holdspeak-choose-your-ai-{width}.png", full_page=False)

            setup.get_by_placeholder("sk-or-v1-…").fill("glass-only-openrouter-key")
            balanced = setup.get_by_role("heading", name="Balanced Qwen", exact=True).locator("xpath=ancestor::article")
            balanced.get_by_role("button", name="ADD & USE", exact=True).click()
            setup.get_by_text("OpenRouter · Balanced Qwen selected for Thoughts & notes.", exact=True).wait_for()
            page.wait_for_timeout(900)
            config = _api(page, "GET", "/api/settings")
            assert config["thoughts"]["inference_target_id"] == "preset_openrouter_qwen35_35b_a3b"
            targets = _api(page, "GET", "/api/inference-targets")["targets"]
            selected = next(row for row in targets if row["id"] == "preset_openrouter_qwen35_35b_a3b")
            assert selected["model"] == "qwen/qwen3.5-35b-a3b"
            assert selected["secret"] == {"required": True, "present": True}
            assert "glass-only-openrouter-key" not in str(targets)
            balanced.scroll_into_view_if_needed()
            assert balanced.get_by_role("button", name="IN USE", exact=True).is_visible()
            page.screenshot(path=f"/tmp/holdspeak-choose-your-ai-preset-{width}.png", full_page=False)

            setup.get_by_role("button", name="DEFINE YOUR OWN PROVIDER", exact=True).click()
            assert connections.get_attribute("open") is not None
            assert setup.get_by_text("Define any OpenAI-compatible provider, private endpoint, paired device, or mesh node here.", exact=True).is_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            if width == 393:
                for label in ["SET UP THIS DEVICE", "USE HOSTED AI", "DEFINE YOUR OWN PROVIDER"]:
                    box = setup.get_by_role("button", name=label, exact=True).bounding_box()
                    assert box and box["height"] >= 44
                preset_box = balanced.get_by_role("button", name="IN USE", exact=True).bounding_box()
                assert preset_box and preset_box["height"] >= 44
            page.screenshot(path=f"/tmp/holdspeak-choose-your-ai-configured-{width}.png", full_page=False)
            assert errors == []
            assert console_errors == []
            browser.close()
    finally:
        server.stop()
