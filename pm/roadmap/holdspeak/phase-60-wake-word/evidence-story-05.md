# Evidence — HS-60-05: Docs: the wake word

**Date:** 2026-06-11
**Branch:** `phase-60-wake-word`

## 1. What shipped

- **`docs/USER_GUIDE.md`** — "The wake word" section (beside the other
  voice-typing surfaces): the hold-to-talk contrast lede, the armed
  window explained, **the safety fork stated as the feature's core**
  (preview-first default with the Type-it flow; type-immediately as the
  explicit opt-in with its consequence stated "where you make it"), the
  one-time model download named as the only network moment, the
  pause-around-captures behavior, the presence recommendation, and **the
  honest numbers verbatim from HS-60-04**: zero false detections in 57
  ordinary utterances, the near-homophone reality ("no threshold can
  separate them… exactly why the preview default exists"), and the
  synthetic-speech caveat.
- **`docs/SECURITY.md`** — the egress table gains the wake-model-download
  row, honestly framed: an inbound one-time ~7 MB fetch, opt-in, cached;
  detection local; no audio ever egresses.
- **`docs/internal/POSITIONING.md`** — the canonical rows: "the wake
  word" (not "hotword"/"voice activation") and "the armed window" (not
  "listening window"/"wake session").

## 2. The guards

Zero em/en dashes in the new prose (audited); canonical names throughout;
the live voice guard, vocabulary guard, and link locks all green in the
82-test doc slice.

## 3. Tests

```
$ uv run pytest -q tests/ -k "doc"
82 passed, 2 skipped
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2723 passed, 17 skipped
```

(Docs-only; suite unchanged.)
