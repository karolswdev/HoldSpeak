# HSM-20-03 — The capture canvas at compact width (the live meeting board)

- **Project:** holdspeak-mobile
- **Phase:** 20
- **Status:** todo
- **Depends on:** 20-01 (`DeskCamera`).
- **Unblocks:** nothing downstream.
- **Owner:** unassigned

## Problem

The live capture surface (`LiveCaptureCanvas`, `MeetingCaptureApp.swift:1137–1186`) assumes a wide
board: free-drag utterance bubbles, a floating recorder orb, and a tack zone. It is the **least
broken** surface — the root is a `GeometryReader`, the tack zone is already `min(264, size.width −
72)`, and the utterance stream is an unconstrained `VStack` — but free-drag bubbles and a floating
recorder are awkward one-thumb on a 390pt phone.

## The design

1. **Verify, then adapt — do not rewrite.** This canvas already scales; confirm it at 390pt first
   (screenshot the seeded board on the iPhone sim). Use it as the reference for the lane's sizing
   math elsewhere.
2. **Lane: a docked recorder, not a floating orb.** On `camera == .lane`, dock the recorder to a
   persistent bottom bar (thumb zone) instead of a free-floating orb; the live transcript stream
   fills the column above it (it already flows top-to-bottom). The tack zone stays centered and
   scales (it already does).
3. **Wrap any chip rows.** The footer/status chips and any horizontal affordance must wrap or
   scroll at 390pt (reuse the `FlowChips`/flow-layout pattern, handover §4f) — no clipped row.
4. **Pinning survives.** The drag-to-tack "mark this moment" gesture (what feeds MIR) must still
   work one-thumb; if free-drag is awkward, offer a tap-to-tack affordance on each bubble as the
   lane equivalent, but **do not remove pinning** (it is a load-bearing capability, not decoration).
5. At `.wide`/`.narrow` the canvas renders exactly as today.

## Scope

- **In:** the lane verification + the docked recorder bar; wrapped chip rows; a one-thumb tack
  affordance if free-drag proves awkward at 390pt.
- **Out:** the desk lane (20-02); forms/teleprompter (20-04).

## Proof

- iPhone sim: the capture board fits 390pt, the recorder is docked, chips wrap, a moment can be
  tacked one-thumb.
- `swift test` + both sim builds green. Device walk = 20-05.
</content>
