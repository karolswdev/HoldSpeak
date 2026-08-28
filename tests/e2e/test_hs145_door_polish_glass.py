"""HS-145 Door polish glass proof.

Scroll-hint gradients (Story 01) and the connect-calendar affordance
(Story 02): real hub, production bundle, Playwright assertions + shots.
Helpers reused from the Phase 144 Door glass test.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="glass walk needs Playwright")
pytest.importorskip("fastapi.testclient", reason="glass walk needs web dependencies")

SHOT_DIR = Path(__file__).resolve().parents[2] / "pm/roadmap/holdspeak/phase-145-the-door-polish/assets/story-03-shots"
TOKEN = "hs145-door-polish"


# ---------------------------------------------------------------------------
# Shared helpers (lifted from test_hs144_door_glass.py)
# ---------------------------------------------------------------------------

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


def _record_console(errors: list[str], message: Any) -> None:
    if message.type == "error":
        errors.append(f"console: {message.text}")


def _start_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
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


def _normal_chair(page: Any) -> None:
    chair = page.locator(".chair")
    chair.wait_for()
    if chair.evaluate("element => element.classList.contains('chair-first-value')"):
        page.get_by_role("button", name="Continue later", exact=True).click()
    page.locator(".chair:not(.chair-first-value)").wait_for()


def _seed_populated_door(page: Any) -> None:
    """Seed enough sources to populate the board's five columns."""
    import uuid
    from datetime import date

    now = datetime.now(timezone.utc)
    today = date.today()
    meeting_id = "hs145-door-polish-meeting"
    action_rows = [
        ("hs145-overdue", "Overdue polish task", "Ada", today - timedelta(days=1)),
        ("hs145-now", "Review today", "Bea", today),
        ("hs145-waiting", "Prepare next week", "Cy", today + timedelta(days=5)),
        ("hs145-unassigned", "Needs an owner", None, None),
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
                "title": "Polish planning",
                "tags": [],
                "segments": [],
                "bookmarks": [],
                "capture_status": "finalized",
                "transcription_status": "active",
                "provenance": "native",
                "intel": {
                    "timestamp": now.timestamp(),
                    "topics": ["polish"],
                    "summary": "Populated board for the scroll hint.",
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

    seeded = _api(page, "POST", "/api/desk/seed")
    assert "total" in seeded
    _api(page, "POST", "/api/thoughts", {
        "request_id": str(uuid.uuid4()),
        "raw_text": "Active thought for scroll hint proof.",
        "source": {"kind": "typed"},
        "initial_note": {
            "title": "Polish active thought",
            "body_markdown": "Active thought for scroll hint proof.",
            "tags": [],
        },
    })


# ---------------------------------------------------------------------------
# LEG 1 + 2: Scroll hint gradient at 393 and 1440
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_hs145_scroll_hint_gradient_393_and_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Populated board: gradient overlays clipped columns at 393, absent at 1440."""
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
            _seed_populated_door(page)
            page.reload(wait_until="load")
            _normal_chair(page)

            door = page.locator(".door-board-section")
            door.wait_for()
            viewport = door.locator(".door-board-viewport")
            viewport.wait_for()

            # The attribute lives on the wrapper, not the viewport itself.
            hint_wrap = door.locator(".door-board-hint-wrap")
            hint_wrap.wait_for()

            # --- LEG 2: 1440 — no scroll needed, no hint ---
            # The rAF-based effect fires after paint; wait for the attribute.
            page.wait_for_timeout(500)
            hint_1440 = hint_wrap.get_attribute("data-scroll-hint")
            assert hint_1440 == "none", f"Expected none at 1440, got {hint_1440}"

            # Pseudo-element height check: at hint=none, pseudo-elements have
            # display: none so computed height is 0/auto.
            after_height_1440 = hint_wrap.evaluate(
                "el => getComputedStyle(el, '::after').height"
            )
            before_height_1440 = hint_wrap.evaluate(
                "el => getComputedStyle(el, '::before').height"
            )
            assert after_height_1440 in ("0px", "auto"), f"::after height at 1440: {after_height_1440}"
            assert before_height_1440 in ("0px", "auto"), f"::before height at 1440: {before_height_1440}"

            _assert_clean(page, errors)
            page.screenshot(path=str(SHOT_DIR / "board-hint-none-1440.png"), full_page=False)

            # --- LEG 1a: 393 — initial load, right hint ---
            page.set_viewport_size({"width": 393, "height": 900})
            page.wait_for_timeout(500)
            hint_right = hint_wrap.get_attribute("data-scroll-hint")
            assert hint_right == "right", f"Expected right at 393 initial, got {hint_right}"

            after_info = hint_wrap.evaluate(
                """el => {
                  const s = getComputedStyle(el, '::after');
                  return { display: s.display, height: s.height };
                }"""
            )
            assert after_info["display"] != "none", f"::after not displayed: {after_info}"
            # Height must be a resolved pixel value > 0
            height_str = after_info["height"]
            assert height_str != "0px" and height_str != "auto", (
                f"::after height is {height_str} — gradient is invisible"
            )

            # Confirm no layout shift: the grid should not be pushed down by
            # the pseudo-element. The viewport top should align with the
            # wrapper top (within padding tolerance).
            grid_shift = viewport.evaluate(
                """el => {
                  const wrap = el.parentElement;
                  if (!wrap) return null;
                  const wr = wrap.getBoundingClientRect();
                  const vp = el.getBoundingClientRect();
                  return { viewportTop: vp.top, wrapTop: wr.top };
                }"""
            )
            assert grid_shift is not None
            assert abs(grid_shift["viewportTop"] - grid_shift["wrapTop"]) < 2, (
                f"Viewport shifted by pseudo-element: {grid_shift}"
            )

            _assert_clean(page, errors)
            page.screenshot(path=str(SHOT_DIR / "board-hint-right-393.png"), full_page=False)

            # --- LEG 1b: scroll to middle → both ---
            viewport.evaluate(
                "el => el.scrollTo({ left: Math.floor(el.scrollWidth / 3) })"
            )
            page.wait_for_timeout(300)
            hint_both = hint_wrap.get_attribute("data-scroll-hint")
            assert hint_both == "both", f"Expected both mid-scroll, got {hint_both}"
            _assert_clean(page, errors)
            page.screenshot(path=str(SHOT_DIR / "board-hint-both-393.png"), full_page=False)

            # --- LEG 1c: scroll fully right → left ---
            viewport.evaluate(
                "el => el.scrollTo({ left: el.scrollWidth })"
            )
            page.wait_for_timeout(500)
            hint_left = hint_wrap.get_attribute("data-scroll-hint")
            assert hint_left == "left", f"Expected left fully scrolled, got {hint_left}"
            _assert_clean(page, errors)
            page.screenshot(path=str(SHOT_DIR / "board-hint-left-393.png"), full_page=False)

            browser.close()
    finally:
        server.stop()
        reset_database()


# ---------------------------------------------------------------------------
# LEG 3 + 4: Connect-calendar affordance and configured-but-quiet
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_hs145_connect_calendar_affordance_and_quiet_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty rail without calendar shows the connect affordance; with calendar shows quiet."""
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

            # Verify the Door reads calendar_configured from the API.
            door_data = _api(page, "GET", "/api/door")
            assert door_data["calendar_configured"] is False

            door = page.locator(".door-board-section")
            rail = door.locator(".door-upcoming-rail")

            # --- LEG 3: No calendar → connect affordance at 1440 ---
            rail.get_by_text("No calendar connected.", exact=True).wait_for()
            connect_btn = rail.get_by_role("button", name="Connect calendar", exact=True)
            assert connect_btn.is_visible()
            assert rail.get_by_text("No future time scheduled.", exact=True).count() == 0
            _assert_clean(page, errors)
            page.screenshot(path=str(SHOT_DIR / "rail-connect-1440.png"), full_page=False)

            # At 393
            page.set_viewport_size({"width": 393, "height": 900})
            rail.get_by_text("No calendar connected.", exact=True).wait_for()
            assert connect_btn.is_visible()
            _assert_clean(page, errors)
            page.screenshot(path=str(SHOT_DIR / "rail-connect-393.png"), full_page=False)

            # Click → Settings opens scoped to Meetings
            page.set_viewport_size({"width": 1440, "height": 900})
            connect_btn.click()
            settings = page.locator("#surface-settings")
            settings.wait_for()
            # The Meetings module shows the Calendar subscription input.
            # Scope to the settings container to avoid matching text elsewhere.
            settings.get_by_role(
                "textbox", name="Calendar subscription", exact=True,
            ).wait_for()
            _assert_clean(page, errors)
            page.screenshot(path=str(SHOT_DIR / "rail-connect-settings-open-1440.png"), full_page=False)

            # Close settings for the next leg.
            page.get_by_role("button", name="Close Settings", exact=True).click()
            settings.wait_for(state="detached")

            # --- LEG 4: Configured-but-quiet calendar ---
            # Write a minimal ICS with ONLY a past event (no future events).
            past = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(hours=2)
            past_end = past + timedelta(minutes=30)
            fixture = tmp_path / "empty-calendar.ics"
            fixture.write_text(
                "\r\n".join([
                    "BEGIN:VCALENDAR",
                    "VERSION:2.0",
                    "PRODID:-//HoldSpeak//HS-145 polish//EN",
                    "BEGIN:VEVENT",
                    "UID:hs145-past-only",
                    f"DTSTART:{past.strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTEND:{past_end.strftime('%Y%m%dT%H%M%SZ')}",
                    "SUMMARY:Past event only",
                    "END:VEVENT",
                    "END:VCALENDAR",
                    "",
                ]),
                encoding="utf-8",
            )
            saved = _api(page, "PUT", "/api/settings", {
                "calendar": {"subscription": str(fixture)},
            })
            assert saved["settings"]["_calendar_subscription"]["kind"] == "file"

            from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
            assert CalendarIngestConductor().refresh() is True

            # Verify the API now reports configured.
            door_data = _api(page, "GET", "/api/door")
            assert door_data["calendar_configured"] is True
            # Past event only → no upcoming items.
            assert len(door_data["upcoming"]) == 0

            page.reload(wait_until="load")
            _normal_chair(page)
            door = page.locator(".door-board-section")
            rail = door.locator(".door-upcoming-rail")
            rail.get_by_text("No future time scheduled.", exact=True).wait_for()
            assert rail.get_by_text("No calendar connected.", exact=True).count() == 0
            assert rail.get_by_role("button", name="Connect calendar").count() == 0
            _assert_clean(page, errors)
            page.screenshot(path=str(SHOT_DIR / "rail-quiet-1440.png"), full_page=False)

            browser.close()
    finally:
        server.stop()
        reset_database()
