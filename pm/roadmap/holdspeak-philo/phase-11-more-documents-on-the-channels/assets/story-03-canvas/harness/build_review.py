"""Build the owner's review page from the shots and facts that shoot.py wrote:
../index.html -- every board at 1440 x 900 and 393 x 852, side by side, with
its one line and the ruling it answers. The measurement line is computed from
facts.json here, never typed."""
from __future__ import annotations

import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANVAS = HERE.parent
SHOTS = CANVAS / "shots"

# (board id, canvas, title, what it shows, what it answers)
BOARDS = [
    ("0a-today-aftercare-slack-rows", "Today", "Today: the aftercare Slack rows", "The Meetings record on today's product with a webhook in config.json: DIGEST → SLACK and FOLLOW-UP → SLACK, each with a Send that only proposes.", "R7: what goes"),
    ("0b-today-credentials-slack-row", "Today", "Today: the Credentials Slack webhook row", "Settings → Connections → Credentials: the Slack webhook row (hooks.slack.com, SET).", "R7: what goes"),
    ("0c-today-room-record-open", "Today", "Today: Open on a Room decision row", "The Room's DECISIONS & COMMITMENTS rows are decision records. Open was pressed on the MTG row: no window opens (one window before, one after).", "design 6a unknown; defect, ledgered"),
    ("A1-brief-chair-no-destination", "A", "A1 · Chair: no destination", "Under the Chair's BRIEF: SEND · NO DESTINATION + Add destination. Each unfolded meeting row carries its own well (C6).", "R4; faces §6 A1"),
    ("D1-slack-form", "D", "D1 · The Slack form", "Settings → Destinations, Channel SLACK: Webhook (typed once, never shown), Channel name #leads, Name filled from it, Save, HOOKS.SLACK.COM.", "R6; design §5"),
    ("D2b-webhook-refused", "D", "D2 · A URL that is not a webhook", "https://example.com/hooks/abc: KEY NOT SAVED · WEBHOOK NOT VALID. Nothing kept.", "design §5 host rule"),
    ("D2a-webhook-saved", "D", "D2 · The webhook saved", "The webhook in the keychain: SET. The URL is never shown again (fact: key_row_text has no hooks.slack.com/services).", "design §5 secret"),
    ("D3-slack-row-checked", "D", "D3 · The Slack row, checked", "Slack #leads: SLACK · #leads · WEBHOOK SET · HOOKS.SLACK.COM. Open: Check → WEBHOOK SET · HOST OK (no test post); Edit; Remove.", "design §5 Check"),
    ("D4-credentials-no-slack-row", "D", "D4 · Credentials without the Slack row", "The same Credentials group as 0b: no Slack webhook row. He adds a Slack destination; no migration.", "R7"),
    ("A2-brief-picked-folder", "A", "A2 · The brief, a destination picked", "Intelligence → BRIEF, under PEOPLE: SEND. Team folder picked: FOLDER, Send + THIS DEVICE, then the brief as it will be written.", "R4; faces §6 A2"),
    ("A3-brief-saved-history", "A", "A3 · The brief sent; its history", "The row's ✓ SAVED 21:19; the history SENDS 1 with the exact file path. No Mark delivered.", "R8; F8 (SENDS, settled)"),
    ("A6-brief-slack-person-sections", "A", "A6 · The person sections in the preview", "Slack picked: the preview in Slack text, scrolled to *People* · Priya Nair: they owe 1 (0d). No Ack/Defer marks in the text.", "R1"),
    ("A5-brief-changed-send-again", "A", "A5 · The brief changed after a send", "Same-day Generate returned the SAME brief id; a new person signal changed its words. The preview shows Marek Wolny; no old-version word.", "R9; same-day id (Astra r1 F4)"),
    ("A5b-brief-changed-verb", "A", "A5 · Send again", "The same row: Send again + ✓ SAVED from the last send. He presses Send again for the new words.", "R9"),
    ("A4-brief-prepared-chair", "A", "A4 · Prepared by the steward: the Chair head", "BRIEF · 9 THINGS WAITING, and ◆ PREPARED ×1 · THIS DEVICE · Generate. At 393 the chips and Generate wrap under the label (round two); the label keeps its line.", "faces §6 A4; Astra r1 F1"),
    ("A4b-brief-prepared-row", "A", "A4 · The prepared row", "First in SEND: ◆ Slack #leads · PREPARED · BY STEWARD · BRIEF SEP 29 · time · WEBHOOK SET · HOOKS.SLACK.COM; open: Send, Discard.", "faces §6 A4"),
    ("A4c-brief-prepared-posted", "A", "A4 · The prepared send, posted", "The row stays as its result: ✓ POSTED · #leads · BY STEWARD. SENDS 2. POSTED has no link.", "R6: POSTED, never a link"),
    ("T3a-chair-last-item", "T", "T3 · The last brief item", "All items but one handled: BRIEF · 1 THING WAITING, Ack, Defer; the well below.", "T3 (Astra r1 F8)"),
    ("T3b-chair-after-last-ack", "T", "T3 · After the last Ack", "The Chair changed branch (headline, ALL 9 HANDLED); SEND and SENDS 2 are still on the section.", "T3"),
    ("T3c-scrolled-clear-of-capture-bar", "T", "T3 · Ordinary scrolling", "After the branch change, the wheel scrolls the Chair: the Slack #leads row and SENDS clear the sticky capture bar at 393; the receipt survives (fact cleared_by_wheel).", "T3; Astra r1 F1"),
    ("B1-decision-window-picked", "B", "B1 · The decision window (400 px), Slack picked", "Under CONSEQUENCES: SEND; Slack #leads open: CHANNEL, WEBHOOK, Send + HOOKS.SLACK.COM, the Slack text. Copy stays in the footer.", "R2, R4, R8 (Copy); F7"),
    ("B2-decision-posted-slack", "B", "B2 · Posted", "Send again + ✓ POSTED · #leads. The row: ✓ POSTED 21:20. No link.", "R6"),
    ("B2b-decision-history", "B", "B2 · The decision's history", "SENDS 1: ✓ Slack #leads · POSTED · #leads · time.", "R8"),
    ("B3-decision-edited-send-again", "B", "B3 · Edit after a send", "Edited on glass (Edit, Done): the preview shows Nov 5; the verb is Send again. No stale word.", "R9; F6"),
    ("T2a-preview-changed-fresh-preview", "T", "T2 · PREVIEW CHANGED", "The decision changed elsewhere after he read the preview. Send: REFUSED · PREVIEW CHANGED · NOTHING SENT; the well read a fresh preview (Nov 6).", "T2 (Astra r1 F8)"),
    ("T2a2-preview-changed-passage", "T", "T2 · The changed passage", "The same fresh preview, scrolled: *Decision* · Freeze the old ledger on Nov 6 on screen (fact changed_passage_on_screen).", "T2; Astra r1 F4"),
    ("T2b-preview-changed-sent", "T", "T2 · Another press", "Send again: ✓ POSTED; the text that went has Nov 6 (fact sent_text_has_nov6). SENDS 2.", "T2"),
    ("B5-record-intelligence-picked", "B", "B5 · The decision record, Intelligence → DECISIONS", "After its fields: SEND; Team folder picked: the record's decision, why, alternatives, owner, review, from, state — in the well's own face, not the receipt view's monospace (round two).", "R2; design 6a; Astra r1 F2"),
    ("B4-room-row-prepared-chip", "B", "B4 · The Room row with PREPARED ×1", "DECISIONS & COMMITMENTS: MTG Finance runs one more reconciliation… · CONFIRMED · ◆ PREPARED ×1. No Open: the row itself unfolds (fact room_open_verbs = 0).", "faces §6 B4; design 6a; Astra r1 F3"),
    ("B4b-room-row-open-prepared", "B", "B4 · The Room row open in place", "The row unfolds in place — the seat: SEND · ◆ Team folder · PREPARED · BY CODEX · D-…; Send, Discard. The dead Open is withheld (G1).", "B4; Q2; Astra r1 F3"),
    ("C1-meetings-record-send", "C", "C1 · The Meetings record (640 px)", "SUMMARY, then SEND with the form picker (SUMMARY) and the destinations; the transcript below.", "R3, R4; F7"),
    ("C2-summary-slack-picked", "C", "C2 · The summary to Slack", "Slack picked: the summary in Slack text (title, date, summary, Topics). Never the transcript (fact transcript_sentinel = false).", "R3"),
    ("C3-summary-posted-slack", "C", "C3 · Posted", "Send again + ✓ POSTED · #leads; the row ✓ POSTED. No link.", "R6"),
    ("C3b-summary-history", "C", "C3 · The meeting's history", "SENDS 1: ✓ Slack #leads · POSTED.", "R8"),
    ("C5-digest-form-slack", "C", "C5 · The digest: a form in the same well", "The picker set to DIGEST: What we decided, Still open. No DIGEST → SLACK rows anywhere on the record (fact).", "R3, R7"),
    ("C5c-digest-body", "C", "C5 · The digest body", "The digest preview scrolled: *What we decided* and its items on screen at both widths (fact digest_body_on_screen).", "R3; Astra r1 F4"),
    ("C5b-followup-form-folder", "C", "C5 · The follow-up to a folder", "The picker set to FOLLOW-UP: the follow-up draft as Markdown.", "R3"),
    ("C4-no-summary-no-well", "C", "C4 · No summary: no well", "Vendor call has no summary: no SEND well (fact send_wells = 0).", "faces §6 C4"),
    ("T1-over-slack-limit-refused", "T", "T1 · Over the Slack limit", "A 41,099-character summary to Slack: REFUSED · TOO LARGE FOR SLACK · 41,099 / 39,000 CHARACTERS · NOTHING SENT. Never NO ANSWER; no Send.", "T1; charter Q1 ruled 39,000"),
    ("C6-meeting-window-well", "C", "C6 · The meeting window", "The meeting window (400 px): SEND with the picker; the history; ACTION ITEMS below.", "R4"),
    ("C6b-chair-meetings-row-well", "C", "C6 · The Chair's MEETINGS row", "The unfolded Ledger cutover sync row: SUMMARY, then SEND (the picker at the 44 px target at 393) and SENDS 1.", "R4; G4"),
    ("E1a-update-well", "E", "E1 · The update", "The settled species on a published update, a preview open: the one row grammar, the well's own type; below it DELIVERY with To + Mark delivered (R8: the update only).", "UX-CANON §D; R8; Astra r1 F2"),
    ("E1b-brief-well", "E", "E1 · The brief", "The settled species in Intelligence → BRIEF, a preview open.", "UX-CANON §D; Astra r1 F2"),
    ("E1c-decision-well", "E", "E1 · A decision", "The settled species in the decision window, a preview open.", "UX-CANON §D; Astra r1 F2"),
    ("E1d-meeting-well", "E", "E1 · A meeting summary", "The settled species in the meeting window, with the form picker, a preview open.", "UX-CANON §D; Astra r1 F2"),
]


