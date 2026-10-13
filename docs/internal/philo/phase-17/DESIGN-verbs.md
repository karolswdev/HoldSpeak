# Phase 17 design: verbs (R1 dead verbs, R6 the engine asked again)

Recon: `RECON-2026-10-13.md`, sections R1 and R6. Cluster: every AI run
(Ask AI, Draft update, the thought's question), its progress and its
failure reasons; the Object menu's dead rows; Terminals; one engine chip.

Sibling designs: `DESIGN-attention.md` (R2, R5), `DESIGN-windows.md` (R4,
the phone), `DESIGN-words.md` (R3, R7, the cut list). Seams are named where
this design touches them.

Code is main @ `b50b13a0b` (2026-10-13). Every claim below cites it.

## 1. The problem

Ask AI, the one question an architect asks, waits 122 s and prints
`NOT ANSWERED · THE HUB REFUSED IT` with no reason, 14 s after the same
engine summarised a meeting (shots 039, 047). Room ▸ Draft update: one
press, 91 s, nothing; the face still says "No updates yet. Draft the first
one." (shot 061). Dock ▸ Terminals: two presses, no window (shot 057). The
thought says `NO ENGINE YET · Choose an engine` while Runs on says
`Answers and thoughts · Qwen3.8 27B · Ready` (shots 016, 018, 043). The
Object menu on a desk icon has 7 of 11 rows greyed with an excuse
(shot 083). The Brief says "not set up: Set up local AI downloads this
model" (shot 001) on a desk whose engine is set.

## 2. The cause in the code

### 2.1 Two engine authorities, one switch nobody flipped (R6, and the Ask refusal)

The desk has two answers to "which engine runs this":

1. **The assignment service** (`holdspeak/services/inference_assignment_service.py`).
   Runs on reads it: `task_overrides[]` with `effective.assignment.entries[0].label`
   (:276-:299, :2513-:2532). This is where `Answers and thoughts · Qwen3.8 27B · Ready`
   comes from. The meeting summary runs through it, which is why it works.
2. **The legacy placement** (`holdspeak/inference_targets.py`): a Config pointer
   (`config.thoughts.inference_target_id`, `resolve_thought_placement` :627-:637)
   that falls to `GLOBAL_DEFAULT_TARGET_ID = THIS_MACHINE_ID` (:45). This
   machine is "ready" only when the starter model file is on disk
   (`_this_machine_readiness` :262-:272); otherwise its reason is
   `NOT_SET_UP_REASON = "not set up: Set up local AI downloads this model"` (:245).

The switch between them is a row in `inference_assignment_migrations` with
`family='thoughts-writing-route-assignments'`:

- `AskService._routed_assignments_active()` (`services/ask_service.py:431-:435`)
  reads that row. Without it, `ask()` takes the legacy branch (:369-:392):
  `resolve_placement(self._db)` → this machine → `target_unavailable` 409
  with the NOT SET UP reason (:392).
- The thought's coordinator does the same (`services/refinement_coordinator.py`
  `_admission_claim`, the `routed` check; else `resolve_thought_placement` at :314).
  The workbench projection carries it as `intended_placement` with
  `readiness: "unavailable"` (`services/refinement_application_service.py:57-:80`),
  and the face prints `NO ENGINE YET · Choose an engine`
  (`web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:400-:408`).
- Settings reads the same row before it will name an engine for answers
  (`web/routes/system/settings.py:205-:220`); so do `settings_service.py:240-:276`
  and `meeting_service.py:600-:606`.
- The Brief's row "Question did not complete / not set up: …" is this refusal
  from a background `AskService` call: `monday_brief_service.py:274` maps
  `AskService` to the word "Question"; `:342` adds "did not complete".

Who writes the row: `migrate_legacy_config`
(`services/inference_adoption_service.py:3018-:3072`), called at startup by
`migrate_startup_legacy_assignments` (:2973-:3016). It writes the marker ONLY
when Config names a v2 profile for both thoughts and writing. With a blank
pointer or `this_machine` it returns `needs_attention · builtin_profile_required`
and writes nothing (:3031-:3041). The owner's fresh start of 2026-10-08
left the pointer blank. Assigning Qwen in Runs on writes an assignment, not
the marker. So the assignment is `Ready` and Ask, the thought and the Brief
never look at it.

