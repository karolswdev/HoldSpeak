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

DOOR_ASSETS = Path(__file__).resolve().parents[2] / "pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/story-03-shots"
RAIL_ASSETS = Path(__file__).resolve().parents[2] / "pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/story-04-shots"
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
    DOOR_ASSETS.mkdir(parents=True, exist_ok=True)
    RAIL_ASSETS.mkdir(parents=True, exist_ok=True)
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

    # HS-145 triage: the original fixed "0 9 * * *" seed made upcoming_today
    # time-of-day dependent (next 09:00 UTC is only "today" for a ~3h local
    # window). Seed a recurring fire relative to now, clamped inside today's
    # local day so the counts assertion holds at any hour. The sub-two-minute
    # window right before local midnight is accepted, not mitigated.
    fire = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(hours=3)
    end_of_local_day = datetime.now().astimezone().replace(hour=23, minute=58, second=0, microsecond=0)
    if fire.astimezone() > end_of_local_day:
        fire = end_of_local_day.astimezone(timezone.utc)
    schedule = _api(page, "POST", "/api/scheduled-recordings", {
        "title": "Door Glass Recording",
        "cron_expr": f"{fire.minute} {fire.hour} * * *",
        "tz": "UTC",
        "one_shot": False,
        "duration_minutes": 30,
        "enabled": True,
    })
    assert schedule["schedule"]["title"] == "Door Glass Recording"
    return {"thought_id": thought_id, "overdue_id": "hs144-overdue"}


def _seed_future_schedule(page: Any, title: str) -> dict[str, Any]:
    """Use the production schedule authority for an honest future rail row."""
    starts = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(hours=3)
    result = _api(page, "POST", "/api/scheduled-recordings", {
        "title": title,
        "cron_expr": f"{starts.minute} {starts.hour} {starts.day} {starts.month} *",
        "tz": "UTC",
        "one_shot": True,
        "duration_minutes": 30,
        "enabled": True,
    })
    assert result["schedule"]["title"] == title
    return result["schedule"]


