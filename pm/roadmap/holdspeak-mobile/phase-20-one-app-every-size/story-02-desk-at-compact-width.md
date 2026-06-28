# HSM-20-02 — The desk at compact width (the lane + the migrating pull-out)

- **Project:** holdspeak-mobile
- **Phase:** 20
- **Status:** todo — the heart of the phase (the signature device moment lives here).
- **Depends on:** 20-01 (`DeskCamera` + `laneWidth`).
- **Unblocks:** nothing downstream; it is the centerpiece.
- **Owner:** unassigned

## Problem

`DioStage` is the front door on device, and it is built for the wide diorama:
absolute-positioned primitives (`positions[id]`, `DeskDioramaStage.swift:2924`), drag-to-arrange,
a right-edge intelligence pull-out (`DioPullout`, `:1200`/rendered `:3197`), and a stack of
fixed-width dim-scrim overlays. On a 390pt iPhone the diorama does not fit, the 380pt panels
overflow, and the scrim overlays are the "modal hells" the owner rejects.

## The design

Follow `EXPERIENCE-VISION-2026-06-27.md:120–153` (§4.3) and the lane mock at line 131.

1. **The `.lane` card column** — a NEW layout engine gated on `camera == .lane` (the vision is
   explicit this is a real renderer, not a free reflow): a single thumb-reachable column of
   full-width `.signalCard` rows (crisp glyph @44pt, title, `CASSETTE · 3 decs` subtitle, chevron),
   a sticky **zone chip rail** (`‹ ●meet ●models ●kb ●notes ›`), a slim header (sync pill +
   Connect), and an accent **FAB** (New Note/KB/Zone). At `.wide` the diorama renders exactly as
   today — the two layouts branch on the camera.
2. **Nothing is destroyed.** The lane sorts by recency + zone; `positions[id]` is **never cleared**
   when entering lane, and rotating back to `.wide` restores the exact hand-arranged desk. (Verify:
   set positions on wide, rotate to lane, rotate back — identical arrangement.)
3. **The migrating pull-out (the signature moment).** Tap a row → the same `DioPullout` content
   (already `maxWidth/maxHeight: .infinity`) **rises from the bottom edge** as a hand-built offset
   container over a transparent catcher (NOT a `.sheet`), with a grab handle. At `.wide`/`.narrow`
   it enters from the right edge as today. Animate the entry edge change on a spring so that, in
   iPad split-view, dragging the multitasking divider visibly migrates the pane right→bottom in
   real time. **Only the entry edge + grab handle change by camera; the content is identical.**
4. **Reframe the scrim overlays** (the modal-hells list, handover §4c) for lane: the in-world
   editors (`DioInlineNoteCard`/`KB`/`ConnectCard`) already lift without a scrim — extend that
   pattern; the action sheets (`DioSendCard`/`DioActSheet`/`DioRunTargetSheet`/`DioRouteSheet`)
   become the same hand-built rising sheet, clamped via `laneWidth`. No `Color.black.opacity` dim
   toward a fixed card on lane.
5. **Clamp the fixed cards** with `laneWidth` (handover §4b): the 380/304/288/296 hard widths and
   the 440/460/480 `maxWidth`s.
6. **Cross-desk drag degrades to the twin.** The lane drops cross-desk drag-to-route (impossible
   one-thumb) and leans on the already-shipping long-press "Route this to AI" twin — an INVARIANT
   that survives the reflow, not a new feature.

## Scope

- **In:** the lane card column + zone chip rail + slim header + FAB; the pull-out bottom-edge
  migration on a spring; reframing the desk scrim overlays as in-world/rising sheets; clamping the
  fixed desk cards; arrangement-preservation on rotate.
- **Out:** `LiveCaptureCanvas` (20-03); the connect/settings/teleprompter screens (20-04); the
  agent/chain editors in `DeskAgents.swift` (20-04 unless trivially clamped here).

## Proof

- iPhone sim: the lane column matches the vision mock; the pull-out rises from the bottom.
- iPad sim split-view: the pull-out migrates right→bottom on the divider drag (capture it).
- Rotate lane↔wide: arrangement identical.
- `swift test` + both sim builds green. Device walk = 20-05.
</content>
