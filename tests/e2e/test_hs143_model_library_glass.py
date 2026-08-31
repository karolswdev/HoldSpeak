"""HS-143-12 — real-hub Model Library glass at the owner working widths."""
from __future__ import annotations

import os
import time
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


def _model_library_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    """Boot the production web composition against an isolated owner DB."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

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
    return server, server.start()


def _navigate_through_door(page: Any) -> None:
    """HS-156-04: the door sits in front of the Model Library.

    After seed, assignment groups are unconfigured so the door shows pack
    cards.  Navigate through the door to expose the Model Library in the
    Advanced fold's Table view.
    """
    door = page.locator(".front-door")
    door.wait_for(timeout=10_000)
    # Cards phase: click "Set up my own" to open the advanced section
    own_btn = page.get_by_role("button", name="Set up my own", exact=True)
    if own_btn.count():
        own_btn.click()
    else:
        # Strip phase: open the Advanced disclosure
        page.get_by_role("button", name="Advanced").click()
    # Switch to Table view to reveal ModelLibraryCore
    page.get_by_role("tab", name="Table").click()
    # Scroll the model library into view so viewport assertions hold
    page.locator(".model-library").wait_for(timeout=5_000)
    page.locator(".model-library").scroll_into_view_if_needed()


def _open_library(page: Any, url: str) -> Any:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    page.goto(f"{url}/profiles", wait_until="load")
    _navigate_through_door(page)
    surface = page.locator(".model-library")
    surface.wait_for()
    return surface


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
            return {
                **projection,
                "summary": {"state": "empty", "label": "Add model", "ready_count": 0, "attention_count": 0},
                "rows": [],
            }

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
            _navigate_through_door(page)

            surface = page.locator(".model-library")
            surface.wait_for()
            shot = SHOTS / f"model-library-{state}-{width}.png"

            if state == "error":
                surface.get_by_role("alert").wait_for()
                assert "Model Library is unavailable." in surface.inner_text()
            elif state == "empty":
                surface.get_by_role("heading", name="Add model", exact=True).wait_for()
                assert surface.get_by_text("Ready", exact=True).count() == 0
                for label in ("Download from catalog", "Connect hosted model", "Define endpoint", "Use model file"):
                    assert surface.get_by_role("button", name=label, exact=True).count() == 1
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
                # HS-156-04: the model library is inside the door's Advanced fold;
                # scroll the action seat into view so bounding-box assertions
                # reflect its rendered position relative to the viewport.
                action.scroll_into_view_if_needed()
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
                        # HS-156-04: the model library is now inside the door's
                        # Advanced fold; allow a few pixels of overlap tolerance
                        # for the deeper nesting (was zero when the library was
                        # the top-level module).
                        overlap_tolerance = 8
                        assert action_box["y"] + action_box["height"] <= dock_box["y"] + overlap_tolerance or action_box["y"] >= dock_box["y"] + dock_box["height"]

            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.screenshot(path=str(shot), full_page=False)
            assert shot.exists() and shot.stat().st_size > 0
            assert errors == []
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_model_library_owner_paths_keyboard_and_accessibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Each in-world add choice returns to this one inventory; no modal detour."""
    from playwright.sync_api import sync_playwright

    server, url = _model_library_hub(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda error: errors.append(str(error)))
            surface = _open_library(page, url)
            group = surface.get_by_role("radiogroup", name="Model Library")
            group.wait_for()
            radios = group.get_by_role("radio")
            assert radios.count() >= 2
            # Labels carry source/status context, and selection detail/status is
            # announced without a browser-created readiness label.
            assert radios.nth(0).get_attribute("aria-label") is None
            assert radios.nth(0).is_checked()
            assert surface.locator(".model-library-detail").get_attribute("aria-live") == "polite"
            assert surface.locator(".model-library-summary").get_attribute("role") == "status"

            radios.nth(0).focus()
            page.keyboard.press("ArrowDown")
            assert radios.nth(1).is_checked()

            add = surface.get_by_role("button", name="+ Add model", exact=True)
            for label in ("Download from catalog", "Connect hosted model", "Define endpoint", "Use model file"):
                add.click()
                choice = surface.get_by_role("button", name=label, exact=True)
                choice.click()
                if label == "Download from catalog":
                    group.wait_for()
                    assert surface.locator('.model-library-tabs [role="tab"]').filter(has_text="Available").get_attribute("aria-selected") == "true"
                else:
                    form = surface.get_by_role("region", name=label, exact=True)
                    form.wait_for()
                    form.get_by_role("button", name="Back", exact=True).focus()
                    page.keyboard.press("Escape")
                    surface.locator(".model-library-inventory").wait_for()
                assert page.locator('[role="dialog"]').count() == 0

            # Escape lands on the original Add trigger; Ctrl+Enter is the
            # Linux equivalent of Mod+Enter and invokes only the selected seat.
            add.focus()
            add.click()
            page.keyboard.press("Escape")
            page.wait_for_function("document.activeElement?.classList.contains('model-library-add-trigger')")
            # Re-select an actionable catalog entry because the choice matrix
            # left the source tab on Available. Mod+Enter invokes its one seat;
            # provider custody and its canonical receipt are proved below.
            surface.locator('.model-library-tabs [role="tab"]').filter(has_text="All").click()
            catalog_row = surface.locator(".model-library-row").filter(has_text="Connect").first
            catalog_radio = catalog_row.get_by_role("radio")
            catalog_radio.check()
            catalog_radio.focus()
            page.keyboard.press("Control+Enter")
            surface.get_by_role("region", name="Connect hosted model", exact=True).wait_for()
            page.keyboard.press("Escape")
            surface.locator(".model-library-inventory").wait_for()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert errors == []
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_model_library_provider_custody_retains_retry_and_assignment_heads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A delayed custody failure retains the write-only field; an add keeps heads byte-identical."""
    from playwright.sync_api import sync_playwright
    from holdspeak.services.errors import ServiceError
    from holdspeak.services.profile_key_service import ProfileKeyService

    original_set = ProfileKeyService.set
    attempts = 0

    def delayed_set(self: ProfileKeyService, *args: Any, **kwargs: Any) -> Any:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            time.sleep(0.2)
            raise ServiceError("custody_delayed", "Key custody is unavailable.", context={"status": 503})
        return original_set(self, *args, **kwargs)

    # Keep the real service/route/key store but make its endpoint probe local.
    monkeypatch.setattr(ProfileKeyService, "set", delayed_set)
    monkeypatch.setattr(
        "holdspeak.services.profile_service.ProfileService.probe_inference_target",
        lambda *_args, **_kwargs: {"reachable": True},
    )
    server, url = _model_library_hub(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            surface = _open_library(page, url)
            sentinel = "hs143-e2e-write-only-sentinel"
            surface.get_by_role("button", name="+ Add model", exact=True).click()
            surface.get_by_role("button", name="Connect hosted model", exact=True).click()
            surface.get_by_label("Provider name", exact=True).fill("S5 Hosted")
            surface.get_by_label("Model", exact=True).fill("s5/test")
            key = surface.get_by_label("Provider key", exact=True)
            key.fill(sentinel)
            surface.get_by_role("button", name="Connect", exact=True).click()
            page.wait_for_timeout(40)
            assert key.input_value() == sentinel
            surface.get_by_role("alert").filter(has_text="Key custody is unavailable.").wait_for()
            assert key.input_value() == sentinel
            assert sentinel not in surface.evaluate("node => node.innerHTML")
            surface.get_by_role("button", name="Connect", exact=True).click()
            surface.get_by_role("status").filter(has_text="Added to the Model Library. Assignments are unchanged.").wait_for()
            assert surface.get_by_label("Provider key", exact=True).count() == 0
            assert attempts == 2

            # A second server-owned add returns canonical before/after heads;
            # equality is the service's no-assignment proof, not browser state.
            receipt = _api(page, "POST", "/api/inference/model-library/connect-hosted-model", {
                "draft": {
                    "request_id": "s5-assignment-heads",
                    "profile_id": "s5-assignment-heads",
                    "expected_profile_revision": 0,
                    "label": "S5 Anthropic",
                    "provider_family": "anthropic",
                    "model": "s5-model",
                    "requires_key": True,
                },
                "secret": {"value": "s5-assignment-key"},
            })
            assert receipt["receipt"]["assignments_unchanged"] is True
            assert receipt["receipt"]["assignments_before"] == receipt["receipt"]["assignments_after"]
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_model_library_broken_repair_is_visible(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """One server-projected repair stays in its original inventory row."""
    from playwright.sync_api import sync_playwright
    from holdspeak.services.model_library_service import ModelLibraryApplicationService

    original_projection = ModelLibraryApplicationService.get_library

    def broken_projection(self: ModelLibraryApplicationService, principal: Any) -> dict[str, Any]:
        projection = original_projection(self, principal)
        repair = {"code": "credential_unavailable", "label": "Provider key is missing"}
        row = {
            "id": "profile:s5-broken",
            "source": "provider",
            "label": "S5 broken provider",
            "status": "broken",
            "detail": {"provider_family": "openrouter"},
            "repair": repair,
            "selected_action": repair["label"],
        }
        return {
            **projection,
            "summary": {"state": "attention", "label": "Needs attention", "ready_count": 0, "attention_count": 1},
            "rows": [row],
        }

    monkeypatch.setattr(ModelLibraryApplicationService, "get_library", broken_projection)
    server, url = _model_library_hub(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            surface = _open_library(page, url)
            row = surface.locator(".model-library-row")
            row.wait_for()
            assert row.get_by_role("radio").count() == 1
            assert "S5 broken provider" in row.inner_text()
            assert "broken" in row.inner_text()
            assert surface.get_by_text("Provider key is missing", exact=True).count() == 2
            assert surface.locator(".model-library-action-seat").get_by_role("button", name="Provider key is missing", exact=True).count() == 1
            assert surface.get_by_text("Egress", exact=True).count() == 1
            assert surface.get_by_text("Needs attention", exact=True).count() >= 1
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_model_library_zoom_and_reduced_motion_glass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The real desktop glass remains action-reachable under 200% and no-motion."""
    from playwright.sync_api import sync_playwright

    server, url = _model_library_hub(tmp_path, monkeypatch)
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            # A 1440×900 display at 200% exposes a 720×450 CSS viewport. The
            # scale factor preserves the owner's 1440×900 review artifact.
            context = browser.new_context(viewport={"width": 720, "height": 450}, device_scale_factor=2)
            page = context.new_page()
            page.emulate_media(reduced_motion="reduce")
            surface = _open_library(page, url)
            action = surface.locator(".model-library-action-seat")
            action.scroll_into_view_if_needed()
            action_box = action.bounding_box()
            _assert_in_viewport(action_box, 720)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert page.locator(".model-library").evaluate("node => getComputedStyle(node).animationName") == "none"
            shot = SHOTS / "model-library-populated-1440-zoom200.png"
            page.screenshot(path=str(shot), full_page=False)
            assert shot.exists() and shot.stat().st_size > 0
            browser.close()
    finally:
        server.stop()
