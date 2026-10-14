# Work surfaces — existing surface audit, 2026-10-14

**DRAFT — HOLD FOR SHIP. UNCHECKED — awaiting Muad'Dib.**

Base: `6e86c666ae15c23241f427ca98981a83c5978d92`. Read-only product audit in
`/Users/karol/dev/tools/wt-surface-audit-20261014`. No product or test edits,
staging, commits, owner hub, owner DB, Keychain or microphone use.

The largest remaining cost is understanding and finding the work inside the
windows. Today and People have a useful next-meeting focus. Notes now have real
Task and Ask doors. However, Memory hides important identity, Ask still exposes
its old configuration rack, and meeting review can offer a source that was never
recorded. The first repair should be the false transcript link; the largest face
repair should be Memory.

## Evidence and limits

`S/` below means `.tmp/evidence-shots/desk-sweep/`; `W/` means
`.tmp/surface-audit/work/`. All paths are relative to this worktree. General
captures came from root's one existing sweep. This lane visually inspected its
captures and read current source. Two supplemental capture attempts reused
`test_desk_sweep`'s actual fixture, boot and page helpers under
`.tmp/surface-audit/locked.py`. They opened real isolated-hub objects and menus;
they injected no producer responses and ran no model or recording.

The first attempt recovered People Prep and an empty Thread at both widths.
The second recovered Ask at 1440 and the unlinked proposal's More menu at both
widths. Phone Note → Task/Ask remains **blocked by this capture's selector**:
the script sought a button named `More`; the footer's accessible name is
`More actions` (`web/src/desk/surface/SurfaceFooter.tsx:105`). This is not evidence
that the product action fails. The attempt budget was exhausted, so it is
reported honestly. `W/observations.json` and `W/observations-final.json` carry
the text, errors and real outcome-review response. Scratch capture completion
does not establish an operation's success.

## Ranked findings

### 1. Meeting review invents an exact transcript destination for an unlinked proposal

- **Evidence:** `W/outcomes-more-no-span-1440.png` and
  `W/outcomes-more-no-span-393.png` show **Show in transcript** for
  “Freeze the ledger on Nov 12.” The actual `/outcome-review` response in
  `W/observations-final.json`, `proposal-data`, has `segment_index: null`,
  `span_start: null`, `span_end: null` and `support: "unknown"`. The transcript
  visible underneath instead says “We move the cutover to Friday.”
- **Cause:** `web/src/pages/cores/history/MeetingDetail.tsx:335` coerces the
  optional segment with `Number(row.segmentIndex)`. `Number(null)` is `0`, which
  passes the integer and bounds check; `:342` then opens segment 0. The menu
  exposes the false source at `:373`. The same proposed decision is also
  already under **Decided · 1** (`:555`) while its state is proposed (`:124`).
- **Owner cost:** a review aid appears to establish evidence for a claim that
  has no recorded source; the section name also presents an unconfirmed claim
  as settled. An architect can confirm the wrong date with false confidence.
- **Fails:** Tenets 3 and 7; Constitution VI.2; UX-CANON A.10 and A.11.
- **Direct repair:** validate the original nullable value as an integer before
  converting or formatting it. Withhold **Show in transcript** without a real
  recorded segment. Use **Decisions** while proposed rows exist, or separate
  proposed from decided rows within this ledger; show the existing unsupported
  fact as **Not in the transcript** where appropriate.
- **Confidence:** high. Real response and rendered menu observed; the click's
  segment-0 target is established by source, not a clicked navigation.

### 2. Memory cannot identify who owes a commitment or where it came from

- **Evidence:** `S/surface-project-memory-1440.png` shows two separate
  “Write the rollback runbook” rows; only one has a Project token and neither
  has a source opener. `S/surface-project-memory-393.png` shows two commitments
  before the next one falls below the window. The head says `REF · · SEARCHED`
  for the initial recent read; rows say `CMT`, `DUE · UNKNOWN OWNER · UNKNOWN`.
