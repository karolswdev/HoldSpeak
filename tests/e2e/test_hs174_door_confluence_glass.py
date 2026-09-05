"""HS-174-07 -- Door Confluence row glass rig.

Tests the Door's third source row (C . Confluence) at 1440 + 393.
The Confluence row is visible only when the provider manifest returns
a confluence entry; the test verifies the Door renders without error
and takes shots.

Shots to phase-174-reach/assets/story-07-shots/.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot,
    _assert_clean,
    _normal_chair,
    _ensure_build,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="Door glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-174-reach/assets/story-07-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs174-door-confluence"


def _open_door(page: Any) -> None:
    """Open the Door surface window."""
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["project-setup"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _window(page: Any) -> Any:
    return page.locator(".desk-surface-window").first


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    old_size = page.viewport_size
    page.set_viewport_size({"width": width, "height": 2400})
    _settle(page)
    path = SHOTS / f"{name}.png"
    win = _window(page)
    if win.count() > 0:
        win.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    page.set_viewport_size(old_size)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def test_door_confluence_row_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Door renders at 1440 with Confluence row (if present)."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)

    from playwright.sync_api import sync_playwright

    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{url}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        _settle(page)
        _open_door(page)
        _settle(page)

        # The Door root should be present.
        root = page.locator('[data-testid="door-root"]')
        root.wait_for(timeout=10_000)
        assert root.count() > 0, "Door root not rendered"

        _shot(page, "build-door-confluence-1440", 1440)
        _assert_clean(page, errors)
        browser.close()


def test_door_confluence_row_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Door renders at 393 (phone width)."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)

    from playwright.sync_api import sync_playwright

    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 393, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{url}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        _settle(page)
        _open_door(page)
        _settle(page)

        _shot(page, "build-door-confluence-393", 393)
        _assert_clean(page, errors)
        browser.close()
