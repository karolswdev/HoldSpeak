"""PHILO-9-04 canvas: shoot the list face and the selection token at 1440 and 393.

Everything is live: a REAL hub (scripts/graph_walk.py serve, isolated HOME,
isolated DB) and the PRODUCT app served by vite. Board 0 (today) runs vite with
PROPOSAL=0 (nothing swapped); the proposal boards run vite with PROPOSAL=1
(harness/vite.config.mjs swaps DeskListView, DeskSortableTable and DeskMenu for
their marked PROPOSAL copies, and ProposedDeskListView imports canvas.css).

Seed: the grounding probe's objects (docs/internal/philo/phase-9/grounding/
probes/d2_probe.py.txt): zones Payments / Hiring / Architecture reviews, seven
notes, one note filed in Payments; the fresh hub's own objects make the rest.

Usage (from the repo root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-list-canvas/harness/shoot.py

shots/facts.json records, per board and width: text nodes under 12 px in the
list, raw (non-.btn) buttons in the list, the WCAG contrast of every distinct
(class, colour, ground) text style in the list, the selection contrasts, each
visible header's right edge against the viewport, the menu's last entry, and
the page's horizontal overflow.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
CANVAS = HERE.parent
REPO = CANVAS.parents[5]
WEB = REPO / "web"
SHOTS = CANVAS / "shots"
TOKEN = "philo9-04-canvas"
WIDTHS = [(1440, 900), (393, 852)]
CANVAS_PORT = int(os.environ.get("CANVAS_PORT", "4443"))
NOTES = ["Ledger cutover plan", "Priya 1:1 notes", "Tomas growth plan", "Vendor risk list",
         "Q4 capacity", "Incident review 42",
         "A very long note title that names the whole architecture decision record for the card ledger"]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_http(url: str, headers: dict[str, str] | None = None, timeout: float = 90) -> None:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=2) as r:
                if r.status < 500:
                    return
        except Exception:
            time.sleep(0.4)
    raise RuntimeError(f"not up: {url}")


def api(hub: str, method: str, path: str, body=None):
    req = urllib.request.Request(f"{hub}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "null")


COLOR_JS = r"""
// The Desk opens the list view straight away (the store's own key,
// desk/store/deskSlice.ts VIEW_KEY), so no board waits on the WebGL Floor.
try { localStorage.setItem('hs.desk.view', 'list'); } catch (e) {}
window.__c = (() => {
  const parse = (css) => {
    const m = css.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
    return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1};
  };
  const over = (top, under) => ({
    r: top.a * top.r + (1 - top.a) * under.r, g: top.a * top.g + (1 - top.a) * under.g,
    b: top.a * top.b + (1 - top.a) * under.b, a: 1});
  const ground = (el) => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const c = parse(getComputedStyle(e).backgroundColor);
      if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; }
    }
    let base = {r: 14, g: 15, b: 19, a: 1}; // --bg under everything
    for (let i = layers.length - 1; i >= 0; i--) base = over(layers[i], base);
    return base;
  };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return +((x + 0.05) / (y + 0.05)).toFixed(2); };
  const hex = (c) => `rgb(${Math.round(c.r)},${Math.round(c.g)},${Math.round(c.b)})`;
  return {parse, over, ground, ratio, hex};
})();
"""

FACTS = r"""() => {
  const C = window.__c;
  const list = document.querySelector('.desk-listmode');
  const vw = innerWidth, vh = innerHeight;
  const small = [], styles = {};
  if (list) {
    const walker = document.createTreeWalker(list, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const t = n.textContent.trim();
      if (!t || /^[●○✓✗⚠—↻ℹ«»·↑↓\[\]x ]+$/.test(t)) continue;
      const el = n.parentElement;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      if (!r.width || cs.visibility === 'hidden' || r.bottom < 0 || r.top > vh || el.closest('.sr-only')) continue;
      const fs = parseFloat(cs.fontSize);
      if (fs < 12) small.push({text: t.slice(0, 40), px: fs, cls: String(el.className).slice(0, 60)});
      const fg = C.parse(cs.color); const bg = C.ground(el);
      const ink = C.over(fg, bg);
      const key = `${String(el.className).split(' ')[0] || el.tagName.toLowerCase()}|${C.hex(ink)}|${C.hex(bg)}`;
      if (!styles[key]) styles[key] = {sample: t.slice(0, 30), cls: String(el.className).slice(0, 60), px: fs,
        ink: C.hex(ink), ground: C.hex(bg), ratio: C.ratio(ink, bg), count: 0};
      styles[key].count++;
    }
  }
  const heads = [...document.querySelectorAll('.desk-listmode thead th')].filter(th => th.getBoundingClientRect().width > 0)
    .map(th => { const r = th.getBoundingClientRect(); return {text: th.innerText.replace(/\s+/g, ' ').trim(), left: Math.round(r.left), right: Math.round(r.right), in_view: r.right <= vw + 0.5}; });
  const sortVerbs = [...document.querySelectorAll('.desk-listmode thead button')].map(b => ({
    text: b.innerText.replace(/\s+/g, ' ').trim(), library: b.classList.contains('btn'),
    visible: b.getBoundingClientRect().width > 0, pressed: b.getAttribute('aria-pressed'),
    right: Math.round(b.getBoundingClientRect().right)}));
  const cellsOut = [...document.querySelectorAll('.desk-listmode tbody td')].filter(td => {
    const r = td.getBoundingClientRect(); return r.width > 0 && td.innerText.trim() && r.right > vw + 0.5; }).length;
  const items = [...document.querySelectorAll('[role=menu] [role=menuitem]')].filter(e => e.getBoundingClientRect().height > 0);
  const last = items.at(-1); const del = items.find(e => /Delete/.test(e.innerText));
  const rect = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return {text: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 30), top: Math.round(r.top), bottom: Math.round(r.bottom),
      right: Math.round(r.right), vh, cut_px: Math.max(0, Math.round(r.bottom - vh))}; };
  return {
    vw, vh,
    census: document.querySelector('.desk-list-census span')?.innerText.trim() ?? null,
    status: document.querySelector('.desk-list-status')?.innerText.trim() ?? null,
    small_text_count: small.length, small_text: small.slice(0, 20),
    raw_buttons_in_list: list ? [...list.querySelectorAll('button')].filter(b => !b.classList.contains('btn') && !b.classList.contains('btn--chrome')).map(b => String(b.className).slice(0, 50)) : null,
    text_styles: Object.values(styles).sort((a, b) => a.ratio - b.ratio),
    min_text_ratio: Object.values(styles).reduce((m, s) => Math.min(m, s.ratio), 99),
    headers: heads, sort_verbs: sortVerbs, cells_past_right_edge: cellsOut,
    fold_lines_visible: [...document.querySelectorAll('.desk-list-fold')].filter(e => e.getBoundingClientRect().height > 0).length,
    menu_last: rect(last), menu_delete: rect(del),
    h_overflow: document.documentElement.scrollWidth > vw,
  };
}"""

SELECTION = r"""(sel) => {
  const C = window.__c;
  const f = document.querySelector(sel);
  if (!f) return null;
  const s = getComputedStyle(f, '::selection');
  const field = C.ground(f);
  const sbg = C.parse(s.backgroundColor) || {r: 0, g: 0, b: 0, a: 0};
  const painted = C.over(sbg, field);
  const ink = C.over(C.parse(s.color), painted);
  const plain = C.over(C.parse(getComputedStyle(f).color), field);
  return {selector: sel, focused: document.activeElement === f, start: f.selectionStart, end: f.selectionEnd,
    length: f.value.length, selection_bg: s.backgroundColor, selection_ink: s.color,
    field_bg: C.hex(field), painted: C.hex(painted),
    selection_vs_field: C.ratio(painted, field),
    selected_text_vs_selection: C.ratio(ink, painted),
    unselected_text_vs_field: C.ratio(plain, field)};
}"""


def main() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    home = tempfile.mkdtemp(prefix="philo9-04-canvas-")
    hub_port = free_port()
    hub_url = f"http://127.0.0.1:{hub_port}"
    hub = subprocess.Popen(
        ["uv", "run", "--extra", "test", "python", "scripts/graph_walk.py", "serve", "--port", str(hub_port), "--token", TOKEN],
        cwd=REPO, env={**os.environ, "HOME": home}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    facts: dict[str, dict] = {"_seed": {}, "_home_is_isolated": home}
    vite = None
    try:
        wait_http(f"{hub_url}/api/projects", {"Authorization": f"Bearer {TOKEN}"})
        print("hub up", hub_url, flush=True)
        zones = [api(hub_url, "POST", "/api/directories", {"name": n}) for n in ("Payments", "Hiring", "Architecture reviews")]
        notes = [api(hub_url, "POST", "/api/notes", {"title": t, "body": t}) for t in NOTES]
        zid = (zones[0].get("directory") or zones[0])["id"]
        nid = (notes[0].get("note") or notes[0])["id"]
        api(hub_url, "PUT", f"/api/directories/{zid}/members/note:{nid}", {})
        facts["_seed"] = {"zones": 3, "notes": len(notes), "filed": f"note:{nid} -> Payments"}

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for proposal in (False, True):
                # A stale server on the port would answer for this one (and serve the
                # wrong face): refuse to shoot through it.
                with socket.socket() as probe:
                    if probe.connect_ex(("127.0.0.1", CANVAS_PORT)) == 0:
                        raise RuntimeError(f"port {CANVAS_PORT} is already served; stop that server first")
                vite = subprocess.Popen(
                    [str(WEB / "node_modules/.bin/vite"), "--config", str(HERE / "vite.config.mjs")],
                    cwd=WEB, env={**os.environ, "HUB": hub_url, "CANVAS_PORT": str(CANVAS_PORT),
                                  "PROPOSAL": "1" if proposal else "0"},
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                origin = f"http://127.0.0.1:{CANVAS_PORT}"
                wait_http(f"{origin}/")
                print("vite up", proposal, flush=True)
                for width, height in WIDTHS:
                    ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
                    ctx.add_init_script(COLOR_JS)
                    page = ctx.new_page()
                    page.set_default_timeout(45_000)
                    print("page", width, flush=True)
                    errors: list[str] = []
                    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
                    page.goto(f"{origin}/?token={TOKEN}", wait_until="domcontentloaded")
                    # The first-run voice card may lead; Continue later leaves it.
                    later = page.get_by_role("button", name="Continue later", exact=True)
                    page.locator("[data-testid=chair-floor-toggle], button:has-text('Continue later')").first.wait_for(timeout=90_000)
                    if later.count():
                        later.first.click()
                    page.locator("[data-testid=chair-floor-toggle]").wait_for(timeout=60_000)
                    print("chair", width, flush=True)

                    def palette(query: str) -> None:
                        page.locator("[aria-controls=desk-tool-shelf]").click()
                        page.locator("[aria-controls=desk-palette-listbox]").fill(query)

                    def to_list() -> None:
                        page.locator("[data-testid=chair-floor-toggle]").click()
                        try:  # 393 opens the list itself; 1440 opens the Floor
                            page.locator(".desk-listmode").wait_for(timeout=6_000)
                        except Exception:
                            pass
                        if not page.locator(".desk-listmode").count():
                            page.locator("[aria-controls=desk-tool-shelf]").wait_for(state="visible", timeout=90_000)
                            palette("List view")
                            page.locator("[id='desk-palette-option-desk.toggle-view']").click()
                        page.locator(".desk-listmode").wait_for(timeout=20_000)
                        page.wait_for_timeout(1200)

                    def shoot(board: str, extra: dict | None = None) -> None:
                        key = f"{board}-{width}"
                        page.screenshot(path=str(SHOTS / f"{key}.png"))
                        facts[key] = {**page.evaluate(FACTS), **(extra or {}), "page_errors": errors[:]}
                        f = facts[key]
                        print(key, f["status"], "small", f["small_text_count"], "raw", len(f["raw_buttons_in_list"] or []),
                              "cells_out", f["cells_past_right_edge"], "min", f["min_text_ratio"], "menu", f["menu_last"])

                    def row_menu(board: str) -> None:
                        # An OBJECT row (zone rows have no menu) scrolled to sit just
                        # above the lowest free band: above the dock at 393, near the
                        # window edge at 1440, as the grounding probe found it.
                        row = page.locator(".desk-listmode tbody tr.desk-sortable-table-row:has(.desk-list-mark)").nth(3)
                        row.scroll_into_view_if_needed()
                        target = height - (150 if width < 720 else 60)
                        box = row.bounding_box()
                        page.mouse.wheel(0, box["y"] + box["height"] - target)
                        page.wait_for_timeout(500)
                        box = row.bounding_box()
                        page.mouse.click(box["x"] + 60, box["y"] + box["height"] / 2, button="right")
                        page.wait_for_timeout(800)
                        page.mouse.move(2, 60)
                        page.wait_for_timeout(200)
                        shoot(board, {"menu_row_y": round(box["y"]), "menu_row_bottom": round(box["y"] + box["height"]),
                                      "menu_opened": page.locator("[role=menu]").count() > 0})
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(300)
                        page.evaluate("window.scrollTo(0, 0)")

                    def zone_field(board: str) -> None:
                        palette("New Zone")
                        page.locator("[id='desk-palette-option-desk.new-zone']").click()
                        f = page.locator(".desk-listmode input.desk-zone-rename")
                        f.wait_for(timeout=20_000)
                        page.wait_for_timeout(500)
                        sel = page.evaluate(SELECTION, ".desk-listmode input.desk-zone-rename")
                        shoot(board, {"selection": sel})
                        f.screenshot(path=str(SHOTS / f"{board}-field-{width}.png"))
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(500)

                    def palette_field(board: str) -> None:
                        palette("Ledger cutover")
                        page.wait_for_timeout(500)
                        page.evaluate("document.querySelector('[aria-controls=desk-palette-listbox]').select()")
                        page.wait_for_timeout(200)
                        sel = page.evaluate(SELECTION, "[aria-controls=desk-palette-listbox]")
                        shoot(board, {"selection": sel})
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(400)

                    to_list()
                    if not proposal:
                        shoot("0-today-list")
                        row_menu("0-today-row-menu")
                        zone_field("0-today-selection-zone")
                        palette_field("0-today-selection-palette")
                    else:
                        shoot("1-list")
                        # Sort by Zone: the library Button (at 393 it rides the Name header).
                        page.locator(".desk-listmode thead button:visible", has_text="Zone").first.click()
                        page.wait_for_timeout(500)
                        shoot("2-sorted-by-zone")
                        page.locator(".desk-listmode thead button:visible", has_text="Name").first.click()
                        page.wait_for_timeout(300)
                        row_menu("3-row-menu-bottom")
                        # One shown: dive into Payments (one filed note).
                        page.get_by_role("button", name="Payments zone").first.click()
                        page.wait_for_timeout(1500)
                        shoot("4-one-shown")
                        page.locator(".desk-list-census button", has_text="ALL").first.click()
                        page.wait_for_timeout(1200)
                        zone_field("5-selection-zone")
                        palette_field("6-selection-palette")
                    ctx.close()
                    # Put the desk back: remove the zones New Zone made.
                    for d in api(hub_url, "GET", "/api/directories").get("directories", []):
                        if str(d.get("name", "")).startswith("New zone"):
                            api(hub_url, "DELETE", f"/api/directories/{d['id']}")
                vite.terminate()
                vite.wait(timeout=10)
                vite = None
            browser.close()
    finally:
        if vite:
            vite.terminate()
        hub.terminate()
        try:
            hub.wait(timeout=10)
        except Exception:
            hub.kill()
    (SHOTS / "facts.json").write_text(json.dumps(facts, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print("facts:", SHOTS / "facts.json")


if __name__ == "__main__":
    main()
