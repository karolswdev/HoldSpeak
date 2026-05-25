# Evidence — HS-17-13 — Transcript Noise Filter for Device LCD Pushback

- **Date:** 2026-05-10
- **Status:** done
- **Story:** [HS-17-13](./story-13-transcript-noise-filter.md)

## What changed

- Added `is_likely_hallucination(text)` in `holdspeak/device_status.py`.
- Added `is_pure_silence(text)` to distinguish no-audio punctuation/empty cases from word-level artifacts.
- Updated `push_segment_to_devices(...)`:
  - pure silence and punctuation-only text skip LCD pushback;
  - word-level hallucinations broadcast `{speaker}: …` as an acknowledgement;
  - real content still broadcasts normally.
- Raised `LCD_TEXT_MAX_CHARS` to 150 for the larger AIPI-side scroll/wrap region.
- Updated protocol docs to state that LCD pushback can filter common Whisper hallucinations while preserving durable transcript storage.

## Verification

```bash
.venv/bin/pytest -q tests/unit/test_device_status_helpers.py
```

Result: included in focused run, `196 passed in 3.53s`.

```bash
.venv/bin/pytest -q
```

Result: `1774 passed, 21 skipped in 124.09s`.

## Acceptance Criteria

- [x] `is_likely_hallucination(text)` implemented and covered.
- [x] `push_segment_to_devices` filters pure silence and acknowledges word-level artifacts.
- [x] Unit tests cover hallucination examples and real-content counterexamples.
- [x] Empty-text LCD pushback behavior updated to no-op.
- [x] `docs/DEVICE_PROTOCOL.md` notes display-only filtering; durable transcript remains unchanged.

## Notes

- The filter is deliberately narrow. Short real words such as `yes`, `no`, `thanks`, and `hello` are allowed through to avoid hiding legitimate meeting content.
