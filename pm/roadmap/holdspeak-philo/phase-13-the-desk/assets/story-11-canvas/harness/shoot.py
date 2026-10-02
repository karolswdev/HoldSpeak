"""PHILO-13-11 (C1) canvas: the Workbench look, drawn on the REAL product.

Everything is live except the stand-ins named in harness/p13.tsx's header: a REAL
hub (scripts/graph_walk.py serve) on an isolated HOME (tempfile.mkdtemp under
/tmp, removed when the run ends), seeded through the product's producers
(seed_db.py, the Phase 13 grounding seed) and its routes (rig.seed_hub); the
PRODUCT app served by vite with the seats (vite.config.mjs) and the proposed
material (canvas.css). Nothing leaves the machine; no send is pressed.

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/harness/shoot.py

Shots: ../shots/C1-<n>-<name>-<width>.png at 1440x900 and 393x852 (device scale 2);
facts.json beside them. Each width runs on its own hub and HOME (the proposal),
and the comparison's alternative runs on the same hub with the theme switched.
ONLY_WIDTH=393 limits the run to one width; ONLY=C1-2 to boards whose id starts so;
STACK_STATE=<dev.py state file> reuses a running stack (iteration only).
Exit 2 on a failed fence.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rig  # noqa: E402

CANVAS = HERE.parent
SHOTS = CANVAS / "shots"
ALL_WIDTHS = [(1440, 900), (393, 852)]
WIDTHS = [w for w in ALL_WIDTHS if not os.environ.get("ONLY_WIDTH") or str(w[0]) == os.environ["ONLY_WIDTH"]]
ONLY = os.environ.get("ONLY", "")
REHEARSE = False

# ── the rendered facts of one board ─────────────────────────────────────────
FACTS = r"""() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && !e.closest('[hidden]'); };
  // The proposal's own surface: the frame (screen bar, Dock), every window head, every menu, every p13 element.
  const roots = [document.body];   // R5: the whole board, not only the proposal's own parts
  const small = [], raw = [];
  for (const root of roots) {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      const t = n.textContent.trim(); if (!t || !/[A-Za-z0-9]/.test(t)) continue;  // a glyph is not text (UX-CANON C)
      const el = n.parentElement; if (!vis(el)) continue;
      const fs = parseFloat(getComputedStyle(el).fontSize);
      if (fs > 0 && fs < 12) small.push({ text: t.slice(0, 30), fs, where: (root.className || '').toString().slice(0, 40), proposal: !el.closest('.desk-surface-body, .desk-window-shell > :not(.desk-pullout-head)') || !!el.closest('.p13-parked, .p13-park-receipt, .p13-sheet') });
    }
    for (const b of [...(root.matches('button') ? [root] : []), ...root.querySelectorAll('button')]) {
      if (!vis(b)) continue;
      const cn = String(b.className || '');
      // the library Button: plated (.btn) or chrome (variant="chrome" carries no plate class; Signal.tsx:62)
      if (!/(^|\s)(btn|btn--chrome)(\s|$)/.test(cn) && !b.closest('.desk-menu-list')) raw.push({ text: (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 30), cls: cn.slice(0, 60), proposal: !!b.closest('[class*=p13-], .p13-chairwin') && !b.closest('.desk-surface-body') });
    }
  }
  const shells = [...document.querySelectorAll('.desk-window-shell')].filter(vis).filter((s) => !s.closest('.p13-sample-stack'));
  const windows = shells.map((s) => {
    const head = s.querySelector(':scope > .desk-pullout-head');
    return {
      name: s.getAttribute('aria-label') || '',
      front: s.hasAttribute('data-p13-front'),
      close: head ? head.querySelectorAll('.p13-gadgets-left .p13-g-close').length : 0,
      depth: head ? head.querySelectorAll('.p13-gadgets-right .p13-g-depth').length : 0,
      zoom: head ? head.querySelectorAll('.p13-gadgets-right .p13-g-zoom').length : 0,
      iconify: head ? head.querySelectorAll('.p13-gadgets-right .p13-g-iconify').length : 0,
      old_traffic_visible: head ? [...head.querySelectorAll('.desk-traffic')].filter(vis).length : 0,
      frame: getComputedStyle(s).borderLeftColor,
    };
  });
  const dock = document.querySelector('.desk-dock');
  const dr = dock ? dock.getBoundingClientRect() : null;
  const menu = [...document.querySelectorAll('[role=menu]')].filter(vis);
  return {
    screen_title: (document.querySelector('.p13-screen-name') || {}).innerText || null,
    clock: (document.querySelector('.desk-clock') || {}).innerText || null,
    windows,
    dock: dr ? { left: Math.round(dr.left), right: Math.round(dr.right), top: Math.round(dr.top), height: Math.round(dr.height), scrolls: dock.scrollWidth > dock.clientWidth } : null,
    appstates: [...document.querySelectorAll('.desk-dock .p13-appstate, .desk-dock .desk-dock-badge')].filter(vis).map((e) => e.innerText.trim()),
    menus: menu.map((m) => ({ label: m.getAttribute('aria-label'), rows: [...m.querySelectorAll('[role^=menuitem]')].filter(vis).map((r) => r.innerText.replace(/\s+/g, ' ').trim()) })),
    small_text: small,
    raw_buttons: raw,
    zero_counter: roots.some((r) => /(^|\s)0 [A-Z]{2,}/.test(r.innerText || '')),
    modal: !!document.querySelector('[role=dialog][aria-modal=true], dialog[open]'),
    h_overflow: document.documentElement.scrollWidth > window.innerWidth,
  };
}"""

# ONE meaning of "needs you" (story 03): every "need(s) you" on the glass is the Chair head's number,
# and the bell and the Dock's needs-you badges carry the same number.
NEEDS = r"""() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight && getComputedStyle(e).visibility !== 'hidden'; };
  const said = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const t = n.textContent.replace(/\s+/g, ' ').trim();
    if (/needs? you/i.test(t) && vis(n.parentElement)) said.push(t);
  }
  const head = document.querySelector('[data-testid=arrival-display]');
  const num = (t) => { const m = (t || '').match(/\d+/); return m ? Number(m[0]) : null; };
  const bell = document.querySelector('.desk-bell strong');
  const intel = document.querySelector('.desk-dock [aria-label^="Intelligence"] .desk-dock-badge');
  const memory = document.querySelector('.desk-dock [aria-label^="Desk memory"] .desk-dock-badge');
  return { said, head: head ? head.innerText : null, head_n: num(head && head.innerText), bell: num(bell && bell.innerText),
           intel: num(intel && intel.innerText), memory: num(memory && memory.innerText) };
}"""

# 393: the shelf ends on a whole icon (no icon cut by the edge or by the More gadget).
SHELF = r"""() => {
  const dock = document.querySelector('.desk-dock'); if (!dock) return null;
  const more = dock.querySelector('.p13-dock-more'); const edge = more ? more.getBoundingClientRect().left : innerWidth;
  const cut = [...dock.children].filter((c) => c !== more).map((c) => ({ c, r: c.getBoundingClientRect() }))
    .filter(({ r }) => r.width && r.left < edge - 1 && r.right > edge + 1).map(({ c }) => (c.getAttribute('aria-label') || c.className || '').toString().slice(0, 40));
  const whole = [...dock.children].filter((c) => c !== more).filter((c) => { const r = c.getBoundingClientRect(); return r.width && r.left >= -1 && r.right <= edge + 1; })
    .map((c) => (c.getAttribute('aria-label') || '').split(',')[0]);
  return { cut, whole, more: !!more, more_w: more ? Math.round(more.getBoundingClientRect().width) : 0, more_h: more ? Math.round(more.getBoundingClientRect().height) : 0 };
}"""

# ── R8 fences (each must be red on the round-two boards and green after) ──────
JS_LIB = r"""
const shown = (e) => { if (!e || e.closest('[hidden]')) return false; const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
  return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && Number(cs.opacity) > 0.05 && r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth; };