```mermaid
flowchart LR
  RO[Runs on face] --> AS[assignment service<br/>Answers and thoughts: Qwen3.8 27B READY]
  ASK[/api/ask] --> GATE{marker row<br/>thoughts-writing-route-assignments?}
  TH[thought projection] --> GATE
  BR[Brief question] --> GATE
  GATE -- yes --> AS
  GATE -- no, the fresh desk --> LEG[legacy placement<br/>Config pointer → this machine<br/>NOT SET UP]
```

One cause, three symptoms: the 122 s refusal with no reason, `NO ENGINE
YET` beside a ready engine, and the Brief's "not set up" row.

Not verified on his desk: the marker's absence. The sqlite copy was outside
this design's reach. The first act of slice 1 is the builder's query on a
`.backup` copy: `SELECT family FROM inference_assignment_migrations`. If the
row IS there, the cause of the refusal is the route receipt instead (2.2),
and slice 1's reason line finds it; the one-authority change stands either way.

The 122 s: in `ask()` the memory reflect and the grounding read
(`ask_service.py:214-:241`) run BEFORE the placement check (:369). The wait
comes first, the refusal after. The hub log of slice 1's first run confirms
which step took the time.

### 2.2 The reason is thrown away on the face (R1 Ask AI)

`runAsk` keeps the hub's sentence and its bounded `code`
(`web/src/desk/ask.ts:192-:218`). `AskPanel` then maps the sentence through
three regexes to one of three fixed labels (`components/AskPanel.tsx:44-:50`);
anything unmatched prints `THE HUB REFUSED IT · ASK KEPT · EDIT THE ASK`.
The `code` is never read for words. On the routed path a failed run raises
`inference_route_failed` with the execution receipt in its context
(`ask_service.py:346-:350`); the receipt's attempts carry the hub's closed
failure classes (`inference_capabilities.py:1088-:1089`: transient, permanent,
invalid output, context overflow, local capacity), and `served_route`
(`inference_locality.py:86-:112`) reads only the lamp from it. The reason
exists in the hub and dies at the face.

The default prompt is a lens instruction, not a question:
`useDurableDraft("desk-ask", ASK_LENSES[0].instruction)` (`AskPanel.tsx:97-:101`,
`ask.ts:19-:22`): "Summarize the following in 3–4 tight sentences."

### 2.3 Two buttons named Draft update, the first one does not draft (R1)

The Room head's `Draft update` (`features/project-room/ProjectRoomCore.tsx:427-:436`)
calls `updateCtrl.enterUpdates()`, which fetches the list and switches to
the `list` posture (`update/useUpdateController.ts:117-:137`). It drafts
nothing. The list posture shows `Close`, a SECOND `Draft update`, and
"No updates yet. Draft the first one." (`update/UpdatePosture.tsx:540-:585`).
That second button is disabled until the engine is read (`CHECKING ENGINE…`)
and only it calls `ctrl.draft()` (:197-:216) → `POST /api/projects/{id}/updates/draft`
(`web/routes/project_updates.py:95-:110`) → `draft_update`
(`services/project_update_service.py:1924`), a synchronous call with a 120 s
deadline (:1888). On a model failure the service silently substitutes the
deterministic draft and marks the row `deterministic:<code>` (:2056-:2072).
While it runs the face shows a spinner on the button and nothing else: no
engine, no elapsed, no reason.

### 2.4 Terminals is a tmux pane picker, not an app (R1)

The dock button comes from `PanePicker`
(`components/SessionPullout.tsx:240-:272`): `announceLauncher({ id: "panes",
label: "Terminals" })` whose `activate` toggles a transient list anchored
above the dock (`session-pullout.css:152-:160`). Two presses open it and close
it. The list reads `/api/coders/steering/panes` (`desk/steering.ts:578-:590`),
this Mac's tmux panes; with no tmux server it says "no tmux panes". It is
mounted at `DeskApp.tsx:272`. The coder's real terminal is the Lane window's
Raw pane (`lane/LaneWindow.tsx:4, :173`).

### 2.5 The Object menu greys what the object cannot do (R1)

