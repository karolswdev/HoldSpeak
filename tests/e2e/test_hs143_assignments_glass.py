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


def _api_json(page: Any, method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body]) => {
          const response = await fetch(path, {method, headers: {
            authorization: 'Bearer hs143-assignments-glass', 'content-type': 'application/json'},
            body: JSON.stringify(body)});
          return {status: response.status, body: await response.json()};
        }""",
        [method, path, body],
    )
    assert result["status"] < 300, result
    return result["body"]


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


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_assignments_editor_real_hub_next_run_preview_and_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Real editor glass saves atomically, previews, then refuses stale clear."""
    from playwright.sync_api import sync_playwright
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import _profile

    server, url = _boot(tmp_path, monkeypatch)
    owner = Principal(PrincipalKind.OWNER, "assignments-editor-owner")
    db = get_database()
    _profile(db, "assignments-editor-model")
    service = InferenceAssignmentService(db)
    service.set_assignment(owner, {
        "command_id": "assignments-editor-global", "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": "assignments-editor-model", "profile_revision": 1}],
    })
    service.set_assignment(owner, {
        "command_id": "assignments-editor-group", "expected_revision": 0,
        "scope": {"kind": "group", "group_id": "thoughts_notes"},
        "entries": [{"profile_id": "assignments-editor-model", "profile_revision": 1}],
    })
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda error: errors.append(str(error)))
            surface = _open_assignments(page, url)
            # The group editor's default preview resolves the real global chain.
            surface.locator(".capability-assignment-row").filter(has_text="Thoughts & notes").get_by_role("button", name="Fix").click()
            sheet = surface.locator(".assignment-sheet")
            sheet.wait_for()
            assert sheet.get_by_role("heading", name="Thoughts & notes").count() == 1
            assert sheet.get_by_text("Assignments Editor Model", exact=True).count() >= 1
            sheet.get_by_role("button", name="Save assignment").click()
            receipt = surface.locator(".assignment-receipt")
            receipt.wait_for()
            assert "Next run" in receipt.inner_text()

            surface.locator(".capability-assignment-row").filter(has_text="Thoughts & notes").get_by_role("button", name="Fix").click()
            sheet.wait_for()
            sheet.get_by_role("button", name="Preview").click()
            preview = sheet.get_by_text("Will use Assignments Editor Model", exact=True)
            preview.wait_for()
            assert sheet.get_by_text("Retry follows the server policy", exact=False).count() == 1
            save_box = sheet.get_by_role("button", name="Save assignment").bounding_box()
            dock_box = page.locator(".desk-dock").bounding_box()
            assert save_box is not None and save_box["y"] >= 0 and save_box["y"] + save_box["height"] <= 900
            if dock_box is not None:
                assert save_box["y"] + save_box["height"] <= dock_box["y"] or save_box["y"] >= dock_box["y"] + dock_box["height"]
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            shot = SHOTS / f"assignments-editor-{width}.png"
            page.screenshot(path=str(shot), full_page=False)
            assert shot.exists() and shot.stat().st_size > 0

            # Another owner write after preview makes this clear stale. The UI
            # must discard the old preview and provide an in-flow refresh.
            _api_json(page, "POST", "/api/inference/assignments/set", {
                "command_id": f"assignments-editor-conflict-{width}",
                "expected_revision": 2,
                "scope": {"kind": "group", "group_id": "thoughts_notes"},
                "entries": [{"profile_id": "assignments-editor-model", "profile_revision": 1}],
                "retry_policy_id": None,
            })
            sheet.get_by_role("button", name="Use default").click()
            sheet.get_by_role("button", name="Refresh").wait_for()
            assert sheet.get_by_text("Assignment changed. Refresh before clearing.").count() == 1
            assert sheet.get_by_text("Will use Assignments Editor Model", exact=True).count() == 0
            if width == 393:
                for button in sheet.locator("button").all():
                    box = button.bounding_box()
                    if box is not None:
                        assert box["height"] >= 44
            assert errors == []
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_s4_contextual_assignment_glass_uses_server_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Thoughts, Dictation, and Meetings expose canonical assignment glass, never a picker."""
    from playwright.sync_api import sync_playwright
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import _profile

    server, url = _boot(tmp_path, monkeypatch)
    db = get_database()
    owner = Principal(PrincipalKind.OWNER, "s4-context-owner")
    _profile(db, "s4-context-model")
    service = InferenceAssignmentService(db)
    service.set_assignment(owner, {
        "command_id": "s4-context-global", "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": "s4-context-model", "profile_revision": 1}],
    })
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda error: errors.append(str(error)))
            assignments = _open_assignments(page, url)
            thought = assignments.locator(".capability-assignment-row").filter(has_text="Thoughts & notes")
            thought.wait_for()
            assert thought.get_by_text("Uses default · S4 Context Model", exact=True).count() == 1
            assert thought.locator("select").count() == 0
            thought.get_by_role("button").click()
            page.get_by_role("heading", name="Thoughts & notes", exact=True).wait_for()
            page.screenshot(path=str(SHOTS / f"thoughts-context-{width}.png"), full_page=False)
            page.get_by_role("button", name="Close", exact=True).click()

            page.goto(f"{url}/settings?token={TOKEN}", wait_until="load")
            page.locator(".prefs-tile").filter(has_text="Meetings").click()
            meetings = page.locator("[data-capability='meeting.live_analysis']")
            meetings.wait_for()
            assert meetings.locator("select").count() == 0
            meetings.get_by_role("button").click()
            meeting_sheet = page.get_by_label("Meetings assignment")
            meeting_sheet.wait_for()
            page.screenshot(path=str(SHOTS / f"meetings-group-{width}.png"), full_page=False)
            meeting_sheet.get_by_role("button", name="Close", exact=True).click()

            page.goto(f"{url}/dictation?token={TOKEN}", wait_until="load")
            dictation = page.locator("[data-capability='speech.rewrite']")
            dictation.wait_for()
            dictation.get_by_text("Uses global · S4 Context Model", exact=True).wait_for()
            assert dictation.locator("select").count() == 0
            page.screenshot(path=str(SHOTS / f"dictation-recovery-{width}.png"), full_page=False)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert errors == []
            browser.close()
    finally:
        server.stop()
