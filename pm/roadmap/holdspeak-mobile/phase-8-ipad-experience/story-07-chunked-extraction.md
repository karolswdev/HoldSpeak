# HSM-8-07 — Chunked extraction for long meetings (map-reduce, length-safe)

- **Project:** holdspeak-mobile
- **Phase:** 8
- **Status:** host-complete (cores + host tests landed; on-device walkthrough deferred per owner — not at the iPad)
- **Depends on:** HSM-8-04 (on-device artifact review + generation), HSM-5-02 (Mode A on-device inference), HSM-6-02 (artifacts), HSM-8-08 (the memory budget that decides *when* to chunk)
- **Unblocks:** hour-plus meetings on-device without growing the context window
- **Owner:** unassigned

## Problem

On-device generation today (HSM-8-04) feeds the **whole transcript** to the model in
a single context (`maxTokenCount`, raised to 16K in HSM-8-06 ≈ ~80 min of speech).
That is fine for short meetings and a calculated bump for medium ones, but it does
not scale: a one-hour meeting is ~10–12K tokens and a two-hour workshop simply will
not fit any context we can afford on the device, because **context size drives the
KV-cache, and the KV-cache is RAM** (see HSM-8-08). Growing the window forever is the
wrong lever — it trades correctness for an OOM. The owner's steer: *"Let's not risk
OOM ever … let's chunk it."*

This story makes long-meeting extraction **length-independent**: split the transcript
into windows that each fit a safe budget, extract per window on-device, then merge the
per-window artifacts into one deduplicated set. Wall-clock and battery scale linearly
with meeting length; **memory stays flat** regardless of how long the meeting ran.

## Scope

- **In:** a pure, host-testable **map-reduce extraction** over a `Transcript`, fully
  on-device —
  (1) **window** the transcript into overlapping segment-aligned chunks sized to a
  token budget (the budget comes from HSM-8-08), never splitting mid-segment, with a
  small overlap so a decision spanning a boundary is not lost;
  (2) **map**: run the existing `ArtifactGenerationEngine` (Mode A `LlamaProvider`)
  over each window for the routed types, carrying each window's `Segment` time range
  so artifacts keep their transcript anchors;
  (3) **reduce**: merge the per-window artifacts into one set — dedup near-identical
  items (same type + near-identical body), preserve provenance (which window/segment
  range), and keep them as `.draft` proposals for the HSM-8-04 review;
  (4) wire it behind the existing **Generate on-device** action so anything longer
  than the single-context budget routes through chunking automatically — the user
  sees streamed progress per window, not a dead multi-minute spinner.
- **Out:** changing the artifact engine (Phase 6) or MIR routing (Phase 7) — chunking
  *drives* them, it does not rebuild them. A hierarchical summarize-then-extract pass
  (a second reduce tier) — parked as a follow-up if simple merge proves lossy. Any
  cloud/off-device path (the air-gapped gate HSM-8-05 forbids it). The memory-budget
  policy itself (that is HSM-8-08; this story consumes its budget number).

## Acceptance criteria

- [ ] A transcript longer than the single-context budget is **windowed into
      segment-aligned chunks** (never mid-segment, with overlap), proven by a unit
      test over a long fixture transcript — windows cover the whole transcript and
      adjacent windows overlap by the configured amount.
- [ ] **Map-reduce produces one merged artifact set**: per-window extraction runs the
      real engine over each window and the results merge into a deduplicated set of
      `.draft` proposals, each retaining its `Segment`-range provenance — host-tested
      against a fake/stub provider so it is deterministic and model-free.
- [ ] **Memory stays flat with length**: the path never holds more than one window's
      context at a time (the provider is sized to the window budget, not the whole
      transcript), so a 2-hour transcript uses the same peak context as a 20-minute
      one. Asserted structurally (the provider's `maxTokenCount` is the budget, and
      windows are bounded by it), and verified on-device in the device walkthrough.
