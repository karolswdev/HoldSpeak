"""Agents shows the crew the Floor shows (inventory A, defect 9; 2026-10-03).

The roster dropped every seeded agent (Chase, Desk, Draft, ...) and showed
only "New Agent" rows; the DELIVERY tab was a blank window. A real hub with
the product's own seed, read at 1440 and 393.
"""
from __future__ import annotations

from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="glass needs Playwright")

TOKEN = "glass-test"
SHOTS = evidence_dir("pm/evidence/agents-roster")
SHOTS.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def _build():
    _ensure_build()


@pytest.fixture()
def desk(tmp_path, monkeypatch, _build):
    server, base_url = _boot(tmp_path, monkeypatch, token=TOKEN)
    from holdspeak.db import get_database
    from holdspeak.db.seed import apply_seed

    apply_seed(get_database())
    try:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        browser = pw.chromium.launch()

        def open_agents(width: int, height: int) -> Any:
            page = browser.new_context(viewport={"width": width, "height": height}).new_page()
            page.goto(f"{base_url}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            page.evaluate(
                """() => sessionStorage.setItem("hs.desk.staged-surface-open",
                     JSON.stringify({key: "inspect-personas-and-coders"}))"""
            )
            page.reload(wait_until="load")
            _normal_chair(page)
            return page

        yield open_agents
        browser.close()
        pw.stop()
    finally:
        server.stop()


@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_roster_lists_the_floor_agents_and_no_blank_delivery_tab(desk, width, height):
    page = desk(width, height)
    # The Floor's agents: every recipe that is not deleted (web/src/desk/api.ts).
    floor = sorted(
        str(row["name"]) for row in _api(page, "GET", "/api/recipes")["recipes"]
        if not row.get("deleted")
    )
    assert {"Chase", "Desk", "Draft"} <= set(floor), floor

    window = page.locator(".desk-surface-window").first
    window.get_by_text("Chase", exact=True).first.wait_for(timeout=15000)
    crew = window.locator(".surface-ledger-rows").last.locator(".surface-primary, .surface-ledger-primary")
    shown = sorted(set(name.strip() for name in crew.all_inner_texts() if name.strip()))
    assert shown == sorted(set(floor)), (shown, floor)

    # No repository work and no pull request receipts: the wing is withheld.
    assert page.get_by_role("tab", name="Delivery").count() == 0
    assert page.get_by_role("tab", name="Roster").count() == 1
    _settle(page)
    page.screenshot(path=str(SHOTS / f"agents-{width}.png"))
