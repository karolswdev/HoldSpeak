# Send: recipe

Build order for `DESIGN.md`. One slice = one PR in the fast cycle
(`CLAUDE.md`). File and line references come from `MODEL.md` and `RECON.md`
(2026-10-17, head `217001b2e`); check them against main before you start.

Rules for every slice:

- **Egress stays his press.** `channel.send` and `channel.discard` stay
  owner-only (`holdspeak/channel_operations.py:251-297`). No slice lets an
  agent, an automation or a timer send.
- **No test sends off the machine.** Tests and rigs use the recording
  runner and the recording HTTPS edge (`scripts/graph_walk.py:3121-3240`;
  fixtures like `tests/fixtures/philo10_atlas/gh-posted.json`). Tests never
  touch the owner's HOME, DB or Keychain.
- **Test doubles replay recorded answers**, never typed ones. The rig
  scripts and runner files in `send/rig/` are the starting point; slice S2
  adds recorded REAL answers.
- **The species is the place to change behavior**
  (`web/src/desk/surface/send/SendWell.tsx`); hosts only seat it.
- Faces obey `docs/internal/UX-CANON.md`: the library Button, no modals,
  the host chip on the line that leaves the machine, no counters of zero.
- Nothing is deleted: parked faces go to `_parked/`; `channel_sends` and
  parked destinations keep every row.
- The fixture for every "done when": the recon seed (two meetings, one
  note, one project, six destinations), recorded once in S1 as
  `tests/fixtures/send_week/` through the product's own producers.

Dependencies: S3 shares the Needs-you face with `../daily/RECIPE.md` D2
(take D2 first if it is in flight, and add the "Ready to send" source to its
list). S7 needs Automations A2 and A6 (`../workbench/RECIPE.md`). S2 needs
the owner at his desk for about 15 minutes.

---

## S1. Tell the truth (small repairs, no new face)

- **Goal:** what the Send face says matches what happened.
- **Files:** `web/src/desk/surface/send/SendWell.tsx` (`accountChip`
  `:190-221`; verb words around `:620-626`), `web/src/features/channels/channels.ts`
  (`SEND_WORDS`), `web/src/pages/cores/connections/Destinations.tsx`
  (`:270-276`), `holdspeak/services/channel_service.py` (`_view`/`sends`
  read path, `_recover` `:511`), `holdspeak/services/channel_contract.py`
  (file naming), `web/src/desk/windowSend.tsx` (the pick),
  `web/src/desk/components/window/Dock.tsx` (`:157-172`), tests.