const layer = (e) => e && e.closest('[role=menu], .desk-window-shell:not(.p13-sample-win), .desk-menubar, .desk-dock, .p13-sheet-host');
// the visible rect of an element: clipped by every scrolling/clipping ancestor and the viewport
const vrect = (e) => { const r = e.getBoundingClientRect(); let t = r.top, l = r.left, b = r.bottom, ri = r.right;
  for (let a = e.parentElement; a; a = a.parentElement) { const cs = getComputedStyle(a);
    if (/(auto|scroll|hidden|clip)/.test(cs.overflowX + cs.overflowY)) { const ar = a.getBoundingClientRect(); t = Math.max(t, ar.top); l = Math.max(l, ar.left); b = Math.min(b, ar.bottom); ri = Math.min(ri, ar.right); } }
  t = Math.max(t, 0); l = Math.max(l, 0); b = Math.min(b, innerHeight); ri = Math.min(ri, innerWidth);
  return { t, l, b, r: ri, w: ri - l, h: b - t, full: Math.abs(ri - l - r.width) < 1.5 && Math.abs(b - t - r.height) < 1.5 }; };
// nine points of a box, 2 px in
const nine = (x0, y0, x1, y1) => { const xs = [x0 + 2, (x0 + x1) / 2, x1 - 2], ys = [y0 + 2, (y0 + y1) / 2, y1 - 2]; return xs.flatMap((x) => ys.map((y) => [x, y])); };
// a point is OWNED by t, OCCLUDED (a different layer above: another window, a menu), or LOST (something else of the same layer)
const probe = (t, x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 'lost'; if (t === h || t.contains(h)) return 'own';
  const lt = layer(t), lh = layer(h); return (lh && lt && lh !== lt && !lt.contains(lh)) ? 'occluded' : 'lost'; };
