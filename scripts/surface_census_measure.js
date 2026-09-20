/* HS-202 THE MEASURED WALK — the in-page measurer.
 *
 * One function, evaluated in the page against a root selector. It takes the
 * numbers the rulebook's section B asks for (docs/internal/surface-inventory-2026-09-20/00-rulebook.md)
 * plus the section-A counts a script can honestly count (U1/U2/U3/U4/A7).
 *
 * Honesty rules baked in:
 *  - a measure this script cannot take returns null, never 0.
 *  - every count carries its evidence (the offending text, the selector path).
 *
 * Loaded and injected by scripts/surface_census_walk.py.
 */
(([rootSelector, width, opts]) => {
  const root =
    (rootSelector && document.querySelector(rootSelector)) ||
    document.querySelector(".desk-next") ||
    document.body;
  const vw = window.innerWidth;
  const vh = window.innerHeight;

  // ── helpers ───────────────────────────────────────────────────────────
  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden") return false;
    if (parseFloat(cs.opacity || "1") < 0.05) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const path = (el) => {
    const bits = [];
    let n = el;
    for (let i = 0; n && n.nodeType === 1 && i < 4; i++) {
      let s = n.tagName.toLowerCase();
      if (n.id) s += "#" + n.id;
      else if (n.className && typeof n.className === "string")
        s += "." + n.className.trim().split(/\s+/).slice(0, 2).join(".");
      bits.unshift(s);
      n = n.parentElement;
    }
    return bits.join(" > ");
  };
  const trim = (s, n) => {
    const t = (s || "").replace(/\s+/g, " ").trim();
    return t.length > n ? t.slice(0, n) + "…" : t;
  };
  const all = Array.from(root.querySelectorAll("*"));
  // A leaf that actually shows type: it owns a non-empty text node.
  const textLeaves = all.filter((el) => {
    if (!visible(el)) return false;
    if (/^(SCRIPT|STYLE|SVG|PATH|NOSCRIPT|TEXTAREA|INPUT|SELECT|OPTION)$/.test(el.tagName))
      return false;
    for (const node of el.childNodes)
      if (node.nodeType === 3 && node.nodeValue.trim().length > 0) return true;
    return false;
  });
  const ownText = (el) => {
    let s = "";
    for (const node of el.childNodes)
      if (node.nodeType === 3) s += node.nodeValue;
    return s.replace(/\s+/g, " ").trim();
  };

  // ── M1 horizontal overflow ────────────────────────────────────────────
  //
  // A window frame's own scrollWidth always exceeds its clientWidth by 3px,
  // because the resize handles are placed 3px OUTSIDE the frame on purpose
  // (`.desk-window-edge-r { right: -3px; width: 6px }`,
  // web/src/desk/components/window-chrome.css:42). That is furniture, not
  // content, so it is named and subtracted: `contentOverflow` is the number
  // that scores M1, and the raw `overflow` is kept beside it.
  const de = document.documentElement;
  const FURNITURE = /desk-window-(edge|corner|grip)/;
  const isFurniture = (el) => {
    for (let n = el; n && n.nodeType === 1 && n !== root; n = n.parentElement) {
      const c = typeof n.className === "string" ? n.className : "";
      if (FURNITURE.test(c)) return true;
    }
    return false;
  };
  const rootRect = root.getBoundingClientRect();
  let contentRight = rootRect.left;
  let widest = null;
  for (const el of all) {
    if (!visible(el) || isFurniture(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0) continue;
    if (r.right > contentRight) {
      contentRight = r.right;
      widest = el;
    }
  }
  const rootStyle = getComputedStyle(root);
  const contentEdge =
    rootRect.left + root.clientWidth + parseFloat(rootStyle.borderLeftWidth || "0");
  const contentOverflow = Math.max(0, Math.round(contentRight - contentEdge));
  const m1 = {
    document: {
      scrollWidth: de.scrollWidth,
      clientWidth: de.clientWidth,
      innerWidth: vw,
      overflow: Math.max(0, de.scrollWidth - vw),
    },
    root: {
      selector: rootSelector || null,
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
      overflow: Math.max(0, root.scrollWidth - root.clientWidth),
      contentOverflow,
      widest:
        contentOverflow > 0 && widest
          ? { path: path(widest), text: trim(widest.textContent, 70) }
          : null,
      furnitureNote:
        root.scrollWidth - root.clientWidth > 0 && contentOverflow === 0
          ? "the raw overflow is the 3px resize-handle affordance (window-chrome.css:42), not content"
          : null,
    },
    // every descendant that scrolls sideways under a clip
    inner: all
      .filter((el) => {
        if (!visible(el)) return false;
        const cs = getComputedStyle(el);
        const clipped = /hidden|clip/.test(cs.overflowX);
        return clipped && el.scrollWidth - el.clientWidth > 2;
      })
      .slice(0, 40)
      .map((el) => ({
        path: path(el),
        by: el.scrollWidth - el.clientWidth,
        text: trim(el.textContent, 70),
      })),
  };

  // ── M2 cut text ───────────────────────────────────────────────────────
  const m2 = [];
  for (const el of all) {
    if (!visible(el)) continue;
    const cs = getComputedStyle(el);
    const ellipsis = cs.textOverflow === "ellipsis";
    const clippedX = /hidden|clip/.test(cs.overflowX);
    const clippedY = /hidden|clip/.test(cs.overflowY);
    const cutX = el.scrollWidth - el.clientWidth > 2 && (clippedX || ellipsis);
    const cutY = el.scrollHeight - el.clientHeight > 2 && clippedY;
    if (!cutX && !cutY) continue;
    const txt = (el.textContent || "").replace(/\s+/g, " ").trim();
    if (!txt) continue;
    // Only report the innermost cut element (a cut parent of a cut child is
    // the same wound reported twice).
    if (el.querySelector("*") && Array.from(el.querySelectorAll("*")).some((c) => {
      const ccs = getComputedStyle(c);
      return (
        (c.scrollWidth - c.clientWidth > 2 &&
          (/hidden|clip/.test(ccs.overflowX) || ccs.textOverflow === "ellipsis")) ||
        (c.scrollHeight - c.clientHeight > 2 && /hidden|clip/.test(ccs.overflowY))
      );
    }))
      continue;
    m2.push({
      path: path(el),
      axis: cutX ? "x" : "y",
      hiddenPx: cutX ? el.scrollWidth - el.clientWidth : el.scrollHeight - el.clientHeight,
      title: el.getAttribute("title") || null,
      text: trim(txt, 120),
    });
  }

  // ── M3 verbs outside their window / the viewport ──────────────────────
  const verbs = all.filter(
    (el) =>
      visible(el) &&
      (el.tagName === "BUTTON" ||
        el.getAttribute("role") === "button" ||
        el.getAttribute("role") === "menuitem" ||
        (el.tagName === "A" && el.getAttribute("href"))),
  );
  const rr = root.getBoundingClientRect();
  // "Its window" means a real window frame. The Chair and a menu are not
  // windows, and their children legitimately paint outside the element's own
  // box (a fixed capture bar, a portalled panel) — counting those would be
  // noise, not a finding.
  const rootIsWindow =
    root !== document.body &&
    (root.classList.contains("desk-window") ||
      root.classList.contains("desk-pullout") ||
      /^surface-/.test(root.id || ""));
  const m3 = [];
  for (const el of verbs) {
    const r = el.getBoundingClientRect();
    const outViewport =
      r.right > vw + 1 || r.left < -1 || r.bottom > vh + 1 || r.top < -1;
    const outWindow =
      rootIsWindow &&
      (r.right > rr.right + 1 || r.left < rr.left - 1 || r.bottom > rr.bottom + 1 || r.top < rr.top - 1);
    if (!outViewport && !outWindow) continue;
    m3.push({
      path: path(el),
      label: trim(el.getAttribute("aria-label") || el.textContent, 50),
      outViewport,
      outWindow,
      rect: [Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)],
    });
  }

  // ── M4 folds, tabs, unsignalled scroll ────────────────────────────────
  const folds = Array.from(root.querySelectorAll(".gadget-fold, details")).map((el) => {
    const open =
      el.tagName === "DETAILS"
        ? el.open
        : !(el.classList.contains("is-closed") || el.getAttribute("data-open") === "false");
    const title =
      trim(
        (el.querySelector(".gadget-fold-title") || el.querySelector("summary") || {}).textContent,
        40,
      ) || null;
    const body = el.querySelector(".gadget-fold-body") || el;
    return { title, open, hides: open ? null : trim(body.textContent, 80) };
  });
  const tablists = Array.from(
    root.querySelectorAll('[role="tablist"], .surface-wings, .mode-tabs, .desk-wings'),
  ).map((el) => {
    const tabs = Array.from(
      el.querySelectorAll('[role="tab"], button'),
    ).map((t) => ({
      label: trim(t.textContent, 30),
      selected:
        t.getAttribute("aria-selected") === "true" ||
        t.classList.contains("is-active") ||
        t.classList.contains("is-on"),
    }));
    return { path: path(el), tabs };
  });
  const scrollers = all
    .filter((el) => {
      if (!visible(el)) return false;
      const cs = getComputedStyle(el);
      return /auto|scroll/.test(cs.overflowY) && el.scrollHeight - el.clientHeight > 24;
    })
    .slice(0, 20)
    .map((el) => ({ path: path(el), hiddenBelowPx: el.scrollHeight - el.clientHeight }));
  const m4 = { folds, tablists, scrollers };

  // ── M5 empty headings / sections / labels ─────────────────────────────
  const m5 = [];
  for (const el of Array.from(
    root.querySelectorAll(
      "h1,h2,h3,h4,h5,h6,.surface-section-head,.gadget-field-label,.surface-identity-name,dt,legend,label",
    ),
  )) {
    if (!visible(el)) continue;
    if ((el.textContent || "").trim() === "") {
      m5.push({ kind: "empty-heading", path: path(el) });
      continue;
    }
    // A label whose value is empty (dt/dd, .gadget-field-label + sibling)
    if (el.tagName === "DT") {
      const dd = el.nextElementSibling;
      if (dd && dd.tagName === "DD" && (dd.textContent || "").trim() === "")
        m5.push({ kind: "label-no-value", path: path(el), label: trim(el.textContent, 40) });
    }
    if (el.classList.contains("gadget-field-label")) {
      const sib = el.nextElementSibling;
      if (sib && (sib.textContent || "").trim() === "")
        m5.push({ kind: "label-no-value", path: path(el), label: trim(el.textContent, 40) });
    }
  }
  for (const el of Array.from(root.querySelectorAll("section,.surface-section,.gadget-card"))) {
    if (!visible(el)) continue;
    const head = el.querySelector(".surface-section-head, h1,h2,h3,h4");
    const rest = (el.textContent || "").replace((head && head.textContent) || "", "").trim();
    if (head && rest === "")
      m5.push({ kind: "empty-section", path: path(el), label: trim(head.textContent, 40) });
  }

  // ── M6 the same FACT stated twice ─────────────────────────────────────
  //
  // A verb label repeated per row ("Open", "Done") is one verb offered on
  // many objects — lawful, and C1 even asks for it. M6 is about a *fact*
  // shown twice, so verb text is counted separately and never scored.
  const inVerb = (el) => {
    for (let n = el; n && n.nodeType === 1; n = n.parentElement)
      if (
        n.tagName === "BUTTON" ||
        n.tagName === "A" ||
        n.getAttribute("role") === "button" ||
        n.getAttribute("role") === "menuitem" ||
        n.getAttribute("role") === "tab" ||
        n.getAttribute("role") === "option"
      )
        return true;
    return false;
  };
  const seen = new Map();
  const seenVerbs = new Map();
  for (const el of textLeaves) {
    const t = ownText(el);
    if (t.length < 4) continue;
    if (/^[\d\s.,:%+\-/]+$/.test(t)) continue; // bare numbers repeat lawfully
    const bucket = inVerb(el) ? seenVerbs : seen;
    const list = bucket.get(t) || [];
    list.push(path(el));
    bucket.set(t, list);
  }
  const m6 = [];
  for (const [text, paths] of seen)
    if (paths.length > 1) m6.push({ text: trim(text, 70), count: paths.length, paths: paths.slice(0, 4) });
  m6.sort((a, b) => b.count - a.count);
  const m6verbs = [];
  for (const [text, paths] of seenVerbs)
    if (paths.length > 1) m6verbs.push({ text: trim(text, 40), count: paths.length });
  m6verbs.sort((a, b) => b.count - a.count);

  // ── M7 type size + touch targets ──────────────────────────────────────
  const small = [];
  for (const el of textLeaves) {
    const size = parseFloat(getComputedStyle(el).fontSize);
    if (size < 12)
      small.push({ path: path(el), px: Math.round(size * 100) / 100, text: trim(ownText(el), 50) });
  }
  const targets = [];
  if (width <= 500) {
    for (const el of verbs) {
      const r = el.getBoundingClientRect();
      if (r.width < 44 || r.height < 44)
        targets.push({
          path: path(el),
          label: trim(el.getAttribute("aria-label") || el.textContent, 40),
          w: Math.round(r.width),
          h: Math.round(r.height),
        });
    }
  }
  const m7 = { smallText: small, smallTargets: width <= 500 ? targets : null };

  // ── M8 contrast ───────────────────────────────────────────────────────
  const parseRGB = (s) => {
    const m = /rgba?\(([^)]+)\)/.exec(s || "");
    if (!m) return null;
    const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const lum = (c) => {
    const f = (v) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const over = (fg, bg) => ({
    r: fg.r * fg.a + bg.r * (1 - fg.a),
    g: fg.g * fg.a + bg.g * (1 - fg.a),
    b: fg.b * fg.a + bg.b * (1 - fg.a),
    a: 1,
  });
  const bgOf = (el) => {
    let n = el;
    let acc = null;
    while (n && n.nodeType === 1) {
      const c = parseRGB(getComputedStyle(n).backgroundColor);
      if (c && c.a > 0) {
        acc = acc ? over(acc, c) : c;
        if (acc.a >= 0.999) return acc;
      }
      n = n.parentElement;
    }
    const page = parseRGB(getComputedStyle(document.body).backgroundColor);
    const base = page && page.a > 0 ? page : { r: 255, g: 255, b: 255, a: 1 };
    return acc ? over(acc, base) : base;
  };
  const m8 = { assessed: 0, fails: [], note: null };
  for (const el of textLeaves) {
    const cs = getComputedStyle(el);
    const fg = parseRGB(cs.color);
    if (!fg) continue;
    // An image/gradient behind the text defeats a computed-colour read: do
    // not guess — count it as not assessed.
    let painted = false;
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const bi = getComputedStyle(n).backgroundImage;
      if (bi && bi !== "none") {
        painted = true;
        break;
      }
      const bc = parseRGB(getComputedStyle(n).backgroundColor);
      if (bc && bc.a >= 0.999) break;
    }
    if (painted) continue;
    const bg = bgOf(el);
    const eff = fg.a < 1 ? over(fg, bg) : fg;
    const l1 = lum(eff);
    const l2 = lum(bg);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    const size = parseFloat(cs.fontSize);
    const bold = parseInt(cs.fontWeight, 10) >= 700;
    const large = size >= 24 || (bold && size >= 18.66);
    const need = large ? 3 : 4.5;
    m8.assessed++;
    if (ratio < need)
      m8.fails.push({
        path: path(el),
        ratio: Math.round(ratio * 100) / 100,
        need,
        px: Math.round(size * 10) / 10,
        fg: cs.color,
        bg: `rgb(${Math.round(bg.r)}, ${Math.round(bg.g)}, ${Math.round(bg.b)})`,
        text: trim(ownText(el), 50),
      });
  }
  m8.fails.sort((a, b) => a.ratio - b.ratio);
  m8.textLeaves = textLeaves.length;
  m8.skippedOverImage = textLeaves.length - m8.assessed;

  // ── M10 font families ─────────────────────────────────────────────────
  const fams = new Map();
  for (const el of textLeaves) {
    const f = getComputedStyle(el).fontFamily;
    fams.set(f, (fams.get(f) || 0) + 1);
  }
  const m10 = Array.from(fams, ([family, count]) => ({ family: trim(family, 90), count })).sort(
    (a, b) => b.count - a.count,
  );

  // ── U1 raw verbs (not the library Button) ─────────────────────────────
  const rawButtons = Array.from(root.querySelectorAll("button")).filter(
    (el) => visible(el) && !el.classList.contains("btn"),
  );
  const rawByFamily = {};
  for (const el of rawButtons) {
    const cls = (typeof el.className === "string" ? el.className : "").trim().split(/\s+/)[0] || "(no class)";
    rawByFamily[cls] = (rawByFamily[cls] || 0) + 1;
  }
  const u1 = {
    rawVisible: rawButtons.length,
    libraryVisible: Array.from(root.querySelectorAll("button.btn")).filter(visible).length,
    byFirstClass: rawByFamily,
    sample: rawButtons.slice(0, 12).map((el) => ({
      path: path(el),
      label: trim(el.getAttribute("aria-label") || el.textContent, 40),
    })),
  };

  // ── U2 modals ─────────────────────────────────────────────────────────
  const u2 = Array.from(
    document.querySelectorAll('dialog[open], [role="dialog"], [role="alertdialog"], [aria-modal="true"]'),
  )
    .filter(visible)
    .map((el) => ({ path: path(el), label: trim(el.getAttribute("aria-label") || el.textContent, 50) }));

  // ── U3 counters of zero ───────────────────────────────────────────────
  const u3 = [];
  for (const el of textLeaves) {
    const t = ownText(el);
    const m = /(^|[^\d.,])0\s+([A-Za-z][A-Za-z-]{2,})/.exec(t);
    if (m) u3.push({ path: path(el), text: trim(t, 60) });
    else if (/^0$/.test(t)) {
      // a bare 0 next to a noun label is the same wound
      const sib = el.previousElementSibling || el.nextElementSibling;
      const lbl = sib ? trim(sib.textContent, 24) : "";
      if (lbl && /^[A-Za-z][A-Za-z \-]{2,}$/.test(lbl))
        u3.push({ path: path(el), text: `0 (beside "${lbl}")` });
    }
  }

  // ── U4 filled primaries ───────────────────────────────────────────────
  const primaries = Array.from(root.querySelectorAll(".btn--primary"))
    .filter(visible)
    .map((el) => ({ path: path(el), label: trim(el.getAttribute("aria-label") || el.textContent, 40) }));

  // ── A7 prose ──────────────────────────────────────────────────────────
  const proseExempt = (el) => {
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const c = typeof n.className === "string" ? n.className : "";
      if (/note|transcript|editor|prosemirror|cm-|markdown|summary-body|thread-row|message|dossier|docs|runtime-doc/i.test(c))
        return true;
      if (n.tagName === "PRE" || n.tagName === "CODE") return true;
    }
    return false;
  };
  const a7 = [];
  for (const el of textLeaves) {
    if (proseExempt(el)) continue;
    const t = ownText(el);
    for (const sentence of t.split(/(?<=[.!?])\s+/)) {
      const words = sentence.trim().split(/\s+/).filter(Boolean);
      if (words.length > 12 && /[.!?]$/.test(sentence.trim()))
        a7.push({ path: path(el), words: words.length, text: trim(sentence, 140) });
    }
  }

  // ── the shape of the surface (for the report's context) ───────────────
  const shape = {
    visibleElements: all.filter(visible).length,
    textLeaves: textLeaves.length,
    verbs: verbs.length,
    inputs: Array.from(root.querySelectorAll("input,textarea,select")).filter(visible).length,
    emptyState: Boolean(root.querySelector('.surface-state[data-kind="empty"]')),
    loadingState: Boolean(root.querySelector('.surface-state[data-kind="loading"]')),
    errorState: Boolean(root.querySelector('.surface-state[data-kind="error"]')),
    headline: trim(
      (root.querySelector(".desk-window-title, .surface-identity-name, h1, h2") || {}).textContent,
      60,
    ),
  };

  return {
    width,
    rootFound: Boolean(rootSelector && document.querySelector(rootSelector)),
    shape,
    M1: m1,
    M2: m2,
    M3: m3,
    M4: m4,
    M5: m5,
    M6: m6,
    M6_repeated_verbs: m6verbs,
    M7: m7,
    M8: m8,
    M10: m10,
    U1: u1,
    U2: u2,
    U3: u3,
    U4: primaries,
    A7: a7,
  };
})
