"""HS-169-07 -- Door legs: blank project + cancel.

Ported from test_hs159_interview_glass.py (blank_leg, abandon_leg)
which tested the same live capabilities through the retired interview.
The Door (web/src/features/project-room/door/) replaced the interview.

Blank leg: type outcome, pick zero sources, click Create Project ->
project exists, no watches, no connector_watches rows.

Cancel leg: type outcome, click Cancel -> no project created, Door
window closed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot,
    _api,
    _assert_clean,
    _normal_chair,
    _ensure_build,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="Door legs glass needs Playwright")

TOKEN = "hs169-door-legs"


# ── Helpers ────────────────────────────────────────────────────────


def _open_door(page: Any, url: str) -> None:
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


# ── Tests ──────────────────────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_blank_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Create Project with zero sources -> blank project, no watches (INT-002)."""
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)

            _open_door(page, url)

            door = page.get_by_test_id("door-root")
            door.wait_for(timeout=10000)

            # Type outcome text (enables Create)
            outcome = page.get_by_test_id("door-outcome-input")
            outcome.wait_for(timeout=5000)
            outcome.fill("Blank project for glass test")
            _settle(page)

            # Receipt reads NO SOURCES
            receipt = page.get_by_test_id("door-receipt")
            assert "NO SOURCES" in receipt.inner_text().upper()

            # Click Create Project
            create_btn = page.get_by_test_id("door-create")
            create_btn.click()

            # Wait for the Door to close (project created)
            page.wait_for_timeout(3000)
            _settle(page)

            door_gone = page.evaluate(
                """() => !document.querySelector('[data-testid="door-root"]')"""
            )
            assert door_gone, "Door should close after Create"

            # Verify: project exists
            from holdspeak.db import get_database
            db = get_database()
            with db._connection() as conn:
                projects = conn.execute("SELECT * FROM projects").fetchall()
            assert len(projects) >= 1, f"Expected >= 1 project, got {len(projects)}"

            # Verify: no watches
            with db._connection() as conn:
                watches = conn.execute("SELECT * FROM connector_watches").fetchall()
            assert len(watches) == 0, f"Expected 0 watches for blank project, got {len(watches)}"

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        reset_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_cancel_door(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancel: open Door -> click Cancel -> no project created, Door closes."""
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)

            _open_door(page, url)

            door = page.get_by_test_id("door-root")
            door.wait_for(timeout=10000)

            # Type something so the door has state
            outcome = page.get_by_test_id("door-outcome-input")
            outcome.wait_for(timeout=5000)
            outcome.fill("This will be cancelled")
            _settle(page)

            # Click Cancel
            cancel_btn = page.get_by_test_id("door-cancel")
            cancel_btn.click()

            # Wait for the Door to close
            page.wait_for_timeout(2000)
            _settle(page)

            door_gone = page.evaluate(
                """() => !document.querySelector('[data-testid="door-root"]')"""
            )
            assert door_gone, "Door should close after Cancel"

            # Verify: no project created
            from holdspeak.db import get_database
            db = get_database()
            with db._connection() as conn:
                projects = conn.execute("SELECT * FROM projects").fetchall()
            assert len(projects) == 0, f"Expected 0 projects after cancel, got {len(projects)}"

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        reset_database()
