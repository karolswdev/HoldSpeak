"""Build the ONE self-contained review page for the PHILO-8-01 canvas.

Writes docs/internal/philo/phase-8/rename-canvas/index.html with every board
embedded (base64), both widths, the strings, the three questions, the fence
sketch and the limits. Run after shoot.py.
"""
from __future__ import annotations

import base64
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANVAS = HERE.parent
REPO = CANVAS.parents[5]
SHOTS = CANVAS / "shots"
OUT = REPO / "docs/internal/philo/phase-8/rename-canvas/index.html"

BOARDS = [
    ("0-today-list-after-new-zone", "0 · Today (built, half A)", "New Zone on the list makes “New zone 2”. Nothing opens."),
    ("1-new-zone-field-open", "1 · New Zone: the field opens", "The “New zone 2” row holds the field. Focused, the name selected, the mic beside it."),
    ("2-typing", "2 · Typing", "“Platform team” in the field."),
    ("3-enter-committed", "3 · Enter", "PUT 200. The row reads “Platform team”. The field is closed."),
    ("4-escape-kept-default", "4 · Escape", "New Zone again, then Escape. The row keeps “New zone 2”. No PUT."),
    ("5-refused-name-taken", "5 · Refused", "“Inbox” exists. PUT 409 zone_name_taken. ✗ NAME TAKEN on the row; the field keeps focus."),
    ("6-f2-rename-existing", "6 · F2 on a zone row", "Focus the “Platform team” row, press F2. The same field opens."),
    ("7-chair-no-new-zone", "7 · The Chair (built, half A)", "The palette on the Chair: no New Zone."),
]


def img(name: str) -> str:
    data = base64.b64encode((SHOTS / f"{name}.png").read_bytes()).decode()
    return f"data:image/png;base64,{data}"


