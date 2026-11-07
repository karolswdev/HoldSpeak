# HS-T24-01 · Establish the Program spending contract

**Contract and source-characterization task only; no implementation brief is unlocked yet.** Parent: HS-S24 in [HS-E20](../epics/HS-E20-program-contracts.md#hs-s24-spending-contract-gate). Requires assigned [HS-T00](HS-T00-baseline.md). Source pin `80b641fa41c7352280cfa52e933acf6dbe8d3857`. Detailed planning is authorized; application/test execution requires its own named scope/environment.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); [HS-S24 gate](../epics/HS-E20-program-contracts.md#hs-s24-spending-contract-gate); D20 in [Decisions](../DECISIONS.md); [V24 current behavior and proof](../VALIDATION.md#v24-program-spending-contract-readiness); [I16/I18/I19/I21/I22](../INVARIANTS.md). Inspect only the named interfaces, callers and proving tests, not the whole research library.

## Outcome

Return one reviewable spending-contract record that an implementation planner can use without guessing what the dollar amount means. It must say which behavior is accepted, which callers/engines it covers, how legacy values and owner decisions are treated, what evidence will prove it, and what remains blocked. A complete record may still say the owner's decision is pending; that is not authorization to invent an answer or claim a spending guarantee.

## Work

1. Revalidate current source and root/scoped instructions. Trace all V24 admission/call paths and actual amount/cost transport. Keep explicit code facts, internal design claims, external capability unknowns and tests-read versus tests-run separate. Do not conclude all provider/account controls are absent or claim actual overspending.
2. Produce a compact current-behavior matrix for absent/null, empty-string clearing, booleans, zero, positive, negative, nonnumeric and non-finite values across create, direct update and text apply. For non-finite values distinguish validation, persistence, serialization and dispatch: source float parsing alone proves none of the later outcomes. Record owner versus creator-agent access and text-specific lower-bar handling; a stored numeric value is not evidence of owner consent.
3. Produce a caller-coverage matrix for ordinary builder admission; continuation/retry/handoff; builder rehand/reviewer dispatch; shaping; draft Plan/Split; automatic dispatch-time sizing/split planning; round synthesis/refinement; night planning; and any additional currently supported Program-paid caller found. For each, name source owner, engine resolution, amount transport, cost evidence, existing refusal/permission and uncertainty. For automatic splitting, distinguish the planning call from later owner Apply/Skip: V24 names the invocation before that proposal and before the later builder money question, with existing hold guards preserved. Record the effective planner route and include/exclude/unknown scope separately from the builder profile or control level. Do not call `_spend_core` the universal gate or conflate token/context limits with dollars.
4. Ask for only the decisions that change the next branch: the desired promise (disclosure-only, enforceable cap, or explicit paid-engine permission) and its scope. Record all subordinate semantics in the contract for review: value meanings, unsupported/unknown engine handling, owner/creator rights, legacy data, historical Go on, engine/model/amount changes, retries/reviews/parallel calls, in-flight changes and failure/recovery. Never upgrade old values or a kind-only clearance into a new approval.
5. Reconcile public docs/MCP descriptions, canonical Program text, parser/shaper/planner grammar and UI words with the selected promise. Retain exact old spellings/wire keys as compatibility evidence; do not rename/deprecate them or rewrite saved/historical text during this task. Internal modeled journeys promising a planner stops at the amount are design claims to resolve, not proof of implementation or fresh user authorization.
6. Use V24's four existing suites only as the initial characterization budget if application-test execution is explicitly assigned. Otherwise return their source assertions and unrun status. Passing current presence/synthetic-cost/text tests does not prove enforcement. Do not add tests, start a paid engine, query a live provider or regenerate fixtures to make this record seem complete.
7. Define the missing composed proof for the chosen branch. Bind each proposed case to its real producer/consumer and an exact existing test home or clearly proposed new path, expected outcome, isolation and required authority. Do not create a huge all-suite mandate. Preserve the independent Automation/CLI capability-aware per-invocation path; it is not an aggregate Program guarantee.
8. Propose the smallest implementation file/test ownership and task dependency map only after the contract/caller coverage is sufficient. If a path or engine capability is unknown, name it and stop that dependent branch. No generic budget service, new ledger, global permission layer or schema migration is justified merely by similarly named fields.

## Required contract record

Use the existing [completion report](../COMPLETION_REPORT_TEMPLATE.md) structure, with these explicit sections:

- **Decision:** actual owner evidence and accepted branch/scope, or exact pending questions. Silence, repository prose and this package are not acceptance.
- **Meaning:** amount/value matrix; per-call, per-step, planner-only or Program-wide scope; included planning/review/retries/parallel work; what unsupported/unknown means.
- **Authority and compatibility:** owner versus creator writes; old null/zero/positive/invalid values; old Go on records; engine/amount/control changes; parser/API/history compatibility. No manufactured consent.
- **Call coverage:** named real callers, effective engine mechanisms, unresolved capabilities, observable evidence and which claim each mechanism actually supports. For dispatch-time splitting, record the order of planner invocation, owner proposal and builder admission; a later Apply/Skip is not pre-call money permission.
- **Proof and ownership:** precise proposed paths/cases, current baseline or unrun status, missing runtime proof, isolation, rollback and independent-review gate. A source claim about an adapter flag is not proof of provider/account enforcement.
- **Readiness:** ready to expand only the accepted branch, or blocked on named decision/evidence. Other independent Program slices may continue; this does not pause the entire product plan.

Return the contract record in the task completion response. Do not create another parallel backlog or standalone research report as the deliverable. Keep D20 and the existing epic/index as the authoritative plan references; any decision update must carry actual user evidence. No later implementation task is implicitly assigned by completing this record.

## Acceptance and stops

The task is complete when the record is source-backed, independently checked and leaves no hidden semantic choice in its claimed ready scope. Pending choices are permissible output, but they block dependent implementation. The matrix must explicitly include the planner promise, direct creator-agent writer, zero/legacy clearance, reviewer/handoff paths, automatic sizing/split invocation before its returned proposal and the later builder money check, and independent CLI support.

Stop for missing owner choice, material source drift, unsupported capability claims, required real paid/provider activity, uncertain old-data meaning or unassigned application execution. Continue permitted source/decision work independently. This task changes no application or durable state, so rollback is correction of the contract record, not data migration, permission revocation, replay, deletion or repository reset. Shipping remains separate.
