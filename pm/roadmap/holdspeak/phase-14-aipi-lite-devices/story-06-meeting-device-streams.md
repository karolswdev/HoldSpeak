# HS-14-06 - Meeting Path Accepts Device Streams + Per-Segment device_id

- **Project:** holdspeak
- **Phase:** 14
- **Status:** done
- **Depends on:** HS-14-04
- **Unblocks:** HS-14-08
- **Owner:** unassigned

## Problem

`MeetingRecorder` already returns `(mic_chunks, system_chunks)` —
a dual-stream model with per-segment speaker labels. To accept N
device streams we need to extend that shape: a meeting can be
configured with one or more registered devices contributing
audio, each with its own label, each producing
`TranscriptSegment`s with the device's `id` recorded.

This unlocks the high-value use case: **one AIPI-Lite per
speaker** at a meeting → speaker attribution falls out for free
(no diarization model required).

## Scope

- **In:**
  - `MeetingState`: new field `devices: list[DeviceDescriptor]`
    captured at meeting start.
  - `MeetingRecorder`: accept additional registered devices via
    constructor or `register_stream(device_id)`. Internally,
    own a per-device chunk queue alongside the existing
    `mic_chunks` / `system_chunks`.
  - `_transcribe_chunks`: new keyword arg
    `device_chunks: dict[str, list[AudioChunk]]`. Each device's
    chunks transcribe with the device's label as `speaker` and
    the device's id as `device_id` on each segment.
  - `TranscriptSegment`: add nullable `device_id: str | None`.
    Default `None` for the legacy local-mic + system-audio
    paths.
  - `POST /api/meeting/start` accepts an optional body
    `{devices: [device_id, ...]}` listing which currently-active
    devices participate. Default empty (legacy behavior).
  - Meeting export (`meeting_exports.py`) and history APIs
    surface `device_id` so it round-trips through Markdown /
    JSON.
  - `tests/integration/test_device_meeting_session.py`: runs a
    short meeting with one local-mic stream + one device
    stream, asserts segments are correctly labeled.

- **Out:**
  - Meeting-time UI showing N device streams — phase 16.
  - More than 2 simultaneous devices in one meeting — works
    architecturally; UX/UI polish for 3+ defers.
  - Speaker diarization within a single device's stream —
    not in scope; one device = one speaker by convention.

## Acceptance Criteria

- [x] `MeetingState.devices` field exists and round-trips
  through `to_dict()`.
- [x] `MeetingRecorder` accepts ≥ 1 device stream alongside
  local mic + system audio.
- [x] `TranscriptSegment.device_id` is nullable; legacy paths
  preserve `None`.
- [x] `POST /api/meeting/start {devices: [...]}` registers the
  devices into the active session; an unknown device id
  returns 404.
- [x] Meeting export Markdown shows the speaker label per
  segment, JSON includes `device_id`.
- [x] `tests/integration/test_device_meeting_session.py` green
  with one local + one device source producing distinct
  speaker-labeled segments.
- [x] Existing meeting tests stay green.

## Test Plan

- Unit: `tests/unit/test_meeting_state.py` extended for
  `devices` + `device_id` round-trip.
- Integration:
  `uv run pytest tests/integration/test_device_meeting_session.py`,
  existing
  `uv run pytest tests/integration/test_meeting_*.py`.
- Manual: AIPI-Lite bridge connected with label "Karol";
  `POST /api/meeting/start {devices: ["aipi-1"]}`; speak via
  device; stop meeting; inspect saved meeting JSON for
  `device_id: "aipi-1"` and `speaker: "Karol"` on the device's
  segments.

## Notes

- The `device_chunks` mapping inside `_transcribe_chunks`
  preserves chronological merging by timestamp so the final
  transcript reads in the order things were said, regardless
  of source.
- Bookmarks (`Bookmark` dataclass +
  `MeetingState.get_context_around()`) work without change — a
  device long-press becoming a bookmark is wired in HS-14-07
  (status protocol gives us the channel for buttons-as-events).
- Cross-repo: the AIPI-Lite firmware doesn't change shape for
  this story — the bridge translates ESPHome events into HTTP
  calls.
