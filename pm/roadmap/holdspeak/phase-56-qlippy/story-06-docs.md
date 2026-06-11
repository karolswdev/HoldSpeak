# HS-56-06 — Docs: Qlippy

- **Project:** holdspeak
- **Phase:** 56
- **Status:** backlog
- **Depends on:** HS-56-03, HS-56-04
- **Unblocks:** HS-56-07
- **Owner:** unassigned

## Problem
A mascot that can surface approval decisions must be documented with the same
honesty it renders: what he is, when he appears, what he never does, and how
to turn him off.

## Scope
- **In:** the presence/desktop-presence documentation (wherever the Phase-41/43
  presence guide section lives) gains the Qlippy story, product-tense: the
  two levels (dock vs. card), exactly which moments produce a card, the
  never-acts guarantee (approving on the card is the same audited approval as
  the dashboard), the three privacy answers every actionable card shows, both
  toggles (presence + mascot, both off by default), reduced-motion behavior,
  and the one-click off. A screenshot or two. Linked from the docs index.
- **Out:** internal/architecture docs beyond evidence; roadmap vocabulary
  anywhere user-facing.

## Acceptance criteria
- [ ] Product-tense, passes the roadmap-vocab guard, zero em/en dashes in the
      new text, `humanizer` run with findings addressed.
- [ ] The never-acts guarantee and the three privacy answers are stated
      verbatim-checkably.
- [ ] Linked from the docs index; screenshots included.

## Test plan
- Doc-guard slice + full suite.

## Notes / open questions
- Find the existing presence doc home first (INTELLIGENT_TYPING_GUIDE §11 per
  the README's links) and extend rather than fragment.
