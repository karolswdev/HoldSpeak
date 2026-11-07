# HS-E20 · Truthful Program execution contracts

**Status:** proposed outcome workstream; implementation not assigned. Parent: [ordered plan](../EXECUTION_INDEX.md#2-proposed-workstream-hierarchy).

## Why and outcome

A technical owner needs to know what a Program may do, which repository input it receives, what review currently permits, what it costs and when it has fulfilled an obligation. Those are related contracts under the existing Program lifecycle, not a reason to create another state machine.

Preserve existing Program/runner collaboration, authentic writer authority, owner control levels, evidence tied to the relevant state, exact checkpoint starts and separate delivery. A field, cached fact or successful final artifact does not establish every intermediate guarantee.

## Stories and dependency boundaries

| ID | Outcome | Gate before implementation |
| --- | --- | --- |
| **[HS-S21](../stories/HS-S21-action-program-binding.md)** | Explicitly bind newly added logical work to its source action while preserving existing IDs/gates/requirements | D14/G21: conditional add-only/append/guard branch accepts existing two-actor/no-PR limits; accepted whole-Program fulfillment remains separate |
| **[HS-S22](../stories/HS-S22-step-starting-input.md)** | Ordinary new work receives an explicit verified starting snapshot | D25/G22: fresh-remote branch versus fixed baseline, local-only compatibility and new checkpoint verification; preserve D17 binding and continuation |
| **[HS-S23](../stories/HS-S23-path-bound-guard.md)** | Program text classifies new path coverage consistently with its limited planning meaning | D23: owner-gate any newly admitted coverage, allow narrowing/equivalent coverage, keep direct-update/manual/diff scope unchanged |
| HS-S24 | Establish the Program spending promise before specifying enforcement | D20/G24: [contract task](../tasks/HS-T24-01-spending-contract.md) is detailed; implementation remains unexpanded until promise/scope, legacy authority and caller coverage are resolved |
| **[HS-S25](../stories/HS-S25-current-person-review.md)** | Person-gated merge uses explicit observed review evidence, not a historical latch | G-REVIEW/G25: coherent observation/head policy, unavailable evidence, current matching and bounded request/feedback semantics |

HS-S25 now has detailed policy, producer, admission and independent-proof tasks. Five existing production owners preserve historical approval while carrying current local evidence; no new polling, lifecycle or concurrency framework. Provider truth and request completion remain separately bounded.

HS-S22 now has detailed contract, implementation and independent-verification tasks. The proposed branch uses the existing local launch admission and ledger, with actual starting-tree proof before spawn. Fixed-baseline/local-only and checkpoint compatibility remain supervised choices.

HS-S21 now has detailed contract, implementation and independent-verification tasks. It adds no backend lifecycle or automatic propagation; the protective bulk-agent interaction is a pending compatibility choice, not an accepted removal.

These stories can proceed independently when their own gate is settled. Coordinate ownership of shared Program files and fixtures. HS-S23 is the first detailed exemplar because it is a bounded source-backed classifier correction; that recommendation does not approve its behavior or priority.

## HS-S24 spending contract gate

**Ready for contract resolution, not implementation.** The owner needs to know whether the Program dollar amount is a genuine ceiling and what work it covers. Current source stores a numeric amount, uses its presence to bypass one hosted-Pi question, and retains only a kind-level historical Go on. Other Program call paths do not all pass that gate. Creator-agents can write the amount, so neither the number nor history can be reinterpreted as owner-approved unlimited spending.

The language/journey documents also promise that a hosted planner stops at the amount. That promise conflicts with the limited inspected transport; changing it to permission-only is a product-contract change, not an innocuous label repair. No actual overrun or absence of independent provider/account limits has been established. [V24](../VALIDATION.md#v24-program-spending-contract-readiness) maps exact sources and missing proof.

D20/G24 has three unselected branches:

| Branch | Useful result | Required decision and limit |
| --- | --- | --- |
| Disclosure-only | Truthful unsupported/not-enforced presentation while preserving current runtime behavior | Explicitly accept shipping the disclosed limitation; retain/compatibly deprecate text/wire spellings. This does not fix the admission bypass or deliver a cap |
| Enforceable cap | Define and enforce a chosen scope, holding unsupported or uncertain calls according to the accepted policy | Specify per-call/step/planner/Program scope, review/retry/parallel inclusion, capability evidence, amount accounting, legacy handling and recovery. No generic engine is presumed |
| Explicit paid-engine permission | Represent deliberate owner permission separately from numeric accounting | New consent and migration semantics must be accepted. Old agent-writable values and kind-only Go on history are not that consent; no default unlimited continuation |

[HS-T24-01](../tasks/HS-T24-01-spending-contract.md) produces one accepted-or-pending contract record, current-behavior/caller matrices and exact proposed proof/ownership. It may finish with a precise unresolved choice. Do not author nominal implementation tasks that silently pick an amount scope or convert legacy data to permission. The initial four-suite characterization budget is source-verified but not executed; composed enforcement proof remains branch-specific.

No new story file, runtime subsystem, schema, capability API or migration is specified at this checkpoint. HS-S24 remains one story in this epic, with its single concrete contract task. Other accepted Program slices can progress independently.

## Prerequisites and proof

Each assigned slice starts with [HS-T00](../tasks/HS-T00-baseline.md), then its exact context, baseline and decision. No whole-epic code rewrite is authorized. Use the existing unit/integration rigs and producer/consumer paths. Never substitute synthetic facts for a claim about runtime enforcement or a fake PR merge for remote behavior.

HS-E20 is complete only for the explicitly accepted stories, each with its test matrix and independent review, followed by the selected build/delivery journey proof in HS-S91. Remaining stories must be reported as pending, not silently dropped. Preserve [I16/I18/I19/I20/I22/I24](../INVARIANTS.md).

## Rollback and stop

No epic-wide migration/cutover is assumed. Each story names its rollback boundary. Stop a slice for unsettled semantics, material baseline drift, authority expansion, real provider effects or a need to alter a different lifecycle. A local rollback must not mutate history or another worker's changes.
