# Phase 20 — One app, every size (the iPhone pass)

**Status:** planned — **follows 18 + 19** (you cannot lay out at compact width what does not
exist yet). Stories detailed on open.

**Last updated:** 2026-06-27 (**authored** from the parity audit, theme 1.)

## Why this phase exists

Audit theme 1: *iPhone is layout debt, not capability debt.* Compact-width adaptation exists
in exactly one place (`DeskDioramaStage.swift:3085` — the rail collapse + hidden title,
shipped this session). Every other Apple surface inherits the iPad layout:

- Fixed `380pt` panels on the desk (`DeskDioramaStage.swift:641/698`) overflow ~390pt iPhone
  portrait, so meeting artifacts are unreachable.
- Fixed-size dim-scrim overlays overflow a phone (`DioCoderSession` 480×560, `DioCoderAnswer`
  400, `DioZoneEditor` 380, `DioSendCard`/`DioActSheet`).
- The capture canvas (`LiveCaptureCanvas`, free-drag bubbles + floating recorder) assumes a
  wide board.
- Unwrapped chip rows (`MeetingCaptureApp.swift:1641`) overflow; the connect screen's two-up
  Port+Token row is cramped (`CompanionShellApp.connectScreen`, fixed maxWidth 560).

The audit's honest framing: most iPhone gaps are "the same finding twice" — the feature is
absent on Apple, so there is nothing to lay out. That is **why this phase follows 18/19**:
build the surfaces first, then make them reflow.

## The load-bearing design call

**A real `horizontalSizeClass` pass with a shared compact pattern, then prove it on metal.**
Not per-screen hacks: a single compact-layout convention (size-class plumbing, a width-relative
card-sizing helper extending the in-world card pattern shipped this session, `presentationDetents`
for any remaining sheets) applied across every Apple surface. Every `🟡`/`❌` iPhone cell in the
matrix stays a *forward constraint* until it is walked on a physical iPhone
([[feedback_verify_on_device_not_seeded]]) — seeded Simulator screenshots do not close a row.

## Stories

| ID | Title | Status |
|----|-------|--------|
| HSM-20-01 | The size-class foundation (shared compact pattern + helpers) — **leads** | todo |
| HSM-20-02 | The desk at compact width (panels, cards, the overlays/scrims) | todo |
| HSM-20-03 | The capture canvas at compact width (list + docked recorder + wrapped chips) | todo |
| HSM-20-04 | The forms + screens at compact width (connect, settings, send/act sheets) | todo |
| HSM-20-05 | On-device proof (every compact screen walked on a real iPhone) | todo |

## Where we are

Not started. **20-01 leads** (the shared pattern the rest apply). The desk overlays
(`DioCoderSession`/`DioSendCard`/`DioZoneEditor`) are also the "modal hells" the owner rejects
([[feedback_no_modals_in_world]]) — 20-02 reframes them as in-world or compact-aware cards,
killing two birds. 20-05 is the gate and the only thing that promotes an iPhone cell from
forward-constraint to proven.
