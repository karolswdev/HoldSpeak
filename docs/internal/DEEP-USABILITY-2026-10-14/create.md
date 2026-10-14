# Create — deep usability audit, 2026-10-14

Status: baseline audit complete; settled Create repair implemented and held
for integration. Baseline: `eb9a3266e`. Baseline source anchors below refer
to that revision and drift after the repair. Current verification and precise
remaining gaps are recorded at the end.
Owned lane: Knowledge, Recipe/Agent, Workflow, Artifact, Directory/Zone,
Thread; actual authoring, save/cancel, return and finding the result.

The Tuesday job is to collect decision context, configure a reviewer, make a
small review workflow and keep a conversation without losing the words.
Tenets 2, 3 and 7 set priority; Tenets 1, 4 and 5 constrain the repair.

## Method and evidence limits

Read Constitution, UX-CANON, latest phase-17 designs, prior surface census,
the active producer routes, object projection and editor handlers. The
prior census explicitly did not render Knowledge/Recipe/Workflow/Artifact/
Directory or their editors; its app sweep cannot verify these jobs.

Scratch walk: `.tmp/deep-usability/create_walk.py`, launched through
`.venv/bin/python .tmp/deep-usability/locked.py create-walk .venv/bin/python
.tmp/deep-usability/create_walk.py`. It uses existing glass `_boot` and a
fresh HOME/DB at each width; no owner port, machine state, keys, microphone,
terminal transport, real inference or external delivery. Results and shots
will be in `.tmp/deep-usability/create/`; run log is
`.tmp/deep-usability/create-walk.log`.

UI creation and fixture setup are distinct: Knowledge, Agent, Workflow and
Thread use Search and their actual New action. A legacy prompt-only Workflow
uses real CRUD as setup. Artifact uses the production run-artifact recorder
with synthetic output and is not proof of a successful inference run.
Directory uses real CRUD to examine the deliberately parked access path.
The refused edit replaces one browser PUT response with 503 and is a boundary
failure observation, not a real hub outage.

## Ranked findings

### 1. Knowledge authoring offers a body that the entity cannot save

Cost: silent loss of written material. Tenets 2/3/7; Constitution VI.2–3.

`web/src/desk/pullouts/editors/KbEditor.tsx:35` restores a body draft;
`:142` renders DeskEditor; `:147` sends `body_markdown`. The update route
`holdspeak/web/routes/primitives/kbs.py:94` passes only name and member_ids
and returns 200 at `:99`. The canonical KB entity has only name and memberIds
(`web/src/lib/primitives.ts:217`), `fromWireKb` discards any body
(`web/src/desk/api.ts:286`), and the repository describes Knowledge as a
container and stores no body (`holdspeak/db/primitives.py:355`, `:384`).

The generic writer marks every 2xx patch saved (`web/src/desk/store/dataSlice.ts:644`,
`:659`) and `useDebouncedSave.ts:26` then forgets the draft fields. Thus the
source causes both false confirmation and removal of the recovery copy.

Observed at **1440 and 393**: Search → New Knowledge (real POST 201) → name
"Architecture decision context" → body "KEEP THIS BODY: rollback owner is
Jordan." → wait → real PUT 200 containing the body in its request, absent
from its response → footer **KEPT · time** → Save → reload → Search by the
saved name → Edit. The body is empty; only the "Write" placeholder remains.
Exact request/response and read events are in
`.tmp/deep-usability/create/observations.json`. Inspected pairs:
`knowledge-before-save-1440.png` / `knowledge-body-after-reload-1440.png` and
`knowledge-before-save-393.png` / `knowledge-body-after-reload-393.png` in
that directory. The owner can lose authored words while the UI reports them
kept. This is the first repair.

Smallest repair: make Knowledge name plus member collection using the
existing member routes, SurfaceRows and filing grammar. Stop unsupported
body authoring. If retained unsupported text exists, offer explicit recovery
through the existing Note producer and keep it until success. Do not add a
second document entity or a KB body backend to justify this field.

### 2. Shared Save/Cancel verbs have the same side effect

Cost: cancellation changes saved work; a failed save can be closed as though
successful. Tenets 2/3/4; UX A.11 and Constitution VI.3.

