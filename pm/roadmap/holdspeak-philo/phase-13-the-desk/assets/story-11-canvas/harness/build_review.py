"""PHILO-13-11 (C1): the review page (../index.html) from the shots and facts.json.

Every board at 1440 x 900 (left) and 393 x 852 (right), in canvas order, with
the criterion it answers and what to check on it.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANVAS = HERE.parent
SHOTS = CANVAS / "shots"

# id: (title, criteria, what to check)
BOARDS: list[tuple[str, str, str, str]] = [
    ("C1-1-the-desk", "C1-1 · The whole Desk", "2, 3, 4, 7",
     "The screen title bar names the front window (Needs you) and the time. The Chair is four windows on the Workbench screen. ONE needs-you number: the Chair head, the bell, Intelligence and Desk memory all read 8; the capped list says ACTIONS 5 OF 7. The Dock is an AppIcon shelf: REC 12:04 on Meetings, 1:1 14:30 on People, a count on each active project (stand-in values until C3). The Brief's destination reads ~/Documents/HoldSpeak/Team updates."),
    ("C1-2a-window-gadgets", "C1-2a · Two real windows: the gadget set", "1, 2, 3",
     "Meetings (All summaries done) and the Payments ledger Room (Clear here): real DeskWindowFrame hosts; narrower counts say what they count. Close at the left; iconify, zoom, depth at the right; the sizing gadget at the bottom right. ONE front window wears the blue frame; the screen bar names it."),
    ("C1-2b-window-menu-amiga-keys", "C1-2b · Right button: the window's menu bar", "1, 5",
     "The right button on the drag bar, beside the title (the name stays readable): Iconify, Zoom, To back, Close window, then Desk ▸ and Go ▸, each verb with its Amiga-key column (⌘ = the Amiga key). Desk ▸ open."),
    ("C1-2c-depth-to-back", "C1-2c · Depth: to back", "1, 2",
     "The depth gadget pressed on the Room: it goes behind, Meetings comes to the front, the screen bar follows (stand-in for C2)."),
    ("C1-2d-zoom", "C1-2d · Zoom", "1",
     "The zoom gadget: the window fills the work band; pressed again it returns (C2 adds the second remembered rect)."),
    ("C1-3-material-tokens", "C1-3 · The material", "3, 5",
     "The four pens and their roles, the gadget glyphs with their keys, the bevels, a front and a back window, the sizes, the library verbs and chips, the AppIcon states, the type steps. Values are read back from the live :root."),
    ("C1-4a-chair-windows", "C1-4a · The Chair composed of windows", "4",
     "Needs you, Brief, The week, Capture: the Arrival's real sections in four windows (1440: The week in front). At 393 the Brief window is open and the others are title bars."),
    ("C1-4b-chair-window-zoomed", "C1-4b · A Chair window zoomed", "1, 4",
     "1440: the Brief window zoomed to the whole screen by its zoom gadget."),
    ("C1-4b-chair-week-open", "C1-4b · The week open (393)", "4, 6",
     "393: The week open by its zoom gadget; the others stay title bars."),
    ("C1-5a-meeting-selected-park", "C1-5a · Parked and Restore: a meeting selected", "A1-F",
     "Meetings, Hiring debrief selected: the footer verb is Park (no confirm: Restore undoes it)."),
    ("C1-5b-meeting-parked-receipt", "C1-5b · PARKED receipt", "A1-F",
     "Park pressed: the meeting leaves the list; the receipt reads PARKED <time> with Restore; the PARKED 1 token appears (no token while nothing is parked)."),
    ("C1-5c-meetings-parked-filter", "C1-5c · The Parked filter", "A1-F",
     "PARKED 1 on: the parked rows, each with its time, the PARKED chip and Restore."),
    ("C1-5d-meeting-restored", "C1-5d · Restored", "A1-F",
     "Restore pressed: the meeting is back in the list; the token and the receipt are gone."),
    ("C1-5e-workbench-item-parked", "C1-5e · A Workbench item parked", "A1-F",
     "The Workbench window: Remove on Old sampling spike parks it; PARKED <time> + Restore in the footer; PARKED 1 above the items."),
    ("C1-5f-workbench-parked-filter", "C1-5f · The Workbench Parked filter", "A1-F",
     "PARKED 1 on: the parked item with Restore."),
    ("C1-6a-phone-desk", "C1-6a · The phone desk", "6",
     "393: one line of screen bar (mark, Go, the front window, the egress lamp, search, time), one Chair window open, the rest title bars, a one-row AppIcon shelf with the daily seats (8, REC, 1:1, the first project) ending on a whole icon and a More gadget at the edge. Frame 96 px (C7's budget 142)."),
    ("C1-6b-phone-window-sheet", "C1-6b · A window at 393", "1, 6",
     "393: People as a sheet: close at the left, depth at the right, 44 px gadgets, the wings in the bar."),
    ("C1-7-comparison", "C1-7 · Recommended vs the one alternative", "—",
     "Left: Workbench Steel (recommended). Right: Honest 2.0, the four pens on every body too. Top: the Chair; bottom: two windows."),
]


def main() -> None:
    facts = json.loads((SHOTS / "facts.json").read_text()) if (SHOTS / "facts.json").exists() else {}
    rows = []
    for bid, title, crit, check in BOARDS:
        cells = []
        for w in (1440, 393):
            p = SHOTS / f"{bid}-{w}.png"
            cells.append(f'<a href="shots/{p.name}"><img src="shots/{p.name}" loading="lazy" class="w{w}"></a>' if p.exists() else f'<div class="none w{w}">NOT DRAWN AT {w}</div>')
        rows.append(f"""<section><h2>{html.escape(title)} <span>CRITERIA {html.escape(crit)}</span></h2>
<p>{html.escape(check)}</p><div class="pair">{''.join(cells)}</div></section>""")
    fails = facts.get("_fails", [])
    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>PHILO-13-11 C1 · The Workbench look</title>
<style>
body {{ margin: 0; background: #3c4454; color: #0b0c10; font: 14px/1.4 'JetBrains Mono', ui-monospace, monospace; }}
header {{ background: #eef0f3; border-bottom: 1px solid #0b0c10; padding: 8px 16px; font-weight: 700; }}
section {{ margin: 16px; background: #9ea4b0; border: 1px solid #0b0c10; box-shadow: inset 1px 1px 0 #fff8, inset -1px -1px 0 #0008; }}
h2 {{ margin: 0; padding: 6px 10px; font-size: 14px; background: #6688bb; border-bottom: 1px solid #0b0c10; }}
h2 span {{ float: right; font-weight: 600; }}
p {{ margin: 8px 10px; }}
.pair {{ display: flex; gap: 12px; padding: 0 10px 10px; align-items: flex-start; }}
img {{ border: 1px solid #0b0c10; display: block; }}
img.w1440 {{ width: min(1000px, 70vw); }} img.w393 {{ width: min(280px, 22vw); }}
.none {{ padding: 20px; border: 1px dashed #0b0c10; }}
</style></head><body>
<header>PHILO-13-11 (C1) · The Workbench look · {len(BOARDS)} boards · fences: {"ALL HELD" if not fails else str(len(fails)) + " FAILED"}</header>
{''.join(rows)}
</body></html>"""
    (CANVAS / "index.html").write_text(page)
    print("wrote", CANVAS / "index.html")


if __name__ == "__main__":
    main()
