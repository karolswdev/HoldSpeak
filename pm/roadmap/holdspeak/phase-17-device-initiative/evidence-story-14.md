# Evidence — HS-17-14 — Filter ack marker for word-level hallucinations

- **Shipped:** 2026-05-10
- **Commit:** `2a6a476`
- **Owner:** karol

## Files touched

### `holdspeak/device_status.py`

- New `is_pure_silence(text)` helper: returns True for empty,
  whitespace-only, or only-punctuation text. False for anything with
  word content (even hallucinated single-word artifacts).
- `push_segment_to_devices` consults the new helper:
  - `is_likely_hallucination` + `is_pure_silence` → skip (return 0)
  - `is_likely_hallucination` + word content → push `{speaker}: …`
    with `ttl_ms=ttl_ms` (default 3000) so the LCD updates.
  - Otherwise → push full `{speaker}: {text}`.

### Tests (`tests/unit/test_device_status_helpers.py`)

- `is_pure_silence`: parametrized tests over empty / whitespace /
  only-punctuation True cases + word-content False cases.
- `test_push_segment_acks_word_level_hallucinations`: parametrized
  over `you` / `You` / `you you you` / `Thanks for watching` etc.
  Asserts payload == `Karol: …` and ttl preserved.
- `test_push_segment_skips_pure_silence`: empty / whitespace / `...`
  / `,,,` → 0 sends, no broadcast.
- `test_push_segment_ack_uses_unknown_speaker_when_missing`:
  unspecified speaker → `?: …`.

## Verification

```
$ .venv/bin/python -m pytest tests/unit/test_device_status_helpers.py -q
93 passed in 0.07s    # tests added in this story

$ .venv/bin/python -m pytest -q
1757 passed, 21 skipped     # full suite, earlier in session
```

## Live verification (2026-05-10)

Real AIPI-Lite hardware + live HoldSpeak. User spoke at the device
between meaningful and noisy moments. Bridge log showed alternating
real-content segments and `Karol: …` ack flashes (when Whisper
auto-detection produced single-word artifacts). User confirmation
that the persist-until-replaced middle slot was getting *some* update
on each utterance even when Whisper output was garbage.

## Acceptance criteria — re-checked

All brackets `[x]` — see [`story-14-filter-ack-marker.md`](./story-14-filter-ack-marker.md).

## Deviations from plan

- None. Implementation matched the design closely.

## Follow-ups

- Possibly tune the speaker prefix on acks — currently shows the same
  `{speaker}` Whisper attributed; ambiguous for the Me/Remote streams.