Every editor sends keystrokes after 450 ms
(`web/src/desk/pullouts/editors/useDebouncedSave.ts:18`, `:35`). Both verbs
call `closeEditor` in the standalone host
(`web/src/desk/components/InlineEditor.tsx:62`, `:65`) and embedded Knowledge
(`web/src/desk/pullouts/KbPullout.tsx:81`), Agent
(`web/src/desk/pullouts/RecipePullout.tsx:89`) and Workflow
(`web/src/desk/pullouts/WorkflowPullout.tsx:49`). `closeEditor` only clears
editor selection (`web/src/desk/store/deskSlice.ts:109`). It cannot cancel
the already landed writes. Embedded editor footers show no save receipt.

Observed at **1440**: Knowledge title changed to "Cancelled architecture
title" → wait → Cancel. GET returns the changed title. Agent name, role and
system prompt, and Workflow name plus three graph steps, likewise remain
saved after Cancel; the real 200 requests and subsequent GETs are recorded.
Inspected `knowledge-after-cancel-1440.png`, `recipe-return-1440.png` and
`workflow-return-1440.png`.

Observed at **1440**, browser boundary failure: Edit Knowledge → replace one
PUT with 503 → title "Refused knowledge edit" → wait. A global **SAVE FAILED
· HTTP 503**, Retry and OK appear, so failure itself is disclosed. Press
Save: editor closes to the object view while the hub keeps the previous
title. Inspected `knowledge-refused-edit-1440.png` and
`knowledge-refused-save-closes-1440.png`. Classify this as **close despite
failure**, separately from the successful-200 silent Knowledge body loss.

Phone Cancel is intentionally in footer **More actions**; the initial direct
button selector did not traverse that menu. The second attempt exercised
Knowledge More → Cancel and the 503 → Save path at **393**, with the same
durable result and editor closure. Inspected
`knowledge-refused-edit-393.png` / `knowledge-refused-save-closes-393.png`.
The action is not dead. Agent/Workflow More in that second run matched an
occluded background window's control. That is a precise selector gap;
their phone Cancel/return and legacy prompt edit remain unobserved. No third
setup attempt was made.

Smallest repair: retain autosave with one honest Done/Back action, one shared
save authority and actual pending/saved/failure receipt. Flush pending work
before close; failed work retains its editor and draft with Retry. Reuse the
current debounced writer and draft store. Include every existing consumer,
including Note, and both editor hosts. Avoid a rollback framework.

### 3. Workflow step fields and actions leave the window

Cost: cannot see or revise a prompt or reach its move/remove controls in the
displayed row. Tenets 2/3/5/7; Constitution VIII.3, UX B/D.

Observed at **1440 and 393**: Search → New Workflow → rename → + LLM prompt
→ type "Find risks and name the accountable person: {input}" → + Action
items. The long LLM step label pushes the Prompt gadget off the right edge;
its move/remove controls are beyond the visible window. Inspected
`workflow-edit-1440.png` and `workflow-edit-393.png`. This is visible in a
short, three-step workflow, without a large fixture.

Source: `web/src/desk/pullouts/editors/WorkflowEditor.tsx:72` renders the
long step label and the Prompt StringGadget at `:89` in one flex row;
`web/src/desk/components/mission-control.css:7` supplies no wrap, `:12`
makes the label nowrap, and `:17` sizes only the raw input rather than its
StringGadget wrapper.

Smallest repair: compose a step as label/actions plus a wrapping parameter
well with existing Button and PadGadget; stack under the surface container
query. Keep the same graph producer and palette. Do not add a canvas or
workflow framework to repair a row.

### 4. Workflow Edit cannot edit a prompt-only Workflow

Cost: cannot revise existing automation. Tenets 2/3/7; UX A.11.

The live CRUD route accepts a prompt with no graph
(`holdspeak/web/routes/primitives/workflows.py:30`). The view handles prompt
as a step (`web/src/desk/pullouts/WorkflowPullout.tsx:21`), but the editor
only parses graphJson (`web/src/desk/pullouts/editors/WorkflowEditor.tsx:31`)
and renders "Graphed on iPad" when parsing fails (`:135`). A missing graph
is not evidence of iPad control flow.

Observed at **1440**: real CRUD POST creates "Legacy prompt review" with
prompt "Find design risks" and empty graph; response declares
`support: prompt_workflow`. Search → object displays that prompt → Edit
displays only the name field and "Graphed on iPad". Inspected
`workflow-legacy-view-1440.png` and `workflow-legacy-edit-1440.png`.

