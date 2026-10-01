"""PHILO-12-02: the review page (../index.html) from the shots and facts.json.

Every board at 1440 x 900 (left) and 393 x 852 (right), in canvas order, with
the default or finding it answers. The art sheet (draw_sprites.py) leads.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANVAS = HERE.parent
SHOTS = CANVAS / "shots"

# id: (title, canvas, what it shows at 1440 / at 393, answers)
BOARDS: list[tuple[str, str, str, str, str]] = [
    ("F1-destinations-column", "F1 · Destinations at the right edge", "F",
     "1440: the folder, Slack and GitHub destinations in one column at the right edge, the brief icon on top; parked ones absent. 393: the list, no destination row, the brief row.",
     "defaults 1, 2, 6, 7"),
    ("F2-destination-menu", "F2 · A destination's menu: Open only", "F",
     "1440: Slack #leads selected, its menu holds Open, nothing else (Park and Remove stay in Settings). 393: the phone has no icon; Settings is the door.",
     "default 8; Open only supersedes grounding F2"),
    ("F2b-open-lands-on-row", "F2b · Open lands on that destination's row", "F",
     "Settings → Destinations opened at Slack #leads, the row open (not the add form).",
     "default 8; Astra r1 finding 6"),
    ("F3-no-destinations", "F3 · No destinations: nothing drawn", "F",
     "The folder parked through the real route, no stand-ins: no icon and nothing in their place. The brief stays.",
     "UX-CANON A.8"),
    ("F4-decision-sprite", "F4 · The decision's own sprite", "F",
     "1440: the decision wears the gavel (selected: the _sel image, the accent label chip) among notes. 393: the list row carries the same art.",
     "faces F2 (red on main: the note sprite)"),
    ("F5-six-channels", "F5 · The six channel sprites", "F",
     "1440: one destination per channel: folder, Slack, GitHub, Jira, Confluence, email. With the brief that is seven icons, and they fit ONE column: the column tightens from 128 to 106 px a cell before it wraps (the wrap is F6). 393: the same six in Send to ▸, each with its channel word.",
     "default 7"),
    ("F6-column-wraps", "F6 · The column wraps", "F",
     "1440: the brief and ten destinations. The column fills (tightened to 106 px a cell) and wraps LEFT; a cell that would overlap a drawer (Personal) or an object is skipped, so the four wrapped icons land in the free cells of the columns at x 1156, 1044 and 932 (between Personal, Egress guard and Desk), not in a neat second column. Measured with the engine's own hit test: each wrapped icon owns nine points of its cell, no wrapped icon overlaps a drawer, every drawer still hits as a drawer. 393: the ten in Send to ▸ (no icons on the phone).",
     "default 1; Astra canvas r1 finding 3"),
    ("G1-decision-held-over-slack", "G1 · A decision held over Slack #leads", "G",
     "1440: the tag Preview for Slack #leads, opened to the left near the edge, one line; the target lit. 393: the menu path, Send to ▸ open.",
     "default 4; faces F4"),
    ("G2-released-preview-open", "G2 · Released: the window, Slack picked, the preview", "G",
     "The decision window opens at the drop point with Slack #leads picked. THE ARRIVAL: once the preview has loaded, the pick brings itself into view; the window title, the picked row, the preview and Send (with HOOKS.SLACK.COM) are whole on screen. The rig does not scroll. Nothing sent.",
     "default 10; design §6"),
    ("G7-second-pick-in-place", "G7 · A second pick on the open window", "G",
     "The decision dropped again on Team folder (393: the Go menu, the window covering the list): the same window changes its pick in place (no second window).",
     "Astra r1 finding 4"),
    ("G3-sent", "G3 · Sent", "G",
     "He pressed Send: POSTED in the same well. A STAND-IN receipt: the shim answers the Slack send; nothing left the machine.",
     "design §6"),
    ("G4-no-summary-tag", "G4 · A meeting with no summary", "G",
     "1440: the tag NO SUMMARY in the warning look, the target not lit; release opens nothing. 393: Send to ▸ withheld on that meeting.",
     "faces F5; default 3"),
    ("G4b-no-published-update-tag", "G4b · A project with no published update", "G",
     "1440: the tag NO PUBLISHED UPDATE. 393: Send to ▸ withheld on that project.",
     "default 5"),
    ("G4c-parked-tag", "G4c · A destination parked since the last read", "G",
     "1440: the tag PARKED over the GitHub icon still on the Floor. 393: after the read, Send to ▸ no longer lists it.",
     "design §6"),
    ("G5-meeting-summary-picked", "G5 · A meeting dropped: Summary first", "G",
     "The meeting window, the picker on SUMMARY, Slack #leads picked and its preview; the arrival brings the picker, the row and Send into view (no rig scroll).",
     "default 9"),
    ("G8-digest-keeps-destination", "G8 · Summary → Digest keeps the destination", "G",
     "The picker moved to DIGEST: Slack #leads stays picked, the digest's preview loads for it, and the arrival holds the picker, the row and Send in view.",
     "Astra r1 finding 4"),
    ("G6-project-latest-update", "G6 · A project dropped: its latest published update", "G",
     "The Room at the Update posture on the latest published update, Team folder picked. The arrival clears the Room's sticky Back strip: the title, the picked row, the preview and Send are whole on screen with no rig scroll (393 is the case Astra r1 caught).",
     "default 5; Astra r1 finding 1"),
    ("G9a-room-on-older-update", "G9a · The Room open on an older update", "G",
     "Before: he has the older published update open in the Room (one milestone in its Progress).",
     "Astra r1 finding 1"),
    ("G9b-room-switched-to-linked-update", "G9b · The open Room switches to the linked update", "G",
     "A pick on the project from the menu bar (the open Room covers its icon at 1440 and the list at 393): the open Room switches to the latest published update (Old ledger frozen in its Progress), Slack #leads picked, and arrives clear of the Back strip (no rig scroll).",
     "Astra r1 finding 1"),
    ("H1-decision-menu", "H1 · Send to ▸ on a decision", "H",
     "1440: right-click on the decision: Open, Send to ▸, then the rest. 393: the list row menu, opened by a touch long-press.",
     "faces F1; Astra r1 finding 5"),
    ("H2-send-to-open", "H2 · Send to ▸ open", "H",
     "1440: the submenu beside the panel, each destination with its channel word. 393 (by touch): the submenu replaces the panel; the first row reads ◂ Back · Send to, its mark outside the glyph lane (shown even with glyphs off), its accessible name Back.",
     "design §3"),
    ("H2b-list-send-to", "H2b · The same menu in the list (1440)", "H",
     "The list view at desktop width: the row menu with Send to ▸ open.",
     "Astra r1 finding 2 (one composition)"),
    ("H2c-back-returns", "H2c · Back returns (393)", "H",
     "A touch tap on Back: the panel's top level again, Send to ▸ in its place; a second tap opens it again. 393 only: at 1440 the submenu sits beside the panel and has no back row.",
     "Astra canvas r1 finding 2"),
    ("H3-add-destination", "H3 · No destinations: Add destination", "H",
     "Send to ▸ holds one row, Add destination.",
     "Phase 10 B2"),
    ("H3b-add-destination-opens-form", "H3b · Add destination opens the form", "H",
     "Settings → Destinations with the add form open.",
     "Phase 10 B2"),
    ("H4-note-withheld", "H4 · A note: Send to ▸ withheld", "H",
     "The note's menu has no Send to ▸ (not a ghost row).",
     "default 3; UX-CANON A.11"),
    ("H5-menu-bar-send-to", "H5 · The menu bar", "H",
     "1440: the Object menu, the decision selected, Send to ▸ right after Open. 393: the compact Go menu, the same entry.",
     "Astra r1 finding 2"),
    ("H6-brief-row-send-to", "H6 · The brief row in the list", "H",
     "The brief row (BRIEF <day>) in the list with Send to ▸ open.",
     "default 6; Astra r1 finding 5"),
    ("H7a-read-loading", "H7a · A read still loading: CHECKING", "H",
     "The meeting's summary read held loading: the row reads Send to · CHECKING and stays.",
     "design §2 (pending is never a refusal)"),
    ("H7b-read-failed", "H7b · A failed read: CAN'T CHECK", "H",
     "The read failed: Send to · CAN'T CHECK; the rows stay pickable.",
     "design §2; UX-CANON A.10"),
    ("H7c-failed-pick-opens-window", "H7c · A pick on a failed read opens the window", "H",
     "Team folder picked on the failed read: the meeting window opens with the pick on its Summary; its well tells the truth (a summary: the preview), and the arrival brings it into view.",
     "design §2"),
    ("I4-no-brief", "I4 · No brief yet: no icon, no row", "I",
     "Before any brief: no brief icon on the Floor (1440) and no brief row in the list (393).",
     "default 6"),
    ("I1-brief-icon", "I1 · The brief icon", "I",
     "1440: the brief icon BRIEF <day> at the top of the column, selected. 393: the brief row in the list.",
     "default 6"),
    ("I2-brief-opened", "I2 · Opened: Intelligence → BRIEF", "I",
     "Intelligence → BRIEF on the exact stored id (read by id, GET /api/brief/{id}).",
     "default 6; Astra r1 finding 4"),
    ("I3-brief-dropped", "I3 · The brief dropped on Slack #leads", "I",
     "Intelligence → BRIEF with Slack #leads picked and the brief's preview, arrived in view (no rig scroll).",
     "default 6"),
    ("J1-artifact-window-well", "J1 · The artifact window with its SEND well", "J",
     "The artifact window: the body, then SEND with the destinations; its three raw buttons are library Buttons.",
     "faces F10; default 11"),
    ("J2-artifact-dropped-on-folder", "J2 · An artifact dropped on the folder", "J",
     "Team folder picked, arrived in view (no rig scroll); the preview is the stored body with the synthesis source footer left out (the shim's render of story 01's source).",
     "default 11; design §4"),
    ("J2b-artifact-saved", "J2b · Saved", "J",
     "He pressed Send: SAVED in the same well. A STAND-IN receipt: the artifact source is story 01's, so the shim answers this send with a made-up file path; nothing is written.",
     "design §4"),
]


def summary(facts: dict) -> list[str]:
    """The measurements, computed from facts.json (no number typed by hand)."""
    boards = {k: v for k, v in facts.items() if not k.startswith("_")}
    named = [n for f in boards.values() for n in f.get("named", [])]
    rows = [r for f in boards.values() for r in f.get("row_points", [])]
    tags = [f["tag"] for f in boards.values() if f.get("tag")]
    errs = sum(len(v) for k, v in facts.items() if k.startswith("_browser_errors_"))
    fails = sum(len(v) for k, v in facts.items() if k.startswith("_fails_"))
    count = lambda key: sum(1 for f in boards.values() if f.get(key))
    return [
        f"Renders: **{len(boards)}** ({sum(k.endswith('-1440') for k in boards)} at 1440, {sum(k.endswith('-393') for k in boards)} at 393), each width on its own hub and HOME. Fence failures: **{fails}**.",
        f"Named elements WHOLE on screen (the full box inside the viewport and every clipping ancestor, on top at nine points; the canvas world counted by the engine's probe instead): **{sum(n['ok'] for n in named)} of {len(named)}**.",
        f"Arrival boards with no rig scroll, the window title, the picked row, the preview's first field and Send each whole on screen: **{sum(1 for k, f in boards.items() if f.get('arrival') and all(n['ok'] for n in f['named']))} of {sum(1 for f in boards.values() if f.get('arrival'))}**.",
        f"Menu rows at 393 (the chrome strip rule: 44 px high, nine points owned, measured with elementFromPoint): **{sum(r['h'] >= 44 and r['own'] == 9 for r in rows)} of {len(rows)}**.",
        f"Drop tags drawn: **{len(tags)}** ({', '.join(sorted(set(tags)))}); tags with the word Send: **{sum('send' in t.lower().replace('preview for', '') for t in tags)}**; egress chips on a tag: **{count('tag_has_egress_chip')}**.",
        f"Raw `<button>` in the proposal (menus, tag, artifact window): **{sum(len(f.get('raw_buttons', [])) for f in boards.values())}**. Text under 12 px in the proposal: **{sum(len(f.get('small_text', [])) for f in boards.values())}**. Counters of zero: **{count('zero_counter')}**. Modals: **{count('modal')}**. Horizontal overflow: **{count('h_overflow')}**.",
        f"Browser errors (page errors and console errors other than 4xx reads): **{errs}**.",
    ]


def main() -> None:
    facts = json.loads((SHOTS / "facts.json").read_text()) if (SHOTS / "facts.json").exists() else {}
    fails = sum(len(v) for k, v in facts.items() if k.startswith("_fails_"))
    keys = [k for k in facts if not k.startswith("_")]
    out = ["""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phase 12 canvases</title><style>
