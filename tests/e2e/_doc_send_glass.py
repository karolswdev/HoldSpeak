"""PHILO-11-05a: the glass machinery for the SEND well on the document faces.

Ported from the ratified canvas rig (phase-11 story 03,
assets/story-03-canvas/harness/shoot.py) with the proposal marker
``[data-p11]`` replaced by the species' own ``[data-send]``: the rendered
facts of the frame (a desk window, or the Chair), the on-screen law for each
board's named elements, the nine-point pointer pass (elementFromPoint AND a
real pointer move; the painted face at 1440, the 44 x 44 target at 393) with
a control under the host's own sticky bar reached by ORDINARY scrolling (the
mouse wheel), and the byte fence with the menu-bar clock masked.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

STALE = ["OLD VERSION", "STALE", "OUTDATED", "PREVIOUS VERSION", "NEWER VERSION", "CHANGED SINCE"]

FRAME = "(a) => a ? (a.closest('.desk-window') || a.closest('.chair') || document.body) : null"

FACTS = (r"""(anchorSel) => {
  const frame = %FRAME%;
  const win = frame(document.querySelector(anchorSel));
  if (!win) return {window: false};
  const GLYPH = /^[●○◆▸▾✓✗⚠—↻ℹ«»·▤›×\s]+$/;
  const small = {touched: [], inherited: []};
  const walker = document.createTreeWalker(win, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const t = n.textContent.trim();
    if (!t || GLYPH.test(t)) continue;
    const el = n.parentElement; const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    if (!r.width || !r.height || cs.visibility === 'hidden' || cs.display === 'none' || el.closest('.sr-only')) continue;
    if (parseFloat(cs.fontSize) < 12) (el.closest('[data-send]') ? small.touched : small.inherited).push({text: t.slice(0, 40), fs: parseFloat(cs.fontSize)});
  }
  const raw = [...win.querySelectorAll('button')].filter((b) => !String(b.className).includes('btn') && b.getBoundingClientRect().width);
  const rawIn = (p) => raw.filter((b) => !!b.closest('[data-send]') === p).map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 30));
  const wells = [...win.querySelectorAll('[data-send=well]')];
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const text = (sel) => [...win.querySelectorAll(sel)].filter(vis).map((e) => e.innerText.replace(/\s+/g, ' ').trim());
  const wellText = wells.map((w) => w.innerText).join('\n') + '\n' + text('[data-send=history]').join('\n');
  const body = win.querySelector('.desk-surface-body') || win;
  return {
    window: true,
    window_width: Math.round(win.getBoundingClientRect().width),
    wells: wells.map((w) => w.dataset.doc),
    destinations: text('[data-send=well] [data-testid=destination-row]'),
    prepared: text('[data-send=well] [data-testid=prepared-row], [data-send=well] [data-testid=prepared-result]'),
    // A field row is display: contents (the dl grid): read it without the box test.
    preview_fields: [...win.querySelectorAll('[data-send=well] [data-testid=send-preview-field]')].map((e) => e.innerText.replace(/\s+/g, ' ').trim()),
    receipts: [...win.querySelectorAll('[data-send=well] [data-receipt=latest], [data-send=well] [data-testid=send-refused], [data-send=well] [data-testid=send-lost]')]
      .filter(vis).map((e) => ({text: e.innerText.replace(/\s+/g, ' ').trim(), state: e.dataset.state || e.dataset.testid, code: e.dataset.code || null})),
    last_chips: text('[data-send=well] [data-testid^=send-last-]'),
    send_verbs: [...win.querySelectorAll('[data-send=well] [data-testid=send-verb], [data-send=well] [data-testid=prepared-send]')].filter(vis)
      .map((b) => ({text: b.innerText.trim(), disabled: b.disabled || b.getAttribute('aria-disabled') === 'true'})),
    send_head: (() => { const s = win.querySelector('[data-send=well] .surface-section-head h3'); return s ? s.innerText.trim() : null; })(),
    history_head: (() => { const s = win.querySelector('[data-send=history] .surface-section-head h3'); return s ? s.innerText.trim() : null; })(),
    history: text('[data-send=history] [data-testid=history-row]'),
    egress_chips: [...win.querySelectorAll('[data-send] .gadget-chip-egress')].filter(vis).map((e) => e.innerText.trim()),
    mark_delivered_in_new_kind: wells.filter((w) => !String(w.dataset.doc).startsWith('project_update:'))
      .some((w) => /Mark delivered/.test((w.parentElement || w).innerText)),
    stale_words: %STALE%.filter((wd) => wellText.toUpperCase().includes(wd)),
    no_answer_shown: /NO ANSWER/.test(wellText),
    row_grammar: [...win.querySelectorAll('[data-send=well] .surface-ledger-line, [data-send=history] .surface-ledger-line')]
      .filter(vis).map((l) => {
        const lead = l.querySelector(':scope > .surface-ledger-lead, :scope > .surface-ledger-time'),
          prim = l.querySelector(':scope > .surface-ledger-primary'), cells = l.querySelector('.send-cells');
        if (!lead || !prim || !cells) return 'missing';
        const a = lead.getBoundingClientRect(), b = prim.getBoundingClientRect(), c = cells.getBoundingClientRect();
        return (Math.abs(a.top - b.top) < 14 && c.top >= b.bottom - 2 && Math.abs(c.left - b.left) < 2) ? 'ok' : 'off';
      }),
    preview_fonts: [...win.querySelectorAll('[data-send=well] .send-preview-body p, [data-send=well] .send-preview-body li')]
      .filter(vis).slice(0, 8).map((e) => getComputedStyle(e).fontFamily.split(',')[0].replace(/"/g, '').trim()),
    room_open_verbs: [...document.querySelectorAll('[data-testid=decision-row]')].filter(vis)
      .map((r) => [...r.querySelectorAll('.btn')].filter((b) => b.innerText.trim() === 'Open').length),
    modal: !!document.querySelector('[role=dialog][aria-modal=true], .modal, dialog[open]'),
    small_text: small,
    raw_buttons: {touched: rawIn(true), inherited: rawIn(false)},
    h_overflow: document.documentElement.scrollWidth > window.innerWidth,
    body_overflow_x: body ? body.scrollWidth > body.clientWidth + 1 : null,
  };
}""").replace("%FRAME%", FRAME).replace("%STALE%", json.dumps(STALE))

# The on-screen law: each NAMED element is in the viewport, inside every
# clipping ancestor, and on top at its centre and two inner corners. A block
# taller than its scroller counts by its first 40 px.
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
  const band = Math.min(r.height, 40);
  const inside = r.top >= top - 1 && r.top + band <= bottom + 1 && r.left >= left - 1 && r.right <= right + 1
    && (r.height <= 40 || r.bottom <= bottom + 1 || r.height > bottom - top);
  const yb = r.top + band / 2;
  const pts = [[r.left + r.width / 2, yb], [r.left + 2, r.top + 2], [r.right - 2, r.top + band - 2]];
  const hit = pts.every(([x, y]) => { const h = document.elementFromPoint(x, y); return !!h && (e.contains(h) || h.contains(e)); });
  return {sel, ok: inside && hit, why: inside ? (hit ? '' : 'covered') : 'clipped', text: (e.innerText || e.value || '').replace(/\s+/g, ' ').trim().slice(0, 80)};
})"""

CONTROLS = (r"""(anchorSel) => {
  const frame = %FRAME%;
  const win = frame(document.querySelector(anchorSel));
  if (!win) return [];
  document.querySelectorAll('[data-probe]').forEach((e) => e.removeAttribute('data-probe'));
  window.__scrollSnap = [...document.querySelectorAll('*')].filter((e) => e.scrollTop || e.scrollLeft || e.scrollHeight > e.clientHeight + 1).map((e) => [e, e.scrollTop, e.scrollLeft]);
  window.__pm = null;
  if (!window.__pmHooked) { document.addEventListener('pointermove', (e) => { window.__pm = e.target; }, true); window.__pmHooked = true; }
  const btns = [...win.querySelectorAll('[data-send] .btn, [data-send] .surface-ledger-line[aria-expanded], [data-send] select, [data-send] input:not([type=hidden]):not([type=checkbox])')]
    .filter((b) => { const r = b.getBoundingClientRect();
      return r.width && r.height > 1 && r.bottom > 0 && r.top < innerHeight && (!b.checkVisibility || b.checkVisibility({checkOpacity: true, checkVisibilityCSS: true})); });
  return btns.map((b, i) => { b.dataset.probe = String(i); return {i, text: (b.innerText || b.getAttribute('aria-label') || b.value || '').trim().slice(0, 30)}; });
}""").replace("%FRAME%", FRAME)

POINTS9 = r"""([i, width]) => {
  const b = document.querySelector(`[data-probe="${i}"]`);
  const r = b.getBoundingClientRect();
  const cy = r.top + r.height / 2, cx = r.left + r.width / 2;
  const w = width <= 420 ? Math.max(44, r.width) : r.width, h = width <= 420 ? Math.max(44, r.height) : r.height;
  const L = cx - w / 2 + 1, R = cx + w / 2 - 1, T = cy - h / 2 + 1, B = cy + h / 2 - 1;
  let top = 0, left = 0, bottom = innerHeight, right = innerWidth;
  for (let a = b.parentElement; a; a = a.parentElement) {
    const cs = getComputedStyle(a);
    if (/(auto|scroll|hidden|clip)/.test(cs.overflowY + ' ' + cs.overflowX)) {
      const ar = a.getBoundingClientRect();
      top = Math.max(top, ar.top); bottom = Math.min(bottom, ar.bottom); left = Math.max(left, ar.left); right = Math.min(right, ar.right);
    }
  }
  const inview = r.top >= top - 1 && r.bottom <= bottom + 1 && r.left >= left - 1 && r.right <= right + 1;
  return {face: [+r.width.toFixed(1), +r.height.toFixed(1)], target: [+w.toFixed(1), +h.toFixed(1)],
    points: [[cx, cy], [cx, T], [R, cy], [cx, B], [L, cy], [L, T], [R, T], [L, B], [R, B]], inview};
}"""
HIT = r"""([i, x, y]) => { const b = document.querySelector(`[data-probe="${i}"]`); const el = document.elementFromPoint(x, y);
  let bar = false;
  for (let a = el; a && !bar; a = a.parentElement) { const p = getComputedStyle(a).position; if ((p === 'sticky' || p === 'fixed') && !a.closest('[data-send]')) bar = true; }
  return {own: !!el && b.contains(el), bar: !!el && !b.contains(el) && bar}; }"""
PM_OWNED = r"""([i]) => { const b = document.querySelector(`[data-probe="${i}"]`); return !!window.__pm && b.contains(window.__pm); }"""
RESTORE = r"""() => { for (const [e, t, l] of [...(window.__scrollSnap || [])].reverse()) { e.scrollTop = t; e.scrollLeft = l; } }"""

WHEEL_POINT = r"""(i) => {
  const b = document.querySelector(`[data-probe="${i}"]`);
  const scroller = (e) => { for (let a = e; a; a = a.parentElement) { const cs = getComputedStyle(a);
    if (a.scrollHeight > a.clientHeight + 1 && /(auto|scroll)/.test(cs.overflowY)) return a; } return document.scrollingElement; };
  // The OUTERMOST scroller of the control (the Chair, the window body): the one that
  // moves it out from under the host's bar. A nested preview scroller does not.
  let own = null;
  for (let a = b.parentElement; a; a = a.parentElement) { const cs = getComputedStyle(a);
    if (a.scrollHeight > a.clientHeight + 1 && /(auto|scroll)/.test(cs.overflowY)) own = a; }
  own = own || document.scrollingElement;
  const xs = [innerWidth / 2, 24, innerWidth - 24];
  for (let d = 0; d < innerHeight / 2; d += 20) for (const y of [innerHeight / 2 - d, innerHeight / 2 + d]) for (const x of xs) {
    const e = document.elementFromPoint(x, y);
    if (e && scroller(e) === own) return [x, y];
  }
  return [innerWidth / 2, innerHeight / 2];
}"""

SEAT = r"""([sel, block]) => { const el = document.querySelector(sel); if (!el) return;
  el.scrollIntoView({block});
  if (block !== 'start') return;
  let s = el.parentElement; while (s && !(s.scrollHeight > s.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(s).overflowY))) s = s.parentElement;
  if (s) s.scrollTop = Math.max(0, s.scrollTop - 48); else window.scrollBy(0, -48); }"""


def pointer_pass(page: Any, width: int, anchor: str) -> dict[str, Any]:
    """Every well control the shot shows, nine points each. A control under the
    HOST's own sticky bar (the Chair's capture bar) is reached by ordinary
    scrolling -- the mouse wheel over it -- and probed again; not reached is a miss."""
    vw, vh = page.viewport_size["width"], page.viewport_size["height"]

    def probe(i: int) -> tuple[dict[str, Any], int, list[Any], int]:
        geo = page.evaluate(POINTS9, [i, width])
        bad, where, under = 0, [], 0
        for x, y in geo["points"]:
            if not (0 <= x < vw and 0 <= y < vh):
                bad += 1
                continue
            h = page.evaluate(HIT, [i, x, y])
            under += 1 if h["bar"] else 0
            page.mouse.move(x, y)
            pm = page.evaluate(PM_OWNED, [i])
            if not (h["own"] and pm):
                bad += 1
                where.append([round(x), round(y), page.evaluate("([x, y]) => { const e = document.elementFromPoint(x, y); return e ? (String(e.className || e.tagName).slice(0, 40) + '|' + (e.innerText || '').slice(0, 20)) : null; }", [x, y])])
        return geo, bad, where, under

    owned: list[dict[str, Any]] = []
    missed: list[dict[str, Any]] = []
    reached: list[dict[str, Any]] = []
    for c in page.evaluate(CONTROLS, anchor):
        geo, bad, where, under = probe(c["i"])
        if not geo["inview"]:
            continue
        if bad and under:
            steps, bad2, where2 = 0, bad, where
            for steps in range(1, 16):
                cy = page.evaluate("(i) => { const r = document.querySelector(`[data-probe=\"${i}\"]`).getBoundingClientRect(); return r.top + r.height / 2; }", c["i"])
                # The wheel where he scrolls: over a point whose nearest scroller is the
                # control's own (not the fixed dock, not a nested preview scroller).
                wx, wy = page.evaluate(WHEEL_POINT, c["i"])
                page.mouse.move(wx, wy)
                page.mouse.wheel(0, 90 if cy > vh / 2 else -90)
                # A wheel scroll animates: probe only once the control stands still.
                last = None
                for _ in range(20):
                    page.wait_for_timeout(60)
                    now = page.evaluate("(i) => document.querySelector(`[data-probe=\"${i}\"]`).getBoundingClientRect().top", c["i"])
                    if now == last:
                        break
                    last = now
                page.mouse.move(1, 1)   # leave no hover from the wheel point behind
                page.wait_for_timeout(120)
                geo2, bad2, where2, under2 = probe(c["i"])
                if not under2:
                    break
            if bad2 == 0:
                reached.append({"text": c["text"], "points_under_host_bar": under, "wheel_steps": steps})
                owned.append({"text": c["text"], "target": geo["target"]})
            else:
                missed.append({"text": c["text"], "missed_points": bad2, "where": where2, "after_scroll": True})
            page.evaluate(RESTORE)
            page.wait_for_timeout(80)
        elif bad:
            missed.append({"text": c["text"], "missed_points": bad, "where": where, "face": geo["face"]})
        else:
            owned.append({"text": c["text"], "target": geo["target"]})
    page.mouse.move(1, 1)
    page.evaluate(RESTORE)
    page.wait_for_timeout(100)
    return {"owned": owned, "missed": missed, "reached_by_scroll": reached}


class Boards:
    """One test's boards at one width: shots, facts, the on-screen law, the pointer
    pass and the byte fence (the menu-bar clock masked)."""

    def __init__(self, shots: Path, width: int) -> None:
        self.shots, self.width = shots, width
        self.facts: dict[str, Any] = {}
        self.fails: list[str] = []
        self.shas: dict[str, str] = {}

    def seat(self, page: Any, sel: str, block: str = "start") -> None:
        page.evaluate(SEAT, [sel, block])
        page.wait_for_timeout(300)

    def shoot(self, page: Any, board: str, anchor: str, named: list[str], *, seat: str | None = "FIRST",
              block: str = "start", pointer: bool = True, same_as: str | None = None) -> dict[str, Any]:
        """`same_as`: the board this one is MEANT to equal pixel for pixel (a receipt that must
        not move); any other identical pair is a failure."""
        target = named[0] if seat == "FIRST" else seat
        if target:
            self.seat(page, target, block)
        page.mouse.move(1, 1)
        page.wait_for_timeout(300)
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
                self.seat(page, target, block)
        self.facts[key] = f
        self.fails += [f"{key}: off screen {v}" for v in vis if not v["ok"]]
        if sha in self.shas.values():
            twin = next(k for k, v in self.shas.items() if v == sha)
            if twin != f"{same_as}-{self.width}":
                self.fails.append(f"{key}: identical to {twin} with the clock masked")
            f["identical_to"] = twin
        self.shas[key] = sha
        return f

    def write(self, name: str, extra: dict[str, Any] | None = None) -> None:
        data = {"boards": self.facts, **(extra or {})}
        (self.shots / f"{name}-{self.width}.json").write_text(
            json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, default=str) + "\n")

    def assert_clean(self) -> None:
        """The laws on every board: named elements on screen, no identical shots,
        no word the well adds under 12 px, no raw button in the well, no modal, no
        overflow, the one row grammar, the well's own type in a preview, no stale
        word, no Mark delivered on a new kind, no Open on a Room decision row,
        every well control owns its nine points (after ordinary scrolling)."""
        bad = list(self.fails)
        for key, f in self.facts.items():
            if not f.get("window"):
                bad.append(f"{key}: no frame")
                continue
            law = {
                "text under 12px in the well": not f["small_text"]["touched"],
                "raw button in the well": not f["raw_buttons"]["touched"],
                "modal": not f["modal"],
                "horizontal overflow": not f["h_overflow"] and not f["body_overflow_x"],
                "row grammar": all(g == "ok" for g in f["row_grammar"]),
                "mono preview": not any("Mono" in x for x in f["preview_fonts"]),
                "stale words": not f["stale_words"],
                "Mark delivered on a new kind": not f["mark_delivered_in_new_kind"],
                "Open on a Room decision row": not any(f["room_open_verbs"]),
                "missed control": not f.get("pointer", {}).get("missed"),
            }
            bad += [f"{key}: {name} {f.get('pointer', {}).get('missed') if name == 'missed control' else ''}"
                    for name, ok in law.items() if not ok]
        assert not bad, bad
