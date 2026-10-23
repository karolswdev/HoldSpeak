# source_context

Job: choose a project, object or source context before an operation  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `source_context`  
Evidence class: active React/TypeScript source and representative assertions; no execution or owner acceptance.

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The job starts at a Desk selection, front object window, Project Room,
selected Note passage, About picker, or in-app drop. It must show the chosen
source, distinguish whole-Desk scope, submit one immutable context snapshot,
show provenance, allow add/remove, recover from stale or missing sources and
failed requests, then return to the source or continue the saved thread. Q5/Q6
cover the happy path: object/project Ask, named chips, whole-Desk shortcut,
and selected-text handoff. The partial inventory brief still omits
cross-window selection, refresh, unsupported resources, and return behavior.

FINDINGS:

1. **P0 — global selection can change context.** Evidence:
   `web/src/desk/components/AskPanel.tsx:331-340` derives About from global
   `selectedIds`; `web/src/desk/store/deskSlice.ts:159-168` opens Ask without
   a snapshot, while `web/src/desk/components/AskPanel.tsx:274-291` resets
   local Ask state without resetting selection. Close then calls
   `clearSelection` (`web/src/desk/components/AskPanel.tsx:266-271`), which
   clears the Desk selection (`web/src/desk/store/deskSlice.ts:153-158`).
   Cost: another window's object can be read, or the selection needed on
   return can disappear. Tenets 3 and 7 fail. Correction: use AskContext/store to
   carry an explicit `wholeDesk`/`selection`/`about` handoff, snapshot it at
   opening, and release only Ask-owned context; preserve the opener's
   selection.

2. **P1 — source support is not bounded.** Evidence:
   `web/src/desk/askAbout.ts:23-28` correctly withholds the object verb when
   `Repository` has no `ask` capability (`web/src/lib/primitives.ts:554-563`),
   but the selected-object Ask bar at
   `web/src/desk/components/AskPanel.tsx:1027-1042` opens for any selected id
   and `web/src/desk/ask.ts:82-101` resolves every item kind without that
   capability check, silently dropping only unknown ids. Cost: a repository
   selected on the Desk can enter Ask through a different path, while a file
   in RepoWindow has no stated context result. Tenets 3, 6 (Workbench) and 7
   fail. Correction: state the supported Ask boundary, align AskBar with the
   existing canAsk guard, and return typed unsupported/missing state rather
   than sending or discarding a resource silently.

3. **P1 — recovery and return are not audited.** Evidence:
   `web/src/desk/components/AskPanel.tsx:353-361` drops a passage when global
   selection/items change; `web/src/desk/components/AskPanel.tsx:457-503`
   fences a run but has no source revision contract; the transient handoff in
   `web/src/desk/ask.ts:26-43` has no durable reopen path. Cost: refresh or
   provider failure can detach an answer from its source. Tenets 3 and 7
   fail. Correction: preserve a captured quote and source ref when the user
   already selected text; for a ref-only source, name stale/missing state,
   and cover Recent/thread reopen plus Back to note.

## Convergence

`ask_whole_desk` is the first consumer of scoped snapshots, async fencing,
operation outcomes and source receipts. `threads` owns durable About refs and
reopen; `notes_editor` owns passage handoff and Add to note;
`projects_room` supplies project identity at
`web/src/features/project-room/ProjectRoomCore.tsx:1594-1600`; `memory`
supplies explicit whole-Desk questions. `automation_build` already reuses
`AboutPicker` at `web/src/desk/components/automation/AboutEditor.tsx:17-18,140-155`,
but its repository folder refs (`web/src/desk/components/automation/AboutEditor.tsx:70-118`)
remain operation-specific. Share
refs, chips and command composition, not a universal picker: Ask grounding,
file/work-folder authority and explorer selection have different providers
and side effects.

## User experience

The simple flow is promising: one in-world Ask window, readable About chips,
source links, and a Note return action. The available Note 393 capture at
`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/note-393.png`
shows Ask about this in the footer, but no Ask capture was inspected, so this
is not visual acceptance. Global-selection ambiguity and absent stale-source words
will erode trust. Keep the one-press path; make scope stable instead of
adding a wizard.

CONDITIONS: Add scoped handoff/close semantics, explicitly bound supported
resources, and source refresh/failure/cancellation/Recent-return scenarios
using existing Ask/thread contracts. Do not add a runtime or approval system.

MISSED:

1. Select a Note, switch windows, then submit Ask.
2. Refresh/remove a selected passage before submission.
3. Reopen a thread, remove About, and follow up without the old ref.
4. Try repository/file context and receive a typed refusal.

TUESDAY: The happy path is fast, but context is not yet reliably owned by the window that started the job.

## Acceptance challenges

1. Select `note:n-mira`, open Ask, select a project elsewhere, and submit;
   the payload must retain the captured note or visibly show replacement.
2. Start Project Room Ask, close the Room, switch windows; the answer retains
   project refs and the Room remains reopenable.
3. Select Note text, refresh/remove the Note, then submit; preserve the
   captured quote and ref, or (for ref-only context) show named missing-source
   state, never whole-Desk scope.
4. Attempt repository context; withhold Ask or return typed unsupported-source
   state. Reopen a saved thread, remove About, and verify its next payload
   omits the removed ref.

UNKNOWN: No tests, live Desk/provider/API/native actions, or owner-state writes
were made. `tests/unit/test_desk_ask.py` and
`web/src/desk/__tests__/ask.app.test.tsx` prove payload/thread examples, not
cross-window isolation, refresh recovery, accessibility, performance, egress,
native behavior, or owner delight.
