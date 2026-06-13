# HS-64-01 — The README catches up

- **Project:** holdspeak
- **Phase:** 64
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-64-02
- **Owner:** unassigned

## Problem
The front door sells a Phase-55 product: zero mentions of the wake word,
Send to Slack, the spoken language setting, or the spoken-symbol
dictionary.

## Scope
- **In:** the two-modes tour absorbs the P59–P62 surface in canon voice
  (dictation cell: the wake word with the preview-default truth, the
  spoken language setting, the spoken-symbol dictionary; meeting cell:
  Send to Slack as aftercare's outbound door); pillars + comparison
  checked for staleness; scannability preserved; locks + renderer
  posture verified.
- **Out:** re-positioning; new screenshots unless a claim needs one.

## Acceptance criteria
- [ ] Every P59–P62 surface is findable from the README, named per
      POSITIONING.
- [ ] The doc-drift guard slice is green (dashes, vocab, names, counts,
      links, images).
- [ ] The diff reads at humanizer standard.

## Test plan
- `uv run pytest -q tests/unit/test_doc_drift_guard.py`; the full suite.
