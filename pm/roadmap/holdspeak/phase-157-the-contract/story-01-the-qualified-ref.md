# HS-157-01 - The qualified ref: one grammar, aliases, the fence

- **Project:** holdspeak
- **Phase:** 157
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** HS-157-02
- **Owner:** unassigned

## Problem

Qualified refs (`meeting:...`, `decision:...`, `person:...`) are the
spine of Project Rooms — every relationship, evidence link, and Delta
grouping rides them (SRS_DOMAIN_DRIVER §4.2). Today the grammar is
feature-local string splitting, and it has already drifted:
`thread_service.py:311` matches `person:` while
`people_service.py:784,799` emits `people:`. The handover names this
hazard first: pick one grammar and fence it, or Delta will silently
miss links. REF-001..004 are the law here.

## Scope

- **In:** a central qualified-ref parser/formatter module
  (`holdspeak/refs.py` or `holdspeak/services/refs.py` — follow
  repo convention): a registered closed set of citizen types, parse +
  format + round-trip, alias resolution (REF-003 settled as one
  canonical type + backward-compatible aliases), unknown types
  representable and inspectable but not mutable through an
  unregistered adapter (REF-004). A fence test that keeps NEWLY
  TOUCHED Project code off feature-local splitting (REF-001 scopes to
  newly touched code; existing emitters stay untouched in P0).
  The canonical-vs-alias ruling recorded in the P0 contract doc.
- **Out:** rewriting existing emitters/consumers (thread_service,
  people_service stay as they are — the parser accepts both);
  any schema or API change.

## Acceptance criteria

- [ ] One canonical people-type is ruled and recorded, with the other form accepted as a parse alias; parsing either yields the same canonical ref; formatting emits only the canonical form (REF-003).
- [ ] Every registered ref round-trips parse→format→parse without loss; property/round-trip tests prove it (REF-002).
- [ ] An unknown ref type parses into an inspectable representation and is refused mutation through the registry (REF-004).
- [ ] A fence test exists that fails when newly touched Project Rooms code splits refs with feature-local string operations instead of the central module (REF-001) — scoped so existing legacy call sites don't light it up.
- [ ] No runtime behavior change anywhere: existing suites green, zero branch-new.

## Test plan

- **Unit:** `tests/unit/test_project_refs.py` (grammar, aliases, round-trip, unknown types, registry refusal) + the fence test.
- **Regression:** full-suite name-diff vs main at the close (05).

## Notes / open questions

- Recommendation going in: canonical `person:` (singular matches `meeting:`, `decision:`), alias `people:` — but verify against what the Desk relationship routes and web consumers actually parse before ruling; the ruling itself is the deliverable, recorded in the contract doc.
