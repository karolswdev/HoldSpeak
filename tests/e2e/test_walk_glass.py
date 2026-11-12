"""The current guide keeps its pane clear and the linked walk stores answers.

Real-browser properties: plain presses reach the marked part, a phone note
pays for its safe area, linked openers wait for the Desk, and the guide and
capture reserve one shared window seat. The retired cursor rendering is
kept in _parked/test_walk_cursor_20261110.py.
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

# The first point outside the marked part and the note,
# and the element the browser hits there.
_FAR_HIT_JS = """
() => {
  const pad = 12;
  const part = document.querySelector('[data-testid="guide-ring"]').getBoundingClientRect();
  const card = document.querySelector('[data-testid="guide-note"]').getBoundingClientRect();
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
                    {"open": {"app": "surface-programs"},
                     "highlight": {"target": "programs-new", "words": "Press New program. The well opens."}},
                ]}, token=TOKEN)
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.goto(f"{base}{made['url_path']}", wait_until="load")

                page.get_by_test_id("guide-ring").wait_for(timeout=T)
                target = page.locator('[data-testid="programs-new"]')
                assert page.evaluate(_HIT_AFTER_MOVE_JS) == {"moved": "programs-new", "back": "programs-new"}
                far = page.evaluate(_FAR_HIT_JS)
                assert far is not None, "no point outside the part and note"
                assert not far["walk"] and not str(far["testid"] or "").startswith("guide-"), far
                # A plain press takes the pointer and ends Show me; the app
                # receives the same press and opens its form.
                target.click(timeout=10_000)
                page.get_by_role("region",name="New program",exact=True).get_by_role("tablist",name="Program form",exact=True).wait_for(state="visible", timeout=T)
                assert page.get_by_test_id("guide-note").count() == 0
                assert errors == [], errors
            finally:
                ctx.close()
                browser.close()
    finally:
        server.stop()


# Chromium reports no home-bar inset; the rig supplies it to the note.
_SAFE_BOTTOM = 34
_SAFE_CSS = f".guide-note {{ --guide-safe-bottom: {_SAFE_BOTTOM}px; }}"

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


def test_on_his_iphone_the_note_holds_the_safe_area_the_guide_selects_and_the_shot_is_the_screen(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    width, height = 430, 932
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=3,
                                      is_mobile=True, has_touch=True, reduced_motion="reduce")
            page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                _api(page, "POST", "/api/projects", {"name": "Walk glass"}, token=TOKEN)
                made: dict[str, Any] = _api(page, "POST", "/api/walks", {"title": "Hand-held", "steps": [
                    {"open": {"app": "surface-settings"},
                     "press": {"target": '[data-testid="settings-rail"] [data-rail-id="engines"]'},
                     "highlight": {"target": '[data-testid="settings-rail"] [data-rail-id="engines"]', "words": "The engine choices."},
                     "ask": {"ref": "s11-well", "question": "Do the engine choices read clearly?",
                             "choices": ["Keep", "Redo"]}},
                ]}, token=TOKEN)
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.goto(f"{base}{made['url_path']}", wait_until="load")
                page.add_style_tag(content=_SAFE_CSS)

                page.get_by_test_id("walk-question").wait_for(timeout=T)
                note = page.get_by_test_id("guide-note")
                assert page.locator('[data-testid="settings-rail"] [data-rail-id="engines"]').get_attribute("aria-selected") == "true"
                page.wait_for_timeout(150)
                sheet = page.evaluate(_BOX_JS, "guide-note")
                assert sheet and sheet["left"] >= 0 and sheet["right"] <= width and sheet["bottom"] <= height - _SAFE_BOTTOM, sheet
                # The completion row pays for the home-bar inset inside its seat.
                keep = page.get_by_test_id("walk-choice-0").bounding_box()
                assert keep and keep["height"] >= 44 and keep["y"] + keep["height"] <= sheet["bottom"] - _SAFE_BOTTOM, (sheet, keep)
                assert page.get_by_test_id("guide-ring").evaluate("el => getComputedStyle(el).pointerEvents") == "none"
                shots = evidence_dir("guide5")
                page.screenshot(path=str(shots / "linked-question-430.png"))

                page.get_by_test_id("walk-choice-0").tap()
                # The PNG producer briefly clones the viewport, including
                # the note. Wait for both the capture clone and guide to leave.
                page.wait_for_function("() => !document.querySelector('[data-testid=guide-note]')", timeout=T)
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
# rig notes the Desk readiness signals and the first note.
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
    const desk = document.querySelector('#desk-next');
    const dock = document.querySelector('.desk-dock');
    if (!("ready" in seen) && seen.windows && desk && desk.getAttribute('aria-busy') !== 'true' && dock?.getBoundingClientRect().height > 0 && !document.querySelector('[data-layer="window"] [aria-busy="true"]')) seen.ready = performance.now();
    mark("note", '[data-testid="guide-note"]');
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
      ready: !!window.__walkSeen.ready,
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
                    {"open": {"app": "surface-programs"},
                     "highlight": {"target": "programs-new", "words": "Press New program."}},
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

                page.get_by_test_id("guide-note").wait_for(timeout=30_000)
                seen: dict[str, float] = page.evaluate("window.__walkSeen")
                assert seen["programs"] >= seen["windows"], seen
                assert "ready" in seen, seen
                assert seen["note"] - seen["ready"] >= 900, seen
                assert page.locator('[data-layer="window"] [aria-busy="true"]').count() == 0
                page.get_by_test_id("programs-new").click()
                page.get_by_role("region",name="New program",exact=True).get_by_role("tablist",name="Program form",exact=True).wait_for(timeout=T)
                assert errors == [], errors
            finally:
                ctx.close()
                browser.close()
    finally:
        server.stop()


