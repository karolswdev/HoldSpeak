# HS-83-04 — Docs + the live walk

- **Project:** holdspeak
- **Phase:** 83
- **Status:** open
- **Depends on:** HS-83-01..03.
- **Unblocks:** phase close.

## Problem

Features that aren't at the entry points don't exist (the Phase-64 lesson),
and this phase's features span two docs surfaces: the product's own README /
web docs (grounded asks, conversations, the models door — voice-guard
territory: product tense, no roadmap vocabulary, no AI-vocab, egress stays a
badge) and the mobile track's 15-07 docs story, which describes the same
features from the phone's side. Write once, aim both.

## The design

- **Entry points touched:** the root `README.md` web section and the web's own
  user-facing doc(s) gain: ground an ask (pick meetings, expand, gauge),
  converse with a persona, open a model. Product tense; the voice guard and
  docs-drift guard must pass.
- **The walk:** one recorded pass on the live hub — import a transcript,
  ground an ask on it (control-vs-treatment), converse with a persona grounded
  on the same meeting, open the hub's model and ask it directly. Screenshots
  at each beat land in `screenshots/`; the walk's narrative closes the phase.
- **The sibling note:** point HSM-15-07 at the shared feature descriptions so
  the mobile docs story doesn't re-derive them.

## Acceptance criteria

- [ ] Entry-point docs describe all three features in product tense; guards
      pass.
- [ ] The recorded walk exists with screenshots; every claim in the docs is a
      beat in the walk.
- [ ] The phase status flips to CLOSED with the final summary.

## Test plan

- The docs guards (voice / drift) via the normal suite.
- The walk itself IS the test — live hub, real model, rendered pixels.
