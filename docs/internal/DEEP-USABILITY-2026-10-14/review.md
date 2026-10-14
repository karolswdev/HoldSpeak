# Independent implementation review — 2026-10-14

Built/frozen worktree review against `eb9a3266e`. This is the requested
independent Sol implementation review, **not Muad'Dib's check or Astra's
postmerge review**. HOLD; no staging or commit. Only this record was edited.
No tests, builds, new capture runs, or owner-machine actions were performed.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **P1 — accepted Schedule creation can erase a newer draft.**
   `web/src/desk/components/ScheduleCreateWindow.tsx:118` awaits the submitted
   operation, then `:128`–`:134` unconditionally forget title, time, mode,
   cron and duration and close the form. The fields remain editable while
   waiting (`:157`, `:167`, `:177`, `:188`, `:198`), and Cancel/chrome Close
   remain available (`:150`, `:218`). Exact source reproduction: submit A;
   before its promise resolves, change the cron/duration/title to B, or close,
   reopen and enter B; resolve A successfully. A's completion erases B from
   the shared `schedule/new/*` keys. The new retention implementation extends
   this existing acknowledgement problem to the newly retained fields. This
   is a deterministic source trace, **not an executed browser reproduction**.
   The three new schedule tests cover ordinary refusal/acceptance/reopen,
   not editing or remounting during the pending write
   (`web/src/desk/components/__tests__/scheduleCreate.test.tsx:21`, `:33`, `:47`).
   Fails Tenets 3 and 7: a changed operation can disappear before the owner
   schedules it. People and Workbench already acknowledge submitted snapshots
   at `PeopleCore.tsx:1281` and `WorkbenchWindow.tsx:1405`.

CONDITIONS:

- Acknowledge only the Schedule snapshot that actually succeeded. Retain
  newer fields and keep their current form open; account for Close/reopen
  while the first operation is pending. A focused deferred-request regression
  should prove that B survives A's success. One bounded recheck is sufficient.
- Keep release claims bounded to the captures available. Knowledge retained
  text recovery and Create desktop implementation shots remain unverified
  below; a component green is not a live recovery or desktop usability pass.

MISSED:

1. The Schedule acknowledgement is the remaining confirmed custody defect
   in the touched creation flow. It does not use the submitted-snapshot
   discipline present in the other repaired composers.
2. The phone Create walk reached a missing **Save as Note** locator after its
   retained-draft fixture. `create-after-retry/knowledge-retained-recovery-393.png`
   visibly has no recovered-text section, and `create-after-retry.log` ends
   with that timeout. This is a capture/fixture gap pending diagnosis, not
   evidence that the product lost existing retained text. Source and the
   partial-failure component test support retaining `recovery_note_id`, but
   cannot establish the missing live recovery outcome.
3. Existing Workbench item-body editing remains a separate custody tail:
   `operate.md` explicitly records the component timer/unmount limit. The
   repaired inlet's durable body/source proof must not be generalized to
   rapid Close or refusal in that existing item-body editor.

TUESDAY: The inspected Person context, refused Room correction, Workbench
Add/recovery, and phone Knowledge/Workflow editors now expose readable work
and useful actions; Schedule's pending-write custody still needs repair.

UNKNOWN:

- No browser reproduction of finding 1 was run by this reviewer.
- Knowledge retained-text recovery after real Note creation plus failed
  membership/retry remains unobserved in the current live capture. The
  component test at `editorRepair.test.tsx:131` proves one Note POST and
  retained recovery ID across the controlled partial failure.
- The latest Create implementation capture currently contains only 393px
  shots. Desktop live editor/recovery usability is not established by this
  review. The absent recovery control is not counted as a product blocker.
- Ask 1440 graph walk completed with `VERDICT: pass terminal=settled`; its
  `after.png` visibly contains both checked objects. Ask 393, inference,
  private-context egress, physical devices, real agent/model execution,
  microphone capture and schedule firing were not observed.
- Integrated quick-check/release/deployment results were not available to
  this bounded reviewer and are the root's responsibility.

Evidence inspected:

- Tracked implementation diff and new `editorRepair`, `groundingSelection`,
  and `scheduleCreate` test source. The editor hook retains failed/sending/
  pending fields, serializes writes and publishes its current acknowledgement;
  the frame guard executes before departure animation. The normal-motion
  regression is `web/src/desk/__tests__/windows.test.tsx:63`.
- Existing captured work/refusal/read-failure observations and readable shots:
  `.tmp/deep-usability/work-after-shots/context-read-{1440,393}.png`,
  `context-refused-393.png`, `room-refused-kept-393.png`, and
  `room-accepted-read-failed-1440.png`. The final work capture log records no
  gaps at either width; `work-tests-ship.log` records 5 files/75 tests passed.
- `.tmp/deep-usability/operate-failure-case-shots/393-add-refused.png`,
  `1440-accepted-under-list-failure.png`, and `393-list-retry-updated.png`.
  The accepted item remains readable while the failed list retains its prior
  card; local Retry updates it to `1 PENDING`. The global aggregate failure
  still has its own Retry. `operate-failure-case.log` records `GAPS []`.
