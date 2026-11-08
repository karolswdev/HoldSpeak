"""The Walk, AS RENDERED: the marked part takes the pointer.

The first walk on the owner's desk (2026-11-07, "totally doesn't work"): the
ring marked New program, but a press on it went to the dim backdrop (a
clip-path cut-out Chromium's hit test did not honour). Only a real browser
proves the hit test, so this is T4: a walk made through the hub
(``POST /api/walks``) marks ``programs-new``; the part takes the pointer two
frames after its window moves; a plain press (no force) on it opens the wizard
(its first step shows). Direction C (2026-11-08): the mark is the part's own
warm halo and nothing dims, so a point far from the part is the desk's, not
the walk's. At 1440 x 900 and 393 x 844.

The hand-held walk (2026-11-08, the owner on his iPhone): on an iPhone
viewport (430 x 932, scale 3, touch) the warm edge sits inside the safe
area, a ``press`` step really opens the well (the guide's cursor travels with
its trail; no hand of the test presses New program), and the stored shot is
the whole viewport at the capture scale. Every other face of the walk is T2
(``web/src/desk/walk/__tests__/walk.app.test.tsx``).
"""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _boot, _ensure_build, _normal_chair

pytest.importorskip("playwright.sync_api", reason="the walk glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "walk-glass"
T = 20_000

# The first point (of a few far ones) outside the marked part and the card,
# and the element the browser hits there.
_FAR_HIT_JS = """
() => {
  const pad = 12;
  const part = document.querySelector('.walk-halo').getBoundingClientRect();
  const card = document.querySelector('[data-testid="walk-card"]').getBoundingClientRect();
  const inside = (box, x, y) => x >= box.left - pad && x <= box.right + pad && y >= box.top - pad && y <= box.bottom + pad;
  const w = window.innerWidth, h = window.innerHeight;
  const points = [[w - 20, 20], [20, h - 20], [w - 20, h - 20], [20, 20], [w / 2, h / 2], [w / 2, 20]];
  for (const [x, y] of points) {
    if (inside(part, x, y) || inside(card, x, y)) continue;
    const hit = document.elementFromPoint(x, y);
    return { x, y, testid: hit && hit.getAttribute('data-testid'), walk: !!(hit && hit.closest('[data-walk]')) };
  }
  return null;
}
"""

# Move the part's window, wait two frames (what Playwright waits for a
# stable box), and name what the browser hits at the part's centre.
_HIT_AFTER_MOVE_JS = """
async () => {
  const part = document.querySelector('[data-testid="programs-new"]');
  const win = part.closest("[data-layer='window']");
  const frames = () => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)));
  const hit = () => {
    const box = part.getBoundingClientRect();
    const element = document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
    return element && (element.closest('[data-testid="programs-new"]') ? "programs-new" : element.getAttribute("data-testid"));
  };
  win.style.translate = "-60px 40px";
  await frames();
  const moved = hit();
  win.style.translate = "";
  await frames();
  return { moved, back: hit() };
}
"""


@pytest.mark.parametrize("size", [(1440, 900), (393, 844)], ids=["1440", "393"])
def test_the_marked_part_takes_a_plain_press_and_the_desk_stays_live(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, size: tuple[int, int]) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    width, height = size
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
            page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                # The well lists his projects: one is enough.
                _api(page, "POST", "/api/projects", {"name": "Walk glass"}, token=TOKEN)
                made: dict[str, Any] = _api(page, "POST", "/api/walks", {"title": "The press", "steps": [
                    {"open": {"app": "surface-programs"}},
                    {"highlight": {"target": "programs-new", "words": "Press New program. The well opens."}},
                ]}, token=TOKEN)
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.goto(f"{base}{made['url_path']}", wait_until="load")

                page.locator('[data-testid="programs-new"].walk-halo').wait_for(timeout=T)
                target = page.locator('[data-testid="programs-new"]')
                assert page.evaluate(_HIT_AFTER_MOVE_JS) == {"moved": "programs-new", "back": "programs-new"}
                # A plain press: Playwright refuses it when another element
                # would take the pointer at the part's centre.
                target.click(timeout=10_000)
                page.locator('[data-testid="programs-wizard-step-1"]').wait_for(state="visible", timeout=T)

                far = page.evaluate(_FAR_HIT_JS)
                assert far is not None, "no point outside the part and the card"
                # No dim: the walk takes no pointer away from the desk.
                assert not far["walk"] and not str(far["testid"] or "").startswith("walk-"), far
                assert errors == [], errors
            finally:
                ctx.close()
                browser.close()
    finally:
        server.stop()


# The Dynamic Island and the home bar: Chromium reports no safe area, so the
# rig sets the two insets the edge reads (an iPhone 18 Pro Max in portrait).
_SAFE_TOP, _SAFE_BOTTOM = 59, 34
_SAFE_CSS = f".walk-layer {{ --walk-safe-top: {_SAFE_TOP}px; --walk-safe-bottom: {_SAFE_BOTTOM}px; }}"

_BOX_JS = """
(testid) => {
  const element = document.querySelector(`[data-testid="${testid}"]`);
  if (!element) return null;
  const box = element.getBoundingClientRect();
  return { left: box.left, top: box.top, right: box.right, bottom: box.bottom };
}
"""


def _png_size(path: Path) -> tuple[int, int]:
    head = path.read_bytes()[:24]
    assert head[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", head[16:24])


def test_on_his_iphone_the_edge_holds_the_safe_area_the_guide_presses_and_the_shot_is_the_screen(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    width, height = 430, 932
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=3,
                                      is_mobile=True, has_touch=True)
            page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                _api(page, "POST", "/api/projects", {"name": "Walk glass"}, token=TOKEN)
                made: dict[str, Any] = _api(page, "POST", "/api/walks", {"title": "Hand-held", "steps": [
                    {"open": {"app": "surface-programs"}},
                    {"press": {"target": "programs-new", "words": "I press New program."},
                     "highlight": {"target": "programs-wizard-step-1", "words": "The project rows."},
                     "ask": {"ref": "s11-well", "question": "Does the well read clearly?",
                             "choices": ["Keep", "Redo"]}},
                ]}, token=TOKEN)
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.goto(f"{base}{made['url_path']}", wait_until="load")
                page.add_style_tag(content=_SAFE_CSS)

                # The warm edge is inside the safe area, edge to edge between them.
                page.get_by_test_id("walk-edge").wait_for(state="attached", timeout=T)
                edge = page.evaluate(_BOX_JS, "walk-edge")
                assert edge == {"left": 0, "top": _SAFE_TOP, "right": width, "bottom": height - _SAFE_BOTTOM}, edge
                assert page.evaluate("getComputedStyle(document.querySelector('.walk-edge')).pointerEvents") == "none"
                # No robot, no bubble, no pixel frame.
                assert page.locator(".walk-guide, .walk-bubble, .walk-frame, .walk-ring").count() == 0
                # A touch device starts the voice from one tap (iOS).
                page.get_by_test_id("walk-begin").tap()

                # The guide's cursor travels with its comet trail (the shots
                # for the owner's eye), then presses New program itself.
                shots = evidence_dir("walk-c")
                page.locator('[data-testid="walk-cursor-ghost"]').first.wait_for(state="attached", timeout=T)
                page.wait_for_timeout(180)
                page.screenshot(path=str(shots / "walk-c-press-430.png"))
                page.locator('[data-testid="walk-cursor"][data-phase="tap"], [data-testid="walk-cursor"][data-phase="rest"]'
                             ).first.wait_for(state="attached", timeout=T)
                page.screenshot(path=str(shots / "walk-c-tap-430.png"))

                # The guide presses New program itself: the wizard opens.
                page.get_by_test_id("walk-question").wait_for(timeout=T)
                assert page.locator('[data-testid="programs-wizard-step-1"]').is_visible()
                # The bar fades in; measure it at rest.
                page.wait_for_timeout(450)
                sheet = page.evaluate(_BOX_JS, "walk-card")
                assert sheet["bottom"] <= height and sheet["left"] == 0 and sheet["right"] == width, sheet
                # One toolbar band of two rows (direction S3): the window keeps the room.
                assert sheet["bottom"] - sheet["top"] <= 140 + _SAFE_BOTTOM, sheet
                keep = page.get_by_test_id("walk-choice-0").bounding_box()
                redo = page.get_by_test_id("walk-choice-1").bounding_box()
                assert keep and redo and keep["height"] >= 44 and abs(keep["width"] - redo["width"]) < 1
                page.wait_for_timeout(500)
                assert page.locator('[data-testid="programs-wizard-step-1"].walk-halo').count() == 1
                caption = page.evaluate(_BOX_JS, "walk-words")
                assert caption and caption["bottom"] <= sheet["top"], (caption, sheet)
                page.screenshot(path=str(shots / "walk-c-ask-430.png"))

                page.get_by_test_id("walk-choice-0").tap()
                page.get_by_test_id("walk-end").wait_for(timeout=T)
                read: dict[str, Any] = _api(page, "GET", f"/api/walks/{made['id']}", token=TOKEN)
                stored = read["answers"]["s11-well"]
                assert stored["choice"] == "Keep" and stored["shot"] == "s11-well.png", stored
                view = stored["view"]
                assert (view["width"], view["height"], view["dpr"], view["scale"]) == (width, height, 3.0, 2.0), view
                assert view["rect"]["width"] > 0 and view["agent"], view
                # The shot is the whole viewport at the capture scale.
                assert _png_size(Path(read["directory"]) / "s11-well.png") == (width * 2, height * 2)
                assert errors == [], errors
            finally:
                ctx.close()
                browser.close()
    finally:
        server.stop()


# The desk's first reads are slow (owner, 2026-11-07, on his iPhone: "the
# click happened only shortly after the web page loaded… only launch when all
# is loaded"). The page's own fetch holds the hub's window list and the
# Programs list 2.5 s on their first read, and every project read 4 s. The
# rig notes when the walk's ready marker, cursor, ripple and halo first appear, and
# the guide's own click (an untrusted one: every press of the rig is trusted).
_SLOW_DESK_JS = """
(() => {
  const delays = { "/api/desk/windows": 2500, "/api/programs": 2500, "/api/projects": 4000 };
  const held = new Set();
  const real = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const url = new URL(typeof input === "string" ? input : input.url, location.href);
    const method = String((init && init.method) || (typeof input === "string" ? "GET" : input.method) || "GET").toUpperCase();
    const ms = method === "GET" ? delays[url.pathname] : undefined;
    if (ms && (url.pathname === "/api/projects" || !held.has(url.pathname))) {
      held.add(url.pathname);
      await new Promise((resolve) => setTimeout(resolve, ms));
    }
    const answer = await real(input, init);
    // The hub's window list landed: the compositor restores from it.
    if (url.pathname === "/api/desk/windows" && method === "GET" && !("windows" in seen)) seen.windows = performance.now();
    return answer;
  };
  const seen = (window.__walkSeen = {});
  const mark = (key, selector) => {
    if (!(key in seen) && document.querySelector(selector)) seen[key] = performance.now();
  };
  new MutationObserver(() => {
    mark("ready", "[data-desk-ready]");
    mark("cursor", '[data-testid="walk-cursor"]');
    mark("ripple", '[data-testid="walk-ripple"]');
    mark("halo", ".walk-halo");
    mark("programs", "[data-layer='window'][id='surface-programs'], [data-layer='window'][id^='surface-programs:']");
  }).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ["data-desk-ready", "class"] });
  document.addEventListener("click", (event) => {
    if (event.isTrusted || window.__walkClick) return;
    const target = event.target instanceof Element ? event.target : null;
    const win = target && target.closest("[data-layer='window']");
    const named = target && target.closest("[data-testid]");
    window.__walkClick = {
      t: performance.now(),
      testid: named && named.getAttribute("data-testid"),
      busy: !!(win && win.querySelector("[aria-busy='true']")),
      ready: !!document.querySelector("[data-desk-ready]"),
    };
  }, true);
})();
"""


def test_the_walk_starts_only_when_the_desk_is_ready_and_moves_one_beat_later(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
            prep = ctx.new_page()
            prep.set_default_timeout(45_000)
            try:
                prep.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(prep, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                _api(prep, "POST", "/api/projects", {"name": "Walk glass"}, token=TOKEN)
                made: dict[str, Any] = _api(prep, "POST", "/api/walks", {"title": "Slow desk", "steps": [
                    {"open": {"app": "surface-programs"}},
                    {"press": {"target": "programs-new", "words": "I press New program."},
                     "highlight": {"target": "programs-wizard-step-1", "words": "The project rows."},
                     "ask": {"ref": "s-ready", "question": "Does the well read clearly?",
                             "choices": ["Keep", "Redo"]}},
                ]}, token=TOKEN)
                prep.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _normal_chair(prep)
                prep.close()

                page = ctx.new_page()
                page.set_default_timeout(45_000)
                errors: list[str] = []
                page.on("pageerror", lambda e: errors.append(str(e)[:200]))
                page.add_init_script(_SLOW_DESK_JS)
                page.goto(f"{base}{made['url_path']}", wait_until="load")

                # The wizard is found after the slow project read.
                page.get_by_test_id("walk-question").wait_for(timeout=30_000)
                assert page.locator('[data-testid="programs-wizard-step-1"]').is_visible()
                assert page.get_by_test_id("walk-line").count() == 0

                seen: dict[str, float] = page.evaluate("window.__walkSeen")
                click: dict[str, Any] | None = page.evaluate("window.__walkClick || null")
                assert click is not None, "the guide never pressed"
                # The walk opens nothing before the hub's window list landed.
                assert seen["programs"] >= seen["windows"], (seen, click)
                # The press waits for the Programs window's first read.
                assert click["testid"] == "programs-new" and not click["busy"], (seen, click)
                # The guide moves one beat after the hub's window list landed.
                first_move = min(seen[key] for key in ("cursor", "ripple", "halo") if key in seen)
                assert first_move - seen["windows"] >= 900, (seen, click)
                # No press and no mark before the desk is ready.
                assert "ready" in seen and click["ready"], (seen, click)
                # The first move comes at least one 900 ms beat after the marker.
                assert first_move - seen["ready"] >= 900, (seen, click)
                assert click["t"] - seen["ready"] >= 900, (seen, click)
                assert errors == [], errors
            finally:
                ctx.close()
                browser.close()
    finally:
        server.stop()
