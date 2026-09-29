"""Build the owner's two review pages from the shots and facts that shoot.py
wrote: ../index.html (canvas A, the SEND well) and
../../story-04-destinations-canvas/index.html (canvas B, the Destinations
group). Every board at both widths; the shots are linked by relative path.
The measurement line is computed from facts.json here, never typed."""
from __future__ import annotations

import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEND = HERE.parent
DEST = SEND.parent / "story-04-destinations-canvas"

SEND_BOARDS = [
    ("0a-today-list", "0a · Today: the list (story 01's face)", "Today", "The product today on story 01's REAL records (update C: a real file send SENT, a real UNKNOWN by story 01's ENAMETOOLONG recipe, a real manual row). The list: DELIVERED ×2 and RESULT UNKNOWN ×1. Question A2 is asked against this face."),
    ("0b-today-history", "0b · Today: the history (story 01's face)", "Today", "Story 01's history: DELIVERED 2; the UNKNOWN row reads ⚠ RESULT UNKNOWN · CHECK Long path folder. No SEND well."),
    ("1-no-destination", "1 · No destination saved", "No destination saved", "SEND holds one token and one verb: NO DESTINATION + Add destination."),
    ("2-back-in-the-room", "2 · Back in the Room, no reload", "Destinations listed", "After Add destination (canvas B boards 1–2: Settings arrives at the group), Save and closing Settings: the Room shows Folder Payments at once. The well reads its destinations again on the Settings change signal and on window focus. No harness scroll, no reload."),
    ("3-destinations", "3 · Destinations listed", "Destinations listed", "One row per destination: name, channel, target (exact spelling), account state (Phase 9 B1 words), last send, the egress chip."),
    ("4-picked-folder", "4 · Folder picked", "Destination picked", "The pick opens the row in place (A1). The preview's fields, then Send, then the body (the verbs sit above the body, in view at 393). An inline file send names only the FOLDER: story 01 mints the file name from the send id at the boundary."),
    ("5-saved-folder", "5 · Folder SAVED", "SENT", "✓ SAVED + the exact path in the open row; the row's chip keeps ✓ SAVED + time from the stored record."),
    ("6-saved-folder-history", "6 · SAVED in the history", "SENT", "The history row from story 01's one table: ✓ Folder Payments · SAVED · the exact path (exact case)."),
    ("7-picked-github", "7 · GitHub picked", "Destination picked", "Preview fields REPOSITORY, ISSUE, ACCOUNT (the concrete login and host); Send."),
    ("8-sending", "8 · Sending", "Sending", "The answer is held: Send is busy; the pick cannot move. The double-click made one send (board 9 fact)."),
    ("9-posted-github", "9 · GitHub POSTED", "SENT", "✓ POSTED + the comment link. Fact: dispatches after the double-click = 1."),
    ("10-picked-jira", "10 · Jira picked", "Destination picked", "Preview fields WORK ITEM, ACCOUNT; the body as plain text."),
    ("11-unknown-jira", "11 · Jira UNKNOWN", "UNKNOWN", "Fixture fault: no answer. RESULT UNKNOWN · NO ANSWER + Check PAY-121 (opens the work item); Send again is a new send with a new key."),
    ("12-commented-jira", "12 · Jira COMMENTED", "SENT", "Send again (a new key): ✓ COMMENTED + the work item link."),
    ("13-picked-confluence", "13 · Confluence picked", "Destination picked", "Preview fields SPACE, TITLE, ACCOUNT; the blog post body parsed back from the XHTML."),
    ("14-refused-confluence-sign-in", "14 · REFUSED: not signed in", "REFUSED", "The account needs sign-in: REFUSED · NOT SIGNED IN · NOTHING SENT."),
    ("15-blog-posted-confluence", "15 · Confluence BLOG POSTED", "SENT", "Fixture: he signed in again and came back to the window. ✓ BLOG POSTED + the post link."),
    ("16-picked-email", "16 · Email picked", "Destination picked", "Preview fields FROM, TO, CC, SUBJECT, parsed back from the SendGrid request bytes."),
    ("17-failed-email-sender", "17 · FAILED: sender not verified", "FAILED", "The from address is not a verified sender in SendGrid (canvas B board 11 said so): SendGrid's pinned 403, FAILED · SENDER NOT VERIFIED · NOTHING SENT; the row's chip LAST SEND FAILED stays."),
    ("18-accepted-by-sendgrid", "18 · Email ACCEPTED BY SENDGRID", "SENT", "Fixture: he verified the sender in SendGrid. ✓ ACCEPTED BY SENDGRID + ID <message id>, exact case."),
    ("19-accepted-history", "19 · ACCEPTED in the history", "SENT", "The history row: ✓ Email lena@acme.io · ACCEPTED BY SENDGRID · ID <message id>. Never DELIVERED on an email row."),
    ("20-refused-github-account", "20 · REFUSED: GitHub account changed", "REFUSED", "The gh login at dispatch is not the saved login: REFUSED · GITHUB ACCOUNT CHANGED · NOTHING SENT."),
    ("21-lost-answer-a", "21 · The answer lost (update A)", "UNKNOWN", "Fixture fault: the send settles, then its answer is lost. NO ANSWER · RESULT UNKNOWN and Retry (the same key)."),
    ("24-retried-one-dispatch", "24 · Back on A, Retry: one dispatch", "SENT", "Two facts, not boards (their screens repeat boards 3 and 21 once the clock is masked): on update B there is no lost line, no Retry, no open row, no history (update_b_clean); back on A the lost line and Retry are on screen (back_on_a_before_retry). Retry with the same key reads the stored row: ✓ SAVED. Fact: dispatches with the lost key = 1."),
    ("25-unknown-after-restart", "25 · UNKNOWN after a restart", "UNKNOWN after a restart", "A restart after the boundary. The history row as story 01 renders it: ⚠ RESULT UNKNOWN · CHECK Jira PAY-121, with INTERRUPTED; no second dispatch."),
    ("26-prepared", "26 · PREPARED", "PREPARED", "Five sends prepared by the steward and an agent sit first in SEND. One is open (the first): who, revision, time, account, egress, the preview's fields, Send and Discard in view (A3)."),
    ("26b-prepared-running-after-return", "26b · A prepared send running, after Back and return", "Sending", "The steward's send is held at the boundary. He goes Back and opens the update again: the row is still there, ◆ SENDING (the stored row is dispatching); the well reads again until it settles (Codex Astra r2 F2)."),
    ("26c-destination-running", "26c · Its destination while it runs", "Sending", "The destination row shows ◆ SENDING; its Send is busy and not enabled (fact send_enabled_while_running = false). No second send while one runs."),
    ("27-prepared-sent", "27 · A prepared send, sent", "PREPARED", "Released: the running row settles on the face with no reload and stays, closed, as its result: ✓ POSTED + link. The next prepared row opens."),
    ("28-prepared-failed", "28 · A prepared send, failed", "FAILED", "Fixture fault: SendGrid refuses the key. The row stays as its result: FAILED · SENDGRID KEY NOT VALID · NOTHING SENT (F1: a failed send never disappears)."),
    ("28b-destination-latest-failed", "28b · The destination shows the LATEST send", "FAILED", "Codex Astra r2 F1's order: lena's send was prepared at board 26; an inline send to lena went first and was ACCEPTED; then the older preparation was sent and FAILED. The destination row shows LAST SEND FAILED: the latest by story 01's dispatch_started_at, not by preparation (facts latest_by_dispatch = failed, latest_by_preparation = sent)."),
    ("28c-destination-reopened", "28c · Reopened: the receipt says what the header says", "FAILED", "Codex Astra r3 F1's sequence through reopening: the destination opened again shows LAST SEND FAILED in its header and FAILED · SENDGRID KEY NOT VALID as its receipt, both from the latest send by dispatch_started_at. The earlier ACCEPTED BY SENDGRID is not shown as the current result (fact reopened: receipts = [failed], success_shown = false)."),
    ("29-prepared-file-sent", "29 · A prepared file send", "SENT", "The prepared preview names the FILE (minted with the send id at prepare); the result names the same file. Fact: same_file = true."),
    ("30-prepared-destination-changed", "30 · DESTINATION CHANGED", "DESTINATION CHANGED", "The folder now resolves elsewhere: the chip DESTINATION CHANGED on the row; only Discard stays."),
    ("31-prepared-destination-parked", "31 · DESTINATION PARKED", "DESTINATION CHANGED", "He removed the Jira destination in Settings: DESTINATION PARKED; only Discard stays."),
    ("32-discard-armed", "32 · Discard armed", "DESTINATION CHANGED", "The library ConfirmVerb: Discard?"),
    ("33-discarded", "33 · Discarded", "DESTINATION CHANGED", "The row stays as its result: DISCARDED, who prepared it, when (F1)."),
    ("34-history-several", "34 · Several sends", "Several sends", "Story 01's one table: each send its own row with its proof, the UNKNOWN rows as story 01 renders them, the manual Mark delivered row (DELIVERED · MANUAL). Head DELIVERY N counts isDelivered rows only."),
    ("34b-history-manual", "34b · The manual row, UNKNOWN beside it", "Manual", "Mark delivered kept as the manual channel: ✓ Priya · DELIVERED · MANUAL, the last row of story 01's one table (the channel rows above it)."),
    ("35-list-chips", "35 · The update list", "Several sends", "PREPARED ×1, RESULT UNKNOWN ×M (story 01's chip, unchanged), DELIVERY ×N (A2). No chip at zero."),
    ("36-draft-no-send", "36 · A draft", "", "A draft has no SEND well: only a published update leaves the machine."),
    ("37-destinations-unreadable", "37 · Destinations: no answer", "Read failure", "The destinations read gets no answer: CANNOT READ DESTINATIONS + Retry. Never NO DESTINATION."),
    ("38-sends-unreadable", "38 · Sends: no answer", "Read failure", "The sends read gets no answer: CANNOT READ SENDS + Retry."),
    ("39-history-unreadable", "39 · History: no answer", "Read failure", "The history read gets no answer: CANNOT READ HISTORY + Retry. Never an empty history."),
    ("40-preview-failed", "40 · Preview: no answer", "Read failure", "The preview gets no answer: NO PREVIEW · NO ANSWER + Retry; Send is not offered."),
]

