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
    ("0-today", "0 · Today", "Today", "The real UpdatePosture on the real hub: Copy and Mark delivered only. No SEND well."),
    ("1-no-destination", "1 · No destination saved", "No destination saved", "SEND holds one token and one verb: NO DESTINATION + Add destination (opens Settings → Connections at Destinations, canvas B board 1)."),
    ("2-destinations", "2 · Destinations listed", "Destinations listed", "One row per destination: name, channel, target, account state (Phase 9 B1 words), last send, the egress chip (THIS DEVICE, SYNCED FOLDER or the host)."),
    ("3-picked-folder", "3 · Folder picked", "Destination picked", "The pick opens the row in place (question A1): the preview parsed back from the frozen bytes (FOLDER, FILE, then the Markdown), then Send and the egress chip."),
    ("4-saved-folder", "4 · Folder SAVED", "SENT", "The row gains ✓ SAVED; the DELIVERY history gains the row with the full path."),
    ("5-picked-github", "5 · GitHub picked", "Destination picked", "Preview fields REPOSITORY, ISSUE, ACCOUNT (the concrete login and host)."),
    ("6-sending", "6 · Sending", "Sending", "The answer is held: Send is busy; the pick cannot move; nothing else moves. The double-click made one send (board 7 fact)."),
    ("7-posted-github", "7 · GitHub POSTED", "SENT", "✓ POSTED + the comment link. Fact: dispatches after the double-click = 1."),
    ("8-picked-jira", "8 · Jira picked", "Destination picked", "Preview fields WORK ITEM, ACCOUNT; the body as plain text (the Jira payload is plain text)."),
    ("9-unknown-jira", "9 · Jira UNKNOWN", "UNKNOWN", "Fixture fault: no answer. ⚠ RESULT UNKNOWN · NO ANSWER + Check PAY-121 (opens the work item). Send again is a new send with a new key."),
    ("10-picked-confluence", "10 · Confluence picked", "Destination picked", "Preview fields SPACE, TITLE, ACCOUNT; the blog post body parsed back from the XHTML (never raw XHTML)."),
    ("11-refused-confluence-sign-in", "11 · REFUSED: not signed in", "REFUSED", "The account needs sign-in: ✗ REFUSED · NOT SIGNED IN · NOTHING SENT. Refused before the boundary: nothing ran."),
    ("12-picked-email", "12 · Email picked", "Destination picked", "Preview fields FROM, TO, CC, SUBJECT; the text body parsed back from the SendGrid request bytes."),
    ("13-failed-email-sender", "13 · FAILED: sender not verified", "FAILED", "Fixture fault: SendGrid's pinned 403 whole-request rejection. ✗ FAILED · SENDER NOT VERIFIED · NOTHING SENT (design section 8: a FAILED outcome, not a refusal)."),
    ("14-accepted-by-sendgrid", "14 · Email ACCEPTED BY SENDGRID", "SENT", "✓ ACCEPTED BY SENDGRID + ID <message id>. The word is never DELIVERED on an email row."),
    ("15-refused-github-account", "15 · REFUSED: GitHub account changed", "REFUSED", "The gh login at dispatch is not the saved login: ✗ REFUSED · GITHUB ACCOUNT CHANGED · NOTHING SENT."),
    ("16-lost-answer-a", "16 · The answer lost (update A)", "UNKNOWN", "Fixture fault: the send settles, then its answer is lost. NO ANSWER · RESULT UNKNOWN and Retry (the same key)."),
    ("17-update-b-clean", "17 · Update B is clean", "UNKNOWN", "The lost answer is bound to update A (Phase 9 r2 F1): update B has no lost line, no Retry, no open row, no history."),
    ("18-back-on-a-retry", "18 · Back on update A", "UNKNOWN", "The lost line and Retry are still on A."),
    ("19-retried-one-dispatch", "19 · Retry: one dispatch", "SENT", "Retry with the same key reads the stored row. Fact: dispatches with the lost key = 1."),
    ("20-unknown-after-restart", "20 · UNKNOWN after a restart", "UNKNOWN after a restart", "Fixture fault: a restart after the boundary. The row settles ⚠ RESULT UNKNOWN · INTERRUPTED; no second dispatch."),
    ("21-prepared", "21 · PREPARED", "PREPARED", "Three prepared sends (the steward, an agent twice) sit first in SEND, open (question A3): who, revision, time, account, egress chip, the preview, Send and Discard."),
    ("22-prepared-sent", "22 · A prepared send, sent", "PREPARED", "Send on the steward's row: the row leaves PREPARED and joins DELIVERY."),
    ("23-prepared-destination-changed", "23 · DESTINATION CHANGED", "DESTINATION CHANGED", "The folder now resolves elsewhere: REFUSED · DESTINATION CHANGED. The email destination is parked: REFUSED · DESTINATION PARKED. Only Discard stays."),
    ("24-discard-armed", "24 · Discard armed", "DESTINATION CHANGED", "The library ConfirmVerb: Discard? (a second press discards)."),
    ("25-discarded", "25 · Discarded", "DESTINATION CHANGED", "The row goes. No counter of zero."),
    ("26-history-several", "26 · Several sends", "Several sends", "One DELIVERY history: each send its own row with its proof; the manual Mark delivered row (DELIVERED · MANUAL) kept beside them. Head: DELIVERY N · UNKNOWN M."),
    ("27-list-chips", "27 · The update list", "Several sends", "Chips on the published update: PREPARED ×K, UNKNOWN ×M, DELIVERY ×N (question A2). No chip at zero (the other update)."),
    ("28-draft-no-send", "28 · A draft", "", "A draft has no SEND well: only a published update leaves the machine."),
]