- **Changes:**
  - The account chip on a destination row shows only when the newest of
    (last check, last send) for that account failed on sign-in. A `sent` row
    counts as a good check. `UNREACHABLE` and `NEVER CHECKED` never sit next
    to a newer `POSTED`.
  - The add form saves a GitHub destination when `channel.save_destination`
    accepts it (it already runs `gh api user`). The form shows the login it
    found. It does not gate on the Accounts row's `gh auth status`.
  - A `dispatching` row older than its channel's limit plus 30 s reads as
    `unknown` with reason `no_answer_in_time` (the read path asks the
    channel's `recover`, which exists). The face shows "No answer from
    <channel>. Check <target> before you try again." with **Check** and
    **Try again**.
  - After `failed`, the verb is **Try again** (not "Send again"). After
    `sent`, **Send again** stays.
  - Saved file names use the local date.
  - `Send to ▸ <destination>` opens the well with that destination picked
    on the form the well shows now (today it lands on another form and the
    last-used row stays open; `18-send-to-picked-1440.png`).
  - The Dock's read of every send on each refresh, which nothing draws, is
    removed (its reducer stays parked).
- **Done when:** on the fixture, after a recorded `POSTED`, the GitHub row
  shows no warning at 1440 and 393; a GitHub destination saves from the
  form in the rig; a held Jira send shows "No answer from Jira" 90 s after
  the press, with Check and Try again, and after a reload; Send to ▸ PAY-12
  opens PAY-12's preview; a file sent at 20:29 on 17 Oct is named
  `2026-10-17-…`.
- **Tests:** T1 `tests/unit/test_desk_send.py` (new: account state after a
  recorded send; `dispatching` past the limit reads `unknown`; local-date
  naming); T2 `web/src/desk/surface/send/__tests__/send.app.test.tsx` (new,
  one file for the app: chip rule, Try again, the Send to pick, replaying
  recorded hub answers); existing `SendWell.test.tsx`,
  `closedReceipt.test.tsx`, `tests/unit/test_channel_send_recovery.py`.
- **Not in this slice:** new words for the receipts (S5), Needs you (S3).

## S2. The first real sends (on his desk, his press)

- **Goal:** a real send to each channel has been seen arriving, once.
- **Files:** `holdspeak/services/channel_cli.py` (`_json_id` `:107-123`, the
  Jira body at `:474`), `holdspeak/services/channel_email.py` (only if the
  evidence asks), `tests/fixtures/send_real/` (new, redacted recordings),
  a short record in `docs/internal/betterment/send/REAL-SENDS.md`.
- **Changes:**
  - With the owner, on his desk: he saves five test destinations (a
    scratch GitHub issue, a test Jira item, his own email through his
    provider, a private Slack channel, a local folder) and presses Send on
    one meeting Summary to each. The orchestrator records, with
    `HOLDSPEAK_WIRE_WRITE`-style redaction, the exact `gh`/`acli` answers
    and the HTTPS answers, and one screenshot of each far side.
  - Fix what the evidence shows: the `acli` answer parser, and the Jira
    body format (if Jira shows raw Markdown, send plain text or the format
    `acli` accepts, and make the preview show the same).
  - The recordings become the runner fixtures for every later Send test.
- **Done when:** each of the five far sides shows the text as the preview
  showed it; each receipt's link opens it; `REAL-SENDS.md` lists what
  arrived and what was fixed.
- **Tests:** T1 replays the recorded real answers through the runner
  (`tests/unit/test_channel_send_contract.py` gains the cases).
- **Not in this slice:** any face change. Nothing is sent by a test.

## S3. Ready to send in Needs you (owner decision 1)

- **Goal:** what an agent, an automation or the steward prepared waits in
  Needs you, and one press sends it.
- **Files:** `holdspeak/services/needs_you_aggregate.py` (`COVERAGE_KINDS`
  `:75`, the row builder), `holdspeak/services/needs_you_membership.py`,
  `holdspeak/services/channel_service.py` (a `prepared/failed/unknown` read
  for the aggregate; mark Needs you dirty on `_changed` `:663`),
  `web/src/desk/needs/NeedsDrawer.tsx` (a row kind `send`),
  `holdspeak/channel_operations.py` (`channel.prepare` description),
  tests.
- **Changes:**
  - A new Needs-you source `send`: one row per `prepared` send, and one per
    `failed` or `unknown` send that he has not acted on. The row: what
    (document label and title), the arrow and the destination name, "by
    <who>" in words (`by Claude Code`, `by Friday team update`, `by you`),
    the time.
  - Row verbs: **Send** (owner press, `channel.send` with `send_id`; the
    host chip on the row), **Look** (unfolds the frozen preview in the row,
    the species' `PreviewWell`), **✕** (Discard, asks once). Failed rows:
    **Try again**. Unknown rows: **Check** and **Try again** (replays the
    same command id).
  - The bell and Today's Needs-you top count these rows.
  - `channel.prepare`'s description ends with: "It waits in the owner's
    Needs you until he presses Send."
  - The `desk.needs_you` MCP tool returns the rows with `kind: "send"`.
- **Done when:** on the fixture, an agent's `channel.prepare` (recorded
  real call) makes a row appear in Needs you within one refresh at 1440 and
  393; **Look** shows the preview; **Send** posts through the runner and
  the row leaves; a held send becomes a "No answer" row with Check.
- **Tests:** T1 `tests/unit/test_desk_needs_you.py` (the `send` source;
  rows leave on sent/discarded); T2 `needs-you.app.test.tsx` (the row and
  its verbs, recorded hub answers); T3 sweep.
- **Not in this slice:** Automations preparing (S7). Today's own layout
  (daily D4).

## S4. What goes out (owner decision 3)

- **Goal:** what his team receives is what he would have written.
- **Files:** `holdspeak/services/document_sources.py` (`_MeetingSummarySource`
  `:466-497`, `_MeetingAftercareSource` `:500-521`, `_ArtifactSource`
  `:524-571`), `holdspeak/meeting_aftercare.py` (`:141`, `:222`),
  `holdspeak/slack_export.py` (`document_markdown_for` `:104`),
  `holdspeak/services/channel_email.py` (`:724`, the message body),
  `web/src/meetings/MeetingSendWell.tsx` (`MEETING_FORMS`), tests.
- **Changes:**
  - Meeting Summary: summary, **Decided** (confirmed decisions), **Who owes
    what** (confirmed items, owner and date). Follow-ups: confirmed items by
    person. Unconfirmed proposals are left out. The `Digest` form leaves the
    face; its document kind stays.
  - The forms read **Summary · Follow-ups** as two plain choices, not a
    cycle gadget.
  - An Automation result's title is "<automation name> · <run date>". A
    first line "Subject: …" becomes the title and leaves the body.
  - Email: send a text part and an HTML part, both from the Markdown; the
    preview shows the rendered form.
- **Done when:** on the fixture, the Summary preview of the platform sync
  shows the confirmed freeze decision and Mira's runbook (after Confirm),
  and no unconfirmed item; the Friday automation result's email preview
  reads "Friday team update · 17 Oct" with no `**`.
- **Tests:** T1 `tests/unit/test_channel_document_refs.py` and
  `test_desk_send.py` (the renderers); T2 `send.app.test.tsx` (two forms).
- **Not in this slice:** the sheet layout (S5).

## S5. The Send sheet

- **Goal:** Send… on any result opens one face, and Send is always in view.
- **Files:** `web/src/desk/surface/send/SendWell.tsx` and `send-well.css`
  (order, chips, Sent list), `web/src/desk/surface/contract.md` (the
  species), the hosts: `web/src/meetings/MeetingSendWell.tsx`,
  `web/src/desk/documentSends.tsx`, `web/src/features/channels/SendWell.tsx`
  (fold `DeliveryHistory` into Sent), the note reader (the window that shows
  `Copy · Dictate about this · Develop this thought`), the artifact window,
  `web/src/pages/cores/connections/Destinations.tsx` (export the form for
  inline use), tests.
- **Changes:**
  - Every host's "Send" becomes **Send…** and opens the sheet in place of
    the result's body, with ‹ Back. The note reader and the Automation
    result get **Send…** directly.
  - Sheet order: forms (meetings only), **To** as one row of destination
    chips (last used first), **Ready to send** rows for this result, the
    preview (receiver's view), **Send** with its host chip, **Sent**.
  - **Add destination** unfolds the Settings form inside the sheet; Save
    picks the new destination. Settings ▸ Accounts stays the list.
  - Receipt words from `DESIGN.md` (Posted on #42, Comment on PAY-12,
    Saved: <file>, Accepted by Resend, Not sent: <reason>), with **Open** /
    **Show**.
  - The update's `DELIVERY` and "Mark delivered" fold into Sent as "Sent by
    hand"; the data and route stay.
  - Phone: the footer holds **Send**; chips scroll sideways in one row.
- **Done when:** from an open meeting, a send to #payments-leads is 3
  presses (Send…, the chip, Send) with no scroll at 1440 and 393; the note
  reader sends in 2 presses; the Friday update shows one Sent list.
- **Tests:** T2 `send.app.test.tsx` (order, chips, inline add, Sent); T3
  sweep (fit, 12 px, egress chip present, Button species); T4 one browser
  case for focus return on ‹ Back and keyboard entry (the old
  `tests/e2e/test_send_glass.py` cases are adapted, not added to).
- **Not in this slice:** Edit (S6).

## S6. Edit before Send

- **Goal:** he can fix one line before it goes, without a new editor.
- **Files:** `SendWell.tsx` (`PreviewWell` `:230`), the note create path
  (`POST /api/notes`), the sheet host switch, tests.
- **Changes:** **Edit** on a preview creates a Note with the rendered
  Markdown (title "<title> (to send)"), opens that note's Send sheet with
  the same destination picked, and leaves the original result unchanged.
- **Done when:** Edit, change a line, Send: the far side shows the edited
  line; the meeting's own Summary is unchanged.
- **Tests:** T1 (the note document renders the edit); T2 (Edit opens the
  note sheet with the destination).
- **Not in this slice:** editing in place inside the preview.

## S7. Automations put their result in a destination

- **Goal:** the Friday update waits in Needs you, ready to send, at 15:05.
- **Files:** `holdspeak/services/workbench_runner.py` (after a result is
  stored), `holdspeak/services/channel_service.py` (`prepare`), the
  Automation's *Put it in* field (`../workbench/RECIPE.md` A6), tests.
- **Changes:** when *Put it in* is a saved destination, the run calls
  `channel.prepare(artifact:<id>, <destination>)` as the run's actor. The
  result shows "Ready to send → <destination>" with a link to the Needs-you
  row. The run never sends.
- **Done when:** a scheduled run with *Put it in: Mira, Theo, Jun* makes one
  Needs-you row "Friday team update · 17 Oct → Mira, Theo, Jun · by Friday
  team update"; Send from the row is accepted by the recording edge.
- **Tests:** T1 `tests/unit/test_desk_send.py` (a run prepares once; a
  second run prepares its own result; a run's `channel.send` is refused).
- **Not in this slice:** any change to how a run is made (Automations A2).

## S8. "Not checked yet" warns (owner decision 2)

- **Goal:** a published update he chose to publish can be sent.
- **Files:** `holdspeak/services/channel_contract.py` (`nothing_verified`
  `:411`, the refusal at `:466-470`), `holdspeak/channel_operations.py`
  (remove `nothing_verified` from the send refusals list), the preview
  fields, `web/src/features/channels/channels.ts`, tests.
- **Changes:** the refusal becomes a preview field "Not checked yet: no
  claim in this update was accepted". Send works. The receipt records that
  it went unchecked.
- **Done when:** the recon's published update (all claims UNVERIFIED) shows
  the warning and sends to the folder with one press.
- **Tests:** T1 `tests/unit/test_channel_send_contract.py` (no refusal; the
  field is in the preview; the receipt notes it).
- **Not in this slice:** claim review in the draft (projects cluster).
