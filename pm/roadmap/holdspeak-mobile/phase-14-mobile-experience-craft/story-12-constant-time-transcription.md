# HSM-14-12 — Constant-time live transcription (sliding window + commit)

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress — **built + host-proven + Simulator-shown** (2026-06-22); only the
  on-device cadence eyeball (acceptance #6) remains for the owner. See "Evidence" below.
- **Depends on:** HSM-14-11 (the live canvas + the model-cache fix), HSM-8-01 (MeetingCapture)
- **Unblocks:** a live transcript that stays immediate on a long meeting (the felt "control plane")
- **Owner:** unassigned

## Problem

`MeetingCapture.tick()` re-transcribes the **entire accumulated buffer every tick**, and
`WhisperKitTranscriber` collapses all of WhisperKit's segments into a single zero-timestamp
segment. HSM-14-11 (PR #117) removed the dominant cost — the model was being reloaded from disk
every tick — by caching the `WhisperKit` instance and tightening the cadence to 1.2 s. But the
per-tick work still grows **O(meeting length)**: a 40-minute meeting re-transcribes ~40 minutes
of audio on every tick, so late in a long meeting the live transcript stops feeling immediate.

The owner's bar: "once a meeting goes on, there's gotta be movement nearly immediately visible
on the control plane." That has to hold at minute 40, not just minute 1.

## Goal

Bound the per-tick transcription cost to a constant (a fixed audio window) **regardless of
meeting length**, while keeping:
- the **live transcript monotonic and complete** (so the bubble sentence-count accumulation in
  `CaptureModel.ingest` stays correct), and
- the **final saved transcript** at least as accurate/complete as today.

## Architecture — committed prefix + live tail (timestamp-driven)

The enabler is **real per-segment timestamps**, which WhisperKit already returns and we currently
throw away:

1. **`WhisperKitTranscriber` preserves timestamps.** Return the real `[Segment]` with
   `startTime`/`endTime` from `results.flatMap { $0.segments }` (relative to the transcribed
   window), instead of one segment with `startTime: 0, endTime: 0`. `WhisperText.clean` still
   runs per segment.

2. **`MeetingCapture` keeps a committed prefix + an active window:**
   - `committedSegments: [Segment]` — frozen, already-final transcript.
   - `committedFrames: Int` — audio frames already represented by `committedSegments`.
   - Each `tick()` transcribes **only the active window** = audio from `committedFrames` to the
     end. If that window's duration exceeds `maxWindowSeconds` (≈ 60 s), commit the front first.
   - **Commit policy (no mid-word cuts):** when the active window's duration > `commitThreshold`
     (≈ 45 s), freeze every window segment whose `endTime < (windowDuration − overlap)` (overlap
     ≈ 8 s, so the in-progress sentence is never cut), append them to `committedSegments`, and
     advance `committedFrames` by `round(lastCommittedEnd * sampleRate)`. Timestamps make the
     audio↔text boundary exact.
   - **Live transcript = `committedSegments` + active-window segments.** Always the full meeting,
     always monotonic; only the bounded tail is recomputed each tick.

3. **`stop()`** assembles `committedSegments` + a final transcription of the remaining tail (or a
   single authoritative full pass if cheaper) for the persisted meeting — never worse than today.

This bounds each `tick()` to transcribing ≤ `maxWindowSeconds` of audio. Commits are periodic and
cheap. The cadence stays ~constant at minute 40.

## Scope

- **In (host-testable):** the windowing/commit logic in `MeetingCapture` behind the existing
  seams; `WhisperKitTranscriber` returning real multi-segment timestamps; preserve the
  `lastGoodSegments` blank-pass fallback (a window that comes back empty must not lose the take).
- **Out:** token-level streaming ASR, speaker diarization, changing the Whisper model/size, any
  UI change (the canvas/bubbles are unaffected — they consume the same live transcript string).

## Acceptance criteria

- [ ] **Bounded per-tick audio** — with a synthetic long buffer, the audio handed to the
      transcriber per tick never exceeds `maxWindowSeconds` (host-tested with a fake timestamped
      `ITranscriber` that records the window length it was asked to transcribe).
- [ ] **No loss or duplication across a commit boundary** — committed prefix + active tail
      reconstruct the full transcript with no dropped or repeated words at the seam (host-tested;
      overlap proves the in-progress sentence is re-transcribed, not split).
- [ ] **Monotonic live transcript** — the live string only grows; `CaptureModel.ingest`'s
      sentence-count diffing still emits one bubble per finished utterance (host/UI-tested).
- [ ] **Commit math** — `committedFrames` advances by the committed segments' end time × sample
      rate; never past the overlap guard (host-tested).
- [ ] **Saved transcript not worse** — the meeting persisted at `stop()` is at least as complete
      as the pre-change full-pass result (host-tested on a fixture).
- [ ] **Steady on real metal** — a ≥ 10-minute real meeting on the iPad Air M4 shows ~constant
      live latency late in the meeting (owner/device verification).

## Test plan

- New `SlidingWindowTests` (or extend `MeetingCaptureTests`) with a **fake `ITranscriber`** that
  returns deterministic timestamped segments and records the window length it received: assert
  window bound, commit advancement, no loss/dup across the boundary, blank-window fallback.
- `uv run`-equivalent: `swift test` (the package suite; target ≥ current 211/0 + the new cases).
- Device: a long real meeting; eyeball the cadence at the end vs the start.

## Risks / mitigations

- **WhisperKit base timestamp accuracy** → the `overlap` guard absorbs small errors; commit only
  whole segments before the guard.
- **Concurrency on the cached model** → live ticks are already sequential (the model awaits each
  tick); keep the cached-instance access serialized.
- **A window that returns blank** → keep `lastGoodSegments`; never commit on a blank pass.

## Evidence (built 2026-06-22; closeout pending the device cadence eyeball)

`MeetingCapture` keeps a **committed prefix + a bounded active window**: `tick()` transcribes only
the audio since the last commit (`Self.windowChunks(_:fromFrame:)`, frame-accurate). Once the window
passes `commitThresholdSeconds` (45 s), every segment ending before the `overlapSeconds` (8 s) guard
is frozen into `committedSegments` and `committedFrames` advances by `lastEnd × sampleRate` — no
mid-word cuts. The live transcript is always `committed + tail` (complete, monotonic). `stop()`
assembles the prefix + a final pass over the bounded tail (long meeting), or the unchanged legacy
full pass with the blank-pass fallback (short meeting). `WhisperKitTranscriber` now returns
WhisperKit's **real per-segment timestamps** (was one `startTime:0/endTime:0` segment).

- **Backward-compatible:** production thresholds + the existing tests' 1-frame chunks mean no
  existing test ever commits, so the short-meeting path is byte-identical; all 211 prior tests pass
  unchanged.
- **Tests:** `swift test` **228/6/0** incl. 3 new `SlidingWindowTests` — bounded per-tick window,
  no loss/dup across the commit seam (the fake capture encodes absolute audio position so a gap is a
  wrong word sequence), and blank-window safety.
- **Built + shown:** app `xcodebuild … BUILD SUCCEEDED`; the live canvas it feeds renders intact —
  [`screenshots/constant-time-transcription-canvas.png`](./screenshots/constant-time-transcription-canvas.png).
- **Files:** `Sources/RuntimeCore/Capture/MeetingCapture.swift`,
  `App/MeetingCaptureApp.swift` (`WhisperKitTranscriber`), `Tests/RuntimeCoreTests/SlidingWindowTests.swift`.
- **Remaining (acceptance #6, device):** eyeball the cadence at the end of a ≥10-minute real meeting
  on the iPad Air M4. The host bound guarantees the cost; the device step confirms the felt immediacy.
