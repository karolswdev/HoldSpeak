# Send: betterment design

Status: draft for the owner. Inputs: `RECON.md` (the live walk, 78 shots,
2026-10-17) and `MODEL.md` (the code map). Product model: `../PLAN.md` §2
("Anything leaving the machine → **Send** → the Send well; he presses Send").
Siblings that hand results to Send: `../workbench/DESIGN.md` (Automations,
"Put it in"), `../agents/DESIGN.md` and `../mcp/DESIGN.md` ("Prepared"),
`../projects/DESIGN.md` (the Friday update, Nudge), `../daily/DESIGN.md`
(Today, Needs you, Nudge), `../asking/DESIGN.md` (Send… on an answer).

## 1. The job

He has a result: a meeting's decisions and owners, the Friday update, a
decision, a note for the VP, or what an automation or an agent wrote for
him. He wants it **in the place his team reads it**: the GitHub issue, the
Jira ticket, the team's Slack channel, an email to Mira, Theo and Jun, or a
shared folder. He opens Send, sees exactly what will arrive and where,
presses **Send** once, and closes it when he has **proof that it arrived**.
More and more, the result is not his: an automation or an agent prepared it
while he was in a meeting. Then the job is shorter: see what waits to go
out, read it, press Send. The rule does not change: anyone may prepare a
send; only he presses Send.

## 2. What it is today

The full walk is in `RECON.md`. In short: **the engine under Send is sound
and the doors to it are not.** Every channel ran its real code to the
process or socket edge in the rig, with a frozen preview, one press, honest
failures and proof. But he meets Send only inside each document, under
different doors, and nothing anywhere tells him what waits to be sent or
what went out.

| Step | What happens | Shot |
|---|---|---|
| Find Send on a meeting | The footer "Send" does not send. It unfolds a section; the real Send is under the preview, below the fold. | `02-meeting-send-well-1440.png` |
| Choose what to send | `↻ SUMMARY` with Summary · Digest · Follow-up, no words for what each holds. Summary has no decisions or owners; Digest and Follow-up list items he never confirmed. | `07-folder-preview-1440.png`, `08-github-preview-1440.png` |
| Add a place | "Add destination" opens the Settings window over the meeting. GitHub cannot be saved when the Accounts row says Unreachable, though `gh` works. | `03-add-destination-settings-1440.png`, `05-new-dest-github-1440.png` |
| Send to each channel | Folder, GitHub, Jira, email and Slack each sent with one press, about 4 s, with proof. Jira and email carry raw Markdown. | `08-*-sent-1440.png` |
| Trust the row | `⚠ UNREACHABLE` next to `✓ POSTED 20:31` on one row. | `08-github-sent-1440.png` |
| A bad day | `FAILED · ISSUE NOT FOUND` is clear, but the verb says "Send again". A send with no answer says `SENDING` forever, even after a reload. | `19-*`, `20-*` |
| Send a note | The note has no Send. It is behind "Develop this thought", in another window. | `10-note-open-1440.png`, `12-thought-window-1440.png` |
| Send the Friday update | `REFUSED · NOTHING VERIFIED · NOTHING SENT`, and the published update is read-only: no next step. | `15-update-email-refused-1440.png` |
| Send an Automation result | Three windows deep. The email subject is the instruction ("Draft: Draft my Friday team update from …"). | `16-*`, `17-artifact-email-preview-1440.png` |
| See what an agent prepared | Nowhere: not on the desk, the bell or Needs you. Only inside that exact document's well. | `09-needs-you-no-prepared-1440.png`, `12-note-send-prepared-1440.png` |
| Know what went out | Only in each document's own `SENDS` list. | `08-history-1440.png` |

What worked: the frozen preview, one press, the named results
(`SAVED <path>`, `POSTED #42`, `COMMENTED PAY-12`, `ACCEPTED BY RESEND · ID`),
`RESULT UNKNOWN · NO CLEAR ANSWER` for a 500 that may have posted, reload
survival, and the kernel's refusal of an agent's Send
(`owner_principal_required`).

## 3. Why it fails

