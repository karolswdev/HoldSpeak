# Send: what it is today (recon, 2026-10-17)

This is the "What it is today" input for `DESIGN.md` section 2. It covers
INVENTORY row 45 (Send to: destinations, preview, receipts) and every face
that hands a result to Send: a meeting, a note, a decision, a Draft update,
an Automation result, and a send that an agent prepared. I walked the jobs as
a first-time user at 1440x900 and 393x852. I fixed nothing. The shots are in
`shots/` (78 files; 8 duplicates from failed presses are parked in
`shots/_parked-duplicates/`). The rig is in the footnote.[^rig]

Nothing left the machine. Folder sends wrote real files into the scratch
HOME. GitHub and Jira sends went through a recording runner that answers in
place of `gh` and `acli`. Email and Slack sends went through the hub's
recording HTTPS edge, which answers in place of Resend and Slack. So every
send ran the product's real code up to the process or socket edge, and I read
the exact command it would have run.

Two desks:

- **The good day** (port 8861): every outside answer is a success.
- **The bad day** (port 8862): GitHub answers "issue not found", Slack
  answers HTTP 500, and the Jira comment never answers.

Seed: two meetings imported as transcripts (`Payments platform sync`, `1:1
with Theo`), summarized for real by the LAN engine (qwen3.8-27b), one note
(`Cutover risks for the VP`), one project (`Payments ledger cutover`), and
six destinations: the built-in HoldSpeak folder, a second folder, a GitHub
issue, a Jira work item, an email list (Mira, Theo, Jun) and a Slack channel.

## The jobs I walked

1. **First send.** Send this meeting's outcome to my team's folder.
2. **Save the places my team reads.** GitHub, Jira, Slack, email.
3. **Send to each place, and know it arrived.**
4. **A bad day.** A send fails, or gets no answer. What do I do?
5. **Send what HoldSpeak made for me**: a note, a decision, the Friday
   update, an Automation result.
6. **An agent prepares, I press Send.**

## 1. First send (a meeting)

- The meeting window's footer has a blue **Send** (`01-meeting-open-1440.png`).
  It does not send. It unfolds a **SEND** section at the foot of the
  Outcomes, 3 s later (`02-meeting-send-open-1440.png`).
- On a fresh desk the only destination is **HoldSpeak folder**, already
  picked, with its preview open (`02-meeting-send-well-1440.png`). The
  preview fills the window. The real Send button is under the preview, below
  the fold. A second **Send** stays in the footer.
- Above the destinations sits a gadget `↻ SUMMARY` with the choices
  `Summary · Digest · Follow-up`. Nothing says what each one contains.
- The Summary form holds only the summary and the topics. It does **not**
  hold what was decided or who owes what (`07-folder-preview-1440.png`). The
  Digest and Follow-up forms hold "Still open" / "Open items": every action
  item, including the ones I never confirmed (`08-github-preview-1440.png`).
- After **Send**: `✓ SAVED` and the path
  `~/Reports/2026-10-18-payments-platform-sync-summary-2026-10-16-6082eaec.md`
  (`07-folder-sent-1440.png`). The file was there, 561 bytes, with exactly
  the previewed text. The file name has tomorrow's date: the walk ran on
  17 Oct at 20:29 local time, which is 18 Oct in UTC.

## 2. Save the places my team reads

- **Add destination** in the well opens a second window, Settings ▸
  Accounts, on top of the meeting (`03-add-destination-settings-1440.png`).
  The form: `Channel ↻ FOLDER`, `Folder`, `SYNCED`, `Name`, `Save`, `Cancel`.
- A folder saved in 3 presses and two typed fields, 2.6 s
  (`04-folder-saved-1440.png`).
- **GitHub could not be saved from the face.** The form asks for an
  `Account`, which comes from the Accounts row above. That row ran its own
  check, `gh auth status`, and said `Unreachable · Checked now`
  (`05-github-rechecked-1440.png`). The form showed `— ⚠ UNREACHABLE · Set
  up account`, and Save stayed disabled (`05-new-dest-github-1440.png`).
  The send path checks the sign-in another way (`gh api user`), and through
  that path the same destination saved at once, as `@karol-arch`. In the rig
  the Accounts check cannot reach a real `gh`, so this is partly the rig. But
  the face has two sign-in checks for one account, and the stricter one
  blocks the save.[^twocheck]
- I saved GitHub, Jira, email and Slack through the hub's own tools (the same
  operation the form calls). The list then read `Destinations 6`
  (`06-destinations-saved-*.png`). Its chips: GitHub `⚠ UNREACHABLE`, Jira
  `○ NEVER CHECKED`, email and Slack no state at all.

