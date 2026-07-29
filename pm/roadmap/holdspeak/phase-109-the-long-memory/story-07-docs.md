# HS-109-07 - Docs — memory at the entry points

- **Project:** holdspeak
- **Phase:** 109
- **Status:** backlog
- **Depends on:** HS-109-01..06
- **Unblocks:** HS-109-08
- **Owner:** unassigned

## The thesis (the bar)

The standing rule: every phase gets its dedicated docs story after
the features stabilize and before closeout, touching the ENTRY
points — and every claim truth-audited against the shipped tree,
never the intended one.

The bar: **the memory is documented as product, in owner vocabulary,
with its limits stated as plainly as its powers** — and the stale
drift the Phase-107 close left behind is reconciled in the same
sweep.

## Problem

Without this story the memory is folklore: the User Guide does not
say what a decision record is or how promotion works, retention
semantics live only in a story file, and two documents still
describe the pre-ruling world (`docs/SECURITY.md:41-44` says N10-N12
are "pending the owner's ruling" — ruled 2026-07-29; BACKLOG
candidate Y still opens with "18 debt" against a 15-debt ledger).

## Recipe

1. **User Guide.** The memory loop in owner vocabulary: record a
   meeting → decisions appear with their moments → accept/supersede →
   promote to the artifact → find it years later by text → ask the
   project and follow the citations. The process window gets its
   paragraph: what it shows, what it never does (no controls), what
   `Unknown` honestly means.
2. **Retention, plainly.** What survives a meeting deletion (the
   severed-source rule from 01), what "years later" promises and does
   not (a local index over what you kept — not backup, not
   immortality). One place, linked from wherever deletion is
   documented.
3. **Architecture doc.** The decision record as a DERIVED projection
   (plugins unchanged), the memory index, grounding-with-citations,
   and the process window as a clause-5 read consumer — each mapped
   to shipped file and line.
4. **README.** One paragraph in the pitch's voice, positioned per
   POSITIONING.md — memory is a pillar-grade capability; lead with
   why.
5. **Reconcile the drift.** Fix `docs/SECURITY.md:41-44` (ruled, not
   pending) without touching the narrowing's strength; update BACKLOG
   candidate Y's header to the 15-debt / post-rulings state (the work
   list itself is already correct in the ledger).
6. **Truth audit.** Every claim in the new text mapped to shipped
   file:line in the evidence; voice guard, doc-drift guards, and
   vocabulary gates green; no roadmap vocabulary in user-facing docs.

## Out of scope

- New guards beyond what the claims need (extend `test_doc_drift_guard`
  only if a number is worth pinning — the debt count already is).
- Any behavior change. Docs-and-test only.
- Rewriting SECURITY's containment story (that is Phase 108's docs
  story).

## Acceptance

- User Guide, Architecture, and README carry the memory + process
  window at their real entry points; owner vocabulary; why-ledes.
- Retention semantics stated where a user will actually meet them.
- The two stale drift items fixed; `docs/SECURITY.md` narrowing
  byte-comparable in strength (only the pending-ruling paragraph
  changes); BACKLOG candidate Y header matches the ledger.
- Truth-audit table in evidence: claim → file:line, zero unproven
  claims; corrected claims listed.
- Voice/doc-drift/vocabulary guards green; full suite green.

## Test plan

- **Unit:** guard suite (voice, drift, vocabulary) green; any new
  pinned number covered by the drift guard.
- **Manual:** read-through against POSITIONING voice rules.
- **Evidence:** the truth-audit table; guard run output.

## Chef's notes

- The em-dash and prose disciplines from the Front Door lineage
  apply; run the voice guard before polishing by hand.
- "Grounded on 12 of 47" belongs in the User Guide too — the honesty
  is the feature; document the limit as the selling point it is.
- Do not let the SECURITY edit grow: one paragraph dies, the
  narrowing stays word-for-word.