def _seed_calendar_fixture_via_settings(page: Any, tmp_path: Path) -> None:
    """Write a local ICS source through Settings, then apply it through its conductor."""
    starts = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(hours=2)
    ends = starts + timedelta(minutes=45)
    fixture = tmp_path / "door-upcoming.ics"
    fixture.write_text(
        "\r\n".join([
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//HoldSpeak//Door glass//EN",
            "BEGIN:VEVENT",
            "UID:hs144-calendar-fixture",
            f"DTSTART:{starts.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{ends.strftime('%Y%m%dT%H%M%SZ')}",
            "SUMMARY:Door Calendar Fixture",
            "LOCATION:Room 4",
            "URL:https://meet.example.test/door-fixture",
            "END:VEVENT",
            "END:VCALENDAR",
            "",
        ]),
        encoding="utf-8",
    )
    saved = _api(page, "PUT", "/api/settings", {
        "calendar": {"sources": [{"id": "hs144-fixture", "label": "Glass", "url": str(fixture), "enabled": True}]},
    })
    # HS-146-04: seed repair — assert the sources-wire fact.
    sources_fact = saved["settings"]["_calendar_sources"]
    assert len(sources_fact) == 1
    assert sources_fact[0]["kind"] == "file"

    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

    # This is the production reader + parser + projection replacement; the
    # browser never receives a mocked Door response or a projection-table write.
    assert CalendarIngestConductor().refresh() is True
    door = _api(page, "GET", "/api/door")
    assert any(
        item["source"] == "calendar_event" and item["title"] == "Door Calendar Fixture"
        for item in door["upcoming"]
    )


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
            rail = door.locator(".door-upcoming-rail")
            assert rail.get_by_text("Door Glass Recording", exact=True).is_visible()
            assert meetings.get_by_text("Door Glass Recording", exact=True).count() == 0
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
            page.screenshot(path=str(DOOR_ASSETS / "door-populated-1440.png"), full_page=False)

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
                # The production schedule seeded above is a separate Door
                # rail source, so this aggregate must retain its one upcoming row.
                "upcoming_today": 1,
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
            page.screenshot(path=str(DOOR_ASSETS / "door-populated-393.png"), full_page=False)

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
            zoom_page.screenshot(path=str(DOOR_ASSETS / "door-populated-1440-zoom200.png"), full_page=False)
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
            page.screenshot(path=str(DOOR_ASSETS / f"door-empty-{width}.png"), full_page=False)

            def refused_door(_self: DoorService, _principal: Any) -> dict[str, Any]:
                raise RuntimeError("controlled Door glass refusal")

            monkeypatch.setattr(DoorService, "get", refused_door)
            page.reload(wait_until="load")
            _normal_chair(page)
            error_state = page.locator('.door-board-section .surface-state[data-kind="error"]')
            error_state.get_by_text("HoldSpeak could not complete that request (HTTP 500).", exact=True).wait_for()
            _assert_clean(page, errors)
            page.screenshot(path=str(DOOR_ASSETS / f"door-error-{width}.png"), full_page=False)
            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_upcoming_rail_real_hub_states_and_dimensions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One actual Door aggregate moves empty → schedule-only → mixed chronology."""
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
            _normal_chair(page)

            door = page.locator(".door-board-section")
            empty_rail = door.locator(".door-upcoming-rail")
            # HS-145-02: an unconfigured hub's empty rail now leads to calendar
            # setup instead of dead-ending. The configured-but-quiet state keeps
            # the original copy (pinned in test_hs145_door_polish_glass).
            empty_rail.get_by_text("No calendar connected.", exact=True).wait_for()
            assert empty_rail.get_by_role("button", name="Connect calendar", exact=True).is_visible()
            _assert_clean(page, errors)
            page.screenshot(path=str(RAIL_ASSETS / "rail-empty-1440.png"), full_page=False)

            # Calendar-less is ordinary: the real recording authority creates
            # the only upcoming row, with no second MeetingsLane projection.
            _seed_future_schedule(page, "Rail-only recording")
            page.reload(wait_until="load")
            _normal_chair(page)
            door = page.locator(".door-board-section")
            rail = door.locator(".door-upcoming-rail")
            rail.get_by_text("Rail-only recording", exact=True).wait_for()
            assert rail.locator('[data-upcoming-source="scheduled_recording"]').count() == 1
            assert rail.locator('[data-upcoming-source="calendar_event"]').count() == 0
            assert page.locator('[data-lane="meetings"]').get_by_text(
                "Rail-only recording", exact=True,
            ).count() == 0

            # The one Story-02 setting reaches the real file reader, parser,
            # conductor and production projection before Door reads it back.
            _seed_calendar_fixture_via_settings(page, tmp_path)
            page.reload(wait_until="load")
            _normal_chair(page)
            door = page.locator(".door-board-section")
            rail = door.locator(".door-upcoming-rail")
            rail.get_by_text("Door Calendar Fixture", exact=True).wait_for()
            rail.get_by_text("Rail-only recording", exact=True).wait_for()
            rows = rail.locator(".door-upcoming-row")
            assert rows.evaluate_all(
                "rows => rows.map(row => row.dataset.upcomingSource)",
            ) == ["calendar_event", "scheduled_recording"]
            assert rail.get_by_text("EVENT", exact=True).is_visible()
            assert rail.get_by_text("SCHEDULED RECORDING", exact=True).is_visible()
            assert rail.get_by_text("Room 4", exact=True).is_visible()
            assert rail.get_by_role("link", name="Meeting link", exact=True).is_visible()
            assert page.locator('[data-lane="meetings"]').get_by_text(
                "Rail-only recording", exact=True,
            ).count() == 0
            _assert_clean(page, errors)
            page.screenshot(path=str(RAIL_ASSETS / "rail-populated-1440.png"), full_page=False)

            page.set_viewport_size({"width": 393, "height": 900})
            rail.get_by_text("Door Calendar Fixture", exact=True).wait_for()
            _assert_clean(page, errors)
            page.screenshot(path=str(RAIL_ASSETS / "rail-populated-393.png"), full_page=False)

            # 720 CSS px at DSF 2 is the actual 200% review condition.
            zoom_context = browser.new_context(
                viewport={"width": 720, "height": 450}, device_scale_factor=2,
            )
            zoom_page = zoom_context.new_page()
            zoom_errors: list[str] = []
            zoom_page.emulate_media(reduced_motion="reduce")
            zoom_page.on("pageerror", lambda error: zoom_errors.append(f"page: {error}"))
            zoom_page.on("console", lambda message: _record_console(zoom_errors, message))
            zoom_page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _normal_chair(zoom_page)
            zoom_page.locator(".door-upcoming-rail").get_by_text(
                "Door Calendar Fixture", exact=True,
            ).wait_for()
            _assert_clean(zoom_page, zoom_errors)
            zoom_page.screenshot(
                path=str(RAIL_ASSETS / "rail-populated-1440-zoom200.png"),
                full_page=False,
            )
            zoom_context.close()
            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_upcoming_rail_schedule_create_round_trip_and_form_cancel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The rail reuses the in-world form and the existing schedule writer."""
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
            _normal_chair(page)
            rail = page.locator(".door-upcoming-rail")

            rail.get_by_role("button", name="Schedule recording", exact=True).click()
            form = page.locator("#schedule\\:__create__")
            form.wait_for()
            assert form.get_by_role("button", name="Speak Title", exact=True).is_visible()
            form.get_by_role("button", name="Cancel", exact=True).click()
            form.wait_for(state="detached")
            assert _api(page, "GET", "/api/scheduled-recordings")["schedules"] == []

            rail.get_by_role("button", name="Schedule recording", exact=True).click()
            form = page.locator("#schedule\\:__create__")
            form.get_by_role("textbox", name="Title", exact=True).fill("Rail form recording")
            form.get_by_test_id("schedule-create-submit").click()
            form.wait_for(state="detached")
            rail.get_by_text("Rail form recording", exact=True).wait_for()
            schedules = _api(page, "GET", "/api/scheduled-recordings")["schedules"]
            assert [schedule["title"] for schedule in schedules] == ["Rail form recording"]
            assert page.locator('[data-lane="meetings"]').get_by_text(
                "Rail form recording", exact=True,
            ).count() == 0
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_go_menu_is_usable_at_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compact Go is the existing WorkMenu and opens its registered application."""
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _start_hub(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 393, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))
            page.on("console", lambda message: _record_console(errors, message))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)

            go = page.get_by_role("button", name="Go", exact=True)
            go.wait_for()
            go.click()
            menu = page.get_by_role("menu", name="Go menu")
            meetings_item = menu.get_by_role("menuitem", name="Meetings")
            meetings_item.wait_for()
            _assert_clean(page, errors)
            page.screenshot(path=str(RAIL_ASSETS / "go-menu-393.png"), full_page=False)
            meetings_item.click()
            page.locator("#surface-meetings").wait_for()
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_meetings_settings_calendar_glass_and_egress_fact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Meetings owns the one calendar setting and its backend-derived egress fact."""
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
            _normal_chair(page)
            saved = _api(page, "PUT", "/api/settings", {
                "calendar": {"sources": [{"id": "hs144-egress", "label": "", "url": "https://calendar.example.test/team.ics", "enabled": True}]},
            })
            # HS-146-04: seed repair — assert the sources-wire fact.
            sources_fact = saved["settings"]["_calendar_sources"]
            assert len(sources_fact) == 1
            assert sources_fact[0] == {
                "id": "hs144-egress",
                "label": "",
                "kind": "https",
                "host": "calendar.example.test",
                "refresh_seconds": 900,
                "egress": True,
                "enabled": True,
            }

            # Open Settings through its normal Go registry path; the settings
            # window retains the browser's authorized root context.
            page.get_by_role("button", name="Go", exact=True).click()
            go_menu = page.get_by_role("menu", name="Go menu")
            go_menu.get_by_role("menuitem", name="Settings").click()
            settings = page.locator("#surface-settings")
            settings.wait_for()
            # A listitem's content is intentionally not its accessible name;
            # select the actual tile button by its visible module label.
            settings.locator("button.prefs-tile", has_text="MEETINGS").click()
            # TODO(HS-146-05): story 03 replaces the single textbox with a
            # GadgetTable list editor; assert the new editor glass here once
            # story 03 lands. For now assert Settings opens to Meetings.
            settings.wait_for()
            _assert_clean(page, errors)
            page.screenshot(path=str(RAIL_ASSETS / "settings-calendar-1440.png"), full_page=False)

            # HS-146-04: seed repair — file and disabled sources use the sources wire.
            for source_url in [str(tmp_path / "calendar.ics"), ""]:
                sources_list = [{"id": "hs144-egress", "label": "", "url": source_url, "enabled": True}] if source_url else []
                fact_resp = _api(page, "PUT", "/api/settings", {
                    "calendar": {"sources": sources_list},
                })["settings"]["_calendar_sources"]
                if source_url:
                    assert fact_resp[0]["egress"] is False
                else:
                    assert fact_resp == []
            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_meetings_deep_link_waits_for_registered_surface_x15(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fifteen serial fresh /meetings arrivals wait for actual registry completion."""
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _start_hub(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            arrival = context.new_page()
            arrival.emulate_media(reduced_motion="reduce")
            arrival.on("pageerror", lambda error: errors.append(f"page: {error}"))
            arrival.on("console", lambda message: _record_console(errors, message))
            arrival.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _normal_chair(arrival)
            arrival.close()

            # These are fifteen independent document loads, not retries: each
            # must queue the demoted route before React registers its Door rows.
            for navigation in range(1, 16):
                page = context.new_page()
                page.emulate_media(reduced_motion="reduce")
                page.on("pageerror", lambda error: errors.append(f"{navigation}: {error}"))
                page.on("console", lambda message: _record_console(errors, message))
                page.goto(f"{url}/meetings?token={TOKEN}", wait_until="load")
                page.locator('[data-surface-registry-state="registered"]').wait_for(state="attached")
                page.locator("#surface-meetings").wait_for()
                assert page.locator("#surface-meetings").is_visible()
                print(f"deep-link {navigation:02d}/15 registry=registered meetings=visible")
                _assert_clean(page, errors)
                page.close()
            context.close()
            browser.close()
    finally:
        server.stop()
        reset_database()
