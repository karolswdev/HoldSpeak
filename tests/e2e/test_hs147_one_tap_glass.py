"""HS-147-02 real-hub one-tap-record proof.

The browser receives the production bundle and talks to a real
MeetingWebServer.  Calendar events enter through the settings authority +
the production ingest conductor; every arm/cancel in this file is a REAL
click on the rail driving the story-01 route.  Nothing is mocked; the one
deliberate refusal is a genuinely stale row hitting the live L1 guard.
Shots land in the phase assets as the story-02 exhibit.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="glass walk needs Playwright")
pytest.importorskip("fastapi.testclient", reason="glass walk needs web dependencies")

SHOTS = Path(__file__).resolve().parents[2] / (
    "pm/roadmap/holdspeak/phase-147-one-tap-record/assets/story-02-shots"
)
TOKEN = "hs147-one-tap-glass"


def _api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = _api_raw(page, method, path, body)
    assert result["status"] < 300, result
    assert isinstance(result["payload"], dict), result
    return result["payload"]


def _api_raw(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    return page.evaluate(
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


def _record_console(errors: list[str], message: Any, *, expected_http_statuses: tuple[int, ...] = ()) -> None:
    if message.type != "error":
        return
    text = message.text
    if any(
        text == f"Failed to load resource: the server responded with a status of {status} (Conflict)"
        for status in expected_http_statuses
    ):
        return
    errors.append(f"console: {text}")


def _assert_clean(page: Any, errors: list[str]) -> None:
    assert not errors, errors
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert page.evaluate("document.body.scrollWidth <= window.innerWidth")


def _start_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    SHOTS.mkdir(parents=True, exist_ok=True)
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


def _seed_two_events(page: Any, tmp_path: Path) -> dict[str, str]:
    """Two timed events through the settings authority + the real conductor."""
    starts_a = datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(hours=2)
    starts_b = starts_a + timedelta(hours=1)
    fixture = tmp_path / "one-tap.ics"
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HoldSpeak//HS147 glass//EN"]
    for uid, starts, title, room in (
        ("hs147-event-a", starts_a, "One Tap Standup", "Room A"),
        ("hs147-event-b", starts_b, "One Tap Review", "Room B"),
    ):
        ends = starts + timedelta(minutes=45)
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART:{starts.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{ends.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:{title}",
            f"LOCATION:{room}",
            "END:VEVENT",
        ]
    lines += ["END:VCALENDAR", ""]
    fixture.write_text("\r\n".join(lines), encoding="utf-8")
    _api(page, "PUT", "/api/settings", {
        "calendar": {"sources": [{"id": "hs147-glass", "label": "Glass", "url": str(fixture), "enabled": True}]},
    })

    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

    assert CalendarIngestConductor().refresh() is True
    door = _api(page, "GET", "/api/door")
    ids = {
        item["title"]: item["id"]
        for item in door["upcoming"]
        if item["source"] == "calendar_event"
    }
    assert set(ids) == {"One Tap Standup", "One Tap Review"}, door["upcoming"]
    return ids


def _normal_chair(page: Any) -> None:
    chair = page.locator(".chair")
    chair.wait_for()
    if chair.evaluate("element => element.classList.contains('chair-first-value')"):
        page.get_by_role("button", name="Continue later", exact=True).click()
    page.locator(".chair:not(.chair-first-value)").wait_for()


def _event_row(page: Any, title: str) -> Any:
    return page.locator(".door-upcoming-rail li.door-upcoming-row", has=page.get_by_text(title, exact=True))


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_hs147_one_tap_arm_cancel_refusal_and_shots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HS-170: RETIRED -- the door-upcoming-rail's per-event RECORD THIS
    one-tap arm and two-beat cancel are PARKED (HS-170-04,
    settled-design-four-faces.md Face 1 Addendum). The arrival's capture bar
    has Schedule (opens ScheduleCreate form, not per-event) + ARMED countdown
    with Cancel. The schedule-create round trip and cancel are covered by
    test_hs144_door_glass::test_upcoming_rail_schedule_create_round_trip_and_form_cancel.
    The per-event one-tap stale-refusal path is intentionally gone.
    """
    pytest.skip(
        "HS-170: door-rail one-tap arm PARKED (HS-170-04); "
        "per-event RECORD THIS gone; Schedule + Cancel at the arrival's capture bar "
        "covered by test_hs144_door_glass::test_upcoming_rail_schedule_create_round_trip_and_form_cancel"
    )
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
            event_ids = _seed_two_events(page, tmp_path)
            page.reload(wait_until="load")
            _normal_chair(page)

            row_a = _event_row(page, "One Tap Standup")
            row_b = _event_row(page, "One Tap Review")
            row_a.get_by_test_id("door-record-this").wait_for()
            row_b.get_by_test_id("door-record-this").wait_for()
            page.screenshot(path=str(SHOTS / "rail-unarmed-1440.png"), full_page=True)

            # ONE TAP: the real button drives the story-01 route.
            row_a.get_by_test_id("door-record-this").click()
            row_a.get_by_test_id("door-armed-chip").wait_for()
            assert row_b.get_by_test_id("door-record-this").is_visible()
            schedules = _api(page, "GET", "/api/scheduled-recordings")["schedules"]
            linked = [s for s in schedules if s.get("calendar_event_id") == event_ids["One Tap Standup"]]
            assert len(linked) == 1, schedules
            assert linked[0]["one_shot"] is True and linked[0]["enabled"] is True
            assert linked[0]["title"] == "One Tap Standup"
            # One intent, one row: the linked schedule never duplicates the
            # armed EVENT row on the rail (HS-147-02 ruling).
            door = _api(page, "GET", "/api/door")
            assert not [
                item for item in door["upcoming"]
                if item["source"] == "scheduled_recording" and item["id"] == linked[0]["id"]
            ], door["upcoming"]
            page.screenshot(path=str(SHOTS / "rail-armed-1440.png"), full_page=True)

            # Two-beat cancel on the armed row.
            row_a.get_by_test_id("door-cancel-prompt").click()
            row_a.get_by_test_id("door-cancel-confirm").wait_for()
            page.screenshot(path=str(SHOTS / "rail-cancel-prompt-1440.png"), full_page=True)
            row_a.get_by_test_id("door-cancel-confirm").click()
            row_a.get_by_test_id("door-record-this").wait_for()
            schedules = _api(page, "GET", "/api/scheduled-recordings")["schedules"]
            assert not [s for s in schedules if s.get("calendar_event_id") == event_ids["One Tap Standup"]]

            # The honest refusal: arm row B out-of-band so its row is stale,
            # then tap the stale RECORD THIS into the live L1 guard.
            _api(page, "POST", "/api/scheduled-recordings", {"calendar_event_id": event_ids["One Tap Review"]})
            row_b.get_by_test_id("door-record-this").click()
            refusal = row_b.get_by_test_id("door-arm-refusal")
            refusal.wait_for()
            assert refusal.inner_text() == "ALREADY ARMED"
            page.screenshot(path=str(SHOTS / "rail-refusal-1440.png"), full_page=True)
            _assert_clean(page, errors)

            # Narrow leg: a FRESH context crosses First Sentence honestly.
            narrow = browser.new_context(viewport={"width": 393, "height": 852})
            npage = narrow.new_page()
            npage.emulate_media(reduced_motion="reduce")
            narrow_errors: list[str] = []
            npage.on("pageerror", lambda error: narrow_errors.append(f"page: {error}"))
            npage.on("console", lambda message: _record_console(narrow_errors, message))
            npage.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _normal_chair(npage)
            nrow_b = _event_row(npage, "One Tap Review")
            nrow_b.get_by_test_id("door-armed-chip").wait_for()
            nrow_a = _event_row(npage, "One Tap Standup")
            nrow_a.get_by_test_id("door-record-this").wait_for()
            npage.screenshot(path=str(SHOTS / "rail-armed-393.png"), full_page=True)
            _assert_clean(npage, narrow_errors)
            narrow.close()
            browser.close()
    finally:
        server.stop()
        reset_database()
