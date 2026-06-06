# Phase 45 — Dictation Memory & the Moment of Truth — FINAL SUMMARY

**Status: CLOSED ✅ (6/6).** 2026-06-06. Branch `phase-45-dictation-memory`.
Opened and closed the same day on user direction ("think really hard around the
experience … scaffold a phase that will be oh-so-meaningful").

## The goal — and was it met?

> Give the daily-driver dictation loop a persistent, private, reviewable memory
> and a tight in-the-moment correct-and-teach loop — turning a black box into a
> trusted, learning companion — **without changing what gets typed.**

**Met.** Your meetings were remembered; your voice wasn't. Now it is. Dictation
went from *"I spoke and hoped"* to *"I spoke, I can see it, I can fix it, it
learned."* — and the typed output is byte-identical to before (journaling is a
pure side-channel; off ⇒ byte-identical, proven).

## Before → after

| | Before (a black box) | After (this phase) |
|---|---|---|
| Record | nothing persisted — a gist-only correction ring + a 20-run in-memory latency ring, both gone on restart | a durable, local **`dictation_journal`** — every run (said → typed → routed → per-stage latency → source) |
| Review | none | the **Journal** tab: a said→typed timeline, latency strip, search/filters, copy, delete/clear |
| Correct | reactive, out-of-flow (fix in the app, maybe teach later via a separate Memory tab) | **in the moment** — *"Was that right? → Fix it → Taught ✓"* right on the result; it teaches AND flags the entry |
| Replay | impossible | **↻ Replay** any utterance through the *current* pipeline; before → after; correct → replay → routing changes |
| Latency | aggregate p50/p95 only | **per-utterance** stage strip on every entry |

The "after" is captured live (no mic): `evidence/journal_timeline.png`,
`evidence/moment_of_truth.png`, `evidence/replay_before_after.png` (also embedded
in the user guide). The "before" is the *absence* of all of it — there was no
surface to capture.

## Per-story recap

- **HS-45-01 — the persistence spine.** A `dictation_journal` table +
  `DictationJournalRepository` + a side-channel `DictationJournalRecorder` fed at
  the same post-run seam telemetry uses, wired into **both** the live runtime
  (`source='dictation'`) and the dry-run path (`source='dry_run'`). Secret-redacted,
  retention-capped (`journal_retention`), toggle (`journal_enabled`, default ON,
  local). Best-effort: a journal error never breaks a dictation. **Proven by a
  true end-to-end run against the live `.43` LLM** (real pipeline → real DB row).
- **HS-45-02 — the Journal.** A `/dictation` tab over `GET/DELETE
  /api/dictation/journal`: elevated said→typed cards with source chips,
  block/target badges, a per-utterance latency strip, search + source/warning/
  corrected filters, copy, per-entry delete + clear, a first-class local-only
  trust statement, a warm empty state, the Phase-44 premium bar.
- **HS-45-03 — the moment of truth.** The dry-run result panel surfaces
  *"Was that right? → Fix it → Taught ✓"* via `POST …/journal/{id}/correct` —
  records a correction (the Phase-40 engine, write-through → nudges future
  routing) keyed on the entry transcript, flips `corrected`, links the
  correction. Focus-safe (no `autofocus`/`.focus()`). *(Surfaced + fixed a
  pre-existing dry-run `telemetryHtml` ReferenceError that had left every browser
  dry-run result blank.)*
- **HS-45-04 — replay.** `POST …/journal/{id}/replay` re-runs the stored
  transcript through the current pipeline (dry-run, no typing, no new row,
  original untouched, original project context); a ↻ Replay action renders
  before → after. The payoff proven offline: correct an utterance's target →
  replay → the routed target flips. Re-insert is preview + copy (focus-safe);
  OS-typing re-insert deferred (no web→typer seam; focus-steal risk).
- **HS-45-05 — docs.** `INTELLIGENT_TYPING_GUIDE.md` §12 documents what's
  recorded, the local-only privacy posture, the in-moment loop, and replay, with
  three screenshots; cross-linked from the README + docs index. Doc guards green.
- **HS-45-06 — closeout (this).** The no-mic dogfood + invariant re-assertion +
  this summary + the PR.

## Verification

- **Dogfood:** `uv run python scripts/dogfood_journal.py` → **`JOURNAL DOGFOOD
  OK`** — record (3 dry-runs journaled) → review (newest-first + latency) →
  correct (teaches + flips `corrected`) → replay (routes to the corrected target,
  no new row) → invariant (journal-off ⇒ no row + byte-identical output). Zero
  file edits, no mic, no LAN-LLM.
- **True e2e:** `tests/e2e/test_dictation_journal_e2e.py` against `.43` (a real
  446-char ramble journaled with real routing/target/latency).
- **Suite:** `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2363 passed,
  17 skipped** (+~35 over the Phase-44 close at 2328). Route-table guard 30 → 35.
  `(cd web && npm run build)` ✓. **0** `holdspeak/static/_built/` tracked.

## Invariants held

- **Behavior-preserving** — journaling is a side-channel; off/empty ⇒
  byte-identical typed output (dogfood step 5; the whole suite green).
- **Local-first & private** — local SQLite only, never uploaded/synced;
  secret-redacted on write; retention-capped; per-entry delete + one-click wipe;
  the trust posture is first-class in the UI *and* the docs. No transcript egress
  (the dogfood makes no outbound call).
- **Focus-safe** — the in-moment fix + replay re-insert never `autofocus` or
  `.focus()`; preview + copy only.
- **Provable remotely (no mic)** — the dry-run path mirrors real dictation and is
  journaled (`source='dry_run'`); everything was exercised mic-free.

## Handoff

Phase 45 is complete. The journal arc (record → review → correct → replay) is the
foundation for natural follow-ons, none committed:

- **Intent-correction replay payoff with a runtime** — the offline payoff proves
  *target* corrections (the heuristic post-step); the *intent* nudge fires inside
  `IntentRouter` (needs an LLM). A `.43`-gated e2e could show an intent-correction
  changing the replayed *route*.
- **OS-typing re-insert** — deferred here for focus-safety; a deliberate, gated
  typer seam (mirroring the presence focus invariant) could let replay/journal
  type the improved result into the active app.
- **Journal-as-corpus** — the journal is now a labeled record of what routed where
  and what the user corrected; it could feed block-suggestion or routing-quality
  surfaces.

Open & **hardware-gated** (author remote, no mic/AI-PI), untouched: Phase 24
(companion, 3/6), Phase 25 (HS-25-07 dogfood), Phase 15 (out-and-about).
