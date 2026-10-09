"""PHILO-13-12 (C2) -- the gadgets that are missing, on glass.

Built to the owner-ratified Workbench canvas (2026-10-02, "Ratify, build
it"; Steel; boards C1-2b, C1-2c, C1-2d). Through the real hub on an
isolated HOME at 1440x900 (mouse) and 393x852 (touch):

  G1 depth: To back sends the window behind every other window; a different
     window is the ONE blue window and the screen title names it (gadget,
     menu, ⌃B; at 393 by touch; a Chair window too).
  G2 zoom: zoom, a resize of the zoomed state, zoom back -> the exact prior
     rect; zoom again -> the remembered zoomed rect; both rects are in the
     workspace document (they survive a reload).
  G3 the right button (393: a long press) anywhere in a window opens its
     menu bar with the key caps: Iconify ⌘M, Zoom ⌃M, To back ⌃B, Close
     window ⌘W, Desk ▸, Go ▸.
  G4 each shortcut fires its verb: ⌃B, ⌃M, ⌘M, ⌘W, ⌘K, ⌘/, ⌃↑, ⌘N.

Shots go to pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-12-build/
under HOLDSPEAK_EVIDENCE_WRITE=1 (``.tmp/evidence-shots/`` otherwise).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from .chair_windows import open_chair_window
from .glass_infra import _boot, _ensure_build, _normal_chair, _settle
from .test_philo13_11_frame_glass import ROOM, _seed, _stage
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the gadget glass needs Playwright")

TOKEN = "philo13-12-gadgets"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-12-build")
SIZES = {1440: 900, 393: 852}

# The stacking facts as rendered: every visible window, its z, its blue head,
# and the screen title.
STACK_JS = r"""() => {
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden'; };
  const blue = (h) => { const m = getComputedStyle(h).backgroundColor.match(/\d+/g) || [];
    return Math.abs(m[0] - 102) < 3 && Math.abs(m[1] - 136) < 3 && Math.abs(m[2] - 187) < 3; };
  const wins = [...document.querySelectorAll('.desk-window-shell:not([data-departing])')].filter(visible).map((s) => {
    const h = s.querySelector(':scope > .desk-pullout-head'); const r = s.getBoundingClientRect();
    return {name: s.getAttribute('aria-label'), z: Number(getComputedStyle(s).zIndex) || 0,
      front: s.classList.contains('is-front'), blue: Boolean(h && blue(h)),
      rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]}; });
  const st = document.querySelector('[data-testid="desk-screen-title"]');
  return {wins, screen: st ? st.textContent.trim() : null};
}"""

MENU_JS = r"""() => {
  const menus = [...document.querySelectorAll('.desk-head-menu')];
  return menus.map((m) => ({label: m.getAttribute('aria-label'),
    rows: [...m.querySelectorAll('[role^="menuitem"]')].map((r) => {
      const b = r.getBoundingClientRect();
      return {label: (r.querySelector('.desk-menu-label') || r).textContent.trim(),
        keycap: (r.querySelector('.desk-menu-keycaps') || {getAttribute: () => null}).getAttribute('aria-label'),
        ghost: r.classList.contains('is-ghost') || r.getAttribute('aria-disabled') === 'true',
        w: Math.round(b.width), h: Math.round(b.height)}; })}));
}"""

DOC_JS = r"""() => JSON.parse(localStorage.getItem('hs.desk.workspace.v1') || 'null')"""


def _one_blue(stack: dict[str, Any], name: str) -> list[str]:
    """The faults when `name` is not the one blue front window the screen names."""
    faults = []
    blue = [w["name"] for w in stack["wins"] if w["blue"]]
    front = [w["name"] for w in stack["wins"] if w["front"]]
    if blue != [name]:
        faults.append(f"blue={blue}, want [{name}]")
    if front != [name]:
        faults.append(f"front={front}, want [{name}]")
    if stack["screen"] != name:
        faults.append(f"screen title={stack['screen']!r}, want {name!r}")
    return faults


def _behind(stack: dict[str, Any], sent: str) -> list[str]:
    """The faults when `sent` is not behind every other window, or the front
    is not ONE blue window (another one) that the screen title names."""
    faults = []
    others = [w for w in stack["wins"] if w["name"] != sent]
    if others and _z(stack, sent) >= min(w["z"] for w in others):
        faults.append(f"{sent} is not behind every other window")
    front = [w["name"] for w in stack["wins"] if w["front"]]
    if len(front) != 1 or front[0] == sent:
        faults.append(f"front={front}")
    else:
        faults += _one_blue(stack, front[0])
    return faults


def _z(stack: dict[str, Any], name: str) -> int:
    return next(w["z"] for w in stack["wins"] if w["name"] == name)


def _rect(stack: dict[str, Any], name: str) -> list[int]:
    return next(w["rect"] for w in stack["wins"] if w["name"] == name)


class TestTheGadgets:
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
                                  device_scale_factor=2, has_touch=width < 720, is_mobile=False)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        page.evaluate(
            """async (token) => fetch('/api/setup/onboarding', {method: 'PUT',
                headers: {authorization: `Bearer ${token}`, 'content-type': 'application/json'},
                body: JSON.stringify({disposition: 'completed'})})""",
            TOKEN,
        )
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _tap(page: Any, loc: Any) -> None:
        box = loc.bounding_box()
        assert box, "nothing to tap"
        page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

    @staticmethod
    def _long_press(page: Any, x: float, y: float) -> None:
        cdp = page.context.new_cdp_session(page)
        point = [{"x": x, "y": y, "radiusX": 4, "radiusY": 4, "force": 1, "id": 1}]
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": point})
        page.wait_for_timeout(800)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        cdp.detach()

    @staticmethod
    def _stack(page: Any) -> dict[str, Any]:
        page.wait_for_timeout(300)
        _settle(page)
        return page.evaluate(STACK_JS)

    def _check_menu(self, page: Any, name: str, width: int, facts: dict[str, Any], fails: dict[str, Any]) -> None:
        menus = page.evaluate(MENU_JS)
        facts[f"menu-{name}"] = menus
        menu = next((m for m in menus if m["label"] == f"{name} window menu"), None)
        if not menu:
            fails["G3 the window menu opens"] = menus
            return
        # a ghosted row carries its reason after the name ("Zoom · Fills the screen")
        got = [(r["label"].split(" · ")[0], r["keycap"]) for r in menu["rows"]]
        # PHILO-16 §5: Zoom ⌘⇧Z, To back ⌘⇧` (⌃M and ⌃B stay bound one release).
        want = [("Iconify", "⌘M"), ("Zoom", "⌘⇧Z"), ("To back", "⌘⇧`"), ("Close window", "⌘W"),
                ("Desk", None), ("Go", None)]
        if width < 720:
            # PHILO-15 11 (B21): a phone has no ⌘ key, so no row at 393 draws
            # a keycap (DeskMenu.tsx `entry.keycap && !NARROW()`).
            want = [(label, None) for label, _ in want]
        if got != want:
            fails["G3 the menu bar with its key caps"] = got
        zoom = menu["rows"][1] if len(menu["rows"]) > 1 else {}
        if width < 720 and not zoom.get("ghost"):
            fails["G3 393: Zoom stays, ghosted with its reason"] = zoom
        if width < 720:
            small = [r for r in menu["rows"] if r["h"] < 44]
            if small:
                fails["G3 393: every menu row owns 44 px"] = small

    def test_gadgets_1440(self) -> None:
        from playwright.sync_api import sync_playwright

        width = 1440
        facts: dict[str, Any] = {}
        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # G1 on the Chair: Needs you to back, another Chair window is front.
                # PHILO-14 A1 (#939): the Chair's windows start closed; he opens
                # the Brief, then Needs you, from Window > Chair.
                open_chair_window(page, "Brief")
                open_chair_window(page, "Needs you")
                needs = page.get_by_role("button", name="To back Needs you")
                needs.click()
                st = self._stack(page)
                facts["chair-after-depth"] = st
                if _behind(st, "Needs you"):
                    fails["G1 Chair: depth"] = _behind(st, "Needs you")

                # Two desk windows: the Room, then Meetings in front.
                _stage(page, "open-project-memory", "project:p-ledger")
                page.locator(".desk-dock [aria-label^='Meetings']").first.click()
                meetings = page.locator(".desk-window-shell[aria-label='Meetings']")
                meetings.wait_for()
                st = self._stack(page)
                if _one_blue(st, "Meetings"):
                    fails["G1 setup: Meetings front"] = st
                page.screenshot(path=str(SHOTS / "build-C1-2c-before-depth-1440.png"))

                # G1 the depth gadget.
                meetings.get_by_role("button", name="To back Meetings").click()
                st = self._stack(page)
                facts["after-depth-gadget"] = st
                faults = _one_blue(st, ROOM) + _behind(st, "Meetings")
                if faults:
                    fails["G1 depth gadget"] = faults
                page.screenshot(path=str(SHOTS / "build-C1-2c-depth-to-back-1440.png"))

                # G4 ⌃B: the front window (the Room) goes to the back.
                page.keyboard.press("Control+b")
                st = self._stack(page)
                facts["after-ctrl-b"] = st
                # Behind every window (the Chair's windows are windows too).
                faults = _behind(st, ROOM)
                if faults:
                    fails["G4 ⌃B runs To back"] = faults

                # G2 zoom: the two remembered rects. Meetings comes forward
                # from its Dock AppIcon.
                page.locator(".desk-dock [aria-label^='Meetings']").first.click()
                page.wait_for_timeout(300)
                # The owner arranges Meetings first (a drag of its title bar):
                # the normal rect is his, and the workspace keeps it.
                title = meetings.locator(".desk-pullout-title").bounding_box()
                assert title
                tx, ty = title["x"] + title["width"] / 2, title["y"] + title["height"] / 2
                page.mouse.move(tx, ty)
                page.mouse.down()
                page.mouse.move(tx + 40, ty + 30, steps=8)
                page.mouse.up()
                prior = _rect(self._stack(page), "Meetings")
                zoom = meetings.get_by_role("button", name="Zoom Meetings")
                zoom.click()
                st = self._stack(page)
                zoomed = _rect(st, "Meetings")
                if zoom.get_attribute("aria-pressed") != "true" or zoomed == prior:
                    fails["G2 zoom fills the work band"] = {"prior": prior, "zoomed": zoomed}
                # PHILO-13-11 close (board C1-2d): the zoomed window fills the
                # screen between the screen bar and the shelf -- its head flush
                # under the bar (no window behind peeks above it) and its foot
                # and sizing gadget clear of the Dock (the 76 px shelf of C3-W).
                band = page.evaluate("""() => {
                    const bar = document.querySelector('.desk-menubar').getBoundingClientRect();
                    const dock = document.querySelector('.desk-dock').getBoundingClientRect();
                    const win = document.querySelector(".desk-window-shell[aria-label='Meetings']").getBoundingClientRect();
                    const grip = document.querySelector(".desk-window-shell[aria-label='Meetings'] .desk-window-grip");
                    const g = grip.getBoundingClientRect();
                    const hit = document.elementFromPoint(g.left + g.width / 2, g.top + g.height / 2);
                    return {bar_bottom: Math.round(bar.bottom), dock_top: Math.round(dock.top),
                            top: Math.round(win.top), bottom: Math.round(win.bottom), grip_owned: grip.contains(hit)};
                }""")
                facts["zoom-band"] = band
                if abs(band["top"] - band["bar_bottom"]) > 2 or band["bottom"] > band["dock_top"] + 1 or not band["grip_owned"]:
                    fails["G2 zoom fills the screen between the bar and the shelf"] = band
                page.screenshot(path=str(SHOTS / "build-C1-2d-zoom-1440.png"))
                # The user sizes the zoomed window: the sizing gadget, dragged.
                grip = meetings.locator(".desk-window-grip").bounding_box()
                assert grip, "the zoomed window has no sizing gadget"
                gx, gy = grip["x"] + grip["width"] / 2, grip["y"] + grip["height"] / 2
                page.mouse.move(gx, gy)
                page.mouse.down()
                page.mouse.move(gx - 240, gy - 160, steps=12)
                page.mouse.up()
                sized = _rect(self._stack(page), "Meetings")
                if sized == zoomed:
                    fails["G2 the zoomed state resizes"] = {"zoomed": zoomed, "sized": sized}
                zoom.click()
                back = _rect(self._stack(page), "Meetings")
                if back != prior:
                    fails["G2 zoom back restores the exact prior rect"] = {"prior": prior, "back": back}
                zoom.click()
                again = _rect(self._stack(page), "Meetings")
                if again != sized:
                    fails["G2 zoom again restores the remembered zoomed rect"] = {"sized": sized, "again": again}
                doc = page.evaluate(DOC_JS) or {}
                panel = doc.get("panel", {})
                mid = next((k for k in (panel.get("zoom") or {}) if "meeting" in k.lower()), None)
                facts["workspace-panel"] = panel
                if not mid or mid not in panel.get("rects", {}) or mid not in panel.get("max", []):
                    fails["G2 both rects in the workspace document"] = panel
                # Each survives a reload: Meetings comes back zoomed at the
                # remembered zoomed rect, and zooms back to the prior rect.
                page.reload(wait_until="load")
                _normal_chair(page)
                meetings.wait_for()
                page.wait_for_timeout(800)
                reloaded = _rect(self._stack(page), "Meetings")
                if reloaded != sized or zoom.get_attribute("aria-pressed") != "true":
                    fails["G2 the zoomed rect survives a reload"] = {"sized": sized, "reloaded": reloaded}
                # G4 ⌃M: zoom back by key.
                page.keyboard.press("Control+m")
                page.wait_for_timeout(300)
                if zoom.get_attribute("aria-pressed") != "false" or _rect(self._stack(page), "Meetings") != prior:
                    fails["G4 ⌃M runs Zoom"] = _rect(self._stack(page), "Meetings")

                # G3 the right button in the BODY of Meetings (the front window).
                box = meetings.bounding_box()
                assert box
                page.mouse.click(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.55, button="right")
                page.locator(".desk-head-menu").first.wait_for()
                self._check_menu(page, "Meetings", width, facts, fails)
                page.locator(".desk-head-menu [role^='menuitem']", has_text="Desk").first.hover()
                page.wait_for_timeout(400)
                page.screenshot(path=str(SHOTS / "build-C1-2b-window-menu-amiga-keys-1440.png"))
                # The submenu sits beside its panel, never over it.
                over = page.evaluate("""() => { const [p, sb] = [...document.querySelectorAll('.desk-menu-list')].map((m) => m.getBoundingClientRect());
                  return sb ? (sb.left < p.right - 1 && sb.right > p.left + 1) : null; }""")
                if over is not False:
                    fails["G3 Desk ▸ opens beside the menu, not over it"] = over
                sub = page.locator(".desk-work-submenu [role^='menuitem']").all_inner_texts()
                facts["desk-submenu"] = sub
                if not any("New Note" in s for s in sub):
                    fails["G3 Desk ▸ carries the registry verbs"] = sub
                page.keyboard.press("Escape")
                page.keyboard.press("Escape")

                # G4 the other shortcuts, each by its verb's effect.
                page.keyboard.press("Meta+k")
                ok_k = page.locator("#desk-palette-listbox").is_visible()
                page.keyboard.press("Escape")
                page.keyboard.press("Meta+/")
                page.wait_for_timeout(300)
                ok_sheet = page.locator(".desk-shortcut-sheet").is_visible()
                page.keyboard.press("Escape")
                page.keyboard.press("Control+ArrowUp")
                page.wait_for_timeout(400)
                ok_expose = page.locator(".desk-expose").count() > 0
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
                facts["keys"] = {"⌘K": ok_k, "⌘/": ok_sheet, "⌃↑": ok_expose}
                for k, ok in facts["keys"].items():
                    if not ok:
                        fails[f"G4 {k} runs its verb"] = False
                # ⌘M iconifies the front window; its Dock chip brings it back.
                front = next(w["name"] for w in self._stack(page)["wins"] if w["front"])
                page.keyboard.press("Meta+m")
                page.wait_for_timeout(600)
                if any(w["name"] == front for w in self._stack(page)["wins"]):
                    fails["G4 ⌘M runs Iconify"] = front
                # ⌘W closes the front window.
                st = self._stack(page)
                front = next((w["name"] for w in st["wins"] if w["front"]), None)
                page.keyboard.press("Meta+w")
                page.wait_for_timeout(600)
                if front and any(w["name"] == front for w in self._stack(page)["wins"]):
                    fails["G4 ⌘W runs Close window"] = front
                # ⌘N makes a note (the one create path).
                before = len(self._notes(page))
                page.keyboard.press("Meta+n")
                page.wait_for_timeout(1200)
                if len(self._notes(page)) != before + 1:
                    fails["G4 ⌘N runs New Note"] = {"before": before, "after": len(self._notes(page))}

                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                facts["failures"] = fails
                (SHOTS / "gadget-facts-1440.json").write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n")
                assert not facts["errors"], facts["errors"]
                assert not fails, json.dumps(fails, indent=2, ensure_ascii=False)
            finally:
                browser.close()

    def test_zoom_survives_reload_unarranged_1440(self) -> None:
        """Astra on PR #731: open, Zoom, reload, Zoom -> the exact original
        rect, with NO drag first (a window the owner never arranged)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                _stage(page, "review-meetings")
                meetings = page.locator(".desk-window-shell[aria-label='Meetings']")
                meetings.wait_for()
                page.wait_for_timeout(600)
                original = _rect(self._stack(page), "Meetings")
                zoom = meetings.get_by_role("button", name="Zoom Meetings")
                zoom.click()
                zoomed = _rect(self._stack(page), "Meetings")
                page.reload(wait_until="load")
                _normal_chair(page)
                meetings.wait_for()
                page.wait_for_timeout(800)
                after_reload = _rect(self._stack(page), "Meetings")
                zoom.click()
                back = _rect(self._stack(page), "Meetings")
                facts = {"original": original, "zoomed": zoomed, "after_reload": after_reload, "back": back,
                         "errors": [e for e in errors if "ResizeObserver" not in e]}
                (SHOTS / "gadget-facts-zoom-reload-1440.json").write_text(json.dumps(facts, indent=2) + "\n")
                assert zoomed != original, facts
                assert after_reload == zoomed, facts
                assert back == original, facts
                assert not facts["errors"], facts["errors"]
            finally:
                browser.close()

    def _notes(self, page: Any) -> list[Any]:
        return page.evaluate(
            """async (token) => { const r = await fetch('/api/notes', {headers: {authorization: `Bearer ${token}`}});
               const j = await r.json(); return Array.isArray(j) ? j : (j.items || j.notes || []); }""",
            TOKEN,
        )

    def test_gadgets_393(self) -> None:
        from playwright.sync_api import sync_playwright

        width = 393
        facts: dict[str, Any] = {}
        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # G1 on the Chair: one window at a time; depth gives the work
                # area to the next Chair window. PHILO-14 A1 (#939): the
                # Chair's windows start closed; he opens the Brief, then Needs
                # you, from Go.
                open_chair_window(page, "Brief")
                open_chair_window(page, "Needs you")
                self._tap(page, page.get_by_role("button", name="To back Needs you"))
                st = self._stack(page)
                facts["chair-after-depth"] = st
                shown = [w["name"] for w in st["wins"]]
                if shown != ["Brief"] or _one_blue(st, "Brief"):
                    fails["G1 393 Chair: depth"] = st

                # Two desk windows, People in front.
                _stage(page, "review-meetings")
                page.locator(".desk-window-shell[aria-label='Meetings']").wait_for()
                _stage(page, "open-people")
                people = page.locator(".desk-window-shell[aria-label='People']")
                people.wait_for()
                st = self._stack(page)
                facts["two-windows"] = st
                if _one_blue(st, "People"):
                    fails["G1 393 setup: People front"] = st
                head = people.locator(":scope > .desk-pullout-head")
                labels = [b.get_attribute("aria-label") for b in head.locator("button").all() if b.is_visible()]
                facts["people-head"] = labels
                if not labels or labels[0] != "Close People" or labels[-1] != "To back People":
                    fails["G1 393 head: close ... depth"] = labels
                # Depth closes the row on the right edge (design §3, board C1-2c).
                edge = page.evaluate("""() => { const s = [...document.querySelectorAll('.desk-window-shell')].find((e) => e.getAttribute('aria-label') === 'People');
                  const h = s.querySelector(':scope > .desk-pullout-head').getBoundingClientRect();
                  const d = s.querySelector('.desk-gadget-depth').getBoundingClientRect(); return Math.round(h.right - d.right); }""")
                if edge > 2:
                    fails["G1 393 depth flush right"] = edge
                depth = people.get_by_role("button", name="To back People")
                db = depth.bounding_box() or {"width": 0, "height": 0}
                if db["width"] < 43.5 or db["height"] < 43.5:
                    fails["G1 393 depth owns 44 x 44"] = db
                page.screenshot(path=str(SHOTS / "build-C1-2c-before-depth-393.png"))
                self._tap(page, depth)
                st = self._stack(page)
                facts["after-depth"] = st
                faults = _one_blue(st, "Meetings")
                if _z(st, "People") >= _z(st, "Meetings"):
                    faults.append("People is not behind Meetings")
                if faults:
                    fails["G1 393 depth by touch"] = faults
                page.screenshot(path=str(SHOTS / "build-C1-2c-depth-to-back-393.png"))

                # G3 a long press in the body opens the window menu.
                meetings = page.locator(".desk-window-shell[aria-label='Meetings']")
                box = meetings.bounding_box()
                assert box
                self._long_press(page, box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.6)
                page.locator(".desk-head-menu").first.wait_for()
                _settle(page)
                self._check_menu(page, "Meetings", width, facts, fails)
                page.screenshot(path=str(SHOTS / "build-C1-2b-window-menu-amiga-keys-393.png"))
                # To back from the menu, by touch.
                self._tap(page, page.locator(".desk-head-menu [role^='menuitem']", has_text="To back").first)
                st = self._stack(page)
                facts["after-menu-depth"] = st
                if _behind(st, "Meetings"):
                    fails["G1 393 To back from the menu"] = _behind(st, "Meetings")

                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                facts["failures"] = fails
                (SHOTS / "gadget-facts-393.json").write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n")
                assert not facts["errors"], facts["errors"]
                assert not fails, json.dumps(fails, indent=2, ensure_ascii=False)
            finally:
                browser.close()

    def test_a_restored_window_is_lifted_above_the_dock_1440(self) -> None:
        """Astra on PR #805: a window saved at 1440x924 and reopened at
        1440x900 kept its foot at 848 px, under the Dock (824 px). The
        window's layout effect runs before the Dock publishes its height;
        the publish must lift the window. The sizing gadget must own its own
        centre after the reload, and after the viewport gets smaller.
        """
        from playwright.sync_api import sync_playwright

        owns = r"""() => {
          const shell = document.querySelector(".desk-window-shell[aria-label='Meetings']");
          const grip = shell.querySelector('.desk-gadget-size');
          const g = grip.getBoundingClientRect(), s = shell.getBoundingClientRect();
          const dock = document.querySelector('.desk-dock').getBoundingClientRect();
          const hit = document.elementFromPoint(g.left + g.width / 2, g.top + g.height / 2);
          return {owns: Boolean(hit && grip.contains(hit)), hit: hit ? String(hit.className).slice(0, 60) : null,
            foot: Math.round(s.bottom), dockTop: Math.round(dock.top), vh: innerHeight};
        }"""
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                page.set_viewport_size({"width": 1440, "height": 924})
                page.wait_for_timeout(400)
                _stage(page, "review-meetings")
                meetings = page.locator(".desk-window-shell[aria-label='Meetings']")
                meetings.wait_for()
                page.wait_for_timeout(600)
                # Snap Meetings to the left half: its foot is the band's foot.
                title = meetings.locator(".desk-pullout-title").bounding_box()
                assert title
                tx, ty = title["x"] + title["width"] / 2, title["y"] + title["height"] / 2
                page.mouse.move(tx, ty)
                page.mouse.down()
                page.mouse.move(1, 460, steps=12)
                page.mouse.up()
                page.wait_for_timeout(400)
                saved = page.evaluate(owns)
                assert saved["owns"] and saved["foot"] == saved["dockTop"], saved
                assert saved["foot"] > 900 - 76, saved  # under the Dock at 900 unless lifted

                # The reload at a smaller height: a new page of the same
                # context (the same saved workspace), never a resize.
                ctx = page.context
                page.close()
                page = ctx.new_page()
                page.set_viewport_size({"width": 1440, "height": 900})
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                meetings = page.locator(".desk-window-shell[aria-label='Meetings']")
                meetings.wait_for()
                page.wait_for_timeout(800)
                reloaded = page.evaluate(owns)
                assert reloaded["owns"] and reloaded["foot"] <= reloaded["dockTop"], reloaded

                # The viewport gets smaller: the window is clamped again.
                page.set_viewport_size({"width": 1440, "height": 860})
                page.wait_for_timeout(700)
                smaller = page.evaluate(owns)
                assert smaller["owns"] and smaller["foot"] <= smaller["dockTop"], smaller
                assert not errors, errors
            finally:
                browser.close()