1. **Prepared work has no inbox.** The product's model is "agents and
   automations prepare, he presses Send" (PLAN §2, `../mcp/DESIGN.md`). But a
   prepared send is stored only on its document, and no list he reads (Needs
   you, Today, the bell) has a source for it (`MODEL.md` §4). So the
   agentic half of Send is invisible, and Automations cannot prepare at all
   (`MODEL.md` §3). Shots `09-*`, `12-note-send-prepared-1440.png`.
2. **Send is a section of each document, not one verb with one face.** Six
   hosts seat the same well in different places and under different doors
   (footer Send, More ▸ Send, Develop this thought ▸ Send, Open artifact ▸
   well, Room ▸ Publish ▸ well, Object ▸ Send to ▸). Two buttons are named
   "Send" and only one sends. The well opens below the document, so the
   preview pushes the real Send under the fold. Shots `02-*`, `10-*`, `16-*`.
3. **What goes out is not what he would write.** The document a channel
   carries is the machine's view: Summary without decisions, Digest with
   unconfirmed items, an Automation's instruction as the email subject, raw
   Markdown in email (text only, `channel_email.py:724`) and in Jira. A
   manager cannot send what he would have to apologize for. Shots `07-*`,
   `08-jira-preview-1440.png`, `17-*`.
4. **The face contradicts itself about trust.** `UNREACHABLE` beside
   `POSTED`; a form that refuses a GitHub account the send path accepts; a
   refusal (`NOTHING VERIFIED`) with no verb; `SENDING` with no end. Two
   sign-in checks and two histories (`SENDS`, `DELIVERY`) for one thing.
   Shots `08-github-sent-1440.png`, `05-new-dest-github-1440.png`, `15-*`, `20-*`.
5. **A real send has never been observed.** The rig proves everything up to
   the edge. How a Jira comment from a Markdown `.txt` file looks, and whether
   the `acli` answer matches the parser ("PROVISIONAL until a real send"),
   only his desk can show.

## 4. The design

### The concept

**A send puts one result in one place your team reads.** Anyone can prepare
it: you, an automation, an agent. Only you press Send. It comes back with
proof, and the proof stays with the result.

Three things, and he learns only these:

- a **Destination**: a place his team reads, saved once ("#payments-leads",
  "PAY-12", "Mira, Theo, Jun", "Team reports folder");
- a **Send**: one result going to one destination, shown as it will arrive;
- a **Receipt**: the proof (the link, the key, the file, the message id), or
  the plain reason it did not go.

### The words

| He sees | It replaces |
|---|---|
| **Send…** (the verb on a result: opens the Send sheet) | the footer "Send" that only unfolds, "Develop this thought" as the way to Send, "Open artifact" as the way to Send |
| **Send** (the one egress press, in the sheet or on a Needs-you row) | – |
| **Ready to send** (a prepared send waiting for him) | `◆ PREPARED`, `PREPARED ×K` |
| **by Claude Code**, **by Friday team update**, **by you** | `BY CLAUDE-CODE-WALK`, `BY STEWARD` |
| **Destination**, **Add destination** | (kept) |
| **Sent**, with the proof: **Posted on #42**, **Comment on PAY-12**, **Saved: <file>**, **Accepted by Resend** | `✓ SAVED`, `POSTED`, `COMMENTED`, `DELIVERY`, `Mark delivered` |
| **Not sent: <reason>** + **Try again** | `✗ FAILED · … · NOTHING SENT` + `Send again` |
| **No answer from Jira. Check PAY-12 before you try again.** + **Check** · **Try again** | `RESULT UNKNOWN`, `NO CLEAR ANSWER`, `LAST SEND UNKNOWN` |
| **Waiting for Jira · 40 s** (then the No-answer line at the limit) | `◆ SENDING` with no end |
| **Summary** (summary, what was decided, who owes what) · **Follow-ups** (who owes what, by person) | `Summary · Digest · Follow-up` (`↻ SUMMARY`) |
| **Not checked yet** (a warning on the preview, not a refusal) | `REFUSED · NOTHING VERIFIED · NOTHING SENT` (decision 2) |
| **Sign in to GitHub** (only when the last send or check failed on sign-in) | `⚠ UNREACHABLE`, `○ NEVER CHECKED` beside a good send |
| **Discard** | (kept) |

