# Evidence — HSM-20-04 — The forms + screens at compact width

**Date:** 2026-06-27. **Branch:** `holdspeak-mobile/phase20-04-forms-screens`.

## What shipped

1. **The connect Port/Token stack** (`CompanionShellApp.swift`). `ShellView` reads
   `@Environment(\.horizontalSizeClass)`; on `.compact` the two-up `Port`(`.frame(width: 130)`) +
   `Token` row stacks vertically (each full-width), staying two-up on iPad. The `maxWidth: 560`
   container caps below 390pt so it fits. Every field keeps its existing keyboard/secure config.

2. **The iPhone HOLD-BAR teleprompter** (`CompanionMesh.swift`, `DictateView`) — the vision's
   signature dictation beat. `DictateView` now branches by size class: the iPad keeps the scrolling
   stage with the centered push-to-talk hero (`regularBody`); the iPhone (`laneBody`) gets:
   - a **persistent accent HOLD BAR** pinned to the bottom edge (thumb zone) — press-and-hold opens
     the mic (reusing `model.startListening`/`stopAndDeliver`), release commits with a `.heavy`
     haptic; unpaired, it routes to pairing.
   - a **bottom-up teleprompter** that rises from the bar while you talk (`.move(edge: .bottom)` on a
     spring), reading bottom-to-top: the live "you said" partial largest and nearest the thumb, the
     "→ <Mac>" target line + the egress badge as one pill at the top. **No dim toward the bar** (the
     bar's elevation carries focus; a dim would be a scrim).
   The read-back of sent lines scrolls above, padded to clear the bar.

3. **Coder-card clamps** (`DeskCoder.swift`). `DioCoderSession` (`width: 480, height: 560`) and
   `DioCoderAnswer` (`width: 400`) gained `maxW`/`maxH` params the desk caller sets to
   `camera.cardWidth(...)` / `min(560, h − …)`, so the live-coder overlays fit a 390pt iPhone.
   (`DioConnectCard`/`DioZoneEditor` were already clamped in 20-02.)

4. **Sim seed** `HS_DEMO_DICTATE` promoted to the root `WindowGroup` so the dictation surface (the
   hold-bar teleprompter) can be screenshot straight.

## Honest scope — deferred

The dim-scrim **action sheets** (`DioSendCard` / `DioActSheet` / `DioRunTargetSheet` /
`DioRouteSheet`) and the agent/chain editors (`DeskAgents`) **already fit 390pt** (their
`maxWidth: 440/460/560` caps below it), but they keep their `Color.black.opacity(...)` scrims. The
full reframe to the hand-built rising sheet (the owner's no-modal law,
[[feedback_no_modals_in_world]]) is a larger, riskier change across ~6 desk overlays best done
deliberately and walked on device — it is carried as a focused follow-up (see the phase status
"Where we are"). The primitive editing the owner most cares about (notes/KBs) is already in-world on
the lane (20-02). This story closed the new compact surfaces + the functional clamps; the scrim
polish on the action/approval destinations is the remaining item.

## Proof

- iPhone-17-Pro sim builds: meeting-capture **BUILD SUCCEEDED** + companion-shell **BUILD
  SUCCEEDED**. `swift test`: **381 passed, 0 failures.**
- `screenshots/2004-holdbar-teleprompter-lane.png` — the dictation surface: the bottom HOLD BAR
  ("Hold to talk", accent), the bottom-up teleprompter (live partial full-weight nearest the thumb,
  "→ Karol's Mac" + the `ON-DEVICE · LOCAL MESH → KAROL'S MAC` egress pill above), the sent read-back
  scrolling above — no dim.
- `screenshots/2004-connect-stacked-lane.png` — Host / Port / Token stacked full-width on the lane,
  the Connect button below.

Device walk = **HSM-20-05** (the gate).
