"""PHILO-17 — Today, the day as a timeline (owner pick, concept C), on glass.

One press each, on the sweep's seeded desk (its own hub; this module writes):
  * Today opens from the dock between the desk's icon columns: it covers no
    icon of the left column and no icon of the right column (Needs you).
  * Open prep opens the 1:1's person on the Prep lens.
  * Make the summary (here Choose engine: the rig has no engine) opens Runs
    on.
  * Confirm on the To decide plate records the answer: the proposal is
    confirmed in the hub's database, and the plate leaves.
"""
from __future__ import annotations

import re
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="the Today glass needs Playwright")

from tests._evidence import evidence_dir  # noqa: E402

from .glass_infra import _normal_chair, clear_hub_windows_http  # noqa: E402
from .test_desk_sweep import SETTLED_JS, T, TOKEN, _page, desk, pw_browser  # noqa: E402,F401

pytestmark = [pytest.mark.e2e]

TODAY = '[id="pullout:intelligence:desk"]'


def _open_today(pw_browser: Any, base: str, width: int) -> tuple[Any, Any]:
    clear_hub_windows_http(base, TOKEN)
    ctx, page, _errors, _requests = _page(pw_browser, width, base)
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _normal_chair(page)
    page.wait_for_function(SETTLED_JS, arg=None, timeout=T)
    page.locator(".desk-dock-launch[aria-label^='Today']").first.click()
    page.locator(f"{TODAY} [data-testid=today-day]").wait_for(timeout=T)
    return ctx, page


@pytest.mark.timeout(240)
def test_today_opens_between_the_icon_columns(desk: dict[str, Any], pw_browser: Any) -> None:
    ctx, page = _open_today(pw_browser, desk["base"], 1440)
    try:
        page.wait_for_function(SETTLED_JS, arg="pullout:intelligence:desk", timeout=T)
        box = page.locator(TODAY).bounding_box()
        assert box, "Today is not drawn"
        icons = page.evaluate("""() => [...document.querySelectorAll('.desk-icon')]
          .filter((e) => !e.closest('.desk-window, .desk-dock'))
          .map((e) => { const r = e.getBoundingClientRect();
            return {name: (e.textContent || '').trim().slice(0, 30), left: r.left, right: r.right, top: r.top, bottom: r.bottom,
                    placed: Boolean(e.closest('.desk-screen-placed'))}; })
          .filter((r) => r.right > r.left)""")
        columns = [i for i in icons if i["right"] <= 160 or (i["placed"] and i["left"] >= 1440 * 0.75)]
        assert any(i["left"] >= 1440 * 0.75 for i in columns), icons
        covered = [i["name"] for i in columns
                   if i["left"] < box["x"] + box["width"] and i["right"] > box["x"]
                   and i["top"] < box["y"] + box["height"] and i["bottom"] > box["y"]]
        assert not covered, (box, covered)
        page.screenshot(path=str(evidence_dir("today") / "today-seat-1440.png"))
    finally:
        ctx.close()


@pytest.mark.timeout(240)
def test_open_prep_and_make_the_summary_land_in_one_press(desk: dict[str, Any], pw_browser: Any) -> None:
    ctx, page = _open_today(pw_browser, desk["base"], 1440)
    try:
        today = page.locator(TODAY)
        today.get_by_test_id("today-open-prep").click()
        person = page.locator(f'[id="pullout:people:{desk["person"]}"]')
        person.wait_for(timeout=T)
        person.get_by_role("tab", name="Prep").and_(person.locator("[aria-selected=true]")).wait_for(timeout=T)

        finish = today.get_by_test_id("today-finish").first
        verb = finish.get_by_role("button", name=re.compile(r"^(Make the summary|Choose engine)$"))
        if verb.inner_text().strip() == "Choose engine":
            verb.click()
            page.locator('[id="surface-concierge"]').wait_for(timeout=T)
        else:  # an engine is set: the run starts from the row
            with page.expect_response(lambda r: "/intel" in r.url and r.request.method == "POST", timeout=T):
                verb.click()
    finally:
        ctx.close()


@pytest.mark.timeout(240)
def test_confirm_records_the_decision(desk: dict[str, Any], pw_browser: Any) -> None:
    from holdspeak.db import get_database

    ctx, page = _open_today(pw_browser, desk["base"], 1440)
    try:
        plate = page.locator(TODAY).get_by_test_id("today-decide")
        plate.wait_for(timeout=T)
        title = plate.locator(".today-decide-title").inner_text().strip()
        page.screenshot(path=str(evidence_dir("today") / "today-decide-1440.png"))
        with page.expect_response(lambda r: r.url.endswith("/confirm") and r.request.method == "POST", timeout=T) as answer:
            plate.get_by_role("button", name="Confirm").click()
        assert answer.value.ok, answer.value.status
        confirmed = [p.text for p in get_database().proposals.list_proposals(state="confirmed")]
        assert title in confirmed, (title, confirmed)
        page.wait_for_function(
            "(t) => ![...document.querySelectorAll('[data-testid=today-decide] .today-decide-title')].some((e) => e.textContent.trim() === t)",
            arg=title, timeout=T)
    finally:
        ctx.close()
