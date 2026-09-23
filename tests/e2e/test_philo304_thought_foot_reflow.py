"""PHILO-3-04 counsel (Astra, RATIFY-WITH-CONDITIONS, condition 1) — the
Thought foot's receipt yields; it never pushes the verbs off the glass.

Above the 560 px container breakpoint the receipt column was `max-content`:
at a 600 px window `DID NOT SAVE · THE HUB DID NOT ACCEPT THE CHANGE` pushed
the verbs' right edge past the window and squeezed READS to zero width, and
a 58-character drawer name overflowed too. JSDOM cannot measure layout, so
this rig loads the BUILT foot on a real hub (its own isolated HOME), names
the drawer with 58 characters, fails the write at the browser boundary with
an HTTP 500, and measures the real geometry.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from scripts.graph_walk import TOKEN, Hub

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(300, method="thread")]

DRAWER = "Architecture decisions for the ingest queue cutover in Q4."  # 58 characters
CAUSE = "DID NOT SAVE · THE HUB DID NOT ACCEPT THE CHANGE"
WRITE = ".thought-note-foot .surface-footer-receipt-line:not([data-line])"

GEOMETRY_JS = """() => {
  const win = document.querySelector('.thought-workspace-window').getBoundingClientRect();
  const box = (sel) => { const e = document.querySelector(sel); if (!e) return null; const r = e.getBoundingClientRect(); return {left: r.left, right: r.right, width: r.width}; };
  const lines = [...document.querySelectorAll('.thought-note-foot .surface-footer-receipt-line')];
  const verbs = [...document.querySelectorAll('.thought-note-foot .surface-footer-verbs button')].map((b) => b.getBoundingClientRect());
  return {
    window: {left: win.left, right: win.right, width: win.width},
    reads: box('.thought-note-foot .surface-footer-egress'),
    receipt: box('.thought-note-foot .surface-footer-receipt'),
    verbs_left: Math.min(...verbs.map((r) => r.left)),
    verbs_right: Math.max(...verbs.map((r) => r.right)),
    clipped: lines.filter((e) => e.scrollWidth > e.clientWidth + 1).map((e) => e.innerText),
    lines: lines.map((e) => e.innerText),
  };
}"""


def _assert_geometry(geo: dict, label: str) -> None:
    right = geo["window"]["right"]
    assert geo["verbs_right"] <= right + 0.5, f"{label}: verbs end at {geo['verbs_right']} past the window's {right}: {geo}"
    assert geo["reads"]["width"] >= 40, f"{label}: READS squeezed to {geo['reads']['width']} px: {geo}"
    assert geo["receipt"]["right"] <= geo["verbs_left"] + 0.5 or geo["receipt"]["left"] >= geo["reads"]["left"], f"{label}: {geo}"
    assert geo["receipt"]["right"] <= right + 0.5, f"{label}: receipt ends past the window: {geo}"
    assert not geo["clipped"], f"{label}: receipt text is clipped, not wrapped: {geo['clipped']}"
    assert geo["lines"][0] == CAUSE, f"{label}: {geo['lines']}"
    assert geo["lines"][1] == f"IN {DRAWER.upper()}", f"{label}: {geo['lines']}"


@pytest.mark.parametrize(("viewport", "window_width"), [(1440, 600), (1440, 700), (1440, None), (393, None)])
def test_the_receipt_yields_to_the_verbs(viewport: int, window_width: int | None) -> None:
    from playwright.sync_api import sync_playwright

    home = Path(tempfile.mkdtemp(prefix="philo304-reflow-home-"))
    profile = Path(tempfile.mkdtemp(prefix="philo304-reflow-profile-"))
    hub = Hub(home).start()
    try:
        with sync_playwright() as play:
            context = play.chromium.launch_persistent_context(
                str(profile), viewport={"width": viewport, "height": 900 if viewport >= 1000 else 852},
                base_url=hub.url)
            page = context.new_page()
            page.goto(f"{hub.url}/?token={TOKEN}")
            try:
                page.get_by_role("button", name="Continue later").click(timeout=8000)
            except Exception:  # noqa: BLE001 — the gate is optional on a returning desk
                pass
            # The desk seeds its Inbox on first load; the thought is filed there.
            page.locator("[data-testid=arrival-develop-thought]").wait_for()
            status, answer = hub.api("PUT", "/api/directories/hs-seed-inbox", {"name": DRAWER})
            assert status == 200, (status, answer)
            page.locator("[data-testid=arrival-develop-thought]").click()
            body = page.locator('[aria-label="Note body"]')
            body.wait_for()
            if window_width:
                page.eval_on_selector(".thought-workspace-window", f"e => {{ e.style.width = '{window_width}px'; }}")
            page.route("**/api/thoughts/*/working", lambda route: route.fulfill(
                status=500, content_type="application/json", body='{"error":"refused"}'))
            body.fill("Drain the queue before the cutover.")
            page.wait_for_function(
                "([sel, want]) => { const e = document.querySelector(sel); return !!e && e.innerText === want; }",
                arg=[WRITE, CAUSE], timeout=15000)
            page.wait_for_timeout(250)
            geo = page.evaluate(GEOMETRY_JS)
            if window_width:
                assert abs(geo["window"]["width"] - window_width) < 1, geo
            context.close()
        _assert_geometry(geo, f"{viewport}/{window_width or 'default'}")
    finally:
        hub.stop()
        shutil.rmtree(profile, ignore_errors=True)
        shutil.rmtree(home, ignore_errors=True)