:root{--bg:#0f1115;--fg:#e8e6e1;--muted:#a3a09a;--line:#2a2d33}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--bg:#f6f5f2;--fg:#1b1c1f;--muted:#55575c;--line:#d9d6cf}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif} main{max-width:1500px;margin:0 auto;padding:16px}
h1{font-size:22px} .m{color:var(--muted)} .board{border-top:1px solid var(--line);padding:14px 0} h2{font-size:17px;margin:0 0 4px}
h2 small{color:var(--muted);font-weight:400} .pair{display:flex;gap:12px;align-items:flex-start;flex-wrap:wrap}
.pair img{max-width:100%;height:auto;border:1px solid var(--line)} .pair a:first-child{flex:3 1 480px} .pair a:last-child{flex:1 1 180px;max-width:300px}
.art img{image-rendering:pixelated;max-width:360px}
</style></head><body><main><h1>PHILO-12-02 · the canvases F–J (round one)</h1>""",
           f"<p class='m'>The real product on an isolated hub; the unbuilt wire and the proposed composition stated in harness/p12.ts. "
           f"Left 1440 × 900, right 393 × 852.</p><ul class='m'>" + "".join(f"<li>{html.escape(x).replace('**', '')}</li>" for x in summary(facts)) + "</ul>",
           "<section class='board art'><h2>The art <small>default 7; faces F2</small></h2>"
           "<p>Rows: the decision (a gavel), the brief (a folded broadsheet), FILE, GITHUB, JIRA, CONFLUENCE, EMAIL, SLACK. "
           "Columns: rest, _sel, _stale (the product's own state script). 64 × 64 pixel art, house palette, no brand logos.</p>"
           "<a href='shots/sprite-sheet.png'><img src='shots/sprite-sheet.png' alt='The proposed sprites at four times size'></a></section>"]
    for bid, title, canvas, what, answers in BOARDS:
        e = html.escape
        imgs = "".join(
            f"<a href='shots/{bid}-{w}.png'><img src='shots/{bid}-{w}.png' alt='{e(title)} at {w}'></a>"
            for w in (1440, 393) if (SHOTS / f"{bid}-{w}.png").exists())
        out.append(f"<section class='board' id='{bid}'><h2>{e(title)} <small>{canvas} · {e(answers)}</small></h2>"
                   f"<p>{e(what)}</p><div class='pair'>{imgs}</div></section>")
    out.append("</main></body></html>")
    (CANVAS / "index.html").write_text("\n".join(out))
    print("wrote index.html,", len(BOARDS), "boards")
    print("\n".join(f"- {x}" for x in summary(facts)))


if __name__ == "__main__":
    main()
