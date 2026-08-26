"""HS-143-12 — real-hub Model Library glass at the owner working widths."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="Model Library glass needs Playwright")

TOKEN = "hs143-model-library-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm" / "roadmap" / "holdspeak" / "phase-143-intelligence-router" / "assets" / "story-12-shots"


def _api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body]) => {
          const response = await fetch(path, {
            method,
            headers: {authorization: 'Bearer hs143-model-library-glass',
                      ...(body ? {'content-type': 'application/json'} : {})},
            body: body ? JSON.stringify(body) : undefined,
          });
          return {status: response.status, payload: await response.json()};
        }""",
        [method, path, body],
    )
    assert result["status"] < 300, result
    return result["payload"]


def _assert_in_viewport(box: dict[str, float] | None, width: int) -> None:
    assert box is not None
    assert box["x"] >= 0
    assert box["x"] + box["width"] <= width + 1
    assert box["y"] >= 0
    assert box["y"] < 900


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.parametrize("state", ["populated", "empty", "error"])
def test_model_library_glass_real_hub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, state: str,
) -> None:
    from playwright.sync_api import sync_playwright
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.services.errors import ServiceError
    from holdspeak.services.model_library_service import ModelLibraryApplicationService
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    original_projection = ModelLibraryApplicationService.get_library

    if state != "populated":
        def shaped_projection(self: ModelLibraryApplicationService, principal: Any) -> dict[str, Any]:
            if state == "error":
                raise ServiceError("model_library_glass_error", "Model Library is unavailable.", context={"status": 503})
            projection = original_projection(self, principal)
            return {**projection, "rows": []}

        monkeypatch.setattr(ModelLibraryApplicationService, "get_library", shaped_projection)

    home = tmp_path / "home"
    home.mkdir()
    browser_cache = Path(os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH",
        Path.home() / "Library/Caches/ms-playwright",
    ))
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
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            page.goto(f"{url}/profiles", wait_until="load")

            surface = page.locator(".model-library")
            surface.wait_for()
            shot = SHOTS / f"model-library-{state}-{width}.png"

            if state == "error":
                surface.get_by_role("alert").wait_for()
                assert "Model Library is unavailable." in surface.inner_text()
            elif state == "empty":
                surface.get_by_text("No models", exact=True).wait_for()
                assert surface.get_by_role("button", name="Add model", exact=True).count() == 1
            else:
                surface.get_by_role("heading", name="Model Library", exact=True).wait_for()
                rows = surface.locator(".model-library-row")
                action = surface.locator(".model-library-action-seat")
                title = surface.locator(".model-library-title")
                tabs = surface.locator(".model-library-tabs")
                assert rows.count() >= 6
                assert action.count() == 1
                assert action.locator("button").count() <= 1
                _assert_in_viewport(title.bounding_box(), width)
                _assert_in_viewport(tabs.bounding_box(), width)
                required_rows = 6 if width == 1440 else 3
                for index in range(required_rows):
                    box = rows.nth(index).bounding_box()
                    _assert_in_viewport(box, width)
                    if width == 393:
                        assert box and box["height"] >= 44
                action_box = action.bounding_box()
                _assert_in_viewport(action_box, width)
                if width == 393:
                    button = action.locator("button")
                    if button.count():
                        button_box = button.bounding_box()
                        assert button_box and button_box["height"] >= 44
                dock = page.locator(".desk-dock")
                if dock.count():
                    dock_box = dock.bounding_box()
                    if dock_box and action_box:
                        assert action_box["y"] + action_box["height"] <= dock_box["y"] or action_box["y"] >= dock_box["y"] + dock_box["height"]

            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.screenshot(path=str(shot), full_page=False)
            assert shot.exists() and shot.stat().st_size > 0
            assert errors == []
            browser.close()
    finally:
        server.stop()
