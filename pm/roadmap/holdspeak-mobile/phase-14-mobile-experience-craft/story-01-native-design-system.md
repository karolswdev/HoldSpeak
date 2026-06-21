# HSM-14-01 — Native design system (Signal → SwiftUI) + the Tactile Sheets hero

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress (design system + hero screen built & Simulator-proven; adoption across the app's real screens is the continuation)
- **Depends on:** —
- **Unblocks:** HSM-14-02..06 (every recrafted screen builds on the system)
- **Owner:** unassigned

## Problem

The app styled each screen ad-hoc on top of a loose `Sig` palette — no spacing rhythm,
type scale, radii, elevation, or reusable crafted components. The result was a flat shell,
not a designed product. A hand-driven app needs a real **native design system** and a proven
**direction** before any screen is recrafted, so craft is consistent and not re-guessed.

## Direction (owner-chosen 2026-06-21)

Presented three concrete directions as mockups; the owner chose **Tactile Sheets** —
gesture-first: big **swipeable** cards (swipe to approve/dismiss), a **draggable bottom-sheet**
action bar, large touch targets, haptic-forward. Built around thumbs + Apple Pencil, not taps.

## Scope

- **In:** the `DS` design system (native SwiftUI) — surface/text/accent **color tokens**,
  a **spacing rhythm**, **radii**, type weights/sizes, soft **elevation**, and reusable
  components (chips, section labels, **swipeable artifact card**, transcript card, **action
  sheet**, circle buttons), with `haptic()` wired. Proven on the **hero screen** (the meeting
  + intelligence surface) rendered with mock data and **screenshot in the iOS Simulator**.
- **Out:** adopting the system into every real app screen (HSM-14-02/03 do that against the
  live runtime). New runtime behaviour. The physical-device feel pass (only hardware-specific
  haptic/Pencil latency needs the device).

## Acceptance criteria

- [x] A native `DS` token system + reusable crafted components exists (not ad-hoc styling).
- [x] The **direction is locked** by the owner from concrete mockups (Tactile Sheets).
- [x] The hero meeting + intelligence screen is built to the system and **proven with a
      committed Simulator screenshot** — swipe-to-approve reveal, draggable action sheet,
      egress as the single **Local badge** (no privacy prose — POSITIONING canon).
- [ ] The system is **adopted** into the app's real screens (rolls out via HSM-14-02/03).

## Evidence

`scripts/experience/MeetingExperienceView.swift` (the system + hero) + the harness build
`scripts/experience-shot.sh` → **`./screenshots/tactile-sheets.png`** (committed), captured on
the iPhone 17 Pro Max simulator. The screen: large title + metadata chips, a transcript card,
INTELLIGENCE with a `Local` egress badge, three swipeable artifact cards (the first mid-swipe
showing the green Approve), and a draggable Regenerate/Ink action sheet.

## Notes

- Built as a standalone harness (one-module `swiftc` for the simulator SDK) so design is
  delivered and **shown without the physical device** — the device is reserved only for true
  hardware feel. Adoption into the real app target (reconciling `DS` with the existing `Sig`)
  is the next step under HSM-14-03.
- Egress shown as the one `Local` badge, never a privacy sentence (caught + removed a
  "Nothing leaves this iPad" line mid-build) — [[feedback_no_privacy_novels]] canon.
