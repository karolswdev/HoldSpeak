# HSM-3-04 — Speaker-ready segmentation

- **Project:** holdspeak-mobile
- **Phase:** 3
- **Status:** backlog
- **Depends on:** HSM-3-01, HSM-3-02
- **Unblocks:** HSM-3-05, HSM-6-01
- **Owner:** unassigned

## Problem

Transcription returns text, but the rest of the runtime (persistence,
intelligence, sync) consumes `Segment`s in the Phase-0 contract shape. The
segments must carry timing and a speaker slot so a later diarization step can
attach identities — without diarization being in scope for Track D.

## Scope

- **In:** mapping WhisperKit's output into the Phase-0 `Segment` contract: text,
  start/end timing, and a reserved speaker slot (unassigned at this stage). The
  segmentation boundaries (how a continuous decode is cut into segments) and their
  validation against the `Segment` JSON Schema.
- **Out:** real diarization (assigning a voice to a speaker) — the slot is
  reserved, not populated. Persistence of segments (Phase 4). Display (Phases
  8–9). Any change to the `Segment` contract itself (Phase 0).

## Acceptance criteria

- [ ] Emitted segments validate against the Phase-0 `Segment` JSON Schema with
      zero errors.
- [ ] Each segment carries start/end timing consistent with the audio and a
      speaker slot field (empty/unassigned, but present in the shape).
- [ ] Segment boundaries are deterministic for a fixed input (same audio → same
      segmentation), so downstream tests aren't flaky on boundaries.
- [ ] The mapping is the single place WhisperKit output becomes a `Segment`; no
      other code reshapes transcription into segments.

## Test plan

- Unit: transcribe a fixed audio fixture → assert the segments validate against
  the `Segment` schema and carry timing + a speaker slot; rerun → identical
  segmentation.
- Manual / device: spot-check a real recording's segments for sane boundaries.

## Notes / open questions

- "Speaker-ready" is the charter's word: produce the shape diarization will fill,
  not diarization. If WhisperKit gives no usable per-segment timing for the slot,
  raise it against the Phase-0 `Segment` contract rather than forking the shape.
- Coordinate the speaker slot's exact field with HSM-0-01's catalog so it matches
  what the desktop emits.
