# Evidence — HSM-8-03 (Transcript linking)

**Date:** 2026-06-21 · **Status:** done

A note (or a one-gesture mark) remembers *when* it was taken — anchored on the transcript
moment, not on rendered text that re-flows — so it resolves to the same segment across
re-render and sync, in both directions.

## What shipped

- **`TranscriptLinker` (RuntimeCore):** a `TranscriptLink` anchors on a `Segment` **start
  time** (the Phase-0 contract's stable timing). `markMoment(at:)` flags a moment with no
  note (the one-gesture mark — raw material for HSM-8-06); `linkNote(page:at:)` binds a
  notebook page to a moment. `resolve(_:in:)` returns the segment whose window contains the
  anchor, else the nearest by start — and `nil` when there's no transcript yet (graceful,
  no dangling link). `links(atSegmentIndex:in:)` is the **bidirectional** lookup (from a
  moment to the notes/marks taken there). Links persist per meeting via a `LinkStore` seam.
- **The app:** a **★ Mark this moment** button on the capture screen during recording
  (with a live count), backed by a `FileLinkStore`; the meeting detail shows a **MARKED
  MOMENTS** list and **taps jump** to the resolved transcript segment
  (`ScrollViewReader`). Bound to the meeting via `MeetingCapture.currentID`.

## Tests (ran)

`swift test` → **154 passed / 6 skipped / 0 failed** (+8 `TranscriptLinkerTests`):
resolves to the containing segment; **stable across re-render** (a fresh linker over the
same store + segments resolves identically); nearest-snap past the end; **bidirectional**
moment→notes; **no-transcript degrades to `nil`, never crashes**; mark vs note-link;
persist + reload; save-failure propagates.

## Acceptance

- **Making a note/mark records the transcript moment** as a structured anchor (a
  `Segment` start time) — host-proven; the app's Mark button creates one live.
- **Tap a link → jump to the moment; bidirectional** — the detail's marked-moments list
  taps-to-scroll to the resolved segment; `links(atSegmentIndex:)` gives the reverse.
- **One-gesture "mark this moment"** — the ★ button creates a linked anchor with no note,
  at speed.
- **Survives reload + re-render** — anchored on `Segment` timing, not text offsets
  (`testStableAcrossReRender`); links persist via the `LinkStore` seam.
- **No-transcript degrades gracefully** — `resolve` returns `nil` over empty segments; a
  mark made before a transcript is stored and simply unresolved until segments arrive.

## Real-metal + a known limitation

The linking app **builds + installs + launched on the physical iPad Air M4**; the Mark
button + the detail jump run there. Note: HSM-8-01's windowed transcriber currently yields
a single clean segment (`startTime 0`), so on-device marks resolve to that one segment
until **HSM-3-02** (realtime/per-utterance segmentation) gives the transcript granular
timing — at which point the *same* anchor logic (proven here over properly-timed segments)
makes the jumps fine-grained. The anchor is deliberately Segment-timing-based so nothing
changes when that lands.
