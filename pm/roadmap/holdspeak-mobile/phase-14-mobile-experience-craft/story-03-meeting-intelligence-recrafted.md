# HSM-14-03 — The meeting + intelligence surface, recrafted (real app)

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress (the swipeable artifact card is adopted into the live app + deployed to device; the rest of the screen — header, transcript, pinned action sheet — continues)
- **Depends on:** HSM-14-01 (design system + Tactile Sheets direction)
- **Unblocks:** the felt-good review flow on real meetings
- **Owner:** unassigned

## Problem

HSM-14-01 proved the Tactile Sheets direction in a Simulator harness. This story brings it
into the **real app** — the meeting detail's intelligence surface — wired to the live
`review.approve` / `review.reject` / `review.generate` actions, so the craft is something the
owner actually uses, not a mockup.

## Scope

- **In:** `SwipeableArtifactCard` in the real app (`MeetingCaptureApp.swift`) — gesture-first
  (swipe **left → Approve**, **right → Dismiss**, with `UIImpactFeedbackGenerator` haptics),
  **type-tinted** (per-type accent + SF Symbol via `artifactTint`/`artifactGlyph` over all 15
  `ArtifactType`s), elevated (large radius, soft shadow), with the ink image, body, status
  pill, and a swipe hint. Swapped into `artifactsSection` over the real grouped artifacts and
  wired to `review.approve(id)` / `review.reject(id)`. Built + **deployed to the physical
  iPad**.
- **Out (continues here):** recrafting the screen **header** (title + metadata chips), the
  **transcript** card, and turning the generate/ink actions into a **draggable bottom action
  sheet** (the harness's pinned sheet) — landing next under this story. Empty/loading/error
  states (HSM-14-06). The capture screen (HSM-14-02).

## Acceptance criteria

- [x] Artifact cards in the real app are **swipeable** (left→approve / right→dismiss) with
      haptics, wired to the live review actions, type-tinted + elevated — built + deployed to
      the iPad.
- [ ] The header + transcript card are recrafted to the design system.
- [ ] The generate/ink actions become a draggable bottom action sheet.
- [ ] Empty / generating / error states are considered (with HSM-14-06).

## Evidence

`apple/App/MeetingCaptureApp.swift` — `SwipeableArtifactCard` + `artifactTint`/`artifactGlyph`/
`tactile`, swapped into `artifactsSection`. Device build **SUCCEEDED** and installed on the
iPad Air M4; the design matches the proven harness screenshot
([../phase-14.../screenshots/tactile-sheets.png](./screenshots/tactile-sheets.png)).

## Notes

- Reuses the app's existing `Sig` palette (near-identical to the harness `DS`) rather than
  importing `DS`, to avoid a `Color(hex:)` collision — reconciling the two into one shared
  design-system file is a HSM-14-01 follow-up.
- Swipe is the primary affordance per the owner's Tactile Sheets choice; a visible "swipe →
  approve · ← dismiss" hint keeps it discoverable.
