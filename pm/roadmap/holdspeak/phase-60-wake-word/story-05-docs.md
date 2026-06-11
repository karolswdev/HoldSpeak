# HS-60-05 — Docs: the wake word

- **Project:** holdspeak
- **Phase:** 60
- **Status:** backlog
- **Depends on:** HS-60-03, HS-60-04
- **Unblocks:** HS-60-06
- **Owner:** unassigned

## Problem
An always-listening feature lives or dies on trust; the docs must state
what listens, what arms, what types, what downloads, and what was
measured.

## Scope
- **In:** the USER_GUIDE section (saying the phrase, the armed window,
  the preview default, Type it, the type opt-in as consent, the
  measured false-accept numbers with the synthetic-speech caveat, the
  pause-during-capture behavior); SECURITY.md's egress table gains the
  model-download row; POSITIONING.md gains the canonical rows ("the
  wake word", "the armed window"). Canon-clean (the live voice guard).
- **Out:** localization; marketing beyond the docs.

## Acceptance criteria
- [ ] Product-tense; voice guard green; the egress row ships; the
      measured numbers cited honestly.
- [ ] Doc slice green.

## Test plan
- Doc-guard slice + full suite.
