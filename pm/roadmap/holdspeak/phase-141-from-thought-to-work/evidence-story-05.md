# Evidence — HS-141-05 Context you can see

**Result:** done; final technical and owner-glass counsel both **RATIFY**.

## Shipped contract

- Power-user and YOLO first does not mean hidden autonomy. Under the shipped
  empty policy a new Thought has no attachments. Only an explicit per-Thought
  choice or owner-configured future set attaches context, and neither attachment
  nor starting refinement silently starts another model turn.
- The in-body `AI context  None  Attach` row opens one compact interaction. Pinned
  **Everyday context** is first and attaches in one selection; Recent and search
  stay compact, while the full Note catalog is behind Browse.
- The browser and MCP send qualified refs, request identity, and expected
  revisions only. One shared application service resolves and freezes the human-
  visible container plus exact versioned Note leaves; copied bodies are rejected.
- Attachment revisions are immutable and cryptographically bound into v2 Thought
  commands and sync. A dispatched turn keeps its frozen bytes even when a source
  changes; detach or Update context supersedes the live parent so late output
  cannot become a review.
- Missing or changed context refuses by human name before model dispatch and
  synthesis acceptance. **Update context** or **Remove it** is explicit; no
  current content is silently substituted for the frozen version.
- HTTP and the fourteen `thought.*` MCP tools share the same owner authority,
  idempotency, cursors, receipts, projections, and stale behavior. Context list,
  attach, detach, and transport `refresh_context` accept refs/cursors only and do
  not start a model turn.

## Integrated HS-141-05A extension — default AI context

Story 05 now also includes the owner-configured future default without adding a
seventh completed Phase 141 story. The phase remains **6/9**.

- The shipped policy is empty. The existing **Attach context** picker shows the
  complete **On this Thought** and **For new Thoughts** sets at both widths.
  **Use these by default** replaces the complete future set; it is absent when
  the current set is empty.
- The policy is owner-only and hub-local. It applies inside the atomic birth
  transaction only to Thoughts created or adopted later on that hub. It does
  not sync, backfill, mutate an existing Thought, or invoke a provider, Ask,
  kernel operation, proposal, or tool.
- **Remove from this Thought** changes only that Thought.
  **Stop using by default** clears the complete future set and leaves every
  existing Thought unchanged. Server projections and scoped receipts, not
  browser inference, drive both lists and every **Default** marker.
- Each local create/adopt durably records `empty`, `applied`, or `not_applied`
  policy provenance. If any configured ref is missing, stale, overlapping,
  unsupported, or over cap, birth succeeds at attachment zero, the whole set is
  skipped, and the receipt names the exact affected selection/leaf. Canonical
  independent failure attribution plus its digest prevents receipt replay from
  swapping another valid default or unrelated leaf.
- HTTP adds `GET` and `PUT /api/thoughts/default-context`; HTTP create/adopt now
  use the same application boundary. MCP adds exactly four tools:
  `thought.create`, `thought.adopt_note`, `thought.get_default_context`, and
  `thought.replace_default_context`. All use closed schemas and the same owner
  authority, idempotency, CAS, projections, fail-open receipts, and refs-only
  context boundary.

The extension's ruled and implemented contract is
[`assets/hs-141-05a-default-ai-context-design.md`](./assets/hs-141-05a-default-ai-context-design.md).
Technical counsel and owner-glass counsel both returned **RATIFY** after the
full policy/action/application ledger, independent failure attribution,
recursive transport types, both-width scope hierarchy, and zero-dispatch glass
were proven.

The ruled implementation contract is
[`assets/hs-141-05-design.md`](./assets/hs-141-05-design.md). It records the
canonical hash grammar and caps, untrusted-context delimiter, concurrency/sync/
privacy/fault matrix, stale primary-action hierarchy, HTTP/MCP parity, and the
executable `ORCHID CLOCK` walk. Two adversarial technical audits initially
blocked on sync metadata binding, frozen-ledger validation, v1/v2 history, and
the Ask boundary; all blockers were fixed before the final RATIFY. The cold owner
review separately ratified the compact interaction and both-width hierarchy.

## Owner glass

The [eight-shot record](./assets/story-05/README.md) contains four states at
1440×900 and 393×900:

1. [picker 1440](./assets/story-05/hs-141-05-picker-1440.png) and
   [picker 393](./assets/story-05/hs-141-05-picker-393.png);
2. [attached 1440](./assets/story-05/hs-141-05-attached-1440.png) and
   [attached 393](./assets/story-05/hs-141-05-attached-393.png);
