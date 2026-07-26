# HS-105-06 - Docs — the bench at the entry points

- **Project:** holdspeak
- **Phase:** 105
- **Status:** done
- **Depends on:** HS-105-01, HS-105-02, HS-105-03, HS-105-04, HS-105-05
- **Unblocks:** HS-105-07
- **Owner:** unassigned

## The bar

The Phase-64 rule (docs touch ENTRY points), the Phase-76 rule
(every written claim true on the shipping tree) — and one more,
borrowed from the reference itself: Commodore shipped the Amiga
User Interface Style Guide as a BOOK. The discipline was written
law, which is why third parties could extend the system without
degrading it. This phase's written deliverables are half user docs,
half that style-guide move: the desk's grammar as citable law for
every future story (and the Swift recreation).

## Recipe

1. **USER_GUIDE — "Using the desk" rewritten around the bench:**
   the icon grammar (what badges mean — a table of marks, no
   prose), drop-onto (the matrix as the user sees it: what can be
   dropped on what, and what happens), zone windows (views, sort,
   Clean Up, Snapshot), Info on everything (including tooltypes:
   "every object carries its settings"), and the menu bar with the
   keyboard equivalents table. Screenshots from the real staged
   desk, current tree.
2. **The Desk Grammar document (the style-guide move):** one
   canonical doc under `docs/internal/` — the icon cell contract,
   the state-image and badge rules, the verb registry doctrine
   (one registry, three faces), the drop-matrix authoring rules,
   the Info section derivation rules, ghosting-over-hiding. Written
   as LAW with the same voice as the Constitution, cited by number
   from future stories. AGENT_BRIEF.md gets a pointer so no UI
   story starts without it.
3. **ARCHITECTURE.md:** the verb registry and its three faces; the
   contract-derived Info; diagram touch + render guard per Phase 66.
4. **SECURITY.md:** the wire verb face's row — token gate, consent
   verbs refusing identically to glass, no authority widening.
5. **README (public):** the desk paragraph refreshed in POSITIONING
   voice — the bench, not the diorama.
6. **Guards:** vocabulary/positioning/doc-drift green; every claim
   spot-walked on a staged hub before the story flips.

## Out of scope

- The spec ledger itself (HS-105-07's bookkeeping); MODELS.md.

## Acceptance

- All five surfaces updated; the Desk Grammar doc exists, is linked
  from AGENT_BRIEF.md, and every rule in it is true of the shipped
  tree (spot-walk recorded in evidence).
- Guards + render guard green.

## Test plan

- Guard suite; the ARCHITECTURE mermaid check; the read-through
  walk recorded in evidence.

## Chef's notes

- Write the Desk Grammar doc from the shipped code, not from the
  story files — stories record intent; the law must record fact.
  Where they differ, the difference is either a bug to fix or a
  rule to amend, decided consciously, never papered.
