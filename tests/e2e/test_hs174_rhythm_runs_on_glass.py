"""HS-174-08 -- Rhythm `Runs on` row glass rig.

Tests the Rhythm face's Runs on row at 1440 + 393.
Legs:
  1. The row is present.
  2. Run now appears exactly once on the page (on Sweep, not Runs on).
  3. Caption WHILE THIS MAC IS AWAKE is absent when THIS DEVICE selected.

Shots to phase-174-reach/assets/story-08-shots/.
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

pytest.importorskip("playwright.sync_api", reason="Rhythm glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-174-reach/assets/story-08-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs174-rhythm"


def _open_rhythm(page: Any) -> None:
    """Open the Rhythm / Cadence surface window."""
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["configure-cadence"],
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


def test_runs_on_row_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Runs on row is present at 1440 with no caption when local."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)

    from playwright.sync_api import sync_playwright

    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{url}/?token={TOKEN}")
        _normal_chair(page)
        _open_rhythm(page)
        _settle(page)

        # Runs on row exists
        row = page.locator('[data-testid="rhythm-runs-on-row"]')
        assert row.count() > 0, "Runs on row not found"

        # Caption absent when THIS DEVICE
        caption = page.locator('[data-testid="rhythm-runs-on-caption"]')
        assert caption.count() == 0, "Caption should be absent when local"

        _shot(page, "build-rhythm-runs-on-1440", 1440)
        _assert_clean(page, errors)
        browser.close()


def test_runs_on_row_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The Runs on row is present at 393."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)

    from playwright.sync_api import sync_playwright

    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 393, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{url}/?token={TOKEN}")
        _normal_chair(page)
        _open_rhythm(page)
        _settle(page)

        row = page.locator('[data-testid="rhythm-runs-on-row"]')
        assert row.count() > 0, "Runs on row not found at 393"

        _shot(page, "build-rhythm-runs-on-393", 393)
        _assert_clean(page, errors)
        browser.close()


def test_run_now_appears_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run now button appears exactly once (on Sweep, not on Runs on)."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)

    from playwright.sync_api import sync_playwright

    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{url}/?token={TOKEN}")
        _normal_chair(page)
        _open_rhythm(page)
        _settle(page)

        run_now = page.locator('[data-testid="rhythm-run-now"]')
        assert run_now.count() == 1, (
            f"Run now should appear exactly once, found {run_now.count()}"
        )

        # Runs on row text should NOT contain "Run now"
        runs_on_row = page.locator('[data-testid="rhythm-runs-on-row"]')
        if runs_on_row.count() > 0:
            text = runs_on_row.text_content() or ""
            assert "Run now" not in text, "Run now must NOT be on the Runs on row"

        _shot(page, "build-rhythm-run-now-once-1440", 1440)
        _assert_clean(page, errors)
        browser.close()
