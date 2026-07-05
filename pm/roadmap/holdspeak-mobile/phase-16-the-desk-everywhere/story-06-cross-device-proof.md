# HSM-16-06 — The cross-device proof

- **Project:** holdspeak-mobile
- **Phase:** 16
- **Status:** todo — **walk staged** (2026-07-05: the press-play runbook is
  [`HSM-16-06-WALK.md`](./HSM-16-06-WALK.md), four checks ~15 min, joins the standing couch
  queue; rescoped to also carry 16-09's device beat, 16-08's manifest round-trip, and the
  16-04 web cross-surface Ask)
- **Depends on:** HSM-16-05 (the wiring).
- **Unblocks:** HSM-16-07 (docs the proof informs).
- **Owner:** the owner's hands (agent-staged)

## Problem

Sync is only real when you watch a thing you made on one device appear on another. This story is the
owner-witnessed, real-metal demonstration that the organization layer flows across the mesh — the
Phase-15-style proof, for the Desk.

## Scope

- **In:** a recorded, owner-witnessed run on real hardware (the iPad Air M4 paired to the Mac hub, the
  web Desk open in a browser):
  1. Create a **Knowledge Base** on the iPad, classify two meetings into it.
  2. It appears on the **desktop** store and on the **web Desk** — same KB, same members.
  3. Classify a third meeting into it **from the web** → it shows up inside the KB **on the iPad**.
  4. Air-gap honest: this is the user's own devices; nothing left the mesh (the egress badge / the
     Phase-15 contract holds).
- **Out:** new features. If the proof exposes a bug, fix it under the relevant 16-0x story, not here.

## Acceptance criteria

- [ ] The full loop is demonstrated on real devices and captured (screenshots / short clips under this
      phase's `screenshots/` or `results/`).
- [ ] iPad → desktop → web and web → desktop → iPad both proven for a KB + its membership.
- [ ] Verified on the device, not seeded fixtures (see [[feedback_verify_on_device_not_seeded]]).

## Test plan

- The proof IS the test: a witnessed cross-device run, artifacts committed. Plus the green unit/
  integration suites from 16-02/16-03/16-05 as the automated backstop.
