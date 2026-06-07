# HS-48-02 — Inline trust signals ("learned from N similar")

- **Project:** holdspeak
- **Phase:** 48
- **Status:** done
- **Depends on:** HS-48-01
- **Owner:** unassigned

## Problem
Even with a digest, the learning is invisible at the moment it matters: when a
dictation is routed or corrected. A user who corrects a route once has no signal
that the correction will actually carry to similar utterances, and no confirmation
later that it did. Trust is built where the work happens, not in a separate tab.

## Scope
- **In:**
  - A small, honest **"learned from N similar" signal** surfaced where routing and
    correction happen: the dry-run result, the journal entries, and the Memory list.
    It states the real count from the HS-48-01 matcher (e.g. "this nudge matches 3
    past utterances") and stays quiet when N is 0.
  - A **confirmation after a correction** that reflects reality: when you teach a
    route, show how many similar utterances it now covers (reusing the digest's
    similarity count), upgrading the current generic "taught" toast.
- **Out:** the digest view (HS-48-01); the one-tap right/wrong ritual (HS-48-03).
  This story makes the existing surfaces *show the learning*.

## Acceptance criteria
- [x] The dry-run result and journal entries carry a truthful "learned from N
      similar" signal (hidden when N is 0); the post-correction confirmation states
      the real coverage count, not a generic message.
- [x] Counts come from the HS-48-01 similarity logic (one matcher, no second
      source of truth); no surface implies learning that did not happen
      (secret-filtered / disabled corrections stay honest).
- [x] Focus-safe; behavior-preserving; tests assert the signal + count; `npm run
      build` ✓; 0 `_built/` tracked.

## Test plan
- Unit/integration: a correction over a seeded journal yields the expected N; the
  signal hides at N=0; the toast text reflects the count;
  `uv run pytest -q -k "dictation or journal or corrections"`.
- Manual + screenshot: correct a route, see an honest coverage count; a route with
  no similar history shows no inflated claim.

## Notes / open questions
- The moment-of-truth correct endpoint already returns `{ taught, size }`
  (`POST /api/dictation/journal/{id}/correct`); extend its response (or compute
  client-side from the digest) to include the similarity count, honestly.
- Keep it calm: a quiet chip, not a celebration banner. Honesty over hype is the
  whole point of this phase.