- **Cause:** `web/src/features/project-room/recall/RecallFace.tsx:220` uses a
  custom `CMT` row. `:228` draws the owner only when the owner is **unknown**,
  so a known owner is omitted from this face (source-established state, not
  present in this fixture). `:238` offers only the next mutation, with no
  source opener. The row model at `recall/model.ts:65` carries action identity,
  owner and project but no meeting/note source. `RecallFace.tsx:395` draws
  `REF ·` even for an empty query. `recall.css:211` wraps project and action
  into one sprawling meta area.
- **Owner cost:** duplicate task text cannot be distinguished, and known
  responsibility is hidden on the screen used to recall work. The phone makes
  the owner scroll through large action areas before he can compare results.
- **Fails:** Tenets 2, 3, 4, 5 and 7; UX-CANON B and D's one row grammar.
- **Direct repair:** compose owed results with `SurfaceLedgerRow`: task, plain
  owner and date, a named source opener, then the one next verb. Carry the
  existing source reference from the read model; do not merge duplicate text
  by guess. Use **Action**, **no date**, **no owner**. Omit the empty reference
  token and local-device footer. This is the settled layout below.
- **Confidence:** high on observed ambiguity and layout; high source confidence
  on the known-owner omission, which was not rendered in this fixture.

### 3. Ask still asks the user to understand a configuration rack before asking a question

- **Evidence:** `W/ask-from-note-1440.png`: an empty question, five lens choices,
  `GROUNDING`, `Context`, `GROUND THIS ASK`, `BUDGET 0.0K/16.4K`, and footer
  `USES ASSIGNMENT` while the same window says **No engine**. Note → Ask itself
  successfully opened and carried the note title.
- **Cause:** `web/src/desk/components/AskPanel.tsx:547` mounts all five lenses;
  `:557` replaces the user's entire draft with a fixed instruction when a lens
  is chosen. `:564` mounts the grounding rack and `:609` its budget meter;
  `:322` supplies `USES ASSIGNMENT` independently of engine state. The newer
  engine/run components already exist at `:492` and `:374`.
- **Owner cost:** the question box competes with controls that require product
  lore. Choosing a lens also replaces a drafted question (source-established
  action, not exercised here). The footer claims an assignment where none is
  selected in this fixture.
- **Fails:** Tenets 2, 3, 4 and 7; UX-CANON A.3 and A.5. This is already the
  repair specified by October 13 `DESIGN-verbs.md` §4.4 and
  `DESIGN-words.md` §4.1, but the old elements remain in current source.
- **Direct repair:** keep the question, mic, **Ask**, one engine line and
  `With: Ledger rollback`. Fold the existing pickers under **Add notes**.
  Park the desk lens strip and its draft-replacement handler; omit budget
  until there is an actual over-budget reason. Let the footer carry the run
  receipt or actual draft recovery state.
- **Confidence:** high at 1440 and for source behavior. Ask at 393, actual
  inference, selected-passage handoff and failure/retry remain unobserved.

### 4. The week and saved meeting records expand Send before it is requested

- **Evidence:** `S/week-393.png` spends the screen on two upcoming events and
  one saved meeting's Summary/Send form; the other meetings and notes are below
  it. `S/week-1440.png` opens near the bottom of the desk with this same large
  content. `S/meeting-393.png` permanently shows a Send picker, **Decide**, and
  a footer with **Send**, **More**, **Add to Project**. `S/meeting-1440.png`
  repeats the Send form and its footer verb.
- **Cause:** `web/src/desk/chair/ChairHome.tsx:2725` sets each meeting row open
  whenever its detail read exists, although its click opens the meeting
  (`:2722`). `ArrivalMeetingWells` automatically mounts Send under every
  available summary (`:2542`). `web/src/pages/cores/history/MeetingDetail.tsx:755`
  does the same inside Outcomes, followed by a separate Decide well (`:762`).
  The compact footer intentionally retains opaque components outside More
  (`web/src/desk/surface/SurfaceFooter.tsx:128`), explaining the third control.
