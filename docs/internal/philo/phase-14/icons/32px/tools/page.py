#!/usr/bin/env python3
"""PHILO-14 A0c: build 32px/sheet.html from tools/picks.json.

One row per base sprite: the 64 px D1 icon, the same icon as the list
showed it before (the browser scaling the 64 to 32), the 2x2 seed the
redraw started from, and the PixelLab candidates. Each cell is on the
dark Dock ground (1:1 and 2x) and on the light steel screen (1:1).
Run from anywhere: python3 docs/internal/philo/phase-14/icons/32px/tools/page.py
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DATA = json.loads((HERE / "tools" / "picks.json").read_text())
PICKS: dict[str, str] = DATA["picks"]
JOBS: dict[str, dict[str, str]] = DATA["jobs"]
WHY: dict[str, str] = DATA.get("why", {})


def cell(src: str, pick: bool = False) -> str:
    """The image three times: dark at 32, dark at 64 (2x), steel at 32.
    Every image renders `pixelated`, as the list did: the 64 px reference
    at 32 is exactly what an ObjectList row showed before A0c."""
    one = f'<img src="{src}" width="32" height="32" alt="">'
    two = f'<img src="{src}" width="64" height="64" alt="">'
    mark = '<div class="pick">PICK</div>' if pick else ""
    return (
        f'<td class="{"is-pick" if pick else ""}">'
        f'<div class="dk">{one}{two}</div><div class="st">{one}</div>{mark}</td>'
    )


rows = []
for name in sorted(PICKS):
    pick = PICKS[name]
    cands = sorted(JOBS.get(name, {}))
    tds = [
        cell(f"ref64/{name}.png"),
        cell(f"seed/{name}.png"),
    ]
    for c in ("e1", "e2"):
        if c in cands:
            tds.append(cell(f"candidates/{name}-{c}.png", pick=(c == pick)))
        else:
            tds.append('<td><div class="none">not drawn</div></td>')
    why = escape(WHY.get(name, ""))
    rows.append(
        f'<tr><th>{escape(name)}<div class="cap">pick {pick}. {why}</div></th>{"".join(tds)}</tr>'
    )

page = (HERE / "tools" / "page.tpl").read_text().replace("{{ROWS}}", "\n".join(rows))
(HERE / "sheet.html").write_text(page)
print(f"wrote {HERE / 'sheet.html'} ({len(rows)} rows)")
