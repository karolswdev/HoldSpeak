"""The type-floor and faint-contrast reader (HS-202-05 M7/M8), shared.

The desk sweep (``test_desk_sweep.py``: its ``floor`` and ``contrast`` fences),
``test_philo13_18_type_floor_glass.py`` and the reader fences
(``test_sweep_readers_glass.py``) read the glass with ``_MEASURE``. It lived in
``test_hs202_05_first_use_type_floor.py`` and
``test_hs202_05_button_hit_ownership.py`` (the hit classifier); the first is
parked (push 2 of the test diet, 2026-10-12: the sweep reads every window at
1440 and 393 with this reader), so the reader lives here, not in a test file.
"""
from __future__ import annotations

from .glass_infra import FOLDED_WORD_JS

# The ONE classifier both HS-202-05 hit readers use. Round 2 of Astra's
# counsel found the live reader calling a BODY hit "covered by a layer in
# front" -- a check that cannot fail proves nothing. A point belongs to
# the Button or it does not; everything else is a MISS, and the label
# says which kind so a layering fact is still distinguishable from a clip.
#
#   own            the Button, or something inside it, answered
#   miss:nothing   elementFromPoint found no element at all
#   miss:body      the body/root (or the Chair's screen, PHILO-14 A1) answered
#                  -- no window paints there, so the halo is absent, not covered
#   miss:ancestor  an ancestor answered -- it CLIPPED the halo
#   miss:sibling   a box in the SAME layer answered -- a neighbour owns it
#   covered        a box in a DIFFERENT layer, in front, answered
#
# Only `own` passes. Only `covered` is a ledger line. The rest fail.
OWNERSHIP_JS = """
  const HS202_LAYER = '.desk-surface-window, .desk-pullout, .desk-window,'
    + ' .desk-next-window, [role=dialog], [role=menu], .desk-dock, .desk-verbbar';
  const hs202Classify = (el, x, y) => {
    const top = document.elementFromPoint(x, y);
    if (!top) return { outcome: 'miss:nothing', owner: null };
    if (top === el || el.contains(top)) return { outcome: 'own', owner: null };
    const owner = top.id
      || (typeof top.className === 'string' && top.className.trim())
      || top.tagName;
    if (top === document.body || top === document.documentElement)
      return { outcome: 'miss:body', owner };
    // PHILO-14 A1: the Chair's screen of objects is the desk's glass, under
    // every window (z 0): a point on it is the body, not a layer in front.
    if (top.closest('.desk-screen') && !el.closest('.desk-screen'))
      return { outcome: 'miss:body', owner };
    if (top.contains(el)) return { outcome: 'miss:ancestor', owner };
    return { outcome: top.closest(HS202_LAYER) === el.closest(HS202_LAYER)
               ? 'miss:sibling' : 'covered', owner };
  };
"""


# The two contrast rules this story owns and gates: the ruling's faint
# gray, and its ember ledger on the faces the first-use path crosses.
# Anything else is printed as measured residue, never swallowed.
GATED_CONTRAST = ("faint", "ember")

# `--text-faint` after the ruling. The rig reads the token from the page
# so it can never drift from design-tokens.json.
_FAINT_JS = "getComputedStyle(document.documentElement).getPropertyValue('--text-faint').trim()"

