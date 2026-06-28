# Evidence — HSM-20-02 — The desk at compact width (the lane + the migrating pull-out)

**Date:** 2026-06-27. **Branch:** `holdspeak-mobile/phase20-02-desk-lane`.

## What shipped

The desk reflows by camera: the lit diorama on iPad (`.wide`/`.narrow`), a one-thumb card column
on iPhone (`.lane`). All in `DeskDioramaStage.swift`, gated on the `DeskCamera` from 20-01.

- **The lane card column** (`laneColumn(_:_:)`, new): a sticky kind-filter chip rail (`All` + a chip
  per present bucket — Meetings / Notes / KB / Agents / Tools / Play, dynamic so a filter is never
  empty) over a scroll of full-width rows. Each row (`DioLaneRow`) is glyph @44 (`DioLaneGlyph`,
  the same sprite-vs-SF-symbol logic as `DioHeroVisual`) · title · `BADGE` · subtitle · chevron;
  zones get their own divable rows (`DioLaneZoneRow`). Tapping a row calls the exact same
  `tapPrimitive` the canvas uses (notes/KBs edit in-world; everything else opens the pull-out).
- **Nothing is hidden between sizes.** The lane lists `members()` (content + tools + agents +
  chains) plus `childZones()` — everything the wide desk shows. `positions[id]` is never touched, so
  rotating back to `.wide` restores the exact hand-arranged diorama.
- **The migrating pull-out (the signature moment).** The same `DioPullout` content (it is
  `maxWidth/maxHeight: .infinity`) enters from the **right edge** on iPad and **rises from the
  bottom edge** on iPhone, with a grab handle, over a **transparent catcher (no dim scrim)**.
  Animated on `dockSpring` keyed to `camera.isLane`, so dragging the iPad split-view divider into
  compact migrates the pane right→bottom live. Only the entry edge + grab handle change by camera.
- **The accent FAB** carries New Note / New KB / New Zone (the create cluster lives in `level`,
  which the lane replaces) via a native `Menu` — not a dimmed sheet. Qlippy tucks up the right edge
  on the lane so it clears the FAB.
- **In-world note/KB editing on the lane** (the editors live in `level`): rendered as a shared
  lifted card over a transparent catcher, clamped via `camera.cardWidth`.
- **Clamped fixed cards** so nothing overflows a small (375pt) iPhone: `DioConnectCard` and
  `DioZoneEditor` gained a `maxW` param the caller sets to `camera.cardWidth(380, in: w)`.
- **Sim verification hook** `HS_DESK_OPEN=1` (matching the existing `HS_DESK_*` debug seeds) seeds
  a deliverable and opens it, so the risen pull-out can be screenshot in the simulator.

## Deferred to HSM-20-04 (honest scope)

The dim-scrim **action sheets** (`DioSendCard` / `DioActSheet` / `DioRunTargetSheet` /
`DioRouteSheet`) and the agent/chain editors keep their scrims for now; story 20-04 explicitly owns
reframing them as the hand-built rising sheet ("if not already reframed in 20-02, clamp +
rising-sheet them here"). Their `maxWidth: 440/460/480` already caps below 390pt so they fit; the
remaining work is the no-modal reframe, not an overflow fix.

## Proof

- `swift test`: **381 passed, 8 skipped, 0 failures.**
- iPhone-17-Pro sim + iPad sim `xcodebuild`: **BUILD SUCCEEDED.**
- `screenshots/2002-desk-lane.png` — the iPhone lane: chip rail (All/Notes/Tools), full-width rows
  (Note, Slack/Webhook/GitHub connectors) with glyph + badge + subtitle, the accent FAB, Qlippy
  tucked up the edge, the record orb.
- `screenshots/2002-pullout-bottom-lane.png` — tapping a deliverable rises the pull-out from the
  bottom with a grab handle, the `🔒 On device` egress badge, "Route this to AI", over the
  (undimmed) lane rows.
- `screenshots/2002-pullout-right-ipad.png` — the same content enters from the right edge on iPad
  beside the diorama (no regression).

Device walk deferred to **HSM-20-05** (the gate). Until then the iPhone cells stay forward
constraints.
