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
    ("C1-1-the-desk", "C1-1 · The whole Desk", "2, 3, 4, 7, A2",
     "The screen bar names the one front window and the time. The Chair is four windows; Needs you leads with the number and the actions: the ranking strip on its own line and whole (393: RANKED ▾), the availability chip off the strip; SETUP below the actions. The Brief's SEND is on the first screen. ONE needs-you number: head, bell, Intelligence, Desk memory = 8. Every active project has its AppIcon; Staff hiring has no count (never a zero)."),
    ("C1-2a-window-gadgets", "C1-2a · Two real windows: the gadget set", "1, 2, 3",
     "Meetings (All summaries done) and the Room (Clear here). Exactly one blue title bar. At 393 a window fills the work area; its head is one 44 px row: close · wings · depth."),
    ("C1-2b-window-menu-amiga-keys", "C1-2b · Right button: the window's menu", "1, 5",
     "Iconify, Zoom, To back, Close window, then Desk ▸ and Go ▸, each verb with its Amiga-key column; the front window's name stays readable."),
    ("C1-2c-depth-to-back", "C1-2c · Depth: to back", "1, 2", "Depth on the Room: it goes behind; Meetings is the one blue window; the screen bar follows."),
    ("C1-2e-strip-menu-open", "C1-2e · The strip menu open (393)", "3b, 6",
     "393: the Meetings tabs do not fit, so they are ONE menu Button (OUTCOMES ▾, 44 px) in the head row; open: every tab and the gear door, a check on the current one. Nothing clips, nothing scrolls sideways."),
    ("C1-2d-zoom", "C1-2d · Zoom (1440)", "1", "Zoom fills the work band; pressed again it returns."),
    ("C1-3-material-tokens", "C1-3 · The material", "3, 5", "The pens, gadgets, bevels, windows, sizes, verbs, AppIcon states and type, read back from the live :root. At 393 the sheet fills the work area."),
    ("C1-4a-chair-windows", "C1-4a · The Chair as windows", "4", "1440: four windows, The week in front. 393: ONE window (Brief) fills the work area; no stack of bars."),
    ("C1-4b-chair-window-zoomed", "C1-4b · A Chair window zoomed (1440)", "1, 4", "The Brief zoomed to the whole screen."),
    ("C1-4b-chair-week-open", "C1-4b · The week (393)", "4, 6", "393: The week fills the work area."),
    ("C1-4c-chair-window-closed", "C1-4c · Close closes (R1)", "1, 4", "Close on Brief CLOSES it. 1440: its place holds one compact reopen Button. 393: the next Chair window fills the work area."),
    ("C1-4d-window-menu-chair", "C1-4d · Window ▸ Chair", "1, 4", "The Window menu (393: Go) lists the four Chair windows with a check on each open one; Brief has none."),
    ("C1-4e-chair-window-reopened", "C1-4e · Reopened", "1, 4", "Picking Brief opens it in front."),
    ("C1-5a-meeting-selected-park", "C1-5a · A meeting selected: Park", "A1-F", "The footer verb is Park (no confirm: Restore undoes it). At 393 the warning, the receipt and the verbs no longer overlap."),
    ("C1-5b-meeting-parked-receipt", "C1-5b · PARKED + Restore", "A1-F", "The meeting leaves the list; PARKED hh:mm + Restore; the PARKED 1 token appears."),
    ("C1-5c-meetings-parked-filter", "C1-5c · The Parked filter", "A1-F", "The parked rows with the time, the PARKED chip and Restore."),
    ("C1-5d-meeting-restored", "C1-5d · RESTORED", "A1-F", "Restore: the receipt reads RESTORED hh:mm and the meeting comes into view, marked."),
    ("C1-5e-meeting-restore-failed", "C1-5e · Restore refused", "A1-F", "The hub refuses the Restore: NOT RESTORED · THE HUB DID NOT ACCEPT THE CHANGE + Retry."),
    ("C1-5f-workbench-item-parked", "C1-5f · A Workbench item parked", "A1-F", "Remove parks the item: PARKED hh:mm + Restore; PARKED 1 above the items."),
    ("C1-5g-workbench-parked-filter", "C1-5g · The Workbench Parked filter", "A1-F", "The parked item with Restore."),
    ("C1-5h-workbench-item-restored", "C1-5h · A Workbench item restored", "A1-F", "RESTORED hh:mm; the item is back, marked."),
    ("C1-5i-workbench-claimed-refused", "C1-5i · Claimed by a run", "A1-F", "A run claimed the item between the read and the press: NOT PARKED · CLAIMED BY A RUN."),
    ("C1-5j-workbench-clear-done-parked", "C1-5j · Clear done (bulk park)", "A1-F", "Clear done parks both done items: PARKED 2 · hh:mm + Restore."),
    ("C1-6a-phone-desk", "C1-6a · The phone desk (393)", "6", "One window fills the work area (content 704 px of 852); the first Done is whole on the first screen; the screen bar's controls and the shelf's icons are 44 px or more; Speak is capture on demand."),
    ("C1-6b-phone-window-sheet", "C1-6b · People at 393", "1, 6, R5", "People fills the work area; its facts read on the dark well (the steel strip at 1.02:1 is gone)."),
    ("C1-8a-dock-ready-and-sent", "C1-8a · C3: ready and sent", "7", "Meetings READY 1; Intelligence SENT 14:02."),
    ("C1-8b-dock-send-failed-unknown", "C1-8b · C3: failed and unknown", "7", "Meetings SEND FAILED; Intelligence UNKNOWN."),
    ("C1-8c-dock-offline", "C1-8c · C3: disconnected", "7", "OFFLINE · AS OF 20:24 heads the shelf; no tag and no count claims to be fresh."),
    ("C1-7-comparison", "C1-7 · Steel vs Honest 2.0", "—", "Top: Workbench Steel. Bottom: Honest 2.0 (grey bodies, a complete palette: every text ≥ 4.5:1). The Chair, two windows, People."),
]


