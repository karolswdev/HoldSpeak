"""HS-202-05 — the disabled Button stays distinct after --text-faint moves.

`--disabled-fg` IS `--text-faint` (`tokens.css:148`), so the type-scale
ruling's contrast fix (`#767e8d` -> `#8b93a3`) lightens every disabled
label toward live text. Muad'Dib's check named that risk: "Disabled
controls may lose distinction from muted text" (the ruling's check
table). The ruling's answer keeps the `disabled` attribute, the
`not-allowed` cursor and the flat treatment, and REFUSES the generic
skill's 0.38-0.5 opacity because it would cut the measured contrast.

This fence holds that answer. A disabled Button must differ from its
enabled twin in FOUR independent channels, and its own label must still
make 4.5:1 on its own ground.

The negative control is the point of the fence: a Button whose ONLY
difference from its twin is a gray label must FAIL here. Without that,
the fence would pass on a face that states "disabled" in gray alone.

Shots (HS202_05_EXPORT_SHOTS=1) land the enabled/disabled pair at 1440
and 393 in the story's assets.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(180, method="thread")]

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CSS_DIR = REPO / "web/src/styles"
SHOTS = REPO / "pm/roadmap/holdspeak/phase-202-the-coherent-face/assets/story-05-shots"
WIDTHS = {1440: 900, 393: 852}


def _css() -> str:
    css_dir = Path(os.environ.get("HS202_05_CSS_DIR", DEFAULT_CSS_DIR))
    tokens = (css_dir / "tokens.css").read_text(encoding="utf-8")
    glob = (css_dir / "global.css").read_text(encoding="utf-8")
    return tokens + "\n" + re.sub(r"^@import\s+[^;]+;\s*$", "", glob, flags=re.MULTILINE)


_PAIR = """
  <div class="pair">
    <button type="button" class="btn" id="on-btn">Run summary</button>
    <button type="button" class="btn" id="off-btn" disabled>Run summary</button>
  </div>
  <div class="pair">
    <button type="button" class="btn btn--primary" id="on-primary">Record</button>
    <button type="button" class="btn btn--primary" id="off-primary" disabled>Record</button>
  </div>
  <div class="pair">
    <button type="button" class="btn btn--sm" id="on-sm">Open</button>
    <button type="button" class="btn btn--sm" id="off-sm" disabled>Open</button>
  </div>
  <div class="pair gray-only">
    <button type="button" class="btn" id="on-gray">Export</button>
    <button type="button" class="btn" id="off-gray" disabled>Export</button>
  </div>
"""

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<style>%s</style>
<style>
  body { margin: 0; padding: 20px; background: var(--bg); }
  .pair { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
</style></head><body>%s</body></html>""" % (_css(), _PAIR)


_READ = """(id) => {
  const el = document.getElementById(id);
  const cs = getComputedStyle(el);
  const parse = (s) => {
    const m = /rgba?\\(([^)]+)\\)/.exec(s || "");
    if (!m) return null;
    const p = m[1].split(/[,\\s\\/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const over = (fg, bg) => ({ r: fg.r*fg.a + bg.r*(1-fg.a), g: fg.g*fg.a + bg.g*(1-fg.a),
                              b: fg.b*fg.a + bg.b*(1-fg.a), a: 1 });
  // The ground the label is really on: the Button's own fill composited
  // over the page, exactly the way the census reads it.
  let bg = parse(cs.backgroundColor);
  const page = parse(getComputedStyle(document.body).backgroundColor) || {r:255,g:255,b:255,a:1};
  bg = !bg || bg.a <= 0 ? page : (bg.a < 1 ? over(bg, page) : bg);
  const fg = parse(cs.color);
  const eff = fg.a < 1 ? over(fg, bg) : fg;
  const l1 = lum(eff), l2 = lum(bg);
  return {
    disabledAttr: el.disabled,
    color: cs.color, background: cs.backgroundColor, borderColor: cs.borderTopColor,
    boxShadow: cs.boxShadow, cursor: cs.cursor, opacity: cs.opacity,
    ratio: Math.round(((Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05)) * 100) / 100,
  };
}"""

# The four channels the ruling keeps. Gray alone is never enough.
CHANNELS = ("background", "borderColor", "boxShadow", "cursor")
REAL_PAIRS = [("on-btn", "off-btn"), ("on-primary", "off-primary"), ("on-sm", "off-sm")]


def _distinct(on: dict, off: dict) -> list[str]:
    return [c for c in CHANNELS if on[c] != off[c]]


@pytest.mark.parametrize("width", sorted(WIDTHS))
def test_disabled_button_stays_distinct(tmp_path: Path, width: int) -> None:
    page_html = tmp_path / "disabled-fixture.html"
    page_html.write_text(HTML, encoding="utf-8")
    failures: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": WIDTHS[width]})
        page.emulate_media(reduced_motion="reduce")
        page.goto(page_html.as_uri())
        page.wait_for_selector("#off-gray")

        for on_id, off_id in REAL_PAIRS:
            on, off = page.evaluate(_READ, on_id), page.evaluate(_READ, off_id)
            if not off["disabledAttr"]:
                failures.append(f"{off_id}: the semantic `disabled` attribute is gone")
            if off["cursor"] != "not-allowed":
                failures.append(f"{off_id}: cursor is {off['cursor']!r}, not 'not-allowed'")
            if off["boxShadow"] != "none":
                failures.append(f"{off_id}: the bevel survived ({off['boxShadow']}); "
                                "the disabled treatment is flat")
            if float(off["opacity"]) < 0.999:
                failures.append(f"{off_id}: opacity {off['opacity']} — the ruling refuses "
                                "an opacity dim; it cuts the measured contrast")
            changed = _distinct(on, off)
            if len(changed) < 3:
                failures.append(
                    f"{off_id}: only {changed or 'no'} channel(s) separate it from {on_id}; "
                    "gray alone never states the disabled position"
                )
            if off["ratio"] < 4.5:
                failures.append(
                    f"{off_id}: the disabled label reads {off['ratio']}:1 on its own ground, "
                    "under the ruling's 4.5:1"
                )

        # ── NEGATIVE CONTROL ─────────────────────────────────────────
        # Built by construction, not by a second stylesheet: every channel
        # but the label's gray is copied from the enabled twin, so this
        # pair IS the "gray alone" face the ruling refuses.
        page.evaluate("""() => {
          const on = document.getElementById('on-gray');
          const off = document.getElementById('off-gray');
          const cs = getComputedStyle(on);
          for (const prop of ['background-color','border-color','box-shadow','cursor','opacity'])
            off.style.setProperty(prop, cs.getPropertyValue(prop), 'important');
        }""")
        gray_on, gray_off = page.evaluate(_READ, "on-gray"), page.evaluate(_READ, "off-gray")
        if len(_distinct(gray_on, gray_off)) >= 3:
            failures.append(
                "NEGATIVE CONTROL: a Button whose only difference is its gray label "
                "passed the channel count, so this fence cannot see a gray-only "
                "disabled state and proves nothing about the others"
            )

        if os.environ.get("HS202_05_EXPORT_SHOTS") == "1":
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.locator(".pair").first.screenshot(
                path=str(SHOTS / f"disabled-pair-{width}.png")
            )
        browser.close()

    assert not failures, (
        f"the disabled Button is not distinct at {width}:\n  " + "\n  ".join(failures)
    )
