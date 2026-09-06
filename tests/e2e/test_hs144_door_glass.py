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
    """HS-170-04 re-point: Door items appear as NEEDS YOU rows on the arrival.

    Seeds the same action items (overdue, now, waiting, unassigned) and a
    thought through production routes. Asserts: NEEDS YOU rows with correct
    order (danger first), tokens (OVERDUE, NOW, WAITING ON), and the
    ``Name an owner`` ghost verb on the unassigned item. The NEXT line
    from the seeded schedule. Active items do NOT appear.
    """
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
            page.reload(wait_until="load")
            _normal_chair(page)

            # Wait for the arrival headline
            page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
            page.wait_for_timeout(500)

            # ── NEEDS YOU section present ──
            needs_you = page.get_by_test_id("arrival-needs-you")
            assert needs_you.count() == 1, "NEEDS YOU section should be present"

            # ── Rows: overdue, now, waiting, unassigned; active is ABSENT ──
            rows = page.get_by_test_id("arrival-needs-you-row")
            # Door items: overdue(danger) + now(warning) + unassigned(warning) +
            # waiting(info) = 4 items (active excluded, the thought is "active")
            assert rows.count() >= 3, f"Expected at least 3 NEEDS YOU rows, got {rows.count()}"

            # Overdue item: severity danger, appears first
            overdue_text = rows.nth(0).locator(".surface-ledger-primary").text_content() or ""
            assert "overdue" in overdue_text.lower() or "Unblock" in overdue_text, \
                f"First row should be the overdue item: {overdue_text}"

            # WHY tokens
            why_tokens = page.get_by_test_id("arrival-why")
            token_texts = [why_tokens.nth(i).text_content() or "" for i in range(why_tokens.count())]
            assert any("OVERDUE" in t for t in token_texts), f"Expected OVERDUE token: {token_texts}"

            # "Name an owner" verb on the unassigned item
            name_owner = page.get_by_test_id("arrival-name-owner")
            assert name_owner.count() >= 1, "Unassigned item should have 'Name an owner' verb"

            # NEXT line from the seeded scheduled recording
            next_line = page.get_by_test_id("arrival-next")
            assert next_line.count() == 1, "NEXT line should be present"
            next_text = next_line.text_content() or ""
            assert "DOOR GLASS RECORDING" in next_text.upper(), \
                f"NEXT should name the schedule: {next_text}"

            # Active thought does NOT appear in NEEDS YOU
            all_primaries = [rows.nth(i).locator(".surface-ledger-primary").text_content() or ""
                             for i in range(rows.count())]
            assert not any("active thought" in p.lower() for p in all_primaries), \
                f"Active items should not appear: {all_primaries}"

            _assert_clean(page, errors)
            page.screenshot(path=str(DOOR_ASSETS / "door-populated-1440.png"), full_page=False)

            # ── 393 shot ──
            page.set_viewport_size({"width": 393, "height": 900})
            page.wait_for_timeout(300)
            _assert_clean(page, errors)
            page.screenshot(path=str(DOOR_ASSETS / "door-populated-393.png"), full_page=False)

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
            # HS-170-04: empty door = NEEDS YOU absent on the arrival
            page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
            page.wait_for_timeout(500)
            assert page.get_by_test_id("arrival-needs-you").count() == 0, \
                "NEEDS YOU section should be absent when door is empty"
            _assert_clean(page, errors)
            page.screenshot(path=str(DOOR_ASSETS / f"door-empty-{width}.png"), full_page=False)

            # Door 500: the arrival catches it silently
            def refused_door(_self: DoorService, _principal: Any) -> dict[str, Any]:
                raise RuntimeError("controlled Door glass refusal")
            monkeypatch.setattr(DoorService, "get", refused_door)
            page.reload(wait_until="load")
            _normal_chair(page)
            page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
            page.wait_for_timeout(500)
            headline = page.get_by_test_id("arrival-display").text_content() or ""
            assert "nothing needs you" in headline.lower(), \
                f"Headline should read 'Nothing needs you' on door error: {headline}"
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
    """HS-170-04 re-point: the NEXT line from schedule/calendar; NO CALENDAR
    + Connect calendar when unconfigured.
    """
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

            # Empty hub with no calendar: NO CALENDAR + Connect calendar
            page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
            page.wait_for_timeout(500)
            no_cal = page.get_by_test_id("arrival-no-calendar")
            connect_btn = page.get_by_test_id("arrival-connect-calendar")
            assert no_cal.count() == 1, "NO CALENDAR should show when unconfigured"
            assert connect_btn.count() == 1, "Connect calendar should be present"
            _assert_clean(page, errors)
            page.screenshot(path=str(RAIL_ASSETS / "rail-empty-1440.png"), full_page=False)

            # Seed a scheduled recording: NEXT line appears
            _seed_future_schedule(page, "Rail-only recording")
            page.reload(wait_until="load")
            _normal_chair(page)
            page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
            page.wait_for_timeout(500)
            next_line = page.get_by_test_id("arrival-next")
            assert next_line.count() == 1, "NEXT line should appear after schedule seed"
            next_text = next_line.text_content() or ""
            assert "RAIL-ONLY RECORDING" in next_text.upper(), \
                f"NEXT should name the schedule: {next_text}"
            _assert_clean(page, errors)
            page.screenshot(path=str(RAIL_ASSETS / "rail-populated-1440.png"), full_page=False)

            page.set_viewport_size({"width": 393, "height": 900})
            page.wait_for_timeout(300)
            _assert_clean(page, errors)
            page.screenshot(path=str(RAIL_ASSETS / "rail-populated-393.png"), full_page=False)
            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_upcoming_rail_schedule_create_round_trip_and_form_cancel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HS-170-04 re-point: the capture bar's Schedule verb opens the in-world
    form; the created schedule appears on NEXT.
    """
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

            # The capture bar's Schedule verb opens the in-world schedule form
            schedule_btn = page.get_by_test_id("arrival-schedule")
            assert schedule_btn.count() == 1, "Schedule verb should be in capture bar"
            schedule_btn.click()
            form = page.locator("#schedule\\:__create__")
            form.wait_for()
            assert form.get_by_role("button", name="Speak Title", exact=True).is_visible()
            form.get_by_role("button", name="Cancel", exact=True).click()
            form.wait_for(state="detached")
            assert _api(page, "GET", "/api/scheduled-recordings")["schedules"] == []

            # Create a schedule through the form
            schedule_btn.click()
            form = page.locator("#schedule\\:__create__")
            form.get_by_role("textbox", name="Title", exact=True).fill("Rail form recording")
            form.get_by_test_id("schedule-create-submit").click()
            form.wait_for(state="detached")
            schedules = _api(page, "GET", "/api/scheduled-recordings")["schedules"]
            assert [schedule["title"] for schedule in schedules] == ["Rail form recording"]
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
            # HS-170-04: the hub is now SurfaceLedgerRows; click the Meetings row.
            settings.locator(".surface-ledger-primary", has_text="Meetings").click()
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