Shot 083's selected object is the Project icon "Ledger migration" (its label
is highlighted), not the note. A Project's capabilities are `["send"]`
(`lib/primitives.ts:533-:545`), so `primitiveCan` (:723-:730) refuses ask,
edit, rename, duplicate, delete, and `handKindOf` refuses the hand-off.
Each verb's `ghost()` returns an excuse (`desk/verbRegistry.ts:468-:623`),
`objectMenuEntries` passes it through (`desk/objectMenu.ts:9-:32`), and
`DeskMenu` draws the row stippled with the excuse (`components/DeskMenu.tsx:401-:434`;
HS-105-05 "ghosting over hiding", :137). A note has all six capabilities
(`primitives.ts:496`); its one ghost is Delete when no face with a receipt
seat is mounted (`verbRegistry.ts:619-:623`, `deleteSeat.ts:8-:10`).

### 2.6 Five readers of the engine, five spellings (R6)

- Ask AI: `Uses group · 192.168.1.43:8080` from `ContextualAssignment`
  (`pages/cores/ContextualAssignment.tsx:12-:17`), plus `USES ASSIGNMENT`
  and `CTX 0.0K/16.4K` in the foot (`AskPanel.tsx:276`).
- Draft update: `192.168.1.43:8080 · LAN`, host only, from `useDraftEgress`
  (`lane/LaneWindow.tsx:868-:900`).
- Thought: `THIS DEVICE` or the target name uppercased, from `engineEgress`
  (`ThoughtWorkspaceWindow.tsx:81-:90`), off the legacy projection.
- Settings: "Summaries: <engine>" (`pages/cores/settingsPrefs.tsx:403-:418`).
- Chair: `No engine yet · Choose an engine` from `meetingPathBlockers`
  (`chair/meetingPathBlocker.ts:60-:90`).
- Receipts: `routeEgress` (`desk/turnRoute.tsx:57-:74`) and `egressFor`
  (`surface/egress.ts`).

The receipt readers are right: they print where bytes went (UX-CANON A.9).
The pre-run readers each invent a spelling.

## 3. The target behavior

### Ask AI (Job 6)

1440: open Ask AI (1 press). The box is empty; the placeholder reads
"Ask about your work". Under it, one line: `Qwen3.8 27B · LAN`. Type, press
Ask (1 press). The HUB turn reads `Asking · Qwen3.8 27B · LAN · 4 s`, counting.
Then the answer, with `Answered in 14 s` on the turn, and Copy · Keep · Discard.
On failure the turn reads `Not answered · Qwen3.8 27B did not answer` (or
`too long for Qwen3.8 27B`, `engine busy`, `timed out after 120 s`,
`no engine for answers`) with Ask again, and Choose an engine only on
`no engine`. 393: the same, in the full-screen pane; the engine line sits
under the box; the verbs are the pane's footer.

Cost: 2 presses (was 4), one window, an answer or a reason. Dead end gone.

### Draft update (Job 5)

1440: Room ▸ Draft update (1 press). The head's button becomes the run line:
`Drafting · Qwen3.8 27B · LAN · 12 s`. The editor opens with the draft and
`Drafted in 31 s` in its foot. On failure: `Not drafted · <reason>` with
Try again and `Draft from the Room's facts` (OWNER CALL 2). The list of past
updates lives under the editor's Back (the UPDATES section) and in the
HISTORY wing; it is not the first thing a press opens. 393: the Room pane,
the same line under the title.

Cost: 1 press to a draft (was 1 press to nothing). Wait: visible.

### The thought

With an engine assigned the band reads `Qwen3.8 27B · LAN` and the verb is
Ask. `No engine · Choose an engine` appears only when the assignment for
answers is empty. The Brief's "not set up" row stops appearing on a desk
with an assigned engine (it is the same refusal).

### The Object menu

On a note: Open, Get Info, Ask AI, Hand to coder, Continue in thread, Edit,
Rename, Duplicate, Move to Zone, Delete. All live. On a project: Open, Get
Info, Ask this project, Draft update, Rename, Move to Zone, Archive. No row
is greyed with an excuse. With nothing selected the menu is one line,
"Select an object" (the existing HS-148-01 collapse).

### Terminals

Not in the dock. A coder lane carries `Open terminal` where its Raw pane
already is. Nothing else changes for terminals in this phase.

## 4. The design

### 4.1 One engine authority (the R6 fix)

Hub, additive:

- `InferenceAssignmentService.routed(capability_id) -> bool`: true when the
  capability has an effective assignment (`_resolve(conn, capability)` status
  `assigned`, :2153) OR the family marker exists. One function.
