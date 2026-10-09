"""PHILO-16 (lane 16a-A2) -- the compositor core, on glass.

COMPOSITOR.md §9: "one glass file at 1440 and 393 with the depth shot".
Through the real hub on an isolated HOME, the built bundle, motion on:

  C1 planes: three windows are FRONT, NEAR, FAR (data-plane), exactly one
     front at every step, z rises with the plane; a raise moves the old
     front to NEAR; a reload keeps the planes (the depths persist).
  C2 tile: Window > Tile left puts the front on the left half of the band
     and the near window on the right; they touch; ONE steel divider sits on
     the seam; dragging it resizes both and keeps both far edges; Esc
     returns the remembered rects exactly.
  C3 stage (⌘⏎): the front takes 76 % of the band; the rest are plates
     scaled <= 300 x 170 on the left shelf; a press on a plate swaps it onto
     the stage; Esc returns.
  C4 exposé (⌘⇧E): every window is a live plate (its own element at its
     own size, scaled, never reflowed), inside the band; Esc returns.
  C5 gather (⌘G): the project drawer and its Get Info (one Room) tile the
     band in two columns.
  C6 keys stay quiet inside a text field.
  C7 393: the sheet is unchanged; nothing is arranged.

Shots: docs/internal/philo/phase-16/a2-shots/ (``.tmp/evidence-shots/``
unless HOLDSPEAK_EVIDENCE_WRITE=1).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .chair_windows import open_chair_window
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from .test_philo13_11_frame_glass import _seed, _stage
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the compositor glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "philo16-compositor"
SHOTS = evidence_dir("docs/internal/philo/phase-16/a2-shots")
SIZES = {1440: 900, 393: 852}
T = 30_000

WINS_JS = r"""() => {
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden'; };
  return [...document.querySelectorAll('.desk-window-shell:not([data-departing])')].filter(visible).map((s) => {
    const r = s.getBoundingClientRect(); const cs = getComputedStyle(s);
    return {name: s.getAttribute('aria-label'), plane: s.dataset.plane || null, layer: s.dataset.layer || null,
      front: s.classList.contains('is-front'), z: Number(cs.zIndex) || 0,
      k: s.style.getPropertyValue('--plate-k') || null, scale: cs.scale,
      layoutW: s.offsetWidth, layoutH: s.offsetHeight,
      rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]}; });
}"""

BAND_JS = r"""() => {
  const st = getComputedStyle(document.documentElement);
  const top = parseFloat(st.getPropertyValue('--desk-work-top'));
  const band = parseFloat(st.getPropertyValue('--desk-work-bottom'));
  const dock = parseFloat(st.getPropertyValue('--desk-dock-h'));
  const bottom = Number.isFinite(dock) ? Math.max(band, dock) : band;
  return {x: 10, y: top, w: innerWidth - 20, h: innerHeight - top - bottom};
}"""

DIVIDERS_JS = r"""() => [...document.querySelectorAll('.desk-window-divider')].map((d) => {
  const r = d.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })"""


def _wins(page: Any) -> list[dict[str, Any]]:
    page.wait_for_timeout(450)  # the longest moment is 360 ms
    _settle(page)
    return page.evaluate(WINS_JS)


def _by(wins: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next(w for w in wins if w["name"] == name)


def _fronts(wins: list[dict[str, Any]]) -> list[str]:
    return [w["name"] for w in wins if w["plane"] == "front"]


def _inside(rect: list[int], band: dict[str, float], slack: int = 2) -> bool:
    x, y, w, h = rect
    return (x >= band["x"] - slack and y >= band["y"] - slack
            and x + w <= band["x"] + band["w"] + slack and y + h <= band["y"] + band["h"] + slack)


PANEL_JS = r"""() => { const d = JSON.parse(localStorage.getItem('hs.desk.workspace.v1') || 'null');
  const p = (d && d.panel) || {}; return {rects: p.rects || {}, zoom: p.zoom || {}, max: p.max || []}; }"""

# The motion moving the window itself (a lift, an arrange): script
# animations on transform / scale. A1's plane change is CSS transitions of
# colour and shadow (the ladder), which may run while the pointer is down.
RUNNING_JS = r"""(name) => { const el = document.querySelector(`.desk-window-shell[aria-label='${name}']`);
  if (!el) return -1;
  return el.getAnimations({subtree: false}).filter((a) => a.playState === 'running' && !(a instanceof CSSTransition))
    .filter((a) => (a.effect.getKeyframes() || []).some((k) => 'scale' in k || 'transform' in k)).length; }"""

ALL_RUNNING_JS = r"""(name) => { const el = document.querySelector(`.desk-window-shell[aria-label='${name}']`);
  return el ? el.getAnimations().filter((a) => a.playState === 'running')
    .map((a) => a instanceof CSSTransition ? `transition:${a.transitionProperty}` : `${a.constructor.name}:${a.animationName || ''}`) : null; }"""


def _drag(page: Any, selector: str, dx: float, dy: float, *, hold: Any = None) -> None:
    box = page.locator(selector).first.bounding_box()
    assert box, f"nothing to drag: {selector}"
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + dx / 2, y + dy / 2, steps=4)
    page.mouse.move(x + dx, y + dy, steps=4)
    if hold:
        hold()
    page.mouse.up()


def _window_menu(page: Any, label: str) -> None:
    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
    page.locator(".desk-verbbar-menu").wait_for()
    page.locator(".desk-verbbar-menu [role^='menuitem']").filter(has_text=label).first.click()


class TestCompositor:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _seed()
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(T)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    def test_compositor_1440(self) -> None:
        from playwright.sync_api import sync_playwright

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                band = page.evaluate(BAND_JS)
                for name in ("Brief", "The week", "Needs you"):
                    open_chair_window(page, name)
                wins = _wins(page)
                names = [w["name"] for w in wins]
                if not {"Brief", "The week", "Needs you"} <= set(names):
                    fails["C1 three windows open"] = names
                planes = {w["name"]: w["plane"] for w in wins}
                if sorted(planes.values()).count("front") != 1 or "near" not in planes.values() or "far" not in planes.values():
                    fails["C1 front, near, far"] = planes
                if any(w["layer"] != "window" for w in wins):
                    fails["C1 data-layer=window"] = wins
                if any(w["front"] != (w["plane"] == "front") for w in wins):
                    fails["C1 is-front is the alias of data-plane=front"] = wins
                order = sorted(wins, key=lambda w: w["z"])
                if order[-1]["plane"] != "front" or order[-2]["plane"] != "near":
                    fails["C1 z rises with the plane"] = [(w["name"], w["z"], w["plane"]) for w in order]
                page.screenshot(path=str(SHOTS / "1440-1-planes.png"))

                # A raise: the far window comes forward; the old front is NEAR.
                old_front = _fronts(wins)[0]
                far = next(w["name"] for w in wins if w["plane"] == "far")
                page.locator(f".desk-window-shell[aria-label='{far}'] .desk-pullout-title").first.click()
                wins = _wins(page)
                if _fronts(wins) != [far] or _by(wins, old_front)["plane"] != "near":
                    fails["C1 raise: far to front, old front to near"] = {w["name"]: w["plane"] for w in wins}

                # The depths persist: a reload keeps the stacking. The Chair's
                # own rule (PHILO-15-09 B16, ChairDesk.raiseNeedsAmongChair)
                # raises Needs you on the Chair's mount; every other window
                # keeps its place.
                # PHILO-16 (16b): the hub owns the stacking; a reload keeps its
                # order exactly (the Chair's mount no longer raises Needs you
                # over the hub's rows).
                stack = [w["name"] for w in sorted(_wins(page), key=lambda w: w["z"])]
                want = stack
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1500)
                after = [w["name"] for w in sorted(_wins(page), key=lambda w: w["z"])]
                if after != want:
                    fails["C1 a reload keeps the stacking"] = {"before": stack, "after": after, "want": want}

                # C2 tile.
                wins = _wins(page)
                free = {w["name"]: w["rect"] for w in wins}
                front = _fronts(wins)[0]
                near = next(w["name"] for w in wins if w["plane"] == "near")
                _window_menu(page, "Tile left")
                wins = _wins(page)
                fr, nr = _by(wins, front)["rect"], _by(wins, near)["rect"]
                half = band["w"] / 2
                if abs(fr[0] - band["x"]) > 2 or abs(fr[2] - half) > 2 or abs(nr[0] - (fr[0] + fr[2])) > 2:
                    fails["C2 tile: front left half, near right half, touching"] = {"front": fr, "near": nr, "band": band}
                if not (_inside(fr, band) and _inside(nr, band)):
                    fails["C2 the band is sacred"] = {"front": fr, "near": nr, "band": band}
                dividers = page.evaluate(DIVIDERS_JS)
                if len(dividers) != 1:
                    fails["C2 one steel divider on the seam"] = dividers
                page.screenshot(path=str(SHOTS / "1440-2-tile.png"))
                if dividers:
                    d = dividers[0]
                    cx, cy = d[0] + d[2] / 2, d[1] + d[3] / 2
                    page.mouse.move(cx, cy)
                    page.mouse.down()
                    page.mouse.move(cx + 40, cy, steps=4)
                    page.mouse.move(cx + 80, cy, steps=4)
                    page.mouse.up()
                    wins = _wins(page)
                    fr2, nr2 = _by(wins, front)["rect"], _by(wins, near)["rect"]
                    if abs(fr2[2] - (fr[2] + 80)) > 2 or abs(nr2[0] - (nr[0] + 80)) > 2:
                        fails["C2 the divider moves the shared edge"] = {"front": fr2, "near": nr2}
                    if fr2[0] != fr[0] or abs((nr2[0] + nr2[2]) - (nr[0] + nr[2])) > 1:
                        fails["C2 the far edges stay"] = {"front": fr2, "near": nr2}
                page.keyboard.press("Escape")
                wins = _wins(page)
                back = {w["name"]: w["rect"] for w in wins}
                if back != free:
                    fails["C2 Esc returns the remembered rects"] = {"free": free, "back": back}
                if page.evaluate(DIVIDERS_JS):
                    fails["C2 no divider after Esc (the windows no longer touch)"] = page.evaluate(DIVIDERS_JS)
                if len(_fronts(wins)) != 1:
                    fails["one front after tile"] = _fronts(wins)

                # C3 stage, by its key; the focus on the front window's bar.
                front = _fronts(wins)[0]
                page.locator(f".desk-window-shell[aria-label='{front}'] .desk-pullout-title").first.click()
                page.keyboard.press("Meta+Enter")
                wins = _wins(page)
                main = _by(wins, front)
                if abs(main["rect"][2] - round(band["w"] * 0.76)) > 2 or main["k"]:
                    fails["C3 the front takes 76 % of the band"] = {"main": main, "band": band}
                plates = [w for w in wins if w["name"] != front]
                for p in plates:
                    if not p["k"] or p["rect"][2] > 302 or p["rect"][3] > 172 or not _inside(p["rect"], band):
                        fails.setdefault("C3 shelf plates scaled, inside the band", []).append(p)
                    if p["rect"][0] + p["rect"][2] > main["rect"][0] + 1:
                        fails.setdefault("C3 the shelf is on the left", []).append(p)
                page.screenshot(path=str(SHOTS / "1440-3-stage.png"))
                swap = plates[0]["name"] if plates else None
                if swap:
                    box = page.locator(f".desk-window-shell[aria-label='{swap}']").bounding_box()
                    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    wins = _wins(page)
                    if _fronts(wins) != [swap] or _by(wins, swap)["k"] or abs(_by(wins, swap)["rect"][2] - round(band["w"] * 0.76)) > 2:
                        fails["C3 a press on a plate swaps it onto the stage"] = {w["name"]: (w["plane"], w["rect"], w["k"]) for w in wins}
                page.keyboard.press("Escape")
                wins = _wins(page)
                back = {w["name"]: w["rect"] for w in wins}
                if back != free:
                    fails["C3 Esc returns the remembered rects"] = {"free": free, "back": back}

                # C4 exposé.
                page.keyboard.press("Meta+Shift+E")
                page.locator(".desk-expose").wait_for()
                wins = _wins(page)
                for w in wins:
                    natural = free.get(w["name"])
                    scaled = w["k"] is not None and float(w["k"]) < 1
                    if natural and scaled and abs(w["layoutW"] - natural[2]) > 2:
                        fails.setdefault("C4 plates scale, never reflow", []).append(w)
                    if not _inside(w["rect"], band):
                        fails.setdefault("C4 plates inside the band", []).append(w)
                cells = page.locator(".desk-expose-cell").count()
                if cells != len(wins):
                    fails["C4 one pick target per plate"] = {"cells": cells, "wins": len(wins)}
                page.screenshot(path=str(SHOTS / "1440-4-expose.png"))
                page.keyboard.press("Escape")
                wins = _wins(page)
                back = {w["name"]: w["rect"] for w in wins}
                if back != free or page.locator(".desk-expose").count():
                    fails["C4 Esc returns the remembered rects"] = {"free": free, "back": back}

                # C5 gather: the project drawer and its Get Info share a Room.
                page.goto(f"{self.base}/?token={TOKEN}&open=project:p-ledger", wait_until="load")
                _normal_chair(page)
                drawer = page.locator(".drawer-window")
                drawer.wait_for(timeout=T)
                drawer.get_by_role("button", name="Get Info", exact=True).click()
                page.locator(".drawer-info-window").wait_for(timeout=T)
                page.locator(".drawer-info-window .desk-pullout-title").first.click()
                page.keyboard.press("Meta+g")
                wins = _wins(page)
                room = [w for w in wins if w["name"] and ("Payments ledger cutover" in w["name"])]
                if len(room) != 2:
                    fails["C5 two windows of the Room"] = [w["name"] for w in wins]
                else:
                    a, b = sorted((w["rect"] for w in room), key=lambda r: r[0])
                    if abs(a[0] - band["x"]) > 2 or abs(b[0] - (a[0] + a[2]) - 8) > 2 or abs(a[2] - b[2]) > 2:
                        fails["C5 equal columns, 8 px gutter"] = {"a": a, "b": b, "band": band}
                    if not (_inside(a, band) and _inside(b, band)):
                        fails["C5 the band is sacred"] = {"a": a, "b": b}
                if len(_fronts(wins)) != 1:
                    fails["one front after gather"] = _fronts(wins)
                page.screenshot(path=str(SHOTS / "1440-5-gather.png"))

                # C6 keys stay quiet inside a text field (a field in the front
                # window: the keymap's typing guard).
                page.evaluate("""() => { const w = document.querySelector('.desk-window-shell.is-front');
                  const i = document.createElement('input'); i.type = 'text'; i.id = 'c6-field';
                  w.appendChild(i); i.focus(); }""")
                rects = {w["name"]: w["rect"] for w in _wins(page)}
                for key in ("Meta+Enter", "Meta+Shift+E", "Meta+g", "Meta+Alt+ArrowLeft"):
                    page.keyboard.press(key)
                wins = _wins(page)
                if any(w["k"] for w in wins) or page.locator(".desk-expose").count() or {w["name"]: w["rect"] for w in wins} != rects:
                    fails["C6 the arrangement keys stay quiet in a field"] = wins
                page.evaluate("() => document.getElementById('c6-field')?.remove()")
                if errors:
                    fails["page errors"] = errors
            finally:
                browser.close()
        assert not fails, fails

    def test_astra_round1_1440(self) -> None:
        """Astra round 1 (5fe358d78), her repros: M1 Stage keeps the saved
        arrangement (zoomed and not); M4 no lift under a resize; M2 the
        divider stops at the frame's real minimum inside the band."""
        from playwright.sync_api import sync_playwright

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                band = page.evaluate(BAND_JS)
                for name in ("Brief", "Needs you"):
                    open_chair_window(page, name)
                needs = ".desk-window-shell[aria-label='Needs you']"

                # M1 (zoomed): Zoom -> Stage -> resize the staged front -> Esc.
                page.get_by_role("button", name="Zoom Needs you").click()
                rects = {w["name"]: w["rect"] for w in _wins(page)}
                doc = page.evaluate(PANEL_JS)
                page.locator(f"{needs} .desk-pullout-title").first.click()
                page.keyboard.press("Meta+Enter")
                _wins(page)
                _drag(page, f"{needs} .desk-window-grip", -200, -100)
                if page.evaluate(PANEL_JS) != doc:
                    fails["M1 zoomed: a Stage resize leaves the saved arrangement"] = {"before": doc, "during": page.evaluate(PANEL_JS)}
                page.keyboard.press("Escape")
                back = {w["name"]: w["rect"] for w in _wins(page)}
                if back != rects or page.evaluate(PANEL_JS) != doc:
                    fails["M1 zoomed: Esc restores both rects and the zoom flag"] = {
                        "before": rects, "after": back, "doc": doc, "doc_after": page.evaluate(PANEL_JS)}

                # M1 (Zoom during Stage leaves Stage first).
                page.keyboard.press("Meta+Enter")
                _wins(page)
                page.get_by_role("button", name="Zoom Needs you").click()  # unzoom
                wins = _wins(page)
                if any(w["k"] for w in wins):
                    fails["M1 Zoom during Stage leaves Stage"] = wins

                # M1 (not zoomed): Stage -> resize -> Esc.
                rects = {w["name"]: w["rect"] for w in _wins(page)}
                doc = page.evaluate(PANEL_JS)
                page.locator(f"{needs} .desk-pullout-title").first.click()
                page.keyboard.press("Meta+Enter")
                _wins(page)
                _drag(page, f"{needs} .desk-window-grip", -150, -80)
                if page.evaluate(PANEL_JS) != doc:
                    fails["M1 a Stage resize writes no free rect"] = {"before": doc, "during": page.evaluate(PANEL_JS)}
                page.keyboard.press("Escape")
                back = {w["name"]: w["rect"] for w in _wins(page)}
                if back != rects:
                    fails["M1 Esc restores the free rects"] = {"before": rects, "after": back}

                # M4: resize Brief (behind Needs you) by its grip: no lift runs
                # while the pointer is held.
                page.locator(f"{needs} .desk-pullout-title").first.click()
                _wins(page)
                running: list[int] = []
                _drag(page, ".desk-window-shell[aria-label='Brief'] .desk-window-grip", -40, -30,
                      hold=lambda: (page.wait_for_timeout(60), running.append(page.evaluate(RUNNING_JS, "Brief"))))
                if running != [0]:
                    fails["M4 no lift during a resize"] = {"lifts": running, "all": page.evaluate(ALL_RUNNING_JS, "Brief")}

                # M2: two surface windows (min-width 420) tiled; the divider
                # dragged past both minimums.
                _stage(page, "review-meetings")
                _stage(page, "open-people")
                wins = _wins(page)
                front = _fronts(wins)[0]
                near = next(w["name"] for w in wins if w["plane"] == "near")
                _window_menu(page, "Tile left")
                _wins(page)
                for dx in (2000, -2000):
                    d = page.evaluate(DIVIDERS_JS)
                    if len(d) != 1:
                        fails[f"M2 one divider ({dx})"] = d
                        break
                    _drag(page, ".desk-window-divider", dx, 0)
                    wins = _wins(page)
                    for name in (front, near):
                        r = _by(wins, name)["rect"]
                        if not _inside(r, band, slack=1) or r[2] < 419:
                            fails.setdefault(f"M2 the band and the 420 minimum ({dx})", []).append({name: r, "band": band})
                    # The two windows still meet at the divider: no overlap, no gap.
                    left, right = sorted((_by(wins, front)["rect"], _by(wins, near)["rect"]), key=lambda r: r[0])
                    seam = page.evaluate(DIVIDERS_JS)
                    if abs(left[0] + left[2] - right[0]) > 1 or not seam or abs(seam[0][0] + 3 - right[0]) > 2:
                        fails.setdefault(f"M2 the windows meet at the divider ({dx})", []).append(
                            {"left": left, "right": right, "divider": seam})
                page.screenshot(path=str(SHOTS / "1440-6-divider-minimum.png"))
                page.keyboard.press("Escape")
                if errors:
                    fails["page errors"] = errors
            finally:
                browser.close()
        assert not fails, fails

    def test_astra_round2_1440(self) -> None:
        """Astra round 2 (c67c80974), her case from UNARRANGED: a fresh People
        window -> Stage -> Zoom -> unzoom returns its pre-Stage rect, and no
        Stage rect lands in panel.rects (Zoom never measures a box in flight)."""
        from playwright.sync_api import sync_playwright

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                open_chair_window(page, "Brief")
                _stage(page, "open-people")
                people = ".desk-window-shell[aria-label='People']"
                page.locator(people).wait_for()
                wins = _wins(page)
                if _fronts(wins) != ["People"]:
                    fails["People is front"] = _fronts(wins)
                before = _by(wins, "People")["rect"]
                doc = page.evaluate(PANEL_JS)
                if "surface-people" in doc["rects"]:
                    fails["People starts unarranged"] = doc["rects"]["surface-people"]
                page.locator(f"{people} .desk-pullout-title").first.click()
                page.keyboard.press("Meta+Enter")
                wins = _wins(page)
                if not any(w["k"] for w in wins):
                    fails["Stage is on"] = wins
                page.locator(f"{people} .desk-gadget-zoom").click()  # zoom: leaves Stage
                _wins(page)
                page.locator(f"{people} .desk-gadget-zoom").click()  # unzoom
                wins = _wins(page)
                after = _by(wins, "People")["rect"]
                if after != before:
                    fails["unzoom returns the pre-Stage rect"] = {"before": before, "after": after}
                saved = page.evaluate(PANEL_JS)["rects"].get("surface-people")
                if saved is not None and [saved["x"], saved["y"], saved["w"], saved["h"]] != before:
                    fails["no Stage rect in panel.rects"] = {"saved": saved, "before": before}
                if errors:
                    fails["page errors"] = errors
            finally:
                browser.close()
        assert not fails, fails

    def test_compositor_393(self) -> None:
        from playwright.sync_api import sync_playwright

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                open_chair_window(page, "Needs you")
                page.wait_for_timeout(800)
                wins = _wins(page)
                if len(_fronts(wins)) != 1:
                    fails["393 one front"] = wins
                page.keyboard.press("Meta+Enter")
                page.keyboard.press("Meta+Shift+E")
                wins = _wins(page)
                if any(w["k"] for w in wins) or page.locator(".desk-expose").count() or page.evaluate(DIVIDERS_JS):
                    fails["C7 393: nothing is arranged"] = wins
                page.screenshot(path=str(SHOTS / "393-sheet.png"))
                if errors:
                    fails["page errors"] = errors
            finally:
                browser.close()
        assert not fails, fails
