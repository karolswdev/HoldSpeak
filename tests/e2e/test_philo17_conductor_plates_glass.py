"""PHILO-17 THE REFIT: the Conductor's plates on a real hub.

The desk sweep's Conductor seed draws no coder that asks, so the NEEDS YOU
plate was proved in vitest only. This file proves it in the browser on the
lane rig (agents_lane_rig: a launch, its Claude Code session that asks, the
drafted answer, the PR) and a held call minted through the real gate route
(`mint_held_call`):

1. the ask plate: ASKS YOU, the question, Answer as the window's one
   primary, at 1440 and 393 (shot);
2. the held plate: WANTS APPROVAL, the command, Approve and Deny, at 1440
   and 393 (shot); Approve decides the call through the gate route and the
   hub records ``approved``.

A separate file, not sweep cases: the sweep's seed is shared by every
window, and an asking coder there changes other windows' counts.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from .agents_lane_rig import QUESTION, TOKEN, _seed, mint_held_call

pytest.importorskip("playwright.sync_api", reason="the Conductor plates glass needs Playwright")

pytestmark = [pytest.mark.e2e]

SIZES = {1440: 900, 393: 852}
SHOTS = "desk-sweep/conductor-plates"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch):
    """(url, seed): a real hub with the lane seed (a launch whose coder asks)."""
    _ensure_build()
    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.delivery.factory_launch as factory_launch
    import holdspeak.delivery.registry as delivery_registry
    from holdspeak.agent_context import event_log
    from holdspeak.services import agent_responder

    state = tmp_path / "home" / ".holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
    monkeypatch.setattr(delivery_registry, "DEFAULT_REGISTRY_PATH", state / "delivery_sources.json")
    monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
    monkeypatch.setattr(agent_responder, "DEFAULT_ANSWERS_PATH", state / "agent_answers.json")
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        yield url, _seed(tmp_path / "home")
    finally:
        server.stop()


def _conductor(pw: Any, url: str, width: int) -> tuple[Any, Any]:
    """(browser, page) with the Conductor open through Go (its real door)."""
    import re

    browser = pw.chromium.launch()
    page = browser.new_page(viewport={"width": width, "height": SIZES[width]})
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    page.reload(wait_until="load")
    _normal_chair(page)
    _settle(page)
    page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
    page.locator("[role^=menuitem]").filter(
        has=page.locator(".desk-menu-label", has_text=re.compile(r"^Conductor$"))).last.click()
    page.locator(".conductor-window").wait_for(timeout=15000)
    return browser, page


def _plate(page: Any) -> Any:
    plate = page.locator(".conductor-window [data-testid='conductor-ask-row'][data-object-id='launch:launch_c2_runbook']")
    plate.wait_for(timeout=20000)
    return plate


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_the_ask_plate_leads_with_answer(hub, width: int) -> None:
    from playwright.sync_api import sync_playwright

    url, _seed_out = hub
    with sync_playwright() as pw:
        browser, page = _conductor(pw, url, width)
        try:
            plate = _plate(page)
            assert plate.locator(".cw-ask-label").inner_text() == "ASKS YOU"
            assert QUESTION[:24] in plate.inner_text()
            answer = plate.get_by_role("button", name="Answer", exact=True)
            assert "btn--primary" in (answer.get_attribute("class") or "")
            # One filled primary in the window.
            assert page.locator(".conductor-window .btn--primary").count() == 1
            plate.scroll_into_view_if_needed()
            page.screenshot(path=str(evidence_dir(SHOTS) / f"needs-you-{width}.png"))
        finally:
            browser.close()


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_the_held_plate_approves_in_one_press(hub, width: int) -> None:
    from playwright.sync_api import sync_playwright

    url, seed = hub
    pid = f"toolu_plate_{width}"
    mint_held_call(url, seed["worktree"], command="cat /etc/review-file", proposal_id=pid)
    with sync_playwright() as pw:
        browser, page = _conductor(pw, url, width)
        try:
            plate = _plate(page)
            plate.locator("[data-testid='conductor-held-call']").wait_for(timeout=20000)
            assert plate.locator(".cw-ask-label").inner_text() == "WANTS APPROVAL"
            assert "cat /etc/review-file" in plate.locator("[data-testid='conductor-held-call']").inner_text()
            approve = plate.get_by_role("button", name="Approve", exact=True)
            assert "btn--primary" in (approve.get_attribute("class") or "")
            assert plate.get_by_role("button", name="Deny", exact=True).is_visible()
            plate.scroll_into_view_if_needed()
            page.screenshot(path=str(evidence_dir(SHOTS) / f"held-{width}.png"))
            with page.expect_response(lambda r: f"/{pid}/decide" in r.url) as got:
                approve.click()
            assert got.value.status == 200, got.value.text()
            assert _api(page, "GET", f"/api/gate/proposals/{pid}", token=TOKEN)["state"] == "approved"
            # The decided call leaves the plate.
            plate.locator("[data-testid='conductor-held-call']").wait_for(state="detached", timeout=20000)
        finally:
            browser.close()


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_the_lane_opens_from_the_plate(hub, width: int) -> None:
    """Answer on the plate opens the coder's lane (shot at both widths)."""
    from playwright.sync_api import sync_playwright

    url, _seed_out = hub
    with sync_playwright() as pw:
        browser, page = _conductor(pw, url, width)
        try:
            _plate(page).get_by_role("button", name="Answer", exact=True).click()
            lane = page.locator(".is-lane")
            lane.wait_for(timeout=15000)
            page.locator("[data-testid='lane-rail']").wait_for(timeout=15000)
            page.locator("[data-testid='lane-ask']").wait_for(timeout=15000)
            page.locator("[data-testid='lane-head']").wait_for(timeout=15000)
            # The window has settled (its open transition ends at opacity 1).
            page.wait_for_function(
                "() => { const el = document.querySelector('.is-lane');"
                " return !!el && getComputedStyle(el).opacity === '1' && getComputedStyle(el).transform === 'none'; }",
                timeout=15000)
            assert "asks you" in page.locator("[data-testid='lane-head']").inner_text()
            page.screenshot(path=str(evidence_dir(SHOTS) / f"lane-{width}.png"))
        finally:
            browser.close()
