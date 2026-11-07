# HS-T23-03 · Verify the classifier change and close the slice

**Status:** conditional verification task, not shipping authority. Depends on [HS-T23-02](HS-T23-02-implementation.md) and its final diff/report. Parent: [HS-S23](../stories/HS-S23-path-bound-guard.md). Reviewer and integration roles must follow current repository instructions; the same actor is not assumed to own every step.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [contract/matrix](../stories/HS-S23-path-bound-guard.md#proposed-contract-and-g23-decision), [observed acceptance](../stories/HS-S23-path-bound-guard.md#required-observed-behavior-after-an-authorized-implementation), [owned context](../stories/HS-S23-path-bound-guard.md#exact-existing-context-and-editable-ownership); [V23](../VALIDATION.md#v23-first-slice-verification); [integrated gate](../VALIDATION.md#integrated-gate); invariants [I16/I18/I19/I20](../INVARIANTS.md); prior task reports.

## Scope

Review/read/test only. No source edits belong to this task. Findings return to HS-T23-02 with explicit paths and repro. Do not add a lint/tool dependency, expand test budgets or run live providers to make the report look complete.

## Procedure

1. Independently inspect the final diff against accepted G23. Check mixed replacement, empty-before/after, parent/child and equivalent spellings. Verify ordinary list representation and `program.within` identity remain, and the helper has no filesystem/provider side effects.
2. Inspect the real `text_apply`/update and shaper flows. Confirm tests prove actual principal behavior, row decisions and stored state rather than only private helper output. Verify owner-invoked generated text still requires a separate lower-bar action at YOLO. Confirm direct update and unrelated guard fields are unchanged.
3. Recheck actual final SHA/diff identity and run V23 collection/final five-file suite under assigned test authority. Retain logs/exit status. If later edits occur, invalidate the earlier proof and rerun the affected budget.
4. The assigned integration/ship owner runs the current repository quick check using the comparison base established in HS-T00 and the V23 `QUICK_TESTS` list. It owns HOME/locks; do not wrap it. Inspect actual stages and Desk sweep shots, not just zero exit. A no-change early exit or no tests collected is not proof. If no integration role/environment is assigned, report focused verification complete and integration pending rather than inventing a pass.
5. Confirm no new schema/wire/import/API contracts, unsafe fixture access or changes outside owned paths. Recheck working-tree ownership. Do not stage/commit from this verification task.
6. Produce the final story report with the matrix result, actual commands/logs, source-vs-fixture-vs-live limits, reviewer disposition, remaining decisions and rollback boundary. State explicitly whether integrated proof is complete and that shipping was not performed.

## Acceptance and definition of done

HS-S23 is complete only after accepted G23, all required focused cases, independent review and applicable integrated gates are proven against the final change. A worker's focused pass may be ready for integration, but is not a whole-story or product-wide pass. No live sandbox guarantee, all-API owner gate or broader journey completion follows.

Use [Completion report](../COMPLETION_REPORT_TEMPLATE.md). Unlocked work is the next explicitly selected story, not automatic execution of the whole plan.

## Rollback and stops

If verification finds a regression, stop advancement and return it to the implementation owner. Use the story's bounded reverse-patch plan only under authorization; preserve stored state and other work. Required failures/skips, unknown effects, absent role authority or a changed comparison base must remain visible. No automatic provider retry, merge, deployment or owner-data action belongs here.