DEST_BOARDS = [
    ("1-arrive-from-room", "1 · Arrive from the Room", "The Room's Add destination opens Settings AT the Destinations group, in view, with the add form open (B1, B2). The group scrolls itself into view; the harness does not scroll."),
    ("2-add-folder", "2 · Add a folder", "Folder and Name (filled from the target, editable: B3); Save. After Save and closing Settings, the Room shows it (canvas A board 2)."),
    ("3-add-synced-folder", "3 · Add a synced folder", "The SYNCED mark set: the egress chip reads SYNCED FOLDER, not THIS DEVICE."),
    ("4-add-github", "4 · Add a GitHub comment", "Repository, Issue or Pull request, Number. The account is today's gh login."),
    ("5-jira-one-key", "5 · REFUSED: one key only", "Two keys typed: REFUSED · ONE KEY ONLY; nothing saved."),
    ("6-add-confluence", "6 · Add a Confluence blog post", "The Confluence account (SIGN IN), Space id, Name."),
    ("7-key-not-saved", "7 · KEY NOT SAVED", "Fixture fault: no safe OS key store. KEY NOT SAVED · NO SAFE KEY STORE; the key is not shown."),
    ("8-add-email-key-set", "8 · Add an email (SendGrid)", "From, From name; the SendGrid key typed once into the OS keychain: SET, never the key; To, Cc."),
    ("9-list", "9 · The list", "Seven destinations, one row each: channel, target (exact spelling), account state, egress chip."),
    ("10-row-open-checked", "10 · GitHub checked", "The row opens in place: Check → CHECKED; Edit, Remove."),
    ("11-email-check-not-verified", "11 · Email Check: sender not verified", "Check asks SendGrid about the SENDER, not the key: SENDER NOT VERIFIED (F6)."),
    ("12-edit", "12 · Edit", "The same form, filled. Save makes a new row and parks the old one."),
    ("13-edited-old-parked", "13 · The old row parked", "PARKED holds Jira PAY-118; the list shows Jira PAY-121."),
    ("14-remove-armed", "14 · Remove armed", "The library ConfirmVerb: Remove?"),
    ("15-removed-parked", "15 · Removed = parked", "The row goes into PARKED, history kept."),
    ("16-destinations-unreadable", "16 · No answer", "The destinations read gets no answer: CANNOT READ DESTINATIONS + Retry; never the empty add form."),
]


