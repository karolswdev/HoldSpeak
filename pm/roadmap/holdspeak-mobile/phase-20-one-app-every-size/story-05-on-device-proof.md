# HSM-20-05 — On-device proof (every compact screen walked on a real iPhone)

- **Project:** holdspeak-mobile
- **Phase:** 20
- **Status:** todo — **the gate.** The ONLY story that promotes an iPhone cell from
  forward-constraint to proven.
- **Depends on:** 20-01, 20-02, 20-03, 20-04 (everything reflows before it is walked).
- **Unblocks:** the phase closeout + every `🟡` iPhone cell in the parity matrix.
- **Owner:** **the owner** (only he can walk the cabled iPhone).

## Problem

Every prior mobile session that called a Simulator screenshot "proof" was wrong, and the owner
walked a real device to find it broken ([[feedback_verify_on_device_not_seeded]], the device-gap
handover). Simulator screenshots are for iteration; they do **not** close a row. A compact layout
that is perfect in the iPhone sim can still break on real metal (safe-area insets, the notch/Dynamic
Island, real rotation, real split-view drag, real keyboard avoidance).

## The design

This story is a **walk + capture protocol**, not new code (any bug it finds spawns a fix in the
relevant story's surface):

1. **Build to a real iPhone** (cabled, UNLOCKED): `scripts/meeting-capture-device.sh <iphone-udid>`
   (run with the sandbox disabled — it clones packages; the build needs `patch-llm-macro.sh` +
   `-disableAutomaticPackageResolution`, handover §6).
2. **Walk every compact surface** and confirm against the vision:
   - The desk **lane** column + zone chip rail + FAB + slim header.
   - The pull-out **rising from the bottom edge** (and, on an iPad in split-view, migrating
     right→bottom on the divider drag — the signature moment).
   - Rotate lane↔wide: the hand-arranged desk arrangement is **restored exactly**.
   - The capture canvas: docked recorder, a moment tacked one-thumb.
   - Connect (Port/Token stacked), settings, the agent/chain editors.
   - The **hold-bar teleprompter**: press-and-hold reflows bottom-up, no dim, release commits.
   - Every text field still has its speak-to-fill mic; every output shows the egress badge.
3. **The owner is the only walker.** Do not ask him for screenshots — diagnose any reported break
   from CODE. The walk is his button; your job is to make it pass on the first walk by being
   ruthless in the sim first.

## Scope

- **In:** the device build + the walk protocol + logging which cells are proven; fixes routed back
  to 20-02/03/04 for anything the walk breaks.
- **Out:** new layout work (lives in the other stories).

## Proof

- The owner confirms each surface on the cabled iPhone. Each confirmed surface promotes its matrix
  cell from `🟡` (forward-constraint) to proven. **No sim screenshot closes this story.**
- Phase closeout (the operating cadence: story headers, `current-phase-status.md`, the README "last
  updated", the EQUILIBRIUM wave log) only after the walk passes.
</content>
