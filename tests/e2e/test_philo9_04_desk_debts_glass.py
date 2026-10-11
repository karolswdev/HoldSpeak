"""PHILO-9-04 -- selection contrast in the note editor and the thread
composer, fenced AS RENDERED through the real hub on an isolated HOME at
1440x900 and 393x852.

Re-homed by PHILO-17 (owner 2026-10-10, "Yes, everything must become one
desk"): the desk-wide list is parked, so both fences enter from the note's
icon on the Screen (its object menu: Edit, Continue in thread). The list's
own fences (selection token, 12 px text, columns, row menu, launch submenu)
are parked with it: tests/e2e/_parked/test_philo9_04_desk_debts_glass.py.
The assertions are unchanged.
"""

from __future__ import annotations

import re

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

# The canvas harness's colour helpers (shoot.py COLOR_JS).
COLOR_JS = r"""
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

ICON = ".desk-screen .desk-icon[aria-label^='Ledger cutover plan']"

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
        # PHILO-17: the one desk. The note's icon is on the Screen.
        page.locator(f"{ICON}").first.wait_for(timeout=T)
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

    def _open_note_editor(self, page: Any) -> Any:
        # PHILO-17: the note's desk icon and its object menu (the Screen).
        icon = page.locator(ICON).first
        icon.scroll_into_view_if_needed()
        icon.click(button="right")
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
                icon = page.locator(ICON).first
                icon.scroll_into_view_if_needed()
                icon.click(button="right")
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
