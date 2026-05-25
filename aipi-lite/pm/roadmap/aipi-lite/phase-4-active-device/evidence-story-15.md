# Evidence — AIPI-4-15 — Overlap windows on transcription passes

- **Shipped:** 2026-05-10
- **Commit:** `0c0e7cf` (HoldSpeak `meeting_session.py` + tests)
- **Owner:** karol

## Files touched

### HoldSpeak (`holdspeak/meeting_session.py`)

- `MeetingSession.__init__` gains two attributes:
  ```python
  self._overlap_tail_seconds: float = 1.5
  self._stream_tails: dict[str, "np.ndarray"] = {}
  ```
- New helper `_apply_overlap(stream_id, audio, final)`:
  - Prepends the previous pass's tail (if any) to the current chunk.
  - On non-final passes, saves the last `1.5 s` of the combined audio
    as next pass's tail.
  - On `final=True`, clears the tail (no next pass to feed).
- `_transcribe_chunks` wraps each of the three audio streams:
  ```python
  mic_audio = self._apply_overlap("mic", mic_audio, final)
  system_audio = self._apply_overlap("system", system_audio, final)
  audio = self._apply_overlap(f"device:{device_id}", audio, final)
  ```

### Tests (`tests/unit/test_meeting_overlap.py`)

New file with 7 unit tests covering:
1. `_overlap_seconds` default value.
2. First pass: no prior tail; audio returned unchanged.
3. Second pass: prepends previous tail.
4. Third pass: carries tail forward (not the original first tail).
5. `final=True` clears tail.
6. Streams are independent (mic / system / device tails don't bleed).
7. Sub-overlap-length chunks save the whole chunk as tail.

## Verification

```
$ cd /home/karol/dev/HoldSpeak && .venv/bin/python -m pytest tests/unit/test_meeting_overlap.py -q
7 passed in 0.40s

$ .venv/bin/python -m pytest -q   # full HS suite, earlier in session
1809 passed, 21 skipped in 124.65s
```

## Acceptance criteria — re-checked

7 of 8 brackets `[x]` — see [`story-15-overlap-windows.md`](./story-15-overlap-windows.md). The one open bracket is the live-hardware verification (a meeting with a sentence spoken across a 10 s `TRANSCRIBE_INTERVAL` boundary); deferred because the unit tests cover the prepend/save/clear math correctness and the live-hardware test cycle is a non-trivial setup that wasn't completed in the live-tuning window.

## Deviations from plan

- **Audio-level overlap, not segment-level dedup.** Whisper may emit
  the overlapped region's text in the next pass's segments — accepted
  per user direction ("occasional duplicate words at boundaries").
  Segment dedup based on text fingerprinting would be a follow-up
  story.
- **1.5 s tail length** chosen by feel; tunable via the instance
  attribute. Could be lowered to 0.5 s if duplicate-word artifacts
  become noticeable.

## Follow-ups

- Live verification with a real sentence spanning a 10 s boundary;
  capture the resulting transcript segments to show the boundary no
  longer splits mid-sentence.
- Consider segment-level dedup if duplicate-word artifacts surface
  meaningfully.
- VAD-aware cut points (option B in the AskUserQuestion the user
  picked overlap over) remains a future enhancement if overlap
  doesn't fully solve the user's UX concern.
