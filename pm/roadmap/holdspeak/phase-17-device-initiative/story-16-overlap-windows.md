# HS-17-16 — Overlap windows on `MeetingSession._transcribe_chunks`

- **Project:** holdspeak
- **Phase:** 17
- **Status:** done
- **Depends on:** HS-17-08 (per-segment transcript pushback)
- **Companion:** AIPI-4-15 on the AIPI-Lite side
- **Owner:** karol

## Problem

`MeetingSession.TRANSCRIBE_INTERVAL = 10` seconds. Every 10 s, a pass
drains the audio buffer and hands the chunk to Whisper as a fresh
standalone blob — no context from the previous pass. Sentences that
span the 10 s boundary get cut at the boundary: first half ends pass N
with no terminal punctuation, second half starts pass N+1 fresh.

Surfaced via the AIPI-Lite hardware tuning session 2026-05-10. User:
*"I do mind that long sentences are always cut up… some of our logic
is kind of cutting up our input that we do by speaking while all of
this is going on."*

## Scope

### In

- New instance state on `MeetingSession`:
  - `self._overlap_tail_seconds: float = 1.5`
  - `self._stream_tails: dict[str, np.ndarray] = {}`
- New helper `_apply_overlap(stream_id, audio, final)`:
  - Prepends previous-pass tail.
  - On non-final passes: saves last `1.5 s` as next pass's tail.
  - On `final=True`: clears tail.
- `_transcribe_chunks` wraps mic / system / per-device audio through
  the helper with stream ids `"mic"`, `"system"`,
  `f"device:{device_id}"`.

### Out

- Segment-level dedup of overlap-region text. Accepted per user
  direction ("occasional duplicate words at boundaries"). Future
  enhancement.
- VAD-aware cut points (transcribe only up to last silence). Offered
  as alternative; user picked overlap windows.

## Acceptance Criteria

- [x] `_overlap_tail_seconds = 1.5` default.
- [x] First pass: audio unchanged + tail saved.
- [x] Second pass: prepends previous tail.
- [x] Third pass: rolls tail forward (gets pass-2 tail, not pass-1).
- [x] `final=True`: prepends tail but clears it after.
- [x] Streams independent (mic/system/device:<id> don't share tails).
- [x] Tiny chunks (< overlap length) save the whole chunk.
- [x] 7 unit tests in `tests/unit/test_meeting_overlap.py`.
- [ ] **Live hardware verification deferred** — needs a sentence
  spoken across a 10 s pass boundary on an AIPI-Lite. Math correctness
  confirmed via unit tests; live ergonomics evidence pending.

## Notes

- **Filed under both phases** (HS-17 here + AIPI-4-15 on the bridge
  side) because the user-visible UX problem surfaced via the device
  LCD, and the fix code lives in HoldSpeak. The cross-link keeps
  the AIPI-Lite phase status reflective of the closure.
- **Why 1.5 s?** Whisper benefits from ~1 s of preceding audio at a
  sentence boundary; 1.5 s adds margin for pause patterns. Cost is
  ~15% more Whisper compute per pass (audio length scales linearly).
  Acceptable.
- **Trade-off.** Whisper may emit the overlapped region's text in
  pass N+1's segments — minor word-level duplication at some
  boundaries, but no cut-mid-sentence artifacts.
