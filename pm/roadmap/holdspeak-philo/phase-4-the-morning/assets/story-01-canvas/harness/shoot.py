import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
BOARDS = ["0-today","1-generate-reachable","2a-generating","2b-reading","3a-did-not-generate","3b-did-not-load","4-next-day-one-decision","5-next-day-several-decisions"]
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
            halo_h: after.height, owns_44_band: own.every(Boolean)};
  });
  const lines = [...root.querySelectorAll('.surface-receipt-line')].map(s => ({text: s.textContent.trim(), px: getComputedStyle(s).fontSize, tone: s.dataset.tone || null}));
  const rows = [...root.querySelectorAll('[data-testid=arrival-brief-row]')].map(e => { const b = e.getBoundingClientRect(); return {text: e.textContent.replace(/AckDefer$/,'').trim(), top: Math.round(b.top), bottom: Math.round(b.bottom), in_viewport: b.top >= 0 && b.bottom <= innerHeight}; });
  const label = root.querySelector('.surface-section-head h3')?.textContent;
  const raw = [...root.querySelectorAll('button:not(.btn)')].length;
  return {label, rows, buttons: btns, lines, raw_buttons: raw, width: Math.round(r.width), scrollW: document.documentElement.scrollWidth, vw: innerWidth};
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
        facts[f"console-errors-{w}"] = errs
        ctx.close()
    br.close()
print(json.dumps(facts, indent=1, ensure_ascii=False))
