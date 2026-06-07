# HS-48-03 — Frictionless correction ritual (right / wrong, in flow)

- **Project:** holdspeak
- **Phase:** 48
- **Status:** done
- **Depends on:** HS-48-01
- **Owner:** unassigned

## Problem
Correcting a dictation is the act that teaches HoldSpeak, but today it is a
multi-field form buried in the dry-run moment-of-truth and the Memory tab. The
meditation's read is right: "that was wrong" should be a normal, one-tap
interaction, not a maintenance flow. If correcting is effortful, the learning loop
that powers the digest (HS-48-01) and the trust signals (HS-48-02) starves.

## Scope
- **In:**
  - A **low-effort right / wrong affordance** on dictation results (journal entries,
    and the dry-run result) that reuses the existing
    `POST /api/dictation/journal/{id}/correct` path. "Right" can mark the entry as
    confirmed (lightweight, no write churn); "wrong" opens the existing correct flow
    inline, pre-scoped to the most likely fix (target or block) rather than a blank
    form.
  - Make correcting **separable and obvious**: target vs. block vs. wording, chosen
    in one tap, not a generic kind/value pair.
- **Out:** the digest (HS-48-01); inline counts (HS-48-02); a presence-surface
  affordance (note it as a candidate, but cockpit-first; presence stays focus-safe
  and is not required for this story).

## Acceptance criteria
- [x] A one-tap right / wrong affordance sits on the dictation result + journal
      entries; "wrong" opens the correct flow inline (pre-scoped), reusing the
      existing correct endpoint — no new write primitive.
- [x] Correcting feels like one decision, not a form; the path still records
      against the journal entry and teaches the correction store (honoring
      secret-filter + `corrections_enabled`).
- [x] Focus-safe (no `.focus()` in the dictation bundle); behavior-preserving;
      tests assert the affordance + the correct call; `npm run build` ✓; 0 `_built/`
      tracked.

## Test plan
- Unit/integration: the affordance posts the expected correction; "right" path does
  not corrupt routing; `uv run pytest -q -k "dictation or journal or moment"`.
- Manual + screenshot: correct a route in one or two taps from a journal entry; the
  digest + trust signal update to reflect it.

## Notes / open questions
- The existing `renderMomentOfTruth` / `submitMomentFix` in
  `web/src/scripts/dictation-app.js` is the seam — extend it, do not duplicate.
- Keep the dictation bundle focus-safe (the standing guard: zero `.focus()`).
- Mind page density: if `dictation-app.js` grows, factor the correction UI into a
  behavior module rather than appending.
