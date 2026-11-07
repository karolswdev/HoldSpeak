# HS-T42-02 · Preserve canonical creation and filing outcomes

**Conditional implementation task.** Requires [HS-T00](HS-T00-baseline.md), accepted creation/recovery subset of G42 and [HS-T42-01](HS-T42-01-contract.md), plus an assigned code lane. Parent: [HS-S42](../stories/HS-S42-decision-filing.md). No implementation authority follows from this file.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [G42](../stories/HS-S42-decision-filing.md#g42-local-decisions-before-implementation), [outcomes](../stories/HS-S42-decision-filing.md#target-interaction-and-outcome-custody), [source map](../stories/HS-S42-decision-filing.md#exact-source-map-and-ownership); [V42](../VALIDATION.md#v42-meeting-decision-filing-verification); [I13/I16/I18/I21/I23](../INVARIANTS.md); accepted contract and baseline reports.

## Owned scope

Existing production: `web/src/desk/decide.ts`, limited to the meeting creation chain and its result/filing phases. Cohesive private helpers/types stay in that file; names are proposed. Keep the separate global producer in `store/dataSlice.ts` read-only. Backend production, source stores, aliases and permission rules are read-only.

Tests/fixtures: the explicitly declared canonical producer/helper cases and owned wire paths in V42. New filenames there are proposed, not existing passing coverage. Coordinate shared tests with task03/04; no broad recording or harness rewrite.

## Steps

1. Revalidate the single production caller relationship and accepted compatibility decision. Separate the canonical POST/decode phase from the project membership phase, without duplicating either producer. Keep meeting provenance and the chosen project's existing source/tag semantics.
2. Validate the canonical/source envelope and nonempty string identities before declaring acknowledgement. A malformed 2xx, missing/wrong-type IDs, HTTP failure or transport loss after attempting canonical creation cannot authorize POST `/api/decisions` or a second canonical POST. Do not invent a capability detector. Preserve legacy endpoints and the separate global producer unchanged.
3. Return or retain an explicit created result as soon as both identities are acknowledged, before attempting membership. Its receipt includes the actual canonical and source IDs, chosen project if any, and separate filing outcome. Do not hide this identity in a generic thrown error that invites new creation.
4. For an explicit unfiled decision, omit the membership action and state that accurately. For a chosen project, use the existing admitted member PUT against `decision_record:<id>`. Distinguish accepted write, refusal, unknown response and later refresh failure. Known creation remains known in every branch.
5. Expose a narrowly scoped same-ID filing/reconciliation operation to the meeting caller. A valid current read of the exact canonical ref/project and live member row confirms member filing. A different relationship kind is an existing edge, not absence or completed member recovery; do not automatically overwrite it. A valid complete read with no matching live edge can support a new explicit same-ID press; malformed/unknown/unavailable reads remain unresolved. Preserve G42's accepted role-change policy and its concurrency limit. Do not create automatically or treat title equality as identity. Preserve applicable current revision/command-replay inputs rather than inventing a new idempotency protocol.
6. Add actual canonical route/source/membership tests and helper request-order tests described in V42. Test missing/malformed envelopes, a membership failure after a valid creation response, lost member response, current non-member edge after an earlier member receipt, malformed/wrong-target relationship envelopes, and unrelated global/legacy preservation. Do not let a test harness return `{}` for canonical creation and silently exercise the legacy branch.
7. Run this task's focused producer/helper budget. Report intermediate UI work still needed in task03; this is not a separately shippable feature. No backend state machine, transaction migration or source-history edit belongs to the task.

## Acceptance

The meeting helper cannot create twice as a fallback after an attempted canonical POST. It retains acknowledged identities across later filing/read failures and uses them for subsequent membership work. Actual producer assertions verify canonical and retained source identities/provenance separately. Explicit unfiled behavior matches G42. Existing legacy APIs/global producer are untouched.

Return the [completion report](../COMPLETION_REPORT_TEMPLATE.md) with exact response/identity boundaries, tests run, proposed-versus-recorded fixtures and unresolved UI proof. Task03 must consume the result before the full creation slice is ready.

## Rollback and stops

Reverse only the scoped helper/test diff; never delete created decisions or rewrite provenance to undo code. Restoring the old helper restores its uncertain-outcome/fallback limitation. Stop for unresolved compatibility, required backend change, unsafe producer setup, missing acknowledged IDs, changed authorization or extra public consumers outside the accepted scope. Hold for review/SHIP; no staging, commit, push or deploy.
