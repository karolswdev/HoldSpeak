"""HS-144-03 real-hub Door board proof.

The browser receives the production bundle and talks to a real MeetingWebServer.
Every populated record enters through a production HTTP adapter: sync ingestion
creates real meeting action items, Thoughts use their custody route, and the
scheduled-recording route feeds the retained Meetings lane.  This test never
writes projection tables directly.
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="glass walk needs Playwright")
pytest.importorskip("fastapi.testclient", reason="glass walk needs web dependencies")

ASSETS = Path(__file__).resolve().parents[2] / "pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/story-03-shots"
TOKEN = "hs144-door-glass"


def _api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body, token]) => {
          const response = await fetch(path, {
            method,
            headers: {
              authorization: `Bearer ${token}`,
              ...(body ? {"content-type": "application/json"} : {}),
            },
            body: body ? JSON.stringify(body) : undefined,
          });
          const contentType = response.headers.get("content-type") || "";
          const payload = contentType.includes("json")
            ? await response.json()
            : await response.text();
          return {status: response.status, payload};
        }""",
        [method, path, body, TOKEN],
    )
    assert result["status"] < 300, result
    assert isinstance(result["payload"], dict), result
    return result["payload"]


def _assert_clean(page: Any, errors: list[str]) -> None:
    assert not errors, errors
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert page.evaluate("document.body.scrollWidth <= window.innerWidth")


def _record_console(errors: list[str], message: Any, *, expected_http_statuses: tuple[int, ...] = ()) -> None:
    """Keep real application console failures distinct from named HTTP refusals."""
    if message.type != "error":
        return
    text = message.text
    if any(text == f"Failed to load resource: the server responded with a status of {status} (Conflict)" for status in expected_http_statuses):
        return
    if 500 in expected_http_statuses and text == "Failed to load resource: the server responded with a status of 500 (Internal Server Error)":
        return
    errors.append(f"console: {text}")


def _start_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    ASSETS.mkdir(parents=True, exist_ok=True)
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    browser_cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
    )
    return server, server.start()


def _seed_populated_door(page: Any) -> dict[str, str]:
    """Make the Door's actual sources through their HTTP authorities only."""
    now = datetime.now(timezone.utc)
    today = date.today()
    meeting_id = "hs144-door-glass-meeting"
    action_rows = [
        ("hs144-overdue", "Unblock the overdue Door proof", "Ada", today - timedelta(days=1)),
        ("hs144-now", "Review the front door today", "Bea", today),
        ("hs144-waiting", "Prepare next week\'s review", "Cy", today + timedelta(days=5)),
        ("hs144-unassigned", "Name an owner for the glass walk", None, None),
    ]
    sync_payload = {
        "meetings": [{
            "meta": {
                "id": meeting_id,
                "kind": "meeting",
                "last_modified": now.isoformat(),
                "deleted": False,
            },
            "value": {
                "id": meeting_id,
                "started_at": (now - timedelta(minutes=30)).isoformat(),
                "ended_at": now.isoformat(),
                "title": "Door glass planning",
                "tags": [],
                "segments": [],
                "bookmarks": [],
                "capture_status": "finalized",
                "transcription_status": "active",
                "provenance": "native",
                "intel": {
                    "timestamp": now.timestamp(),
                    "topics": ["Door board"],
                    "summary": "Production sync ingestion for the Door proof.",
                    "action_items": [
                        {
                            "id": item_id,
                            "task": task,
                            "owner": owner,
                            "due": due.isoformat() if due else None,
                            "status": "pending",
                            "review_state": "accepted",
                            "created_at": now.isoformat(),
                        }
                        for item_id, task, owner, due in action_rows
                    ],
                },
            },
        }],
    }
    pushed = _api(page, "POST", "/api/sync/push", sync_payload)
    assert pushed["received"]["meetings"] == 1

    # Thoughts require their lawful Inbox owner. The ordinary Desk seed is itself
    # an owner HTTP verb; it establishes the directory through production code.
    seeded = _api(page, "POST", "/api/desk/seed")
    assert "total" in seeded  # repeat seed is intentionally preservation-first
    created = _api(page, "POST", "/api/thoughts", {
        "request_id": str(uuid.uuid4()),
        "raw_text": "Keep the Door board honest on glass.",
        "source": {"kind": "typed"},
        "initial_note": {
            "title": "Door active thought",
            "body_markdown": "Keep the Door board honest on glass.",
            "tags": [],
        },
    })
    thought = created.get("thought", created)
    thought_id = str(thought["id"])

    schedule = _api(page, "POST", "/api/scheduled-recordings", {
        "title": "Door Glass Recording",
        "cron_expr": "0 9 * * *",
        "tz": "UTC",
        "one_shot": False,
        "duration_minutes": 30,
        "enabled": True,
    })
    assert schedule["schedule"]["title"] == "Door Glass Recording"
    return {"thought_id": thought_id, "overdue_id": "hs144-overdue"}


