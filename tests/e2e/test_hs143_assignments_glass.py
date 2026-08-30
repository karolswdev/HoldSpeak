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


def _open_assignments(page: Any, url: str, *, summary_ready: bool = True) -> Any:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    page.goto(f"{url}/settings", wait_until="load")
    page.locator(".prefs-tile").filter(has_text="Assignments").click()
    surface = page.locator(".prefs-module")
    surface.wait_for()
    if summary_ready:
        # The Settings shell appears before CapabilityAssignmentsCore has consumed
        # its server-owned summary. Wait for the component's loaded fact and its
        # complete bounded roster, never a timing delay or a snapshot count.
        assignments = surface.locator(
            ".capability-assignments[data-assignment-summary-state='loaded']"
        )
        assignments.get_by_role("heading", name="Assignments", exact=True).wait_for()
        assignments.locator(".capability-assignment-row").nth(6).wait_for(state="visible")
    return surface


def _open_desk_surface(page: Any, url: str, path: str) -> None:
    """Use the live desk's demoted-surface protocol, not a component harness."""
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    page.reload(wait_until="load")
    page.evaluate(
        """path => {
          history.pushState({}, "", path);
          dispatchEvent(new PopStateEvent("popstate"));
        }""",
        f"{path}?token={TOKEN}",
    )


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
            surface = _open_assignments(page, url, summary_ready=state != "error")
            if state == "populated" and width == 1440:
                # Product-level reduced-motion check: the real CSS preference
                # zeroes transition/animation timing without changing the face.
                page.emulate_media(reduced_motion="reduce")
                assert page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--duration-short').trim()") == "0ms"
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
            if state == "populated" and width == 1440:
                # Desktop 200% zoom halves the CSS viewport, rather than applying
                # CSS zoom (which would magnify a fixed window without reflowing
                # its dock reservation). Capture at 2x device scale so the proof
                # remains a 1440×900 image of the reflowed, real hub.
                zoom_context = browser.new_context(
                    viewport={"width": 720, "height": 450}, device_scale_factor=2,
                )
                zoom_page = zoom_context.new_page()
                zoom_surface = _open_assignments(zoom_page, url)
                zoom_rows = zoom_surface.locator(".capability-assignment-row")
                zoom_rows.nth(0).wait_for()
                zoom_dock = zoom_page.locator(".desk-dock").bounding_box()
                first_row = zoom_rows.nth(0).bounding_box()
                assert first_row is not None
                if zoom_dock is not None:
                    assert first_row["y"] + first_row["height"] <= zoom_dock["y"]
                assert zoom_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                zoom_shot = SHOTS / "assignments-populated-1440-zoom200.png"
                zoom_page.screenshot(path=str(zoom_shot), full_page=False, scale="device")
                assert zoom_shot.exists() and zoom_shot.stat().st_size > 0
                zoom_context.close()
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


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_s5_recipe_and_workbench_contextual_assignments_are_pre_scoped_and_accessible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Production Recipe/Workbench objects share the one contextual editor."""
    from playwright.sync_api import sync_playwright
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import _profile

    server, url = _boot(tmp_path, monkeypatch)
    db = get_database()
    owner = Principal(PrincipalKind.OWNER, "s5-context-owner")
    _profile(db, "s5-subject-first")
    _profile(db, "s5-subject-second")
    service = InferenceAssignmentService(db)
    service.set_assignment(owner, {
        "command_id": "s5-context-global", "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": "s5-subject-first", "profile_revision": 1}],
    })
    recipe = db.recipes.upsert(
        recipe_id="recipe-s5-context", name="S5 Recipe", system_prompt="system", user_template="{input}",
    )
    workbench = db.workbenches.upsert(
        workbench_id="workbench-s5-context", name="S5 Workbench", recipe_id=recipe.id,
    )
    db.workbench_items.upsert(
        item_id="workbench-s5-item", workbench_id=workbench.id, title="Subject proof", body="body",
    )
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    requests: list[dict[str, Any]] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("request", lambda request: requests.append({
                "url": request.url, "post_data": request.post_data,
            }) if request.url.endswith("/api/inference/assignments/editor") else None)

            # Recipe thread uses the durable Recipe id + chat.turn pair.
            _open_desk_surface(page, url, "/companion")
            page.get_by_role("button", name="S5 Recipe\nOK", exact=True).click()
            recipe_context = page.locator("[data-capability='chat.turn']")
            recipe_context.wait_for()
            assert recipe_context.get_by_text("Uses global · S5 Subject First", exact=True).count() == 1
            assert recipe_context.locator("select").count() == 0
            page.screenshot(path=str(SHOTS / f"recipe-chat-context-{width}.png"), full_page=False)
            recipe_change = recipe_context.get_by_role("button", name="Change")
            recipe_change.click()
            recipe_sheet = page.get_by_label("Thread assignment")
            recipe_sheet.wait_for()
            assert recipe_sheet.get_by_role("radiogroup", name="Compatible models").count() == 1
            # Screen-reader-visible names and roving radio state are live facts.
            radios = recipe_sheet.get_by_role("radio")
            assert radios.count() == 2
            radios.nth(0).press("ArrowDown")
            assert radios.nth(1).get_attribute("aria-checked") == "true"
            assert recipe_sheet.locator("[aria-live='polite']").count() == 1
            page.screenshot(path=str(SHOTS / f"recipe-chat-editor-{width}.png"), full_page=False)
            # Keyboard-only composition: choose the roving candidate, then use
            # the sheet's documented Ctrl/Cmd+Enter primary without a pointer.
            radios.nth(1).press("Enter")
            radios.nth(1).press("Control+Enter")
            recipe_context.get_by_role("status").filter(has_text="Next run").wait_for()
            assert "Next run" in recipe_context.get_by_role("status").inner_text()
            recipe_change.click()
            recipe_sheet.wait_for()
            recipe_sheet.press("Escape")
            assert page.evaluate("document.activeElement?.textContent") == "Change"

            # Workbench exposes both exact durable Workbench subject pairs.
            _open_desk_surface(page, url, "/workbenches")
            page.locator(".wb-home-card").filter(has_text="S5 Workbench").click()
            page.get_by_role("button", name="Expand configuration").click()
            item_context = page.locator("[data-capability='workbench.item']")
            resolver_context = page.locator("[data-capability='voice.reference_resolve']")
            item_context.wait_for()
            resolver_context.wait_for()
            assert item_context.get_by_text("Uses global · S5 Subject First", exact=True).count() == 1
            assert resolver_context.get_by_text("Uses global · S5 Subject First", exact=True).count() == 1
            assert page.locator(".wb-config-panel select").count() == 0
            for contextual in (item_context, resolver_context):
                box = contextual.bounding_box()
                assert box is not None and box["x"] >= 0 and box["x"] + box["width"] <= width + 1
            page.screenshot(path=str(SHOTS / f"workbench-context-{width}.png"), full_page=False)

            item_change = item_context.get_by_role("button", name="Change")
            item_change.click()
            item_sheet = page.get_by_label("Item assignment")
            item_sheet.wait_for()
            sheet_box = item_sheet.bounding_box()
            dock_box = page.locator(".desk-dock").bounding_box()
            assert sheet_box is not None
            if dock_box is not None:
                assert sheet_box["y"] + sheet_box["height"] <= dock_box["y"]
            item_sheet.get_by_role("radio").nth(0).click()
            # The real device walk proves the server receipt through the one
            # primary after a local candidate choice (never an autosave).
            item_sheet.get_by_role("button", name="Save assignment").click()
            item_context.get_by_role("status").filter(has_text="Next run").wait_for()
            assert "Next run" in item_context.get_by_role("status").inner_text()
            page.screenshot(path=str(SHOTS / f"workbench-item-editor-{width}.png"), full_page=False)

            resolver_context.get_by_role("button", name="Change").click()
            resolver_sheet = page.get_by_label("Reference assignment")
            resolver_sheet.wait_for()
            assert resolver_sheet.get_by_role("heading", name="Reference assignment").count() == 1
            resolver_sheet.get_by_role("radio").nth(0).click()
            resolver_sheet.get_by_role("button", name="Save assignment").click()
            resolver_context.get_by_role("status").filter(has_text="Next run").wait_for()

            bodies = [entry["post_data"] or "" for entry in requests]
            assert any('"subject_kind":"recipe"' in body and '"capability_id":"chat.turn"' in body for body in bodies)
            assert any('"subject_kind":"workbench"' in body and '"capability_id":"workbench.item"' in body for body in bodies)
            assert any('"subject_kind":"workbench"' in body and '"capability_id":"voice.reference_resolve"' in body for body in bodies)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            if width == 393:
                for button in page.locator(".assignment-sheet button").all():
                    box = button.bounding_box()
                    if box is not None:
                        assert box["height"] >= 44
            assert errors == []
            browser.close()
    finally:
        server.stop()