def measurements(facts: dict) -> str:
    """Every count the README states, generated from facts.json, run.log and the red-before files."""
    b = [k for k in facts if not k.startswith("_")]
    w1440, w393 = [k for k in b if k.endswith("-1440")], [k for k in b if k.endswith("-393")]
    log = (SHOTS / "run.log").read_text().splitlines() if (SHOTS / "run.log").exists() else []
    guard = sorted({g for k in facts if k.startswith("_seat_guard_") for g in (facts[k] or [])})
    verdict = "ALL FENCES HELD" if any("ALL FENCES HELD" in ln for ln in log) and not facts.get("_fails") else f"{len(facts.get('_fails', []))} FENCES FAILED"
    exitc = next((ln for ln in reversed(log) if ln.startswith("EXIT")), "EXIT ?")
    named = [k for k in b if facts[k].get("intended_front")]
    content = sorted({facts[k].get("content_px") for k in w393 if facts[k].get("content_px") is not None})
    ell = sorted({t for k in b for t in facts[k].get("clip", {}).get("ellipsis", [])})
    rows = [
        ("Verdict of this run (`shots/run.log`)", f"{verdict}; {exitc}"),
        ("Seat guard (both widths)", "; ".join(guard)),
        ("Boards", f"{len(b)} ({len(w1440)} at 1440, {len(w393)} at 393) + the C1-7 comparison"),
        ("Window observations (one gadget set each)", str(sum(len(facts[k]["windows"]) for k in b))),
        ("Frame-control observations / lost points", f"{sum(len(facts[k]['own']) for k in b)} / {sum(o['lost'] for k in b for o in facts[k]['own'])}"),
        ("Boards with exactly one blue title bar", f"{sum(1 for k in b if len(facts[k]['front_state']['blue']) == 1)} of {len(b)}"),
        ("Boards whose intended front window is the recorded one, on the glass", f"{sum(1 for k in named if facts[k]['front_state']['front'] == facts[k]['intended_front'] and facts[k]['front_state']['on_glass'])} of {len(named)} that name one"),
        ("Texts under 4.5:1 (3:1 large), in place", str(sum(len(facts[k]["low_contrast"]) for k in b))),
        ("Texts under 12 px", str(sum(len(facts[k]["small_text"]) for k in b))),
        ("393: the front window's content (px)", ", ".join(str(c) for c in content)),
        ("393: targets under 44 × 44", f"{sum(len(facts[k].get('targets_under_44') or []) for k in w393)} on {len(w393)} boards"),
        ("Sideways-scrolling strips / clipped texts", f"{sum(len(facts[k]['clip']['strips']) for k in b)} / {sum(len(facts[k]['clip']['clipped']) for k in b)}"),
        ("Rendered overlaps", str(sum(len(facts[k].get('overlap') or []) for k in b))),
        ("Overlap waivers used (each its exact relationship)", "; ".join(f"{w}: {n} pairs ({', '.join(sorted({x['a'] + ' / ' + x['b'] for k in b for x in facts[k].get('overlap_waived', []) if x['waiver'] == w}))})" for w, n in sorted(__import__('collections').Counter(x['waiver'] for k in b for x in facts[k].get('overlap_waived', [])).items())) or "none"),
        ("Mutation proof", "see the table below (`shots/mutation-proof.json`)"),
        ("Ellipsis lines (recorded, allowed by A.6)", ", ".join(f"`{t}`" for t in ell) or "none"),
        ("Needs-you numbers (head, bell, Intelligence, Desk memory)", "; ".join(f"{t} on {n} boards" for t, n in sorted(__import__('collections').Counter(str(tuple('not on the glass' if x is None else x for x in (facts[k]['needs_you']['head_n'], facts[k]['needs_you']['bell'], facts[k]['needs_you']['intel'], facts[k]['needs_you']['memory']))) for k in b).items())) + " (the Chair head is off the glass when a window fills the 393 work area)"),
        ("Active projects missing from the Dock / zero badges", f"{sum(len(facts[k]['dockfacts']['missing'] or []) for k in b)} / {sum(facts[k]['dockfacts']['zeros'] for k in b)}"),
        ("Browser errors", str(sum(len(facts.get(f'_browser_errors_{w}', [])) for w in (1440, 393)))),
    ]
    out = ["| Measure | Value |", "|---|---|"] + [f"| {a} | {v} |" for a, v in rows]
    mp = SHOTS / "mutation-proof.json"
    if mp.exists():
        m = json.loads(mp.read_text())
        what = {"a_sticky": "a Button in the Room's sticky Ask bar (computed position: absolute), over a body row NOT beneath the bar",
                "b_mic": "a mic button over a DIFFERENT text field of the Workbench window (no shared field wrapper)",
                "c_more": "a stray text element of the shelf under More (not an AppIcon)"}
        out.append("\nMutation proof (`shots/mutation-proof.json`): each targeted near miss against round 3c's broad-waiver fence (kept verbatim as `OVERLAP_BROAD`) and the narrowed fence (`OVERLAP`); a miss under the narrowed fence fails the run.\n")
        out.append("| Mutant | Width | Round 3c broad fence | Narrowed fence | Caught pair |")
        out.append("|---|---|---|---|---|")
        for wd in (1440, 393):
            for t, v in sorted(m.get(f"_mutation_{wd}", {}).items()):
                pair = f"{v['caught'][0]['a']} / {v['caught'][0]['b']}" if v.get("caught") else "—"
                chk = f" (computed: {v['check']['position']}; nearest bar: {v['check']['nearestBar']})" if v.get("check") else ""
                out.append(f"| {t}: {what.get(t, t)}{chk} | {wd} | {v['broad_fence']} | {v['narrowed_fence']} | {pair} |")
        out.append(f"\nMutation proof run: {'held' if not m.get('fails') else 'FAILED: ' + '; '.join(m['fails'])}.")
    for name, label in (("red-before-r2.json", "round two"), ("red-before-r3.json", "round three"), ("red-before-r3b.json", "round 3b (`e23ce53d`)")):
        p = SHOTS / name
        if p.exists():
            r = json.loads(p.read_text())
            n = r.get("boards_red", len([k for k in r if not k.startswith("_")]))
            out.append(f"\nRed before, {label}: `shots/{name}`, {n} boards red" + (f" of {r['boards']} measured" if "boards" in r else "") + ".")
    return "\n".join(out)


def stamp_readme(facts: dict) -> None:
    readme = CANVAS / "README.md"
    text = readme.read_text()
    a, b = "<!-- generated:measurements:begin -->", "<!-- generated:measurements:end -->"
    if a in text and b in text:
        head, rest = text.split(a, 1)
        _, tail = rest.split(b, 1)
        readme.write_text(f"{head}{a}\n{measurements(facts)}\n{b}{tail}")


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
    stamp_readme(facts)
    print("wrote", CANVAS / "index.html")


if __name__ == "__main__":
    main()
