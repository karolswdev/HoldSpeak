"""Shoot every board at 1440x900 and 393x852 and record rendered facts.

Starts vite on 127.0.0.1:4442 with harness/vite.config.mjs (from web/), then
shoots. Usage (repo root):
  PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/ms-playwright \
    uv run --extra test python <canvas>/harness/shoot.py [a|b ...]

Per board and width, shots/facts.json records the rows, chips, verbs, the foot,
the receipt well, and the measurements:
- `small_text`: every painted text node in the WHOLE Settings window under
  12 px (a lone non-text glyph is exempt, UX-CANON C);
- `raw_buttons`: <button> elements without the library `.btn` class;
- `contrast`: every chip and token (StateChip, surface-token, gadget-fact,
  Receipt): its text colour against the background composited from its
  ancestors (WCAG 2 ratio);
- `pointer`: every Button in the body and footer, centre + four corners inset
  1 px (the painted face at 1440; the 44 x 44 target at 393), each checked by
  elementFromPoint AND a real pointer move;
- horizontal overflow.
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
CANVAS = HERE.parent
REPO = CANVAS.parents[5]
WEB = REPO / "web"
OUT = CANVAS / "shots"
SETS = sys.argv[1:] or ["a", "b"]
BOARDS = ("0-today", "1-never", "2-live", "3-live-open", "4-stopped", "5-expired",
          "6-orphan", "7-orphan-off", "7b-off-credential", "8-refused", "9-two-projects")
BASE = "http://127.0.0.1:4442"

FACTS = """() => {
  const win = document.querySelector('.grant-canvas-window');
  const body = document.querySelector('[data-testid=settings-body]');
  const txt = (e) => (e?.innerText ?? '').replace(/\\s+/g, ' ').trim();
  const rows = [...document.querySelectorAll('.surface-ledger-row')].map(r => ({
    text: txt(r.querySelector('.surface-ledger-line')),
    nested: !!r.parentElement.closest('.surface-ledger-open'),
    open: r.dataset.open === 'true' || r.hasAttribute('data-open'),
    verbs: [...r.querySelector('.surface-ledger-line').querySelectorAll('.surface-ledger-trailing button')].map(b => ({text: b.innerText, species: b.className.trim()})),
    refused_code: r.querySelector(':scope > .surface-ledger-line [data-testid=grant-refused]')?.dataset.code ?? null,
  }));
  const small = [];
  const walker = document.createTreeWalker(win, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const t = n.textContent.trim();
    if (!t || /^[●○✓✗⚠—↻ℹ«»·]$/.test(t)) continue;
    const el = n.parentElement;
    const r = el.getBoundingClientRect();
    if (!r.width || getComputedStyle(el).visibility === 'hidden') continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 12) small.push({text: t.slice(0, 40), fs, cls: String(el.className)});
  }
  // WCAG contrast of every chip / token against its composited background.
  const parse = (c) => { const m = c.match(/[\\d.]+/g) || []; return {r:+m[0]||0, g:+m[1]||0, b:+m[2]||0, a: m[3] === undefined ? 1 : +m[3]}; };
  const blend = (top, under) => ({r: top.r*top.a + under.r*(1-top.a), g: top.g*top.a + under.g*(1-top.a), b: top.b*top.a + under.b*(1-top.a), a: 1});
  const bgOf = (el) => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const c = parse(getComputedStyle(e).backgroundColor);
      if (c.a > 0) { layers.push(c); if (c.a >= 1) break; }
    }
    let acc = {r: 0, g: 0, b: 0, a: 1};
    for (let i = layers.length - 1; i >= 0; i--) acc = blend(layers[i], acc);
    return acc;
  };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v/12.92 : ((v+0.055)/1.055)**2.4; }; return 0.2126*f(c.r)+0.7152*f(c.g)+0.0722*f(c.b); };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return +((x + 0.05) / (y + 0.05)).toFixed(2); };
  const contrast = [];
  for (const el of win.querySelectorAll('.surface-state-chip, .surface-token, .gadget-fact, .surface-receipt, .surface-ledger-count')) {
    const r = el.getBoundingClientRect();
    if (!r.width || !txt(el)) continue;
    // measure the element that paints the words (the deepest with text)
    let paint = el;
    const inner = [...el.querySelectorAll('*')].filter(c => c.childNodes.length && [...c.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()));
    if (!([...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) && inner.length) paint = inner[inner.length - 1];
    const fg = parse(getComputedStyle(paint).color);
    const bg = bgOf(paint);
    const fgc = fg.a < 1 ? blend(fg, bg) : fg;
    contrast.push({text: txt(el).slice(0, 40), cls: String(el.className).split(' ')[0], ratio: ratio(fgc, bg),
                   fs: parseFloat(getComputedStyle(paint).fontSize)});
  }
  const well = document.querySelector('[data-testid=grant-receipt]');
  return {
    caption: txt(document.querySelector('.surface-ledger-count')) || null,
    rows,
    ledger_present: !!document.querySelector('.surface-ledger'),
    receipt_well: well ? {text: txt(well), operation_id: well.dataset.operationId, outcome: well.dataset.outcome, code: well.dataset.code ?? null} : null,
    foot: txt(document.querySelector('.desk-surface-foot')) || null,
    small_text: small,
    raw_buttons: [...win.querySelectorAll('button')].filter(b => !String(b.className).includes('btn')).map(b => txt(b) || b.getAttribute('aria-label')),
    contrast,
    scroll_width: document.documentElement.scrollWidth,
    body_overflow_x: body ? body.scrollWidth > body.clientWidth : null,
  };
}"""

POINTS = """([width]) => {
  const win = document.querySelector('.grant-canvas-window');
  const btns = [...win.querySelectorAll('.desk-surface-body .btn, .desk-surface-foot .btn')];
  return btns.map((b, i) => {
    b.dataset.probe = String(i);
    b.scrollIntoView({block: 'center'});
    const r = b.getBoundingClientRect();
    const cy = r.top + r.height / 2;
    const box = width <= 420 ? {l: r.left, r: r.right, t: cy - 22, b: cy + 22} : {l: r.left, r: r.right, t: r.top, b: r.bottom};
    return {
      i, text: b.innerText.replace(/\\s+/g, ' ').trim(), in_foot: !!b.closest('.desk-surface-foot'),
      face: {w: +r.width.toFixed(2), h: +r.height.toFixed(2)},
      target: {w: +(box.r - box.l).toFixed(2), h: +(box.b - box.t).toFixed(2)},
      points: [[(box.l + box.r) / 2, cy], [box.l + 1, box.t + 1], [box.r - 1, box.t + 1], [box.l + 1, box.b - 1], [box.r - 1, box.b - 1]],
    };
  });
}"""

HIT = """([i, x, y]) => {
  const b = document.querySelector(`[data-probe="${i}"]`);
  const el = document.elementFromPoint(x, y);
  return {ok: !!el && b.contains(el), hit: el ? (typeof el.className === 'string' && el.className ? el.className.split(' ')[0] : el.tagName) : null};
}"""


def wait(url: str, timeout: float = 60) -> None:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=2):
                return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError(f"not up: {url}")


def main() -> None:
    vite = subprocess.Popen([str(WEB / "node_modules/.bin/vite"), "--config", str(HERE / "vite.config.mjs")],
                            cwd=WEB, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    facts, errors = {}, []
    try:
        wait(BASE + "/")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width, height in ((1440, 900), (393, 852)):
                ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2, timezone_id="UTC")
                page = ctx.new_page()
                page.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)
                page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
                for words in SETS:
                    for board in BOARDS:
                        if board == "0-today" and words != SETS[0]:
                            continue
                        page.goto(f"{BASE}/?board={board}&words={words}")
                        page.wait_for_selector(".gadget-group-label")
                        page.evaluate("document.fonts.ready")
                        page.wait_for_timeout(300)
                        name = board if board == "0-today" else f"{board}-{words}"
                        fact = page.evaluate(FACTS)
                        page.evaluate("() => { window.__pm = null; document.addEventListener('pointermove', e => { window.__pm = e.target; }, true); }")
                        pointer = []
                        for probe in page.evaluate(POINTS, [width]):
                            results = []
                            for x, y in probe["points"]:
                                page.evaluate(f"document.querySelector('[data-probe=\"{probe['i']}\"]').scrollIntoView({{block:'center'}})")
                                efp = page.evaluate(HIT, [probe["i"], x, y])
                                page.mouse.move(x, y)
                                real = page.evaluate(f"(() => {{ const b = document.querySelector('[data-probe=\"{probe['i']}\"]'); return !!window.__pm && b.contains(window.__pm); }})()")
                                results.append({"x": round(x, 1), "y": round(y, 1), "efp": efp["ok"], "pointer": real, "hit": efp["hit"]})
                            pointer.append({k: probe[k] for k in ("text", "in_foot", "face", "target")} | {
                                "owned": all(r["efp"] and r["pointer"] for r in results), "points": results})
                        page.mouse.move(0, 0)
                        fact["pointer"] = pointer
                        # The shot: the Remote access group from its top; when the
                        # board has an open expansion or receipt well that the
                        # window cannot hold, scroll so its end is in view.
                        page.evaluate("""() => {
                          const g=[...document.querySelectorAll('.gadget-group')].find(g=>g.querySelector('.gadget-group-label')?.textContent==='Remote access');
                          g?.scrollIntoView({block:'start'});
                          const last = document.querySelector('[data-testid=grant-receipt]') || document.querySelector('.surface-ledger-open');
                          const body = document.querySelector('[data-testid=settings-body]');
                          if (last && body && last.getBoundingClientRect().bottom > body.getBoundingClientRect().bottom) last.scrollIntoView({block:'end'});
                        }""")
                        page.wait_for_timeout(120)
                        target = OUT / ("today" if board == "0-today" else words)
                        target.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(target / f"{name}-{width}.png"))
                        facts[f"{name}-{width}"] = fact
                ctx.close()
            browser.close()
    finally:
        vite.terminate()
    low = [(k, c) for k, v in facts.items() for c in v["contrast"] if c["ratio"] < 4.5]
    summary = {
        "renders": len(facts),
        "browser_errors": errors,
        "small_text": {k: v["small_text"] for k, v in facts.items() if v["small_text"]},
        "raw_buttons": {k: v["raw_buttons"] for k, v in facts.items() if v["raw_buttons"]},
        "overflow": [k for k, v in facts.items() if v["scroll_width"] > int(k.rsplit("-", 1)[1]) or v["body_overflow_x"]],
        "chips_measured": sum(len(v["contrast"]) for v in facts.values()),
        "contrast_min": min((c["ratio"] for v in facts.values() for c in v["contrast"]), default=None),
        "contrast_under_4_5": sorted({(c["text"], c["cls"], c["ratio"]) for _, c in low}),
        "buttons_probed": sum(len(v["pointer"]) for v in facts.values()),
        "points_probed": sum(len(p["points"]) for v in facts.values() for p in v["pointer"]),
        "not_owned": [(k, p["text"], [pt["hit"] for pt in p["points"] if not (pt["efp"] and pt["pointer"])]) for k, v in facts.items() for p in v["pointer"] if not p["owned"]],
    }
    (OUT / "facts.json").write_text(json.dumps({"summary": summary, "boards": facts}, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
