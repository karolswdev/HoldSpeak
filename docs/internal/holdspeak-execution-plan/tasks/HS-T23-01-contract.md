# HS-T23-01 · Settle coverage semantics and characterize the baseline

**Status:** proposed assignment; no implementation authority from this file. Depends on [HS-T00](HS-T00-baseline.md). Unlocks HS-T23-02 only after G23 is explicitly resolved. Parent: [HS-S23](../stories/HS-S23-path-bound-guard.md).

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story sections [proposed contract](../stories/HS-S23-path-bound-guard.md#proposed-contract-and-g23-decision), [acceptance matrix](../stories/HS-S23-path-bound-guard.md#acceptance-matrix), and [exact existing context](../stories/HS-S23-path-bound-guard.md#exact-existing-context-and-editable-ownership); [V23](../VALIDATION.md#v23-first-slice-verification); invariants [I16/I18/I19/I20](../INVARIANTS.md). Current repository-mandated instructions still apply.

## Scope and why

Read source and named test code; run the unchanged focused baseline only when the assignment covers test execution. No production, test, fixture or documentation edits belong to this task. The proposed correction changes partial-removal behavior already asserted by tests, so the contract must not be silently chosen by an implementation agent.

## Steps

1. Verify `program_text._lowers_head` and `diff_program_text` produce `program.within`; trace `ProgramService.text_apply` → `_check_text_rows` → lower-bar/agent handling → `_apply_text`/`update`. Read only the relevant story anchors.
2. Confirm writer authority precisely: head writes reach `update`'s owner/creator-agent check; preview alone is not proof of write authority. `shape` checks its writer before inference. Direct `update(within=...)` remains outside text classification and outside this slice.
3. Compare night `_inside_within` and canon `_within` without changing either. Record the known `src` versus `src/` edge and other accepted unusual spellings. The parser retains order/duplicates/slashes; service validation does not turn dots, globs, backslashes or case into filesystem semantics.
4. Complete G23 with the owner/assigned design authority. The proposal treats any newly admitted coverage as lower-bar, including mixed replacement. Record whether narrowing/equivalent coverage should cease to be lower-bar; the proposed default is no owner gate. Keep consumer migration, direct-update/manual/diff guards and any new sandbox outside this slice. Explicitly settle the story's normalization edge cases. A proposed answer is not acceptance.
5. When test execution is authorized, run V23 collection and unchanged five-file baseline. Record source SHA, commands, collection count, exit status, logs and baseline failures. Do not alter tests to make the baseline green.
6. Map C01–C15 to proposed additions in existing `test_program_text.py`; map owner/agent/conflict/YOLO cases to the existing tests named in V23. Distinguish existing assertions from planned cases.

## Acceptance

Return one bounded contract report: accepted G23 text or exact unresolved choice; the coverage/normalization table; existing versus proposed assertions; authority/scope exclusions; baseline proof or explicit blocked status; and confirmed edit set for HS-T23-02. It must explain why `src/` → `docs/` needs owner handling even though it also removes coverage, and why empty → bounded is narrowing. All unexpected differences are reported.

No need to resolve D13, budget scope or other unrelated stories. If G23 remains pending, the baseline/report can be complete but HS-T23-02 remains blocked.

## Rollback and stops

No code/data rollback should be needed. Stop for a requested consumer/parser normalization change, universal path enforcement, direct-update authorization redesign, new API/schema or a failing/unsafe baseline. Request the smallest scope amendment; do not broaden the exemplar. Return the [completion report](../COMPLETION_REPORT_TEMPLATE.md), marked characterization/decision work, not implemented.
