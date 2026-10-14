# Operate — deep usability pass, 2026-10-14

**DRAFT — UNCHECKED, awaiting Muad'Dib. HOLD FOR SHIP.**

Base `eb9a3266e` (#1201). The baseline audit was read-only. The bounded repair
below was authorized after the root read the native component canvas.
The owner can create a workbench and add a pending instruction, but returning
to the work is unreliable: the unfinished instruction disappears, the original
list still says there are no workbenches, and setup leads ahead of the work.
Those are the first bounded repairs. Existing components and draft storage
are sufficient; no new agent or workflow framework is needed.

## Evidence and limits

Production bundle, real isolated `MeetingWebServer`, shared glass helpers,
actual palette/menu/buttons, 1440×900 mouse and 393×852 touch emulation.
Every build/browser invocation used `.tmp/deep-usability/locked.py`, hence
the machine test lock, isolated HOME and Node 22. The terminal runner was
replaced with an unavailable fixture; no real tmux, coder, scheduler, keys,
microphone, inference, credentials, external delivery or owner hub was used.

Attempt 1: `.tmp/deep-usability/operate-walk-1.log`, capture source
`operate_walk.py`, observations `operate-observations.json`, screenshots
`operate-shots/`, all under `.tmp/deep-usability/`. The first attempt finished
both widths with no recorded browser page errors. Screenshots cited below
were visually inspected. This is a usability walk, not a green test suite.

Workbench creation and Add were actual UI actions through production routes.
The repository was a new local scratch git directory with two untracked
Markdown files, registered through the production API for fixture setup.
Its navigation was actual UI; registration was not proved as a UI action.
Roadmap read the checked-in project through the production reader. Delivery
opened through its actual palette launcher; its incompatible scratch source
is an input state, not a product failure. No execution or terminal action was
attempted. Populated workbench run/memory states and a successful dossier
producer are outside this observation.

Two bounded capture attempts only. Attempt 1's optional Memory step used a
locator tied to the Items inlet, which unmounts on another wing; the phone
folded-wing locator also named the control too narrowly. Its Schedule step
opened Today instead of Capture. These are harness gaps, not product defects.
Attempt 2 corrects only those openers and captures the return state; results
are appended below when available. No further setup retries are authorized.

## Ranked findings

### 1. Closing a workbench discards the instruction being composed

**Cost:** Lost draft and context. Workbenches → Create → Blank → collapse
configuration → type “Review release ownership with the team” → close/back →
search and open the same New Workbench. The instruction is empty. At 393 the
owner sees an item well again and cannot tell that text was discarded.

**Proof:** `.tmp/deep-usability/operate-shots/1440-workbench-item-draft.png`
and `1440-workbench-draft-return.png`; the same `393-` pair. The observations
record the input value before/after. This starts from a real UI-created object,
not a seeded final pose.

**Cause:** `web/src/desk/components/WorkbenchWindow.tsx:1049` holds title,
body, priority and grounding in component state. Closing unmounts the window;
reopening initializes an empty title. Nearby Schedule already consumes the
existing desk draft hook (`ScheduleCreateWindow.tsx:74`).

**Fails:** Tenets 2, 3, 7; Constitution VII.3; UX-CANON A.5.
**Smallest repair:** Keep the inlet composition under the existing per-object
desk draft key. Preserve the instruction and its selected priority/references;
clear only after Add succeeds. Failed Add and close/back/reload must retain
the same composition. Do not auto-add or auto-run it.
**Confidence:** Observed at both widths.

### 2. The list contradicts successful creation

**Cost:** Hidden created work. The owner creates Blank and adds an instruction,
but the original Workbenches app still says “No workbenches yet.” The palette
can find the object, which is how this walk reopened it; the original app does
not show its own successful creation or pending item without remounting.

**Proof:** `.tmp/deep-usability/operate-shots/1440-workbench-item-added.png`
and the observations for `workbench-item-added` at both widths show the real
pending row and the retained empty list. Direct list-return shots from attempt
2 are recorded below if reached.

**Cause:** `web/src/pages/cores/WorkbenchesHomeCore.tsx:81` loads only on
mount. The local `workbenches` projection never follows the object's Create,
Add, rename or return. The chooser does refresh the Desk store
(`WorkbenchTemplatePicker.tsx:45`), but that is not this component's local list.

**Fails:** Tenets 2, 3, 7; Constitution VI.1; UX-CANON A.10.
**Smallest repair:** Refresh the existing list projection on the existing Desk
change/return signal and after creation. Keep the object and list in one useful
return path; the owner must see its real name and pending count on return.
**Confidence:** Observed underlying list at 1440 and in browser text at 393;
no claim that reload fails.

### 3. An unbound workbench leads with configuration instead of the work

**Cost:** Composition and hidden next action. A newly created Blank opens
with a half-window scrolling configuration panel. Only Collapse, Search agents
and the first three agent names are visible; Runs on, reference resolution,
start conditions and skills sit deeper in that separate scrolling region.
Below it is a large “No items yet” area plus Add an item, while the actual
instruction inlet and Add sit at the bottom. At 393 the Run control occupies
most of the head despite being disabled (“Bind an agent first”).

**Proof:** `.tmp/deep-usability/operate-shots/1440-workbench-created-empty.png`
and `393-workbench-created-empty.png`; reopening repeats the composition
in `*-workbench-draft-return.png`. Compare the collapsed `*-item-draft.png`
pose, where the actual composer is immediately understandable.

**Cause:** `WorkbenchWindow.tsx:1193` auto-expands configuration when no
recipe is bound; `:1689` places it before Items. `workbench-config.css:57`
gives it a separate scroll region capped at 50%. `WorkbenchWindow.tsx:1726`
adds an empty-state action that only focuses the second Add door. The disabled
Run explanation is also in the window head (`:1634`).

**Fails:** Tenets 2, 3, 5, 6, 7; UX-CANON A.5 and D.
**Smallest repair:** Lead with work, items and the existing instruction well.
Keep the existing configuration strip closed until requested; expose a small
bound/unbound fact with Choose agent. Reuse the current configuration fold and
library controls. Use one clear Add door and one named action for the missing
agent/engine; do not build another setup screen or agent framework.
**Confidence:** Observed at both widths.

### 4. Schedule recovery preserves the title but changes the planned operation

**Cost:** Draft/context loss, potentially wrong recurrence. Source inspection
shows that title/time survive close/reload, but the mode, recurring cron and
duration reset to Once, weekdays at 9, and 60 minutes respectively. A returning
owner can see the same title attached to a different plan.

**Source proof:** `web/src/desk/components/ScheduleCreateWindow.tsx:74`
persists title, `:76` time; `:75`, `:87`, `:88` hold mode, cron and duration
only in component state. `:96` chooses the submitted operation from that mode.

**Fails:** Tenets 2, 3, 7; Constitution VI.1 and VII.3.
**Smallest repair:** Extend the same new-schedule draft to its mode, cron and
duration, and clear all parts only after successful save. Keep the existing
Once/Recurring form. No new scheduler is needed.
**Proof from attempt 2:** At 393, actual Capture → Schedule → enter the title,
Recurring, `30 14 * * 2`, 90 minutes → Back → Schedule restores the title but
changes to Once/60 minutes. Shots:
`.tmp/deep-usability/operate-followup-shots/393-schedule-recurring-draft.png`
and `393-schedule-draft-return.png`; the observation records each value.
**Confidence:** Observed at 393 and source-confirmed; the desktop Capture menu
opener remains a harness gap. No scheduled recording was created.

### 5. Roadmap presents historical rails as the current next action

**Cost:** Ambiguous current work. The real HoldSpeak roadmap opens on
“PH 202 The Coherent Face” with “WHAT'S NEXT · HS-202-06”, several historical
phases marked ACTIVE, and six issues. The repository's current status explicitly
says this old roadmap is history. The face offers no qualifier; a tired owner
cannot distinguish this saved plan from current work. Health also truncates
every source path while five rows repeat “final-summary.md is missing”, so the
owner cannot identify their affected phases from the visible phone rows.

**Proof:** `.tmp/deep-usability/operate-shots/{1440,393}-roadmap-timeline.png`,
`*-roadmap-stories.png` and `*-roadmap-health.png`; actual producer/read and
all three wing actions. `pm/STATUS.md:4` declares the old roadmap history.
`holdspeak/web/routes/roadmaps.py:179` reads it and invokes historical `dw`
check/next at `:191`/`:194`. `RoadmapWindow.tsx:106`/`:118` call that result
WHAT'S NEXT; `RoadmapWindow.css:38` hides Health path overflow without a
reader/opener in the row.

**Fails:** Tenets 3, 4, 7; Constitution VI.1; UX-CANON A.10.
**Smallest repair:** Mark this existing face as the saved roadmap and its
next item as recorded history, or park the obsolete next-work claim. Preserve
the read-only historical material. Let the existing Health row show the full
affected phase/path on request. Do not rebuild delivery or invent a new plan
authority during this repair.
**Confidence:** Observed at both widths; no claim that the historical reader
misparsed its own files.

### 6. Delivery recovery verbs promise different actions from their handler

**Cost:** False next action. The phone's actual Delivery board shows the scratch
repository INCOMPATIBLE and “Update source.” Source inspection shows that this
button only re-reads the snapshot, just as “Reconnect node” and “Reauthorize
source” would. It does not update or reconnect anything. A separate source-only
gap is worse: the dossier's Reload dossier/Retry source/Retry verbs all close
the window.

**Proof:** `.tmp/deep-usability/operate-shots/393-delivery-open.png` shows
Update source on the actual incompatible input. `DeliveryBoard.tsx:93` always
calls refresh; `web/src/desk/delivery.ts:326` maps distinct recovery labels.
`DeliveryDossierWindow.tsx:35` defines the dossier labels and `:53` binds every
one to close. Dossier refusal was not reached by this walk and remains source
evidence only.

**Fails:** Tenets 3, 4, 7; UX-CANON A.10–11.
**Smallest repair:** Name a read Refresh/Retry and show the actual source reason.
Only offer Update/Reconnect where the existing handler performs it. Retain the
dossier subject and re-read that same subject for Retry; Close should say Close.
**Confidence:** Board mismatch supported by shot + handler; dossier is source-only.

## Inner-state coverage

| Surface / state | 1440 | 393 | Proof limit |
|---|---|---|---|
| Workbenches empty → Create → chooser → Blank | Observed UI | Observed UI | Exactly one actual UI-created object per width; no template run |
| Workbench unbound configuration, empty Items | Observed | Observed | Configuration not executed; only collapsed |
| Typed instruction → close/back → reopen | Observed loss | Observed loss | Same created object reopened through real palette |
| Add → pending item | Observed UI | Observed UI | Real durable add; execution withheld |
| Runs empty | Observed, both attempts | Folded-menu locator gap | Bound/working/failed/completed runs unobserved |
| Memory empty | Observed in attempt 2 | Folded-menu locator gap | Real desktop wing action, no memory producer |
| Schedule Once/Recurring/recovery | Capture submenu locator gap | Observed loss in attempt 2 | No create/fire or countdown |
| Roadmap Timeline/Stories/Health | Observed | Observed | Real checked-in historical producer; no writes |
| Repo root → directory → file selection | Observed UI | Observed UI | Fixture registered via API; Stage/Commit/branch untouched |
| Repo PRs / Issues unavailable | Observed | Observed | No PR provider/receipt refresh, no external query |
| Delivery launcher / no-live-source | Observed | Observed | Actual launcher and source projection; no launch |
| Delivery incompatible source recovery pose | Not on first capture | Observed | Missing delivery metadata is the fixture, not the finding |
| Dossier success/refusal, bound terminal | Unobserved | Unobserved | No eligible actual producer/target in bounded setup |

Repository file selection is intentionally reported as read-only coverage,
not automatically a missing-editor defect. The known window offers Stage
and Commit; this pass did not authorize git mutations. The footer keeps these
controls on PRs/Issues too, which is a lower-cost composition issue, below
the actual draft/return failures above.

**Tuesday:** Workbench creation and Add work; closing and returning does not
yet preserve a reliable work loop. Historical Roadmap and unavailable Delivery
need honest names before they can guide current work.

## Bounded follow-up

Attempt 2 finished both widths with no recorded browser page errors:
`.tmp/deep-usability/operate-walk-2.log`, `operate-followup-observations.json`,
and `operate-followup-shots/`. The desktop's actual Runs and Memory wings were
captured and inspected. After Add → close, `1440-workbench-return-list.png`
shows the original app still saying “No workbenches yet.” The schedule's
real recurring-draft loss is confirmed at 393 as described in finding 4.

Remaining exact setup gaps: desktop Window → Desk → Capture submenu locator
did not resolve; the phone's folded Window faces menu opened and visibly
listed Runs/Memory, but the harness's menuitem role locator did not resolve.
Neither is promoted to a product defect. No third capture attempt.

Read-only DB snapshots in `.tmp/deep-usability/operate-durable-rows.json`
confirm both actual UI Adds: `wbi_c3274033b7a8` in
`operate-1440-_g13o27y/holdspeak.db` and `wbi_a6499b39a5b5` in
`operate-393-bk5v3cgc/holdspeak.db`, each with the typed title/body and
`status=pending`. These are isolated scratch databases, not the owner's desk.

## Bounded repair and verification

The root read the production-component canvas at
`docs/internal/philo/phase-17/canvas/deep-operate/` and authorized the exact
Workbench/Home/Schedule build. The canvas's eight poses are synthetic design
evidence, not runtime proof. Source anchors in the audit findings above name
the baseline and have shifted in the touched files.

Changed product files:

- `web/src/desk/components/WorkbenchWindow.tsx`: work and the item composer
  lead; the existing configuration owns the body only when requested. A small
  true agent fact and Choose agent/Configure stay available; the duplicate
  empty Add door is removed. The disabled Run stays compact while its name and
  the visible missing-agent/engine actions retain the reason. Touched verbs
  use the library Button. The inlet's full instruction, priority and selected
  references use the existing per-Workbench desk draft; an accepted Add clears
  only its unchanged submitted snapshot. New text entered in flight remains.
- `web/src/desk/components/workbench-config.css`: existing configuration and
  item/composer composition follows the work lead, with wrapping item titles
  and a wider instruction field in a narrow window. The Workbench's existing
  reference picker is anchored below this composer.
- `web/src/pages/cores/WorkbenchesHomeCore.tsx`: follows the existing
  `useOnDeskChanged` signal with quiet authoritative reads; the known rows
  remain on read failure with the existing retry treatment.
- `web/src/desk/components/ScheduleCreateWindow.tsx`: mode, cron and duration
  use the same draft mechanism as title/time and clear after accepted create.
  The title has one existing gadget mic. The form and schedule authority stay
  as before; no engine chooser or scheduler execution was added.

After-capture attempts 1 and 2 stayed bounded. The first exposed reference
selector ambiguities; the second exposed two real seams. These were verified
as defects and fixed under the root's explicit direction, with one targeted
option probe and one targeted failure-case walk rather than another broad
setup round:

1. A controlled aggregate `/api/workbenches` 503 after accepted Add empties
   the Desk's workbench bucket. The old `if (!wb) return null` hid the window
   although its own detail read succeeded. The window now keeps that existing
   authoritative detail and its name. The focused regression removes the
   aggregate bucket and proves the object, composer and accepted Add remain.
   Before: `.tmp/deep-usability/operate-after-r2-shots/1440-workbench-gap.png`.
2. At 393 the actual source-option Button measured `x=11,y=-9,w=371,h=44`.
   Its center `(196.5,13)` belonged to `.desk-screen-name`, even after scrolling.
   A real tap therefore left `Review ownership @Release sources` unchanged and
   selected no reference. This was a product placement defect, not a failed
   Button handler or an unexplained harness gap. Its old upward popup had no
   positioned inlet ancestor. Probe: `operate-option-observations.json` and
   `operate-option-shots/` under `.tmp/deep-usability/`. The scoped existing
   picker now opens below the positioned composer. At 393 its row is 44 px
   high and its center belongs to the actual option Button; the real tap
   selects the source.

### Executed checks

All commands used `.tmp/deep-usability/locked.py`, isolated HOME, Node 22 and
two Vitest workers. No dependency versions or installations changed. “Vitest2”
in the brief means two workers; the repo's installed Vitest is 4.1.9.

The named six-file run passed **44/44**:
`operate-collect.log` and `operate-tests-r2.log`. After the reproduced aggregate
failure regression and the root-authorized automation opener adaptation,
Editing + Automations passed **17/17** in `operate-final-tests-r2.log`, with
the names in `operate-final-collect.log`. This is **50 unique passing tests
across seven files**, not 61 unique tests:

- `workbenchEditing.test.tsx` — 12, including close/reopen source custody,
  refused Add/Retry, submitted-snapshot clearing and aggregate-bucket loss.
- `workbenchAutomations.test.tsx` — 5; existing behavior assertions retained,
  opener label updated to the requested Configure control.
- `workbenchFrames.test.tsx`, `workbenchOperates.test.tsx`,
  `workbenchesHome.test.tsx`, `scheduledRecordingSlice.test.ts`, and new
  `scheduleCreate.test.tsx` — the other 33, including quiet list reread/failure
  and recurring/empty-cron/refused/accepted schedule draft cases.

An intermediate run exposed the old manual-Retry error-clearing expectation
and assertions made during frame entrance. Manual Retry still clears its old
error while it loads; quiet event rereads retain the known rows. Visibility
assertions now wait for the existing animation. Those failures are preserved
in the earlier logs. Shared typecheck initially named invalid test query
options, which were corrected in this lane; final integrated typecheck belongs
to root. No whole-suite claim is made.

### Actual repaired work loop

The targeted reproduced-failure case finished **GAPS: [] at both widths**:
`.tmp/deep-usability/operate-failure-case.log`. Its sixteen screenshots in
`operate-failure-case-shots/` were all visually inspected; observations and
read-only DB rows are in `operate-failure-case-observations.json` and
`operate-failure-case-durable.json`.

At each width: actual Workbenches → Create → Blank → type the full instruction
and select Release sources through the real option Button → P1 → close → open
the new card → reload retains all three fields without submitting. Controlled
HTTP 503 for Add retains the draft and its source with Retry. Retry continues
through the real service and creates exactly one pending row. Its submitted
draft clears; its full body, priority and source are durable. A concurrent
controlled aggregate 503 leaves that accepted object open and readable.
Return to Home retains the last known card and names the failed read; the
actual Try again updates that card to `1 PENDING`.

The 503s are controlled browser-boundary refusals, not claims of a real backend
policy refusal. Retry's accepted writes are real. The two durable rows are:

| Width | Item | Workbench | Durable facts |
|---|---|---|---|
| 1440 | `wbi_c336e28a04b8` | `workbench_d37c8e5a4da1` | Full instruction body, P1, pending, `zone:dir_72109cfe9444` |
| 393 | `wbi_8470d4cf6ba0` | `workbench_bdd5c8d8acf7` | Full instruction body, P1, pending, `zone:dir_48fde03efdfd` |

The phone option's final center `(196.5,366.89)` is inside its own library
Button (`x=25,y=344.89,w=343,h=44`), and the same real tap selects it. At 1440
its center also belongs to that Button. These are measured hit owners plus
actual pointer actions, not rectangle-only proof.

Schedule's actual Capture → Schedule → recurring draft → Back → Schedule →
reload retained title, Recurring, `30 14 * * 2` and 90 minutes at both widths.
Inspected `*-schedule-return.png` and `*-schedule-reload.png` in
`.tmp/deep-usability/operate-after-shots/` and `operate-after-r2-shots/` carry
that proof. No schedule was created, armed or fired in a browser walk.

### Remaining limits

No live agent/model run, schedule fire, terminal transport or external
delivery was exercised. Populated Runs/Memory and dossier success/refusal
remain unobserved. Repo/Roadmap and Delivery findings 5–6 remain audit findings;
their source files were not changed. The aggregate read's global receipt has
its own Retry; a successful Home-local Retry is not proof that every Desk
collection has recovered.

The existing item-body autosave (distinct from the new-item instruction/body)
still uses component `bodyDraft` plus a pause timer around
`WorkbenchWindow.tsx:690`; unmount cancels that timer. A rapid Close before
that save or a refused body-save followed by reopen was not observed in this
lane. No broad body-editor custody claim is made. The implementation does
preserve the complete new-item instruction as the durable item body.

**HOLD FOR SHIP.** Product source frozen after the targeted fixes and checks.
No staging or commit. Root owns integrated validation and ship.

## Review correction — pending Schedule acknowledgement

The independent implementation review's P1 finding in `review.md` was valid:
an accepted schedule A could unconditionally clear and close newer draft B,
including B in a form reopened while A remained pending. This correction
touches only `ScheduleCreateWindow.tsx`, `scheduleCreate.test.tsx` and this
record. No new browser, dependency or broad-suite work was run.

`ScheduleCreateWindow.tsx:118` captures the submitted draft and the existing
chooser object's identity. After successful creation, `:132` reads the latest
Desk state. All five schedule fields must still match the submitted snapshot;
a currently open chooser must also be the submitting chooser. Otherwise the
completion retains the entire newer draft and keeps its current form open.
An unchanged submitted draft can still be acknowledged after its form was
closed, without closing another form. This uses the existing draft store and
window identity, with no global acknowledgement framework.

The focused deferred-promise regressions prove:

- Editing A's title, mode, time and duration into B while A waits keeps B
  intact and open when A succeeds. Only A was submitted.
- Close → reopen → edit title/cron/duration into B while A waits preserves
  B's current form and all its stored fields after A succeeds.
- Even a reopened form with unchanged values is a new interaction; the
  previous form's completion cannot clear or close it.

The named collection is
`.tmp/deep-usability/operate-schedule-review-collect.log`. The isolated,
machine-locked two-worker Vitest run passed **1 file / 6 tests** in
`operate-schedule-review-tests.log`; its tail was read. The original three
schedule cases still pass. These three added regressions bring this lane's
combined focused evidence to **53 unique tests across the same seven files**.
`git diff --check` is clean for the two touched source/test files.

This is executed component-level pending/remount proof. Earlier live
close/reopen/reload shots do not claim to reproduce this concurrency case.
Source frozen; **HOLD FOR SHIP**. The root's one bounded review recheck and
integrated validation remain next.
