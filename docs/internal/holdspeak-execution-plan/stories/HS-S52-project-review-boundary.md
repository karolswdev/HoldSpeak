# HS-S52 · Give open-review reads an explicit lower owner

**Conditional structural plan, not implementation authority.** Epic: [HS-E50](../epics/HS-E50-ownership-boundaries.md). D06/G52 remains pending. Source pin: `80b641fa41c7352280cfa52e933acf6dbe8d3857`. No application/test execution occurred.

## Outcome and evidence

A Room-read change should not require understanding the Delta command orchestrator merely to select an existing open review. Remove that inappropriate dependency only if the smaller boundary preserves the real product contract and makes ownership easier to find.

Current `ProjectService._read_room_review` calls `ProjectDeltaService._find_open_review`, then counts its own returned open-proposal rows. Delta also needs the same ProjectService for transactional item creation. This is genuine bidirectional object collaboration, not proof of a runtime failure. The [measured responsibility evidence](../STRUCTURAL-REVIEW.md#measured-appendix-projectservice-responsibility-cohesion) does not justify extracting all Room reads, saved Ask or every helper into new services.

The shared selector is small: `db.project_observations.list_reviews(project_id, status="open", limit=1)`, first row or None. The persistence query belongs to `DeltaRepository` in `holdspeak/db/delta.py`; first-row selection currently lives in Delta's private helper. The proposed change belongs in that existing repository, not a new query service/module/registry. Room's availability, projection and fault policy remain in ProjectService; frozen review serialization and commands remain in Delta.

## G52 alternatives and proposed branch

**A. Retain the collaboration with an explicit contract.** Keep the service façade and declare the query/capability contract, its side effects and proof. A reviewed public/internal query façade may replace the private cross-service call if appropriate. This can be the final design; it clarifies ownership but does not remove the retained service-instance edge.

**B. Use the existing repository as the shared query owner.** The following detailed implementation tasks describe this conditional branch:

1. Add a narrowly named selector to `DeltaRepository` (proposed name `get_open_review`), delegating to the same `list_reviews` parameters and returning its first row or None. Keep ordering, normalization, row shape and connection/error semantics unchanged. Do not add a tie-break, cache, new transaction, join or true-count query.
2. Let Room use that repository selector without calling or retaining the Delta service instance. Retain Delta's `_find_open_review` as a small delegating compatibility wrapper; its `open_review`, `get_delta` and the MCP resource continue to use their current serializers and error boundaries.
3. Make review availability explicit in ProjectService rather than equating capability with a retained command-service pointer. Proposed constructor flag name is `review_available`; exact spelling is not an existing API. Proposed default is `None`, inferring legacy availability as below; an explicit True/False takes precedence. Default/bare construction remains unavailable, not an automatic DB capability probe.
4. Preserve the existing `delta_service=` constructor keyword as a bounded compatibility input if its supported callers need it. Derive legacy availability using `is not None`, not truthiness; do not retain or invoke that object in the new branch. An explicit boolean wins when both inputs are supplied; `None` means infer from the legacy input. This preserves call shape/availability only, not arbitrary injected query behavior. The inspected production path uses the same DB; a different-DB or overridden-query contract requires separate treatment. If supported custom query injection is an actual contract, this shim is insufficient: retain branch A or revise the design before implementation.
5. At active runtime construction, pass explicit availability only where the existing Delta capability is composed. Retain current assembly order and the same held Project instance wherever the existing composition attaches Delta for commands. Do not repair partial-context wiring as a side effect. The late `attach_project_service` setter may stay for compatibility/assembly; update its now-stale mutual-read rationale rather than inventing a second composition root or deleting it by grep.

Selection requires an owner decision and a supported-caller census. If no meaningful ownership/onboarding benefit is demonstrated, retain A rather than force B. No behavior fix, screen change, new feature or broad package relocation is included.

## Preserved behavior and responsibilities

- **Unavailable differs from empty.** Bare ProjectService currently produces an absent review section and no Delta needs-you row. An available capability with no open review returns a real section with zero pending and no open ID. Preserve all three availability gates, not just the outer Room field.
- **Fault outcomes are not uniform.** The review helper's later `get_project_room_fields` call executes outside its inner catch; failure reaches the existing outer degraded-section wrapper (or is caught/omitted by needs-you). Room also reads those fields earlier for orientation; failure there can fail the whole Room. Target the later call in a section-fault test, not a globally failing repository method. A selector failure is caught and leaves zero/no ID. A proposal-read failure occurs after the open ID is set and leaves that ID with zero. Preserve these current states for this structural change; a new degraded/unknown policy is a separate supervised behavior decision.
- **Returned rows are not automatically a total.** Pending count is the length of the current proposal query result, with its existing default limit of 200. Do not silently change it into a database total. Preserve ordering and proposal lifecycle filter.
- **Public consumers keep their own shape.** Delta's `get_delta` empty state includes source coverage; the MCP resource's empty shape omits it. Replacing the resource with `get_delta` would change its contract. Frozen window sorting/serialization is not part of this extraction.
- **Admission and effects stay put.** The repository selector grants no new principal authority. Project/Delta public entry checks remain; observer/decorator behavior stays at the existing public service boundary. Read means query purpose, not a promise that a full Room call cannot record observation/cache effects.
- **Commands stay atomic.** Delta `decide_proposal` acceptance/edit-accept can call `ProjectService.create_item_in_transaction` on the same connection. Preserve revision/idempotency/item/change/ledger/kernel completion coordination. `accept_review` has a separate review/cursor/supersession transaction. Do not merge or rewrite them to make the diagram simpler.
- **No adjacent cleanup.** Saved Ask, cursor secrets, mark-room-read wire naming, general Room composition, receipt-retention vocabulary, authority/private-source scope and current frontend loading/layout are unchanged. No arbitrary line cap or new small-file target applies.

## Acceptance matrix

All new assertions are proposed until implemented/run.

| ID | Required proof |
| --- | --- |
| C52-01 | Shared selector returns the same first open-review row/None with current project normalization, ordering and exception propagation; it performs no domain writes |
| C52-02 | Bare/no-capability Room stays absent and contributes no Delta needs-you row; explicit enabled/no-review is real zero/None |
| C52-03 | Legacy non-None input, including a falsey object, preserves availability under the accepted same-DB contract without retaining/calling the old service; None infers and explicit True/False wins, with custom query compatibility explicitly bounded |
| C52-04 | Open/accepted review shapes, last accepted timestamp, proposal lifecycle/default limit and singular/plural needs-you wording remain unchanged |
| C52-05 | Outer field-read failure versus selector failure versus proposal-read failure preserve their exact degraded/zero/partial-ID outcomes |
| C52-06 | Delta one-open sequential behavior and frozen readback/ordering remain; no new atomic concurrency or snapshot guarantee is claimed |
| C52-07 | MCP resource keeps its exact empty and frozen shapes through the retained wrapper; no collector starts on a read |
| C52-08 | Active runtime/operation targets retain held instances. Existing bare Project is not backfilled when a missing Delta is built; when both instances are held, attachment is not newly forced. No duplicate observer/service instance is introduced |
| C52-09 | `decide_proposal` create-item success/rollback/replay preserves one revision and the caller connection; `accept_review` separately preserves cursor, ledger and supersession semantics |
| C52-10 | [Outer-terminal fault proof](../VALIDATION.md#delta-terminal-failure-recipe) hits the matching Delta command/connection exactly once, then proves rollback and same-operation recovery/replay. Nested item-command failure and publication-only tests do not substitute; successful create-item acceptance legitimately records both inner and outer command answers |
| C52-11 | Active Room review reads no longer call or retain the Delta orchestrator; retained compatibility symbols are not falsely treated as dead code |
| C52-12 | A short maintained contract identifies query owner, capability gates, fault shapes, transaction boundaries and exact proof. A fresh reviewer can locate them without reading unrelated saved Ask/whole-service history |

## Tasks and rollback

[HS-T00](../tasks/HS-T00-baseline.md) → [HS-T52-01](../tasks/HS-T52-01-contract.md) → accepted G52-B → [HS-T52-02](../tasks/HS-T52-02-boundary.md) → [HS-T52-03](../tasks/HS-T52-03-verification.md). Use [V52](../VALIDATION.md#v52-project-review-boundary-verification). Each task names editable paths separately from read-only context.

No schema/data/wire migration is intended. Reverse the cohesive repository/caller/capability/wiring patch while retaining durable reviews, proposals and command history. Do not undo accepted items, revise receipts or reset an owner's checkout. Stop for supported injection incompatibility, changed authority/fault/count semantics, a new transaction, duplicate observation/instances or a required wider split. Retaining A is a legitimate result; an interface plan is not permission to implement or ship.
