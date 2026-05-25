# Evidence — HS-17-16 — Overlap windows on transcription passes

- **Shipped:** 2026-05-10
- **Commit:** `0c0e7cf`
- **Companion:** AIPI-4-15 on the AIPI-Lite side
- **Owner:** karol

## Files touched

### `holdspeak/meeting_session.py`

- `MeetingSession.__init__` gains:
  ```python
  self._overlap_tail_seconds: float = 1.5
  self._stream_tails: dict[str, "np.ndarray"] = {}
  ```
- New `_apply_overlap(stream_id, audio, final)` helper.
- `_transcribe_chunks` wraps mic / system / per-device streams:
  ```python
  mic_audio = self._apply_overlap("mic", mic_audio, final)
  system_audio = self._apply_overlap("system", system_audio, final)
  audio = self._apply_overlap(f"device:{device_id}", audio, final)
  ```

### Tests (`tests/unit/test_meeting_overlap.py` — NEW)

7 cases:
1. `test_overlap_seconds_default` — default 1.5 s.
2. `test_first_pass_no_prior_tail` — fresh stream returns audio
   unchanged + saves tail.
3. `test_second_pass_prepends_previous_tail` — combined length =
   1.5 s tail + N s new; leading samples come from previous chunk.
4. `test_third_pass_carries_overlap_forward` — tail rolls (gets
   pass-2's tail, not pass-1's).
5. `test_final_pass_clears_tail` — final pass prepends but no new
   tail saved.
6. `test_streams_are_independent` — mic / system / device tails
   don't bleed.
7. `test_small_first_chunk_saves_whole_chunk_as_tail` — sub-overlap
   chunks save whole thing.

## Verification

```
$ .venv/bin/python -m pytest tests/unit/test_meeting_overlap.py -q
7 passed in 0.40s

$ .venv/bin/python -m pytest -q     # full HS suite
1809 passed, 21 skipped in 124.65s
```

## Acceptance criteria — re-checked

7 of 8 brackets `[x]` — see [`story-16-overlap-windows.md`](./story-16-overlap-windows.md). The one open bracket is the live-hardware verification (a meeting with a sentence spoken across a 10 s boundary on AIPI-Lite); math correctness is confirmed; live ergonomic evidence pending.

## Deviations from plan

- None.

## Follow-ups

- Live verification with a sentence spanning a boundary.
- Optional: segment-level dedup of overlap-region text if duplicate
  artifacts surface meaningfully.
- Optional: VAD-aware cut points (the alternative the user passed
  on) remains a future enhancement if overlap doesn't fully solve
  the perceived cut-sentence issue.
