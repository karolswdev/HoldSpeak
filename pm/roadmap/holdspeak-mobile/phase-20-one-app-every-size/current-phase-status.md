# Phase 20 — One app, every size (the iPhone pass)

**Status:** in progress — **follows 18 + 19** (you cannot lay out at compact width what does not
exist yet). **20-01 → 20-04 all landed sim-proven** (`DeskCamera`, the desk lane, the capture canvas,
the forms + the hold-bar teleprompter). Only **20-05 (the device walk)** remains — plus a carried
follow-up: the action-sheet/editor scrim → rising-sheet reframe (see "Where we are").

**Last updated:** 2026-06-27 (HSM-20-04 shipped: the connect Port/Token row stacks vertically on the
lane; the iPhone dictation surface gains the **hold-bar teleprompter** — a persistent bottom-edge
accent HOLD BAR that, on press, reflows a bottom-up teleprompter (live partial nearest the thumb, the
`→ Mac` target + egress pill above), no dim; the live-coder cards (`DioCoderSession`/`Answer`) clamped
via `camera.cardWidth`. meeting-capture + companion-shell sim builds green, `swift test` 381 green;
see `evidence-story-04.md`. Earlier today: 20-01 (`DeskCamera`), 20-02 (the desk lane + migrating
pull-out), 20-03 (the capture canvas + one-thumb tack).)

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
| HSM-20-04 | The forms + screens at compact width (connect, editors, sheets, hold-bar teleprompter) | done (sim)¹ |
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

**20-04 (forms/screens) landed:** the connect Port/Token row stacks vertically on the lane
(`ShellView` reads `horizontalSizeClass`); the iPhone dictation surface gains the **hold-bar
teleprompter** (`DictateView.laneBody` — a persistent bottom-edge accent HOLD BAR that, on
press-and-hold, reflows a bottom-up teleprompter with the live partial nearest the thumb and the
`→ Mac` target + egress pill above, no dim; release commits with a `.heavy` haptic); the live-coder
cards (`DioCoderSession`/`Answer`) clamped via `camera.cardWidth`. `HS_DEMO_DICTATE` promoted to root
for screenshots.

**¹ Carried follow-up (the remaining 20-04 sub-item).** The dim-scrim **action sheets**
(`DioSendCard`/`DioActSheet`/`DioRunTargetSheet`/`DioRouteSheet`) and the agent/chain editors
(`DeskAgents`) **already fit 390pt** (their `maxWidth: 440/460/560` caps below it) but keep their
`Color.black.opacity(...)` scrims. Reframing them as the hand-built rising sheet (the owner's
no-modal law, [[feedback_no_modals_in_world]]) touches ~6 desk overlays and is a larger, riskier
change best done deliberately and walked on device — so it is carried as a focused follow-up rather
than rushed in. The primitive editing the owner most cares about (notes/KBs) is already in-world on
the lane (20-02).

**Next: 20-05 — the device walk.** It is the gate and the only thing that promotes an iPhone cell
from forward-constraint to proven (the owner walks the cabled iPhone;
[[feedback_verify_on_device_not_seeded]]).
</content>
