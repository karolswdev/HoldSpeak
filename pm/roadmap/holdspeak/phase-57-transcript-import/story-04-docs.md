# HS-57-04 — Docs: transcript import

- **Project:** holdspeak
- **Phase:** 57
- **Status:** done
- **Depends on:** HS-57-03
- **Unblocks:** HS-57-05
- **Owner:** unassigned

## Problem
The Meeting Mode Guide documents recording import only; the transcript path
needs the same honest treatment (and the docs index entry should mention it).

## Scope
- **In:** extend the guide's import section (product-tense): the three
  formats, where each timestamp/speaker truth comes from (real cues for
  VTT/SRT + voice-tag/`Name:` speakers; synthetic ordering for TXT), the
  file-not-retained statement, intel parity ("an imported transcript is a
  real meeting"), and that recordings still import exactly as before.
  Docs-index touch.
- **Out:** internal/architecture docs beyond evidence.

## Acceptance criteria
- [x] Product-tense; vocab guard green (77-doc-test slice); zero em/en
      dashes in new text (grep-verified); humanizer applied.
- [x] The timestamp-honesty and speaker-label rules stated plainly — plus
      the explicit "recordings import exactly as they did before"
      statement (the user's constraint, in writing).
- [x] Docs index updated. See `evidence-story-04.md`.

## Test plan
- Doc-guard slice + full suite.