"""

# 1. Ownership: every sampled point of a frame control's rect is that control's.
OWN = "() => {" + JS_LIB + r"""
  const sel = '.p13-gadget, .desk-menubar button, .desk-dock > button, .desk-dock-chip button, .desk-pullout-head .desk-wings button, .desk-pullout-head .desk-window-actions button, .p13-dock-more, .p13-chair-closed .btn, .p13-chair-reopen-list .btn';
  const out = [];
  for (const t of document.querySelectorAll(sel)) {
    if (!shown(t) || t.closest('.p13-sample-stack')) continue;
    const v = vrect(t); if (!v.full) continue;   // scrolled out of its strip: not a target now
    const res = nine(v.l, v.t, v.r, v.b).map(([x, y]) => probe(t, x, y));
    const own = res.filter((r) => r === 'own').length, occ = res.filter((r) => r === 'occluded').length;
    out.push({ name: (t.getAttribute('aria-label') || t.innerText || '').trim().slice(0, 32), own, occ, lost: 9 - own - occ, w: Math.round(v.w), h: Math.round(v.h) });
  }
  return out;
}"""

# 2. Visible state: the front window (the one blue bar) and its title; it is really on the glass.
FRONT = "() => {" + JS_LIB + r"""
  const heads = [...document.querySelectorAll('.desk-pullout-head')].filter((h) => shown(h) && !h.closest('.p13-sample-stack'));
  const blue = heads.filter((h) => { const c = getComputedStyle(h).backgroundColor; return c === 'rgb(102, 136, 187)'; });
  const front = document.querySelector('.desk-window-shell[data-p13-front]');
  let onGlass = false;
  if (front) { const hd = front.querySelector(':scope > .desk-pullout-head') || front; const r = hd.getBoundingClientRect();
    onGlass = [0.1, 0.3, 0.5, 0.7, 0.9].some((f) => { const h = document.elementFromPoint(r.left + r.width * f, r.top + r.height / 2); return !!h && (front.contains(h) || !!h.closest('[role=menu]')); }); }   // its own menu over it counts as on the glass
  return { blue: blue.map((h) => (h.parentElement.getAttribute('aria-label') || '?')), front: front ? front.getAttribute('aria-label') : null, on_glass: onGlass };
}"""

# 3. In-place contrast of every text node: ≥ 4.5:1, or ≥ 3:1 for large text (24 px, or 18.66 px bold).
CONTRAST_ALL = "() => {" + JS_LIB + r"""
  const rgb = (c) => { const m = c.match(/[\d.]+/g); return m ? m.map(Number) : null; };
  const lum = (m) => { const [r, g, b] = m.slice(0, 3).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const ground = (e) => { for (let a = e; a; a = a.parentElement) { const m = rgb(getComputedStyle(a).backgroundColor); if (m && (m.length < 4 || m[3] >= 0.9)) return m; } return [14, 15, 19]; };
  const bad = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const t = n.textContent.trim(); if (!t || !/[A-Za-z0-9]/.test(t)) continue;
    const el = n.parentElement; if (!shown(el)) continue;
    if (el.closest('[disabled], [aria-disabled=true], .desk-menu-list [aria-disabled]')) continue;   // a disabled control (WCAG 1.4.3 exemption; UX-CANON C: it differs by its state)
    const cs = getComputedStyle(el); const fg = rgb(cs.color); if (!fg || (fg.length > 3 && fg[3] < 0.5)) continue;
    const range = document.createRange(); range.selectNodeContents(n); const rr = [...range.getClientRects()].find((x) => x.width > 1);
    if (!rr) continue; const v = vrect(el); if (v.w <= 0 || v.h <= 0) continue;
    const cx = Math.min(v.r - 1, Math.max(v.l + 1, rr.left + Math.min(4, rr.width / 2))), cy = Math.min(v.b - 1, Math.max(v.t + 1, rr.top + rr.height / 2));
    const top = document.elementFromPoint(cx, cy); if (!top || (!el.contains(top) && !top.contains(el))) continue;  // covered: not on the glass
    const a = lum(fg), b = lum(ground(el)); const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    const px = parseFloat(cs.fontSize), wt = Number(cs.fontWeight) || 400; const large = px >= 24 || (px >= 18.66 && wt >= 700);
    if (ratio < (large ? 3 : 4.5)) bad.push({ text: t.slice(0, 30), ratio: Math.round(ratio * 100) / 100, px, large });
  }
  return bad;
}"""

# 4. 393: every target owns a 44 × 44 box (plated Buttons by their halo), the front window's content ≥ 700 px.
TARGETS44 = "() => {" + JS_LIB + r"""
  const out = [];
  for (const t of document.querySelectorAll('button, a[href], [role=button], [role=menuitem], [role=menuitemcheckbox], [role=tab], [role=checkbox], input:not([type=hidden]), select, textarea')) {
    if (!shown(t) || t.closest('.p13-sample-stack')) continue;
    if (t.parentElement && t.parentElement.closest('button, [role=button], a[href], [role=menuitem]')) continue;   // a part of a bigger target
    const v = vrect(t); if (!v.full) continue;
    const cx = (v.l + v.r) / 2, cy = (v.t + v.b) / 2, hw = Math.max(22, v.w / 2), hh = Math.max(22, v.h / 2);
    const res = nine(cx - hw, cy - hh, cx + hw, cy + hh).map(([x, y]) => probe(t, x, y));
    const own = res.filter((r) => r === 'own').length, occ = res.filter((r) => r === 'occluded').length;
    if (own + occ < 9) out.push({ name: (t.getAttribute('aria-label') || t.innerText || t.getAttribute('placeholder') || t.className || '').toString().trim().replace(/\s+/g, ' ').slice(0, 32), w: Math.round(v.w), h: Math.round(v.h), own, occ });
  }
  return out;
}"""
CONTENT = r"""() => {
  const f = document.querySelector('.desk-window-shell[data-p13-front]'); if (!f) return null;
  const r = f.getBoundingClientRect(); const head = f.querySelector(':scope > .desk-pullout-head'); const hh = head ? head.getBoundingClientRect().height : 0;
  const cs = getComputedStyle(f); const bt = parseFloat(cs.borderTopWidth) + parseFloat(cs.borderBottomWidth);
  const top = Math.max(r.top, 0), bottom = Math.min(r.bottom, innerHeight);
  return Math.round(bottom - top - hh - bt);
}"""
DOCKFACTS = r"""async () => {
  const projects = await fetch('/api/projects', { headers: { Authorization: 'Bearer philo13-c1' } }).then((r) => r.json()).then((j) => (j.projects || []).filter((p) => (p.status || 'active') === 'active').map((p) => p.id)).catch(() => null);
  const icons = [...document.querySelectorAll('.desk-dock [data-project]')].map((e) => e.dataset.project);
  const zeros = [...document.querySelectorAll('.desk-dock .desk-dock-badge, .desk-bell strong')].filter((b) => b.getBoundingClientRect().width && /^\s*0\s*$/.test(b.innerText)).length;
  return { projects, icons, missing: projects ? projects.filter((p) => !icons.includes(p)) : null, zeros };
}"""



# R 3b: nothing clips, nothing scrolls sideways. (a) no horizontally scrolling strip (an element whose
# overflow-x scrolls or hides and whose content is wider than it); (b) no text node whose box runs past
# its clipping ancestor or spills out of its own control. Ellipsis truncation (text-overflow: ellipsis,
# UX-CANON A.6: titles shrink first) is recorded, not failed. The Dock is excluded by name: it is the
# AppIcon shelf, paged by its More gadget at 393 (round two), not a strip of choices.
CLIP = "() => {" + JS_LIB + r"""
  const tiny = (e) => { const r = e.getBoundingClientRect(); return r.width < 3 || r.height < 3; };   // visually hidden (sr-only)
  const skip = (e) => tiny(e) || e.closest('.desk-dock, textarea, input, pre, code, .xterm, [aria-hidden=true], .p13-sample-stack');
  const strips = [], clipped = [], ellipsis = [];
  for (const e of document.querySelectorAll('body *')) {
    if (!shown(e) || skip(e)) continue;
    const cs = getComputedStyle(e);
    if (/(auto|scroll|hidden|clip)/.test(cs.overflowX) && e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0) {
      if (cs.textOverflow === 'ellipsis') continue;   // a truncated line, recorded below
      strips.push({ cls: String(e.className).slice(0, 60), scroll: e.scrollWidth, client: e.clientWidth, text: (e.innerText || '').replace(/\s+/g, ' ').slice(0, 40) });
    }
  }
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const t = n.textContent.trim(); if (!t || !/[A-Za-z0-9]/.test(t)) continue;
    const el = n.parentElement; if (!shown(el) || skip(el)) continue;
    const cs = getComputedStyle(el); if (parseFloat(cs.fontSize) === 0) continue;
    const range = document.createRange(); range.selectNodeContents(n);
    const rects = [...range.getClientRects()].filter((r) => r.width > 0.5); if (!rects.length) continue;
    const l = Math.min(...rects.map((r) => r.left)), r = Math.max(...rects.map((x) => x.right));
    // the nearest ancestor that clips horizontally (the element itself included)
    let anc = null, ell = null;
    for (let a = el; a; a = a.parentElement) { const c = getComputedStyle(a);
      if (c.textOverflow === 'ellipsis' && a.scrollWidth > a.clientWidth + 1) ell = a;
      if (/(auto|scroll|hidden|clip)/.test(c.overflowX)) { anc = a; break; } }
    if (ell) { ellipsis.push(t.slice(0, 30)); continue; }
    if (anc) { const ar = anc.getBoundingClientRect(); if (l < ar.left - 1 || r > ar.right + 1) { clipped.push({ text: t.slice(0, 30), why: 'past ' + String(anc.className).slice(0, 40) }); continue; } }
    const ctl = el.closest('button, [role=button], [role=tab], a[href]');
    if (ctl) { const br = ctl.getBoundingClientRect(); if (l < br.left - 1 || r > br.right + 1) clipped.push({ text: t.slice(0, 30), why: 'spills out of its control' }); }
  }
  return { strips, clipped, ellipsis };
}"""


# 3c: RENDERED OVERLAP. No two visible interactive or text elements in the same window (or bar,
# shelf, menu) intersect, a parent and its own descendant excepted. Text elements are the elements
# that hold a text node of their own. An intersection counts when it is more than 2 × 2 px and the
# glass at its centre shows one of the two (a third element over both is occlusion, not a collision).
# Three waivers, each exactly its relationship (round 3d; see the functions): (a) content scrolling
# beneath a sticky/fixed bar of its own window; (b) the in-well MicButton inside ITS field; (c) a Dock
# AppIcon partly scrolled past the shelf's edge under More. Every waived pair is recorded.
OVERLAP = "() => {" + JS_LIB + r"""
  const isText = (e) => [...e.childNodes].some((n) => n.nodeType === 3 && /[A-Za-z0-9]/.test(n.textContent));
  const isCtl = (e) => e.matches('button, a[href], input, select, textarea, [role=button], [role=tab], [role^=menuitem], [role=checkbox]');
  const scope = (e) => e.closest('[role=menu], .desk-window-shell:not(.p13-sample-win), .desk-menubar, .desk-dock, .p13-sheet-host') || document.body;
  const R = (e) => e.getBoundingClientRect();
  const inside = (r, o, tol = 1) => r.left >= o.left - tol && r.right <= o.right + tol && r.top >= o.top - tol && r.bottom <= o.bottom + tol;
  // the nearest sticky or fixed bar of e, strictly inside its window (the window shell itself is not a bar)
  const barOf = (e, sc) => { for (let p = e; p && p !== sc; p = p.parentElement) { const ps = getComputedStyle(p).position; if (ps === 'sticky' || ps === 'fixed') return p; } return null; };
  // the nearest vertical scroll container of e, strictly inside its window
  const scrollerOf = (e, sc) => { for (let p = e.parentElement; p && p !== sc; p = p.parentElement) { const oy = getComputedStyle(p).overflowY; if (oy === 'auto' || oy === 'scroll') return p; } return null; };

  // WAIVER (a): x sits in a sticky/fixed bar of its window; y is that window's scrolling content passing
  // beneath the bar. Fixed bar: y's scroll container is an ancestor of y and NOT of the bar. Sticky bar: a
  // sticky bar sticks INSIDE its scroll container (CSS), so: the bar sticks to y's scroll container, y is not
  // in the bar, and the overlap lies within the bar's box.
  const waiveSticky = (x, y, sc, ov) => {
    const bar = barOf(x.e, sc); if (!bar || bar.contains(y.e) || barOf(y.e, sc) === bar) return false;
    const S = scrollerOf(y.e, sc); if (!S || !S.contains(y.e)) return false;
    const ps = getComputedStyle(bar).position;
    const fixedOk = ps === 'fixed' && !S.contains(bar);
    const stickyOk = ps === 'sticky' && scrollerOf(bar, sc) === S;
    return (fixedOk || stickyOk) && inside(ov, R(bar));
  };
  // WAIVER (b): the in-well MicButton and ITS field: x is an input/textarea, y is a mic button; their nearest
  // common ancestor is x's field wrapper (x's parent or grandparent) holding no other text field; the mic's box
  // is inside the input's box.
  const waiveMic = (x, y) => {
    if (!x.e.matches('input, textarea')) return false;
    const mic = y.e.closest('button.desk-mic, button[class*=mic], .desk-mic button, [class*=mic] > button, button[aria-label^=Speak]');
    if (!mic) return false;
    let c = x.e.parentElement; while (c && !c.contains(mic)) c = c.parentElement;
    if (!c || !(c === x.e.parentElement || c === x.e.parentElement?.parentElement)) return false;
    if ([...c.querySelectorAll('input, textarea')].filter((f) => f !== x.e).length) return false;
    return inside(R(mic), R(x.e));
  };
  // WAIVER (c): the Dock's More gadget over an AppIcon of the same shelf that is partly scrolled past the
  // shelf's visible edge (the icon begins left of More and runs on under it).
  const waiveMore = (x, y) => {
    const more = x.e.closest('.p13-dock-more'); if (!more) return false;
    const icon = y.e.closest('.desk-dock-launch'); if (!icon || icon.parentElement !== more.parentElement) return false;
    const ir = R(icon), mr = R(more);
    return ir.left < mr.left && ir.right > mr.left + 1;
  };

  const els = [];
  for (const e of document.querySelectorAll('body *')) {
    if (!(isText(e) || isCtl(e))) continue;
    if (!shown(e) || e.closest('[aria-hidden=true], .p13-sample-stack, svg')) continue;
    const r = e.getBoundingClientRect(); if (r.width < 3 || r.height < 3) continue;
    if (isText(e) && parseFloat(getComputedStyle(e).fontSize) === 0) continue;
    const v = vrect(e); if (v.w < 3 || v.h < 3) continue;   // the box as the glass shows it
    els.push({ e, v, s: scope(e) });
  }
  const hits = [], waived = [];
  const name = (e) => ((e.getAttribute('aria-label') || e.innerText || e.className || '') + '').replace(/\s+/g, ' ').trim().slice(0, 28);
  for (let i = 0; i < els.length; i++) for (let j = i + 1; j < els.length; j++) {
    const a = els[i], b = els[j];
    if (a.s !== b.s || a.e.contains(b.e) || b.e.contains(a.e)) continue;
    const l = Math.max(a.v.l, b.v.l), r = Math.min(a.v.r, b.v.r), t = Math.max(a.v.t, b.v.t), bt = Math.min(a.v.b, b.v.b);
    if (r - l <= 2 || bt - t <= 2) continue;
    const h = document.elementFromPoint((l + r) / 2, (t + bt) / 2);
    if (!h || !(a.e.contains(h) || b.e.contains(h) || h.contains(a.e) || h.contains(b.e))) continue;
    const ov = { left: l, right: r, top: t, bottom: bt };
    const why = (waiveSticky(a, b, a.s, ov) || waiveSticky(b, a, a.s, ov)) ? 'sticky' : (waiveMic(a, b) || waiveMic(b, a)) ? 'mic' : (waiveMore(a, b) || waiveMore(b, a)) ? 'more' : null;
    const rec = { a: name(a.e), b: name(b.e), w: Math.round(r - l), h: Math.round(bt - t) };
    if (why) { waived.push({ ...rec, waiver: why }); continue; }
    hits.push(rec);
    if (hits.length > 40) break;
  }
  return { hits, waived };
}"""

# 3d: THE MUTATION PROOF. Three injected overlaps, each the near miss of one waiver; the fence must
# catch every one (red), and the boards without them stay green.
PLACE = r"""const place = (el, x, y) => { el.style.position = 'fixed'; el.style.left = x + 'px'; el.style.top = y + 'px';
      const r = el.getBoundingClientRect(); el.style.left = (x + (x - r.left)) + 'px'; el.style.top = (y + (y - r.top)) + 'px'; };"""
MUTATE = {
    # (a) a button inside the Room's sticky Ask bar, moved over the window's own title (not content
    #     scrolling beneath the bar)
    "a_sticky": "() => { " + PLACE + r""" const bar = document.querySelector('.room-ask-container'); if (!bar) return 'no bar';
      // a button that lives IN the sticky bar, moved up over a text row of the body that is NOT beneath the bar
      const br = bar.getBoundingClientRect(); const body = bar.closest('.desk-surface-body');
      const t = [...body.querySelectorAll('*')].find((e) => !bar.contains(e) && [...e.childNodes].some((n) => n.nodeType === 3 && /[A-Za-z]/.test(n.textContent)) && e.getBoundingClientRect().bottom < br.top - 20 && e.getBoundingClientRect().top > body.getBoundingClientRect().top + 10);
      if (!t) return 'no target'; const r = t.getBoundingClientRect(); const b = document.createElement('button'); b.className = 'btn p13-mutant'; b.textContent = 'MUTANT A';
      Object.assign(b.style, { width: Math.max(80, r.width) + 'px', height: Math.max(20, r.height) + 'px', zIndex: 9999 }); bar.appendChild(b); place(b, r.left, r.top);
      window.__p13MutantTarget = (t.innerText || '').trim().slice(0, 20); return 'ok'; }""",
    # (b) a mic, not of this field, placed over a DIFFERENT field of the same window (it shares no field wrapper with it)
    "b_mic": "() => { " + PLACE + r""" const w = document.querySelector('.desk-window-shell[data-p13-front]'); if (!w) return 'no window';
      const mic = [...w.querySelectorAll('button')].find((b) => /^Speak/.test(b.getAttribute('aria-label') || ''));
      const body = w.querySelector('.desk-surface-body') || w;
      const fields = [...body.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=radio]), textarea')].filter((f) => f.getBoundingClientRect().width > 60 && f.getBoundingClientRect().height > 20);
      const other = fields.find((f) => { let c = f.parentElement; for (let i = 0; i < 2 && c; i++, c = c.parentElement) if (c.contains(mic)) return false; return true; });
      if (!mic || !other) return 'no target'; const r = other.getBoundingClientRect(); const m = mic.cloneNode(true); m.classList.add('p13-mutant');
      m.style.zIndex = 9999; body.appendChild(m); place(m, r.left + 30, r.top + 2); window.__p13MutantTarget = other.getAttribute('aria-label') || other.getAttribute('placeholder') || ''; return 'ok'; }""",
    "c_more": "() => { " + PLACE + r""" const more = document.querySelector('.p13-dock-more'); if (!more) return 'no target'; const r = more.getBoundingClientRect();
      const s = document.createElement('span'); s.className = 'p13-mutant'; s.textContent = 'STRAY TEXT'; Object.assign(s.style, { font: '700 14px monospace', zIndex: 1 });
      more.parentElement.appendChild(s); place(s, r.left - 30, r.top + 10); return 'ok'; }""",
}
UNMUTATE = "() => document.querySelectorAll('.p13-mutant').forEach((e) => e.remove())"


def run(width: int, height: int, state: dict | None) -> tuple[list[str], dict]:
    facts: dict = {}
    fails: list[str] = []
    errors: list[str] = []
    phone = width <= 420
    stack = None
    try:
        if state is None:
            stack = rig.Stack("proposal").__enter__()
            url, seed, guard = stack.url, stack.seed, stack.guard
        else:
            url, seed, guard = state["url"], state["seed"], state.get("guard")
        facts[f"_seat_guard_{width}"] = guard
        facts[f"_seed_{width}"] = {k: v for k, v in seed.items() if k != "db"}
        SHOTS.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2, has_touch=phone)
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
            page.on("console", lambda m: errors.append(f"console: {m.text[:200]}")
                    if m.type == "error" and "status of 4" not in m.text and "Failed to fetch" not in m.text else None)
            try:
                # REHEARSAL (no shot, no fact): walk every board once so a cold vite server has optimized every
                # dependency before the real pass (a late optimization RELOADS the page; the reload fence proves none).
                global REHEARSE
                REHEARSE = not os.environ.get("NO_REHEARSE")
                try:
                    if not REHEARSE:
                        raise RuntimeError("rehearsal skipped (NO_REHEARSE, a warm stack)")
                    boards(page, width, url, seed, {}, [])
                except Exception as exc:
                    print("rehearsal:", str(exc).splitlines()[0][:200], flush=True)
                REHEARSE = False
                page.close()
                page = ctx.new_page()
                page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
                page.on("console", lambda m: errors.append(f"console: {m.text[:200]}")
                        if m.type == "error" and "status of 4" not in m.text and "Failed to fetch" not in m.text else None)
                boards(page, width, url, seed, facts, fails)
            except Exception as exc:
                traceback.print_exc()
                fails.append(f"CRASH at width {width}: {str(exc).splitlines()[0][:300]}")
                try:
                    page.screenshot(path=str(SHOTS / f"_crash-{width}.png"))
                except Exception:
                    pass
            browser.close()
    finally:
        if stack is not None:
            stack.__exit__(None, None, None)
        facts[f"_browser_errors_{width}"] = errors
    return fails, facts


def boards(page, width: int, url: str, seed: dict, facts: dict, fails: list[str]) -> None:
    phone = width <= 420
    W = page.viewport_size["width"]

    def ev(js: str, arg=None):
        return page.evaluate(js, arg)

    def settle(ms=700):
        page.wait_for_timeout(ms)

    def boot():
        page.goto(url, wait_until="load")
        page.locator(".chair").wait_for(timeout=120_000)
        for _ in range(40):
            cl = page.get_by_role("button", name="Continue later", exact=True)
            if not cl.count():
                break
            try:
                cl.first.click(timeout=2000)
            except Exception:
                pass
            settle(500)
        page.locator("[data-testid=p13-chairdesk]").wait_for(timeout=60_000)
        settle(2500)
        live()
        close_all()
        ev("() => { window.__p13Booted = true; }")

    def live(**over):
        tags = {"surface-meetings": {"text": ("REC 12:04" if phone else "● REC 12:04"), "tone": "rec"},
                "surface-people": {"text": "1:1 14:30"}}
        tags.update(over.get("tags", {}))
        ev("(v) => window.__p13.live(v)", {"tags": tags, "offline": over.get("offline"), "projects": {"p-ledger": 3, "p-obs": 1}})

    def close_all():
        """Every desk window closes by its own close gadget (the Chair's windows stay)."""
        ev("() => { window.__p13.sheet(false); window.__p13Open.closeAll(); }")
        for _ in range(12):
            n = ev("""() => { const g = [...document.querySelectorAll('.desk-window-shell:not(.p13-chairwin):not(.p13-sample-win) > .desk-pullout-head .p13-g-close')]
                       .filter((e) => e.getBoundingClientRect().width); if (g.length) g[0].click(); return g.length; }""")
            if not n:
                break
            settle(450)
        page.keyboard.press("Escape")
        settle(500)

    def jsclick(loc):
        loc.first.evaluate("(e) => { e.scrollIntoView({block: 'center'}); e.click(); }")
        settle(700)

    def shoot(board: str, front: str | None, checks: dict | None = None, extra: dict | None = None):
        if REHEARSE or (ONLY and not board.startswith(ONLY)):
            return None
        ev("() => { if (!document.querySelector('[role=menu]')) document.activeElement?.blur?.(); }")
        settle(600)
        key = f"{board}-{width}"
        if not ev("() => window.__p13Booted === true"):
            fails.append(f"{key}: the page reloaded during the run")
        page.screenshot(path=str(SHOTS / f"{key}.png"))
        f = ev(FACTS)
        f["needs_you"] = ev(NEEDS)
        f["own"] = ev(OWN)
        f["front_state"] = ev(FRONT)
        f["low_contrast"] = ev(CONTRAST_ALL)
        f["dockfacts"] = ev(DOCKFACTS)
        f["clip"] = ev(CLIP)
        ov = ev(OVERLAP)
        f["overlap"], f["overlap_waived"] = ov["hits"], ov["waived"]
        if phone:
            f["shelf"] = ev(SHELF)
            f["targets_under_44"] = ev(TARGETS44)
            f["content_px"] = ev(CONTENT)
        f["intended_front"] = front
        if extra:
            f.update(extra)
        facts[key] = f
        fs, ny = f["front_state"], f["needs_you"]
        n = ny["head_n"]
        law = {
            "(1) every window carries close + depth, zoom at 1440": all(w["close"] == 1 and w["depth"] == 1 and (phone or w["zoom"] == 1) for w in f["windows"]),
            "(1) the old traffic lights are gone": all(w["old_traffic_visible"] == 0 for w in f["windows"]),
            "(2) the screen bar names the front window": f["screen_title"] == fs["front"],
            "(2) the screen bar shows the time": bool(f["clock"]),
            "(5) no text under 12 px on the board": not f["small_text"],
            "no modal": not f["modal"],
            "no horizontal overflow": not f["h_overflow"],
            "the Dock inside the viewport": bool(f["dock"]) and f["dock"]["left"] >= 0 and f["dock"]["right"] <= W,
            "no scratch path on the glass": not ev("() => /p13c1-|\\/private\\/tmp|\\/tmp\\//.test(document.body.innerText)"),
            "one needs-you number": all((t == ny["head"]) or t == "Needs you" or (n is not None and t.startswith(f"{n} need")) for t in ny["said"]),
            # R8
            "R8 ownership: every sampled point of each frame control is that control's (or under a window in front)": all(o["lost"] == 0 for o in f["own"]),
            "R8 visible state: the intended window is the front one, on the glass": front is None or (fs["front"] == front and fs["on_glass"]),
            "R8 exactly one blue title bar": len(fs["blue"]) == 1,
            "R8 in-place contrast ≥ 4.5:1 (≥ 3:1 large)": not f["low_contrast"],
            "R8 no zero badge": f["dockfacts"]["zeros"] == 0,
            "3b no horizontally scrolling strip": not f["clip"]["strips"],
            "3b no clipped text (past its clipping ancestor or out of its control)": not f["clip"]["clipped"],
            "3c no rendered overlap (two interactive or text elements of one window intersect)": not f["overlap"],
            "R8 no active project missing from the Dock": f["dockfacts"]["missing"] == [],
        }
        if n is not None and ny["bell"] is not None:
            law["the bell carries the Chair's needs-you number"] = ny["bell"] == n
        if phone:
            law["R8 393: the front window's content ≥ 700 px"] = (f["content_px"] or 0) >= 700
            law["R8 393: no target under 44 × 44 (owned)"] = not f["targets_under_44"]
            law["393: the shelf ends on a whole icon"] = bool(f["shelf"]) and not f["shelf"]["cut"] and f["shelf"]["more"]
        for name, ok in {**law, **(checks or {})}.items():
            if not ok:
                fails.append(f"{key}: {name}")
        print(key, "front", fs["front"], "blue", fs["blue"], "lowc", f["low_contrast"][:3], "own-lost", [o for o in f["own"] if o["lost"]][:3],
              "t44", (f.get("targets_under_44") or [])[:4], "content", f.get("content_px"), "small", f["small_text"][:3], flush=True)
        return f

    # WARM-UP (not a board): a cold vite server optimizes a dependency the first time a lazy
    # window imports it and then RELOADS the page. Open every window once, then start clean.
    page.goto(url, wait_until="load")
    page.locator(".chair").wait_for(timeout=120_000)
    settle(2000)
    for js, arg in [("(s) => window.__p13Open.surface(s)", "review-meetings"), ("(p) => window.__p13Open.room(p)", "p-ledger"),
                    ("(s) => window.__p13Open.surface(s)", "open-people"), ("(r) => window.__p13Open.open(r)", f"workbench:{seed['workbench']}"),
                    ("() => window.__p13.sheet(true)", None)]:
        try:
            ev(js, arg) if arg is not None else ev(js)
        except Exception:
            pass
        settle(2500)
    settle(3000)
    boot()

    # ── C1-1 the whole Desk ──
    ev("() => window.__p13.chairFront('needs')")
    shoot("C1-1-the-desk", "Needs you")

    # ── C1-2 one window close-up: gadgets, the right-button menu, depth, zoom ──
    ev("(s) => window.__p13Open.surface(s)", "review-meetings")
    settle(2500)
    ev("(p) => window.__p13Open.room(p)", "p-ledger")
    settle(3000)
    shoot("C1-2a-window-gadgets", "Payments ledger cutover")
    tb = page.locator(".desk-window-shell[data-p13-front] > .desk-pullout-head .desk-pullout-title").last
    if phone or not tb.is_visible():
        hb = page.locator(".desk-window-shell[data-p13-front] > .desk-pullout-head").last.bounding_box()
        px, py = hb["x"] + hb["width"] - 70, hb["y"] + hb["height"] / 2
        # at 393 the head row is the wings strip: the right button lands on its free end
    else:
        b = tb.bounding_box()
        px, py = b["x"] + b["width"] + 18, b["y"] + b["height"] / 2
    page.mouse.click(px, py, button="right")
    page.locator("[role=menu]").first.wait_for(timeout=10_000)
    settle(300)
    sub = page.locator("[role=menu] [role=menuitem][aria-haspopup=menu]:has-text('Desk')").first
    (sub.click() if phone else sub.hover())
    settle(600)
    f = shoot("C1-2b-window-menu-amiga-keys", "Payments ledger cutover")
    if f is not None and not any("⌘N" in r.replace(" ", "") for m in f["menus"] for r in m["rows"]):
        fails.append(f"C1-2b-{width}: no Amiga-key column on the menu")
    page.keyboard.press("Escape"); page.keyboard.press("Escape")
    ev("() => document.body.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true}))")
    settle(400)
    page.locator(".desk-window-shell[data-p13-front] > .desk-pullout-head .p13-g-depth").last.click()
    settle(800)
    shoot("C1-2c-depth-to-back", "Meetings")
    if phone:
        # R 3b: the Meetings tabs at 393 are ONE menu Button; open it
        jsclick(page.locator(".desk-window-shell[data-p13-front] [data-testid=p13-strip-wings] .p13-strip-button"))
        f = shoot("C1-2e-strip-menu-open", "Meetings")
        if f is not None:
            rows = [r for m in f["menus"] for r in m["rows"]]
            if not any("OUTCOMES" in r.upper() for r in rows):
                fails.append(f"C1-2e-{width}: the tabs menu does not list OUTCOMES ({rows})")
        page.keyboard.press("Escape")
        settle(300)
    if not phone:
        page.locator(".desk-window-shell[data-p13-front] > .desk-pullout-head .p13-g-zoom").last.click()
        settle(900)
        shoot("C1-2d-zoom", "Meetings")
        page.locator(".desk-window-shell[data-p13-front] > .desk-pullout-head .p13-g-zoom").last.click()
        settle(600)
    close_all()

    # ── C1-3 the material sheet ──
    ev("() => window.__p13.sheet(true)")
    settle(900)
    shoot("C1-3-material-tokens", "Material")
    ev("() => window.__p13.sheet(false)")
    settle(400)

    # ── C1-4 the Chair as windows; R1 the one lifecycle: close, reopen ──
    if phone:
        ev("() => window.__p13.openChair('brief')")
        shoot("C1-4a-chair-windows", "Brief")
        ev("() => window.__p13.openChair('week')")
        shoot("C1-4b-chair-week-open", "The week")
    else:
        ev("() => window.__p13.chairFront('week')")
        shoot("C1-4a-chair-windows", "The week")
        page.locator("[data-testid=p13-chair-brief] .p13-g-zoom").click()
        settle(800)
        shoot("C1-4b-chair-window-zoomed", "Brief")
        page.locator("[data-testid=p13-chair-brief] .p13-g-zoom").click()
        settle(500)
    # close Brief by its close gadget: it is CLOSED (not sent back)
    target = "brief"
    if phone:
        ev("() => window.__p13.openChair('brief')")
        settle(400)
    page.locator(f"[data-testid=p13-chair-{target}] .p13-g-close").click()
    settle(700)
    f = shoot("C1-4c-chair-window-closed", "The week" if phone else None)
    if f is not None and ev("() => !!document.querySelector('[data-testid=p13-chair-brief]')"):
        fails.append(f"C1-4c-{width}: Brief is still open after close")
    if not phone and f is not None and not ev("() => !!document.querySelector('[data-testid=p13-chair-closed-brief] .btn')"):
        fails.append(f"C1-4c-{width}: no reopen Button where Brief was")
    # the Window menu (1440) / Go (393): Chair ▸ with a check on the open ones
    menu_id = "go" if phone else "window"
    btn = page.locator(f".desk-verbbar [data-menu-id={menu_id}] button").first
    btn.click()
    settle(500)
    chair_sub = page.locator("[role=menu] [role=menuitem][aria-haspopup=menu]:has-text('Chair')").first
    (chair_sub.click() if phone else chair_sub.hover())
    settle(700)
    f = shoot("C1-4d-window-menu-chair", None)
    if f is not None:
        rows = [r for m in f["menus"] for r in m["rows"]]
        if not any("Brief" in r for r in rows):
            fails.append(f"C1-4d-{width}: Window ▸ Chair does not list Brief ({rows})")
    page.locator("[role=menu] [role=menuitemcheckbox]:has-text('Brief'), [role=menu] [role=menuitem]:has-text('Brief')").last.click()
    settle(800)
    f = shoot("C1-4e-chair-window-reopened", "Brief")
    page.keyboard.press("Escape")
    ev("() => { window.__p13.openChair('needs'); }")
    settle(400)

    # ── C1-5 Parked and Restore (A1-F) ──
    ev("(s) => window.__p13Open.surface(s)", "review-meetings")
    settle(2500)
    jsclick(page.locator(".desk-window-shell[aria-label='Meetings'] :text('Hiring debrief: staff engineer')"))
    shoot("C1-5a-meeting-selected-park", "Meetings")
    jsclick(page.locator("[data-testid=p13-park]"))
    f = shoot("C1-5b-meeting-parked-receipt", "Meetings")
    if f is not None and "PARKED" not in ev("() => (document.querySelector('[data-testid=p13-park-receipt-meetings]') || {}).innerText || ''"):
        fails.append(f"C1-5b-{width}: no PARKED receipt")
    jsclick(page.locator("[data-testid=p13-parked-meetings] button, [data-testid=p13-parked-meetings] label"))
    shoot("C1-5c-meetings-parked-filter", "Meetings")
    jsclick(page.locator("[data-testid=p13-parked-row] button:has-text('Restore')"))
    settle(600)
    f = shoot("C1-5d-meeting-restored", "Meetings")
    if f is not None:
        rec = ev("() => (document.querySelector('[data-testid=p13-park-receipt-meetings]') || {}).innerText || ''")
        inview = ev("""() => { const e = document.querySelector('[data-p13-restored]'); if (!e) return false; const r = e.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; }""")
        if "RESTORED" not in rec or not inview:
            fails.append(f"C1-5d-{width}: RESTORED receipt {rec!r} / restored row in view {inview}")
    # the Restore failure: park again, the hub refuses the Restore
    jsclick(page.locator(".desk-window-shell[aria-label='Meetings'] :text('Hiring debrief: staff engineer')"))
    jsclick(page.locator("[data-testid=p13-park]"))
    ev("() => window.__p13.failRestore(true)")
    jsclick(page.locator("[data-testid=p13-park-receipt-meetings] button:has-text('Restore')"))
    f = shoot("C1-5e-meeting-restore-failed", "Meetings")
    if f is not None and "NOT RESTORED" not in ev("() => (document.querySelector('[data-testid=p13-park-receipt-meetings]') || {}).innerText || ''"):
        fails.append(f"C1-5e-{width}: no NOT RESTORED receipt with Retry")
    jsclick(page.locator("[data-testid=p13-park-receipt-meetings] button:has-text('Retry')"))
    close_all()
    ev("(r) => window.__p13Open.open(r)", f"workbench:{seed['workbench']}")
    settle(3000)
    wb = page.locator(".desk-window-shell[data-p13-front]").last
    coll = wb.locator("button:has-text('Collapse')")
    if coll.count():
        jsclick(coll)
    jsclick(wb.locator(":text('Old sampling spike')"))
    jsclick(wb.locator("button:has-text('Remove')"))
    f = shoot("C1-5f-workbench-item-parked", "Ledger cutover bench")
    jsclick(page.locator("[data-testid=p13-parked-workbench] button, [data-testid=p13-parked-workbench] label"))
    page.locator("[data-testid=p13-parked-workbench]").first.evaluate("(e) => e.scrollIntoView({block: 'start'})")
    shoot("C1-5g-workbench-parked-filter", "Ledger cutover bench")
    jsclick(page.locator("[data-testid=p13-parked-workbench] [data-testid=p13-parked-row] button:has-text('Restore')"))
    settle(500)
    f = shoot("C1-5h-workbench-item-restored", "Ledger cutover bench")
    if f is not None and "RESTORED" not in ev("() => (document.querySelector('[data-testid=p13-park-receipt-workbench]') || {}).innerText || ''"):
        fails.append(f"C1-5h-{width}: no RESTORED receipt on the Workbench window")
    # a run claims the item between the read and the press: the hub refuses the park
    ev("(t) => window.__p13.claim(t)", "Rerun shard benchmark")
    jsclick(wb.locator(":text('Rerun shard benchmark')"))
    jsclick(wb.locator("button:has-text('Remove')"))
    f = shoot("C1-5i-workbench-claimed-refused", "Ledger cutover bench")
    if f is not None and "CLAIMED" not in ev("() => (document.querySelector('[data-testid=p13-park-receipt-workbench]') || {}).innerText || ''"):
        fails.append(f"C1-5i-{width}: no claimed-item refusal")
    jsclick(page.locator("[data-testid=p13-clear-done]"))
    f = shoot("C1-5j-workbench-clear-done-parked", "Ledger cutover bench")
    if f is not None and "PARKED 2" not in ev("() => (document.querySelector('[data-testid=p13-park-receipt-workbench]') || {}).innerText || ''"):
        fails.append(f"C1-5j-{width}: bulk park receipt is not PARKED 2")
    close_all()

    # ── C1-6 the phone desk ──
    if phone:
        ev("() => window.__p13.openChair('needs')")
        settle(500)
        first_done = ev("""() => { const b = [...document.querySelectorAll('[data-testid=p13-chair-needs] button')].find((e) => e.innerText.trim() === 'Done');
                          if (!b) return null; const r = b.getBoundingClientRect(); const body = b.closest('.p13-chairwin-body').getBoundingClientRect();
                          return { whole: r.top >= body.top && r.bottom <= body.bottom && r.bottom <= innerHeight, top: Math.round(r.top) }; }""")
        f = shoot("C1-6a-phone-desk", "Needs you", extra={"first_done": first_done})
        if f is not None and not (first_done and first_done["whole"]):
            fails.append(f"C1-6a-{width}: the first Done is not whole on the first screen ({first_done})")
        ev("(s) => window.__p13Open.surface(s)", "open-people")
        settle(2500)
        shoot("C1-6b-phone-window-sheet", "People")
        close_all()

    # ── C1-8 the C3 states on the AppIcons ──
    ev("() => window.__p13.openChair('needs')")
    live(tags={"surface-meetings": {"text": "READY 1", "tone": "ok"}, "intelligence:desk": {"text": "SENT 14:02", "tone": "ok"}})
    shoot("C1-8a-dock-ready-and-sent", "Needs you")
    live(tags={"surface-meetings": {"text": "SEND FAILED", "tone": "fail"}, "intelligence:desk": {"text": "UNKNOWN", "tone": "warn"}})
    shoot("C1-8b-dock-send-failed-unknown", "Needs you")
    live(offline="20:24")
    shoot("C1-8c-dock-offline", "Needs you")
    live()

    # ── 3d: the mutation proof (no board; the facts are `_mutation_<width>`) ──
    if not REHEARSE and not ONLY:
        proof = {}
        def caught(tag: str, setup) -> None:
            setup()
            res = ev(MUTATE[tag])
            settle(400)
            ov = ev(OVERLAP)
            pair = lambda h, x, y: (x in h["a"] and y in h["b"]) or (x in h["b"] and y in h["a"])
            target = ev("() => window.__p13MutantTarget || ''")
            want = {"a_sticky": lambda h: "MUTANT A" in h["a"] + h["b"],   # the bar's button over a body row NOT beneath the bar
                    "b_mic": lambda h: h["a"].startswith("Speak") != h["b"].startswith("Speak") and (target[:12] in h["a"] + h["b"] if target else True),   # the mic over ANOTHER field
                    "c_more": lambda h: pair(h, "More AppIcons", "STRAY TEXT")}[tag]
            hit = [h for h in ov["hits"] if want(h)]
            proof[tag] = {"injected": res, "target": ev("() => window.__p13MutantTarget || ''"), "caught": hit[:3], "waived": [w for w in ov["waived"] if "MUTANT" in (w["a"] + w["b"]) or "STRAY" in (w["a"] + w["b"])]}
            ev(UNMUTATE)
            settle(300)
            if res != "ok" or not hit:
                fails.append(f"3d mutation {tag}-{width}: the fence did not catch the injected overlap ({res}, {proof[tag]})")
        if not phone:
            def room():
                close_all(); ev("(p) => window.__p13Open.room(p)", "p-ledger"); settle(3000)
            caught("a_sticky", room)
            def bench():
                close_all(); ev("(r) => window.__p13Open.open(r)", f"workbench:{seed['workbench']}"); settle(3000)
                w = page.locator(".desk-window-shell[data-p13-front]").last
                c = w.locator("button:has-text('Collapse')")
                if c.count():
                    jsclick(c)
                jsclick(w.locator(":text('Draft rollback runbook')"))
            caught("b_mic", bench)
            close_all()
        else:
            caught("c_more", lambda: (close_all(), ev("() => window.__p13.openChair('needs')"), settle(500)))
        facts[f"_mutation_{width}"] = proof
        print("mutation", width, json.dumps(proof)[:600], flush=True)

    # ── C1-7 the comparison (two states) ──
    if not REHEARSE and (not ONLY or ONLY.startswith("C1-7")):
        def pair(tag: str):
            page.screenshot(path=str(SHOTS / f"_cmp-steel-{tag}-{width}.png"))
            facts[f"_cmp_steel_{tag}_{width}"] = {"low_contrast": ev(CONTRAST_ALL)}
            ev("() => window.__p13.theme('honest')")
            settle(900)
            page.screenshot(path=str(SHOTS / f"_cmp-honest-{tag}-{width}.png"))
            facts[f"_cmp_honest_{tag}_{width}"] = {"low_contrast": ev(CONTRAST_ALL)}
            ev("() => window.__p13.theme(null)")
            settle(500)
        ev("() => window.__p13.openChair('needs')")
        settle(600)
        pair("chair")
        ev("(s) => window.__p13Open.surface(s)", "review-meetings")
        settle(2000)
        ev("(p) => window.__p13Open.room(p)", "p-ledger")
        settle(3000)
        pair("windows")
        ev("(s) => window.__p13Open.surface(s)", "open-people")
        settle(2500)
        pair("people")
        close_all()


def compose_comparison() -> None:
    """C1-7: one artboard per width: Steel (top row) and Honest 2.0 (bottom row), each in three states
    (the Chair; two windows; People)."""
    for width, height in WIDTHS:
        tags = ["chair", "windows", "people"]
        if not all((SHOTS / f"_cmp-{d}-{t}-{width}.png").exists() for d in ("steel", "honest") for t in tags):
            continue
        pad = 10 if width > 500 else 3
        row = lambda d: "".join(f'<img src="_cmp-{d}-{t}-{width}.png">' for t in tags)
        html = f"""<!doctype html><html><head><style>
          body {{ margin: 0; background: #3c4454; font: 700 {13 if width > 500 else 12}px 'JetBrains Mono', monospace; color: #0b0c10; }}
          .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: {pad}px; padding: {pad}px; }}
          .cap {{ grid-column: 1 / -1; background: #eef0f3; border: 1px solid #0b0c10; padding: 3px 6px; }}
          .cap.rec {{ background: #6688bb; }}
          img {{ width: 100%; border: 1px solid #0b0c10; display: block; }}
        </style></head><body><div class="grid">
          <div class="cap rec">RECOMMENDED · STEEL</div>{row("steel")}
          <div class="cap">ALTERNATIVE · HONEST 2.0</div>{row("honest")}
        </div></body></html>"""
        page_file = SHOTS / f"_cmp-{width}.html"
        page_file.write_text(html)
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
            pg.goto(page_file.as_uri())
            pg.wait_for_timeout(500)
            pg.screenshot(path=str(SHOTS / f"C1-7-comparison-{width}.png"))
            br.close()
        page_file.unlink()


def main() -> int:
    state = json.loads(Path(os.environ["STACK_STATE"]).read_text()) if os.environ.get("STACK_STATE") else None
    all_fails: list[str] = []
    facts_path = SHOTS / "facts.json"
    facts: dict = json.loads(facts_path.read_text()) if (ONLY or os.environ.get("ONLY_WIDTH")) and facts_path.exists() else {}
    for width, height in WIDTHS:
        fails, f = run(width, height, state)
        all_fails += fails
        facts.update(f)
    if not ONLY or ONLY.startswith("C1-7"):
        compose_comparison()
    facts["_fails"] = all_fails
    facts_path.write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    print("\nFAILS:" if all_fails else "\nALL FENCES HELD", *all_fails, sep="\n  ")
    return 2 if all_fails else 0


if __name__ == "__main__":
    sys.exit(main())
