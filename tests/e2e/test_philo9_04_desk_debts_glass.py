"""PHILO-9-04 -- the desk debts, fenced AS RENDERED through the real hub on an
isolated HOME at 1440x900 and 393x852.

The owner ratified the list canvas "as drawn" on 2026-09-27
(pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/
story-04-list-canvas/): Q6 the selection token (--selection-bg: var(--accent),
--selection-ink: var(--bg)) desk-wide; Q7 at 393 Kind, Zone and Attention fold
into a second line in the name Button, their sort Buttons in the NAME header,
by `@container surface`. Settled: every desk menu keeps itself in view, with
44 px rows at 393; "SHOWN" for any count; all list text at 12 px or more; the
sort headers are the library Button; ATTN at 4.5:1 or more.

The charter's red-first matrix (current-phase-status.md "D2" rows):
  selection >= 3:1              red at 1440 and 393
  list text >= 12 px, SHOWN     red at 1440 and 393
  every kept column in view     preservation green at 1440, red at 393
  row menu in view (bottom)     preservation green at 1440, red at 393
  sort headers library Button   red at both (structural; the unit fence
                                tests/unit/test_philo9_04_sort_button_fence.py
                                carries the mutation)
The measurements reuse the canvas harness's probes (harness/shoot.py):
the same composited-ground contrast, the same scan roots (the list AND every
open menu, which portals outside the list), the same nine-point pointer pass.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the desk-debts glass needs Playwright")

TOKEN = "philo9-04-desk-debts"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-04-shots")
SIZES = {1440: 900, 393: 852}
WIDTHS = list(SIZES)
T = 20_000
NOTES = ["Ledger cutover plan", "Priya 1:1 notes", "Tomas growth plan", "Vendor risk list",
         "Q4 capacity", "Incident review 42",
         "A very long note title that names the whole architecture decision record for the card ledger"]

# The canvas harness's colour helpers (shoot.py COLOR_JS), and the list view
# opened straight away (the store's own key, desk/store/deskSlice.ts VIEW_KEY).
COLOR_JS = r"""
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
    let base = {r: 14, g: 15, b: 19, a: 1};
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
  const roots = [list, ...document.querySelectorAll('[role=menu]')].filter(Boolean);
  for (const root of roots) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
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
    .map(th => { const r = th.getBoundingClientRect(); return {text: th.innerText.replace(/\s+/g, ' ').trim(), right: Math.round(r.right), in_view: r.right <= vw + 0.5}; });
  const sortVerbs = [...document.querySelectorAll('.desk-listmode thead button')].map(b => ({
    text: b.innerText.replace(/\s+/g, ' ').trim(), library: b.classList.contains('btn'),
    visible: b.getBoundingClientRect().width > 0, pressed: b.getAttribute('aria-pressed')}));
  const cellsOut = [...document.querySelectorAll('.desk-listmode tbody td')].filter(td => {
    const r = td.getBoundingClientRect(); return r.width > 0 && td.innerText.trim() && r.right > vw + 0.5; }).length;
  const items = [...document.querySelectorAll('[role=menu] [role=menuitem]')].filter(e => e.getBoundingClientRect().height > 0);
  const last = items.at(-1);
  const rect = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return {text: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 30), top: Math.round(r.top), bottom: Math.round(r.bottom), vh}; };
  // Each visible object row's Kind and Zone words, read where the owner can
  // see them: a visible cell or the visible fold line, inside the viewport.
  const rowWords = [...document.querySelectorAll('.desk-listmode tbody tr.desk-sortable-table-row')]
    .filter(tr => tr.querySelector('.desk-list-mark') && tr.getBoundingClientRect().height > 0).map(tr => {
      const seen = [...tr.querySelectorAll('td, .desk-list-fold-token')].filter(e => {
        const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.left >= -0.5 && r.right <= vw + 0.5
          && getComputedStyle(e).display !== 'none'; }).map(e => e.innerText.replace(/\s+/g, ' ').trim()).join(' | ');
      return seen;
    });
  return {
    vw, vh,
    status: document.querySelector('.desk-list-status')?.innerText.trim() ?? null,
    small_text_count: small.length, small_text: small.slice(0, 20),
    menu_rows: items.map(e => { const r = e.getBoundingClientRect(); return {text: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 30), h: +r.height.toFixed(1), top: Math.round(r.top), bottom: Math.round(r.bottom)}; }),
    scroll_width: document.documentElement.scrollWidth,
    attention_tokens: [...document.querySelectorAll('.desk-list-attention')].filter(e => e.getBoundingClientRect().width > 0)
      .map(e => { const cs = getComputedStyle(e); const bg = C.ground(e); const ink = C.over(C.parse(cs.color), bg);
        return {text: e.innerText.trim(), px: parseFloat(cs.fontSize), ratio: C.ratio(ink, bg)}; }),
    raw_buttons_in_list: list ? [...list.querySelectorAll('button')].filter(b => !b.classList.contains('btn') && !b.classList.contains('btn--chrome')).map(b => String(b.className).slice(0, 50)) : null,
    text_styles: Object.values(styles).sort((a, b) => a.ratio - b.ratio).slice(0, 6),
    min_text_ratio: Object.values(styles).reduce((m, s) => Math.min(m, s.ratio), 99),
    headers: heads, sort_verbs: sortVerbs, cells_past_right_edge: cellsOut,
    row_words: rowWords,
    menu_last: rect(last),
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
  return {start: f.selectionStart, end: f.selectionEnd, length: f.value.length,
    selection_bg: s.backgroundColor, selection_ink: s.color, field_bg: C.hex(field),
    selection_vs_field: C.ratio(painted, field), selected_text_vs_selection: C.ratio(ink, painted)};
}"""

# The pointer pass (shoot.py POINTS / HIT / PM_ARM / PM_READ): nine points per
# control (centre, edge midpoints, corners, inset 1 px); at 393 on the 44 x 44
# target (UX-CANON C). A point is owned when elementFromPoint AND the target of
# a real pointermove both land inside the control.
POINTS = r"""([width, kinds]) => {
  document.querySelectorAll('[data-probe]').forEach(e => e.removeAttribute('data-probe'));
  const pick = {sort: '.desk-listmode thead .btn', menu: '[role=menu] [role=menuitem]', census: '.desk-list-census .btn',
                name: '.desk-listmode tbody .desk-sortable-table-open',
                submenu: "[role=menu][aria-label='Launch submenu'] [role=menuitem]"};
  // The name Buttons (the fold line rides inside them at 393): the first six
  // wholly in the upper band of the viewport, clear of the fixed dock.
  const band = (b) => { const r = b.getBoundingClientRect(); return r.top >= 60 && r.bottom <= innerHeight * 0.6; };
  const els = kinds.flatMap(k => { const all = [...document.querySelectorAll(pick[k])];
      return k === 'name' ? all.filter(band).slice(0, 6) : all; })
    .filter(b => { const r = b.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  return els.map((b, i) => {
    b.dataset.probe = String(i);
    const r = b.getBoundingClientRect();
    const cy = r.top + r.height / 2;
    const narrow = width <= 420;
    const box = narrow ? {l: r.left, r: r.right, t: cy - Math.max(22, r.height / 2), b: cy + Math.max(22, r.height / 2)}
                       : {l: r.left, r: r.right, t: r.top, b: r.bottom};
    const cx = (box.l + box.r) / 2, l = box.l + 1, rr = box.r - 1, t = box.t + 1, bb = box.b - 1;
    return {i, text: b.innerText.replace(/\s+/g, ' ').trim().slice(0, 30),
      face: {w: +r.width.toFixed(1), h: +r.height.toFixed(1)},
      points: [[cx, cy, 'centre'], [cx, t, 'top'], [rr, cy, 'right'], [cx, bb, 'bottom'], [l, cy, 'left'],
               [l, t, 'top-left'], [rr, t, 'top-right'], [l, bb, 'bottom-left'], [rr, bb, 'bottom-right']]};
  });
}"""
HIT = r"""([i, x, y]) => {
  const b = document.querySelector(`[data-probe="${i}"]`);
  const el = document.elementFromPoint(x, y);
  return {ok: !!el && !!b && b.contains(el), hit: el ? String(el.className || el.tagName).split(' ')[0] : null};
}"""
PM_ARM = r"""() => { window.__pm = null; if (!window.__pmArmed) { window.__pmArmed = true;
  document.addEventListener('pointermove', e => { window.__pm = e.target; }, true); } }"""
PM_READ = r"""([i]) => { const b = document.querySelector(`[data-probe="${i}"]`); const t = window.__pm;
  return {ok: !!t && !!b && b.contains(t), hit: t ? String(t.className || t.tagName).split(' ')[0] : null}; }"""


# Round two (Codex Astra r1 finding 1): every selection host inside a scope —
# form fields and the CodeMirror lines — measured by its own ::selection pair,
# composited over its own ground: the selection against the ground, and the
# selected text against the selection.
HOSTS = r"""(scope) => {
  const C = window.__c;
  const root = document.querySelector(scope);
  if (!root) return null;
  return [...root.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=radio]), textarea, .cm-line')]
    .filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map(e => {
      const s = getComputedStyle(e, '::selection');
      const g = C.ground(e);
      const p = C.over(C.parse(s.backgroundColor) || {r: 0, g: 0, b: 0, a: 0}, g);
      const ink = C.over(C.parse(s.color), p);
      return {host: e.classList.contains('cm-line') ? 'codemirror' : e.tagName.toLowerCase(),
        cls: String(e.className).slice(0, 50), selection_bg: s.backgroundColor, selection_ink: s.color,
        ground: C.hex(g), selection_vs_ground: C.ratio(p, g), selected_text_vs_selection: C.ratio(ink, p)};
    });
}"""
MENUS = r"""() => [...document.querySelectorAll('[role=menu]')].filter(e => e.getBoundingClientRect().height > 0).map(e => {
  const r = e.getBoundingClientRect();
  return {label: e.getAttribute('aria-label'), left: Math.round(r.left), top: Math.round(r.top),
    right: Math.round(r.right), bottom: Math.round(r.bottom), vw: innerWidth, vh: innerHeight,
    in_view: r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight};
})"""

def _record(name: str, width: int, data: Any) -> None:
    (SHOTS / f"{name}-{width}.json").write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


class TestDeskDebtsGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _open(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
        ctx.add_init_script(COLOR_JS)
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        self._seed(page)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.locator("[data-testid=chair-floor-toggle]").click()
        try:
            page.locator(".desk-listmode").wait_for(timeout=6_000)
        except Exception:
            pass
        if not page.locator(".desk-listmode").count():
            self._palette(page, "List view")
            page.locator("[id='desk-palette-option-desk.toggle-view']").click()
        page.locator(".desk-listmode").wait_for(timeout=T)
        page.locator(".desk-listmode tbody tr", has_text="Ledger cutover plan").first.wait_for(timeout=T)
        page.wait_for_timeout(1200)
        return browser, page, errors

    def _seed(self, page: Any) -> None:
        """The grounding probe's objects (d2_probe.py.txt), and a real Attention:
        a GitHub proposal under the NEUTRAL mode waits `proposed` and is never
        executed; the projection counts it as needs_attention on the note."""
        zones = [_api(page, "POST", "/api/directories", {"name": n}, token=TOKEN)
                 for n in ("Payments", "Hiring", "Architecture reviews")]
        notes = [_api(page, "POST", "/api/notes", {"title": t, "body": t}, token=TOKEN) for t in NOTES]
        zid = (zones[0].get("directory") or zones[0])["id"]
        nid = (notes[0].get("note") or notes[0])["id"]
        _api(page, "PUT", f"/api/directories/{zid}/members/note:{nid}", {}, token=TOKEN)
        _api(page, "PUT", "/api/authority/control-mode", {"control_mode": "neutral"}, token=TOKEN)
        _api(page, "POST", "/api/desk/actuators/github/propose",
             {"text": "Check the ledger cutover plan", "repo": "example/payments", "source_ref": f"note:{nid}"},
             token=TOKEN)
        counts = _api(page, "GET", "/api/desk/projections?limit=50", token=TOKEN).get("subject_counts", {})
        assert counts.get(f"note:{nid}", {}).get("needs_attention") == 1, counts

    @staticmethod
    def _palette(page: Any, query: str) -> None:
        page.locator("[aria-controls=desk-tool-shelf]").click()
        page.locator("[aria-controls=desk-palette-listbox]").fill(query)

    @staticmethod
    def _facts(page: Any) -> dict[str, Any]:
        return page.evaluate(FACTS)

    def _pointer(self, page: Any, width: int, kinds: list[str]) -> list[dict[str, Any]]:
        page.evaluate(PM_ARM)
        out = []
        for probe in page.evaluate(POINTS, [width, kinds]):
            bad = []
            for x, y, where in probe["points"]:
                if not (0 <= x < width and 0 <= y < SIZES[width]):
                    bad.append((where, "off-screen"))
                    continue
                h = page.evaluate(HIT, [probe["i"], x, y])
                page.mouse.move(x, y)
                m = page.evaluate(PM_READ, [probe["i"]])
                if not (h["ok"] and m["ok"]):
                    bad.append((where, h["hit"], m["hit"]))
            out.append({"text": probe["text"], "face": probe["face"], "points": len(probe["points"]), "not_owned": bad})
        page.mouse.move(2, 60)
        return out

    def _row_menu(self, page: Any, width: int) -> None:
        """The canvas's board 3: an OBJECT row scrolled to sit just above the
        lowest free band (above the dock at 393, near the edge at 1440), then
        the row menu by a right-click on it."""
        height = SIZES[width]
        row = page.locator(".desk-listmode tbody tr.desk-sortable-table-row:has(.desk-list-mark)").nth(3)
        row.scroll_into_view_if_needed()
        target = height - (150 if width < 720 else 60)
        box = row.bounding_box()
        page.mouse.wheel(0, box["y"] + box["height"] - target)
        page.wait_for_timeout(500)
        box = row.bounding_box()
        page.mouse.click(box["x"] + 60, box["y"] + box["height"] / 2, button="right")
        page.locator("[role=menu]").wait_for(timeout=T)
        page.wait_for_timeout(600)
        page.mouse.move(2, 60)
        page.wait_for_timeout(200)

    # ── the fences ───────────────────────────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_selection_is_visible(self, width: int) -> None:
        """Q6: the selected name reads 3:1 or more against the field (red on
        main: 1.13:1), the selected text 4.5:1 or more; the zone name field
        on the list and the palette field."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._palette(page, "New Zone")
                page.locator("[id='desk-palette-option-desk.new-zone']").click()
                field = page.locator(".desk-listmode input.desk-zone-rename")
                field.wait_for(timeout=T)
                page.wait_for_timeout(400)
                zone = page.evaluate(SELECTION, ".desk-listmode input.desk-zone-rename")
                field.screenshot(path=str(SHOTS / f"selection-zone-field-{width}.png"))
                page.screenshot(path=str(SHOTS / f"selection-zone-{width}.png"))
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)
                self._palette(page, "Ledger cutover")
                page.wait_for_timeout(400)
                page.evaluate("document.querySelector('[aria-controls=desk-palette-listbox]').select()")
                page.wait_for_timeout(200)
                palette = page.evaluate(SELECTION, "[aria-controls=desk-palette-listbox]")
                page.screenshot(path=str(SHOTS / f"selection-palette-{width}.png"))
                _record("selection", width, {"zone": zone, "palette": palette})
                for where, s in (("zone field", zone), ("palette", palette)):
                    assert s and s["end"] > s["start"], (where, s)
                    assert s["selection_vs_field"] >= 3.0, (where, s)
                    assert s["selected_text_vs_selection"] >= 4.5, (where, s)
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_list_text_is_12px_and_readable(self, width: int) -> None:
        """No list text under 12 px (red on main: 51 / 33 nodes); every text
        4.5:1 on its composited ground, ATTN included (3.92:1 on main); the
        status says SHOWN for many and for one (red on main: SHOWNS)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                page.locator(".desk-listmode tbody tr", has_text="Ledger cutover plan").first.evaluate(
                    "e => e.scrollIntoView({block: 'center'})")
                page.wait_for_timeout(400)
                many = self._facts(page)
                page.screenshot(path=str(SHOTS / f"list-{width}.png"))
                page.evaluate("window.scrollTo(0, 0)")
                page.get_by_role("button", name="Payments zone").first.click()
                page.locator(".desk-list-census .btn", has_text="ALL").wait_for(timeout=T)
                page.wait_for_timeout(1200)
                one = self._facts(page)
                page.screenshot(path=str(SHOTS / f"one-shown-{width}.png"))
                _record("list-text", width, {"many": many, "one": one})
                for f in (many, one):
                    assert f["small_text_count"] == 0, f["small_text"]
                    assert f["min_text_ratio"] >= 4.5, f["text_styles"]
                assert many["attention_tokens"] and all(
                    t["px"] >= 12 and t["ratio"] >= 4.5 for t in many["attention_tokens"]), many["attention_tokens"]
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_status_says_shown(self, width: int) -> None:
        """The status says SHOWN for many and for one (red on main: SHOWNS)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                many = self._facts(page)["status"]
                page.get_by_role("button", name="Payments zone").first.click()
                page.locator(".desk-list-census .btn", has_text="ALL").wait_for(timeout=T)
                page.wait_for_timeout(1200)
                one = self._facts(page)["status"]
                _record("status", width, {"many": many, "one": one})
                n = many.split()[0]
                assert many == f"{n} SHOWN OF {n}" and int(n) > 1, many
                assert one == "1 SHOWN OF 1", one
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_every_kept_column_is_in_view(self, width: int) -> None:
        """Q7: at 393 Kind, Zone and Attention ride the fold line in the name
        Button and every header is on screen (red on main: three columns off
        the right edge); at 1440 the four columns stay (preservation). Every
        object row's Kind and Zone words are read in view at both widths; no
        page overflow, dived or not."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                f = self._facts(page)
                shot = page.screenshot(path=str(SHOTS / f"columns-{width}.png"))
                assert shot
                page.get_by_role("button", name="Payments zone").first.click()
                page.locator(".desk-list-census .btn", has_text="ALL").wait_for(timeout=T)
                page.wait_for_timeout(1200)
                dived = self._facts(page)
                _record("columns", width, {"list": f, "dived": dived})
                heads = " ".join(h["text"] for h in f["headers"])
                for word in ("NAME", "KIND", "ZONE", "ATTENTION"):
                    assert word in heads.upper(), f["headers"]
                assert all(h["in_view"] for h in f["headers"]), f["headers"]
                assert f["cells_past_right_edge"] == 0, f["cells_past_right_edge"]
                assert f["scroll_width"] == width and dived["scroll_width"] == width, (f["scroll_width"], dived["scroll_width"])
                assert f["row_words"], f
                kinds = [w for w in f["row_words"] if "NOTE" in w.upper()]
                assert len(kinds) >= len(NOTES), f["row_words"]
                assert any("PAYMENTS" in w.upper() for w in f["row_words"]), f["row_words"]
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)  # the real-pointer pass; 200 s on the macOS CI runner
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_sort_headers_are_the_library_button(self, width: int) -> None:
        """Every sort verb in the list header is the library Button (red on
        main: four raw <button>s); the Zone sort presses; every visible sort
        Button, six name Buttons (the fold line rides inside them at 393) and
        the census ALL verb own their nine points to a real pointer."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                f = self._facts(page)
                assert f["sort_verbs"] and all(v["library"] for v in f["sort_verbs"]), f["sort_verbs"]
                assert f["raw_buttons_in_list"] == [], f["raw_buttons_in_list"]
                page.locator(".desk-listmode thead button:visible", has_text="Zone").first.click()
                page.wait_for_timeout(500)
                pressed = self._facts(page)["sort_verbs"]
                page.screenshot(path=str(SHOTS / f"sorted-by-zone-{width}.png"))
                zone = [v for v in pressed if v["visible"] and v["text"].upper().startswith("ZONE")]
                assert zone and zone[0]["pressed"] == "true" and "↑" in zone[0]["text"], pressed
                owned = self._pointer(page, width, ["sort", "name"])
                page.get_by_role("button", name="Payments zone").first.click()
                page.locator(".desk-list-census .btn", has_text="ALL").wait_for(timeout=T)
                page.wait_for_timeout(1200)
                owned += self._pointer(page, width, ["census"])
                _record("sort-buttons", width, {"verbs": pressed, "pointer": owned})
                assert len(owned) >= 8, owned  # 4 sort, 3+ name Buttons, ALL
                assert all(not p["not_owned"] for p in owned), owned
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)  # the real-pointer pass; 200 s on the macOS CI runner
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_row_menu_keeps_itself_in_view(self, width: int) -> None:
        """The row menu on a row near the bottom edge: its last entry ends
        inside the viewport (red on main at 393: cut 15 px; in view at 1440);
        at 393 every row is 44 px; every row owns its nine points; its text is
        12 px or more."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._row_menu(page, width)
                f = self._facts(page)
                page.screenshot(path=str(SHOTS / f"row-menu-bottom-{width}.png"))
                owned = self._pointer(page, width, ["menu"])
                _record("row-menu", width, {"facts": f, "pointer": owned})
                last = f["menu_last"]
                assert last and last["text"].startswith("Delete"), f["menu_rows"]
                assert last["bottom"] <= SIZES[width] and min(r["top"] for r in f["menu_rows"]) >= 0, f["menu_rows"]
                if width <= 420:
                    assert all(r["h"] >= 44 for r in f["menu_rows"]), f["menu_rows"]
                assert all(not p["not_owned"] for p in owned), owned
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_open_row_menu_text_is_12px(self, width: int) -> None:
        """The 12 px floor holds in the open row menu too (it portals outside
        the list): the quiet reason and the keycap wells (10 px on main)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._row_menu(page, width)
                f = self._facts(page)
                _record("row-menu-text", width, {"small_text": f["small_text"], "text_styles": f["text_styles"]})
                assert f["small_text_count"] == 0, f["small_text"]
                assert f["min_text_ratio"] >= 4.5, f["text_styles"]
                assert not errors, errors
            finally:
                browser.close()

    # ── round two (Codex Astra r1, checks/story-04-built-astra-r1.md) ──────

    def _open_note_editor(self, page: Any) -> Any:
        row = page.locator(".desk-listmode tbody tr", has_text="Ledger cutover plan").first
        row.scroll_into_view_if_needed()
        row.click(button="right")
        page.get_by_role("menuitem", name="Edit", exact=True).click()
        editor = page.locator(".cm-content").first
        editor.wait_for(timeout=T)
        return editor

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_editor_selection_is_readable(self, width: int) -> None:
        """Finding 1: selected note text in the CodeMirror editor reads 4.5:1
        or more on a selection that reads 3:1 against the editor (red at
        f58cb5b0: 1.33:1, the tint ground under the page ink). The census
        covers every selection host in the open editor window: the title
        field, the body lines, the tags field."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                editor = self._open_note_editor(page)
                editor.fill("Review the ledger cutover plan with Priya.")
                editor.click()
                page.keyboard.press("ControlOrMeta+a")
                # The shot before the editor's AI bar opens over a selection
                # (EditorAIBar; at 393 it covers the body: BACKLOG
                # "PHILO-9-04 follow-ups"), and one after it.
                page.wait_for_timeout(60)
                page.screenshot(path=str(SHOTS / f"editor-selected-{width}.png"))
                page.wait_for_timeout(300)
                page.screenshot(path=str(SHOTS / f"editor-selected-aibar-{width}.png"))
                selected = page.evaluate("window.getSelection().toString()")
                window = page.evaluate(HOSTS, ".desk-window:has(.cm-content)") or []
                _record("editor-selection", width, {"selected": selected, "hosts": window})
                assert "ledger cutover" in selected, selected
                cm = [h for h in window if h["host"] == "codemirror"]
                assert cm, window
                for h in window:
                    assert h["selected_text_vs_selection"] >= 4.5, h
                    assert h["selection_vs_ground"] >= 3.0, h
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_thread_composer_selection_is_readable(self, width: int) -> None:
        """Finding 1's census: the thread composer's textarea (the draft
        field; row menu > Continue in thread) takes the same pair."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                row = page.locator(".desk-listmode tbody tr", has_text="Ledger cutover plan").first
                row.scroll_into_view_if_needed()
                row.click(button="right")
                page.get_by_role("menuitem", name="Continue in thread", exact=True).click()
                area = page.locator("textarea").first
                area.wait_for(timeout=T)
                area.fill("Ask Priya about the cutover date")
                area.evaluate("e => { e.focus(); e.select(); }")
                page.wait_for_timeout(300)
                hosts = [h for h in page.evaluate(HOSTS, "body") if h["host"] == "textarea"]
                page.screenshot(path=str(SHOTS / f"composer-selected-{width}.png"))
                _record("composer-selection", width, {"hosts": hosts})
                assert hosts, "no textarea measured"
                for h in hosts:
                    assert h["selected_text_vs_selection"] >= 4.5, h
                    assert h["selection_vs_ground"] >= 3.0, h
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    # The spatial Floor plus a nine-point real-pointer pass over every submenu
    # row outlasted the suite's 300 s bound on the macOS CI runner (PR #683 run
    # 36387708744: the other fences there took up to 200 s each).
    @pytest.mark.timeout(900)
    def test_the_launch_submenu_keeps_itself_in_view(self) -> None:
        """Finding 2 (inherited on main): the Floor menu opened near the
        bottom-right corner at 1440, then Launch; both panels end inside the
        viewport (main: the Desk menu to 1454 x 906, the Launch submenu to
        1474 x 1034). 1440 only: at the narrow desk the submenu replaces its
        panel (DeskMenu.tsx), which the row-menu fence covers."""
        from playwright.sync_api import sync_playwright

        width = 1440
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._palette(page, "Spatial view")
                page.locator("[id='desk-palette-option-desk.toggle-view']").click()
                page.locator(".desk-world").wait_for(timeout=T)
                page.wait_for_timeout(3000)
                page.mouse.click(1422, 650, button="right")
                page.wait_for_timeout(400)
                if not page.get_by_role("menuitem", name="Launch", exact=False).count():
                    page.mouse.click(1400, 620, button="right")
                    page.wait_for_timeout(500)
                page.get_by_role("menuitem", name="Launch", exact=False).first.hover()
                page.locator("[role=menu][aria-label='Launch submenu']").wait_for(timeout=T)
                page.wait_for_timeout(400)
                menus = page.evaluate(MENUS)
                page.screenshot(path=str(SHOTS / f"launch-submenu-{width}.png"))
                owned = self._pointer(page, width, ["submenu"])
                _record("launch-submenu", width, {"menus": menus, "pointer": owned})
                assert owned and all(not p["not_owned"] for p in owned), owned
                assert any(m["label"] == "Launch submenu" for m in menus), menus
                assert all(m["in_view"] for m in menus), menus
                sub = next(m for m in menus if m["label"] == "Launch submenu")
                parent = next(m for m in menus if m["label"] != "Launch submenu")
                assert sub["right"] <= parent["left"] or sub["left"] >= parent["right"], (sub, parent)
                assert not errors, errors
            finally:
                browser.close()