- [ ] **Routed through the real action**: a meeting longer than the budget generates
      via chunking through the existing Generate-on-device button, streaming progress
      per window; a short meeting still uses the single-context fast path (no
      regression). Proven on a physical iPad with a real long meeting.
- [ ] **Fully on-device** — windowing, mapping, and merging are all local; no network,
      so HSM-8-05's air-gapped loop holds at any meeting length.

## Test plan

- Unit (host, model-free): windowing over a long fixture (e.g. 200 segments) yields
  budget-bounded, segment-aligned, overlapping windows covering the whole transcript;
  map-reduce over a **stub provider** that returns one artifact per window merges +
  dedups into the expected set with correct `Segment`-range provenance; the short-path
  vs chunked-path selection picks chunking exactly when the transcript exceeds the
  budget.
- Device: record (or import) a real **hour-plus** meeting on the iPad, Generate
  on-device, and watch it extract per window without OOM, producing a coherent merged
  artifact set in review — folded into the HSM-8-05 air-gapped walkthrough where
  practical.

## Host-complete (2026-06-21)

Cores + host tests landed (PR pending); the on-device walkthrough is the only remaining
acceptance item, deferred per the owner ("not at my iPad — don't consider any iPad gates").

- **`TranscriptWindowing.windows`** (RuntimeCore) — segment-aligned, budget-bounded,
  overlapping windows; never splits a segment; an oversized lone segment is kept whole
  rather than dropped. Host-tested (coverage, overlap, budget bound, empty, oversized).
- **`ArtifactMerge.dedup`** — collapses cross-window duplicates by (type + normalized
  body), keeping the higher-confidence draft, order-stable. Host-tested.
- **`ChunkedExtractor`** — `shouldChunk` decides the path; `generate` runs the real
  `ArtifactGenerationEngine` per window and merges. Host-tested over a fake provider
  (N windows × M types collapse to M artifacts; propose-only `.draft` preserved).
- **App wiring** — `generate()` opens the provider at the HSM-8-08 budget, and a meeting
  that exceeds one window routes through `ChunkedExtractor` with a legible "extracting in
  N passes…" note; a short meeting keeps the single fast streaming pass. The meeting app
  **builds + signs for device** (verified); the on-device long-meeting run is the deferred
  item.
- `swift test` → **182 passed / 6 skipped / 0 failed** (+12 with HSM-8-08).

**Remaining for `done`:** the physical-iPad long-meeting (hour-plus) walkthrough —
extract via chunking with no OOM, coherent merged set in review. Folds into the HSM-8-05
air-gapped walkthrough at the reconvene.

## Follow-up landed — HSM-11-07

This story's windowing originally kept an oversized *single* segment whole (correctness over
budget). But the on-device transcriber emits the whole meeting as one giant segment, so that
exception was the normal case and left the per-pass budget unbounded. **HSM-11-07** (Phase 11)
closed it: `windows()` now splits an oversized segment internally (sentence → word → hard-cut),
so every pass is genuinely bounded on real transcriber output. The public API is unchanged.

## Notes / open questions

- Overlap size is a tuning knob: enough that a decision straddling a boundary is
  captured in at least one window, small enough not to double the work. Default to a
  modest segment overlap; expose it as a constant, not magic.
- Merge/dedup is deliberately simple in v1 (same type + near-identical body). If the
  owner finds duplicates or cross-window contradictions, a hierarchical reduce
  (summarize each window, then extract over the summaries) is the next tier — parked
  here intentionally, not built speculatively.
- This is the desktop's long-meeting story in on-device form. Keep the windowing a
  contract-level operation over `Segment`s so it can ride sync (Phase 10) and stay
  compatible with the desktop's handling.
- Sequencing: HSM-8-08 lands the **budget** (how many tokens is safe on this device);
  this story consumes it. They can ship together, but the budget is the dependency.
