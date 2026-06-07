# Evidence — HS-48-02: Inline trust signals ("learned from N similar")

Write-once record. The learning is now visible at the moment it matters — on
the dry-run result, on journal entries, and in the Memory list — and the
post-correction confirmation states real coverage. Every count comes from the
HS-48-01 matcher; there is no second source of truth.

## What shipped

**Backend — one matcher, reused everywhere** (`holdspeak/dictation_learning.py`)
- `reach_for_gist(gist, transcripts)` — the single definition of "N similar"
  (Jaccard >= 0.5 over journal transcripts). The digest, the inline chips, and
  the toast all count through this one function, so no surface can drift.
- `reach_by_gist_map(corrections, transcripts)` — precompute reach per gist so
  per-entry lookups stay cheap (corrections cap 20 x journal; one pass).
- `best_correction_signal(text, corrections, reach_by_gist)` — the correction
  the live router would apply to an utterance (reusing `best_match_in` across
  both kinds) and its reach, or `None` when nothing matches. Passing
  `corrections=None` (the disabled / no-snapshot posture) returns `None`,
  byte-identical to routing. `build_learning_digest` was refactored onto
  `reach_for_gist` so HS-48-01 and HS-48-02 share the count.

**Backend — the three surfaces + the toast** (`web/routes/dictation/`)
- Dry-run (`_helpers.py`): the result carries `learning` — the signal for the
  utterance, computed from the same `correction_snapshot` routing used (so it is
  `None` when corrections are off), over the journal as it stood *before* this
  run (past utterances, not counting this one). Quiet when nothing matches.
- `GET /api/dictation/journal` (`pipeline.py`): each entry gets a `learning`
  signal, gated on `corrections_enabled` (a `None` snapshot means the router
  nudges nothing, so the API claims nothing).
- `GET /api/dictation/corrections`: each item gets its real `similar` reach over
  the journal (the Memory list shows how far each thing it learned carries).
- `POST /api/dictation/journal/{id}/correct`: response gains `similar` (the
  taught correction's reach, 0 when nothing was taught) + `enabled`, so the UI
  says "now nudges N" vs "matches N — turn on corrections" without overclaiming.

**UI** (`web/src/scripts/dictation-app.js` + `dictation.astro`)
- `learnSigChip(n)` — one calm, success-tinted chip ("learned from N similar"),
  quiet at N=0. Rendered on the dry-run moment-of-truth head, on journal entry
  headers, and on Memory list items. CSS is in `<style is:global>` (the chips
  live in JS-injected DOM).
- The post-correction toast was upgraded from the generic "taught" line to state
  real coverage, honestly split on `enabled`. Focus-safe (no `.focus()`).

## How to verify

- `(cd web && npm run build)` — completes; 0 `_built/` tracked.
- Screenshots (real server, seeded temp DB, corrections on, no mic/LLM):
  `uv run python scripts/screenshot_learning_digest.py` →
  `docs/assets/screenshots/trust-signals-journal.png` (each matched entry shows
  "learned from N similar"; the unrelated "book the conference room" line shows
  none) and `trust-signals-memory.png` (Memory list reach chips; the target
  correction with no journal match correctly shows none).

## Tests run (read the output)

- `uv run pytest -q tests/unit/test_dictation_learning_digest.py` — 10 passed
  (3 new: reach via the matcher, `best_correction_signal` finds the router
  match, and stays quiet when nothing matches / corrections are None).
- `uv run pytest -q tests/integration/test_web_dictation_trust_signals.py` —
  7 passed: Memory-list reach; journal signal present only when
  `corrections_enabled` and quiet for unrelated entries; dry-run signal on a
  matching utterance + quiet otherwise + none when disabled; the correct
  response's real coverage + posture; secret-filtered teaches nothing
  (`taught=false`, `similar=0`); the is:global CSS guard for `.learn-sig`.
- Slice: `uv run pytest -q -k "dictation or journal or corrections or learning" --ignore=tests/e2e/test_metal.py` — 390 passed, 6 skipped.
- Spoken e2e still green (dry-run now returns `learning`): 1 passed
  (`HOLDSPEAK_SPOKEN_DICTATION_E2E=1`).
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` — 2395 passed, 18 skipped.

## Invariants held

- Honest over hype: one matcher (`reach_for_gist` / `best_match_in`), quiet at
  N=0, `corrections_enabled` posture respected on every nudging surface,
  secret-filtered corrections teach nothing and claim nothing.
- Behavior-preserving: routing stays byte-identical when corrections are off
  (the snapshot is `None`, so the signal is `None`); the digest count is
  unchanged (shared function). Full suite green.
- Focus-safe; local-first; 0 `_built/` tracked; no `--no-verify`, no `Co-Authored-By`.
