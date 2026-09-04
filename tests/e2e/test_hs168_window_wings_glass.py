"""HS-168-05 -- window wings glass: a 70-character project name must NOT
push the wings (TIMELINE, DECISIONS, SEARCH, ASK) past the window edge.

The title shrinks with ellipsis; the wings bounding box stays inside both
the head and the window.  Parametrized at 1440 and 393.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="168 wings glass needs Playwright")

TOKEN = "hs168-wings-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-168-the-connections-door/assets/story-05-shots"

# A project name longer than any reasonable head can show without ellipsis.
LONG_NAME = "A Very Long Project Name That Should Trigger Ellipsis On The Title Bar Here"
assert len(LONG_NAME) >= 70, f"Name is only {len(LONG_NAME)} chars"


# -- helpers -------------------------------------------------------


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)


def _create_project(page: Any) -> str:
    result = _api(page, "POST", "/api/projects", {
        "name": LONG_NAME,
        "description": "Glass test project for HS-168-05 wings layout.",
        "command_id": "hs168-wings-glass",
    }, token=TOKEN)
    return result["project"]["id"]


def _open_project_room(page: Any, url: str, project_id: str) -> None:
    page.evaluate(
        """([key, scope]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key, scope})
          );
        }""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


# -- tests ---------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_wings_inside_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    width: int,
) -> None:
    """Wings bounding box lies inside the head and window at both widths."""
    _ensure_build()
    from playwright.sync_api import sync_playwright

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))

            _init_desk(page, url)
            project_id = _create_project(page)
            _open_project_room(page, url, project_id)

            # Wait for room name to appear
            room_name = page.get_by_test_id("project-room-name")
            room_name.wait_for(timeout=15000)

            _settle(page)

            # Locate the elements
            head = page.locator(".desk-pullout-head.has-wings")
            title = head.locator(".desk-pullout-title")
            wings_loc = head.locator(".desk-wings")
            window = page.locator(".desk-window-shell")

            head.wait_for(timeout=5000)

            head_box = head.bounding_box()
            title_box = title.bounding_box()
            window_box = window.first.bounding_box()

            assert head_box is not None, "head bounding box is null"
            assert title_box is not None, "title bounding box is null"
            assert window_box is not None, "window bounding box is null"

            # At 393, wings may not be visible (compact mode may hide them).
            wings_visible = wings_loc.is_visible()
            wings_box = wings_loc.bounding_box() if wings_visible else None

            # Shoot the window element
            SHOTS.mkdir(parents=True, exist_ok=True)
            shot_path = SHOTS / f"wings-{width}.png"
            window.first.screenshot(path=str(shot_path))

            if wings_box is not None:
                # Wings right edge must be inside the head right edge
                wings_right = wings_box["x"] + wings_box["width"]
                head_right = head_box["x"] + head_box["width"]
                window_right = window_box["x"] + window_box["width"]

                assert wings_right <= head_right + 1, (
                    f"Wings right edge ({wings_right:.0f}) exceeds head right edge "
                    f"({head_right:.0f}) -- wings pushed off the window"
                )
                assert wings_right <= window_right + 1, (
                    f"Wings right edge ({wings_right:.0f}) exceeds window right edge "
                    f"({window_right:.0f})"
                )

                # Wings left edge must be inside the head
                assert wings_box["x"] >= head_box["x"] - 1, (
                    f"Wings left edge ({wings_box['x']:.0f}) is before head left edge "
                    f"({head_box['x']:.0f})"
                )

            # Title must be truncated: scrollWidth > clientWidth (ellipsis fired)
            title_scroll = title.evaluate("el => el.scrollWidth")
            title_client = title.evaluate("el => el.clientWidth")
            assert title_scroll > title_client, (
                f"Title not truncated: scrollWidth={title_scroll}, "
                f"clientWidth={title_client} -- ellipsis did not fire"
            )

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
