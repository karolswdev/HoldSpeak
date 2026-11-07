# HS-T22-01 · Choose and characterize new-step input

**Decision/characterization task; no application implementation.** Depends on [HS-T00](HS-T00-baseline.md). Parent: [HS-S22](../stories/HS-S22-step-starting-input.md). An unresolved D25/G22 blocks dependent implementation, not useful source inspection.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [choices](../stories/HS-S22-step-starting-input.md#d25-and-g22-choices), [durable proof](../stories/HS-S22-step-starting-input.md#proposed-selection-and-durable-proof), [preservation](../stories/HS-S22-step-starting-input.md#preservation-and-failure-boundaries), [matrix](../stories/HS-S22-step-starting-input.md#acceptance-matrix); [V22](../VALIDATION.md#v22-step-starting-input-verification); current root/backend instructions. Do not read every Program research file.

## Work

1. Revalidate source selection, worktree classification, capacity, process admission/claim, actual worktree creation, spawn, first-message hold/send and runner recording. Mark exactly where each effect and durable write occurs. `agent.hand` and a Program decision receipt are not substitutes for enforced `process.spawn` admission.
2. Resolve D25 fresh remote snapshot versus deliberately fixed baseline. For branch A, settle local-only/missing-origin behavior, raw-object-fetch refusal, the new checkpoint moved-ref comparison, legacy continuation and new unknown-attempt handling. If local-only preservation requires a separate local policy, specify it before code; never silently fall back after a configured remote fails.
3. Freeze server-owned nested descriptor validation and bounded launch evidence fields. Bind Program/step/source/base and a credential-free configured/effective remote identity. Validation remains read-only. Revalidate after claim; a source ID alone does not freeze an externally mutable endpoint.
4. Freeze the pre-spawn sequence and first-message byte check, retaining request hash versus execution result as distinct facts. Ensure starting/failure/success ledger replacements preserve evidence. Agree how missing/mismatched persistence blocks new spawn without deleting the created tree.
5. Check the assigned Git version and supported flags only when tool execution is authorized. Choose a command sequence supported by official semantics and the current environment, with exact result checking and no mutable-ref fallback. Server refusal is a named failure, not permission to change server security settings.
6. Under the assigned test scope, establish the V22 baseline and freeze its [fixture composition map](../VALIDATION.md#fixture-composition-and-failure-visibility): one temporary DB/actual launch ledger, bare local remote, production hand/launch for B, checked observation of both Git seams, per-launch rider claims and in-test proof before scratch teardown. The existing local-only hand fixture is not already that combined rig. Record where FakeHand/FakeGitHub bypass the behavior; do not duplicate the selector in a fake. Use the explicit V22 subprocess switch/isolation recipe; a disabled direct Program runner or empty/failed collection is not baseline proof.

## Acceptance and stops

Return the accepted or unresolved G22 contract, exact effect/admission/persistence/identity map, local-only and checkpoint decisions, focused ownership and baseline evidence using the [completion report](../COMPLETION_REPORT_TEMPLATE.md). Fixed-baseline selection requires a different bounded implementation design. Stop for unsafe remote fixtures, unassigned execution, source drift, unavailable command capability, unclear first-message timing or a new cross-process/platform requirement. No data rollback is intended by this task; preserve all unrelated work.
