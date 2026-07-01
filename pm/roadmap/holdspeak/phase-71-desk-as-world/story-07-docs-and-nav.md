# HS-71-07 — Docs + the nav decision (the docs story)

- **Status:** done
- **Priority:** MED (the dedicated docs story — after the build, before closeout)
- **Depends on:** HS-71-01 … HS-71-06
- **Evidence:** [evidence-story-07.md](./evidence-story-07.md)

## Goal

Record the web diorama in the docs, and resolve the one open product question
the build surfaces: now that `/desk` is a real "world", does it stay in the
Studio tier or get promoted?

## Scope

- **The nav decision (owner call).** Phase 70 put Desk in the Studio tier and
  made the two modes the front door. Now the Desk is the showpiece. Options to
  put to the owner and then implement: (a) keep it in Studio (the two modes stay
  the front door; the world is a place you go); (b) promote it to a top-level
  nav item beside the two modes; (c) a "Enter the Desk" affordance from Home.
  Implement the chosen one; keep the four-door legibility Phase 70 won.
- **Docs**: the Desk gets its short guide / section (what the world is, how to
  arrange, file, and dive); POSITIONING gains a line on the web diorama as the
  spatial expression of the Primitive Framework (dash-free; the voice guard runs
  on `docs/*.md` + README). Any screenshot of the old flat `/desk` re-shot.
- Naming stays canonical (the surface is "the Desk"; directories are still
  "directories" in the contract, "zones/shelves" only as the on-screen spatial
  metaphor if used).

## Proof required

The nav decision implemented + screenshot; the Desk documented; POSITIONING
line added; voice/doc guard green; re-shot screenshots committed.

## Done

Shipped. Nav decision (owner-chosen): celebrate the Desk on Home + keep it in
Studio (the four-door nav is unchanged). Home gains a prominent accent-edged
"The Desk -> Your primitives as a spatial world" entry beside the quiet Studio
link (now pointing at `/studio`). Docs: a short `docs/WEB_DESK.md` guide (arrange,
file, dive, Qlippy) linked from the index, and a Desk paragraph in POSITIONING's
web-surface section. Voice/doc guard + preflight 17 passed (dash-free); suite
green. See [evidence-story-07.md](./evidence-story-07.md).
