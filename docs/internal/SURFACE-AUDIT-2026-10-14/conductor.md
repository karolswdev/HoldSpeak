# Conductor and agent work surfaces — 2026-10-14

**DRAFT — UNCHECKED, awaiting Muad'Dib. HOLD FOR SHIP.**

Base: `6e86c666ae15c23241f427ca98981a83c5978d92` (#1199). Read-only audit;
no product or test changes. Scope: Conductor, plain sessions, launched coder
lanes, Info, launch sheet, CoderPullout, terminals, Workbenches and their controls.

The rejected Conductor → Codex screen is a real usability failure. Its first
view is an almost empty terminal with a large classification/control footer.
It does not show the working session's identity, current work, or a useful next
action. The launched coder lane provides a better existing starting point,
especially its question/answer well, but exposes too much delivery machinery.
Conductor's own Needs you / At work ordering is worth keeping.

## Evidence and limits

Root supplied the unchanged verified frontend and its general sweep shots.
Additional captures used the actual production app on a new isolated hub,
`tests/e2e/glass_infra.py:_boot` and `tests/e2e/conductor_rig.py:_seed`. An
additional unbound Codex session was created through `ingest_agent_hook_event`.
No product responses were stubbed. No real tmux, microphone, credentials,
owner hub, or owner DB was used. Machine-state isolation switches were set.
Both runs went through `scripts/test_lock.py` using the root's isolated wrapper.

Shots: `.tmp/evidence-shots/surface-audit-conductor/`; capture source and final
393 observations: `.tmp/surface-audit/conductor/`. The six critical poses were
captured and visually inspected at 1440×900 and 393×852. All captured critical
poses had no recorded browser page errors. This is not a behavioral test pass.

Two capture attempts, then stopped. Attempt 1 captured the six 1440 poses and
stopped during optional Workbench navigation, where `_normal_chair` waited for
a hidden Chair. Attempt 2 captured the six 393 poses and stopped when direct
`/workbenches` navigation did not expose the requested `+ Create` locator.
Neither optional fixture/navigation failure is classified as a product defect.
Logs: `.tmp/surface-audit/conductor-capture.log` and
`.tmp/surface-audit/conductor-capture-2.log`.

The first unbound session's nonexistent repository path let the producer derive
`home` as its project. The second attempt gave it an isolated repository marker;
Conductor and Info then correctly said `payments-ledger`. Use those **393 shots**
for finding 2. First-attempt shots are preserved under
`.tmp/surface-audit/conductor/attempt1/`. The deliberately absent tmux pane and
launch worktree are fixture facts, not product defects. Findings concern how
the face handles those states.

## Ranked findings

### 1. The plain session gives classification and control the most prominent actions

**Owner cost:** The owner opens a working coder and gets an empty pane plus
`ARM`, `CLASSIFY`, `Keep as note`, two mic affordances, an `HS-87-05` example
field, and Pin. There is no leading work fact. At 1440 the footer occupies
roughly 180 px while the large body contains only the node and pane absence.
At 393 the same secondary controls dominate the bottom third. A successful
component guard cannot make this hierarchy useful.

**Evidence:**
`.tmp/evidence-shots/surface-audit-conductor/session-plain-no-pane-1440.png`,
`session-plain-no-pane-393.png`;
`web/src/desk/components/SessionPullout.tsx:752` renders facts/question/pane;
`:790` renders the large footer; `:803` leads with Arm;
`:833` always adds Classify; `:637` adds a separate story-pin mic and field.
The additional keys, factory controls, grounding and rails are source-only
authorized variants (`:804`, `:513`, `:524`), not observed live panes.

**Fails:** Tenets 2, 3, 6 and 7; UX-CANON A.5, C and D.
**Repair:** Lead with session identity, state and the latest reported work.
Use the existing question/answer well when it needs the owner. Keep terminal
content behind Open terminal. Move classification, pinning and session control
out of the default footer into existing object operations or one folded detail
area. Keep one visible next action and its receipt.
**Confidence:** High, observed at both widths.

### 2. A working unbound session loses its known project when Open is pressed

**Owner cost:** Conductor identifies `payments-ledger`; Open changes the title
to lowercase `codex`, repeats only `node / this Mac`, and puts the raw session
id in the footer. Several working Codex sessions become difficult to distinguish.

**Evidence:**
`.tmp/evidence-shots/surface-audit-conductor/conductor-populated-393.png`,
`conductor-session-info-393.png`, `session-plain-no-pane-393.png`.
`web/src/desk/components/SessionPullout.tsx:716` looks up the project only in
`useDesk.items.coder`. That bucket comes from `/api/coders/status`
(`web/src/desk/api.ts:911`), whose server selects awaiting sessions
(`holdspeak/web/routes/system/coders.py:119`, `:122`). Conductor instead reads
the full session registry and already has the folder name
(`web/src/desk/agentFlights.ts:90`, `:94`). Thus this working session is known
to Conductor but missing from the title's lookup. A waiting session can have
different results; this finding concerns the working state.

**Fails:** Tenets 3 and 7; UX-CANON A.7 and A.10.
**Repair:** Resolve the session subject by its compound key from the existing
all-session projection. Use its work title, else project/folder, with the human
agent name. Keep the session id inside Info. No new data system is needed.
**Confidence:** High, corrected fixture observed at 393 and source chain traced.

### 3. The phone session fails the existing full-width window grammar

**Owner cost:** At 393, the plain session is 361.55 px wide and exposes the
Conductor behind it on the right. The separate scrolling footer leaves Pin
below the initial view. The owner has to recognize multiple scroll regions
to operate a nearly empty session.

**Evidence:**
`.tmp/evidence-shots/surface-audit-conductor/session-plain-no-pane-393.png`;
measured window bounds in `.tmp/surface-audit/conductor/observations.json`.
The neighboring Conductor, Info and launched lane are all 393 px wide on that
same hub. `web/src/desk/components/session-pullout.css:2` sets the session to
`width: min(620px, 92vw)`; `:387` caps its control area at `30vh` with its own
vertical scrolling. The rendered Pin is outside the initial footer view;
this is not a claim that it can never be reached.

**Fails:** Tenets 3, 5 and 6; Constitution VIII.3; UX-CANON D.
**Repair:** Let the shared frame own phone width. Keep the body as the main
scroll region and the footer to the current action plus receipt. Use a fold
for secondary controls rather than a second scrolling console.
**Confidence:** High, screenshot and measured geometry.

### 4. A missing terminal is a dead end, while unrelated action controls remain available

**Owner cost:** `no pane on this session` is a true fact but provides no way
back to useful work. ARM remains visible. The launched Raw view has the same
blank result, with Keys and Re-brief/ARM/Stop still around it. An unavailable
terminal becomes an empty screen rather than a local, understandable state.

**Evidence:**
`.tmp/evidence-shots/surface-audit-conductor/session-plain-no-pane-393.png`,
`lane-codex-raw-no-pane-1440.png`, `lane-codex-raw-no-pane-393.png`.
`web/src/desk/components/SessionPullout.tsx:60` names absences;
`:784` renders only the status label even though `paneDetail` is read at `:671`;
`:803` mounts Arm independently of absence. ArmStrip's default branch at
`:133` has no absent-pane disabled condition. The launched Raw rendering
also supplies only a label (`web/src/desk/lane/LaneWindow.tsx:778`), and mounts
Keys at `:783`. The generic Delivery terminal handles absence differently,
hiding its footer (`web/src/desk/components/DeliveryTerminalWindow.tsx:233`),
which is source-only coverage.

**Fails:** Tenets 3 and 7; Constitution VI.1; UX-CANON A.10 and A.11.
**Repair:** Keep the session's work visible when terminal access fails. Put
the exact absence and an existing Retry/Return to session action where the
pane would be. Offer pane-dependent controls only when their target can be
resolved. Do not treat a missing pane as a missing coder.
**Confidence:** High for the observed absence layout; no Arm, key or send was
performed, so no claim about their execution result.

### 5. The launched coder lane makes the delivery process compete with the owner's question

**Owner cost:** The question appears in the answer well and again in the
timeline. A seven-station strip appears before it, including stages that have
no facts. A pending `MERGE · Your press in GitHub` row appears even before a
PR exists. In the captured asking state, `YOLO · ARM FIRST` and ARM appear
beside the answer and again in the footer. At 393 the process furniture uses
precious space before and after the actual reply. The real question/answer
well itself is a useful existing component.

**Evidence:**
`.tmp/evidence-shots/surface-audit-conductor/lane-claude-asking-1440.png`,
`lane-claude-asking-393.png`, `lane-codex-working-393.png`.
`web/src/desk/lane/LaneWindow.tsx:270` mounts the head, `:271` the station
track, `:279` the question, and `:256` the timeline. The question is added
again by `web/src/desk/lane/laneWire.ts:493`; the speculative Merge row is
unconditional when not merged (`:513`). ArmLine mounts in the answer
(`LaneWindow.tsx:433`) and footer (`:817`). Missing worktree/pane facts in
these fixtures explain some unavailable values; their absence is not a bug.

**Fails:** Tenets 3 and 7; UX-CANON A.5 and D.
**Repair:** Show the question and its answer once at the top. Show one current
state, then actual recorded activity. Fold the process track and branch details.
Show PR/Merge operations when a PR exists. Show the relevant authority fact
once at the action that requires it, using the existing policy behavior.
**Confidence:** High for the repeated layout; no claim that all seeded stages
represent a real fully provisioned launch.

### 6. The same coder has several operational faces with different vocabularies

**Owner cost:** Open means a raw SessionPullout for an unbound coder and a
LaneWindow for a launched coder. Info opens a third window that repeats the
identity/state before offering Open again. Source also retains CoderPullout's
Reply/Use the hotkey/Watch live flow, and a separate target terminal. The owner
must learn whether to Answer, Send reply, Steer, Re-brief or Watch live based
on how the session was obtained.

**Evidence:**
`.tmp/evidence-shots/surface-audit-conductor/session-plain-no-pane-393.png`,
`lane-claude-asking-393.png`, `conductor-session-info-393.png`.
`web/src/desk/conductor/open.ts:16` and `:29` choose the doors;
`web/src/desk/openObject.ts:159` and `:165` split session and launch refs;
`web/src/desk/components/SessionPullout.tsx:684` explicitly gives launched
sessions to the lane. Info duplicates the identity through GetInfo
(`web/src/desk/conductor/ConductorInfoWindow.tsx:85`). CoderPullout remains
registered (`web/src/desk/pullouts/registry.ts:35`) with Send reply and
Watch live (`web/src/desk/pullouts/CoderPullout.tsx:129`, `:176`). Its
launched-session redirect exists at `web/src/desk/store/compositorSlice.ts:268`.
The coder pullout and target terminal were not rendered in this audit.

**Fails:** Tenets 3, 5 and 7; UX-CANON A.5 and D's one object grammar.
**Repair:** Use one session content grammar for plain and launched coders,
adding existing launch/PR facts when available. Fold Info facts into that
session. Fold the legacy coder reply path into the same answer well. Keep
the immutable target terminal as terminal content reached from its owner,
with its existing target semantics. Park the dock pane picker as the October
13 `DESIGN-verbs.md:370` already proposes. This is a face consolidation,
not a replacement framework or authority redesign.
**Confidence:** High for the observed split; medium for the full reachability
of the source-only legacy card and target terminal.

### 7. Workbench first-use failures can disappear without a receipt

**Owner cost:** A failed list read can be shown as `No workbenches yet`. A
failed template or Blank creation simply stops being busy and leaves the
chooser in place. The owner cannot tell whether work was saved or retry
confidently. This sits directly on the first use path.

**Evidence:** Root's observed empty-list context:
`.tmp/evidence-shots/desk-sweep/surface-workbenches-1440.png` and
`surface-workbenches-393.png`. **Failure behavior is source-only, not an
observed error state.** `web/src/pages/cores/WorkbenchesHomeCore.tsx:55` and
`:59` swallow read failures; `:79` then renders the empty branch.
`web/src/desk/components/WorkbenchTemplatePicker.tsx:57` and `:77` swallow
creation failures, without setting the error used by the load-failure face.

**Fails:** Tenets 2 and 3; Constitution VI.2; UX-CANON A.10.
**Repair:** Give list read failures their own retry state. Keep a named write
receipt beside the chosen template/Blank action and retain the choice on
failure, using the existing write receipt pattern. Do not turn an unread
list into an empty one.
**Confidence:** High in the code path, unverified on rendered error glass.

## Coverage census

`Both` means the actual rendered pose was visually inspected at both widths;
it does not mean every state or action of that face was exercised.

| Face / state | 1440 / 393 | Evidence and limit |
|---|---|---|
| Conductor populated, asks + working + PR row | Both | `surface-audit-conductor/conductor-populated-{width}.png`; fresh seeded hub |
| Conductor ready agents / No hooks | Both | Root `desk-sweep/conductor-{width}.png`; Install not pressed |
| Conductor read failure, empty, ended fold, Stop confirmation | Source-only | `ConductorWindow.tsx:524`, `:604`, `:684`, `:150` |
| Plain working SessionPullout, no pane | Both | `session-plain-no-pane-{width}.png`; corrected project at 393 |
| Plain session asking/answer, armed/direct/live terminal | Source-only | `SessionPullout.tsx:760`, `:766`, `:804`; no mic/Arm/send actions |
| Conductor Info for an unbound working session | Both | `conductor-session-info-{width}.png`; name/project correction at 393 |
| Ready-agent Info; launched Info details | Source-only | `ConductorInfoWindow.tsx:43`; launched Info was traversed, not captured/read as its own pose |
| Launched Codex working | Both | `lane-codex-working-{width}.png`; absent worktree is intentional fixture state |
| Launched Claude asking | Both | `lane-claude-asking-{width}.png`; answer field observed, no send |
| Launched Raw, no pane | Both | `lane-codex-raw-no-pane-{width}.png`; no live ANSI or keys |
| Launch sheet (Hand to coder); held approvals; Re-brief/Stop outcome | Source-only | `HandSheet.tsx:415`, `LaneWindow.tsx:590`, `:627`, `:838` |
| CoderPullout | Source-only | `pullouts/CoderPullout.tsx`; still registered, launched coders redirect |
| PanePicker / Terminals launcher | Source-only, still mounted | `SessionPullout.tsx:240`; `DeskApp.tsx:271`; proposed parking is not yet implemented |
| Delivery target terminal | Source-only | `DeliveryTerminalWindow.tsx:190`; no target or stream was created |
| Workbenches list, empty | Both | Root `desk-sweep/surface-workbenches-{width}.png`; Create visible in those shots |
| Workbench chooser and template object | Blocked capture; source-only | Two optional fixture/navigation failures described above; no product defect inferred |
| Workbench Items, expanded item, Config, Runs, Memory | Source-only | `WorkbenchWindow.tsx:1567`, `:1699`, `:1974`, `:1987`; all inner states unobserved |
| Workbench schedule/event/idle policy and agent selection | Source-only | `WorkbenchWindow.tsx:356`, `:448`; `WorkbenchAutomations.tsx`, `WorkbenchResourceful.tsx` |

## One recommended session layout

The Tuesday job is: **see what this coder is doing; answer or direct it when
needed; inspect its terminal only when that helps.** Compose the existing
frame, state, question well, PadGadget, activity rows, folds and footer.

| Region | 1440 desktop window | 393 phone |
|---|---|---|
| Title bar | Close, agent sprite, work title or project, normal shared gadgets | Back, same identity, shared full-width frame |
| First body row | One state fact, latest report time; agent/model as quiet metadata | Same row, metadata wraps |
| Needs owner, when present | One complete question or held call; multiline answer with one mic and Answer, or Deny/Approve | Same order; answer field owns a full row and its verb is wholly visible |
| Current work | Latest reported assistant text/tool, then actual recorded activity; launch adds existing PR/file facts | One column with the same order; no empty future stages |
| Details | Folded session id, node, path, branch and launch facts; existing control mode here unless needed at a current action | Same fold inside body; no separate scrolling control footer |
| Terminal | Open terminal reveals the existing pane and Keys fold; absence keeps identity/current work and provides Retry/Return | Same view, full width, one body scroll |
| Footer | Current action and its receipt; egress at the action that sends | Same; no permanent Classify or pin form |

**Fold or park:** Classify/story pin form; duplicate policy/ARM furniture;
future station markers; duplicate question in the timeline; Info's redundant
identity window; CoderPullout's second reply composer; dock PanePicker. Preserve
the existing kernel, grants, session keys, immutable terminal targets and
receipts. This audit recommends a presentation change, not bypassing them.

**Smallest repair order:** (1) fix title lookup and phone width at their existing
seams; (2) replace the plain session's default body/footer composition with
the layout above and its unavailable-terminal state; (3) bring the launched
lane into that same grammar, folding duplicates; (4) fold the extra doors and
give Workbench first-use failures receipts. Inspect actual populated, asking,
unavailable and completed states before calling the repaired face usable.

**Tuesday:** Conductor can identify the coder that needs the owner. The plain
Codex session cannot yet help him understand or manage that coder on first
open. The launched answer well can, once its process/control repetition is
reduced. Workbench inner usability and real send/terminal behavior remain
unverified.
