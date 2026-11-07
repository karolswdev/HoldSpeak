# HS-T52-02 · Move only the open-review lookup below orchestration

**Conditional implementation task for G52-B.** Requires accepted B/constructor compatibility, [HS-T00](HS-T00-baseline.md), [HS-T52-01](HS-T52-01-contract.md) and a scoped code/test assignment. Parent: [HS-S52](../stories/HS-S52-project-review-boundary.md). A retained-façade decision does not authorize this task.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); accepted caller/compatibility report; story [branch B](../stories/HS-S52-project-review-boundary.md#g52-alternatives-and-proposed-branch), [preservation](../stories/HS-S52-project-review-boundary.md#preserved-behavior-and-responsibilities), [matrix](../stories/HS-S52-project-review-boundary.md#acceptance-matrix); [V52](../VALIDATION.md#v52-project-review-boundary-verification), especially exact editable/read-only paths; current root/backend/document instructions.

## Owned scope

Five existing application files only: `holdspeak/db/delta.py`, `holdspeak/services/project_service.py`, `holdspeak/services/project_delta_service.py`, `holdspeak/runtime/room_composition.py`, `holdspeak/web_server.py`. Edit only the selector, capability constructor/gates, delegation and corresponding constructor calls/comments identified in V52. Delta command bodies and frozen serializers remain read-only even though they share an edited file.

Documentation: the existing review-composition section of `docs/internal/project-rooms/CONTRACTS-P0.md`. Test edits: V52's seven explicitly editable existing files. No new production/test file, frontend/wire fixture, schema, registry or query framework is planned. Extra necessary paths require a bounded amendment, not opportunistic cleanup.

## Implementation and proof

1. Add the proposed first-or-None selector beside the existing Delta repository review methods. Delegate to `list_reviews(project_id, status="open", limit=1)` rather than duplicating SQL or changing normalization/order/connections. Test project scoping, accepted-row exclusion, empty/newest-open behavior and unchanged failure propagation.
2. Convert Delta `_find_open_review` to a delegating compatibility wrapper. Keep all existing `open_review`, `get_delta`, frozen-by-ID and MCP resource callers/serializers intact. No collector is introduced on the read path and no private helper is deleted merely because the active Room no longer needs it.
3. Implement the accepted explicit Project availability flag and legacy keyword shim without storing/invoking the Delta instance. Update all three gates and only the one private query call. Preserve placement of room-fields read, open ID assignment, proposal query and catches so partial fault results remain identical.
4. Pass explicit capability only at the current hub and missing-Project composition constructors. Preserve bootstrap order, held objects, observer/callback identity, root/context installation and attachment timing. Do not backfill existing bare Project capability or force attachment when both instances are already held; those are separate behavior choices. Leave the documented bare MCP/resource builders and briefing fallback to their accepted existing/shim paths.
5. Update comments that falsely describe a mutual read dependency, not the whole runtime assembly. Retain the Delta→Project command dependency, constructor and attachment method. Do not manufacture another Project/Delta/repository instance.
6. Extend the existing focused tests for C52. Specifically test falsey legacy input, explicit precedence, all availability gates, no old helper call/retained object, exact capped count, targeted fault injection, resource empty/frozen shape and partial composition identity. Preserve actual observation/principal behavior; a full Room read is not globally write-free.
7. Verify atomic command preservation using the exact [Delta terminal-failure recipe](../VALIDATION.md#delta-terminal-failure-recipe). Retain the real held hub and explicitly install its no-op collector before producing the review. Add the six proposed answer/receipt scenarios with outer ID/kind/handle and caller-connection targeting, an exactly-one-hit assertion, rollback and same-operation recovery/replay. Preserve the legitimate nested item command; the old publication injector cannot be reused unchanged. Restore faults before retry, and do not alter command bodies to satisfy a mistaken stronger assertion.
8. Update the existing contract with a short current owner/capability/fault/proof map. Mark earlier P0 availability lists as historical where necessary to avoid contradicting the current review capability, without rewriting unrelated Room features. Keep typed contract, exact test links and transaction ownership discoverable.
9. Run the focused relevant subset after each change, then the final V52 union. Inspect actual code/test/doc diff and compare the same before/after ownership concern. No frontend/browser/fixture rewrite is needed for unchanged wire behavior.

## Acceptance and handoff

Project's active review read neither retains nor invokes the Delta orchestrator. The existing repository owns the selector; the compatibility wrapper and same command-service instance remain where current composition requires them. Every shape/fault/observation/transaction invariant has focused proof, or the task is incomplete. The maintained context map demonstrates the intended discovery improvement without claiming performance gains or a smaller full-service responsibility count.

Return the [completion report](../COMPLETION_REPORT_TEMPLATE.md) with actual diff ownership, test evidence, compatibility limits and before/after dependency map. Hold for [HS-T52-03](HS-T52-03-verification.md) and separate shipping authority.

## Rollback and stops

Reverse the cohesive query/gates/wiring/test/doc patch, retaining durable records and unrelated work. No data rollback or review acceptance reversal is needed. Stop for custom injection reliance, changed wire/fault/count policy, double observation, differing service/database objects, new transaction boundaries, failed baseline or a move that does not simplify responsibility.
