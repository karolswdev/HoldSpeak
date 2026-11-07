# HS-T32-04 · Verify recovery without repeating external effects

**Conditional independent review/test task.** Requires final task02/03 reports, accepted G32 and an assigned role/environment. Parent: [HS-S32](../stories/HS-S32-delivery-recovery.md). No production/test edits or shipping authority.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); accepted choices and actual final diff; story [scope](../stories/HS-S32-delivery-recovery.md#outcome-and-explicit-scope), [matrix](../stories/HS-S32-delivery-recovery.md#acceptance-matrix) and [rollback](../stories/HS-S32-delivery-recovery.md#rollback-and-stops); [V32](../VALIDATION.md#v32-delivery-recovery-verification); [I10/I16/I18/I21/I24](../INVARIANTS.md).

## Review and proof

1. Verify exact accepted scope: known-PR continuation and handled failure, not crash-safe dispatch. Only the explicitly accepted owner-Merge request receipt precedes that remote command. No general pre-effect claim, scheduler, table, source-registration requirement or generic recovery engine is added.
2. Trace acknowledged identity from create response/prepared commit to failure, Check, displayed/frozen receipt and merge. No reconstruction from title/branch/current repository; old incomplete rows remain readable and ineligible under G32. Preserve phase facts and evidence confidentiality.
3. Check Retry derives from actual stage/remote-attempt evidence and relevant prior history. Assert absence of DW/worktree/commit/push/create on every known/uncertain-remote recovery path, not merely the final success string.
4. Confirm owner admission and the existing process-local lock scope. Compare displayed expected receipt before effects; frozen pages must not swap it for current state. SDK/CLI/MCP forwarding and legacy/direct-channel refusal must match the accepted matrix. Do not call this a durable cross-process exclusion guarantee.
5. Verify committed request receipt before every owner Merge, including fresh Secure; append failure must run zero merge commands. Reconstruct state after marker-before-command and after failed outcome append: Check/Skip remains, the marker survives observations and no second merge is offered. This is a narrow durable-receipt proof, not a process-kill or multi-process test. Verify the provider-side conditional-head argument, exact recorded target, bounded reads and post-merge observation. A queued/open or unavailable observation is not Delivered. No auto/admin/force/delete/cancel or polling behavior appears silently. A fake that always merges successfully cannot prove these branches.
6. Inspect fake/fixture safety before execution. Future integration runs real local Git/DW with a bare origin; all gh branches must be injected and fail closed. Isolated HOME is not itself an egress firewall. Block unsupported nonlocal commands, owner repositories, credentials and unexpected agent/provider/device effects.
7. Collect/run the exact focused tests and owned fixture producer, then app/browser proof after the last edit. Empty/skipped collection, hand-built fixture data, unread screenshots or obsolete mocked choices are incomplete proof. Retain command logs, counts and status.
8. Inspect actual UI/brief wording for Check versus Merge versus confirmation, legacy/unknown blocks and Program Done independent of delivery. Repeated Check may add truthful observations; it must not create new work. For the accepted G32 distinction, verify Skip after queued/unconfirmed outcome executes zero provider commands, removes the held turn while Program stays Done, retains visible acknowledged identity where available and unresolved uncertainty and does not claim “not delivered” or cancelled. Preserve the supported known no-effect Skip case. Check both consequence and settled-brief/window output within the existing V32 budget; Skip creates no automatic recheck.
9. The integration owner runs the current quick check and reviews relevant images and diff. Failures return to the implementing task; rerun final-state proof after fixes. No live GitHub action is required or authorized by this plan.

## Conditional joined workflow

When both slices and the joint proof are assigned, require the T25-04 report and independently run the [review-to-delivery gate](../VALIDATION.md#review-to-delivery-integration-gate) after final edits. Check real raw-review producers, request-versus-terminal step state, Secure closure, distinct final PR identity, current delivery binding and known-PR command counts in the same Program. Neither two independently green suites nor manually stamped Done proves the crossing. The existing ten-target V32 union and V25's union remain required; there is no additional test target or browser/capture scope. Keep the two rollback populations separate. If not jointly assigned, explicitly report the crossing as outside this verification, not passed or a new standalone blocker.

## Exit and stop

Return the [completion report](../COMPLETION_REPORT_TEMPLATE.md): accepted subset, full C32 trace, fake versus real-local execution limits, actual result evidence, compatibility restrictions, residual initial-automatic/preparation-Retry receipt windows and cohesive rollback. Confirm an older server cannot be resumed unguarded against new unconfirmed markers. Hold for separate shipping permission.

Stop for unbound authority/identity, unsafe subprocess fallback, claimed success from unknown observation, unexpected remote write during Check, scope drift or incomplete final proof. Do not weaken expectations, rewrite history, reset another lane or perform a real remote effect to make the test pass.