Chip words follow ASD-STE100 and UX-CANON (12 px, no counters of zero).
The host chip (`GITHUB.COM`, `HOOKS.SLACK.COM`) stays on the line that
leaves the machine and nowhere else.

### The Send sheet (one face, every result)

**Send…** on any result opens the same sheet **in place of the result's
body** in its own window (UX-CANON: own the body, no modal; Back returns to
the result). This is the existing well species, re-seated at the top and
re-ordered. Every host uses it: meeting, note, decision, update, brief,
Automation result, Ask answer, agent result.

Desktop (in the result's window, at least 720×560):

```
┌ Payments platform sync ─────────────────────── OUTCOMES  ARTIFACTS ┐
│ ‹ Back to the meeting                                     Send       │
│                                                                      │
│ SEND   [ Summary ] [ Follow-ups ]                                    │
│                                                                      │
│ TO   (● #payments-leads) ( PAY-12 ) ( Mira, Theo, Jun ) ( Team       │
│       reports ) ( acme/payments #42 ) ( + Add destination )          │
│                                                                      │
│ ┌ PREVIEW · as #payments-leads will see it ──────────────────────┐   │
│ │ Payments platform sync · 16 Oct                                │   │
│ │ Ledger cutover: dual-write live in staging; target stays 28th. │   │
│ │ Decided                                                        │   │
│ │  • Freeze schema changes on the ledger tables until cutover    │   │
│ │ Who owes what                                                  │   │
│ │  • Mira: rollback runbook, Tue  • Theo: profile recon job, Thu │   │
│ └────────────────────────────────────────────────── [ Edit ] ────┘   │
│                                                                      │
│ [ Send ]  HOOKS.SLACK.COM                                            │
│                                                                      │
│ SENT                                                                 │
│  ✓ Comment on PAY-12 · Summary · 20:31                        Open › │
│  ✓ Posted on acme/payments #42 · Follow-ups · 20:31           Open › │
│  ✓ Saved: Reports/2026-10-17-payments-platform-sync.md · 20:29  Show │
└──────────────────────────────────────────────────────────────────────┘
```

- **Order:** what (only when the result has forms), to whom, the preview,
  the one **Send**, then what was sent. The Send press is always on screen
  without a scroll at 1440; the preview scrolls inside its well.
- **To** is one row of destination chips, the last one used for this kind
  of result first and picked. A pick replaces the preview at once. There is
  no list of six three-line rows.
- **Add destination** unfolds the same form that Settings ▸ Accounts uses,
  **inside the sheet**, under the chips. Save picks the new destination.
  Settings stays the one home that lists and edits them all.
- **The preview is what the receiver sees**: Slack text as Slack draws it,
  an email with its subject line on top, a Jira comment in the format Jira
  draws (decided after the first real send, slice S2), a file with its name.
  Never raw `#` and `**`.
- **Edit** makes a copy of the words as a Note (a `note:` document, which
  Send already carries) and opens the sheet on that note. The original
  result stays unchanged. That gives him a way to fix one line before it
  goes, with no new editor.
- **Send** is the one egress press. Its host chip sits beside it.
- **Sent** lists this result's receipts, newest first, with **Open**
  (the comment, the work item, the Slack message link when the channel gives
  one) or **Show** (the file in Finder). The update's separate `DELIVERY`
  history and its manual "Mark delivered" fold into this list as **Sent by
  hand**. It is the same fact, so it gets the same list.

Phone (393): the sheet owns the window; the same order in one column.

```
┌───────────────────────────────┐
│ ‹ Back        Send             │
│ [ Summary ] [ Follow-ups ]     │
│ TO                             │
│ (● #payments-leads) (PAY-12) › │  ← chips scroll sideways
│ ┌ PREVIEW ───────────────────┐ │
│ │ Payments platform sync     │ │
│ │ Decided …                  │ │
│ │ Who owes what …            │ │
│ └──────────────────[ Edit ]──┘ │
│                                │
│ SENT                           │
│ ✓ Comment on PAY-12 · 20:31  › │
├────────────────────────────────┤
│ [ Send ]       HOOKS.SLACK.COM │  ← the footer holds Send
└────────────────────────────────┘
```

On the phone the footer holds the one **Send** (44 px target), so it is
never under the fold.

### Ready to send: prepared work goes to Needs you

Every prepared send is a **Needs you** row, the one list of what waits on
him (PLAN §2). Today shows it with the top of Needs you, so the morning brings
"3 ready to send".

```
NEEDS YOU · Ready to send                                        3
┌───────────────────────────────────────────────────────────────────┐
│ Follow-ups · Payments platform sync  →  #payments-leads           │
│ by Claude Code · 20:32                    [ Send ] [ Look ] [ ✕ ] │
├───────────────────────────────────────────────────────────────────┤
│ Friday team update  →  Mira, Theo, Jun                            │
│ by Friday team update (automation) · Fri 15:00  [Send] [Look] [✕] │
├───────────────────────────────────────────────────────────────────┤
│ No answer from Jira · Summary → PAY-12        [ Check ] [ Try again ]│
└───────────────────────────────────────────────────────────────────┘
```

- **Send** sends that frozen send, with its host chip on the row, in one
  press. The row turns into its receipt for a moment and leaves the list.
- **Look** unfolds the preview in the row (the same preview well), with
  **Edit** as above.
- **✕** is Discard (it asks once: "Discard?").
- A send that **failed** or got **no answer** is also a Needs-you row,
  because it needs him: "Not sent: issue 4242 not found · Try again", "No
  answer from Jira · Check · Try again".
- The bell counts these rows like any other Needs-you row.
- The same rows show on the result itself (in its Send sheet, above **To**,
  as "Ready to send"), so opening the meeting also shows them.

### What goes out (the documents)

- **Meeting ▸ Summary**: the summary, **Decided** and **Who owes what**,
  confirmed items only (decision 3). **Meeting ▸ Follow-ups**: who owes
  what, grouped by person, confirmed only. The Digest form leaves the face;
  its document kind stays for agents.
- **Automation result**: its subject or title is the automation's name and
  the run's date ("Friday team update · 17 Oct"); when the result's first
  line is "Subject: …", that line becomes the subject and leaves the body.
- **Note**: its title and words, as today.
- **Draft update**: as today, with "Not checked yet" as a warning (decision 2).
- **File names** use the local date.
- **Email** goes as text and HTML, both from the same Markdown, so neither
  shows `#` or `**`.

### Trust: the account line tells the truth

- A destination row shows an account warning only when the **last thing that
  touched that account failed on sign-in** (a check or a send). A successful
  send is a check: it clears `UNREACHABLE` and `NEVER CHECKED`.
- The add form saves a GitHub destination when `gh api user` names a login,
  the same check the send uses. The Accounts row reads the same result.
- A send that hits the channel's time limit (60 s for `gh`/`acli`) ends as
  **No answer** with **Check** and **Try again**. Nothing stays `SENDING`
  past the limit.

### Who prepares (the rest of the agentic OS)

| Producer | Prepares by | Lands in |
|---|---|---|
| He | Send… on a result; Send in the sheet (inline, as today) | sent at once |
| An Automation | *Put it in: a destination* (`../workbench/DESIGN.md`) | Needs you ▸ Ready to send |
| An agent (Claude Code, Codex, pi) | `channel.prepare` over the desk's tools | Needs you ▸ Ready to send |
| A Thread or Ask | Send… on an answer; or its tool call | Needs you ▸ Ready to send |
| The steward / Nudge | as today | Needs you ▸ Ready to send |

The agent's tool description says what happens next: "Prepared. It waits in
Needs you until the owner presses Send." So an agent can tell him in one line
where to look.

### Every press

| Verb | Where | What one press does |
|---|---|---|
| **Send…** | any result (footer on desktop, More on phone, Object ▸ Send to ▸ a destination) | Opens the Send sheet in that window, with the last-used destination (or the one picked in Send to ▸) chosen and its preview drawn |
| A destination chip | Send sheet | Picks it; the preview redraws for that destination |
| **Add destination** | Send sheet | Unfolds the add form in place; Save adds and picks it |
| **Summary / Follow-ups** | Send sheet, meetings only | Changes what is sent; the preview redraws |
| **Edit** | preview | Copies the words into a new Note and opens its Send sheet with the same destination |
| **Send** | Send sheet, Needs-you row | Sends the frozen preview; shows the receipt in the same place |
| **Look** | Needs-you row | Unfolds the preview in the row |
| **✕ / Discard** | Needs-you row, ready-to-send row | Asks "Discard?"; then discards; nothing is sent |
| **Try again** | failed or no-answer row | Failed: sends again with a new press. No answer: replays the same command, so a send that did arrive is not doubled |
| **Check** | no-answer row | Opens the far side (the issue, the work item, the channel) in the browser |
| **Open / Show** | Sent row | Opens the comment or work item; shows the file in Finder |
| **‹ Back** | Send sheet | Returns to the result, focus on Send… |

No verb is shown that cannot work: no Send… on a meeting without a summary,
no Follow-ups when nobody owes anything, no Check when the channel gives no
link.

### Removed or parked (nothing is deleted)

- The footer "Send" that only unfolds: renamed **Send…**, and it opens the
  sheet at the top of the body.
- "Develop this thought" as the only way to send a note: the note reader gets
  **Send…** itself.
- The `Digest` form on the face (its document kind and MCP stay).
- The update's `DELIVERY` history and `Mark delivered` as a separate section:
  folded into **Sent** ("Sent by hand"). The data stays.
- The Dock's read of every send on each refresh, which nothing draws: parked.
- The legacy actuator proposals' send path (Settings ▸ Meetings ▸ RAW ▸
  Allow actuators) stays behind RAW; it is not a second Send on any face.
