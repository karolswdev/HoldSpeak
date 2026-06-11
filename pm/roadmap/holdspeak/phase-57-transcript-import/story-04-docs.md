# HS-57-04 — Docs: transcript import

- **Project:** holdspeak
- **Phase:** 57
- **Status:** backlog
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
- [ ] Product-tense; vocab guard green; zero em/en dashes in new text;
      humanizer applied.
- [ ] The timestamp-honesty and speaker-label rules stated plainly.
- [ ] Docs index updated.

## Test plan
- Doc-guard slice + full suite.
