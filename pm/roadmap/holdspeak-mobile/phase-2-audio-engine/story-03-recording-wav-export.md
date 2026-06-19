# HSM-2-03 — Recording + WAV export (16 kHz mono PCM)

- **Project:** holdspeak-mobile
- **Phase:** 2
- **Status:** done
- **Depends on:** HSM-2-01, HSM-2-02
- **Unblocks:** HSM-2-04, HSM-3-01
- **Owner:** unassigned

## Problem

A captured `AudioChunk` stream is ephemeral. The runtime needs a durable
recording on disk and a WAV export in exactly the format the Phase-3 transcriber
(WhisperKit) consumes — 16 kHz mono PCM. If the export format drifts (hardware
rate, stereo, float32), every downstream transcription pays for it.

## Scope

- **In:** writing the captured stream to an on-disk recording; exporting a valid
  WAV file at 16 kHz mono PCM (LEI16); a re-read/verify step that confirms the
  written file's header, sample rate, channel count, and bit depth. The on-disk
  location + naming convention (handoff to Phase-4 persistence noted, not built).
- **Out:** associating the recording with a durable `Meeting` row (Phase 4).
  Compressed formats (the desktop import path handles those; mobile capture is
  PCM). Transcription (Phase 3). Any UI.

## Acceptance criteria

- [ ] A recording session produces a WAV file that re-reads as **16 kHz, mono,
      PCM 16-bit** — asserted by parsing the file header, not by trusting the
      writer config.
- [ ] The export matches the transcriber contract byte-for-format (the same
      params Phase 3 expects), so no resample happens downstream.
- [ ] A recording of known duration produces the expected sample count (no
      truncation/padding drift).
- [ ] The recordings directory + naming convention is documented and its Phase-4
      handoff is noted.

## Test plan

- Unit: record a fixed-length synthetic/captured buffer → export → re-parse the
  WAV header and assert rate/channels/depth/sample-count.
- Manual / device: record a short clip on a Tier-1 device, export, and confirm it
  transcribes cleanly once Phase 3 exists (forward check, noted).
- Integration: n/a here (the 1-hour run is HSM-2-04).

## Notes / open questions

- Pin the canonical format here once; the converter that reaches it lives in the
  capture seam (HSM-2-01/02) per this phase's decisions.
- Keep the writer streaming (don't buffer the whole recording in memory) so the
  1-hour gate (HSM-2-04) isn't bottlenecked by the export path.