- **Owner cost:** a weekly scan becomes a hunt through full meeting forms.
  Reviewing a meeting competes with sending and creating another decision
  before the owner has asked for either operation.
- **Fails:** Tenets 2, 3, 5 and 7; UX-CANON A.5 and the phone footer rule from
  `DESIGN-windows.md` §4.6 P4.
- **Direct repair:** make The week's saved meetings closed ledger rows with
  title, date, one summary excerpt and **Open**. Keep the full summary and
  outcome ledgers in the meeting. Mount its Send well only on **Send**, then
  return focus there; fold **Decide**, export, park and project filing into
  the existing More menu so the phone footer is **Send · More**.
- **Confidence:** high. Populated default layouts observed at both widths;
  no send, file export or decision creation was performed.

### 5. Project History throws away the changed object's name

- **Evidence:** `S/room-1440-History.png` and `S/room-393-History.png` show
  `Item created · risk` twice and `Item created · milestone` twice. None tells
  the owner which risk or milestone changed, and none offers its item.
- **Cause:** `web/src/features/project-room/model.ts:147` formats an
  action-shaped summary from `action` and `item_type` only, ignoring `title`.
  The real producer already records `title` with `item_id` at
  `holdspeak/services/project_service.py:4559`. The producer points the change
  at the project (`:4555`); `ProjectRoomCore.tsx:2458` suppresses an opener for
  that target. Search then filters only this reduced phrase (`:2405`).
- **Owner cost:** “what changed in this project?” cannot identify or find the
  affected work. Searching “Production cutover” misses its create event even
  though the recorded change already contains the name.
- **Fails:** Tenets 3 and 7; UX-CANON A.10.
- **Direct repair:** include the recorded title in the phrase, e.g.
  **Added milestone · Production cutover**; preserve item identity as the
  destination and open the existing Room item at that identity. Search the
  title as well. Reuse the current History stream.
- **Confidence:** high. Both duplicate rows observed and title-loss seam read;
  search miss is established by its filter source, not exercised in the browser.

### 6. Needs you still spends the attention list on kind/state repetitions and four verbs

- **Evidence:** `S/needs-1440.png`: **DECISION**, `PROPOSAL`, `TO DECIDE`, then
  **Add to Project**, **Decline**, **Defer**, **Confirm** on one row. Other
  action rows repeat **ACTION** twice. `S/needs-393.png` reaches only two whole
  rows and the start of the third after the availability, checked, next event,
  calendar offer, filter strip and list caption. `RANKED` appears both as the
  default filter and a second time in the footer.
- **Cause:** `web/src/desk/needs/needsFace.ts:159` returns `PROPOSAL`, `:415`
  adds the redundant state lamp, and `NeedsDrawer.tsx:211` composes all four
  proposal actions. `:465` names the all filter Ranked; `:610` formats the
  duplicated checked time as RANKED. This is not a request to remove coverage
  truth or change the one hub count.
- **Owner cost:** the primary daily list requires decoding status language
  and comparing secondary actions before acting on the work.
- **Fails:** Tenets 2, 3 and 4; UX-CANON A.3; the accepted word/attention
  direction in October 13 `DESIGN-words.md` §4.1 and `DESIGN-attention.md` §4.1.
- **Direct repair:** keep one kind plate only on this mixed list, work title,
  useful owner/date/source, and **Confirm** or **Open**. Move secondary actions
  under the same More species used in Outcomes. Say **All** and keep one
  **Checked hh:mm** receipt. Fold detailed coverage behind its real status.
- **Confidence:** high on default populated layout. Empty, incomplete coverage,
  muted, waiting and writes were not rendered or exercised.

### 7. A fresh Thread's mode strip has no keyboard entry and still uses raw controls

