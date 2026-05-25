# HS-17-13 — Transcript Noise Filter for Device LCD Pushback

- **Project:** holdspeak
- **Phase:** 17
- **Status:** done
- **Depends on:** HS-17-08 (per-segment pushback — adds the surface this filter cleans)
- **Unblocks:** —
- **Owner:** karol

## Problem

After HS-17-08 shipped (per-segment transcript pushback to the AIPI-Lite LCD), live verification 2026-05-10 surfaced cosmetic noise: the AIPI-Lite LCD flashed `Me: ... ... ... ... ...` and `Remote: You` segments alongside the user's actual speech.

The `Me:` / `Remote:` legs are HoldSpeak's host-side audio sources (laptop's mic + system audio loopback). When the user attaches an AIPI-Lite device to a meeting, all three legs (mic, system, device) keep transcribing in parallel. Whisper has known hallucination behavior on low-amplitude / silent audio:

- Outputs literal `...` (periods) from silence.
- Hallucinates lone words like `You`, `Yeah`, `Thanks for watching!`, `Subscribe to my channel!` — artifacts of its YouTube-heavy training data.
- Outputs repeated single words (`you you you`, `the the`) from noisy fragments.

These segments are real `TranscriptSegment` objects with non-empty `text`, so they pass HS-17-08's existing emptiness check. They land on the LCD, eating attention from real content.

User feedback 2026-05-10: filter them out so the device shows only meaningful transcript content.

## Scope

### In

- New helper `is_likely_hallucination(text: str) -> bool` in `holdspeak/device_status.py`:
  - Returns True for empty / whitespace-only text.
  - Returns True for all-punctuation text (`...`, `…`, `,,,`).
  - Returns True for the narrow single-word artifacts currently proven noisy enough to suppress/ack (`you`, `uh`, `um`, `the`).
  - Returns True for repeated-single-word patterns (`you you you`).
  - Returns True for known short-phrase hallucinations (`thanks for watching`, `subscribe to my channel`, `please subscribe`, `like and subscribe`).
- `push_segment_to_devices` consults the filter:
  - pure silence / punctuation-only text skips LCD pushback;
  - word-level hallucinations push a short `{speaker}: …` acknowledgement so stale device text is replaced;
  - real meeting content passes through unchanged.
- Unit tests: parametrized over each filter class (empty, punctuation-only, single-word artifacts, repeated, short phrases) + counter-examples that should NOT be filtered (long sentences containing those words, real content).
- Update existing tests for `push_segment_to_devices` that assumed empty-text segments push — now they don't push (no-op).

### Out

- Filtering at the `MeetingSession` level (segment never gets stored). Out of scope — keeps the durable transcript intact; only the LCD pushback is opinionated about cosmetic noise.
- Configurable filter lists (env var, runtime config). Hard-coded for v1. Revisit if users hit false-positive complaints.
- Machine-learning-based "is this a hallucination?" classifier. Way too much for what's effectively a regex.
- Filtering segments by speaker leg (e.g., always filter system-audio segments). Could be a HS-17-14 followup, but the current text-based filter catches most cases without per-leg discipline.

## Acceptance Criteria

- [x] `is_likely_hallucination(text)` implemented in `holdspeak/device_status.py`. Returns True for: empty, whitespace-only, all-punctuation, narrow single-word artifacts (case-insensitive), repeated-word patterns, known short hallucinations. Returns False for real meeting content.
- [x] `is_pure_silence(text)` implemented to split no-audio cases from word-level hallucinations.
- [x] `push_segment_to_devices` consults the filter; pure silence causes zero broadcasts and word-level hallucinations broadcast `{speaker}: …` as an acknowledgement.
- [x] Unit tests added: parametrized over each filter class and counter-examples.
- [x] Existing tests updated (empty-text test now asserts no push).
- [x] Live verification 2026-05-10 established the noisy LCD problem; automated tests now lock the filter/ack behavior.
- [x] `docs/DEVICE_PROTOCOL.md` notes the filter (servers may drop transcript segments matching common Whisper hallucinations from device pushback — durable transcript unaffected).

## Test Plan

- **Unit:** parametrized tests over each filter class.
- **Integration:** none needed — the filter is a pure function applied inside `push_segment_to_devices`, already covered by HS-17-08's integration.
- **Manual:** AIPI-Lite + meeting + brief silence (host mic on but no speaking); confirm LCD doesn't flash `...` / `You` / etc.

## Notes

- **Case-insensitive** for word matching to catch `You` / `you` / `YOU` from Whisper's varying capitalization.
- **Strip trailing punctuation** before matching (`you.` and `you` should both match).
- **Whisper's hallucination set is not exhaustive.** This story ships the well-known classics; future-us can extend the list when new hallucination patterns surface.
- **Why not filter at MeetingSession** — the durable transcript should preserve everything Whisper said, even if it's hallucination. Researchers / debuggers might want to see exactly what Whisper emitted. The LCD is opinionated UX; the transcript is canonical record.