Smallest repair: distinguish prompt-only from unsupported graphs. Edit the
existing prompt with PadGadget and the same save contract. Leave branching
graphs intact and explain the actual editing limit in one true label.

### 5. Raw editor controls do not use the library Button

Cost: inconsistent action grammar and possible phone target/scroll trouble.
Tenets 4/5; UX A.1. Current source examples: Agent More
(`web/src/desk/pullouts/editors/RecipeEditor.tsx:109`), Workflow move/remove
and palette (`web/src/desk/pullouts/editors/WorkflowEditor.tsx:97`, `:110`,
`:124`), Knowledge proposal Accept/Reject (`KbEditor.tsx:112`, `:119`).
The AI proposal state requires real or controlled inference and remains
outside this no-inference audit. Prioritize controls actually used in the
repair; use existing Button, PadGadget and surface layout.

## Parked tail — do not count as an active defect

Directory is intentionally absent from the live face and palette:
`web/src/desk/verbRegistry.ts:101`, `:434`, `:573` and
`web/src/desk/components/DeskToolShelf.tsx:661`. The compatibility pullout's
"Drop items here" handler is a no-op
(`web/src/desk/pullouts/DirectoryPullout.tsx:73`) but no live owner click has
reached it. Do not revive zones as part of the editor repair.

## Inner-state matrix

Both widths rendered and inspected unless the cell states otherwise.
API setup does not count as a UI create success. A captured empty state
does not prove the result of an unexecuted operation.

| Object | Create | Populated / empty | Editor | Save / Cancel | Return / find | Failure |
|---|---|---|---|---|---|---|
| Knowledge | actual New UI / 201 | empty and typed body | both widths | Save/body loss both; Cancel 1440; phone menu retry | actual Search/reload/Edit both | 503/close despite failure 1440; phone retry |
| Agent / Recipe | actual New UI / 201 | typed name/role/instructions | expanded More both | Cancel persists 1440; phone selector gap | actual Search → Continue in thread / 201 at 1440; phone selector gap | no default engine disclosed; no inference run |
| Workflow | actual New UI / 201; legacy API setup | three steps both; legacy 1440 | linear clipped both; legacy noneditable 1440 | Cancel persists 1440; phone selector gap | actual Search at 1440; legacy phone selector gap | run source only |
| Artifact | production recorder fixture | populated output both | no registered editor, generated output | not applicable | actual Search/open both | source only; Copy/Send unexecuted |
| Thread | actual New UI / 201 both; also Continue at 1440 | empty and typed draft both | actual rename/composer both | actual close/reopen 1440; 393 helper did not click Back, so same-window draft only | actual Search by renamed title both | actual Send / HTTP 400 both; draft kept, user turn stored, no answer |
| Directory | API setup only | source only, parked | no registered editor | not applicable | absent from Search both, as designed | source only |

Knowledge row update: Cancel and 503/close despite failure are observed at
both widths after the second attempt. Artifact and Directory captures came
from the first attempt. Thread captures came from the second. Every cited
shot was opened and inspected. No test suite green is claimed.

## Other observed limit

Thread rename and draft retention are observed at both widths. Actual
New Thread → Rename → type unsent words → close → Search by name → open
restores the exact draft at 1440. The baseline helper used "Close" rather
than the phone's "Back from" control, so 393 proves only same-window draft
retention; phone close/reopen remains unobserved.
On a fresh isolated hub with no default engine, Send returns HTTP 400,
keeps the draft and also stores/draws the user turn. The face says **SEND
TURN FAILED · HTTP 400** without a visible setup action there. Inspected
`thread-draft-return-{1440,393}.png` and `thread-no-engine-{1440,393}.png`.
Recorded user messages are in `observations-retry.json`. This is not proof
of an answer or a lost draft. Retry duplication was not exercised; do not
claim it. Keep this outside the settled editor repair unless root expands
scope from the observed cost.

## Small coherent implementation scope

Root settles ownership before any product edit. Proposed bounded files:

- Shared save authority/draft lifecycle: `pullouts/editors/useDebouncedSave.ts`,
  `editorDraft.ts` if recovery needs its existing helpers, `editors/types.ts`.