- Every marker gate calls it: `ask_service.py:431`, `refinement_coordinator.py`
  `_admission_claim`, `settings_service.py:270-:276`, `meeting_service.py:600-:606`,
  `web/routes/system/settings.py:207-:214`, `speech_session/session.py:302, :647`.
  The duplicated SQL goes.
- When `routed()` is true by assignment alone, `migrate_legacy_config` writes
  the marker on the next startup (`inference_adoption_service.py:3018`): the
  assignment IS the chosen profile. Then the gate is only ever true. This is
  the minimal step; parking the legacy branch is slice 7.

Nothing on the wire changes. No migration beyond the marker row the code
already knows how to write.

### 4.2 The reason reaches the face

Hub: the `/api/ask` refusal body (`ask_service.py:346-:350`, `:392`) gains
`reason`, one token from a closed set, beside the `code` it already sends:

| `reason` | source |
|---|---|
| `no_engine` | assignment status `no_assignment` |
| `engine_busy` | attempt class `local_capacity_unavailable` |
| `did_not_answer` | `known_no_generation_transient` |
| `refused` | `provider_permanent` |
| `too_long` | `context_overflow` |
| `not_usable` | `invalid_typed_output` |
| `timed_out` | the route deadline elapsed |
| `stopped` | the owner's cancel |

The attempt class is read from the receipt's last sent attempt (the field
the controller writes per attempt in `inference_adoption_service.py`; the
builder confirms its name there). The same `reason` goes on the draft route's
refusal (4.3) and the thought's `terminal_status` (it already carries a
token, `refinement_thought_service.py:1700`).

Face: `askFailureLabel` (`AskPanel.tsx:44-:50`) is replaced by one table in
`web/src/desk/surface/runWords.ts`, `reason → words`, used by every run:

| `reason` | words | verb |
|---|---|---|
| `no_engine` | No engine for answers | Choose an engine |
| `engine_busy` | Engine busy | Try again |
| `did_not_answer` | `<engine>` did not answer | Try again |
| `refused` | `<engine>` refused it | Ask again |
| `too_long` | Too long for `<engine>` | (shorten) |
| `not_usable` | The answer was not usable | Try again |
| `timed_out` | Timed out after `<n>` s | Try again |
| `stopped` | Stopped | Ask again |
| none | Not answered | Ask again |

The regexes on prose go. The hub's sentence never prints (PHILO-13-04 holds).

### 4.3 Two library species: EngineLine and RunLine

UX-CANON B: a recurring element the library lacks is added to the library.
Both live in `web/src/desk/surface/`.

**`useEngine(capabilityId)`** (`desk/hooks/useEngine.ts`): one hook, reads
`/api/inference/assignments` once per desk (shared store slice, refreshed on
`desk_changed`, as `useDraftEgress` does at `LaneWindow.tsx:884-:900`) and
returns `{ state: "set" | "none" | "unread" | "failed", model, place }` for one
capability: `model` = `entries[0].label` ("Qwen3.8 27B"), `place` from
`boundary` (`same_device` → THIS MAC, `private_network` → LAN, `external_service`
→ the host, as `boundaryEgressLamp` maps, `inferenceEgress.ts:10-:26`).

**`EngineLine`**: the pre-run fact. `Qwen3.8 27B · LAN`. `No engine` + the
library Button `Choose an engine` when `none`. `Engine not read` + `Try again`
when `failed`. Nothing while `unread` (the empty slot never moves its
neighbours, UX-CANON D). No host:port, no `USES ASSIGNMENT`, no CTX meter.
Over-budget material is a run reason (`too_long`), not a meter.

**`RunLine`**: the run and its end, for things that genuinely RUN.
`Asking · Qwen3.8 27B · LAN · 12 s` (elapsed counts on the client from the
press; no new wire), then `Answered in 14 s` or `Not answered · <reason words>`
with the one verb the table names. The verb word per caller: Asking/Answered,
Drafting/Drafted, Summarising/Summarised. This is the meeting summary's
grammar (`chair/intelBadge.ts:10-:16`, `ChairHome.tsx:2611-:2644`) made one
species. Receipts keep their own chip (`RouteEgressChip`): where bytes went
is a per-run fact; `RunLine` prints the receipt's model and place when the
hub returns `route`, so the words match before and after.

