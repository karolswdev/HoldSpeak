# HSM-11-07 — Bounded windows for single-segment transcripts (intra-segment split)

- **Project:** holdspeak-mobile
- **Phase:** 11
- **Status:** done
- **Depends on:** HSM-8-07 (chunked extraction), HSM-8-08 (the budget)
- **Unblocks:** chunking that actually bounds memory on real on-device transcripts
- **Owner:** unassigned

## Problem

HSM-8-07's chunking is **segment-aligned** and kept an oversized segment *whole*
("correctness over the budget for the pathological case"). But that pathological case is
the **normal** case on-device: the HSM-8-01 windowed transcriber emits the **whole meeting
as one giant segment** (a known limitation until realtime segmentation). So for a real
hour-long meeting (~9k tokens in one segment), `windows()` produced a single window holding
the entire transcript — which overflows the model context exactly the way HSM-8-07 was
built to prevent. The "never gamble on RAM" guarantee had a hole precisely where it
mattered, surfaced by the real-metal 22-min run (`segments=1`).

This story closes that hole: when a single segment exceeds the window budget, split it
**internally** so the windows are genuinely bounded regardless of how the transcript was
segmented.

## Scope

- **In:** `TranscriptWindowing` (RuntimeCore) gains intra-segment splitting, run inside
  `windows()` before grouping —
  (1) **`splitOversized`**: replace any segment whose text exceeds `maxTokens` with
  sub-segments each ≤ `maxTokens`; within-budget segments pass through untouched;
  (2) **`splitText`**: split a too-long string preferring **sentence** boundaries
  (`.!?`/newline), falling back to **word** boundaries, then a **hard char cut** for a
  runaway unbroken span — preserving the original text exactly (slice + trim);
  (3) **timing**: sub-segments interpolate start/end across the parent's span by character
  offset, so transcript anchoring stays monotonic and the first sub-segment keeps the
  parent's start.
- **Out:** realtime/streaming segmentation in the transcriber itself (HSM-3-02 — a
  different layer; this is the consumer-side safety net). Semantic/topic chunking. Any
  device-specific code — this is pure, host-tested.

## Acceptance criteria

- [x] A single oversized segment is **split so every window fits the budget** (not kept
      whole) — host-tested (`windows([big], maxTokens:10)` → >1 window, each ≤ budget, no
      text lost).
- [x] `splitText` **prefers sentence boundaries**, falls back to words, then hard-cuts an
      unbroken span — host-tested, each piece ≤ budget, text preserved.
- [x] `splitOversized` **interpolates timing monotonically** and keeps the parent's start;
      within-budget segments pass through unchanged — host-tested.
- [x] No regression: normal multi-segment transcripts window exactly as before (the
      existing `ChunkedExtractionTests` stay green).

## Test plan

- Unit (host, model-free): the four cases above + the existing windowing/merge/chunked-
  extraction suite. `swift test` → **201 passed / 6 skipped / 0 failed** (+4 net).

## Notes / open questions

- This makes HSM-8-07's promise real on the *current* transcriber output (one segment). It
  does NOT need the device — it's a deterministic RuntimeCore change — but it does sharpen
  the eventual HSM-8-07/8-08 device proof (a real hour-plus meeting now has a path that
  actually bounds each pass).
- Sentence detection is deliberately simple (`.!?`/newline). Abbreviations ("e.g.") may
  cut slightly early; harmless for extraction, and the hard-cut fallback guarantees the
  budget is never exceeded.
