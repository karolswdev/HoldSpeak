# HS-180-03 — The Constitution audit

- **Project:** holdspeak
- **Phase:** 180
- **Status:** backlog
- **Depends on:** Phase 179 merged
- **Unblocks:** HS-180-09
- **Owner:** unassigned

## Problem

The Constitution (docs/internal/CONSTITUTION.md) is the supreme canon.
Every phase since 95 cites its articles, but no comprehensive audit
has verified every clause against the shipped product. Phase 180 is
the audit: every article, every clause, with evidence.

## Scope

- In:
  - Audit every clause of every article (I through XI):
    - **Article I** (The Desk is the operating surface): 4 clauses.
    - **Article II** (Everything is a primitive): 3 clauses.
    - **Article III** (Local first, honest egress): 3 clauses.
    - **Article IV** (Voice is a first-class input): 3 clauses.
    - **Article V** (Consent is the spine of action): 5 clauses.
    - **Article VI** (Honest by construction): 3 clauses.
    - **Article VII** (The interface serves, it does not speak): 3
      clauses.
    - **Article VIII** (Native-grade craft): 3 clauses.
    - **Article IX** (Proof over claim): 4 clauses.
    - **Article X** (Amendment): 3 clauses.
    - **Article XI** (The Kernel): 5 clauses.
  - For each clause: cite the evidence (a test, a screenshot, a
    receipt, a walk result, a code reference) that the shipped product
    satisfies it.
  - For each clause that is NOT satisfied: name the gap honestly, cite
    the drift, and file a backlog item (Article X.3 -- drift is named,
    never ignored).
  - The audit is filed as a structured document in the phase folder.
- Out:
  - Fixing gaps (180 proves, it does not build).
  - Amending the Constitution (Article X.1 -- only the owner amends).

## Acceptance criteria

- [ ] Every clause of Articles I through XI is audited with evidence
      (Article IX.3 -- evidence rides with the change).
- [ ] Satisfied clauses cite their evidence (file:line, test name,
      screenshot, receipt).
- [ ] Unsatisfied clauses name the gap and cite the drift
      (Article X.3).
- [ ] Unsatisfied clauses have backlog items filed.
- [ ] The audit document is filed in the phase folder.

## Test plan

- Unit: n/a.
- Integration: n/a.
- Manual: the audit is a manual review with evidence collection.

## Notes / open questions

- The audit is expected to find gaps. A gap in Article III (privacy)
  or Article V (consent) is a release-candidate blocker; gaps in other
  articles are filed and documented but do not block the release.
- The audit may reference evidence from walk stories across phases
  169-179 (each walk's verbatim verdict is evidence for Article IX).
