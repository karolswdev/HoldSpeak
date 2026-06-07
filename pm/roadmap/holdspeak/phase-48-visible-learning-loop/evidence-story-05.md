# Evidence — HS-48-05: Closeout (before/after + dogfood + PR)

**Date:** 2026-06-07. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-48/story-01-learning-digest`.

## What shipped

The verified exit: before/after captures, a green dogfood, a green suite, and the
final summary. The phase is CLOSED and the PR to `main` is opened (merged on green
CI).

### Before / after

Real screenshots under `docs/assets/screenshots/`:

- `learning-loop-before-memory.png` / `learning-loop-before-journal.png` — the old
  surfaces: the Memory tab was a raw correction list (no "What HoldSpeak learned"
  digest, no reach chips); journal entries had no "learned from N similar" signal
  and no one-tap right/wrong correction.
- `learning-digest-week.png` / `-all` / `-empty` — the new digest hero.
- `trust-signals-memory.png` / `trust-signals-journal.png` — the inline reach
  chips on the Memory list + journal entries.
- `correction-ritual.png` — the one-tap correction mid-flow.

The before set was captured by temporarily checking out `5a3c047`'s
`dictation.astro` + `dictation-app.js`, building, screenshotting the Memory +
Journal tabs, then restoring the branch versions and rebuilding (verified clean).
The after-state is regenerable via `scripts/screenshot_learning_digest.py`.

### Dogfood (green)

`scripts/dogfood_learning_loop.py` (HTTP-driven, stub runtime, no mic) re-run at
closeout:

```
2. digest before correcting:
   corrections_made=0  dictations_corrected=0  similar_nudged=0
3. corrected the launch-checklist utterance -> intent: action_item
   taught=True  enabled=True  similar=2
4. digest after correcting:
   corrections_made=1  dictations_corrected=1  similar_nudged=2
   by_block=[{'block_id': 'action_item', 'count': 1}]
   correction reach: 'follow up with sam about the launch checklist' -> action_item (learned from 2 similar)
PASS
```

## Tests run

- Dogfood: `scripts/dogfood_learning_loop.py` → PASS.
- Real-voice e2e (opt-in): `tests/e2e/test_dictation_learning_digest_spoken_e2e.py`
  → 1 passed.
- Full-suite gate: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → **2401 passed, 18 skipped** (exit 0).
- `(cd web && npm run build)` clean; **0** `holdspeak/static/_built/` tracked
  (the branch bundle restored after the before-capture; the digest CSS is back).

## Acceptance criteria

- [x] Before/after captured (old vs new surfaces) + a green dogfood transcript.
- [x] Full suite green; `npm run build` ✓; 0 `_built/` tracked.
- [x] `final-summary.md` written; phase CLOSED; status docs + roadmap updated; PR
      to `main` opened (merged when CI green).
