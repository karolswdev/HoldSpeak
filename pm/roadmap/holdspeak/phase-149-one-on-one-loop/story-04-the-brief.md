# HS-149-04 — The brief (Prep lens + PREP on the rail)

- **Project:** holdspeak
- **Phase:** 149
- **Status:** ready
- **Depends on:** HS-149-02
- **Unblocks:** HS-149-06
- **Owner:** unassigned

## Problem

The next 1:1 should open prepared. Today nothing aggregates a
person's open commitments, agenda backlog, and the last linked
meetings' outcomes (census: every input exists EXCEPT the chain
now built in 02).

## Scope

### In (settled-design D5, D6)

- `people_service.one_on_one_brief(relationship_id)`: read-time,
  in-memory — open commitments + agenda backlog + grounding count
  (encrypted) ⊕ the last N linked meetings via the uid chain with
  their OPEN action items BY REFERENCE and any decisions minted
  from them (plaintext). NEVER persisted; never enters
  cadence_*/action_items/caches/exports (the 138 law verbatim in a
  test).
- The **Prep lens** on the relationship (PeopleCore) rendering the
  brief in house grammar; the LINKED rail row gains an in-world
  **PREP** affordance beside Record this, opening the person's
  Prep lens — the Tuesday pair.
- MCP `people.one_on_one.brief` (families/people.py, the
  grounding-bundle pattern).
- The meeting origin line (147 D7) extends with the resolved
  person when the sidecar is open.

### Out

- Any write path from brief data; unifying the commitment triad
  (D6 — a pin proves action_items stay untouched by brief reads);
  Monday Brief sections (next arc).

## Acceptance criteria

1. A populated brief on glass (through the 01 seam): commitments +
   agenda + last-linked-meeting action items, each traceable to
   its source store.
2. PREP on the linked rail row opens the person's Prep lens in one
   tap; Record this unaffected beside it.
3. The never-persist pin: brief generation writes ZERO rows
   anywhere (DB write-count spy on both stores).
4. Locked sidecar → the brief refuses honestly (L2 vocabulary),
   never renders half-true.

## Test plan

Brief service unit tests (aggregation, guards, the write-count
spy, the 138-law pin), PeopleCore Prep lens + rail PREP component
tests, MCP tool test, live shots both widths.
