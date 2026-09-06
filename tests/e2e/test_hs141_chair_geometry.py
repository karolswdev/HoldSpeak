"""Real-browser geometry proof for the Chair working band.

HS-170-04 RE-POINT: the arrival replaces the Chair hero/lanes. The capture
surface is now the arrival-capture-bar (Talk, Develop a thought, Record
meeting, Schedule). The thought-entry test-id, More capture options, Open
advanced capture, and the door-board-column are all parked. The geometry
assertion checks the arrival's capture bar stays inside the chrome, and a
real Thought appears in the THOUGHTS section.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="glass walk needs Playwright")
pytest.importorskip("fastapi.testclient", reason="glass walk needs web dependencies")

ASSETS = Path(__file__).resolve().parents[2] / "pm/roadmap/holdspeak/phase-141-from-thought-to-work/assets/story-05a"
TOKEN = "hs141-chair-geometry-glass"
VIEWPORTS = (
    (1440, 900, "1440x900"),
    (393, 900, "393x900"),
    (393, 667, "393x667"),
)


def _api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body]) => {
          const response = await fetch(path, {
            method,
            headers: {
              'authorization': 'Bearer hs141-chair-geometry-glass',
              ...(body ? {'content-type': 'application/json'} : {}),
            },
            body: body ? JSON.stringify(body) : undefined,
          });
          return {status: response.status, payload: await response.json()};
        }""",
        [method, path, body],
    )
    assert result["status"] < 300, result
    return result["payload"]


def _assert_clean(page: Any, errors: list[str]) -> None:
    assert not errors, errors
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert page.evaluate("document.body.scrollWidth <= window.innerWidth")


def _assert_working_band(page: Any) -> None:
    """HS-170-04 re-point: the arrival's capture bar replaces the thought-entry
    as the interactive bottom element that must stay above the dock.
    """
    geometry = page.evaluate(
        """() => {
          const chair = document.querySelector('.chair:not(.chair-first-value)');
          const bar = document.querySelector('[data-testid="arrival-capture-bar"]');
          const menubar = document.querySelector('.desk-menubar');
          const dock = document.querySelector('.desk-dock');
          if (!chair || !bar || !menubar || !dock) return null;
          const c = chair.getBoundingClientRect();
          const b = bar.getBoundingClientRect();
          const m = menubar.getBoundingClientRect();
          const d = dock.getBoundingClientRect();
          const style = getComputedStyle(document.documentElement);
          return {
            chairTop: c.top,
            chairBottom: c.bottom,
            barTop: b.top,
            barBottom: b.bottom,
            menubarBottom: m.bottom,
            dockTop: d.top,
            viewportHeight: innerHeight,
            workTop: parseFloat(style.getPropertyValue('--desk-work-top')),
            workBottom: parseFloat(style.getPropertyValue('--desk-work-bottom')),
          };
        }"""
    )
    assert geometry is not None
    assert geometry["workTop"] == 54
    assert geometry["workBottom"] == 52
    assert geometry["chairTop"] >= geometry["workTop"] - 0.5, geometry
    assert geometry["barTop"] >= max(geometry["workTop"], geometry["menubarBottom"]), geometry
    # The Chair box ends at the canonical work-band boundary. The Dock has a
    # decorative raised edge above that token, so collision is judged on the
    # interactive capture surface rather than the transparent Chair box.
    assert geometry["chairBottom"] <= geometry["viewportHeight"] - geometry["workBottom"] + 0.5, geometry
    assert geometry["barBottom"] <= geometry["dockTop"], geometry


def _assert_hit(page: Any, name: str) -> None:
    control = page.get_by_role("button", name=name, exact=True)
    control.wait_for()
    control.scroll_into_view_if_needed()
    assert control.evaluate(
        """el => {
          const r = el.getBoundingClientRect();
          const x = r.left + r.width / 2;
          const y = r.top + r.height / 2;
          const hit = document.elementFromPoint(x, y);
          const dock = document.querySelector('.desk-dock')?.getBoundingClientRect();
          return r.left >= 0 && r.right <= innerWidth && r.top >= 0 &&
            (!dock || r.bottom <= dock.top) && !!hit && (hit === el || el.contains(hit));
        }"""
    ), f"{name} must remain wholly visible and hit-testable"


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_normal_chair_stays_inside_chrome_at_all_owner_widths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from playwright.sync_api import sync_playwright
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    db_path = tmp_path / "holdspeak.db"
    browser_cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", db_path)
    reset_database()
    callbacks = WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {})
    server = MeetingWebServer(callbacks, auth_token=TOKEN)
    url = server.start()
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")

            # Leave first value through the real owner action. This applies the
            # ordinary seed and reveals the normal Chair without test fixtures.
            page.get_by_role("button", name="Continue later", exact=True).click()
            # HS-170-04: the arrival's capture bar carries Develop a thought.
            page.get_by_test_id("arrival-capture-bar").wait_for()

            for width, height, label in VIEWPORTS:
                page.set_viewport_size({"width": width, "height": height})
                page.reload(wait_until="load")
                page.get_by_test_id("arrival-capture-bar").wait_for()
                _assert_working_band(page)
                # HS-170-04: the capture bar's verbs replace "More capture options".
                _assert_hit(page, "Develop a thought")
                _assert_hit(page, "Record meeting")
                _assert_clean(page, errors)
                ASSETS.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(ASSETS / f"chair-working-band-empty-{label}.png"), full_page=False)

            # A real unfinished Thought now appears in the arrival's THOUGHTS
            # section, not the parked Door board's Active column.
            _api(page, "POST", "/api/thoughts", {
                "request_id": str(uuid.uuid4()),
                "raw_text": "Keep the Chair capture surface clear of global chrome.",
                "source": {"kind": "typed"},
                "initial_note": {
                    "title": "Chair geometry",
                    "body_markdown": "Keep the Chair capture surface clear of global chrome.",
                    "tags": [],
                },
            })

            for width, height, label in VIEWPORTS:
                page.set_viewport_size({"width": width, "height": height})
                page.reload(wait_until="load")
                page.get_by_test_id("arrival-capture-bar").wait_for()
                # HS-170-04: the thought shows in the THOUGHTS section.
                thoughts = page.get_by_test_id("arrival-thoughts")
                thoughts.wait_for(timeout=10_000)
                thought_row = page.get_by_test_id("arrival-thought-row").filter(has_text="Chair geometry")
                thought_row.wait_for(timeout=10_000)
                # The parked door board columns are absent.
                assert page.locator(".door-board-column").count() == 0
                _assert_working_band(page)
                _assert_hit(page, "Develop a thought")
                _assert_hit(page, "Record meeting")

                # HS-170-04: the Schedule verb on the capture bar replaces the
                # retired "Open advanced capture".
                _assert_hit(page, "Schedule")
                _assert_clean(page, errors)
                page.screenshot(path=str(ASSETS / f"chair-working-band-populated-{label}.png"), full_page=False)
            browser.close()
    finally:
        server.stop()
