"""Shoot the PHILO-4-04 proposal boards at the two required widths.

Run from this harness directory after starting Vite:
  python shoot.py <output-directory>

The output is scratch evidence for the orchestrator. The harness itself does
not alter product files or the roadmap.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
BOARDS = [
    "7a-empty-original",
    "7b-fully-triaged-original",
    "7c-one-line-proposed",
    "7b-fully-triaged-proposed",
    "8a-quiet-generating-proposed",
    "8b-quiet-failed-proposed",
    "9-same-day-success-proposed",
]
PROPOSED = {
    "7c-one-line-proposed",
    "7b-fully-triaged-proposed",
    "8a-quiet-generating-proposed",
    "8b-quiet-failed-proposed",
    "9-same-day-success-proposed",
}
SNAPSHOT_PROPOSED = {
    "7b-fully-triaged-proposed",
    "8a-quiet-generating-proposed",
    "8b-quiet-failed-proposed",
    "9-same-day-success-proposed",
}
STORED_HEADLINE = "1 thing changed, 3 things waiting, 2 decisions waiting."
DATE_LINE = "SEP 21 – 23 · GENERATED SEP 23 17:40"
SNAPSHOT = "SNAPSHOT · SEP 21 – 23 · GENERATED SEP 23 17:40"
HANDLED = "ALL 6 HANDLED"

MEASURE = r"""() => {
  const root = document.querySelector('[data-testid=arrival-brief]');
  const section = root.querySelector('.surface-section');
  const buttons = [...section.querySelectorAll('.btn')].map((button) => {
    const box = button.getBoundingClientRect();
    const range = document.createRange();
    range.selectNodeContents(button);
    const text = range.getBoundingClientRect();
    return {
      text: button.textContent.trim(),
      disabled: button.disabled,
      width: Math.round(box.width),
      text_fits: text.left >= box.left - .5 && text.right <= box.right + .5,
    };
  });
  const textNodes = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    if (!node.textContent.trim()) continue;
    const style = getComputedStyle(node.parentElement);
    if (style.display === 'none' || style.visibility === 'hidden') continue;
    textNodes.push({ text: node.textContent.trim(), px: parseFloat(style.fontSize) });
  }
  return {
    label: section.querySelector('h3')?.textContent ?? null,
    headline: root.querySelector('[data-testid=arrival-brief-headline]')?.textContent ?? null,
    snapshot: root.querySelector('[data-canvas-snapshot]')?.textContent ?? null,
    handled: root.querySelector('[data-testid=arrival-brief-handled]')?.textContent ?? null,
    date: root.querySelector('[data-testid=arrival-brief-date]')?.textContent ?? null,
    generating: !!root.querySelector('[data-testid=arrival-brief-generating]'),
    failed: !!root.querySelector('[data-testid=arrival-brief-generate-failed]'),
    receipts: [...root.querySelectorAll('[role=status]')].map((line) => line.textContent.trim()),
    marker_before_headline: (() => {
      const marker = root.querySelector('[data-canvas-snapshot]');
      const headline = root.querySelector('[data-testid=arrival-brief-headline]');
      return !!marker && !!headline && !!(marker.compareDocumentPosition(headline) & Node.DOCUMENT_POSITION_FOLLOWING);
    })(),
    handled_role: root.querySelector('[data-testid=arrival-brief-handled]')?.getAttribute('role') ?? null,
    raw_buttons: root.querySelectorAll('button:not(.btn)').length,
    has_zero_brief_counter: /BRIEF\s*·\s*0/.test(root.textContent),
    buttons,
    min_text_px: Math.min(...textNodes.map(({ px }) => px)),
    section_width: Math.round(section.getBoundingClientRect().width),
    scrollW: document.documentElement.scrollWidth,
    vw: innerWidth,
  };
}"""

facts = {}
browser_errors = []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    for width, height in ((1440, 900), (393, 852)):
        context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2)
        page = context.new_page()
        page.on("console", lambda message: browser_errors.append(f"console: {message.text}") if message.type == "error" else None)
        page.on("pageerror", lambda error: browser_errors.append(f"pageerror: {error}"))
        for board in BOARDS:
            page.goto(f"http://127.0.0.1:4424/?board={board}")
            page.wait_for_selector("[data-testid=arrival-brief] .surface-section")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(250)
            page.locator("[data-testid=arrival-brief]").screenshot(path=str(OUT / f"{board}-{width}.png"))
            facts[f"{board}-{width}"] = page.evaluate(MEASURE)
        context.close()
    browser.close()

(OUT / "facts.json").write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(facts, indent=2, ensure_ascii=False))
print(json.dumps({"browser_errors": browser_errors}, indent=2, ensure_ascii=False))

bad = [key for key, fact in facts.items() if (
    fact["scrollW"] > fact["vw"]
    or fact["min_text_px"] < 12
    or fact["raw_buttons"] != 0
    or fact["has_zero_brief_counter"]
    or not all(button["text_fits"] for button in fact["buttons"])
)]
assert not bad, f"canvas geometry/text failure: {bad}"
assert not browser_errors, f"browser errors: {browser_errors}"
for key in PROPOSED:
    for width in (1440, 393):
        fact = facts[f"{key}-{width}"]
        assert fact["headline"] == STORED_HEADLINE, f"stored headline changed: {key}-{width}"
        assert fact["handled"] == HANDLED, f"handled receipt missing: {key}-{width}"
        assert fact["handled_role"] is None, f"durable handled line must stay a plain receipt: {key}-{width}"
        if key in SNAPSHOT_PROPOSED:
            assert fact["snapshot"] == SNAPSHOT, f"snapshot marker changed: {key}-{width}"
            assert fact["date"] == SNAPSHOT, f"snapshot date testid changed: {key}-{width}"
            assert fact["marker_before_headline"], f"snapshot marker must precede headline: {key}-{width}"
        else:
            assert fact["snapshot"] is None, f"one-line option gained snapshot copy: {key}-{width}"
            assert fact["date"] == DATE_LINE, f"one-line date moved or changed: {key}-{width}"
            assert not fact["marker_before_headline"], f"one-line option unexpectedly has snapshot marker: {key}-{width}"
        assert len(fact["buttons"]) == 1, f"Generate button missing: {key}-{width}"
        expected_disabled = key == "8a-quiet-generating-proposed"
        assert fact["buttons"][0]["disabled"] is expected_disabled, f"Generate disabled state drifted: {key}-{width}"
for width in (1440, 393):
    empty = facts[f"7a-empty-original-{width}"]
    assert empty["headline"] == "No changes" and empty["snapshot"] is None and empty["handled"] is None, f"empty board drifted: {width}"
    baseline = facts[f"7b-fully-triaged-original-{width}"]
    assert baseline["snapshot"] is None and baseline["handled"] is None, f"original quiet baseline gained proposal copy: {width}"
    generating = facts[f"8a-quiet-generating-proposed-{width}"]
    assert generating["generating"] and not generating["failed"] and generating["buttons"][0]["disabled"], f"generating state drifted: {width}"
    failed = facts[f"8b-quiet-failed-proposed-{width}"]
    assert failed["failed"] and not failed["generating"] and not failed["buttons"][0]["disabled"], f"failure state drifted: {width}"
for width in (1440, 393):
    success = facts[f"9-same-day-success-proposed-{width}"]
    assert "Brief ready · 6 items · 5:40 PM" in success["receipts"], f"success receipt did not coexist with handled receipt: {width}"
for key in ("8a-quiet-generating-proposed", "8b-quiet-failed-proposed"):
    assert facts[f"{key}-1440"]["handled"] == HANDLED, f"handled receipt lost in {key}"
