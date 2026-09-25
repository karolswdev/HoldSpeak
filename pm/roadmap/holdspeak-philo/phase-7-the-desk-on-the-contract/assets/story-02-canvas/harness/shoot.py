"""Shoot every board at 1440 and 393 and record rendered facts.

Run with the harness served on 127.0.0.1:4432 (vite --config harness/vite.config.mjs
from web/). Usage: uv run python shoot.py <out-dir> [a|b ...]

Per board and width, facts.json records:
- the caption, each row's text, grant chip, verbs (with the Button species
  class), refusal code and cell order; the foot; the receipt well;
- `small_text`: every painted text node in the WHOLE Settings window (body,
  head and footer) under 12 px (a lone non-text glyph is exempt, UX-CANON C);
- `pointer`: for every Button in the window body and footer, the probe points
  (1440: the painted face's centre and four corners inset 1 px; 393: the
  44 x 44 target, centre and four corners inset 1 px, per UX-CANON C) with
  `elementFromPoint` AND a real pointer move (the pointermove target), each
  checked to land inside that Button;
- raw buttons and horizontal overflow.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1])
SETS = sys.argv[2:] or ["a", "b"]
BOARDS = ("0-today", "1-never", "2-live", "3-revoked", "4-expired", "4b-cred-expired",
          "5-orphan", "5b-orphan-off", "5c-orphan-expired", "5d-off-credential",
          "6-refused", "6b-refused-gone", "7-empty")

FACTS = """() => {
  const win = document.querySelector('.grant-canvas-window');
  const body = document.querySelector('[data-testid=settings-body]');
  const rows = [...document.querySelectorAll('.surface-ledger-row')].map(r => ({
    text: r.innerText.replace(/\\s+/g, ' ').trim(),
    grant_chip: r.querySelector('[data-testid=grant-chip]')?.innerText.replace(/\\s+/g, ' ') ?? null,
    verbs: [...r.querySelectorAll('.surface-ledger-trailing button')].map(b => ({text: b.innerText, species: b.className.trim()})),
    refused_code: r.querySelector('[data-testid=grant-refused]')?.dataset.code ?? null,
    cells: [...r.querySelector('.surface-ledger-line').children].map(c => c.innerText.replace(/\\s+/g, ' ').trim()),
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
    if (fs < 12) small.push({text: t.slice(0, 40), fs, cls: el.className});
  }
  const well = document.querySelector('[data-testid=grant-receipt]');
  return {
    caption: document.querySelector('.surface-ledger-count')?.innerText ?? null,
    rows,
    ledger_present: !!document.querySelector('.surface-ledger'),
    receipt_well: well ? {text: well.innerText.replace(/\\s+/g, ' '), operation_id: well.dataset.operationId, outcome: well.dataset.outcome, code: well.dataset.code ?? null} : null,
    foot: document.querySelector('.desk-surface-foot')?.innerText.replace(/\\s+/g, ' ').trim() ?? null,
    small_text: small,
    raw_buttons: [...win.querySelectorAll('button')].filter(b => !b.className.includes('btn')).length,
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
    const box = width <= 420
      ? {l: r.left, r: r.right, t: cy - 22, b: cy + 22}
      : {l: r.left, r: r.right, t: r.top, b: r.bottom};
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
  return {ok: !!el && b.contains(el), hit: el ? (el.className && typeof el.className === 'string' ? el.className.split(' ')[0] : el.tagName) : null};
}"""

facts, errors = {}, []
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for width, height in ((1440, 900), (393, 852)):
        ctx = browser.new_context(viewport={"width": width, "height": height},
                                  device_scale_factor=2, timezone_id="UTC")
        page = ctx.new_page()
        page.on("console", lambda m: errors.append(f"console: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        for words in SETS:
            for board in BOARDS:
                if board == "0-today" and words != SETS[0]:
                    continue
                page.goto(f"http://127.0.0.1:4432/?board={board}&words={words}")
                page.wait_for_selector(".gadget-group-label")
                page.evaluate("document.fonts.ready")
                page.wait_for_timeout(250)
                name = board if board == "0-today" else f"{board}-{words}"
                fact = page.evaluate(FACTS)
                # Pointer ownership (the probe scrolls; the shot is taken after).
                page.evaluate("""() => { window.__pm = null; document.addEventListener('pointermove', e => { window.__pm = e.target; }, true); }""")
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
                page.evaluate("""() => { const g=[...document.querySelectorAll('.gadget-group')].find(g=>g.querySelector('.gadget-group-label')?.textContent==='Remote access'); g?.scrollIntoView({block:'start'}); }""")
                page.wait_for_timeout(100)
                target = OUT / ("today" if board == "0-today" else words)
                target.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(target / f"{name}-{width}.png"))
                facts[f"{name}-{width}"] = fact
        ctx.close()
    browser.close()

(OUT / "facts.json").write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n")
(OUT / "browser-errors.json").write_text(json.dumps(errors, indent=2) + "\n")
summary = {
    "renders": len(facts),
    "browser_errors": errors,
    "small_text": {k: v["small_text"] for k, v in facts.items() if v["small_text"]},
    "raw_buttons": sum(v["raw_buttons"] for v in facts.values()),
    "overflow": [k for k, v in facts.items() if v["scroll_width"] > int(k.rsplit("-", 1)[1]) or v["body_overflow_x"]],
    "buttons_probed": sum(len(v["pointer"]) for v in facts.values()),
    "points_probed": sum(len(p["points"]) for v in facts.values() for p in v["pointer"]),
    "not_owned": [(k, p["text"], [pt for pt in p["points"] if not (pt["efp"] and pt["pointer"])]) for k, v in facts.items() for p in v["pointer"] if not p["owned"]],
}
print(json.dumps(summary, indent=2, ensure_ascii=False))
