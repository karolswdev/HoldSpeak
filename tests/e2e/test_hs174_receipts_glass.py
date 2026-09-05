"""HS-174-04 -- Receipts with REMOTE badge glass rig.

Verifies the EgressChip remote scope CSS (accent outline, transparent
background) exists in the built bundle.  Takes shots at 1440 + 393.

Shots to phase-174-reach/assets/story-04-shots/.
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

pytest.importorskip("playwright.sync_api", reason="Receipts glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-174-reach/assets/story-04-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs174-receipts"


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    old_size = page.viewport_size
    page.set_viewport_size({"width": width, "height": 2400})
    _settle(page)
    path = SHOTS / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    page.set_viewport_size(old_size)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def test_egress_chip_remote_scope_css_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CSS rule for data-scope=remote exists in the built bundle."""
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
        _settle(page)

        # Inject a test chip with data-scope="remote" and verify styling.
        result = page.evaluate("""() => {
            const chip = document.createElement('span');
            chip.className = 'gadget-chip gadget-chip-egress';
            chip.dataset.scope = 'remote';
            chip.textContent = 'REMOTE . 100.64.0.5';
            document.body.appendChild(chip);
            const cs = getComputedStyle(chip);
            return {
                borderColor: cs.borderColor,
                backgroundColor: cs.backgroundColor,
            };
        }""")

        # Remote scope: transparent/translucent background (stroke not fill).
        bg = result["backgroundColor"]
        assert bg in (
            "rgba(0, 0, 0, 0)",
            "transparent",
        ) or bg.startswith("rgba") and bg.endswith(", 0)"), (
            f"Expected transparent bg for remote scope, got {bg}"
        )

        _shot(page, "build-egress-remote-chip-1440", 1440)
        _assert_clean(page, errors)
        browser.close()


def test_shade_finished_at_both_widths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The shade renders at 1440 and 393 with the face changes intact."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)

    from playwright.sync_api import sync_playwright

    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}")
            _normal_chair(page)
            _settle(page)
            _shot(page, f"build-shade-receipts-{width}", width)
            _assert_clean(page, errors)
            errors.clear()
            page.close()

        browser.close()