def summary(facts: dict) -> dict:
    boards = {k: v for k, v in facts.items() if not k.startswith("_")}
    ptr = [c for v in boards.values() for c in v["pointer"]]
    touched = [c for c in ptr if c["touched"]]
    mins = [v["min_contrast"] for v in boards.values() if v["min_contrast"] is not None]
    low = min((v["min_contrast_el"] for v in boards.values() if v.get("min_contrast_el")), key=lambda e: e["ratio"], default=None)
    low_boards = sorted({k.rsplit("-", 1)[0] for k, v in boards.items() if v.get("min_contrast_el") and low and abs(v["min_contrast_el"]["ratio"] - low["ratio"]) < 1e-9})
    named = [n for v in boards.values() for n in v.get("named", [])]
    inherited_raw = sorted({x for v in boards.values() for x in v["raw_buttons"]["inherited"]})
    return {
        "renders": len(boards),
        "small_proposal": sum(len(v["small_text"]["proposal"]) for v in boards.values()),
        "small_inherited": sum(len(v["small_text"]["inherited"]) for v in boards.values()),
        "raw_proposal": sum(len(v["raw_buttons"]["proposal"]) for v in boards.values()),
        "raw_inherited_boards": sum(1 for v in boards.values() if v["raw_buttons"]["inherited"]),
        "raw_inherited": inherited_raw,
        "overflow": sum(1 for v in boards.values() if v["h_overflow"] or v["body_overflow_x"]),
        "contrast_min": min(mins) if mins else None,
        "contrast_min_el": low, "contrast_min_boards": low_boards,
        "named": len(named), "named_hidden": sum(1 for n in named if not n["ok"]),
        "contrast_low": sum(len(v["low_contrast"]) for v in boards.values()),
        "controls": len(ptr), "touched": len(touched), "points": 9 * len(touched),
        "touched_not_owned": sum(1 for c in touched if not c["owned"]),
        "inherited_not_owned": sum(1 for c in ptr if not c["touched"] and not c["owned"]),
        "modal": sum(1 for v in boards.values() if v["modal"]),
        "raw_preview": sum(1 for v in boards.values() if v["preview_has_raw"]),
        "email_delivered": sum(1 for v in boards.values() if v["words_delivered_on_email"]),
        "errors": sum(len(v) for k, v in facts.items() if k.startswith("_browser_errors")),
    }


