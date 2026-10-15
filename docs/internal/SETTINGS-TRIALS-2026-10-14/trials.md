# Trial face repair — source diagnosis and direction

Status: direction settled by root; implementation held for SHIP.
Base `a9f07971d`.

Tuesday job: choose a job, press Try it once, and see that row work and
return a truthful result. Constitution XI.4 makes that owner gesture the
approval. Tenets 1, 2 and 3 reject an extra confirmation for the same act;
tenets 4 and 5 require plain words and the existing library controls.

## Source cause

1. Every off-machine first press stops at `useRunsOn.ts:522-525` and
   creates pending consent. Busy starts only at `:528-529`; the first
   button cannot show work. `RunsOnCore.tsx:504-507` then draws a second
   primary button in the footer. This repeats the owner gesture.
2. At compact width the library does not render `SwitchJob.verb`
   (`desk/surface/Switchboard.tsx:558-574`). The face moves Try it to the
   footer (`RunsOnCore.tsx:508-511`), where it omits `loading`. The active
   row and its active control are apart.
3. Only Answers invokes the real task route (`useRunsOn.ts:534-557`). The
   other text jobs call the engine probe (`:559-573`), which checks a model
   list and cannot prove a job works. A cloud probe can check nothing.
4. Answers derives its status from `answer.ok` but displays any
   `answer.reasonCode` on failure (`:554-557`). The reported contradictory
   Broken / inference succeeded outcome needs the producer contract fix;
   the face must not turn a success reason into an error label.
5. The row names are static group summaries (`model.ts:28-35`), and the
   task list is only an HTML title (`RunsOnCore.tsx:256`, library
   `Switchboard.tsx:442,560`). A phone cannot inspect that title.

Line anchors describe the base. Recheck after the sibling settings and
probe lanes land.

## Bounded direction

- Compose an EgressChip beside the real row Try it before the press, for
  an off-machine destination only. Use the displayed destination's exact
  job, engine key, host/address and revision binding for that press.
- The first press immediately sets the job busy and calls the bounded
  task-probe contract. A stale displayed binding returns a same-row
  Changed destination result; it cannot silently authorize a new target.
- Preserve the backend boundary refusal. Show its plain reason in the
  row; do not turn refusal into another footer confirmation.
- Compose the row action from the library Button and EgressChip. At board
  width use `job.verb`; at list width use the existing `job.result` well
  for action plus result, because that slot already renders in the open
  job. This stays inside the face lane. The footer keeps Undo and Settings.
- Busy is visible from the press: library loading, Trying on the row,
  no second request while active. Speech keeps Stop while listening and
  shows Transcribing after Stop; it must not invite a new capture then.
- Each text trial runs a small synthetic input through its named job's
  actual model route, returns that sample output in the row, and identifies
  the tested task. One sample does not certify all tasks in a group.
- A real successful trial says Completed with the tested task, served model and positive measured
  latency. Failure says Not tried with the producer's plain reason.
  Missing probe support says No trial; it must not manufacture Ready.
- Keep results on their job and bind them to the tested destination. If
  routing changes in flight, show the actual tested destination and do not
  describe the new assignment as tried.

Row words settled by root:

| Group | Outcome label |
|---|---|
| speech_recognition | Speech to text |
| writing_dictation | Dictation clean-up |
| thoughts_notes | Answers and notes |
| meetings | Meeting summaries |
| agents_tools | Custom tasks |
| background | Background work |
| default | Default engine |

Default engine has no Try it: there is no global task to exercise without
changing route planning. Inherited jobs say Uses default engine.

Use one selected-row FoldGadget Details for the task names and routing
detail. Keep server capability ids out of product text. Do not build a new
router, schema, framework, or consent wizard.

## Native direction canvas

`canvas/` imports the production DeskWindowFrame, SurfaceSwitchboard,
Button, EgressChip and FoldGadget plus their existing CSS. Its sample
route and result are explicitly canvas data, with no hub, microphone,
model, or external request. Shots are direction evidence, not proof of a
production trial. Query `state=idle|busy|done|failed` selects the row state.

Root inspected the busy desktop and completed phone directions before build.
The six direction shots are under `.tmp/settings-trials/canvas-shots/`,
outside the committed documentation tree.
Canvas limitation: Vite refused the symlinked warm dependency font files;
those direction PNGs use fallback fonts. The production build's packaged
fonts are covered by the separate production walk.

## Focused validation budget

Existing files only: `web/src/features/runson/__tests__/runsOn.test.tsx`
and `stateWord.test.ts` if its mapper changes. Model cases currently live
inside runsOn.test.tsx; there is no separate model test file.

Cover local and remote first press; pre-press destination; one bounded
request; actual sample output; same-row loading in board and list; named
server refusal; stale binding; routing change while in flight; speech
Listen → Stop → Transcribing → result. Preserve assignment, Undo,
summary-route and download cases already in the file. Run through
`.tmp/settings-trials/locked.py`, vitest 4 with maxWorkers=2. No broader
suite in this lane.

## Implementation and focused proof

The row owns its initial press, pre-press destination chips, library Button
loading, progress and terminal result. List layout composes into the existing
result well. Footer trial actions are parked; assignment receipts and Undo
remain. Speech keeps Stop while listening and shows Transcribing while its
real transcript request is pending. Details stays in the selected row and
does not trigger row deselection when opened.

The closed text map is `speech.rewrite`, `ask.answer`,
`meeting.deferred_analysis`, `recipe.run`, `background.rails_summary` in row
order. The request carries the displayed profile chain as expectedProfileIds.
The frontend compares the displayed job, key, host/address and profile
revision before dispatch. The server refuses any planned profile outside
that set. Same-profile server retarget races remain outside that ID guard;
root explicitly retained the existing wire instead of adding target fields.

Focused proof: `.tmp/settings-trials/trial-unit-final3.log` — 47 tests passed
in 5.48 s, existing runsOn.test.tsx only, isolated HOME and machine test lock.
The full list of 47 test names is `.tmp/settings-trials/trial-list-final.log`.
Wire replay in the existing file
copies the real isolated ASGI task-probe response recorded by the probe lane:
adopted kernel and controlled provider leaf, with no physical inference claim.
`git diff --check` on this lane's five product/test files was clean.
The final source freeze also derives destination and result chip scope from
the same canonical enginePlace helper as the off-machine decision.

Production UI → real HTTP → adopted-kernel verification is owned by the probe
lane. Its screenshots and terminal DB observations are required separately;
these unit and canvas checks do not claim owner-desk or physical-model proof.