- **Evidence:** `W/thread-empty-1440.png` and `W/thread-empty-393.png` show an
  empty Thread with **Desk · Interview · Chase · Draft · Plan** and more
  material cut at the right edge, no selected mode, and its name repeated
  inside the window. The composer and empty state rendered at both widths.
- **Cause:** `web/src/desk/components/ModeTabs.tsx:121` uses raw buttons.
  `:130` makes a tab focusable only when it is already the active mode; a bare
  thread has `activeMode: null`, so every tab gets `tabIndex=-1` while the
  container at `:110` has no tab stop. The arrow handler cannot be entered
  through ordinary Tab in that state. Thread's title is another raw button
  (`web/src/desk/pullouts/ThreadPullout.tsx:1669`); its own duplicate head
  remains even though the title bar has the name.
- **Owner cost:** the architect cannot reach the mode strip by the advertised
  keyboard path on a fresh thread. An unexplained horizontal bank and a
  second title consume the small window before the first message.
- **Fails:** Tenets 3, 5, 6 and 7; UX-CANON A.1 and A.7.
- **Direct repair:** use the existing library cycle or tab controls for Mode,
  with a focusable default when no mode is bound; expose its current value
  once beside the composer. Keep title editing in the title's existing
  in-place grammar and remove the repeated head. A change here should also
  retire the mode strip's custom raw-button styling.
- **Confidence:** high on raw controls and default layout; high source
  confidence on the all-negative-tabindex state. No keyboard sequence or
  model/tool turn was exercised.

## Face and state coverage

**Rendered** means inspected pixels, not a passed deep workflow. Basenames
below are exact; paired widths are shown explicitly. **Source-only** and
**blocked** states are not counted as observed.

| Face | 1440 / 393 evidence | States actually observed | Other state coverage |
|---|---|---|---|
| Today · Day | `S/today-1440.png`, `S/today-393.png` | Populated calendar, failed-summary row, next prep/arming controls, owed/decision side wells on desktop | Empty, read error, record/arm/confirm results source-only |
| Today · Brief | `S/brief-1440.png`, `S/brief-393.png` | Populated recent activity/weekly overview | Empty, failed read/generate, shelf/refresh/send source-only |
| The week | `S/week-1440.png`, `S/week-393.png` | Populated calendar and expanded saved-meeting summary/Send | Lower notes/due/decision rows and actions source-only |
| Needs you | `S/needs-1440.png`, `S/needs-393.png` | Ranked populated list, complete availability, proposals, missing-owner rows | Empty, incomplete coverage, filters, mutation results source-only |
| Note object | `S/note-1440.png`, `S/note-393.png` | Working populated note, no-engine band, footer | Selection, saved conflict, Finish/Resume, Project/Send source-only |
| Note · Task | `W/note-task-1440.png` / **blocked** | Desktop form opens with task seeded from note, owner/date fields | Phone capture selector blocked; Add result unobserved |
| Tasks · Follow-through | **Source-only** `web/src/desk/pullouts/views/FollowThroughView.tsx` | None | Board, source, Done/Reopen/Snooze/Delegate and error logic read; no rendered claim |
| Decisions · list and object | **Source-only** `DecisionsView.tsx`, `DecisionPullout.tsx` | Today/Needs decision summaries only, not these faces | Search/detail/edit/status changes unobserved |
| Project · Room | `S/room-1440.png`, `S/room-393.png` | Populated plan, late milestone, desktop signals and Ask bar | Item details, sources/steward, draft update/editor/posting source-only |
| Project · History | `S/room-1440-History.png`, `S/room-393-History.png` | Populated stream and filter/search controls | Search/filter result, Writes fold and object open unobserved |
| Memory | `S/surface-project-memory-1440.png`, `S/surface-project-memory-393.png` | Populated recent read, owed rows, filters/search controls | Explicit search, decision/belief detail, source open, owner/date/Done mutation source-only |
| Ask AI | `W/ask-from-note-1440.png` / **blocked** | Empty composer grounded on one note; no engine | Phone selector blocked; selected quote, engine run, success, failure/retry/Keep source-only |
| Thread | `W/thread-empty-1440.png`, `W/thread-empty-393.png` | Real newly created empty thread, mode strip, composer | Populated/streaming/error/crash/tool decision/branch/annotation states source-only |
| Meetings · list | `S/surface-meetings-1440.png`, `S/surface-meetings-393.png` | Five records, one failed, summaries stored | Empty, search, failure retry and open-actions filtering source-only |
| Meetings · Record | `S/surface-meetings-1440-Record.png`, `S/surface-meetings-393-Record.png` | Idle Record/Import choices | Import progress/error and recording source-only |
| Meeting · Outcomes | `S/meeting-1440.png`, `S/meeting-393.png`; `W/outcomes-more-no-span-1440.png`, `W/outcomes-more-no-span-393.png` | Saved summary/action; proposed decision/failed summary; actual More menu | Gap/edit, confirm/bulk/dismiss/defer, completion/reopen and cross-face durable state unobserved |
| Meeting · Artifacts | `S/meeting-1440-Artifacts.png`, `S/meeting-393-Artifacts.png` | Empty artifacts wing | Populated artifacts/export source-only |
| Live meeting | `S/surface-live-1440.png`, `S/surface-live-393.png` | Idle, speech-not-set-up/audio-only readiness | Live capture, transcript, Stop/saved handoff forbidden in this audit and unobserved |
| People · roster | `S/surface-people-1440.png`, `S/surface-people-393.png` | Four people, next prep, owed counts | Add/duplicate/archive and protected failure source-only |
| Person · Prep | `S/person-1440.png`, `W/people-prep-393.png` | Linked upcoming 1:1, Record meeting, one you-owe item, agenda/add forms | Add/Done/record result and meeting-commitment join source-only; `S/person-393.png` was an early blank, recovered by supplemental capture |
| Person · Context/History/Info | **Source-only** `web/src/pages/cores/PeopleCore.tsx:1257` | None | Project/calendar/aliases/notes/history/archive read, not rendered |
| Compatibility faces | **Parked** | None | Separate Chair Brief and meeting Review are parked; no finding reopens them |