## 3. Send to each place

All four went out from one meeting in about 5 s each
(`08-*-preview-1440.png`, `08-*-sent-1440.png`):

| Destination | Form | Preview shows | After Send | Recorded command |
|---|---|---|---|---|
| GitHub `acme/payments #42` | Follow-up | Repository, issue, account, then the rendered text | `✓ POSTED · acme/payments #42` (a link) | `gh issue comment 42 --repo acme/payments --body-file <file>` |
| Jira `PAY-12` | Summary | Work item, account, then **raw Markdown** (`# Payments platform sync`, `## Summary`, `- Ledger cutover`) | `✓ COMMENTED · PAY-12` | `acli jira auth switch`, `acli jira auth status` (each twice), then `acli jira workitem comment create --key PAY-12 --body-file <file>.txt --json` |
| Email to three people | Digest | From, To, Subject, then raw Markdown | `✓ ACCEPTED BY RESEND · ID re-walk-0001` | `POST api.resend.com /emails` |
| Slack `#payments-leads` | Digest | Channel, webhook host, Slack text (`*bold*`) | `✓ POSTED · #payments-leads` | `POST hooks.slack.com /services/[redacted]` |

- The GitHub row kept `⚠ UNREACHABLE` next to `✓ POSTED 20:31` in the same
  row (`08-github-sent-1440.png`). Jira kept `○ NEVER CHECKED` next to
  `COMMENTED`. A send that worked does not count as a check.
- Under the destinations, **SENDS 5** lists each send with its form, its
  proof and its time (`08-history-1440.png`, `21-meeting-sends-history-393.png`).
  This is the only place the proof is shown. Nothing on Today, Needs you,
  the dock or the desk says that something was sent.
- How a Jira comment looks to the team, I could not see. HoldSpeak writes
  the Markdown to a `.txt` file for `acli`. The code says the shape of the
  `acli` answer is "PROVISIONAL until a real send".[^jira]
- On the phone the well is a long list: six destinations take the whole
  screen, each three lines tall, and the footer **Send** stays
  (`21-meeting-send-well-393.png`).

## 4. A bad day

| Case | What I saw | Shot |
|---|---|---|
| GitHub answers "could not resolve issue 4242" | `✗ FAILED · ISSUE NOT FOUND · NOTHING SENT`; row: `LAST SEND FAILED`. The verb under it says `Send again`. | `19-github-failed-1440.png` |
| Slack answers HTTP 500 | `⚠ RESULT UNKNOWN · NO CLEAR ANSWER`; history: `RESULT UNKNOWN · CHECK #payments-leads`. Correct: a 500 can still have posted. | `19-slack-failed-1440.png` |
| Jira comment never answers | `◆ SENDING`, `Send again` disabled. After a page reload: still `SENDING`, still disabled, at both widths. No time, no way out on the face. | `19-jira-held-1440.png`, `20-after-reload-jira-sending-*.png` |
| The phone, all three | `LAST SEND FAILED · ISSUE NOT FOUND · NOTHING SENT`, `SENDING`, `LAST SEND UNKNOWN · NO CLEAR ANSWER` stacked as chips | `24-failed-states-393.png` |