def measure_line(m: dict) -> str:
    raw_inh = (f"; inherited raw buttons on {m['raw_inherited_boards']} renders ({', '.join(m['raw_inherited'])}, the library TransportKey, BACKLOG)"
               if m["raw_inherited_boards"] else "")
    return (f"Measured on {m['renders']} renders: text under 12 px {m['small_proposal']} in the proposal, {m['small_inherited']} inherited; "
            f"proposal raw buttons {m['raw_proposal']}{raw_inh}; horizontal overflow {m['overflow']}; lowest contrast {m['contrast_min']:.7f}:1 "
            f"({(m['contrast_min_el'] or {}).get('text', '')!r}, boards {', '.join(m['contrast_min_boards'])}), "
            f"under 4.5:1 {m['contrast_low']}; proposal controls {m['touched']}, points {m['points']}, not owned {m['touched_not_owned']}; "
            f"named elements on screen {m['named'] - m['named_hidden']} of {m['named']}; modals {m['modal']}; raw JSON or XHTML in a preview {m['raw_preview']}; DELIVERED on an email row {m['email_delivered']}; browser errors {m['errors']}.")


def pair(name: str, label: str) -> str:
    return (
        '<div class="pair">'
        f'<figure><img src="shots/{name}-1440.png" alt="{html.escape(label)} at 1440" loading="lazy"><figcaption>1440 × 900</figcaption></figure>'
        f'<figure><img src="shots/{name}-393.png" alt="{html.escape(label)} at 393" loading="lazy"><figcaption>393 × 852</figcaption></figure>'
        "</div>"
    )


