"""Package PHILO-4-04 board shots into one self-contained review page.

Run from this harness directory after the orchestrator has captured the seven
boards into ../shots:
  python page.py

This wrapper is canvas review material. Its small layout CSS is outside the
product face; the PNGs themselves come from the actual library species.
"""
import base64
from pathlib import Path

from playwright.sync_api import sync_playwright


HARNESS = Path(__file__).resolve().parent
CANVAS = HARNESS.parent
SHOTS = CANVAS / "shots"

HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PHILO-4-04 · Triaged headline canvas</title>
<style>
:root { color-scheme: dark; --bg:#0e0f13; --surface-1:#15171d; --border:#2a2e3e; --text:#f2f3f5; --text-muted:#9ba2b0; --text-faint:#8b93a3; --font-mono:"JetBrains Mono","SFMono-Regular","SF Mono",Consolas,monospace; }
body { margin:0; background:var(--bg); color:var(--text); font-family:var(--font-mono); padding:24px 16px; }
h1 { font-size:14px; letter-spacing:.08em; color:var(--text-muted); margin:0 0 20px; font-weight:600; }
.state { border-top:1px solid var(--border); padding:16px 0 24px; }
h2 { font-size:13px; letter-spacing:.06em; margin:0 0 4px; }
.note { font-size:12px; color:var(--text-faint); margin:0 0 12px; }
.pair { display:grid; grid-template-columns:minmax(0,3fr) minmax(0,1fr); gap:16px; align-items:start; }
figure { margin:0; background:var(--surface-1); border:1px solid var(--border); padding:10px; min-width:0; }
figcaption { font-size:12px; color:var(--text-faint); margin-bottom:6px; }
img { display:block; width:100%; height:auto; }
.w393 img { max-width:369px; }
@media (max-width:720px) { .pair { grid-template-columns:minmax(0,1fr); } }
</style></head><body>
<h1>PROPOSED — OWNER RATIFICATION PENDING — CANVAS ONLY · PHILO-4-04 · THE TRIAGED HEADLINE · QUIET BRANCH</h1>
<p class="note review-note">ALL 6 HANDLED counts Arrival rows only. It excludes THIS WEEK, so the count may be smaller than the headline total. The six-row fixture is an acceptance fixture, not a full-producer board claim.</p>
"""

BOARDS = [
    (
        "7a-empty-original",
        "7A · EMPTY BRIEF · ORIGINAL",
        "preserved empty result · No changes · no snapshot marker and no handled claim",
    ),
    (
        "7b-fully-triaged-original",
        "7B · FULLY TRIAGED · ORIGINAL",
        "current quiet baseline · the stored headline remains bare after all six fixture rows leave the Arrival",
    ),
    (
        "7c-one-line-proposed",
        "7C · FULLY TRIAGED · RECOMMENDED MINIMAL",
        "recommended minimal option · original headline and generated date stay in place · one plain 12px ALL 6 HANDLED line follows",
    ),
    (
        "7b-fully-triaged-proposed",
        "7B · FULLY TRIAGED · ALTERNATIVE SNAPSHOT",
        "alternative owner choice · SNAPSHOT · SEP 21 – 23 · GENERATED SEP 23 17:40 · stored headline unchanged · ALL 6 HANDLED",
    ),
    (
        "8a-quiet-generating-proposed",
        "8A · QUIET BRANCH · GENERATING",
        "proposed marker and ALL 6 HANDLED persist while Generate is disabled and GENERATING… is in flow",
    ),
    (
        "8b-quiet-failed-proposed",
        "8B · QUIET BRANCH · GENERATION FAILED",
        "proposed marker and ALL 6 HANDLED persist beside the in-flow generation failure",
    ),
    (
        "9-same-day-success-proposed",
        "9 · QUIET BRANCH · SAME-DAY SUCCESS",
        "proposed marker and ALL 6 HANDLED coexist with the original-generation Brief ready · 6 items · 5:40 PM receipt",
    ),
]


def image_data(name: str) -> str:
    return base64.b64encode((SHOTS / name).read_bytes()).decode()


parts = [HEAD]
for key, title, note in BOARDS:
    parts.append(
        f'<section class="state"><h2>{title}</h2><p class="note">{note}</p>\n'
        f'<div class="pair"><figure class="w1440"><figcaption>1440</figcaption>'
        f'<img alt="{key} at 1440" src="data:image/png;base64,{image_data(key + "-1440.png")}"></figure>\n'
        f'<figure class="w393"><figcaption>393</figcaption>'
        f'<img alt="{key} at 393" src="data:image/png;base64,{image_data(key + "-393.png")}"></figure></div></section>'
    )
parts.append("</body></html>\n")
(CANVAS / "triaged-headline.html").write_text("".join(parts))

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    for width in (1440, 393):
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.goto(f"file://{CANVAS / 'triaged-headline.html'}")
        page.wait_for_timeout(250)
        page.screenshot(path=str(CANVAS / f"triaged-headline{'-393' if width == 393 else ''}.png"), full_page=True)
    browser.close()
