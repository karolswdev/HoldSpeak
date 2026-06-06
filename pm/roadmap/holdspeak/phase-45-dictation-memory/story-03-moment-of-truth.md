# HS-45-03 — The moment of truth: correct in flow, and it teaches

- **Project:** holdspeak
- **Phase:** 45
- **Status:** done
- **Depends on:** HS-45-01
- **Unblocks:** HS-45-04
- **Owner:** Claude (Opus 4.8)
- **Evidence:** [evidence-story-03.md](./evidence-story-03.md)

## Problem
The moment a dictation lands wrong is when fixing is cheapest — and when teaching
matters most. Today the user fixes it *in the target app* and, separately,
teaches the copilot via the `/dictation` **Memory tab** after the fact
(`/api/dictation/corrections`). Correction is reactive and out-of-flow; the
"it learns from me" loop is real (`intent_router.py` Jaccard nudge) but it never
*meets the user in the moment*. This story makes correction an in-the-moment,
focus-safe gesture that teaches — and records the fix against the journal.

## Scope
- **In:**
  - An **in-the-moment review + correct** affordance: right after a run, surface
    the just-typed **result** with a one-tap **"Fix"** → a quick re-route (pick
    the correct block / target) → which **writes a correction** (reuse the
    Phase-40 `CorrectionStore` + `dictation_corrections`, via the existing
    `/api/dictation/corrections` POST or a thin wrapper) **and marks the
    HS-45-01 journal entry `corrected`** (linking to the new correction).
  - **Surfaces:** the **dry-run result panel** is the guaranteed no-mic path
    (review the dry-run output, fix it, it teaches); the **real-dictation**
    surface is the web dashboard (and, where presence is enabled, a focus-safe
    presence affordance). The fix flow is identical across surfaces.
  - **Focus-safe:** the surface NEVER steals keyboard focus (same invariant as
    desktop presence) — correcting must not interrupt the dictation flow.
  - A new endpoint (or extension) to **attach a correction to a journal entry**
    (`POST /api/dictation/journal/{id}/correct` → records the correction + flips
    `corrected`), so the Journal (HS-45-02) shows which utterances were fixed.
- **Out:** the correction *engine* / nudge (already exists — do not rebuild);
  replay (HS-45-04). This is the in-moment **surface** + the journal↔correction
  **linkage**.

## Acceptance criteria
- [x] After a **dry-run**, the result panel offers a one-tap fix that records a
      correction and flips the journal entry's `corrected` flag — verifiable
      without a mic.
- [x] The recorded correction is the same kind the Memory tab manages and
      **nudges future routing** (a follow-up similar utterance routes to the
      corrected block/target — asserted via the intent-router `best_match_in`
      nudge path).
- [x] The Journal (HS-45-02) renders a `corrected` marker on fixed entries.
- [x] The in-moment surface does **not** steal keyboard focus (no `autofocus`;
      the dictation app script never calls `.focus()`; reveal is click-driven).
- [x] Journaling/typing **output is byte-identical** when the user does NOT
      correct (the fix path is purely additive — no run path touched).
- [x] Suite green; `(cd web && npm run build)` succeeds; **0** `_built/` tracked.

## Test plan
- Unit: correction-attach endpoint writes a correction + flips `corrected`;
  the intent-router nudge fires for a subsequent similar utterance.
  `uv run pytest -q -k "correction or nudge or journal_correct"`.
- Integration: dry-run → fix → re-run a similar dry-run routes to the corrected
  target; the journal entry shows `corrected`.
- Page-content: the in-moment fix affordance markup + focus-safe attributes.
- Live (Playwright): dry-run → fix-in-place → `evidence/moment_of_truth.png`.
- Manual / device: n/a — dry-run is the no-mic equivalent; real-dictation surface
  verified structurally + (if a mic session is ever available) live.

## Notes / open questions
- **Where the real-dictation surface lives** (dashboard panel vs presence HUD vs
  transient toast) — settle during build; the dry-run panel is the guaranteed
  surface and the one the tests/dogfood drive.
- Keep the correction payload **gist-only + secret-filtered** (parity with the
  existing store) — never persist raw secrets in the teach path.
- Consider a subtle "taught ✓" confirmation so the learning feels acknowledged
  (delight), reduced-motion-safe.