- `.tmp/deep-usability/create-after-retry/knowledge-failed-close-kept-393.png`,
  `knowledge-return-393.png`, `knowledge-retained-recovery-393.png`,
  `workflow-editor-393.png`, and `workflow-prompt-editor-393.png`.
  Knowledge refusal keeps its editable name and membership; the Workflow
  prompt and step actions fit. `create-focused.log` records 5 files/40 tests
  passed, and `create-frame-focused.log` records 3 files/35 tests passed;
  these are separate runs, not 75 unique tests.
- `.tmp/deep-usability/shared-read-green.log`: 2 files/16 tests passed.
  Source at `web/src/desk/api.ts:744` classifies failures by collection;
  `store/dataSlice.ts:196` retains only the classified transient buckets.
  Named cases include mixed first-ranked 503/later 403, 401/403 clearing,
  authoritative empty200 and existing write/rollback fences. No confirmed
  authorization-retention regression was found in this correction.
- `.tmp/deep-usability/graph-ask-1440.log` and the corresponding
  `.tmp/graph-walk/deep-usability/ask-1440/20261014T225028Z-case.deep.ask.sources-astra-1440/after.png`.

One final review completed. One recheck remains available for the identified
fix and newly completed evidence; no broad second review is requested.

## Final bounded recheck — independent Sol, 2026-10-14

This is the one recheck of finding 1 and the completed evidence, performed
by an independent Sol verifier. It is **not Muad'Dib's check or Astra's
postmerge review**. Schedule review used source, test source, collection
output and the existing focused run log only; no further tests, builds or
Schedule capture executions were requested or run. No product edits,
staging, commits or owner-machine operations were made. HOLD FOR SHIP.

VERDICT: RATIFY

FINDINGS:

1. **Original P1 Schedule draft-custody finding is resolved.**
   `web/src/desk/components/ScheduleCreateWindow.tsx:118` captures the submitted
   draft map and chooser identity before awaiting creation. At `:133`, the
   accepted operation compares all five current draft fields (title, time,
   mode, cron and duration) with its submitted values. At `:138`, a changed
   draft or a different current chooser returns before the forget calls;
   at `:144`, only the original chooser can be closed. The draft snapshot is
   stable because `store/compositorSlice.ts:248` replaces the draft map;
   reopening creates a fresh chooser at
   `store/scheduledRecordingSlice.ts:190`. Thus A cannot erase or close the
   visible B in either reviewed edit-during-pending or Close/reopen case.
   This meets the original Tenets 3 and 7 condition.
2. The three deferred-request regressions exercise edited B, reopened B,
   and an unchanged reopened form at
   `components/__tests__/scheduleCreate.test.tsx:29`, `:51`, and `:71`.
   They assert the current chooser, retained draft map and rendered values
   after A resolves; the first also checks A's actual submitted payload.
   `.tmp/deep-usability/operate-schedule-review-collect.log` lists all six
   tests. `.tmp/deep-usability/operate-schedule-review-tests.log` records
   **1 file / 6 passed**, Vitest 4.1.9, after acquiring the machine lock.
   This is source and focused component evidence, not a browser Schedule
   race reproduction or a schedule firing observation.
3. The earlier Create desktop/recovery capture conditions are closed by
   this verifier's completed real local UI/API walks at 1440 and 393.
   `create.md` records all inspected shots and exact results under
   `.tmp/deep-usability/create-independent/` (bundle 5139c83a6b641bb0).
   Restored legacy draft text visibly renders before Save as Note; real
   Note GET returns the exact text and member GET contains the original
   Note plus one recovered edge. Recovery is explicitly fixture-seeded.
   The separate Workflow chrome correction passed both widths on fresh
   bundle 0f8e8c6f99943972, with same-id edit and durable GET evidence under
   `.tmp/deep-usability/create-chrome-independent/`.

CONDITIONS: None remaining from this bounded implementation review. Release
and deployment checks remain the root's responsibility.

MISSED: No further defect found within the requested Schedule-fix recheck.
The existing Workbench item-body custody limit remains recorded in
`operate.md`; this verdict does not extend the repaired inlet proof to it.

TUESDAY: The reviewed local creation flows retain changed work through
refusal and pending acceptance; the owner can return to the saved result at
both inspected widths.

UNKNOWN:

- The Schedule race is proved by the inspected source and deferred component
  regressions, not a new browser reproduction; schedule firing is unobserved.
- Live partial-failure recovery (Note creation succeeds, membership fails,
  then retry) remains unobserved; the component regression proves retained
  recovery-id reuse. The new browser runs prove one successful recovery per
  width and distinct membership refs, not an audit of orphan Notes.
- Ask 393 is now observed: `.tmp/deep-usability/graph-ask-393.log` records
  `VERDICT: pass terminal=settled`, and inspected
  `.tmp/graph-walk/deep-usability/ask-393/20261014T225543Z-case.deep.ask.sources-astra-393/after.png`
  visibly contains both checked Audit Notes. The rig reports `engine=none`;
  inference and private-context egress remain unobserved.
- Physical devices, real agent/model execution, microphone, terminal,
  external Send and owner-desk observation remain outside these local rigs.
- Integrated quick-check/release/deployment evidence is owned by the root.

The permitted review and one fix recheck are complete. The prior verdict and
proof-gap statements above remain the historical first review and are
superseded only to the extent stated here. HOLD FOR SHIP.