CSS = """
:root { --bg:#f6f6f3; --fg:#1c1d21; --muted:#555a66; --line:#d4d5d9; --card:#ffffff; --accent:#1f7a52; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#15171d; --fg:#e7e8ec; --muted:#a3a9b6; --line:#2a2e3e; --card:#1b1e26; --accent:#4fd29a; } }
:root[data-theme="dark"] { --bg:#15171d; --fg:#e7e8ec; --muted:#a3a9b6; --line:#2a2e3e; --card:#1b1e26; --accent:#4fd29a; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.45 system-ui, -apple-system, sans-serif; }
main { max-width:1500px; margin:0 auto; padding:24px 16px 64px; }
h1 { font-size:24px; margin:0 0 4px; }
.sub { color:var(--muted); margin:0 0 12px; font-size:13px; }
.status { display:inline-block; font:600 12px ui-monospace, monospace; letter-spacing:.06em; border:1px solid var(--line); padding:2px 8px; margin-bottom:12px; }
.matrix { display:inline-block; font:600 12px ui-monospace, monospace; color:var(--accent); margin-left:6px; }
table { border-collapse:collapse; width:100%; margin:12px 0 20px; font-size:13px; background:var(--card); }
th, td { border:1px solid var(--line); padding:6px 8px; text-align:left; vertical-align:top; }
code { font:12px ui-monospace, monospace; }
.board { margin:28px 0; }
.board h2 { font-size:17px; margin:0 0 2px; }
.note { color:var(--muted); margin:0 0 8px; font-size:13px; }
.pair { display:grid; grid-template-columns:minmax(0,1fr) 220px; gap:12px; align-items:start; }
figure { margin:0; background:var(--card); border:1px solid var(--line); padding:6px; }
figure img { width:100%; height:auto; display:block; }
figcaption { font:12px ui-monospace, monospace; color:var(--muted); padding-top:4px; }
@media (max-width: 720px) { .pair { grid-template-columns:1fr; } }
"""


def page(title: str, sub: str, words: str, boards: list[str], questions: list[str], limits: list[str], m: dict) -> str:
    qs = "".join(f"<li>{q}</li>" for q in questions)
    ls = "".join(f"<li>{x}</li>" for x in limits)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>{html.escape(title)}</h1>
