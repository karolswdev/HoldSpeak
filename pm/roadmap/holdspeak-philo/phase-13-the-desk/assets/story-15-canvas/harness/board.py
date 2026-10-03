"""PHILO-13-15/17 canvas: the shared board runner (one stack per width, the fences, the touch hands).

The fence code is C1's, imported from the RATIFIED canvas harness unchanged
(../../story-11-canvas/harness/shoot.py: JS_LIB, CONTRAST_ALL, CLIP, OVERLAP,
TARGETS44), so a board here is measured by exactly the rules the owner ratified.
The front-window and content fences read the BUILT product's classes
(`.is-front`, the blue head) instead of C1's canvas-only `data-p13-front`.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rig  # noqa: E402  (registered as `rig` first, so C1's module reuses it)

_spec = importlib.util.spec_from_file_location("c1shoot", HERE.parents[1] / "story-11-canvas/harness/shoot.py")
C1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C1)
JS_LIB, CONTRAST_ALL, CLIP, OVERLAP, TARGETS44 = C1.JS_LIB, C1.CONTRAST_ALL, C1.CLIP, C1.OVERLAP, C1.TARGETS44

ALL_WIDTHS = [(1440, 900), (393, 852)]
BLUE = "rgb(102, 136, 187)"

FRONT = "() => {" + JS_LIB + r"""
  const heads = [...document.querySelectorAll('.desk-window-shell > .desk-pullout-head')].filter((h) => shown(h));
  const blue = heads.filter((h) => getComputedStyle(h).backgroundColor === '""" + BLUE + r"""');
  const front = document.querySelector('.desk-window-shell.is-front');
  let onGlass = false;
  if (front) { const hd = front.querySelector(':scope > .desk-pullout-head') || front; const r = hd.getBoundingClientRect();
    onGlass = [0.1, 0.3, 0.5, 0.7, 0.9].some((f) => { const h = document.elementFromPoint(r.left + r.width * f, r.top + r.height / 2); return !!h && (front.contains(h) || !!h.closest('[role=menu]')); }); }
  return { blue: blue.map((h) => h.parentElement.getAttribute('aria-label') || '?'), front: front ? front.getAttribute('aria-label') : null, on_glass: onGlass };
}"""

BASIC = r"""() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && !e.closest('[hidden]') && r.bottom > 0 && r.top < innerHeight; };
  const small = [], raw = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const t = n.textContent.trim(); if (!t || !/[A-Za-z0-9]/.test(t)) continue;
    const el = n.parentElement; if (!vis(el)) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize); if (fs > 0 && fs < 12) small.push({ text: t.slice(0, 30), fs });
  }
  for (const b of document.querySelectorAll('button')) {
    if (!vis(b)) continue;
    if (!/(^|\s)(btn|btn--chrome)(\s|$)/.test(String(b.className || '')) && !b.closest('.desk-menu-list'))
      raw.push({ text: (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 30), cls: String(b.className).slice(0, 50), win: (b.closest('.desk-window-shell') || {}).id || null });
  }
  const menus = [...document.querySelectorAll('[role=menu]')].filter(vis).map((m) => ({ label: m.getAttribute('aria-label'),
    rows: [...m.querySelectorAll('[role^=menuitem]')].filter(vis).map((r) => r.innerText.replace(/\s+/g, ' ').trim()) }));
  const r = (s) => { const e = document.querySelector(s); if (!e || !vis(e)) return null; const b = e.getBoundingClientRect(); return { top: Math.round(b.top), h: Math.round(b.height) }; };
  return { small_text: small, raw_buttons: raw, menus, screen_title: (document.querySelector('.desk-screen-name') || {}).innerText || null,
    modal: !!document.querySelector('[role=dialog][aria-modal=true], dialog[open]'), h_overflow: document.documentElement.scrollWidth > innerWidth,
    scratch_path: /p13c57-|\/private\/tmp|\/tmp\//.test(document.body.innerText),
    frame: { menubar: r('.desk-menubar'), dock: r('.desk-dock'), capture: r('[data-testid=arrival-capture-bar]') } };
}"""

CONTENT = r"""() => {
  const f = document.querySelector('.desk-window-shell.is-front'); if (!f) return null;
  const r = f.getBoundingClientRect(); const head = f.querySelector(':scope > .desk-pullout-head'); const hh = head ? head.getBoundingClientRect().height : 0;
  const cs = getComputedStyle(f); const bt = parseFloat(cs.borderTopWidth) + parseFloat(cs.borderBottomWidth);
  return Math.round(Math.min(r.bottom, innerHeight) - Math.max(r.top, 0) - hh - bt);
}"""

# A named element is WHOLE on screen: its full box inside the viewport and every clipping ancestor,
# and on top at its centre (the Phase 12 visibility probe, Astra canvas r1 finding 4).
WHOLE = "(sel) => {" + JS_LIB + r"""
  const e = typeof sel === 'string' ? document.querySelector(sel) : null; if (!e || !shown(e)) return { found: !!e, whole: false };
  const v = vrect(e); const h = document.elementFromPoint((v.l + v.r) / 2, (v.t + v.b) / 2);
  return { found: true, whole: v.full && !!h && (e === h || e.contains(h) || h.contains(e)), w: Math.round(v.w), h: Math.round(v.h), top: Math.round(v.t) };
}"""


# Astra canvas r1, condition 6: C1's TARGETS44 counts a point covered by the menu bar or the Dock as
# "occluded" (another layer), so a content control under chrome passes. For C7 the chrome must own NO
# point of a content control's 44 px band: every fully visible control inside a window (menus excepted),
# nine points of its box grown to 44 x 44; a point whose top element is in the menu bar or the Dock fails.
CHROME_OWNS = "() => {" + JS_LIB + r"""
  const out = [];
  for (const t of document.querySelectorAll('button, a[href], [role=button], [role=menuitem], [role=tab], [role=checkbox], input:not([type=hidden]), select, textarea')) {
    if (!shown(t) || !t.closest('.desk-window-shell') || t.closest('[role=menu], .desk-menubar, .desk-dock')) continue;
    if (t.parentElement && t.parentElement.closest('button, [role=button], a[href], [role=menuitem]')) continue;
    const v = vrect(t); if (!v.full) continue;
    const cx = (v.l + v.r) / 2, cy = (v.t + v.b) / 2, hw = Math.max(22, v.w / 2), hh = Math.max(22, v.h / 2);
    const w0 = (document.elementFromPoint(cx, cy) || { closest: () => null }).closest('.desk-window-shell');
    if (w0 && w0 !== t.closest('.desk-window-shell')) continue;   // a window behind another window: not on the glass
    const hits = nine(cx - hw, cy - hh, cx + hw, cy + hh).map(([x, y]) => document.elementFromPoint(x, y)).filter((h) => h && h.closest('.desk-menubar, .desk-dock'));
    if (hits.length) out.push({ name: (t.getAttribute('aria-label') || t.innerText || '').toString().trim().replace(/\s+/g, ' ').slice(0, 32), chrome_points: hits.length, w: Math.round(v.w), h: Math.round(v.h) });
  }
  return out;
}"""

# Astra canvas r1, condition 4: a desktop submenu opens NEXT TO its parent panel (its left edge at the
# parent's right edge, or its right edge at the parent's left edge, within 3 px; tops overlap).
SUBMENU_ADJ = r"""() => {
  const subs = [...document.querySelectorAll('[role=menu].desk-work-submenu')].filter((m) => m.getBoundingClientRect().width);
  return subs.map((m) => { const p = m.parentElement.closest('[role=menu]'); const r = m.getBoundingClientRect(), q = p.getBoundingClientRect();
    const right = Math.abs(r.left - q.right) <= 3, left = Math.abs(r.right - q.left) <= 3;
    return { label: m.getAttribute('aria-label'), adjacent: (right || left) && r.top < q.bottom && r.bottom > q.top, side: right ? 'right' : left ? 'left' : 'apart', gap_right: Math.round(r.left - q.right) }; });
}"""


class Runner:
    """One width: a fresh stack (hub + vite on a scratch HOME), a page, shoot() with the fences."""

    def __init__(self, shots: Path, prefix: str, width: int, height: int, shims: str, state: dict | None = None):
        self.shots, self.prefix, self.width, self.height, self.shims = shots, prefix, width, height, shims
        self.phone = width <= 420
        self.facts: dict = {}
        self.fails: list[str] = []
        self.errors: list[str] = []
        self.state = state
        self.only = os.environ.get("ONLY", "")
        self.scope44: str | None = None
        self.strict_chrome = False   # C7 sets it (condition 6)

    # ── hands ──
    def ev(self, js: str, arg=None):
        return self.page.evaluate(js, arg)

    def settle(self, ms=700):
        self.page.wait_for_timeout(ms)

    def tap(self, loc, settle=700):
        """393: every press is a touch tap (CDP touch); 1440: a mouse click."""
        loc = loc.first
        loc.scroll_into_view_if_needed()
        b = loc.bounding_box()
        if self.phone:
            self.page.touchscreen.tap(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        else:
            loc.click()
        self.settle(settle)

    def long_press(self, x: float, y: float, ms=700):
        cdp = self.page.context.new_cdp_session(self.page)
        pt = [{"x": x, "y": y, "id": 1}]
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": pt})
        self.page.wait_for_timeout(ms)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        cdp.detach()
        self.settle(500)

    def window_menu(self, win_id: str):
        """Open the window's menu: the right button on its title bar (1440) or a long press (393)."""
        head = self.page.locator(f"[id='{win_id}'] > .desk-pullout-head")
        t = head.locator(".desk-pullout-title").first
        b = t.bounding_box() if t.count() and t.is_visible() else head.first.bounding_box()
        x, y = b["x"] + min(b["width"] - 4, max(8, b["width"] / 2)), b["y"] + b["height"] / 2
        if self.phone:
            self.long_press(x, y)
        else:
            self.page.mouse.click(x, y, button="right")
            self.settle(500)
        self.page.locator("[role=menu]").first.wait_for(timeout=10_000)

    def open_sub(self, label_start: str):
        sub = self.page.locator(f"[role=menu] [role=menuitem][aria-haspopup=menu]:has-text('{label_start}')").first
        if self.phone:
            self.tap(sub, 600)
        else:
            sub.hover()
            self.settle(700)

    def pick_row(self, text: str):
        self.tap(self.page.locator(f"[role=menu] [role^=menuitem]:has-text('{text}')").last, 900)

    def escape(self):
        self.page.keyboard.press("Escape")
        self.page.keyboard.press("Escape")
        self.settle(300)

    def close_all(self):
        self.ev("() => window.__cOpen.closeAll()")
        self.settle(600)
        self.page.keyboard.press("Escape")
        self.settle(300)

    def boot(self):
        p = self.page
        p.goto(self.url, wait_until="load")
        p.locator(".chair, [data-testid=chair-desk], button:has-text('Continue later')").first.wait_for(timeout=180_000)
        self.settle(2500)
        for _ in range(30):
            cl = p.get_by_role("button", name="Continue later", exact=True)
            if not cl.count():
                break
            try:
                cl.first.click(timeout=2000)
            except Exception:
                pass
            self.settle(600)
        p.locator("[data-testid=chair-desk]").wait_for(state="attached", timeout=60_000)
        self.settle(2500)
        # Every board starts on the Chair with no desk window open (the warm-up's windows persist).
        self.close_all()
        self.ev("() => { window.__cBooted = true; }")

    # ── the board ──
    def shoot(self, board: str, front: str | None, checks: dict | None = None, extra: dict | None = None, whole: list[str] | None = None):
        if self.only and not board.startswith(self.only):
            return None
        self.ev("() => { if (!document.querySelector('[role=menu]')) document.activeElement?.blur?.(); }")
        self.settle(600)
        key = f"{board}-{self.width}"
        if not self.ev("() => window.__cBooted === true"):
            self.fails.append(f"{key}: the page reloaded during the run")
        self.page.screenshot(path=str(self.shots / f"{key}.png"))
        f = self.ev(BASIC)
        f["front_state"] = self.ev(FRONT)
        f["low_contrast"] = self.ev(CONTRAST_ALL)
        f["clip"] = self.ev(CLIP)
        ov = self.ev(OVERLAP)
        f["overlap"], f["overlap_waived"] = ov["hits"], ov["waived"]
        if self.phone:
            f["targets_under_44"] = self.ev(TARGETS44)
            if self.scope44:
                # This story's own surfaces only; every other small target is recorded as inherited.
                mine = set(self.ev(self.scope44))
                f["inherited_under_44"] = [t for t in f["targets_under_44"] if t["name"] not in mine]
                f["targets_under_44"] = [t for t in f["targets_under_44"] if t["name"] in mine]
            f["content_px"] = self.ev(CONTENT)
        if whole:
            f["whole"] = {s: self.ev(WHOLE, s) for s in whole}
        f["submenus"] = self.ev(SUBMENU_ADJ)
        if self.strict_chrome and self.phone:
            f["chrome_owns_content"] = self.ev(CHROME_OWNS)
        f["intended_front"] = front
        if extra:
            f.update(extra)
        self.facts[key] = f
        fs = f["front_state"]
        law = {
            "no text under 12 px": not f["small_text"],
            "no modal": not f["modal"],
            "no horizontal overflow": not f["h_overflow"],
            "no scratch path on the glass": not f["scratch_path"],
            "exactly one blue title bar": len(fs["blue"]) == 1,
            "the intended window is the front one, on the glass": front is None or (fs["front"] == front and fs["on_glass"]),
            "in-place contrast >= 4.5:1 (3:1 large)": not f["low_contrast"],
            "no sideways strip": not f["clip"]["strips"],
            "no clipped text": not f["clip"]["clipped"],
            "no rendered overlap": not f["overlap"],
        }
        if not self.phone:
            law["a desktop submenu opens next to its parent panel"] = all(m["adjacent"] for m in f["submenus"])
        if self.strict_chrome and self.phone:
            law["C7: the menu bar and the Dock own no point of a content control's 44 px band"] = not f["chrome_owns_content"]
        if whole:
            for s, w in f["whole"].items():
                law[f"whole on screen: {s}"] = bool(w.get("whole"))
        if self.phone:
            law["393: no target under 44 x 44 (owned)"] = not f["targets_under_44"]
        for name, ok in {**law, **(checks or {})}.items():
            if not ok:
                self.fails.append(f"{key}: {name}")
        print(key, "front", fs["front"], "blue", fs["blue"], "lowc", f["low_contrast"][:2], "t44", (f.get("targets_under_44") or [])[:3],
              "ov", f["overlap"][:2], "clip", f["clip"]["clipped"][:2], "small", f["small_text"][:2], "whole", {k: v.get("whole") for k, v in (f.get("whole") or {}).items()}, flush=True)
        return f

    def run(self, boards) -> None:
        stack = None
        try:
            if self.state is None:
                stack = rig.Stack("proposal", self.shims).__enter__()
                self.url, self.seed, guard = stack.url, stack.seed, stack.guard
            else:
                self.url, self.seed, guard = self.state["url"], self.state["seed"], self.state.get("guard")
            self.facts[f"_seat_guard_{self.width}"] = guard
            self.shots.mkdir(parents=True, exist_ok=True)
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                ctx = browser.new_context(viewport={"width": self.width, "height": self.height}, device_scale_factor=2, has_touch=self.phone)

                def page():
                    pg = ctx.new_page()
                    pg.on("pageerror", lambda e: self.errors.append(f"pageerror: {e}"))
                    pg.on("console", lambda m: self.errors.append(f"console: {m.text[:200]}")
                          if m.type == "error" and "status of 4" not in m.text and "Failed to fetch" not in m.text else None)
                    return pg
                try:
                    # WARM-UP (no shot, no write): a cold vite optimizes a lazy window's dependency the first
                    # time it opens and then RELOADS the page. Open every window once, then start clean.
                    if not os.environ.get("NO_WARMUP"):
                        self.page = page()
                        try:
                            self.boot()
                            for js in ["window.__cOpen.open('meeting:m-standup')", "window.__cOpen.open('decision:d-freeze')",
                                       "window.__cOpen.open('artifact:art-cutover-reqs')", "window.__cOpen.room('p-ledger')",
                                       "window.__cOpen.brief()", "window.__cOpen.surface('review-meetings')",
                                       "window.__cOpen.surface('open-people')", "window.__cOpen.surface('configure-settings', 'integrations')"]:
                                self.ev("() => " + js)
                                self.settle(2500)
                        except Exception as exc:
                            print("warm-up:", str(exc).splitlines()[0][:200], flush=True)
                        self.settle(3000)
                        try:
                            self.close_all()
                        except Exception:
                            pass
                        self.page.close()
                    self.errors.clear()
                    self.page = page()
                    self.boot()
                    boards(self)
                except Exception as exc:
                    traceback.print_exc()
                    self.fails.append(f"CRASH at width {self.width}: {str(exc).splitlines()[0][:300]}")
                    try:
                        self.page.screenshot(path=str(self.shots / f"_crash-{self.width}.png"))
                    except Exception:
                        pass
                browser.close()
        finally:
            if stack is not None:
                stack.__exit__(None, None, None)
            self.facts[f"_browser_errors_{self.width}"] = self.errors
            if self.errors:
                self.fails.append(f"browser errors at {self.width}: {self.errors[:3]}")


def main(shots: Path, prefix: str, shims: str, boards) -> int:
    state = json.loads(Path(os.environ["STACK_STATE"]).read_text()) if os.environ.get("STACK_STATE") else None
    widths = [w for w in ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
    facts_path = shots / "facts.json"
    facts: dict = json.loads(facts_path.read_text()) if (os.environ.get("ONLY") or os.environ.get("ONLY_WIDTH")) and facts_path.exists() else {}
    fails: list[str] = []
    for width, height in widths:
        r = Runner(shots, prefix, width, height, shims, state)
        r.run(boards)
        fails += r.fails
        facts.update(r.facts)
    facts["_fails"] = fails
    facts_path.write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    print("\nFAILS:" if fails else "\nALL FENCES HELD", *fails, sep="\n  ")
    return 2 if fails else 0