Useful existing material: Today makes the next 1:1 obvious; People roster and
Prep provide an actual prep/record handoff; the note's Task well stays in its
window; the meeting's one Outcomes wing replaces the old Review loop. These
are rendered affordances. Completing those jobs against durable state remains
outside this audit's observed action coverage.

## Smallest coherent repair sequence

1. Repair Outcome source/state truth (finding 1), then include the existing
   known owner and source identity in Memory (finding 2).
2. Finish the already specified Ask simplification and stop eager Send forms
   in scan/review faces (findings 3–4).
3. Preserve the object in Project History; reduce Needs rows to one action;
   replace Thread's custom controls with current library species (5–7).

No new app, workflow engine, memory framework or alternate navigation is
needed. The remaining deep operations should be walked when their particular
repair is built; this audit does not call the entire application usable.

## Settled recommendation — Memory, this lane's worst face

Use the current Memory window and current result groups. Put one search row at
the top, then the existing light filter strip, then the result ledger. The
leading fact is the result count only after a real read. For recent reads,
say **Recent work** rather than an empty `REF` header.

Each owed result is one `SurfaceLedgerRow`: **Action** in the lead slot; task
as the primary line; **Jordan · by Friday** as plain metadata; **from Ledger
cutover sync** as the named source opener. Its trailing action is **Name an
owner**, **Set a date**, or **Done**, based on the stored gaps. More holds
secondary operations. At 393 the task wraps, owner/date stays together below,
and source/action follows in that same row. Keep the existing inline owner/date
well directly under the selected row.

Park the `CMT` emblem, empty reference token and local-device footer. Fold the
existing belief evidence, old decisions and history under their individual
rows. Keep source identity visible; keep repeated text as separate objects
until a durable identity proves that they are the same commitment.