def test_phone_receipt_keeps_its_whole_verb_and_accessible_words(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import expect
    from playwright.sync_api import sync_playwright
    from holdspeak.services import desk_window_service as windows
    _ensure_build()
    server,base=_boot(tmp_path,monkeypatch,token=TOKEN)
    # The isolated web rig has no runtime composition. Bridge the real
    # service's own produced display frame to this rig's real websocket.
    monkeypatch.setattr(windows, '_send_request', lambda sent: server.broadcast('desk_request', sent))
    pw=sync_playwright().start()
    browser=pw.chromium.launch()
    ctx=browser.new_context(viewport={'width':393,'height':852},reduced_motion='reduce')
    page=ctx.new_page()
    page.set_default_timeout(T)
    errors=[]
    page.on('pageerror', lambda error:errors.append('pageerror: '+str(error)))
    try:
        page.goto(f'{base}/?token={TOKEN}',wait_until='load')
        _api(page,'PUT','/api/setup/onboarding',{'disposition':'completed'},token=TOKEN)
        _api(page,'POST','/api/desk/windows/surface-projects/open',{},token=TOKEN)
        page.reload(wait_until='load')
        page.goto(f'{base}/?token={TOKEN}',wait_until='load')
        _normal_chair(page)
        from .test_desk_sweep import SETTLED_JS
        page.wait_for_function(SETTLED_JS,arg='surface-projects',timeout=T)
        _api(page,'POST','/api/desk/windows/surface-projects/close',{},token=TOKEN)
        button=page.get_by_test_id('desk-window-undo')
        button.wait_for(timeout=T)
        expect(button).to_have_accessible_name('Undo: Close Projects')
        receipt=page.locator('.desk-window-undo')
        expect(receipt).to_have_accessible_name('Close Projects')
        assert not receipt.locator(':scope > span').is_visible()
        assert button.inner_text() == 'Undo'
        page.screenshot(path=str(evidence_dir('guide5')/'receipt-393.png'))
        button.click(button='right')
        item=page.get_by_role('menuitem', name='Undo: Close Projects', exact=True)
        expect(item).to_be_visible()
        item.click()
        page.locator('[id="surface-projects"]').wait_for(timeout=T)
        assert not any('pageerror:' in error for error in errors),errors
    finally:
        ctx.close()
        browser.close()
        pw.stop()
        server.stop()