- Existing consumers: `NoteEditor.tsx`, `KbEditor.tsx`, `RecipeEditor.tsx`,
  `WorkflowEditor.tsx` in that directory; no new editor framework.
- Hosts/footers: `components/InlineEditor.tsx`, `pullouts/NotePullout.tsx`,
  `KbPullout.tsx`, `RecipePullout.tsx`, `WorkflowPullout.tsx`.
- Workflow layout: `components/mission-control.css` (only the initial
  workflow block) or existing editor stylesheet under root's exact brief.
- KB membership: reuse current member routes and SurfaceRows rather than
  adding DB columns. `components/DeskFilingStrip.tsx` is an existing reverse
  membership producer, not automatically lane-owned.

Existing focused tests to adapt: `web/src/desk/components/InlineEditor.test.tsx`,
`web/src/desk/__tests__/deskRemembers2.philo1307.test.tsx`,
`web/src/desk/__tests__/speakableDesk.test.tsx`. Root can name a single focused
editor interaction test file for real loss/retry/member/prompt behavior, plus
`tests/e2e/test_creation_glass.py` only if it extends actual Save→reload→read
coverage. Its baseline `:176`–`:190` assertions check the name in the open
window, not persisted body after save/reload. The read-only baseline phase
did not run or edit tests; the implementation checks are below.

## Tuesday

Observed Knowledge body loss and false Save/Cancel prevent trusted authoring.
Workflow parameter clipping blocks a small useful review workflow at both
widths. Owner usability is not ratified by these isolated observations.
No owner acceptance, real model output or physical phone interaction is
claimed. HOLD FOR SHIP; no stage or commit.

## Implemented repair and native canvas

Root read and accepted the native direction before product edits:
`canvas/deep-create/` in this folder. Production Button, StringGadget,
PadGadget and SurfaceLedger compose Knowledge, Agent, linear Workflow,
prompt-only Workflow and saved/failure/recovery artboards. Both sizes are
captured under `.tmp/deep-usability/create-canvas/`.

The existing debounced writer now publishes its local status and flush
authority to all four consumers and their standalone/embedded hosts. Done
flushes the current revision. A refused write retains the editor and durable
draft with Retry. It acknowledges only fields actually carried by each
accepted write and keeps newer pending values. It does not use an older
keptAt timestamp as proof of a newer revision.

The existing frame has an optional beforeClose guard. It awaits a mounted
editor before departure or WAAPI motion, deduplicates pending close presses
and restores availability after refusal. Pullout registers a local guard
only while a supported ordinary editor is mounted, and removes it on
unmount. Root owns the separate Thought writer integration.

Knowledge now edits its name and real member edges using the existing
GET/PUT/DELETE membership routes. The Add items well lists actual saved
objects; it does not create a document body. Retained unsupported text has
an explicit Save as Note action through the existing Note producer and then
membership producer. A partially completed recovery keeps its created Note
id beside the retained text, so retry does not create another Note. Already
forgotten text cannot be recovered.

Workflow composes its step header/actions above its parameter Pad. Library
Buttons replace the touched raw controls. Prompt-only Workflows edit their
existing prompt; branching graphs are left intact. The browser found one
additional real picker defect: productLabel did not recognize roadmap and
threw a route error when Add items listed a real Roadmap. Knowledge now
uses the existing kind label map with the existing kindWord fallback, and
the regression includes a Roadmap.

## Executed scoped checks

Every command used `.tmp/deep-usability/locked.py`, a fresh HOME, the machine
lock, Node 22 and installed Vitest with **two workers**. No dependency change,
broad suite, owner state or external operation was used.

| Check | Collected / executed result | Log under `.tmp/deep-usability/` |
|---|---|---|
| Initial five named editor files | 40 collected; 5 files / 40 passed | `create-collect.log`, `create-focused.log` |
| Diagnosed frame guard: windows, Pullout, InlineEditor | 35 collected; 3 files / 35 passed | `create-frame-collect.log`, `create-frame-focused.log` |
| Picker kind regression and affected editor/voice/host files | 3 files / 21 passed | `create-picker-focused.log` |
| Final canonical failure-cause regression | 9 collected; 1 file / 9 passed | `create-cause-collect.log`, `create-cause-focused.log` |
| Final Workflow chrome dispatch regression | 5 collected; 1 file / 5 passed | `create-workflow-chrome-collect.log`, `create-workflow-chrome-focused.log` |