Callers after the fold: `AskPanel`, `UpdatePosture`, `ThoughtWorkspaceWindow`
(the band), `ProjectRoomCore` head, `settingsPrefs` headline, `meetingPathBlocker`
(reads `useEngine` state, keeps its own one-line verb). `ContextualAssignment`,
`useDraftEgress` and `engineEgress` are parked
(`web/src/desk/_parked/`, with their tests).

### 4.4 Ask AI face changes

`AskPanel.tsx`:
- Default draft "" (`:97-:101`); placeholder "Ask about your work".
- The head `SESSION · N TURNS` and `NO TRAFFIC` go (`:303-:311`); the traffic
  well shows turns or nothing.
- The foot's status line (`:276-:290`) becomes `EngineLine` before a run and
  the receipt route after it.
- `GROUNDING · GROUND THIS ASK` becomes one ghost Button `Add material` that
  unfolds the existing `GroundingSection` (no modal). Words cluster owns the
  final word.
- The five lens checkboxes: OWNER CALL 1.

A desk-wide ask with no material still answers: the hub already folds the
memory pages and observations into the prompt (`ask_service.py:214-:231`).
No new retrieval.

### 4.5 Draft update

- `ProjectRoomCore.tsx:427-:436`: the head verb calls `ctrl.draft(engine.state === "set" ? "model" : "deterministic")`
  directly; `enterUpdates` is the Back/UPDATES path only. One `Draft update`
  on the face.
- `useUpdateController.ts:197-:216`: `draft()` records `startedAt`; the head
  renders `RunLine` from it; on success the editor opens with `Drafted in N s`
  in its foot (the generator row already carries host and model, `UpdatePosture.tsx:600-:612`).
- OWNER CALL 2 decides the failure shape. Recommended: with an engine SET, a
  model failure is a refusal (409 with `reason`), not a silent deterministic
  draft (`project_update_service.py:2056-:2072`); the face prints
  `Not drafted · <reason>` with Try again and `Draft from the Room's facts`.
  With no engine set, the deterministic draft is made at once and the foot
  says `Drafted from the Room's facts · no engine`.
- The list posture (`UpdatePosture.tsx:540-:587`) stays as the UPDATES section
  under Back; its own `Draft update` button and the `CHECKING ENGINE…` chip go.

### 4.6 The Object menu

- `objectMenuEntries` (`objectMenu.ts:21-:32`) drops rows whose `ghost()` is
  an object excuse. `DeskMenu` keeps ghosting for the other menus; a verb a
  menu cannot run on THIS object is not a row (UX-CANON A.11; the recon's
  ruling). HS-105-05's "ghosting over hiding" stays for state (no selection,
  a running thing), not for kind.
- `primitives.ts:541`: project capabilities become `["send", "rename", "archive"]`.
  `verbRegistry.ts`: `object.rename` on a project opens the Room's name
  EditInPlace (the Room already edits the name; `project_update` is the
  route); a new `object.archive` (group danger, label Archive) calls
  `project_archive` and runs where `object.delete` runs for other kinds. A
  project never offers Delete.
- `object.draft-update` joins the object verbs for a project (the palette
  already has it, `verbRegistry.ts:1001`).
- Delete on a note with no receipt seat: the seat rule holds (`deleteSeat.ts`);
  the row is withheld instead of greyed "Not on the desk".

No hub change. Hand to coder stays as it is.

### 4.7 Terminals

- Park `PanePicker` and its `announceLauncher` (`SessionPullout.tsx:240-:345`)
  to `web/src/desk/_parked/PanePicker.tsx`; remove the mount at `DeskApp.tsx:272`;
  park `session-pullout.css:150-:240` beside it. `systemSprites.test.ts:29-:41`
  counts launchers from source and adjusts by itself.
- The Lane window's Raw pane gets the verb word `Open terminal` beside its
  gadget (`LaneWindow.tsx:173`), so the terminal is reachable from the coder
  that owns it.
- Seams: the dock's 393 list is the windows design; the cut list and the
  word are the words design.

### 4.8 Product words (ASD-STE100)

Verbs: Ask · Ask again · Try again · Keep · Discard · Draft update · Choose
an engine · Add material · Rename · Archive · Open terminal.
Lines: `Qwen3.8 27B · LAN` · `No engine` · `Asking · … · 12 s` ·
`Answered in 14 s` · `Not answered · Engine busy` · `Drafting · …` ·
`Drafted in 31 s` · `Not drafted · Too long for Qwen3.8 27B`.
Placeholder: "Ask about your work".
Gone from these faces: SESSION, NO TRAFFIC, CTX, USES ASSIGNMENT, GROUND
THIS ASK, THE HUB REFUSED IT, ASK KEPT, EDIT THE ASK, NO ENGINE YET, CHECKING
ENGINE…, ENGINE NOT READ, host:port strings, the `Uses group` prefix.

