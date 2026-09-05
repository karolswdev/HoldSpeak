# HS-176-02 — The first correction

- **Project:** holdspeak
- **Phase:** 176
- **Status:** backlog
- **Depends on:** HS-176-01
- **Unblocks:** HS-176-05
- **Owner:** unassigned

## Problem

The correction store exists (corrections.py:1-56, CorrectionStore with
Jaccard matching, durable via DictationCorrectionRepository, wired at
web_runtime.py:97-109 and web_server.py:225-228) and the API routes
exist (pipeline.py:917-1009), but the owner's desk has 0 corrections.
The "learns how you work" loop is untrained. The Speak face has no
correction flow: the user cannot tap a landed utterance and teach a
correction in-world. The learning digest (dictation_learning.py:1-58)
reads empty because there is nothing to aggregate.

## Scope

- In:
  - The correction flow on the Speak face built to the HS-176-01
    artboard: tap a landed utterance → the correction well unfolds →
    type the correction → save via POST /api/dictation/corrections.
  - The pipeline applies the correction: the CorrectionStore's
    best_match_in() fires on the next matching utterance; the
    corrected text is what lands in the target.
  - The correction chip on the utterance row shows what fired (the
    correction key → value, the similarity score).
  - The learning digest section on the Speak face reads > 0 with
    honest reach numbers.
  - The correction is durable: restart the hub, the correction
    persists and applies.
- Out:
  - Correction import/export.
  - Correction suggestions from the model (the correction is typed by
    the owner, never generated).
  - Bulk correction editing (one correction at a time; a correction
    list is a future candidate).
  - Cloud-based correction sync (Article III).

## Acceptance criteria

- [ ] The correction flow on the Speak face matches the HS-176-01
      artboard (Article IX.2).
- [ ] A correction taught via the flow is persisted by
      DictationCorrectionRepository and survives a hub restart.
- [ ] The pipeline's Jaccard matcher applies the correction to the
      next matching utterance; the corrected text lands in the target
      (Article IX.1).
- [ ] The correction chip on the utterance row shows the correction
      that fired.
- [ ] The learning digest reads > 0 corrections with honest reach
      numbers (Article VI.1).
- [ ] The correction count on his desk is > 0 (the census fact paid).
- [ ] Zero egress (Article III).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k correction`
  - A correction is created via the API and persists across restart.
  - The Jaccard matcher fires on a matching utterance and returns the
    corrected text.
  - The learning digest aggregates the correction's reach.
- Integration: the rig boots a hub, creates a correction via POST,
  runs a matching utterance through the pipeline, asserts the
  corrected text.
- Manual: the owner teaches one correction on the Speak face;
  dictates a matching sentence; sees the correction applied.

## Notes / open questions

- The ring buffer cap is 20 (corrections.py). For the first phase this
  is sufficient; if the owner hits the cap, the oldest correction is
  evicted. A cap increase or unbounded store is a future candidate.
- The Jaccard threshold for matching is tunable. The default should be
  validated against the owner's real dictation during the walk.
