"""Shoot every board at 1440 and 393 and record rendered facts.

Run with the harness served on 127.0.0.1:4432 (vite --config harness/vite.config.mjs
from web/). Usage: uv run python shoot.py <out-dir> [a|b ...]
The facts recorded here are the canvas's own checks: every verb is a library
Button (.btn), no text under 12 px, no horizontal overflow, and the rendered
strings of each board.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1])
SETS = sys.argv[2:] or ["a", "b"]
BOARDS = ("0-today", "1-never", "2-live", "3-revoked", "4-expired", "5-orphan",
          "5b-orphan-off", "5c-orphan-expired", "6-refused", "7-empty")

PROBE = """() => {
  const win = document.querySelector('.grant-canvas-window');
  const body = document.querySelector('[data-testid=settings-body]');
  const group = [...document.querySelectorAll('.gadget-group')].find(g => g.querySelector('.gadget-group-label')?.textContent === 'Remote access');
  const rows = [...document.querySelectorAll('.surface-ledger-row')].map(r => ({
    text: r.innerText.replace(/\\s+/g, ' ').trim(),
    grant_chip: r.querySelector('[data-testid=grant-chip]')?.innerText ?? null,
    verbs: [...r.querySelectorAll('.surface-ledger-trailing button')].map(b => ({text: b.innerText, species: b.className})),
    refused_code: r.querySelector('[data-testid=grant-refused]')?.dataset.code ?? null,
    chip_order: [...r.querySelectorAll('.surface-ledger-lead .surface-state-chip, .surface-ledger-line > .surface-state-chip, .surface-ledger-line > span > .surface-state-chip, .surface-ledger-line > .surface-token')].map(c => c.innerText.trim()),
  }));
  const small = [];
  for (const el of (group ? group.querySelectorAll('*') : [])) {
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim() && !/^[●○✓✗⚠—]$/.test(n.textContent.trim()));
    if (!own) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 12) small.push({text: el.textContent.trim().slice(0, 40), fs});
  }
  const rawButtons = [...(group ? group.querySelectorAll('button') : [])].filter(b => !b.className.includes('btn')).length;
  const foot = document.querySelector('.desk-surface-foot');
  return {
    caption: document.querySelector('.surface-ledger-count')?.innerText ?? null,
    rows,
    ledger_present: !!document.querySelector('.surface-ledger'),
    receipt_well: document.querySelector('[data-testid=grant-receipt]')?.innerText.replace(/\\s+/g, ' ') ?? null,
    foot: foot ? foot.innerText.replace(/\\s+/g, ' ').trim() : null,
    small_text: small,
    raw_buttons: rawButtons,
    scroll_width: document.documentElement.scrollWidth,
    window_width: win ? win.getBoundingClientRect().width : null,
    body_overflow_x: body ? body.scrollWidth > body.clientWidth : null,
  };
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
                # Scroll the Settings body so the Remote access group is in view.
                page.evaluate("""() => { const g=[...document.querySelectorAll('.gadget-group')].find(g=>g.querySelector('.gadget-group-label')?.textContent==='Remote access'); g?.scrollIntoView({block:'start'}); }""")
                page.wait_for_timeout(100)
                name = board if board == "0-today" else f"{board}-{words}"
                (OUT / words).mkdir(parents=True, exist_ok=True)
                target = OUT / ("today" if board == "0-today" else words)
                target.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(target / f"{name}-{width}.png"))
                facts[f"{name}-{width}"] = page.evaluate(PROBE)
        ctx.close()
    browser.close()

(OUT / "facts.json").write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n")
(OUT / "browser-errors.json").write_text(json.dumps(errors, indent=2) + "\n")
bad = {k: v for k, v in facts.items() if v["small_text"] or v["raw_buttons"] or v["scroll_width"] > int(k.rsplit("-", 1)[1])}
print(json.dumps({"boards": len(facts), "errors": errors, "violations": bad}, indent=2, ensure_ascii=False))
