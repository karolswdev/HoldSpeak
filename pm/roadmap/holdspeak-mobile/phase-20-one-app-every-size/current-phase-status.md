# Phase 20 — One app, every size (the iPhone pass)

**Status:** in progress — **follows 18 + 19** (you cannot lay out at compact width what does not
exist yet). **20-01 (`DeskCamera`) + 20-02 (the desk lane) + 20-03 (the capture canvas) landed**
(sim-proven); 20-04 next, 20-05 is the device gate.

**Last updated:** 2026-06-27 (HSM-20-02 shipped: the iPhone desk lane — a one-thumb card column
(`laneColumn`) with a dynamic kind-filter chip rail, full-width primitive rows, an accent FAB, and
the signature **migrating pull-out** that rises from the bottom edge on iPhone / enters from the
right on iPad on a spring, over a transparent catcher (no scrim), egress badge riding along.
Fixed cards clamped via `camera.cardWidth`; `positions[id]` untouched (rotation restores the
diorama). `swift test` 381 green + iPhone/iPad sim builds green; see `evidence-story-02.md`.
Earlier: HSM-20-01 — `DeskCamera` is the one width authority, the four strays folded in.)

**Start here:** `../HANDOVER-2026-06-27-phase20-one-app-every-size.md` — the master orientation
doc (verified code map, the build/screenshot pipeline, the doctrine call, the hard-won lessons,
the definition of done). Read it before any code.

## Why this phase exists

Audit theme 1: *iPhone is layout debt, not capability debt.* Compact-width adaptation exists in
exactly one place (`DeskDioramaStage.swift:3085`, the rail collapse + hidden title, shipped this
session). Every other Apple surface inherits the iPad layout:

- Fixed `380pt` panels on the desk (`DeskDioramaStage.swift:641/698`) overflow ~390pt iPhone
  portrait, so meeting artifacts are unreachable.
- Fixed-size dim-scrim overlays overflow a phone — `DioCoderSession` 480×560 + `DioCoderAnswer` 400
  (**in `DeskCoder.swift:183/367`, not `DeskDioramaStage` — audit was wrong**), `DioZoneEditor`
  380, `DioSendCard`/`DioActSheet` 460, the `DeskAgents.swift` editors 560/740.
- The capture canvas (`LiveCaptureCanvas`, `MeetingCaptureApp.swift:1137`) assumes a wide board
  (though it is the least broken — it is already `GeometryReader`-driven).
- The companion connect screen's two-up Port+Token row is cramped
  (`CompanionShellApp.swift:651–653`, **not** `MeetingCaptureApp.swift:1641` — audit was wrong).

The audit's honest framing: most iPhone gaps are "the same finding twice" — the feature is absent
on Apple, so there is nothing to lay out. That is **why this phase follows 18/19**: build the
surfaces first, then make them reflow.

## The load-bearing design call — `DeskCamera`, the one width authority

**Introduce a single `DeskCamera` (`.wide` / `.narrow` / `.lane`) derived from
`horizontalSizeClass` FIRST and geometry width second, then fold every stray width check into it.**
This is the vision's explicit first move (`../EXPERIENCE-VISION-2026-06-27.md:128`, §4.3): *"DeskCamera
is the only width authority; delete the strays."* NOT per-screen `w < 500` hacks (that lies in iPad
split-view and multiplies debt). The lane is a real card-column renderer, not a free reflow; the
intelligence pull-out (`DioPullout`) migrates right-edge→bottom-edge on a spring (the signature
device moment); nothing is hidden or removed between sizes, and the hand-arranged desk arrangement
(`positions[id]`) is restored exactly on rotate. Every `🟡`/`❌` iPhone cell stays a *forward
constraint* until walked on a physical iPhone ([[feedback_verify_on_device_not_seeded]]) — seeded
Simulator screenshots do not close a row.

## Stories

| ID | Title | Status |
|----|-------|--------|
| HSM-20-01 | The `DeskCamera` foundation (one width authority + the lane helper) — **leads** | done (sim) |
| HSM-20-02 | The desk at compact width (the lane + the migrating pull-out) | done (sim) |
| HSM-20-03 | The capture canvas at compact width (docked recorder + wrapped chips) | done (sim) |
| HSM-20-04 | The forms + screens at compact width (connect, editors, sheets, hold-bar teleprompter) | todo |
| HSM-20-05 | On-device proof (every compact screen walked on a real iPhone) — **the gate** | todo |

## Where we are

**20-01 + 20-02 landed (sim-proven).** `DeskCamera` is the only width authority (size class first,
500pt boundary second; the four strays folded in, byte-equivalent on iPad). On top of it, **20-02
built the iPhone desk lane**: `laneColumn` renders a dynamic kind-filter chip rail over full-width
primitive rows (`DioLaneRow` glyph@44 · title · badge · subtitle · chevron; zones are divable rows),
an accent FAB carries create, and the signature **migrating pull-out** rises from the bottom edge on
iPhone / enters from the right on iPad on a spring, over a transparent catcher (no scrim), egress
badge riding along. `positions[id]` is untouched, so rotating back to `.wide` restores the diorama.
Fixed cards (`DioConnectCard`/`DioZoneEditor`) clamped via `camera.cardWidth`. `swift test` 381
green + iPhone/iPad sim builds green.

**20-03 (capture canvas) landed:** confirmed the least-broken surface (it already scales; the
recorder docks bottom by default) and added a one-thumb tap-to-tack on live bubbles + a
`HS_DEMO_CAPTURE` screenshot seed.

**Next: 20-04 (forms/screens + the hold-bar teleprompter).** 20-04 owns the
remaining desk **scrim reframes** — the action sheets (`DioSendCard`/`DioActSheet`/`DioRunTargetSheet`/
`DioRouteSheet`) and agent/chain editors — as the hand-built rising sheet (the "modal hells" the
owner rejects, [[feedback_no_modals_in_world]]). **20-05 is the device gate** and the only thing that
promotes an iPhone cell from forward-constraint to proven.
</content>
