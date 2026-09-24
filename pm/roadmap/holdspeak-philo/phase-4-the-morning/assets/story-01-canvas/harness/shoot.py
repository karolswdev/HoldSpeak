import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
BOARDS = ["0-today","1-generate-reachable","2a-generating","2b-reading","3a-did-not-generate","3b-did-not-load","3c-generate-after-load-failure","4-next-day-one-decision","5-next-day-several-decisions","6-null-brief","6b-null-brief-did-not-generate","7a-empty-brief","7b-fully-triaged","8a-quiet-generating","8b-quiet-did-not-generate","9-empty-success-receipt"]
# Library-risk probes (Astra r2, condition 3): the REAL DirectoryPullout and
# ConnectionsPane at 393. Each asserts no horizontal overflow and every
# Button's text inside its own box.
LIBS = {"lib-directory": ".surface-section-head", "lib-jira-chip": "[data-testid=connections-jira-conn-c1]"}
FLOOR = 12.0
MEASURE = r"""() => {
  const root = document.querySelector('[data-testid=arrival-brief]');
  const r = root.getBoundingClientRect();
  const btns = [...root.querySelectorAll('.btn')].map(b => {
    const bb = b.getBoundingClientRect();
    const after = getComputedStyle(b, '::after');
    // hit proof: elementFromPoint at center and 4 inset corners of a 44px band centred on the Button
    const cy = bb.top + bb.height/2, cx = bb.left + bb.width/2;
    const pts = [[cx,cy],[bb.left+1,cy-21],[bb.right-1,cy-21],[bb.left+1,cy+21],[bb.right-1,cy+21]];
    const own = pts.map(([x,y]) => { const e = document.elementFromPoint(x,y); return !!e && (e===b || b.contains(e)); });
    return {text: b.textContent.trim(), disabled: b.disabled, w: Math.round(bb.width), painted_h: Math.round(bb.height),
            halo_h: after.height, owns_44_band: own.every(Boolean), text_w: (() => { const rg = document.createRange(); rg.selectNodeContents(b); return Math.round(rg.getBoundingClientRect().width); })(),
            content_w: Math.round(b.clientWidth - parseFloat(getComputedStyle(b).paddingLeft) - parseFloat(getComputedStyle(b).paddingRight)),
            text_fits: (() => { const rg = document.createRange(); rg.selectNodeContents(b); const t = rg.getBoundingClientRect(); return t.left >= bb.left - 0.5 && t.right <= bb.right + 0.5; })()};
  });
  const lines = [...root.querySelectorAll('.surface-receipt-line')].map(s => ({text: s.textContent.trim(), px: getComputedStyle(s).fontSize, tone: s.dataset.tone || null}));
  const rows = [...root.querySelectorAll('[data-testid=arrival-brief-row]')].map(e => { const b = e.getBoundingClientRect(); return {text: e.textContent.replace(/AckDefer$/,'').trim(), top: Math.round(b.top), bottom: Math.round(b.bottom), in_viewport: b.top >= 0 && b.bottom <= innerHeight}; });
  // the 12 px floor: EVERY painted text node in the section, its computed font-size
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const texts = [];
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const t = n.textContent.trim(); if (!t) continue;
    const el = n.parentElement; const cs = getComputedStyle(el);
    const rg = document.createRange(); rg.selectNodeContents(n); const rr = rg.getBoundingClientRect();
    if (cs.visibility === 'hidden' || cs.display === 'none' || rr.width === 0 || rr.height === 0) continue;
    texts.push({text: t, px: parseFloat(cs.fontSize), cls: el.className || el.tagName.toLowerCase()});
  }
  const min_text_px = Math.min(...texts.map(x => x.px));
  const label = root.querySelector('.surface-section-head h3')?.textContent;
  const h3 = root.querySelector('.surface-section-head h3');
  const chip = root.querySelector('.gadget-chip');
  const head = {label_lines: h3 ? Math.round(h3.getBoundingClientRect().height / parseFloat(getComputedStyle(h3).lineHeight || getComputedStyle(h3).fontSize)) : null,
                label_h: h3 ? Math.round(h3.getBoundingClientRect().height) : null,
                chip_h: chip ? Math.round(chip.getBoundingClientRect().height) : null,
                chip_clipped: chip ? chip.scrollWidth > chip.clientWidth : null};
  const raw = [...root.querySelectorAll('button:not(.btn)')].length;
  return {label, head, rows, buttons: btns, lines, texts, min_text_px, floor_ok: min_text_px >= 12, raw_buttons: raw, width: Math.round(r.width), scrollW: document.documentElement.scrollWidth, vw: innerWidth};
}"""
LIB_MEASURE = r"""(sel) => {
  const root = document.querySelector('[data-testid=lib-probe]');
  const box = e => { const b = e.getBoundingClientRect(); return {left: Math.round(b.left), right: Math.round(b.right), w: Math.round(b.width)}; };
  const scrollers = [...root.querySelectorAll('*')].filter(e => e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== 'hidden' && getComputedStyle(e).textOverflow !== 'ellipsis')
    .map(e => ({cls: String(e.className), scrollW: e.scrollWidth, clientW: e.clientWidth}));
  const target = root.querySelector(sel);
  const btns = [...target.querySelectorAll('.btn')].map(b => {
    const bb = b.getBoundingClientRect(); const rg = document.createRange(); rg.selectNodeContents(b); const t = rg.getBoundingClientRect();
    return {text: b.textContent.trim(), w: Math.round(bb.width), text_w: Math.round(t.width),
            content_w: Math.round(b.clientWidth - parseFloat(getComputedStyle(b).paddingLeft) - parseFloat(getComputedStyle(b).paddingRight)),
            text_fits: t.left >= bb.left - 0.5 && t.right <= bb.right + 0.5};
  });
  const chips = [...target.querySelectorAll('.gadget-chip')].map(c => ({text: c.textContent.trim(), ...box(c), scrollW: c.scrollWidth, clientW: c.clientWidth,
    truncated: c.scrollWidth > c.clientWidth, text_overflow: getComputedStyle(c).textOverflow, title: c.title || null}));
  const h3 = target.querySelector('h3');
  const heading = h3 ? {text: h3.textContent, ...box(h3), scrollW: h3.scrollWidth, clientW: h3.clientWidth,
    lines: Math.round(h3.getBoundingClientRect().height / parseFloat(getComputedStyle(h3).lineHeight || getComputedStyle(h3).fontSize))} : null;
  const t = box(target);
  return {target: sel, target_box: t, target_scrollW: target.scrollWidth, target_clientW: target.clientWidth,
          inside_viewport: t.left >= 0 && t.right <= innerWidth, buttons: btns, chips, heading, overflowing_descendants: scrollers,
          scrollW: document.documentElement.scrollWidth, vw: innerWidth,
          no_h_overflow: document.documentElement.scrollWidth <= innerWidth && target.scrollWidth <= target.clientWidth + 1 && scrollers.length === 0};
}"""
facts = {}
with sync_playwright() as p:
    br = p.chromium.launch()
    for w, h in ((1440, 900), (393, 852)):
        ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
        page = ctx.new_page()
        errs = []
        page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        for b in BOARDS:
            page.goto(f"http://127.0.0.1:4417/?board={b}")
            page.wait_for_selector("[data-testid=arrival-brief] .surface-section")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(300)
            page.locator("[data-testid=arrival-brief]").screenshot(path=str(OUT / f"{b}-{w}.png"))
            facts[f"{b}-{w}"] = page.evaluate(MEASURE)
        if w == 393:
            for lib, sel in LIBS.items():
                page.goto(f"http://127.0.0.1:4417/?board={lib}")
                page.wait_for_selector(f"[data-testid=lib-probe] {sel}")
                page.evaluate("document.fonts.ready")
                page.wait_for_timeout(400)
                page.locator(f"[data-testid=lib-probe] {sel}").first.screenshot(path=str(OUT / f"{lib}-{w}.png"))
                facts[f"{lib}-{w}"] = page.evaluate(LIB_MEASURE, sel)
        facts[f"console-errors-{w}"] = errs
        ctx.close()
    br.close()
print(json.dumps(facts, indent=1, ensure_ascii=False))
under = [k for k, v in facts.items() if isinstance(v, dict) and "min_text_px" in v and v["min_text_px"] < FLOOR]
assert not under, f"text under {FLOOR}px in: {under}"
lib_bad = [k for k, v in facts.items() if k.startswith("lib-") and not (v["no_h_overflow"] and v["inside_viewport"] and all(b["text_fits"] for b in v["buttons"]))]
assert not lib_bad, f"library overflow in: {lib_bad}"