### 4.9 Owner calls

**OWNER CALL 1: the five lenses on Ask AI** (Summarize, Action items, Risks,
Decisions, Draft email; `ask.ts:19-:42`). Recommendation: show them only when
material is selected or added; a desk-wide ask is a question. Other option:
keep them always, as five ghost Buttons under the box.

**OWNER CALL 2: Draft update when the engine fails.** Recommendation: with an
engine set, say `Not drafted · <reason>` and offer `Draft from the Room's
facts` as the second verb; never a silent swap. Other option: keep today's
silent deterministic fallback and print its reason on the row
(`humanFallbackReason`, `update/model.ts:460-:473`), so a press always yields
a draft.

**OWNER CALL 3: a project's danger verb.** Recommendation: Archive (the Room's
`project_archive`, restorable), never Delete. Other option: Delete through
the one receipt, like a note.

### 4.10 Parked, never deleted

- `web/src/desk/_parked/PanePicker.tsx` (+ css): the tmux pane picker.
- `web/src/desk/_parked/ContextualAssignment.tsx`, `useDraftEgress.ts`,
  `engineEgress.ts`: the three pre-run engine readers, once `useEngine` lands.
- `askFailureLabel` and its test (`philo13FacesDoNotLie.test.tsx:52`): parked
  with the regex table, replaced by `runWords.ts`.
- Slice 7: the legacy ask branch (`ask_service.py:369-:392`),
  `resolve_thought_placement`, `Config.thoughts.inference_target_id`:
  parked behind the always-true gate, then moved to `holdspeak/_parked/`
  when a week of his use shows no caller.

## 5. The slices

Each one PR on the fast cycle; `scripts/quick_check.sh` before merge.

### Slice 1: one authority, one reason (build first)

First act: on a `.backup` copy of his DB, `SELECT family FROM
inference_assignment_migrations;` and the hub log of one Ask. Record both
in the PR.

Files: `holdspeak/services/inference_assignment_service.py` (`routed()`),
`ask_service.py` (:346-:350 reason, :431 gate), `refinement_coordinator.py`
(`_admission_claim`), `settings_service.py`, `meeting_service.py`,
`web/routes/system/settings.py`, `speech_session/session.py`,
`inference_adoption_service.py:3018` (marker from assignment),
`web/src/desk/ask.ts` (read `reason`), `web/src/desk/surface/runWords.ts`,
`components/AskPanel.tsx:44-:50` (use the table).

Tests: T1 `tests/unit/test_desk_ask_ai.py`: an assignment and no marker →
`/api/ask` answers through the route; a failed route → 409 with `reason`
from the closed set; `/api/thoughts/*` workbench projection reads
`availability: ready` from the assignment. T2 `askai.app.test.tsx`: each
`reason` prints its words and its verb. T3 unchanged.

Risk: the gate change reaches speech and meetings; `routed()` is true where
it was true before (marker OR assignment), never false where it was true.
The thought's coordinator caches an admission claim at reservation; its
recheck must read the same function.

He judges it: Ask "What do I owe Mira this week?"; an answer from the LAN
engine, or one line that says why not. The thought's band says
`Qwen3.8 27B · LAN`. The Brief's "not set up" row is gone the next morning.

### Slice 2: EngineLine, RunLine, the Ask face

Files: `surface/EngineLine.tsx`, `surface/RunLine.tsx`, `hooks/useEngine.ts`,
`AskPanel.tsx`, `ask.ts:19-:22`, `desk/surface/contract.md`.
Tests: T2 `askai.app.test.tsx` (empty default, the line under the box, the
counting run line over a recorded hub answer, the receipt words after). T3
the sweep's Ask AI at 1440 and 393 (12 px, 44 px, contrast; no new browser file).
Risk: the durable draft key `desk-ask` holds the old instruction on his desk;
the first open clears a draft equal to a lens instruction.
He judges it: open Ask AI; an empty box, one engine line, one count while it runs.

### Slice 3: Draft update drafts