The state survives a reload, which is good (T3, #1240). In the rig the held
Jira call never ends, so I did not see what the product shows when `acli`
times out (the limit is 60 s).[^timeout] None of the three cases reached
Needs you or the bell.

## 5. Send what HoldSpeak made

| Source | How I reached Send | Presses to the preview | What I met |
|---|---|---|---|
| A meeting | Footer **Send** | 2 | See §1. Also **Object ▸ Send to ▸** lists the six destinations (`18-meeting-object-send-to-1440.png`). I picked `PAY-12 ticket`; the well opened on `#payments-leads`, the destination I had used last, not the one I picked (`18-send-to-picked-1440.png`). |
| A note | Double-click the note: a reader with `Copy · Dictate about this · Develop this thought` and no Send (`10-note-open-1440.png`). Its Object menu has no Send to (`11-note-object-menu-1440.png`). **Develop this thought** opens the Thought window, which has **Send** (desktop) or **More ▸ Send** (phone) (`12-thought-window-*.png`). | 3 | Send is two windows deep, behind a verb named "Develop". |
| A decision | Confirm it in the meeting, then Today ▸ Decisions ▸ the row ▸ **Send** (`22-today-decisions-1440.png`, `22-decision-open-1440.png`) | 4 | Worked. Sent to Slack: `✓ POSTED` (`22-decision-slack-sent-1440.png`). |
| The Friday update | Room ▸ Draft update (51 s on the LAN engine) ▸ Publish ▸ the Send well (`13-*`, `14-update-published-1440.png`) | 3 + 51 s | Every destination answered `✗ REFUSED · NOTHING VERIFIED · NOTHING SENT` (`15-update-*-refused-1440.png`). The draft's claims were all `UNVERIFIED`, and after Publish the update is `READ-ONLY`, so the refusal names no next step. Under the well sits a second history, `DELIVERY`, with a `To` field and `Mark delivered`. |
| An Automation result | Search ▸ the automation ▸ the item ▸ **Open artifact** ▸ a third window with a Send well (`16-*`) | 4 | The automation window has no Send. The result was good (a real team update that named Mira, Theo and Jun). Sent by email: `✓ ACCEPTED BY RESEND`. But the email subject was `Draft: Draft my Friday team update from the Payments platform sync and the 1:1 with Theo: what shipped, …` (the item's instruction), and the body began with the model's own `**Subject: Payments platform — Friday update**` line in raw Markdown (`17-artifact-email-preview-*.png`). |
| The Brief | Not walked here; the Brief window carries the same well (`../daily/shots/m12-brief-window-*.png`). | – | – |

## 6. An agent prepares, I press Send

I issued an agent credential in the rig and called the hub's tools as that
agent (the way Claude Code or Codex would):

- `channel.prepare` for the note to the HoldSpeak folder, and for the
  meeting's follow-up to Slack: both answered `prepared`, with a receipt
  that names the agent.
- `channel.send` as the agent: refused, `owner_principal_required`. The rule
  holds: an agent prepares, only he sends.
- **Where did the prepared sends show?** Not on the desk, not on the bell
  (still 10), not in Needs you, which listed only the meeting's ten proposals
  (`09-desk-after-agent-prepared-*.png`, `09-needs-you-no-prepared-*.png`).
  Two of those proposals were `Send the team update` and `Send status to the
  VP`, each with `Confirm · More` and no way to send.
- I found the note's prepared send only by opening that note's Thought window
  and its Send well: `◆ PREPARED · BY CLAUDE-CODE-WALK · NOTE`, with its
  preview, **Send** and **Discard** (`12-note-send-prepared-*.png`,
  `12-note-prepared-open-*.png`). On the first open the row took between 3
  and 6 s to appear. One press: `✓ SAVED`, and the file was there
  (`12-note-prepared-sent-1440.png`).
- The Slack send prepared for the meeting would show only inside that
  meeting's well, on the Follow-up form.

## Friction log

"Presses" counts presses and typed fields. "Wait" is measured machine time.
"Est." is my estimate for a first-time user who reads the screen.

| # | Job step | Presses | Wait / est. | What he expects | Where he stops |
|---|---|---|---|---|---|
| 1 | Find Send on a meeting | 1 (footer Send) | 3 s / 10 s | Send sends, or asks where | It unfolds a section; the real Send is under the preview, below the fold |
| 2 | Choose what to send | 1 (`↻ SUMMARY`) | – / 30 s | "Summary with decisions and owners" | Three forms, no words for what each holds; Summary has no decisions, Digest has unconfirmed items |
| 3 | First send to a folder | 3 + scroll | 2 s + 3 s / 20 s | Done, with a link to the file | Works. Path cut at the bottom; file date is UTC tomorrow |
| 4 | Add a folder | 3 + 2 fields | 2.6 s / 60 s | Add it here, in the well | A second window (Settings) opens over the meeting |
| 5 | Add GitHub | 4 + 3 fields | – / stuck | Use the `gh` I already signed in to | `UNREACHABLE · Set up account`; Save disabled; two sign-in checks disagree |
| 6 | Send to GitHub, Jira, email, Slack | 3 each | 4 s each / 15 s | Proof it arrived | Works, with proof. Jira and email previews show raw Markdown; GitHub keeps `UNREACHABLE` next to `POSTED` |
| 7 | Know it arrived, later | – | – / stuck | A record in one place | Proof lives only in each document's own well |
| 8 | A send failed | 0 | – / 20 s | Why, and Try again | Reason is clear; the verb says `Send again` |
| 9 | A send hangs | 0 | – / stuck | It ends, or tells me what to do | `SENDING` forever, Send disabled, after reload too |
| 10 | Send a note | 3 | 4 s / 45 s | Send on the note | The note has no Send; it is behind "Develop this thought" |
| 11 | Send the Friday update | 4 + 51 s | – / stuck | Send it | `NOTHING VERIFIED`; published is read-only; no next step |
| 12 | Send an Automation result | 4 | – / 60 s | Send on the result | Third window; subject is the instruction; raw Markdown |
| 13 | Find what an agent prepared for me | – | – / stuck | It waits in Needs you | Nowhere, unless he opens that exact document's well |
| 14 | Send what an agent prepared | 1 | 1 s | One press | Works, once found |
| 15 | Object ▸ Send to ▸ a destination | 3 | 3 s | That destination open | Opened the last-used one instead |

## What worked

- The core is sound. Every channel ran its real code to the edge: frozen
  preview, digest check, one press, a named result, and proof (a file path, a
  comment link, a work-item key, a message id).
- Failures are honest and specific: `ISSUE NOT FOUND · NOTHING SENT`;
  `RESULT UNKNOWN · NO CLEAR ANSWER` for an HTTP 500 that may have posted.
- State survives a reload, and the history keeps each send with its form.
- The rule "an agent prepares, he sends" is enforced by the kernel and
  recorded with the agent's name.
- The Automation's result was a good team update, worth sending.

## Unknown (not verified)

- A real send to a real GitHub issue, Jira work item, Slack channel or inbox.
  The rig stops at the process and socket edge by design. How a Jira comment
  renders from a Markdown `.txt` body, and whether the `acli` answer matches
  the parser, are unknown.
- What the face shows when `acli` hits its 60 s limit.
- Why **Send to ▸ PAY-12 ticket** opened `#payments-leads`. The well was on
  the Digest form at the time; I believe the pick landed on the Summary form,
  but I did not trace it.
- The `503` in the browser console on each Settings load. I did not find the
  request.
- Whether the Accounts row's `UNREACHABLE` is only the rig (it cannot run a
  real `gh auth status`). The disagreement between the two checks is real
  code either way.[^twocheck]

[^rig]: Isolated hubs started with `scripts/graph_walk.py serve --scheduler
    --cli-runner <script>` from the owner's desk worktree
    (`wt-daily-delight-delivery-20261017`, `217001b2e`), with
    `_isolated_hub_env` (scratch `HOME` from `mktemp -d`, every isolation
    switch from `CLAUDE.md`). Ports 8861 (the good day, `rig/runner-ok.json`)
    and 8862 (the bad day, `rig/runner-bad.json`). The recording runner
    replaces `channel_cli.CLI_RUNNER`; the recording HTTPS edge replaces
    `channel_email.HTTPS_HANDLER` and the Slack opener, with in-memory key
    stores (`scripts/graph_walk.py:3121-3240`). The recorded calls are in
    `rig/calls-ok.jsonl` and `rig/calls-bad.jsonl`. Seed through the
    product's own routes: `POST /api/meetings/import` (two `.vtt`
    transcripts in `rig/`), `POST /api/notes`, `project.create`, the engine
    through the face (Settings ▸ Engines ▸ Find on LAN ▸ Use it ▸ Default
    engine), summaries on the real LAN engine `qwen3.8-27b` at
    `192.168.1.43:8080`. Destinations: the folder through the face; GitHub,
    Jira, email and Slack through `channel.save_destination` over the hub's
    MCP endpoint as the owner. The agent: `POST /api/settings/remote` (rig
    only) and `POST /api/settings/remote/credentials`, palette `PROJECT`.
    Chromium headless via Playwright, 1440x900 and 393x852 (mobile, touch,
    scale 2), steps in `rig/s*.py`. Both hubs stopped, both scratch HOMEs and
    browser profiles removed afterwards.
[^twocheck]: The Accounts row probes `gh auth status`
    (`holdspeak/services/connections_service.py:302`); the destination save
    and every GitHub send read `gh api user --hostname`
    (`holdspeak/services/channel_cli.py:260-262`). The form gates on the
    first (`web/src/pages/cores/connections/Destinations.tsx:270-276`); the
    row chip shows the first even after the second succeeded
    (`web/src/desk/surface/send/SendWell.tsx:209-221`).
[^jira]: `holdspeak/services/channel_cli.py:107-108` (`_json_id`: "shape
    PROVISIONAL until a real send"); the argv at `:474`.
[^timeout]: `CREATE_TIMEOUT = 60.0` at `holdspeak/services/channel_cli.py:56`.
    The rig's runner holds the call without honoring the timeout.