def _door_column(page: Any, name: str) -> Any:
    return page.locator(".door-board-column", has=page.get_by_role("heading", name=name, exact=True))


def _normal_chair(page: Any) -> None:
    # Wait for React's actual arrival choice before inspecting it. A same-context
    # reload remembers dismissal; a fresh context crosses First Sentence through
    # the owner control rather than bypassing the arrival contract.
    chair = page.locator(".chair")
    chair.wait_for()
    if chair.evaluate("element => element.classList.contains('chair-first-value')"):
        page.get_by_role("button", name="Continue later", exact=True).click()
    page.locator(".chair:not(.chair-first-value)").wait_for()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_hs144_door_cold_open_keeps_first_sentence_one_job(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fresh HOME still starts at First Sentence, before any Door data exists."""
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _start_hub(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))
            page.on("console", lambda message: _record_console(errors, message))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            first_sentence = page.get_by_test_id("chair-first-value")
            first_sentence.get_by_role("heading", name="Dictate one sentence", exact=True).wait_for()
            assert first_sentence.get_by_role("button", name="Continue later", exact=True).is_visible()
            assert page.locator(".door-board-section").count() == 0
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_hs144_door_populated_glass_action_refusal_and_shots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Five source-owned columns, a real verb, and an in-flow stale refusal."""
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _start_hub(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))
            page.on("console", lambda message: _record_console(errors, message, expected_http_statuses=(409,)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            ids = _seed_populated_door(page)
            # Door deliberately revalidates on its normal-Chair remount; reload
            # after the real writes instead of forging a browser response.
            page.reload(wait_until="load")
            _normal_chair(page)

            door = page.locator(".door-board-section")
            door.get_by_text("1 overdue · 1 now · 1 waiting · 1 active", exact=True).wait_for()
            expected_columns = {
                "Overdue": "1 overdue items",
                "Now": "1 now items",
                "Waiting": "1 waiting items",
                "Active": "1 active items",
            }
            for name, count_label in expected_columns.items():
                column = _door_column(page, name)
                assert column.get_by_label(count_label, exact=True).is_visible()
            assert _door_column(page, "Unassigned").locator(".door-card", has_text="Name an owner for the glass walk").is_visible()

            overdue = _door_column(page, "Overdue")
            overdue_card = overdue.locator(".door-card", has_text="Unblock the overdue Door proof")
            assert "action item · owner Ada · overdue 1d" in overdue_card.inner_text()
            active = _door_column(page, "Active")
            active_card = active.locator(".door-card", has_text="Door active thought")
            assert "thought · idle · updated now" in active_card.inner_text()
            page.get_by_role("heading", name="MEETINGS", exact=True).wait_for()
            meetings = page.locator('[data-lane="meetings"]')
            assert meetings.get_by_text("Door Glass Recording", exact=True).is_visible()
            agents = page.locator('[data-lane="agents"]')
            agents.get_by_text("No sessions", exact=True).wait_for()
            assert agents.get_by_role("heading", name="AGENTS · CREW 0 · BLOCKED 0", exact=True).is_visible()

            # At desk width the five-column Door is one workbench rail. It must
            # fit without a concealed fifth column or a horizontal scroll affordance.
            wide_board = door.locator(".door-board-viewport")
            wide_geometry = wide_board.evaluate(
                """viewport => {
                  const active = [...viewport.querySelectorAll('.door-board-column')]
                    .find(column => column.querySelector('h4')?.textContent === 'Active');
                  if (!active) return null;
                  return {
                    activeRight: active.getBoundingClientRect().right,
                    clientWidth: viewport.clientWidth,
                    scrollWidth: viewport.scrollWidth,
                    viewportWidth: window.innerWidth,
                  };
                }"""
            )
            assert wide_geometry is not None
            assert wide_geometry["scrollWidth"] == wide_geometry["clientWidth"], wide_geometry
            assert wide_geometry["activeRight"] <= wide_geometry["viewportWidth"] + 0.5, wide_geometry

            # Door leaves the two retained lanes as one calm, equal lower band.
            lower_band = page.evaluate(
                """() => {
                  const meetings = document.querySelector('[data-lane="meetings"]');
                  const agents = document.querySelector('[data-lane="agents"]');
                  if (!meetings || !agents) return null;
                  const meetingBox = meetings.getBoundingClientRect();
                  const agentBox = agents.getBoundingClientRect();
                  return {
                    agentsTop: agentBox.top,
                    agentsWidth: agentBox.width,
                    meetingsTop: meetingBox.top,
                    meetingsWidth: meetingBox.width,
                  };
                }"""
            )
            assert lower_band is not None
            assert abs(lower_band["meetingsWidth"] - lower_band["agentsWidth"]) <= 0.5, lower_band
            assert abs(lower_band["meetingsTop"] - lower_band["agentsTop"]) <= 0.5, lower_band
            page.screenshot(path=str(ASSETS / "door-populated-1440.png"), full_page=False)

            # A named Door descriptor calls its production route; the settled card
            # disappears only after the board reloads from the aggregate.
            overdue_card.get_by_role("button", name="Done", exact=True).click()
            overdue_card.wait_for(state="detached")
            landed = _api(page, "GET", "/api/door")
            assert landed["counts"] == {
                "overdue": 0,
                "now": 1,
                "waiting": 1,
                "active": 1,
                "upcoming_today": 0,
            }

            # Drift the thought through its genuine custody endpoint while the
            # card still has the old projection cursors. Its Complete descriptor
            # must refuse at the real authority and seat the receipt next to Door.
            current = _api(page, "GET", f"/api/thoughts/{ids['thought_id']}")["thought"]
            _api(page, "PATCH", f"/api/thoughts/{ids['thought_id']}/working", {
                "expected_aggregate_revision": current["aggregate_revision"],
                "expected_working_revision": current["working_revision"],
                "title": "Door active thought revised",
                "body_markdown": "A real stale cursor refusal belongs beside the board.",
                "tags": [],
            })
            active_card.get_by_role("button", name="Complete", exact=True).click()
            receipt = door.locator(".door-board-receipt [role=status]")
            receipt.get_by_text("COMPLETE FAILED · HTTP 409", exact=True).wait_for()
            assert receipt.get_by_role("button", name="Retry", exact=True).is_visible()
            assert page.get_by_role("dialog").count() == 0

            page.set_viewport_size({"width": 393, "height": 900})
            board_viewport = door.locator(".door-board-viewport")
            assert board_viewport.evaluate("el => el.scrollWidth > el.clientWidth")
            _assert_clean(page, errors)
            page.screenshot(path=str(ASSETS / "door-populated-393.png"), full_page=False)

            # Phase-143 review convention: 720 CSS px at DSF 2 yields a 1440 px
            # owner artifact while testing the 200% layout, not a fake CSS zoom.
            zoom_context = browser.new_context(viewport={"width": 720, "height": 450}, device_scale_factor=2)
            zoom_page = zoom_context.new_page()
            zoom_errors: list[str] = []
            zoom_page.emulate_media(reduced_motion="reduce")
            zoom_page.on("pageerror", lambda error: zoom_errors.append(f"page: {error}"))
            zoom_page.on("console", lambda message: zoom_errors.append(f"console: {message.text}") if message.type == "error" else None)
            zoom_page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _normal_chair(zoom_page)
            zoom_door = zoom_page.locator(".door-board-section")
            zoom_door.wait_for()
            zoom_done = _door_column(zoom_page, "Now").locator(".door-card", has_text="Review the front door today").get_by_role("button", name="Done", exact=True)
            zoom_done.focus()
            assert zoom_done.evaluate("el => document.activeElement === el && el.matches(':focus-visible')")
            _assert_clean(zoom_page, zoom_errors)
            zoom_page.screenshot(path=str(ASSETS / "door-populated-1440-zoom200.png"), full_page=False)
            zoom_context.close()

            # The header is the re-homed one-click Brief capability, not a second
            # Chair lane. The actual existing Intelligence pullout owns this view.
            door.get_by_role("button", name="Brief", exact=True).click()
            page.get_by_role("group", name="Intelligence view").get_by_role("button", name="Brief", exact=True).wait_for()
            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_hs144_door_empty_and_error_shots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Clean projection and controlled Door 500 both render in-flow on glass."""
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database
    from holdspeak.services.door_service import DoorService

    server, url = _start_hub(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))
            page.on("console", lambda message: _record_console(errors, message, expected_http_statuses=(500,)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            empty = page.locator(".door-board-section")
            empty.get_by_text("Door clear", exact=True).wait_for()
            _assert_clean(page, errors)
            page.screenshot(path=str(ASSETS / f"door-empty-{width}.png"), full_page=False)

            def refused_door(_self: DoorService, _principal: Any) -> dict[str, Any]:
                raise RuntimeError("controlled Door glass refusal")

            monkeypatch.setattr(DoorService, "get", refused_door)
            page.reload(wait_until="load")
            _normal_chair(page)
            error_state = page.locator('.door-board-section .surface-state[data-kind="error"]')
            error_state.get_by_text("HoldSpeak could not complete that request (HTTP 500).", exact=True).wait_for()
            _assert_clean(page, errors)
            page.screenshot(path=str(ASSETS / f"door-error-{width}.png"), full_page=False)
            browser.close()
    finally:
        server.stop()
        reset_database()