Files: `ProjectRoomCore.tsx:427-:436`, `update/useUpdateController.ts`,
`update/UpdatePosture.tsx:540-:612`, `update/model.ts`,
`project_update_service.py:2056-:2072` and `web/routes/project_updates.py:95-:110`
(the refusal, per OWNER CALL 2).
Tests: T1 `tests/integration/test_desk_project_room.py`: a draft with a fixture
engine returns the model draft; a failed engine returns 409 `reason` (or the
fallback row, per the call). T2 `room.app.test.tsx`: one `Draft update`, the
run line, the editor opens, the failure line and its two verbs.
Risk: the steward's own draft effect (`_effect_draft_update`,
`project_steward_service.py:1515`) keeps the silent fallback; only the owner's
press changes.
He judges it: Room ▸ Draft update; a count, then a draft, in one press.

### Slice 4: the Object menu offers only what works

Files: `desk/objectMenu.ts`, `lib/primitives.ts:541`, `desk/verbRegistry.ts`
(`object.rename` on a project, `object.archive`, `object.draft-update`),
`components/DeskMenu.tsx` (no change expected; confirm the collapse hint).
Tests: T2 `menus.app.test.tsx`: a project's Object menu lists exactly its
rows; a note's lists all ten; no row carries an excuse; Archive calls
`project_archive`. T1 none (the routes exist).
Risk: `hand.test.tsx:232` and `palette` tests assert ghost reasons; they move
to "not listed".
He judges it: right-click Ledger migration; seven rows, every one does something.

### Slice 5: Terminals leaves the dock

Files: `components/SessionPullout.tsx`, `DeskApp.tsx:272`,
`_parked/PanePicker.tsx`, `session-pullout.css`, `lane/LaneWindow.tsx:173`,
`systemSprites.test.ts`.
Tests: T2 `dock.app.test.tsx` (no Terminals launcher), `conductor.app.test.tsx`
(the lane's `Open terminal`). T3 the sweep's dock rows at 1440 and 393.
Risk: none on the hub; `/api/coders/steering/panes` stays.
He judges it: the dock has no Terminals; a coder lane opens its terminal.

### Slice 6: the engine line everywhere

Files: `ThoughtWorkspaceWindow.tsx:81-:90, :400-:408`, `settingsPrefs.tsx:403-:418`,
`chair/meetingPathBlocker.ts`, `UpdatePosture.tsx` (already on `useEngine`
after slice 3), the three parked readers.
Tests: T2 per app (`chair.app.test.tsx`, the thought's `ThoughtWorkspaceWindow.test.tsx`
cases at :316-:373 rewritten against `useEngine` states), T3 the sweep.
Seams: Runs on as a Settings wing is the windows design; it shows one
`EngineLine` per job (speech, answers, summaries) from the same hook. The
Speak face's "Set up speech" is honest (no speech model) and stays; its
words are the words design.
He judges it: every face that uses AI says the same four words.

### Slice 7: park the legacy branch

After a week of green on his desk: `ask_service.py:369-:392`,
`resolve_thought_placement`, the Config pointer, the duplicated gates.
Tests: T1 `test_desk_ask_ai.py` keeps the route path only; the legacy
cases move to `tests/unit/_parked/`.
Risk: the mesh-node and paired-device legs of the legacy branch; speech
keeps `resolve_placement` (`speech_session/plan.py:470, :647`) and is out of
scope.
He judges it: nothing changes on the desk. That is the point.

## 6. What not to do

- **A progress protocol for runs.** No SSE stream, no job table, no polling
  route for Draft update. The press is one HTTP call with a 120 s deadline;
  a client-side count and the hub's reason on return are the whole truth.
- **A retry planner on the face.** The hub's route already falls back across
  the chain; the face prints the receipt, it does not plan.
- **A third authority.** No "effective engine" cache in the browser store
  beyond one shared read; the assignment service is the one place.
- **A terminal app.** A dock app for terminals needs a window, sessions,
  xterm; none of that is this week. The coder owns its terminal.
- **Per-kind menus.** One registry, one filter: rows the object cannot run
  are not drawn. No second menu model for projects.
- **A grounding wizard.** `Add material` unfolds what exists; the desk-wide
  ask answers from memory as the hub already does.
- **Guessing the 122 s.** The builder reads the hub log on the first run of
  slice 1 before touching the reflect step.
