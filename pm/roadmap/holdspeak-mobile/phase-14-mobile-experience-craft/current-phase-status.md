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
| HSM-14-02 | The capture experience, recrafted (flagship moment) | in-progress | story-02 | floating draggable recorder + full-bleed canvas + mic-reactive waveform + faster transcription |
| HSM-14-03 | The meeting + intelligence surface, recrafted | in-progress | [story-03](./story-03-meeting-intelligence-recrafted.md) | cards materialize (glow+insert) + MIR-as-lens, on device |
| HSM-14-04 | Interaction craft (gesture, haptic, motion, Pencil) | backlog | story-04 | — |
| HSM-14-05 | Accessibility + adaptivity | backlog | story-05 | — |
| HSM-14-06 | Polish & craft QA (states, micro-copy, screenshot gallery) | backlog | story-06 | — |
| HSM-14-07 | Voice correction — reject by voice → local model re-routes | in-progress | [story-07](./story-07-voice-correction.md) | host-tested + on iPad |
| HSM-14-08 | The Pencil as a diagram language (sketch → Mermaid) | in-progress | [story-08](./story-08-pencil-diagram-language.md) | engine host-tested (209/0) |
| HSM-14-09 | Local vision model (Gemma 4) seam + ambiguity resolution | in-progress | [story-09](./story-09-local-vision-model.md) | seam host-tested (211/0) |
| HSM-14-10 | Models, front and center (import + manage, AirDrop-ready) | in-progress | [story-10](./story-10-model-import.md) | device-built |
| HSM-14-11 | The live capture canvas (transcription bubbles + tack-to-board) | in-progress | [story-11](./story-11-live-capture-canvas.md) | built + on iPad + Simulator-proven |
| HSM-14-12 | Constant-time live transcription (sliding window + commit) | planned | [story-12](./story-12-constant-time-transcription.md) | designed |
| HSM-14-13 | The spatial workspace (OS-like capture surface) | planned | [story-13](./story-13-spatial-workspace.md) | designed |

## Where we are

Just opened, in direct response to owner feedback that craft/usability/design was absent from
the roadmap and undelivered. The runtime is done; this phase is about the **experience on top
of it**. It runs design-first: each story is built, then **screenshotted in the Simulator and
committed**, so the owner can see and judge the craft without the physical iPad — the device
is only for final hardware feel. The design direction (the visual + interaction language) is
the owner's call and is being set before HSM-14-01 lands, so the system is built to the right
target, not guessed.

**2026-06-21 — the intelligence pane + the live capture canvas.** Owner: artifacts "just
start appearing, no effect, no nothing," and the balanced/architect/delivery/product/incident
profiles "don't do shit — all it does is change the order." Fixed both. Cards now
**materialize**: a type-tint ring flashes around each as it lands + the insert is animated, so
a generated insight announces itself. The MIR profile became a real **lens** — a pill row with
a per-profile icon, a one-line blurb of what it surfaces, and emphasized-type chips, and the
Generate button names the lens it runs through (HSM-14-03). And the flagship: the live
transcript "wall of text" is replaced by the **live capture canvas** (HSM-14-11) — utterances
float up as bubbles, the live fragment breathes as a caption, and you grab a bubble with the
Pencil and **tack it to a pin board**, which marks the moment so the on-device intelligence
weights it. Three bespoke **Pixellab** pixel-art assets (Qlippy mascot, brass pushpin, waveform
orb) bundled offline. Built + installed on the iPad Air M4; Simulator screenshot committed.

**2026-06-22 — shipped the live-dynamism batch + planned the next two.** PRs #117/#118 landed:
the transcription slowness was root-caused (the Whisper model reloaded every tick → cached;
3 s → 1.2 s cadence), an **audio-reactive waveform** off the real mic level, the recording
controls collapsed into a **draggable floating recorder** (no big button), the canvas became
**one free-form dot-grid desktop** (fling a bubble anywhere to tack), and note cards now
**promote to real `needs_review` artifacts**. Then the owner asked to **plan, not build, the next
two properly**: **HSM-14-12** (constant-time live transcription — a timestamp-driven sliding
window so long meetings stay immediate; the model-cache fixed the acute pain but per-tick cost
still grows O(length)) and **HSM-14-13** (the spatial workspace — dockable/minimizable recorder,
free-place vs tack, resizable cards, tidy, and stretch: minimap + windowed panes). Both are
written up as stories with architecture, acceptance criteria, and test plans; implementation is
deferred.

## Operating principle (standing, beyond this phase)

Design/usability/craft is now a **standing quality bar on every mobile surface**, not a
one-time pass: any new mobile UI meets the HSM-14-01 design system, has its states, and ships
a Simulator screenshot. Flat/default/unconsidered components are a regression.
