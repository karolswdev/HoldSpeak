# AIPI-1-06 - Phase Exit + DoD + Provisioning Runbook

- **Project:** aipi-lite
- **Phase:** 1
- **Status:** in-progress
- **Depends on:** AIPI-1-01, AIPI-1-02, AIPI-1-03, AIPI-1-04, AIPI-1-05
- **Unblocks:** AIPI-2
- **Owner:** karol

## Problem

Close the phase: ship the user-facing runbook so a new user (or
the same user three months from now) can set up a fresh AIPI-Lite
on a new network in under five minutes via any of the four
provisioning paths.

## Scope

- **In:**
  - `docs/PROVISIONING.md` covering, in order:
    1. **First-time flash** — clone repo, fill in `secrets.yaml`,
       `esphome run aipi.yaml`. Cover the "two known networks"
       expectation up front.
    2. **Re-provision via captive portal** — what the user sees
       (LCD `Setup-AP`), how to join `AiPi-Setup`, what the
       captive portal looks like, what to do if iOS doesn't
       auto-pop the portal.
    3. **Re-provision via Improv-WiFi (BLE)** — link to the
       official mobile app, screenshots of the pairing flow.
    4. **USB recovery via improv_serial** — link to
       improv-wifi.com, the click-to-flash path, what to do
       if the device is wedged.
    5. **Factory-reset gesture** — boot-hold the left button
       for 5 s, what's wiped, what's preserved.
  - `pm/roadmap/aipi-lite/README.md`: phase 1 status flips to
    `done`, phase 2 (bridge protocol translator) row added with
    `not-started`, "Last updated" bumped, "Current phase"
    pointer moves to phase 2.
  - `phase-1-provisioning/final-summary.md` per the
    `roadmap-builder.md` template: goal recap, exit criteria
    final state with evidence links, story table, surprises +
    lessons, handoff to AIPI-2.
  - `current-phase-status.md` frozen — no further edits after
    phase close.

- **Out:**
  - AIPI-2 work itself (bridge protocol translator). That phase
    opens after this DoD lands.
  - Marketing / onboarding HTML — `docs/PROVISIONING.md` is the
    canonical source; web rendering is out of scope.

## Acceptance Criteria

- [x] `docs/PROVISIONING.md` exists, covers all four
  provisioning paths + factory-reset, includes screenshots or
  terminal output where useful. Landed 2026-05-07. Five
  numbered sections (first-time flash, captive portal,
  Improv-WiFi BLE, improv_serial USB, factory-reset gesture)
  plus a TL;DR table and a troubleshooting cheatsheet. The
  AP→STA "no auto-return" caveat from the AIPI-1-05
  implementation is documented in §2. Screenshots not
  included (host has no way to generate phone-app captures);
  user can append later if useful.
- [ ] All AIPI-1-01..05 stories show `Status: done` with paired
  `evidence-story-{n}.md` files.
  **Pending hardware verification** of stories 01..05.
  Today's evidence lives inline in each story file under
  the acceptance brackets; per the `roadmap-builder.md`
  contract, `evidence-story-{n}.md` files are created **only
  when the story actually ships** (i.e., flips to `done`),
  so they don't exist yet. They'll be authored at the same
  time the stories close.
- [ ] `final-summary.md` records what shipped + what surprised
  us + handoff notes for AIPI-2.
  **Pending phase exit.** Per the contract, `final-summary.md`
  is "created on phase exit and is immutable afterwards."
  Writing it now would either be premature or get rewritten;
  it lands when the last story closes.
- [ ] `pm/roadmap/aipi-lite/README.md` reflects phase 1 done +
  phase 2 not-started.
  **Pending phase exit.** README still shows phase 1 as
  in-progress; flip happens with the same commit that lands
  `final-summary.md`.

## Test Plan

- Manual: have a *fresh* user (or simulate one) provision a
  device onto a new network using only `docs/PROVISIONING.md`.
  Capture friction points and either fix or record in
  final-summary.

## Notes

- Per the spirit of HoldSpeak's PMO contract: evidence lives in
  the per-story evidence files, not summarized. The
  final-summary references them.
- AIPI-2 hands off to a host-side change (bridge → HoldSpeak
  WS forwarder). Make sure the final-summary's "Handoff" section
  names what assumptions phase 1 baked in (NVS layout, BLE
  resource usage, captive portal port, etc.) so AIPI-2 can
  reference them rather than re-derive.

### 2026-05-07 — partial close

`docs/PROVISIONING.md` shipped. The other three acceptance
bullets (per-story evidence files, `final-summary.md`, README
phase-1-done flip) are sequenced behind the hardware
verification of AIPI-1-01..05, which the user has deferred.
Story stays `in-progress` until those stories close. When they
do, the close-out commit will:

1. Author each `evidence-story-{n}.md` with build/flash/test
   evidence (most of the inputs are already inline in the
   story files; it's a re-format pass).
2. Flip stories 01..05 to `done`.
3. Author `final-summary.md` per `roadmap-builder.md` §2.5.
4. Freeze `current-phase-status.md`.
5. Bump `pm/roadmap/aipi-lite/README.md`: phase 1 → done,
   "Current phase" pointer moves to phase 2.

Until then this story is the only thing tracking phase-exit
work; everything else in the phase has its evidence inline.