# The live hit probe, shared by `_MEASURE` and the SELF-TEST so the self-test
# exercises the very path the gate reads (Astra r1, PR #1075).
HIT_PROBE_JS = """
  // The product rule (window-chrome.css scroll-padding-block, PHILO-7-02):
  // a Button is fully hittable once it is scrolled into view. So before the
  // probe, scroll ONLY the containers a user can scroll (overflow auto or
  // scroll, and the page) to bring the Button in, nearest, inside each
  // one's scroll padding. An overflow:hidden box is never scrolled: what it
  // clips stays clipped and fails. Every scroller goes back after the probe.
  const hs202Scrollable = (n, axis) => {
    const o = getComputedStyle(n)[axis === 'y' ? 'overflowY' : 'overflowX'];
    return (o === 'auto' || o === 'scroll')
      && (axis === 'y' ? n.scrollHeight > n.clientHeight : n.scrollWidth > n.clientWidth);
  };
  const hs202Bring = (el, n, viewTop, viewBottom, viewLeft, viewRight) => {
    const cs = getComputedStyle(n);
    const pt = parseFloat(cs.scrollPaddingTop) || 0, pb = parseFloat(cs.scrollPaddingBottom) || 0;
    const pl = parseFloat(cs.scrollPaddingLeft) || 0, pr = parseFloat(cs.scrollPaddingRight) || 0;
    let r = el.getBoundingClientRect();
    if (hs202Scrollable(n, 'y')) {
      if (r.top < viewTop + pt) n.scrollTop -= (viewTop + pt) - r.top;
      else if (r.bottom > viewBottom - pb) n.scrollTop += r.bottom - (viewBottom - pb);
    }
    r = el.getBoundingClientRect();
    if (hs202Scrollable(n, 'x')) {
      if (r.left < viewLeft + pl) n.scrollLeft -= (viewLeft + pl) - r.left;
      else if (r.right > viewRight - pr) n.scrollLeft += r.right - (viewRight - pr);
    }
  };
  const hs202Probe = (el, hit, where) => {
    const doc = document.scrollingElement;
    const saved = [];
    for (let n = el.parentElement; n && n !== doc && n !== document.body; n = n.parentElement)
      if (hs202Scrollable(n, 'y') || hs202Scrollable(n, 'x')) saved.push([n, n.scrollTop, n.scrollLeft]);
    saved.push([doc, doc.scrollTop, doc.scrollLeft]);
    try {
      for (const [n] of saved) {
        if (n === doc) {
          const st = getComputedStyle(doc);
          if (st.overflowY !== 'hidden' && st.overflowX !== 'hidden') hs202BringPage(el);
          continue;
        }
        const nr = n.getBoundingClientRect();
        const top = nr.top + n.clientTop, left = nr.left + n.clientLeft;
        hs202Bring(el, n, top, top + n.clientHeight, left, left + n.clientWidth);
      }
      const r = el.getBoundingClientRect();
      const halfW = Math.max(hit, r.width) / 2, halfH = Math.max(hit, r.height) / 2;
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      const label = (el.textContent || '').trim().slice(0, 24);
      // A Desk window covers the Chair behind it. Those Buttons are in the
      // DOM and laid out, but nothing can reach them and the halo is not
      // what is in their way. ONLY a centre in another layer, in front
      // (`covered`), makes the Button OCCLUDED and outside this probe's
      // claim. A centre lost to a same-layer neighbour, an ancestor clip
      // or the body is a MISS like any other point (Astra r1, PR #1075).
      const centreSeen = hs202Classify(el, cx, cy);
      if (centreSeen.outcome === 'covered') {
        return { label, occluded: true, by: centreSeen.owner,
                 w: Math.round(halfW*2), h: Math.round(halfH*2), covered: [],
                 painted: Math.round(r.height), path: where, bad: [] };
      }
      // The ruling rejects two things: a CLIPPED area, and an adjacent
      // CONTROL owning the same point. A window drawn in front of the
      // Chair is neither -- it is the layer order doing its job. Split
      // the two, so a real clip is never excused and a layering fact is
      // never reported as a hit-area defect.
      const bad = [], covered = [];
      for (const [fx, fy] of [[0,0],[-1,0],[1,0],[0,-1],[0,1],[-1,-1],[1,-1],[-1,1],[1,1]]) {
        const x = cx + fx * (halfW - 1), y = cy + fy * (halfH - 1);
        if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) continue;  // off-screen edge
        const seen = hs202Classify(el, x, y);
        if (seen.outcome === 'own') continue;
        const at = `(${fx},${fy})[${seen.outcome}]->` + seen.owner;
        // ONLY a box in another layer, in front, is coverage. A body hit,
        // an ancestor clip or a neighbour in the same layer is a MISS.
        if (seen.outcome === 'covered') covered.push(at); else bad.push(at);
      }
      return { label, occluded: false, w: Math.round(halfW*2), h: Math.round(halfH*2),
               covered, painted: Math.round(r.height), path: where, bad };
    } finally {
      for (const [n, top, left] of saved) { n.scrollTop = top; n.scrollLeft = left; }
    }
  };
  const hs202BringPage = (el) => {
    const doc = document.scrollingElement;
    const r = el.getBoundingClientRect();
    if (r.top < 0) doc.scrollTop += r.top;
    else if (r.bottom > innerHeight) doc.scrollTop += r.bottom - innerHeight;
    const r2 = el.getBoundingClientRect();
    if (r2.left < 0) doc.scrollLeft += r2.left;
    else if (r2.right > innerWidth) doc.scrollLeft += r2.right - innerWidth;
  };
"""