def main() -> None:
    facts = json.loads((SHOTS / "facts.json").read_text())
    keys = [k for k in facts if not k.startswith("_")]
    named = sum(len(facts[k]["named"]) for k in keys)
    named_ok = sum(1 for k in keys for v in facts[k]["named"] if v["ok"])
    owned = sum(facts[k]["pointer"]["owned"] for k in keys)
    missed = sum(len(facts[k]["pointer"]["missed"]) for k in keys)
    under = sum(len(facts[k]["pointer"]["reached_by_scroll"]) for k in keys)
    grammar = sum(len(facts[k].get("row_grammar", [])) for k in keys)
    grammar_ok = sum(1 for k in keys for g in facts[k].get("row_grammar", []) if g == "ok")
    mono = sum(1 for k in keys for x in facts[k].get("preview_fonts", []) if "Mono" in x)
    opens = sum(sum(facts[k].get("room_open_verbs", [])) for k in keys if not k.startswith("0"))
    small = sum(len(facts[k]["small_text"]["proposal"]) for k in keys)
    raw = sum(len(facts[k]["raw_buttons"]["proposal"]) for k in keys)
    modal = sum(1 for k in keys if facts[k]["modal"])
    overflow = sum(1 for k in keys if facts[k]["h_overflow"])
    stale = sum(1 for k in keys if facts[k]["stale_words"])
    links = sum(facts[k]["proof_links_on_slack"] for k in keys)
    md = sum(1 for k in keys if facts[k]["mark_delivered_in_new_kind"])
    errors = sum(len(v) for k, v in facts.items() if k.startswith("_browser_errors"))
    line = (f"{len(keys)} renders ({len(keys) // 2} boards × 2 widths). Named elements on screen: {named_ok} of {named}. "
            f"Pointer (9 points, 44 px at 393): {owned} proposal controls owned on all nine points ({under} of them reached by ordinary scrolling from under the host's sticky bar), {missed} with misses. "
            f"Rows in the one grammar: {grammar_ok} of {grammar}. Preview text in a mono face: {mono}. Open on a proposed Room decision row: {opens}. "
            f"Text under 12 px in the proposal (its headings included): {small}. Raw buttons in the proposal: {raw}. Modals: {modal}. Horizontal overflow: {overflow}. "
            f"Stale-version words: {stale}. Links on a Slack post: {links}. Mark delivered on a new kind: {md}. Browser errors: {errors}.")
    rows = []
    for bid, canvas, title, what, answers in BOARDS:
        rows.append(f"""<section class="board" id="{bid}"><h2>{html.escape(title)} <small>{canvas} · {html.escape(answers)}</small></h2>
<p>{html.escape(what)}</p><div class="pair"><a href="shots/{bid}-1440.png"><img src="shots/{bid}-1440.png" alt="{html.escape(title)} at 1440"></a>
<a href="shots/{bid}-393.png"><img class="phone" src="shots/{bid}-393.png" alt="{html.escape(title)} at 393"></a></div></section>""")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Phase 11 canvases</title><style>
:root{{--bg:#0f1115;--fg:#e8e6e1;--muted:#a3a09a;--line:#2a2d33}}
@media (prefers-color-scheme: light){{:root:not([data-theme="dark"]){{--bg:#f6f5f2;--fg:#1b1c1f;--muted:#55575c;--line:#d9d6cf}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}} main{{max-width:1500px;margin:0 auto;padding:16px}}
h1{{font-size:22px}} .m{{color:var(--muted)}} .board{{border-top:1px solid var(--line);padding:14px 0}} h2{{font-size:17px;margin:0 0 4px}}
h2 small{{color:var(--muted);font-weight:400}} .pair{{display:flex;gap:12px;align-items:flex-start;flex-wrap:wrap}}
.pair img{{max-width:100%;height:auto;border:1px solid var(--line)}} .pair a:first-child{{flex:3 1 480px}} .pair a:last-child{{flex:1 1 180px;max-width:300px}}
</style></head><body><main><h1>PHILO-11-03 · the canvases A–E and T1–T3 (round two)</h1>
<p class="m">The real product on an isolated hub; the unbuilt wire stated in harness/shim.ts. Left 1440 × 900, right 393 × 852. {html.escape(line)}</p>
{''.join(rows)}</main></body></html>"""
    (CANVAS / "index.html").write_text(page)
    print(line)


if __name__ == "__main__":
    main()
