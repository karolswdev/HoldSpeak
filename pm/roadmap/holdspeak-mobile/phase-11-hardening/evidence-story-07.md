# Evidence — HSM-11-07 (Bounded windows for single-segment transcripts)

**Date:** 2026-06-21 · **Status:** done

HSM-8-07's chunking only bounded memory when the transcript had *multiple* segments — but
the on-device transcriber emits the whole meeting as **one giant segment** (`segments=1` in
the real-metal 22-min log), and the old windowing kept an oversized segment whole. So a real
hour-long meeting would still produce one over-budget window and overflow the context. This
host-side hardening closes that hole: `windows()` now splits an oversized segment internally
so every pass is genuinely bounded.

## What shipped (`TranscriptWindowing`, RuntimeCore)

- **`splitOversized(_:maxTokens:)`** — replaces any segment over budget with sub-segments
  each ≤ `maxTokens`; within-budget segments pass through untouched. Sub-segments interpolate
  start/end across the parent's span by character offset (first keeps the parent's start), so
  transcript anchoring stays monotonic.
- **`splitText(_:maxTokens:)`** — splits a too-long string preferring **sentence** boundaries
  (`.!?`/newline), then **word** boundaries, then a **hard char cut** for a runaway unbroken
  span. Preserves the original text exactly (slice + per-piece trim).
- **`windows()`** runs `splitOversized` first, so the rest of the (unchanged) grouping logic
  now operates on bounded segments. Public signature unchanged → the app's chunked path
  benefits transparently, no app change.

## Tests (ran)

`swift test` → **201 passed / 6 skipped / 0 failed** (+4 net in `ChunkedExtractionTests`):
a single 100-token unbroken segment → >1 window, **every window ≤ budget**, no text lost;
`splitText` breaks at sentence ends (each piece ends `.`, ≤ budget, coverage preserved);
`splitText` hard-cuts an unbroken span with no text lost; `splitOversized` interpolates
timing monotonically + keeps the parent's start + passes within-budget segments through. The
existing windowing/merge/chunked-extraction tests stay green (no regression).

## Acceptance

- A single oversized segment is **split so every window fits the budget**, not kept whole. ✅
- `splitText` prefers sentence → word → hard-cut, text preserved, each piece ≤ budget. ✅
- `splitOversized` interpolates timing monotonically, keeps the parent start, passes
  within-budget segments through. ✅
- No regression — normal multi-segment transcripts window exactly as before. ✅

## Note

Pure RuntimeCore, host-tested — no device needed. It makes HSM-8-07's "memory flat
regardless of length" real on the *current* transcriber output, and sharpens the eventual
HSM-8-07/8-08 device proof (a real hour-plus meeting now has a path that bounds each pass).