# The M7/M8 reader. Kept deliberately close to the census's own code so a
# number here means the same thing a number in census.json means.
_MEASURE = """(faintHex) => {""" + OWNERSHIP_JS + HIT_PROBE_JS + FOLDED_WORD_JS + """
  const parse = (s) => {
    const m = /rgba?\\(([^)]+)\\)/.exec(s || "");
    if (!m) return null;
    const p = m[1].split(/[,\\s\\/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const hex = (h) => {
    h = h.replace('#','');
    return { r: parseInt(h.slice(0,2),16), g: parseInt(h.slice(2,4),16),
             b: parseInt(h.slice(4,6),16), a: 1 };
  };
  const same = (a, b) => a && b && a.r === b.r && a.g === b.g && a.b === b.b;
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
    return 0.2126*f(c.r) + 0.7152*f(c.g) + 0.0722*f(c.b);
  };
  // Source-over, alpha-correct. The census's own M8 block
  // (`scripts/surface_census_measure.js`, bgOf/over) composites a
  // translucent layer onto a translucent backdrop as if the backdrop
  // were OPAQUE, and then marks the result a:1 -- so a dark chip fill
  // (rgba(0,0,0,.28)) over a white hairline wash (rgba(255,255,255,.035))
  // reads as rgb(184,184,184) instead of the near-black the eye sees.
  // This rig gates on the number, so it does the arithmetic properly and
  // keeps walking until the stack is actually opaque.
  const over = (fg, bg) => {
    const a = fg.a + bg.a * (1 - fg.a);
    if (a <= 0) return { r: 0, g: 0, b: 0, a: 0 };
    return {
      r: (fg.r*fg.a + bg.r*bg.a*(1-fg.a)) / a,
      g: (fg.g*fg.a + bg.g*bg.a*(1-fg.a)) / a,
      b: (fg.b*fg.a + bg.b*bg.a*(1-fg.a)) / a,
      a,
    };
  };
  const path = (el) => {
    const bits = [];
    for (let n = el; n && n.nodeType === 1 && bits.length < 6; n = n.parentElement) {
      let b = n.tagName.toLowerCase();
      if (n.id) { bits.unshift(b + '#' + n.id); break; }
      if (n.className && typeof n.className === 'string')
        b += '.' + n.className.trim().split(/\\s+/).slice(0, 2).join('.');
      bits.unshift(b);
    }
    return bits.join(' > ');
  };
  const ownText = (el) => [...el.childNodes]
    .filter((n) => n.nodeType === 3).map((n) => n.textContent).join('').trim();
  const visible = (el) => {
    const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' &&
           s.display !== 'none' && Number(s.opacity) > 0;
  };

  // PHILO-13-11 (Astra counsel #730): a zero-size word has no box of its
  // own, so `visible` alone never read it; it is a leaf when its parent is
  // visible and it is not hidden (it then meets foldedWord or the floor).
  const zeroWord = (el) => {
    const s = getComputedStyle(el);
    return parseFloat(s.fontSize) === 0 && s.display !== 'none' && s.visibility !== 'hidden'
      && el.parentElement && visible(el.parentElement);
  };
  const leaves = [...document.querySelectorAll('body *')]
    .filter((el) => ownText(el) && (visible(el) || zeroWord(el)));

  // A nontext glyph is exempt from the floor, and only when a readable
  // word or an accessible name says the same thing. A word or a number
  // is never a glyph.
  const GLYPH = /^[^\\p{L}\\p{N}]+$/u;
  const named = (el) => {
    const host = el.closest('[aria-label],[title],button,a,[role=button]');
    if (!host) return null;
    const label = host.getAttribute('aria-label') || host.getAttribute('title') || '';
    const text = (host.textContent || '').trim();
    const word = (label || text).replace(/[^\\p{L}\\p{N}]/gu, '');
    return word ? (label || text) : null;
  };

  const faint = hex(faintHex);
  // EVERY accent fill, read from the running token layer so the list can
  // never drift from design-tokens.json. Round 2 of Astra's counsel: the
  // hardcoded list predated --accent-ink and --accent-ink-press, so a
  // 2.27:1 pair on the NEW plate fell into ungated `other`.
  const rootCs = getComputedStyle(document.documentElement);
  const EMBER = ['--accent', '--accent-hover', '--accent-press', '--accent-ink',
                 '--accent-ink-hover', '--accent-ink-press',
                 '--p-color-orange-300']
    .map((n) => rootCs.getPropertyValue(n).trim())
    .filter((v) => /^#[0-9a-f]{6}$/i.test(v));
  const small = [], contrast = [];
  for (const el of leaves) {
    const cs = getComputedStyle(el);
    const text = ownText(el);
    const size = parseFloat(cs.fontSize);

    // PHILO-13-11 (C1, §4 393): a word folded into one of the screen bar's
    // picture controls (glass_infra.FOLDED_WORD_JS, narrowed after Astra's
    // counsel on #730). Any other text under 12 px still fails.
    if (foldedWord(el, text)) continue;
    if (size < 12) {
      const glyph = GLYPH.test(text);
      const alt = glyph ? named(el) : null;
      if (!glyph || !alt) {
        // The signature is the consumer, not the instance: the element's
        // own classes (or its tag) plus the computed size. A face that
        // repeats one styled span twenty times is ONE ledger line.
        // HS-202-03 adds a `btn--chrome` marker to the Buttons that
        // replace today's raw wing tabs, menu rows and dock chips. It
        // marks a species, not a size, so it must not mint twelve new
        // ledger signatures on the combined revision. Drop that ONE
        // marker; every other class and the size stay part of the key.
        const cls = (el.className && typeof el.className === 'string')
          ? '.' + el.className.trim().split(/\s+/)
                    .filter((c) => c !== 'btn--chrome').join('.')
          : el.tagName.toLowerCase();
        small.push({ sig: cls + '@' + Math.round(size*100)/100 + 'px',
                     path: path(el), px: Math.round(size*100)/100,
                     text: text.slice(0, 40), glyph, alt });
      }
    }

    const fg = parse(cs.color);
    if (!fg) continue;
    // PHILO-17 (the desk sweep, sweepreds r2): text that is not drawn (a
    // zero-size glyph in a transparent ink: the StateChip lamp keeps its
    // glyph in the DOM, state-chip.css) has no contrast to read; it read as
    // 1:1 on the lit lamp. The floor rule above still reads it.
    if (size === 0 || fg.a === 0) continue;
    let painted = false, bg = null;
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const bi = getComputedStyle(n).backgroundImage;
      if (bi && bi !== 'none') { painted = true; break; }
      const bc = parse(getComputedStyle(n).backgroundColor);
      if (bc && bc.a > 0) { bg = bg ? over(bg, bc) : bc; if (bg.a >= 0.999) break; }
    }
    if (painted) continue;                    // the census skips these too
    // Census parity (`scripts/surface_census_measure.js`, bgOf): a body
    // whose own background is TRANSPARENT is not a ground. Falling back
    // to it paints every composite against rgb(0,0,0) and invents
    // ratios. White is the base the census uses in that case.
    const pageBg = parse(getComputedStyle(document.body).backgroundColor);
    const page = pageBg && pageBg.a > 0 ? pageBg : {r:255,g:255,b:255,a:1};
    bg = !bg ? page : (bg.a < 1 ? over(bg, page) : bg);
    const eff = fg.a < 1 ? over(fg, bg) : fg;
    const l1 = lum(eff), l2 = lum(bg);
    const ratio = (Math.max(l1,l2)+0.05) / (Math.min(l1,l2)+0.05);
    const bold = parseInt(cs.fontWeight, 10) >= 700;
    const need = (size >= 24 || (bold && size >= 18.66)) ? 3 : 4.5;
    if (ratio < need) {
      // Which rule owns this observation: the ruling's faint gray, the
      // ruling's ember ledger, or neither.
      const isFaint = same(fg, faint);
      const onEmber = EMBER.some((e) => same(bg, hex(e)));
      const inEmber = EMBER.some((e) => same(fg, hex(e)));
      // The composited ground is a derived number; record the chain that
      // produced it so a reader can tell a real defect from a bad read.
      const chain = [];
      for (let n = el; n && n.nodeType === 1 && chain.length < 10; n = n.parentElement) {
        const bc = getComputedStyle(n).backgroundColor;
        const c = parse(bc);
        if (c && c.a > 0) chain.push((n.className && typeof n.className === 'string'
          ? '.' + n.className.trim().split(/\s+/)[0] : n.tagName.toLowerCase()) + '=' + bc);
        if (c && c.a >= 0.999) break;
      }
      contrast.push({ path: path(el), ratio: Math.round(ratio*100)/100, need,
                      px: Math.round(size*10)/10, text: text.slice(0, 40),
                      kind: isFaint ? 'faint' : (onEmber || inEmber ? 'ember' : 'other'),
                      fg: cs.color, chain: chain.join(' < '),
                      bg: `rgb(${Math.round(bg.r)}, ${Math.round(bg.g)}, ${Math.round(bg.b)})` });
    }
  }
  // ── the hit contract, in the REAL layout (393 only) ──────────────
  //
  // The isolated fixture proves the CSS; it cannot prove that a live
  // face leaves the halo unclipped or that no neighbour steals a point.
  // This pass runs `elementFromPoint` over the nine points of every
  // visible plated Button ON THE SCREEN ITSELF. It does NOT click:
  // a real pointer on a live first-use face would fire real verbs, and
  // the pointer half of the proof belongs to the fixture rig.
  //
  // Chrome-variant Buttons (menu rows, wing tabs, dock chips) carry no
  // plate, so they take their target from the strip's own row height.
  // Those are measured, not probed.
  const plated = [], chromeRows = [];
  if (innerWidth <= 420) {
    const hit = parseFloat(
      getComputedStyle(document.documentElement).getPropertyValue('--desk-button-hit-size')) || 44;
    for (const el of document.querySelectorAll('.btn')) {
      if (!visible(el)) continue;
      const r0 = el.getBoundingClientRect();
      if (r0.bottom <= 0 || r0.top >= innerHeight || r0.right <= 0 || r0.left >= innerWidth) continue;
      plated.push(hs202Probe(el, hit, path(el)));
    }
    // The chrome strips this product actually has at 393.
    for (const [kind, sel] of [
        ['wing tab', '.desk-wings-tabs > button'],
        ['dock chip', '.desk-dock button'],
        ['menu row', '[role=menuitem]'],
    ]) {
      for (const el of document.querySelectorAll(sel)) {
        if (!visible(el)) continue;
        const r = el.getBoundingClientRect();
        chromeRows.push({ kind, label: (el.getAttribute('aria-label')
          || el.textContent || '').trim().slice(0, 24),
          h: Math.round(r.height * 10) / 10, path: path(el) });
      }
    }
  }

  return { leaves: leaves.length, small, contrast, plated, chromeRows };
}"""
