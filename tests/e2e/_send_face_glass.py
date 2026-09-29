"""PHILO-10-04: the shared glass machinery for the Send face fences.

Ported from the ratified canvas harness
(pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/
harness/shoot.py): the rendered facts of a window, the on-screen law for each
board's named elements, the nine-point pointer pass (elementFromPoint AND a
real pointer move, the painted face at 1440 and the 44 x 44 target at 393),
and the byte fence with the menu-bar clock masked. The touched face carries
``data-send``.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

FACTS = r"""(anchorSel) => {
  const anchor = document.querySelector(anchorSel);
  const win = anchor ? anchor.closest('.desk-window') : null;
  if (!win) return {window: false};
  const GLYPH = /^[●○◆▸▾✓✗⚠—↻ℹ«»·▤›×\s]+$/;
  const small = {touched: [], inherited: []};
  const walker = document.createTreeWalker(win, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const t = n.textContent.trim();
    if (!t || GLYPH.test(t)) continue;
    const el = n.parentElement;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (!r.width || !r.height || cs.visibility === 'hidden' || cs.display === 'none' || el.closest('.sr-only')) continue;
    const fs = parseFloat(cs.fontSize);
    if (fs < 12) (el.closest('[data-send]') ? small.touched : small.inherited).push({text: t.slice(0, 40), fs, cls: String(el.className).slice(0, 60)});
  }
  const raw = [...win.querySelectorAll('button')].filter((b) => !String(b.className).includes('btn') && b.getBoundingClientRect().width);
  const rawIn = (p) => raw.filter((b) => !!b.closest('[data-send]') === p).map((b) => (b.innerText || b.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 30));
  const body = win.querySelector('.desk-surface-body') || anchor;
  const text = (sel) => [...win.querySelectorAll(sel)].filter((e) => e.getBoundingClientRect().height > 0).map((e) => e.innerText.replace(/\s+/g, ' ').trim());
  const head = (sel) => { const s = win.querySelector(sel); return s ? s.innerText.replace(/\s+/g, ' ').trim() : null; };
  return {
    window: true,
    destinations: text('[data-testid=destination-row], [data-testid=dest-row]'),
    prepared: text('[data-testid=prepared-row]'),
    prepared_open: text('[data-testid=prepared-open]').length,
    prepared_results: text('[data-testid=prepared-result]'),
    preview_fields: [...win.querySelectorAll('[data-testid=send-preview-field]')].map((e) => e.innerText.replace(/\s+/g, ' ').trim()),
    preview_has_raw: /[{}]|<\/?(p|h2|ul|li)>/.test(text('[data-testid=send-preview-body]').join(' ')),
    send_verbs: [...win.querySelectorAll('[data-testid=send-verb], [data-testid=send-retry], [data-testid=prepared-send], [data-testid=prepared-retry]')]
      .map((b) => ({text: b.innerText.trim(), disabled: b.disabled || b.getAttribute('aria-disabled') === 'true', busy: b.getAttribute('aria-busy') === 'true'})),
    receipts: [...win.querySelectorAll('[data-receipt=latest], [data-testid=send-refused], [data-testid=send-lost]')]
      .map((e) => ({text: e.innerText.replace(/\s+/g, ' ').trim(), state: e.dataset.state || e.dataset.testid, code: e.dataset.code || null})),
    last_chips: text('[data-testid^=send-last-]'),
    send_head: head('[data-send=well] .surface-section-head h3, [data-send=well] h3'),
    history_head: head('[data-send=history] .surface-section-head h3, [data-send=history] h3'),
    history: text('[data-testid=delivery-row]'),
    history_outcomes: [...win.querySelectorAll('[data-testid=delivery-row] [data-outcome]')].map((e) => e.dataset.outcome),
    list_rows: text('[data-testid=update-list-item]'),
    list_chips: text('[data-testid=update-prepared-chip], [data-testid=update-unknown-chip], [data-testid=update-delivered-chip]'),
    dest_head: head('[data-send=destinations] .gadget-group-label'),
    dest_parked: text('[data-testid=dest-parked-row]'),
    egress_chips: [...win.querySelectorAll('[data-send] .gadget-chip-egress')].map((e) => `${e.innerText.trim()}:${e.dataset.scope || ''}`),
    send_well_present: !!win.querySelector('[data-testid=send-well]'),
    words_delivered_word: /\bDELIVERED\s+[×\d]/.test(win.innerText),
    modal: !!document.querySelector('[role=dialog][aria-modal=true], .modal, dialog[open]'),
    small_text: small,
    raw_buttons: {touched: rawIn(true), inherited: rawIn(false)},
    h_overflow: document.documentElement.scrollWidth > window.innerWidth,
    body_overflow_x: body ? body.scrollWidth > body.clientWidth + 1 : null,
  };
}"""

CONTROLS = r"""(anchorSel) => {
  const anchor = document.querySelector(anchorSel);
  const win = anchor ? anchor.closest('.desk-window') : null;
  if (!win) return [];
  document.querySelectorAll('[data-probe]').forEach((e) => e.removeAttribute('data-probe'));
  window.__scrollSnap = [...document.querySelectorAll('*')].filter((e) => e.scrollTop || e.scrollLeft).map((e) => [e, e.scrollTop, e.scrollLeft]);
  window.__pm = null;
  if (!window.__pmHooked) { document.addEventListener('pointermove', (e) => { window.__pm = e.target; }, true); window.__pmHooked = true; }
  const btns = [...win.querySelectorAll('[data-send] .btn, [data-send] .surface-ledger-line[aria-expanded], [data-send] select, [data-send] input:not([type=hidden]):not([type=checkbox]), [data-send] label.gadget-check-token')]
    .filter((b) => b.getBoundingClientRect().width);
  return btns.map((b, i) => {
    b.dataset.probe = String(i);
    return {i, text: (b.innerText || b.getAttribute('aria-label') || b.value || '').trim().slice(0, 30),
      kind: b.matches('.surface-ledger-line') ? 'row' : b.tagName.toLowerCase()};
  });
}"""

POINTS9 = r"""([i, width]) => {
  const b = document.querySelector(`[data-probe="${i}"]`);
  b.scrollIntoView({block: 'center', inline: 'nearest'});
  const r = b.getBoundingClientRect();
  const cy = r.top + r.height / 2, cx = r.left + r.width / 2;
  const w = width <= 420 ? Math.max(44, r.width) : r.width, h = width <= 420 ? Math.max(44, r.height) : r.height;
  const L = cx - w / 2 + 1, R = cx + w / 2 - 1, T = cy - h / 2 + 1, B = cy + h / 2 - 1;
  return {face: [+r.width.toFixed(1), +r.height.toFixed(1)], target: [+w.toFixed(1), +h.toFixed(1)],
    points: [[cx, cy], [cx, T], [R, cy], [cx, B], [L, cy], [L, T], [R, T], [L, B], [R, B]]};
}"""

HIT = r"""([i, x, y]) => {
  const b = document.querySelector(`[data-probe="${i}"]`);
  const el = document.elementFromPoint(x, y);
  return {efp: !!el && !!b && b.contains(el), hit: el ? String(typeof el.className === 'string' ? el.className : el.tagName).split(' ')[0] : null};
}"""
PM_OWNED = r"""([i]) => { const b = document.querySelector(`[data-probe="${i}"]`); return !!window.__pm && !!b && b.contains(window.__pm); }"""
RESTORE = r"""() => { for (const [e, t, l] of (window.__scrollSnap || []).reverse()) { e.scrollTop = t; e.scrollLeft = l; } }"""
NAMES = ["centre", "top", "right", "bottom", "left", "top-left", "top-right", "bottom-left", "bottom-right"]

# The on-screen law: each board's NAMED elements are in the viewport, inside
# every clipping ancestor, and on top at their centre and two inner corners.
VISIBLE = r"""(sels) => sels.map((sel) => {
  const els = [...document.querySelectorAll(sel)].filter((e) => { const r = e.getBoundingClientRect(); return r.width && r.height; });
  if (!els.length) return {sel, ok: false, why: 'absent'};
  const e = els[0]; const r = e.getBoundingClientRect();
  let top = 0, left = 0, bottom = innerHeight, right = innerWidth;
  for (let a = e.parentElement; a; a = a.parentElement) {
    const cs = getComputedStyle(a);
    if (/(auto|scroll|hidden|clip)/.test(cs.overflowY + ' ' + cs.overflowX)) {
      const ar = a.getBoundingClientRect();
      top = Math.max(top, ar.top); bottom = Math.min(bottom, ar.bottom); left = Math.max(left, ar.left); right = Math.min(right, ar.right);
    }
  }
  const inside = r.top >= top - 1 && r.bottom <= bottom + 1 && r.left >= left - 1 && r.right <= right + 1;
  const pts = [[r.left + r.width / 2, r.top + r.height / 2], [r.left + 2, r.top + 2], [r.right - 2, r.bottom - 2]];
  const hit = pts.every(([x, y]) => { const h = document.elementFromPoint(x, y); return !!h && (e.contains(h) || h.contains(e)); });
  return {sel, ok: inside && hit, why: inside ? (hit ? '' : 'covered') : 'clipped', text: (e.innerText || e.value || '').replace(/\s+/g, ' ').trim().slice(0, 60)};
})"""

SEAT = r"""(sel) => { const el = document.querySelector(sel); if (!el) return;
  el.scrollIntoView({block: 'start'});
  let s = el.parentElement; while (s && !(s.scrollHeight > s.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(s).overflowY))) s = s.parentElement;
  if (s) s.scrollTop = Math.max(0, s.scrollTop - 120); }"""


def pointer_pass(page: Any, width: int, anchor: str) -> list[dict[str, Any]]:
    """Every touched control, nine points each, elementFromPoint AND a real pointer move."""
    out = []

    def probe(i: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        geo = page.evaluate(POINTS9, [i, width])
        pts = []
        for name, (x, y) in zip(NAMES, geo["points"]):
            hit = page.evaluate(HIT, [i, x, y])
            page.mouse.move(x, y)
            pts.append({"at": name, "efp": hit["efp"], "pointer": page.evaluate(PM_OWNED, [i]), "hit": hit["hit"]})
        return geo, pts

    for c in page.evaluate(CONTROLS, anchor):
        geo, pts = probe(c["i"])
        retried = None
        if not all(p["efp"] and p["pointer"] for p in pts):
            # A control can change size under the probe (ConfirmVerb disarms after 3 s).
            retried = {"face_before": geo["face"], "failed_before": [p for p in pts if not (p["efp"] and p["pointer"])]}
            geo, pts = probe(c["i"])
        out.append({"text": c["text"], "kind": c["kind"], "face": geo["face"], "target": geo["target"],
                    "owned": all(p["efp"] and p["pointer"] for p in pts),
                    "failed_points": [p for p in pts if not (p["efp"] and p["pointer"])], "retried": retried})
    page.mouse.move(1, 1)
    page.evaluate(RESTORE)
    page.wait_for_timeout(100)
    return out


class Boards:
    """One test's boards at one width: shots, facts, the on-screen law, the pointer
    pass and the byte fence (the menu-bar clock masked)."""

    def __init__(self, shots: Path, width: int, anchor: str) -> None:
        self.shots, self.width, self.anchor = shots, width, anchor
        self.facts: dict[str, Any] = {}
        self.hidden: list[str] = []
        self.shas: dict[str, str] = {}

    def seat(self, page: Any, sel: str) -> None:
        if sel.startswith("CENTER:"):
            page.evaluate("(s) => { const el = document.querySelector(s); if (el) el.scrollIntoView({block: 'center'}); }", sel[7:])
        else:
            page.evaluate(SEAT, sel)
        page.wait_for_timeout(250)

    def shoot(self, page: Any, board: str, named: list[str], *, seat: str | None = "FIRST",
              anchor: str | None = None, pointer: bool = True) -> dict[str, Any]:
        anchor = anchor or self.anchor
        target = named[0] if seat == "FIRST" else seat
        if target:
            self.seat(page, target)
        page.mouse.move(1, 1)
        page.wait_for_timeout(250)
        key = f"{board}-{self.width}"
        vis = page.evaluate(VISIBLE, named)
        page.screenshot(path=str(self.shots / f"{key}.png"))
        sha = hashlib.sha256(page.screenshot(mask=[page.locator(".desk-clock")], mask_color="#000000")).hexdigest()
        f = page.evaluate(FACTS, anchor)
        f["named"] = vis
        f["masked_sha"] = sha
        if pointer:
            f["pointer"] = pointer_pass(page, self.width, anchor)
            if target:
                self.seat(page, target)
        self.facts[key] = f
        self.hidden += [f"{key}: {v}" for v in vis if not v["ok"]]
        if sha in self.shas.values():
            twin = next(k for k, v in self.shas.items() if v == sha)
            self.hidden.append(f"{key}: identical to {twin} with the clock masked")
        self.shas[key] = sha
        return f

    def write(self, name: str, extra: dict[str, Any] | None = None) -> None:
        data = {"boards": self.facts, **(extra or {})}
        (self.shots / f"{name}-{self.width}.json").write_text(
            json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, default=str) + "\n")

    def assert_clean(self) -> None:
        """The laws on every board: named elements on screen, no identical shots,
        no text under 12 px, no raw button, no modal, no overflow, every touched
        control owns its nine points."""
        assert not self.hidden, self.hidden
        for key, f in self.facts.items():
            assert f["window"], key
            assert not f["small_text"]["touched"] and not f["small_text"]["inherited"], (key, f["small_text"])
            assert f["raw_buttons"]["touched"] == [], (key, f["raw_buttons"])
            assert not f["modal"], key
            assert not f["h_overflow"] and not f["body_overflow_x"], key
            assert not f["preview_has_raw"], key
            bad = [p for p in f.get("pointer", []) if not p["owned"]]
            assert not bad, (key, bad)
