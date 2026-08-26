"""HS-143-13 S2 — real-hub bounded Assignments overview at owner widths."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="Assignments glass needs Playwright")

TOKEN = "hs143-assignments-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-143-intelligence-router/assets/story-13-shots"


def _boot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"))))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
    )
    return server, server.start()


def _api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> None:
    result = page.evaluate(
        """async ([method, path, body]) => {
          const response = await fetch(path, {method, headers: {
            authorization: 'Bearer hs143-assignments-glass',
            ...(body ? {'content-type': 'application/json'} : {}),
          }, body: body ? JSON.stringify(body) : undefined});
          return response.status;
        }""",
        [method, path, body],
    )
    assert result < 300, result


def _open_assignments(page: Any, url: str) -> Any:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    page.goto(f"{url}/settings", wait_until="load")
    page.locator(".prefs-tile").filter(has_text="Assignments").click()
    surface = page.locator(".prefs-module")
    surface.wait_for()
    return surface


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.parametrize("state", ["populated", "empty", "error"])
def test_assignments_overview_real_hub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, state: str,
) -> None:
    from playwright.sync_api import sync_playwright
    from holdspeak.services.errors import ServiceError
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    original = InferenceAssignmentService.assignment_summary
    if state == "error":
        def assignment_summary(self: InferenceAssignmentService, principal: Any) -> dict[str, Any]:
            raise ServiceError("assignment_glass_error", "Assignments are unavailable.", context={"status": 503})
        monkeypatch.setattr(InferenceAssignmentService, "assignment_summary", assignment_summary)

    server, url = _boot(tmp_path, monkeypatch)
    if state == "populated":
        # Real profile/binding/assignment material, not a browser wire fake.
        from holdspeak.db import get_database
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService
        from tests.unit.test_phase143_inference_assignments import _profile

        db = get_database()
        owner = Principal(PrincipalKind.OWNER, "assignments-glass-owner")
        _profile(db, "assignments-glass-model")
        InferenceAssignmentService(db).set_assignment(owner, {
            "command_id": "assignments-glass-set", "expected_revision": 0,
            "scope": {"kind": "global"},
            "entries": [{"profile_id": "assignments-glass-model", "profile_revision": 1}],
        })
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda error: errors.append(str(error)))
            surface = _open_assignments(page, url)
            if state == "error":
                alert = surface.get_by_role("alert")
                alert.wait_for()
                assert "Assignments are unavailable." in alert.inner_text()
            else:
                rows = surface.locator(".capability-assignment-row")
                assert rows.count() == 7
                assert surface.locator("select").count() == 0
                if state == "empty":
                    assert surface.get_by_text("No default model", exact=True).count() >= 1
                else:
                    assert surface.get_by_text("Assignments Glass Model", exact=True).count() >= 1
                for index in range(7):
                    box = rows.nth(index).bounding_box()
                    assert box is not None and box["x"] >= 0 and box["x"] + box["width"] <= width + 1
                    if width == 393:
                        assert box["height"] >= 44
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            shot = SHOTS / f"assignments-{state}-{width}.png"
            page.screenshot(path=str(shot), full_page=False)
            assert shot.exists() and shot.stat().st_size > 0
            assert errors == []
            browser.close()
    finally:
        server.stop()
        monkeypatch.setattr(InferenceAssignmentService, "assignment_summary", original)