- `NOTHING VERIFIED` as a refusal (decision 2).

## 5. Decisions for the owner

1. **Ready-to-send work lives in Needs you.** Every prepared send (by an
   agent, an automation, a thread or the steward), and every send that failed
   or got no answer, is a Needs-you row with Send in place. Recommended: yes.
   It is the "Prepared … he presses Send" model with a place to press.
2. **"Not checked yet" warns; it does not refuse.** Today a published update
   whose claims nobody accepted cannot be sent at all, and nothing says how
   to fix it. His press is the check (Tenet 1; ledger, not gate). The preview
   shows "Not checked yet" over the claims, and Send works. Recommended: yes.
3. **Meetings send confirmed items only, in two forms.** Summary (with what
   was decided and who owes what) and Follow-ups. Items he has not confirmed
   stay off what his team reads. Recommended: yes.

## 6. How we know it worked

On his own desk, with his own accounts, the first time:

- **Real sends, once each.** He sends one meeting Summary to a test GitHub
  issue, a test Jira item, his own email and a private Slack channel, and a
  file to his team folder. Each one arrives looking like the preview, and
  each receipt's **Open** lands on it. Target: each send **3 presses from the
  open meeting, under 15 s**, no raw Markdown on the far side.
- **Agent prepares, he sends.** He asks Claude Code to "prepare the
  follow-ups from today's platform sync for #payments-leads". Within a
  minute Needs you shows **Ready to send · by Claude Code**. **Look**, then
  **Send**: **2 presses**, and the row turns into "Posted".
- **The Friday update.** The *Friday team update* automation runs at 15:00
  with *Put it in: Mira, Theo, Jun*. At 15:05 Needs you shows it. He reads
  it, edits one line through **Edit**, presses **Send**: **under 2 minutes**,
  subject "Friday team update · 17 Oct".
- **A bad day.** A send to a wrong issue says "Not sent: issue not found"
  with **Try again** in Needs you. A send with no answer ends within a
  minute as "No answer from Jira · Check · Try again", never as a spinner.