These runs overlap; their counts are not added. The nine final regression
names cover callable writer publication, flush completion, failed Done and
Retry, newer in-flight values, superseded refused fields, canonical Knowledge
failure cause, actual membership, partial recovery id reuse, prompt-only
editing and branching preservation (some related facts share one test).
The existing normal-motion frame test also proves that refusal starts no
departure animation and that another close remains possible.

Scoped typecheck before the last integration changes reported no Create
diagnostics and only the other lane's temporary ByRoleOptions errors. Root
owns the fresh combined typecheck and quick check. No final typecheck green
is claimed here.

## Real after walk and remaining proof gaps

Scratch: `.tmp/deep-usability/create_after.py`. Two after attempts were made;
no third browser retry was made in this lane. First attempt found and fixed
the real Roadmap picker crash. The second captured normal motion at **393**
on built id `ef1cac51f666efce`. This build precedes the final canonical
failure-cause wording fix; that small fix has its focused regression above.

All following shots under `.tmp/deep-usability/create-after-retry/` were
opened and inspected. The same directory's observations.json records
actual API responses and an isolated temporary DB path.

| Actual UI job at 393 | Observed result | Inspected shot |
|---|---|---|
| New Note → type title/body → Done | GET returns exact typed body | durable JSON in observations |
| New Knowledge → Add items → choose saved Note → Done | real member edge retained; no body editor | `knowledge-items-393.png` |
| Edit name → PUT 503 → Done → normal-motion Back | editor and typed name stay visible through both failed closes | `knowledge-failed-close-kept-393.png` |
| Retry → 200 → Done → Back (assert detached) → Search | changed name and original member survive actual return | `knowledge-retried-393.png`, `knowledge-return-393.png` |
| New Agent → name/role/instructions → Back before debounce | close flushes; GET retains all fields; Search opens it | `agent-return-393.png` |
| New Workflow → AI prompt and Action items → Move up → Done | all control centers owned their visible button; graph stores reordered steps and prompt | `workflow-editor-393.png`, `workflow-return-393.png` |
| API setup of legacy prompt Workflow → UI Edit → multiline Prompt → Done | GET returns the edited prompt; graph stays empty | `workflow-prompt-editor-393.png` |

The second attempt stopped at the retained-text **fixture**, before 1440:
the live localStorage mutation did not rehydrate into the next store, so
Save as Note was absent. `knowledge-retained-recovery-393.png` and
`gap-393.png` show that exact gap. Recovery has focused partial-failure
coverage but has **not been observed live**. Do not claim it has. Desktop
1440 after behavior also remains for the independent verifier.

Root received a corrected, **unrun** fixture handoff: seed the legacy draft
in page.add_init_script before the next store loads, after the old store's
pagehide write. The script now accepts repeated `--width=1440` /
`--width=393` and `--out=.tmp/deep-usability/create-independent` so the
independent verifier can preserve the successful phone observations. It
must see Recovered text before pressing Save as Note, then inspect the real
Note GET and Knowledge members GET. Fixture setup is not UI authoring proof.

### Final Workflow chrome dispatch repair

Root authorized the exact diagnosed remaining action after the first source
freeze. The prominent **Edit Workflow** action now calls the same
`openEditor(o.id)` route as the footer (`web/src/desk/components/Pullout.tsx:122`),
and its old Workbenches dispatch/imports are removed. No new editor or face
was added. The existing Pullout test now renders frame actions and verifies
the current Workflow id reaches openEditor without opening an application.
All five tests in that file were collected and passed under the helper and
lock. This is focused dispatch proof; the independent verifier owns the
fresh native chrome click and app/result evidence. Source is frozen again.

No owner observation, real model response, physical phone interaction,
external Send, microphone or terminal operation is claimed. Source is
frozen. HOLD FOR SHIP.

## Independent verification — Sol, 2026-10-14

The independent verifier completed both widths, **1440 first, then 393**,
with normal motion (`reduced_motion='no-preference'`). Command:
`python3 .tmp/deep-usability/locked.py create-independent .venv/bin/python
.tmp/deep-usability/create_after.py --width=1440 --width=393
--out=.tmp/deep-usability/create-independent`. Exit **0**, with
`CREATE AFTER COMPLETE`, both `width-complete` events, and no recorded
pageerror or gap. Log: `.tmp/deep-usability/create-independent.log`.
Actual API responses: `.tmp/deep-usability/create-independent/observations.json`.

