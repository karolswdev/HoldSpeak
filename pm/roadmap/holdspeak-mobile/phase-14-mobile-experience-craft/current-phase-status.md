# Phase 14 — Mobile Experience & Craft

**Status:** in-progress (opened 2026-06-21 in direct response to the owner: usability,
design, and modern hand-driven mobile practice were never in the roadmap, and the app
shipped as a bare functional shell, not a crafted product. This phase makes the
**experience** first-class.)

**Last updated:** 2026-06-21 (**opened + first craft delivered.** The owner chose the
**Tactile Sheets** design direction from three concrete mockups (gesture-first: swipeable
cards, draggable action sheet, big targets, haptic-forward). HSM-14-01 in progress: a native
`DS` design system (color/spacing/radii/elevation tokens + reusable swipeable-card / action-
sheet / chip components, `haptic()` wired) built and **proven on the hero meeting +
intelligence screen — committed Simulator screenshot** (`./screenshots/tactile-sheets.png`,
iPhone 17 Pro Max). Swipe-to-approve reveal, draggable Regenerate/Ink sheet, egress as the
single `Local` badge (caught + removed a banned "privacy novel" line mid-build). Built as a
one-module `swiftc` simulator harness so craft is shown **without the device**. **HSM-14-03 started + on device:** the Tactile Sheets
`SwipeableArtifactCard` is now adopted into the REAL app (`MeetingCaptureApp`) — swipe
left→approve / right→dismiss with haptics, type-tinted over all 15 artifact types, elevated —
wired to the live `review.approve`/`review.reject`, built + deployed to the iPad Air M4. Next
under 14-03: the header + transcript card + a draggable bottom action sheet. — the missing dimension. The mobile roadmap was all
engineering tracks (Council Charter A–N); there was no track that owned whether the app is
**usable, designed, and modern** as a hand-driven (touch + Apple Pencil) product. Phase 14
is that track. It is **proven in the iOS Simulator with committed screenshots** — design and
interaction craft do NOT need the physical device to be delivered and shown — with the device
reserved only for true hardware feel (haptics latency, Pencil pressure). Owner bar: flat /
basic / default-SwiftUI components are a failure; the app must feel like a premium, modern,
native iOS app.)

## Why this phase exists

The HoldSpeak Mobile runtime is engineering-complete (Phases 0–13) but the **product** — the
felt, hand-driven experience — was never crafted or even tracked. Recording, the meeting
list, the transcript, the PencilKit notebook, and the intelligence review are functional but
plain: default styling, abrupt states, no gesture/haptic craft, no considered empty/loading/
error moments, no accessibility pass. For an app whose whole premise is *"pick it up, press
record, leave with artifacts"*, the experience IS the product. This phase elevates it to the
owner's bar and keeps it there.

## Goal

Make the iPad/iPhone app a **premium, modern, hand-driven native experience**: a real native
design system, every core screen recrafted, interaction craft (gesture, haptic, motion,
Pencil), accessibility + adaptivity, and a polish pass — each delivered with committed
**Simulator screenshots** as visible proof, so design is shown without the physical device.

## Scope

- **In:** the design system as native SwiftUI tokens + reusable components (HSM-14-01); the
  **capture** experience recrafted — record → live transcript, the flagship moment
  (HSM-14-02); the **meeting + intelligence** surface recrafted — list → detail → review,
  with felt-good states and gestures (HSM-14-03); **interaction craft** — gestures, haptics,
  motion/transitions, Pencil affordances (HSM-14-04); **accessibility + adaptivity** —
  Dynamic Type, VoiceOver, dark/light, size classes / multitasking, reduce-motion
  (HSM-14-05); a **polish & craft-QA** pass — empty/loading/error everywhere, micro-copy,
  edge cases, a screenshot gallery (HSM-14-06).
- **Out:** new runtime features or engines (Phases 1–13 own those — this phase recrafts how
  they're *presented*, not what they do). Backend logic in views (stays in the Runtime Core).
  App Store / TestFlight logistics (a release step).

## Exit criteria (evidence required)

- [ ] A **native design system** (typography scale, color + elevation tokens, spacing,
      motion) with reusable components (cards, buttons, chips, sheets, states) replaces ad-hoc
      styling — Simulator-screenshot-verified (HSM-14-01).
- [ ] The **capture** screen is a crafted flagship moment (live level/feedback, fluid
      record/stop, haptics, considered states) — screenshot + device-feel verified (HSM-14-02).
- [ ] The **meeting + intelligence** surface is recrafted: modern cards, swipe/gesture
      actions, clear empty/loading/generating/error states, a felt-good regenerate/approve
      flow — screenshot-verified (HSM-14-03).
- [ ] **Interaction craft**: gesture, haptic, motion, and Pencil affordances make it feel
      hand-driven, not tapped-through — verified (HSM-14-04).
- [ ] **Accessibility + adaptivity**: Dynamic Type, VoiceOver labels, dark/light, size
      classes / iPad multitasking, reduce-motion — verified (HSM-14-05).
- [ ] **Polish & craft QA**: every surface has its empty/loading/error state, micro-copy is
      considered, and a committed Simulator screenshot gallery is the proof of bar (HSM-14-06).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-14-01 | Native design system (Signal → SwiftUI tokens + components) | in-progress | [story-01](./story-01-native-design-system.md) | [shot](./screenshots/tactile-sheets.png) |
| HSM-14-02 | The capture experience, recrafted (flagship moment) | backlog | story-02 | — |
| HSM-14-03 | The meeting + intelligence surface, recrafted | in-progress | [story-03](./story-03-meeting-intelligence-recrafted.md) | swipeable cards live on device |
| HSM-14-04 | Interaction craft (gesture, haptic, motion, Pencil) | backlog | story-04 | — |
| HSM-14-05 | Accessibility + adaptivity | backlog | story-05 | — |
| HSM-14-06 | Polish & craft QA (states, micro-copy, screenshot gallery) | backlog | story-06 | — |
| HSM-14-07 | Voice correction — reject by voice → local model re-routes | in-progress | [story-07](./story-07-voice-correction.md) | host-tested + on iPad |

## Where we are

Just opened, in direct response to owner feedback that craft/usability/design was absent from
the roadmap and undelivered. The runtime is done; this phase is about the **experience on top
of it**. It runs design-first: each story is built, then **screenshotted in the Simulator and
committed**, so the owner can see and judge the craft without the physical iPad — the device
is only for final hardware feel. The design direction (the visual + interaction language) is
the owner's call and is being set before HSM-14-01 lands, so the system is built to the right
target, not guessed.

## Operating principle (standing, beyond this phase)

Design/usability/craft is now a **standing quality bar on every mobile surface**, not a
one-time pass: any new mobile UI meets the HSM-14-01 design system, has its states, and ships
a Simulator screenshot. Flat/default/unconsidered components are a regression.