3. [used 1440](./assets/story-05/hs-141-05-used-1440.png) and
   [used 393](./assets/story-05/hs-141-05-used-393.png); and
4. [stale 1440](./assets/story-05/hs-141-05-stale-1440.png) and
   [stale 393](./assets/story-05/hs-141-05-stale-393.png).

The companion [HS-141-05A eight-shot record](./assets/story-05a/README.md)
captures at 1440×900 and 393×900: the complete current/future sets before
promotion, a newly born Thought with visible default attachments, the named
stale explanation with **Update context** as the sole primary followed by
successful repair, and whole-set not-applied with the unavailable last-known
default plus **Stop using by default**.

The deterministic provider returned the expected question only when it observed
the exact canonical material containing the owner-edited seed phrase. The walk
proved `Used Everyday context · 5 notes`, exact formatted blocks, Answer without
an automatic continuation, idle stale zero-send, explicit Update context,
post-hook immutable bytes, explicit Reject, detach-during-flight suppression,
restart persistence, MCP parity, refs-only browser payloads, and no overflow or
console/page errors.

## Verification

Final runs on the assembled tree:

```text
uv run pytest -q \
  tests/unit/test_refinement_context_service.py \
  tests/unit/test_refinement_thought_service.py \
  tests/unit/test_refinement_coordinator.py \
  tests/integration/test_refinement_coordinator_kernel.py \
  tests/unit/test_mcp_thoughts.py \
  tests/unit/test_web_routes_thoughts.py \
  tests/unit/test_desk_seed.py \
  tests/unit/test_grounding_shared.py \
  tests/unit/test_primitive_contract.py \
  tests/unit/test_reconcile.py \
  tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot

133 passed in 19.24s

uv run pytest -q \
  tests/unit/test_refinement_context_service.py \
  tests/unit/test_refinement_coordinator.py \
  tests/unit/test_ask_no_retarget.py \
  tests/unit/test_placement_provenance.py \
  tests/unit/test_hs13103_remaining_obligations.py

70 passed in 9.85s

uv run pytest -q tests/e2e/test_hs14105_context_glass.py --timeout=120
2 passed in 23.55s
```

The first suite includes schema reconciliation/canonical-snapshot guards and the
second includes the final Ask-boundary type/byte/cap refusal. The two focused web
test files passed 27 tests and the production web build completed. The generated
API-surface guard, MCP catalogue guards, doc-drift guard, UAT ledger guard, and
`git diff --check` also pass at close. GitHub Actions was not watched or used as
a gate.

HS-141-05A focused close ledger:

```text
uv run pytest -q \
  tests/unit/test_refinement_default_context.py \
  tests/unit/test_refinement_context_service.py \
  tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot

55 passed

uv run pytest -q \
  tests/unit/test_refinement_default_context.py \
  tests/unit/test_refinement_context_service.py \
  tests/unit/test_refinement_thought_service.py \
  tests/unit/test_refinement_coordinator.py \
  tests/unit/test_mcp_thoughts.py \
  tests/unit/test_web_routes_thoughts.py \
  tests/unit/test_web_routes_sync.py \
  tests/unit/test_web_routes_sync_primitives.py \
  tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot

138 passed

uv run pytest -q tests/e2e/test_hs14105a_default_context_glass.py --timeout=120

2 passed
```

The backend ledger covers canonical rev0 and contiguous policy history, action
linkage, mandatory application proof, restart/replay, both empty↔nonempty race
orders, exact selection/leaf fail-open attribution, malformed nested HTTP/MCP
parity, v2 manifests, sync exclusion, privacy, and zero model calls. The glass
uses fresh HOME/database instances and real HTTP/application/browser paths; its
no-dispatch engine remains at zero calls.

Two repository-wide legacy guards are recorded, not misreported as green. The
product-language guard's remaining findings are the pre-existing `Context` in
Recipe Editor and `ACTIONS` in Model Settings; HS-141-05 adds no offender. The
global PMO checker reports an unrelated Phase 101 evidence file whose story is
not marked done. HS-141-05 does not weaken either guard or rewrite those
out-of-scope product/roadmap records.

## Honest boundary

The walkthrough provider was deterministic, not a claimed production model.
Its prompt input, kernel dispatch, receipt, review, mutations, restart, and MCP
commands were real product paths. HS-141-05 attaches Notes and the seeded
Everyday Knowledge collection only. It creates no Decision, Jira issue, calendar
event, or other outcome; HS-141-07 and HS-141-08 own typed outcomes and the real
GitHub actuator proof.
