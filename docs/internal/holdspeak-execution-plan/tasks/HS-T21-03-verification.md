# HS-T21-03 · Verify the action to Program journey

**Independent review/test task, not shipping authority.** Requires accepted G21-A, final [HS-T21-02](HS-T21-02-binding.md) report/diff and a named environment/role. Parent: [HS-S21](../stories/HS-S21-action-program-binding.md). No source/test/fixture edits belong to this task.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); accepted contract and final diff; story [matrix](../stories/HS-S21-action-program-binding.md#acceptance-matrix), [limits](../stories/HS-S21-action-program-binding.md#completion-boundaries-that-must-stay-truthful), [rollback](../stories/HS-S21-action-program-binding.md#tasks-and-rollback); [V21](../VALIDATION.md#v21-action-program-binding-verification). Read only named producer/consumer paths and current repository-mandated instructions.

## Proof

1. Check that this is explicit add-only binding under existing completion semantics. No Program-level fallback, first/every-step propagation, origin reassignment, new schema/engine, hidden backend permission or global unique-origin invariant may appear.
2. Trace the actual Add payload and real stored result. Existing step IDs, gate values and step-local requirement links must survive; a mocked returned Program cannot prove custody. Match captured fixtures to their real producer and assertions, not shape alone.
3. Inspect both Add entry points and protected bulk-agent callback. Confirm action-backed and explicit action-origin cases, no re-POST after uncertainty, guard on unavailable fresh read, and usable per-step PATCH. Separate continuation/idle callbacks must not be disabled as collateral. The legacy replacement API remains outside this UI-only guarantee.
4. Trace binding through text, split/overturn and race grouping. Multiple physical rows can be one logical race; existing duplicate logical origins are not silently cleaned up. No exact-one claim may exceed the UI request scope.
5. Review actual action/linked-record/event results and two-actor characterization. Verify no-PR Done, observer versus runner order, mixed controls, already-done/dismissed/reopened cases, and action/marker/checkpoint failure windows. A Program checkpoint is not a canonical causal completion receipt, and neither is current action state. Do not turn preserved limitations into passing proof of a stronger policy.
6. Run final V21 collection/tests after the last edit in isolated state; inspect counts/skips/logs. Rig Git/worktrees are local and real; fake GitHub/agents must not fall back to live execution. Browser Program mutations must be intercepted and fail closed. Keep fixture-write flags off.
7. Inspect actual 1440/393/narrow-in-wide screenshots, keyboard/Escape/focus and target hits. Verify the new well and guard interaction, not only a generic sweep. Verify the new binding line is read-only recorded identity, with existing source controls unchanged; an openRef mock, Needs window or focus event is not exact-row/current-status proof. Binding issues no extra Start, acceptance, completion or Send command; an appended step in an already-running Program remains subject to its existing scheduler. Missing/skipped required cases remain blocked proof.
8. Have the assigned integration owner run the current final gate. Report actual stages and comparison base; exit zero with no affected tests is not the required journey proof.

## Exit and stops

Return C21 outcomes, exact final diff, real run/screens evidence, accepted scope/known limits and rollback using the [completion report](../COMPLETION_REPORT_TEMPLATE.md). Hold for separately authorized shipping. Request the smallest correction if identity/gates/requirements are lost, guards overreach, UI claims completion without evidence, fixtures execute real effects, or implementation quietly consolidates authority. Do not repair unrelated code in this review lane.