This run rebuilt and used bundle **5139c83a6b641bb0** at both widths.
Root authorized the separate Workflow chrome dispatch repair while this run
was active; that later source change is not covered by this first bundle.
The core and recovery paths below were already frozen and passed unchanged.
Every shot in the following table was opened and inspected at both widths;
the filename suffix is `-1440.png` or `-393.png` under
`.tmp/deep-usability/create-independent/`.

| Actual UI job at both widths | Observed durable result | Inspected shot stems |
|---|---|---|
| New Note → title and body → Done | Note GET returns the exact typed body | `note-ui-saved` event in observations |
| New Knowledge → Add items → saved Note → Done | Member GET contains the original Note edge; no unsupported body editor | `knowledge-items` |
| Refused name PUT → Done → chrome Close/Back | Both close attempts retain the name field and editor; local receipt says Not saved · HTTP 503 | `knowledge-failed-close-kept` |
| Retry → Done → Close/Back → Search | Name GET returns Context with retry; original Note remains visible after actual return | `knowledge-retried`, `knowledge-return` |
| New Agent → name, role, instructions → immediate chrome Close/Back | Recipe GET retains all three values; Search returns the Agent | `agent-return` |
| New Workflow → AI prompt and Action items → Move up → Done | Graph GET stores LLM, Summarize, Action items in the new order and exact prompt; every measured control center hits its own Button | `workflow-editor`, `workflow-return` |
| API-seeded prompt-only Workflow → UI Edit → multiline Prompt → Done | Workflow GET returns Review design risks followed by `{input}` on its next line; graph remains empty | `workflow-prompt-editor` |
| Restored legacy Knowledge draft fixture → Save as Note | Recovered text renders first; Note GET returns its exact body; member GET has the original Note plus exactly one recovered Note edge | `knowledge-retained-recovery`, `knowledge-recovered-note` |

The recovery fixture uses a next-document init script to restore the old
workspace draft contract. It is **seeded restored legacy data**, not evidence
of UI body authoring or the owner's machine. The visible text was
`Recovered architecture material.` at both widths. Real recovered Note ids:
`note_650033e033ff` at 1440 and `note_da780f39effb` at 393. Each recorded
membership response contains two distinct Note refs: the previously added
Note and that one recovered Note. After success, the recovered section and
Save as Note action disappear and the second member appears. This observes
one successful recovery per width; partial-failure retry deduplication is
covered by the focused regression, not this browser run.

The second bounded run covered only the newly fixed Workflow title-bar
action. Command: `python3 .tmp/deep-usability/locked.py
create-chrome-independent .venv/bin/python
.tmp/deep-usability/create_chrome.py`. It rebuilt bundle
**0f8e8c6f99943972**, exited **0** with `CREATE CHROME COMPLETE`, and
completed 1440 then 393 with no pageerror or gap. Log:
`.tmp/deep-usability/create-chrome-independent.log`; actual results:
`.tmp/deep-usability/create-chrome-independent/observations.json`.

At each width, actual New Workflow → name → Done → Search → **Edit Workflow**
opened the current Workflow's name/step editor inside its own pullout. The
verifier changed the name and pressed Done; real GET retained it on the
same Workflow id (`workflow_9337cdbbc97a` at 1440,
`workflow_b58dada524ce` at 393). All six shots were inspected:
`workflow-chrome-before-{1440,393}.png`,
`workflow-chrome-editor-{1440,393}.png`, and
`workflow-chrome-saved-{1440,393}.png` in
`.tmp/deep-usability/create-chrome-independent/`.

Both runs used the machine lock, isolated temporary HOME/DB and glass
isolation switches. They ran local authoring and readback only. No owner
desk observation, physical phone, inference, workflow execution, external
Send, microphone, terminal or machine-state operation is claimed. The
temporary DBs were removed by the rig after their real API results were
recorded. The prior desktop/recovery/chrome proof gaps above are closed
within these limits. No product edits, dependency changes, staging or
commits were made by the independent verifier. HOLD FOR SHIP.
