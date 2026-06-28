# Evidence — HSM-20-03 — The capture canvas at compact width

**Date:** 2026-06-27. **Branch:** `holdspeak-mobile/phase20-03-capture-canvas`.

## Finding: it was the least-broken surface, as the handover predicted

`LiveCaptureCanvas` (`MeetingCaptureApp.swift:1137`) is `GeometryReader`-rooted, the tack zone is
already `min(264, width − 72)`, the utterance stream is an unconstrained `VStack`, and the floating
recorder defaults to `RecorderDock.bottom` (`RecorderLayout.swift:18`) — bottom-center, thumb-reach.
Verified at 390pt in the iPhone-17-Pro simulator: the bubbles flow full-width, the recorder sits
docked at the bottom with its controls fitting the width, the live caption and a tacked moment
render correctly. No fixed-width overflow, no clipped chip rows. So the work here was small and
targeted, not a rewrite.

## What shipped

- **A one-thumb tack affordance.** Free-drag-to-the-tack-zone is awkward one-handed on a phone, so
  `LiveBubbleView` gained an `onTack` closure and a **"Tack this moment"** context-menu action
  (alongside the existing Add-to-notes / Copy). It calls `model.pin(b, at: tackZone.center, ...)` —
  the same MIR-steering tack as a drop-on-target, just reachable with one thumb. The drag path is
  untouched (still works); this is an addition, not a replacement (pinning is load-bearing, never
  removed).
- **A simulator screenshot seed** `HS_DEMO_CAPTURE=1` (at the root `WindowGroup`, matching the
  existing `HS_DEMO_*` entries) opens the capture canvas straight, so the compact-width board can be
  screenshot without a mic or taps.

The docked recorder, the scaling tack zone, and the full-width stream were already correct — this
story verified them and added the one-thumb tack. At `.wide`/`.narrow` the canvas renders exactly as
before (the changes are camera-agnostic — a context-menu item + a debug seed).

## Proof

- iPhone-17-Pro sim `xcodebuild`: **BUILD SUCCEEDED.** `swift test`: **381 passed, 0 failures.**
- `screenshots/2003-capture-canvas-lane.png` — the capture board at 390pt: full-width utterance
  bubbles, the live caption, the recorder **docked at the bottom** with its stop/timer/waveform/
  controls fitting the width, a tacked moment at the foot.

Device walk = **HSM-20-05** (the gate).