def main() -> None:
    facts = json.loads((SHOTS / "facts.json").read_text())
    cards = []
    for key, title, caption in BOARDS:
        f1440 = facts.get(f"{key}-1440", {})
        writes = [f"{w['method']} {w['status']}" for w in f1440.get("writes", [])[-2:]]
        cards.append(f"""
<section class="board" id="b-{key}">
  <h2>{html.escape(title)}</h2>
  <p class="cap">{html.escape(caption)}</p>
  <div class="pair">
    <figure class="w1440"><img loading="lazy" alt="{html.escape(title)} at 1440" src="{img(f'{key}-1440')}"><figcaption>1440 × 900</figcaption></figure>
    <figure class="w393"><img loading="lazy" alt="{html.escape(title)} at 393" src="{img(f'{key}-393')}"><figcaption>393 × 852</figcaption></figure>
  </div>
  <p class="facts">field focused: <b>{str(f1440.get('field_focused')).lower()}</b> · last writes: <b>{html.escape(', '.join(writes) or 'none')}</b></p>
</section>""")
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Zone rename canvas</title>
<meta name="description" content="PHILO-8-01: the zone name field in the list row, eight live boards at 1440 and 393, for the owner's ratification.">
<style>
:root {{ --bg:#f6f6f4; --fg:#1b1d22; --muted:#5b6070; --line:#d8d9dd; --card:#ffffff; --accent:#1f7a55; --warn:#b3261e; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#111317; --fg:#e7e8ec; --muted:#9ba2b0; --line:#2a2e3e; --card:#181b22; --accent:#4fd29a; --warn:#ff8a80; }} }}
:root[data-theme="dark"] {{ --bg:#111317; --fg:#e7e8ec; --muted:#9ba2b0; --line:#2a2e3e; --card:#181b22; --accent:#4fd29a; --warn:#ff8a80; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.45 system-ui, -apple-system, sans-serif; }}
main {{ max-width:1500px; margin:0 auto; padding:24px 16px 64px; }}
h1 {{ font-size:26px; margin:0 0 4px; }}
h2 {{ font-size:18px; margin:0 0 4px; }}
h3 {{ font-size:15px; margin:20px 0 6px; }}
.sub, .cap, .facts, figcaption {{ color:var(--muted); font-size:13px; margin:0 0 10px; }}
.status {{ display:inline-block; font:600 12px ui-monospace, monospace; letter-spacing:.06em; border:1px solid var(--accent); color:var(--accent); padding:2px 8px; margin:8px 0 16px; }}
nav {{ display:flex; flex-wrap:wrap; gap:6px; position:sticky; top:0; background:var(--bg); padding:8px 0; border-bottom:1px solid var(--line); z-index:2; }}
nav a {{ font:600 12px ui-monospace, monospace; color:var(--fg); text-decoration:none; border:1px solid var(--line); background:var(--card); padding:4px 8px; }}
.board {{ background:var(--card); border:1px solid var(--line); padding:14px; margin:16px 0; }}
.pair {{ display:grid; grid-template-columns: minmax(0, 3.6fr) minmax(0, 1fr); gap:12px; align-items:start; }}
figure {{ margin:0; }}
img {{ width:100%; height:auto; display:block; border:1px solid var(--line); }}
table {{ border-collapse:collapse; width:100%; font-size:13px; }}
th, td {{ text-align:left; border-bottom:1px solid var(--line); padding:6px 8px; vertical-align:top; }}
code {{ font:12px ui-monospace, monospace; }}
.q {{ background:var(--card); border:1px solid var(--line); border-left:3px solid var(--accent); padding:10px 12px; margin:8px 0; }}
.wrap {{ overflow-x:auto; }}
@media (max-width: 720px) {{ .pair {{ grid-template-columns: 1fr; }} h1 {{ font-size:22px; }} }}
</style>
</head>
<body>
<main>
<h1>The zone name field in the list row</h1>
<p class="sub">PHILO-8-01 · Phase 8 The Honest Floor · the owner's Q2 (c): “on the list, the name field opens in the new zone's row”.</p>
<span class="status">FOR YOUR RATIFICATION · NOT BUILT</span>
<p class="sub">Every board is a live run: a real hub on an isolated database and the product app, with one module swapped (the list, with the proposal). Boards 0 and 7 are the product as built on this branch.</p>
<nav>{''.join(f'<a href="#b-{k}">{html.escape(t.split(" · ")[0])}</a>' for k, t, _ in BOARDS)}<a href="#questions">Questions</a><a href="#fences">Fences</a><a href="#limits">Limits</a></nav>
{''.join(cards)}
<section id="questions">
<h2>Three questions</h2>
<div class="q"><b>1. The field in the row, as drawn?</b> The name field opens in the new zone's row with the name selected. Enter writes. A click elsewhere writes. Escape keeps the name (“New zone 2”) and closes the field. The same field serves F2. <i>Recommended: yes.</i></div>
<div class="q"><b>2. A refused name: <code>✗ NAME TAKEN</code> on the row?</b> The field stays open with focus. The same chip also replaces the Floor's sentence (“A zone named "Inbox" already exists”, 11 px, under the 12 px floor), so both faces show one species. <i>Recommended: yes, on both faces.</i></div>
<div class="q"><b>3. F2 on a focused zone row opens the field?</b> Zone rows cannot be selected on the list, so F2 does not reach them today. No row menu for zones. <i>Recommended: yes.</i></div>
</section>
<section>
<h3>The strings</h3>
<div class="wrap"><table>
<tr><th>Slot</th><th>String</th></tr>
<tr><td>Field (accessible name)</td><td><code>Zone name</code></td></tr>
<tr><td>Default name (built, half A)</td><td><code>New zone</code>, then <code>New zone 2</code>, <code>New zone 3</code> …</td></tr>
<tr><td>Refused (StateChip failure)</td><td><code>✗ NAME TAKEN</code> · <code>data-code="zone_name_taken"</code></td></tr>
<tr><td>Verbs</td><td>none new. Enter writes, Escape keeps. The mic is the library MicButton.</td></tr>
</table></div>
</section>
<section id="fences">
<h3>Fence sketch (the build after your word)</h3>
<div class="wrap"><table>
<tr><th>After</th><th>Assert (rendered, 1440 and 393, real hub)</th><th>Red today</th></tr>
<tr><td>New Zone on the list</td><td>the “New zone 2” row holds the field, focused, the name selected</td><td>no field (board 0)</td></tr>
<tr><td>Type + Enter</td><td>PUT 200; <code>GET /api/directories</code> lists the name; the row reads it</td><td>no field</td></tr>
<tr><td>Escape</td><td>no PUT; the row reads “New zone 2”</td><td>no field</td></tr>
<tr><td>A taken name + Enter</td><td>PUT 409; <code>[data-code=zone_name_taken]</code> reads NAME TAKEN; focus kept; the Floor shows the same chip</td><td>list: no field · Floor: the sentence</td></tr>
<tr><td>F2 on a focused zone row</td><td>the field opens on that row with focus</td><td>nothing happens</td></tr>
<tr><td>Every state</td><td>one Enter/blur/Escape path; no text under 12 px in the row; the mic is the library Button</td><td>—</td></tr>
</table></div>
</section>
<section id="limits">
<h3>Limits</h3>
<ul class="sub">
<li>The list module on boards 1–6 is a copy with the proposal. The product list is unchanged until you ratify.</li>
<li>Inherited, not in this story: the list's census line (“17 ITEMS · 8 ZONES”, “17 SHOWN of 17”) is 10 px; at 393 the Zone column is cut at the right edge.</li>
<li>Observed, not changed: a rename that fails with 422 or a network error reverts without a word.</li>
</ul>
</section>
</main>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page)
    print(OUT, f"{OUT.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
