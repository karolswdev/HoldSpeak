# HS-48-01 — The learning digest ("What HoldSpeak learned")

- **Project:** holdspeak
- **Phase:** 48
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-48-02, HS-48-03, HS-48-04, HS-48-05
- **Owner:** unassigned

## Problem
HoldSpeak records every dictation (the journal), learns from corrections (the
correction memory), and can replay to prove it improved. But none of that is
visible as *progress*. The Memory tab lists raw corrections; the Journal tab lists
raw entries. A user cannot see, at a glance, "this is what HoldSpeak learned from
me this week." The learning loop is the product's strongest differentiator and it
is invisible.

## Scope
- **In:**
  - A **learning-digest aggregation** over the existing data, windowed (this week /
    all time): how many corrections you made, how many journal dictations got
    corrected, the breakdown by kind (intent → block / target → profile) and by the
    blocks/targets that changed, and a "learned from N similar utterances" count per
    correction (computed with the existing `CorrectionStore` Jaccard similarity over
    journal transcripts). Read-only over `dictation_journal` + `dictation_corrections`.
  - A **new API** (e.g. `GET /api/dictation/learning-digest?window=week|all`) that
    returns the aggregation; pure aggregation, no new writes.
  - A **"What HoldSpeak learned" view** at the Signal bar: a digest hero (the
    headline numbers + a short, honest sentence like "You corrected 4 dictations
    this week; 12 similar utterances are now nudged"), the per-correction "learned
    from N similar" rows, and a window toggle. Home it where it reads as a reward,
    not a config editor (a new section, or the top of the Memory tab reframed).
- **Out:** inline trust signals on the result surfaces (HS-48-02); the one-tap
  correction ritual (HS-48-03); docs (HS-48-04). This story is the digest itself.

## Acceptance criteria
- [ ] An aggregation endpoint returns honest, windowed counts over the journal +
      corrections (corrections made, dictations corrected, by-kind/by-target/by-block
      breakdown, and a real "N similar" count from the existing Jaccard matcher).
- [ ] A "What HoldSpeak learned" view renders the digest at the Signal bar with a
      week/all-time toggle; empty state teaches ("make a correction and it shows up
      here"); numbers are accurate, never inflated.
- [ ] Local-first and read-only: no new writes, `corrections_enabled` posture
      respected; behavior-preserving; page-content + API tests; `npm run build` ✓;
      0 `_built/` tracked.

## Test plan
- Unit/integration: seed journal + corrections, assert the digest counts +
  "N similar" match the matcher; window filtering by `created_at`;
  `uv run pytest -q -k "dictation or journal or corrections or learning"`.
- Manual + screenshot: the view reads as progress, not a table; empty state invites.

## Notes / open questions
- Reuse `CorrectionStore.best_match_in` / `similarity` (Jaccard) for "N similar" —
  do not invent a second matcher; the count must reflect what actually nudges.
- `created_at` is ISO text; window by it in SQL or in Python over `recent()`.
- Decide the home: a new "Learned" section vs. a reframed Memory hero. Favor the
  lightest thing that reads as a reward and does not bloat `dictation.astro`
  (heed the page-density warning; prefer a section partial if it grows).