<p class="sub">{sub}</p>
<span class="status">DRAFT · FOR THE OWNER'S RATIFICATION</span>
{words}
<p class="sub">{html.escape(measure_line(m))}</p>
<section class="board"><h2>Three questions</h2><ol>{qs}</ol></section>
{''.join(boards)}
<section class="board"><h2>Limits</h2><ul>{ls}</ul></section>
</main>
</body>
</html>
"""


LIMITS_COMMON = [
    "Story 01 is built (#692): board 0 is its face on its real records. The rest of the send wire (stories 02–03, and the canvas's own states) is <code>harness/shim.ts</code>, which says how in its header: the records, the frozen payload bytes, the file name minted once with the send id, the dispatch boundary, recovery after a restart, and each settled send written as ONE row of story 01's history table, in story 01's shape. Every other request goes to a real hub on an isolated HOME.",
    "The dispatch is a stand-in: nothing leaves the machine. Fixture faults and fixture acts are named on their boards: no answer, a lost answer, a restart, a changed gh login, a moved folder, a refused key, a key store that is not safe, reads and a preview that get no answer, and his own acts outside HoldSpeak (he signs in to Atlassian again; he verifies the sender in SendGrid).",
    "The GitHub account (<code>kwork</code>, CONNECTED) and one Confluence account (SIGN IN) are overlaid on the Connections read; the Jira account is real (added through the real route, NEVER CHECKED).",
    "Proposal CSS: <code>harness/canvas.css</code>. Its repair block (the 12 px floor, the 44 px narrow target for gadget controls) names each library file the build moves it into.",
]


def main() -> None:
    sf = json.loads((SEND / "shots/facts.json").read_text())
    df = json.loads((DEST / "shots/facts.json").read_text())

    send_boards = []
    for key, title, row, note in SEND_BOARDS:
        tag = f'<span class="matrix">{html.escape(row.upper())}</span>' if row else ""
        send_boards.append(f'<section class="board"><h2>{html.escape(title)}{tag}</h2><p class="note">{html.escape(note)}</p>{pair(key, title)}</section>')
    send_words = """<table>
<tr><th>Slot</th><th>Words</th></tr>
<tr><td>Section</td><td><code>SEND</code>; empty: <code>NO DESTINATION</code> + <code>Add destination</code></td></tr>
<tr><td>Verbs</td><td><code>Send</code>, <code>Send again</code>, <code>Retry</code> (a lost answer only, the same key), <code>Discard</code> → <code>Discard?</code>, <code>Check &lt;target&gt;</code></td></tr>
<tr><td>SENT, per channel</td><td><code>SAVED</code>, <code>POSTED</code>, <code>COMMENTED</code>, <code>BLOG POSTED</code>, <code>ACCEPTED BY SENDGRID</code>; manual <code>DELIVERED</code></td></tr>
<tr><td>Outcomes</td><td><code>REFUSED · &lt;reason&gt; · NOTHING SENT</code>; <code>FAILED · &lt;reason&gt; · NOTHING SENT</code>; <code>RESULT UNKNOWN · &lt;reason&gt;</code>; <code>NO ANSWER · RESULT UNKNOWN</code></td></tr>
<tr><td>Result, where he looks</td><td>a destination row: <code>✓ SAVED 17:20</code>, <code>LAST SEND UNKNOWN</code>, <code>LAST SEND FAILED</code>; a prepared row that ended stays as its result, <code>DISCARDED</code> included</td></tr>
<tr><td>Read failures</td><td><code>CANNOT READ DESTINATIONS</code> / <code>SENDS</code> / <code>HISTORY</code> + <code>Retry</code>; <code>NO PREVIEW · NO ANSWER</code> + <code>Retry</code></td></tr>
<tr><td>History and list</td><td>story 01's one table; head <code>DELIVERY N</code> (delivered rows); the UNKNOWN row as story 01 renders it (<code>RESULT UNKNOWN · CHECK &lt;destination&gt;</code>); list chips <code>PREPARED ×K</code>, <code>RESULT UNKNOWN ×M</code>, <code>DELIVERY ×N</code>; no chip at zero</td></tr>
</table>"""
    send_q = [
        "<b>The pick:</b> picking a destination opens its preview and Send in place, under that row (no popover, no modal)? <b>Recommended: yes.</b>",
        "<b>The record word:</b> story 01's face today (boards 0a, 0b) reads <code>DELIVERED ×N</code> and already keeps UNKNOWN apart (<code>RESULT UNKNOWN ×M</code>). Change the word to <code>DELIVERY ×N</code> / <code>DELIVERY N</code>, with the same counts? The reason: the record now mixes channels, and a provider's acceptance (ACCEPTED BY SENDGRID) is not a delivery. <b>Recommended: yes.</b>",
        "<b>Prepared sends:</b> first in SEND, with a <code>PREPARED ×K</code> chip on the update list; ONE preview open (the first), each other one a click away with its Send and Discard; a prepared send that ended stays as its result? <b>Recommended: yes</b> (Codex Astra r1: first and chip yes; not all previews forced open).",
    ]
    (SEND / "index.html").write_text(page(
        "Send well canvas",
        "PHILO-10-04 canvas A · the SEND well on a published update · the product app, a real hub, library species; the unbuilt wire stated in harness/shim.ts",
        send_words, send_boards, send_q, LIMITS_COMMON, summary(sf)))

    dest_boards = [f'<section class="board"><h2>{html.escape(t)}</h2><p class="note">{html.escape(n)}</p>{pair(k, t)}</section>' for k, t, n in DEST_BOARDS]
    dest_words = """<table>
