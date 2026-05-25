# AIPI-4-15 — Overlap windows on transcription passes

- **Project:** aipi-lite (server-side fix; tracked here because the
  user-visible problem surfaced via the AIPI-Lite hardware pass)
- **Phase:** 4
- **Status:** done
- **Depends on:** HS-17-08 (per-segment transcript pushback to LCD)
- **Owner:** karol

## Problem

HoldSpeak's `MeetingSession` transcribes incrementally every
`TRANSCRIBE_INTERVAL = 10` seconds. Each pass takes a fresh chunk of
buffered audio and hands it to Whisper as a standalone blob — Whisper
has zero context from the previous pass. Sentences that span the
10 s boundary get cut at the boundary: the first half ends pass N
with no terminal punctuation, the second half starts pass N+1 fresh.

User feedback 2026-05-10 live tuning: *"I do mind that long sentences
are always cut up… some of our logic is kind of cutting up our input
that we do by speaking while all of this is going on."*

Confirmed in meeting `0f6c3773`'s transcript:
`"stupidly enough that"` landed as its own segment with no closing
punctuation — the user's continuation was in the next pass.

## Scope

### In

**`holdspeak/meeting_session.py`:**
- New instance state on `MeetingSession`:
  - `self._overlap_tail_seconds: float = 1.5`
  - `self._stream_tails: dict[str, np.ndarray] = {}`
- New helper `_apply_overlap(stream_id, audio, final)`:
  - Prepends the previously-saved tail (if any) to the current audio.
  - On non-final passes, saves the last `1.5 s` of the combined audio
    as the next pass's tail.
  - On `final=True`, clears the tail (no next pass to feed).
- `_transcribe_chunks` wraps each of its three streams (mic, system,
  per-device) with `_apply_overlap` using stream ids `"mic"`,
  `"system"`, `f"device:{device_id}"`.

### Out

- Dedup of overlap-region text. The user accepted occasional
  duplicate words at boundaries as the trade-off. Future enhancement
  could fingerprint segment starts against previous pass's segment
  ends.
- Streaming partials (faster-whisper streaming hook). Separate story
  if/when ergonomics demand sub-pass latency.
- VAD-aware cut points (transcribe only up to last silence within
  the past 10 s). Bigger refactor; offered as option B in the live
  AskUserQuestion but user picked overlap windows for speed.

## Acceptance Criteria

- [x] `_overlap_tail_seconds = 1.5` default on `MeetingSession`.
- [x] First pass returns audio unchanged + saves last 1.5 s as tail.
- [x] Second pass prepends the saved tail.
- [x] Tail rolls forward each pass (third pass gets second pass's
  tail, not first pass's).
- [x] `final=True` pass still gets the prepended tail (so the LAST
  sentence isn't cut) but no new tail is saved.
- [x] Streams are independent (mic / system / device:<id> each carry
  their own tail).
- [x] Short chunks (< overlap length) save the whole chunk as tail.
- [x] 7 unit tests in `tests/unit/test_meeting_overlap.py`; all pass.
- [ ] **Live hardware verification deferred** — needs a meeting with
  a sentence spoken across a 10 s `TRANSCRIBE_INTERVAL` boundary on
  the AIPI-Lite. Code-correct; ergonomic-correct pending evidence.

## Notes

- **Why 1.5 s tail?** Whisper's context window benefits from ~1 s of
  preceding audio at a sentence boundary; 1.5 s adds margin for the
  user's pause-pattern. Cost is 1.5 s of duplicate transcription per
  pass — Whisper runtime scales linearly with audio length, so this
  is ~15% extra work per pass. Acceptable.
- **Duplicate-text trade-off.** With overlap, Whisper may emit a
  segment in pass N+1 whose first 1–2 words match the last words of
  pass N's final segment. Accepted as documented user trade-off; the
  durable transcript will have minor word-level duplication at some
  boundaries but no cut-mid-sentence artifacts.
- **Why a HoldSpeak fix, tracked in AIPI-Lite phase 4?** The user-
  visible UX problem (cut sentences flashing on the LCD via HS-17-08)
  was surfaced by the AIPI-Lite hardware pass. The fix lives in
  HoldSpeak's `meeting_session.py` because that's where the chunk
  boundary is. Story is filed here so the AIPI-Lite phase status
  reflects the closure of a hardware-surfaced bug; cross-link from
  HS-17 if/when that phase needs the bookkeeping.
- **`final=True` semantics nuance.** The final pass still gets the
  PREPENDED tail from the previous pass — that's correct, because
  the user's last sentence needs its leading context too. The tail
  is *cleared after* the final pass so subsequent meetings don't
  inherit stale audio.
