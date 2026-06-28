# Phase 20 — One app, every size (the iPhone pass)

**Status:** planned — **follows 18 + 19** (you cannot lay out at compact width what does not
exist yet). **Stories authored** (this is an executable front, lead-phase cadence).

**Last updated:** 2026-06-27 (authored from the parity audit theme 1; **refined into an
executable front** with a full handover + 5 detailed stories + verified file:line corrections.)

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
| HSM-20-01 | The `DeskCamera` foundation (one width authority + the lane helper) — **leads** | todo |
| HSM-20-02 | The desk at compact width (the lane + the migrating pull-out) | todo |
| HSM-20-03 | The capture canvas at compact width (docked recorder + wrapped chips) | todo |
| HSM-20-04 | The forms + screens at compact width (connect, editors, sheets, hold-bar teleprompter) | todo |
| HSM-20-05 | On-device proof (every compact screen walked on a real iPhone) — **the gate** | todo |

## Where we are

Not started; **fully storied and handed over.** **20-01 leads** (the `DeskCamera` authority the
rest read). 20-02/03/04 parallelize once 20-01 lands (disjoint surfaces). The desk scrim overlays
(`DioCoderSession`/`DioSendCard`/`DioZoneEditor`…) are also the "modal hells" the owner rejects
([[feedback_no_modals_in_world]]) — 20-02/04 reframe them as in-world or hand-built rising sheets,
killing two birds. **20-05 is the gate** and the only thing that promotes an iPhone cell from
forward-constraint to proven.
</content>