<tr><th>Slot</th><th>Words</th></tr>
<tr><td>Place</td><td>Settings → Connections, group <code>DESTINATIONS</code> under Tools</td></tr>
<tr><td>Verbs</td><td><code>Add destination</code>, <code>Save</code>, <code>Check</code>, <code>Edit</code>, <code>Remove</code> → <code>Remove?</code>, the key <code>Replace</code></td></tr>
<tr><td>Channels</td><td><code>FOLDER</code>, <code>GITHUB COMMENT</code>, <code>JIRA COMMENT</code>, <code>CONFLUENCE BLOG POST</code>, <code>EMAIL (SENDGRID)</code></td></tr>
<tr><td>Row chips</td><td>channel, target, account state (<code>CONNECTED</code>, <code>NEVER CHECKED</code>, <code>SIGN IN</code>, <code>KEY SET</code>, <code>NO KEY</code>), egress (<code>THIS DEVICE</code>, <code>SYNCED FOLDER</code>, the host)</td></tr>
<tr><td>Removed or edited</td><td>the <code>PARKED</code> fold; history kept</td></tr>
</table>"""
    dest_q = [
        "<b>The place:</b> destinations live in Settings → Connections, in a Destinations group under Tools? <b>Recommended: yes.</b>",
        "<b>The Room's verb:</b> <code>Add destination</code> in the Room opens Settings AT the group (board 1, in view with the form open), and the Room shows the new destination when he comes back, with no reload (canvas A board 2)? <b>Recommended: yes.</b>",
        "<b>The name:</b> a new destination's name fills from its target (<code>Folder Payments</code>, <code>Jira PAY-118</code>) and stays editable? <b>Recommended: yes.</b>",
    ]
    dest_limits = LIMITS_COMMON + [
        "The COPY key on the Jira account row (Settings → Connections, above the group) is the library TransportKey, a raw <code>&lt;button&gt;</code> (<code>web/src/desk/surface/gadgets.tsx:720</code>). The canvas does not touch it; the facts count it apart (BACKLOG).",
    ]
    (DEST / "index.html").write_text(page(
        "Destinations canvas",
        "PHILO-10-04 canvas B · the Destinations group in Settings → Connections · the product app, a real hub, library species; the unbuilt wire stated in ../story-04-send-canvas/harness/shim.ts",
        dest_words, dest_boards, dest_q, dest_limits, summary(df)))
    for p in (SEND / "index.html", DEST / "index.html"):
        print(p, p.stat().st_size)
    print("send", summary(sf))
    print("dest", summary(df))


if __name__ == "__main__":
    main()
