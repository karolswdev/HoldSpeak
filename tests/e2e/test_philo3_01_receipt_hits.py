"""PHILO-3-01 (Astra round 2, condition 3) -- the write receipt's verbs own their areas.

Three real consumers of the ONE receipt (web/src/desk/hooks/useWriteReceipt.ts),
each driven to a real failure on a real rig hub (scripts/graph_walk.py Hub, a
fresh HOME) with the fault injected at the BROWSER boundary (Playwright
page.route; the hub never sees the faulted request):

  * the chrome receipt  -- Search > New Decision, POST /api/decisions -> 500
  * a Thread receipt    -- New Thread, rename, PATCH /api/threads/<id> -> 500
  * a footer receipt    -- the Brief view (SurfaceFooter), Acknowledge,
                           POST /api/brief/items/<id>/shelf -> 500

For each of Retry and OK: nine points (center, four edge midpoints, four
corners) of the area the verb must own -- 44 x 44 px at 393 (the library
Button's halo, global.css HS-202-05), the painted face at 1440 (no halo
there) -- under both instruments of test_hs202_05_button_hit_ownership.py:
`elementFromPoint` (the shared classifier) and a real pointer that must
reach exactly this Button. The two verbs' areas must not intersect. The
label and verbs obey the 12 px floor.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from tests.e2e.test_hs202_05_button_hit_ownership import OWNERSHIP_JS, PROBES, _overlap

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(600, method="thread")]

REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/assets/story-01-shots/receipt-hits"

_spec = importlib.util.spec_from_file_location("graph_walk_receipt_hits", REPO / "scripts/graph_walk.py")
gw = importlib.util.module_from_spec(_spec)
sys.modules["graph_walk_receipt_hits"] = gw
_spec.loader.exec_module(gw)

VIEWPORTS = {1440: {"width": 1440, "height": 900}, 393: {"width": 393, "height": 852}}

_GEOMETRY = """([id, hit]) => {
  const el = document.querySelector(`[data-probe="${id}"]`);
  const r = el.getBoundingClientRect();
  const halfW = Math.max(hit, r.width) / 2, halfH = Math.max(hit, r.height) / 2;
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  return { painted: { w: r.width, h: r.height },
           area: { left: cx - halfW, right: cx + halfW, top: cy - halfH, bottom: cy + halfH },
           cx, cy, halfW, halfH,
           font: parseFloat(getComputedStyle(el).fontSize) };
}"""

_OWNS = """([id, x, y]) => {
""" + OWNERSHIP_JS + """
  const el = document.querySelector(`[data-probe="${id}"]`);
  const seen = hs202Classify(el, x, y);
  return { owner: seen.owner, outcome: seen.outcome };
}"""

# A window capture listener runs before React's root listener: it records
# which probed Button a real click reached and stops the product acting on it.
_TRAP = """() => {
  window.__fired = [];
  if (window.__trap) return;
  window.__trap = true;
  window.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-probe]');
    window.__fired.push(b ? b.dataset.probe : (e.target.className || e.target.tagName));
    e.stopPropagation(); e.preventDefault();
  }, true);
}"""


def _points(g: dict) -> list[tuple[float, float, str]]:
    out = []
    for fx, fy in PROBES:
        out.append((g["cx"] + fx * (g["halfW"] - 1), g["cy"] + fy * (g["halfH"] - 1),
                    {(0, 0): "center"}.get((fx, fy), f"({fx:+d},{fy:+d})")))
    return out


def _fault(page, method: str, prefix: str) -> None:
    def handler(route):
        req = route.request
        from urllib.parse import urlsplit
        if req.method == method and urlsplit(req.url).path.startswith(prefix):
            route.fulfill(status=500, content_type="application/json", body='{"error":"substituted"}')
        else:
            route.fallback()
    page.route("**/*", handler)


def _search(page, query: str, option: str) -> None:
    page.locator("[aria-controls=desk-tool-shelf]").click()
    page.locator("[aria-controls=desk-palette-listbox]").fill(query)
    page.locator(option).first.click()


def _probe(page, scope: str, name: str, width: int, failures: list[str]) -> None:
    receipt = page.locator(f"{scope} .write-receipt").first
    receipt.wait_for(state="visible", timeout=15000)
    # the receipt seats with an animation (write-receipt.css receipt-seat);
    # geometry read mid-flight is not the geometry a press meets
    receipt.evaluate("e => Promise.all(e.getAnimations({ subtree: true }).map(a => a.finished))")
    page.wait_for_timeout(100)
    label_px = receipt.locator(".write-receipt-label").evaluate("e => parseFloat(getComputedStyle(e).fontSize)")
    if label_px < 12:
        failures.append(f"{name}@{width}: label is {label_px}px, under the 12 px floor")
    ids = []
    for cls in ("write-receipt-retry", "write-receipt-dismiss"):
        pid = f"{name}-{cls}"
        receipt.locator(f".{cls}").evaluate(f"(e) => e.dataset.probe = '{pid}'")
        ids.append(pid)
    page.evaluate(_TRAP)
    hit = 44 if width <= 420 else 0
    geo = {i: page.evaluate(_GEOMETRY, [i, hit]) for i in ids}
    for i in ids:
        g = geo[i]
        if g["font"] < 12:
            failures.append(f"{i}@{width}: verb is {g['font']}px, under the 12 px floor")
        for x, y, where in _points(g):
            if not (0 <= x < VIEWPORTS[width]["width"] and 0 <= y < VIEWPORTS[width]["height"]):
                failures.append(f"{i}@{width}: {where} ({x:.1f},{y:.1f}) is off the screen")
                continue
            seen = page.evaluate(_OWNS, [i, x, y])
            if seen["outcome"] != "own":
                stack = page.evaluate(
                    "([x, y, id]) => { const el = document.querySelector(`[data-probe=\"${id}\"]`);"
                    " const r = el.getBoundingClientRect(); const a = getComputedStyle(el, '::after');"
                    " return { stack: document.elementsFromPoint(x, y).slice(0, 4).map(e => (e.className || e.tagName).toString().slice(0, 40)),"
                    " face: [r.top, r.bottom], halo: [a.content, a.height] }; }", [x, y, i])
                failures.append(f"{i}@{width}: {where} ({x:.1f},{y:.1f}) -> {seen['owner']!r} [{seen['outcome']}] {stack}")
                continue
            page.evaluate("window.__fired = []")
            page.mouse.click(x, y)
            fired = page.evaluate("window.__fired")
            if fired != [i]:
                failures.append(f"{i}@{width}: a real pointer at {where} reached {fired!r}")
    if _overlap(geo[ids[0]]["area"], geo[ids[1]]["area"]):
        failures.append(f"{name}@{width}: Retry and OK areas intersect")
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))


def _row_law(page, failures: list[str]) -> None:
    """The row is in the flow between the bar and the work, full width, its
    label whole; the Chair starts below it; the bar holds no receipt."""
    fact = page.evaluate("""() => {
      const row = document.querySelector('.desk-receipt-row');
      const bar = document.querySelector('.desk-menubar');
      const chair = document.querySelector('.chair');
      const label = row.querySelector('.write-receipt-label');
      const rr = row.getBoundingClientRect(), br = bar.getBoundingClientRect();
      const cr = chair ? chair.getBoundingClientRect() : null;
      return { position: getComputedStyle(row).position, rowTop: rr.top, rowBottom: rr.bottom,
               rowLeft: rr.left, rowRight: rr.right, barBottom: br.bottom, vw: innerWidth,
               chairTop: cr && cr.top, labelClipped: label.scrollWidth > label.clientWidth + 1,
               labelFont: parseFloat(getComputedStyle(label).fontSize),
               barReceipt: !!document.querySelector('.desk-menubar .write-receipt') };
    }""")
    if fact["position"] not in ("static", "relative"):
        failures.append(f"row@393: position {fact['position']}, not in the flow")
    if fact["rowTop"] < fact["barBottom"]:
        failures.append(f"row@393: top {fact['rowTop']} is under the bar ({fact['barBottom']})")
    if fact["rowLeft"] > 16.5 or fact["rowRight"] < fact["vw"] - 16.5:
        failures.append(f"row@393: {fact['rowLeft']}..{fact['rowRight']} is not full width")
    if fact["chairTop"] is not None and fact["chairTop"] < fact["rowBottom"]:
        failures.append(f"row@393: the Chair starts at {fact['chairTop']}, inside the row")
    if fact["labelClipped"]:
        failures.append("row@393: the label is cut")
    if fact["barReceipt"]:
        failures.append("row@393: the bar still holds a receipt")


@pytest.fixture(scope="module")
def hub():
    home = Path(tempfile.mkdtemp(prefix="philo3-receipt-hits-"))
    h = gw.Hub(home).start()
    try:
        yield h
    finally:
        h.stop()


@pytest.mark.parametrize("width", [1440, 393])
def test_receipt_verbs_own_their_areas(hub, width: int) -> None:
    failures: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport=VIEWPORTS[width])
        page.emulate_media(reduced_motion="reduce")
        page.goto(f"{hub.url}/?token={hub.token}")
        try:
            page.get_by_role("button", name="Continue later").click(timeout=4000)
        except Exception:
            pass
        page.locator("[aria-controls=desk-tool-shelf]").wait_for(timeout=15000)

        # 1. the chrome receipt (the desk backstop)
        _fault(page, "POST", "/api/decisions")
        _search(page, "New Decision", "[id='desk-palette-option-desk.new-decision']")
        # the owner's ruling (2026-09-23): at phone width the backstop is a
        # full-width row in the desk flow, not a seat in the bar
        seat = ".desk-receipt-row" if width <= 720 else ".desk-chrome-receipt"
        _probe(page, seat, "chrome", width, failures)
        if width <= 720:
            _row_law(page, failures)
        page.unroute("**/*")
        page.reload()
        page.locator("[aria-controls=desk-tool-shelf]").wait_for(timeout=15000)

        # 2. a Thread receipt (in flow in the pullout)
        _search(page, "New Thread", "[id='desk-palette-option-desk.new-thread']")
        page.locator(".thread-title").first.click()
        _fault(page, "PATCH", "/api/threads/")
        page.locator("input[aria-label='Thread title']").fill("Renamed")
        page.keyboard.press("Enter")
        _probe(page, ".desk-pullout", "thread", width, failures)
        page.unroute("**/*")
        page.reload()
        page.locator("[aria-controls=desk-tool-shelf]").wait_for(timeout=15000)

        # 3. a footer receipt (the Brief view's SurfaceFooter)
        status, _ = hub.api("POST", "/api/decisions", {"title": "Receipt hit material", "status": "proposed"})
        assert status == 201
        # the brief is made through the hub's own route (the Chair's Generate
        # is J10's case; at 393 the open Thread sheet covers the Chair here)
        status, _ = hub.api("POST", "/api/brief/generate", {})
        assert status in (200, 201), status
        _search(page, "Show today's brief", "[id='desk-palette-option-desk.intelligence-brief']")
        page.locator(".intelligence-brief-sf-primary").first.click()
        _fault(page, "POST", "/api/brief/items/")
        page.get_by_role("button", name="Acknowledge").first.click()
        _probe(page, ".surface-footer-receipt", "brief-footer", width, failures)
        browser.close()
    assert not failures, "\n".join(failures)