DEST_BOARDS = [
    ("1-empty-from-room", "1 · Empty, reached from the Room", "The Room's Add destination opens Settings → Connections at the Destinations group (questions B1, B2): the add form, open."),
    ("2-add-folder", "2 · Add a folder", "Channel FOLDER: Folder and Name. The name fills from the target and stays editable (question B3). The SYNCED mark is the owner's."),
    ("3-add-synced-folder", "3 · Add a synced folder", "The SYNCED mark set: the row will carry SYNCED FOLDER, not THIS DEVICE."),
    ("4-add-github", "4 · Add a GitHub comment", "Repository, Issue or Pull request, Number. The account is the gh login of today (✓ CONNECTED KWORK)."),
    ("5-jira-one-key", "5 · REFUSED: one key only", "Two keys typed: ✗ REFUSED · ONE KEY ONLY; nothing saved."),
    ("6-add-email-key-set", "6 · Add an email (SendGrid)", "Provider SENDGRID; From, From name; the SendGrid key typed once into the OS keychain: the face shows SET, never the key (fact: key text on the face = false); To, Cc."),
    ("7-list", "7 · The list", "Seven destinations, one row each: channel, target, account state, egress chip."),
    ("8-row-open-checked", "8 · A row open, checked", "The row opens in place: Check (✓ CHECKED + time), Edit, Remove."),
    ("9-edit", "9 · Edit", "Edit opens the same form, filled. Save makes a new row and parks the old one (a row never changes)."),
    ("10-edited-old-parked", "10 · The old row parked", "The PARKED fold holds Jira PAY-118; the list shows Jira PAY-121."),
    ("11-remove-armed", "11 · Remove armed", "The library ConfirmVerb: Remove?"),
    ("12-removed-parked", "12 · Removed = parked", "The row leaves the list and goes into PARKED (history kept)."),
]


def summary(facts: dict) -> dict:
    boards = {k: v for k, v in facts.items() if not k.startswith("_")}
    ptr = [c for v in boards.values() for c in v["pointer"]]
    touched = [c for c in ptr if c["touched"]]
    mins = [v["min_contrast"] for v in boards.values() if v["min_contrast"] is not None]
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
            f"proposal raw buttons {m['raw_proposal']}{raw_inh}; horizontal overflow {m['overflow']}; lowest contrast {m['contrast_min']}:1, "
            f"under 4.5:1 {m['contrast_low']}; proposal controls {m['touched']}, points {m['points']}, not owned {m['touched_not_owned']}; "
            f"modals {m['modal']}; raw JSON or XHTML in a preview {m['raw_preview']}; DELIVERED on an email row {m['email_delivered']}; browser errors {m['errors']}.")


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
    "The wire is unbuilt (stories 01–03). <code>harness/shim.ts</code> stands in for it and says how in its header: stored destination and send records, the frozen payload bytes, the dispatch boundary, recovery after a restart. Every other request goes to a real hub on an isolated HOME.",
    "The dispatch is a stand-in: nothing leaves the machine. Fixture faults (no answer, lost answer, restart, sender not verified, changed gh login, a moved folder) are named on their boards.",
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
<tr><td>History and list</td><td>head <code>DELIVERY N · UNKNOWN M</code>; list chips <code>PREPARED ×K</code>, <code>UNKNOWN ×M</code>, <code>DELIVERY ×N</code>; no chip at zero</td></tr>
</table>"""
    send_q = [
        "<b>The pick:</b> picking a destination opens its preview and Send in place, under that row (no popover, no modal)? <b>Recommended: yes.</b>",
        "<b>The record words:</b> <code>DELIVERY N</code> (history head) and <code>DELIVERY ×N</code> (list chip), replacing the ratified <code>DELIVERED ×N</code> (Phase 9 Q2)? An email that SendGrid accepted is not delivered, and this history holds such rows. <b>Recommended: yes.</b>",
        "<b>Prepared sends:</b> they sit first in SEND, open, with a <code>PREPARED ×K</code> chip on the update list? <b>Recommended: yes.</b>",
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
        "<b>The Room's verb:</b> <code>Add destination</code> in the Room opens Settings there, and does not add a destination in the Room? <b>Recommended: yes.</b>",
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
