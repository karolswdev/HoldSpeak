# HS-164-06 - The walk: Gate A on glass — the desk works alone

- **Project:** holdspeak
- **Phase:** 164
- **Status:** done
- **Depends on:** HS-164-04 (rig vs the wire; face legs after 05's functional)
- **Unblocks:** HS-164-07
- **Owner:** unassigned

## Problem

The P5 exit: Gate A observes at least two useful unattended runs
without confirmation prompts or duplicate effects. Measured on
glass, across ticks — not within one run.

## Scope

- **In:** tests/e2e/test_hs164_unattended_glass.py (the house rig —
  BUILD FIRST, the 163 law): (1) THE GATE A LEG — seeded room,
  opt-in enabled with a real grant, watch cadence due → drive the
  conductor's two blocks (or their entry seams) across ticks → TWO
  useful unattended runs complete with real effects, ZERO
  confirmation prompts anywhere, ZERO duplicate effects across both
  runs (counted via the wire: door items, applied proposals,
  updates — before/after each tick); provenance visible. (2) THE
  DEDUP-ACROSS-TICKS LEG — same watermark re-requested on a later
  tick ⇒ resolves to the existing run, nothing minted. (3) THE
  CIRCUIT LEG — a failing source opens the circuit, visible on the
  face, intervention chip lands; recovery closes it. (4) THE OPT-OUT
  LEG — disable mid-cadence ⇒ the next tick runs NOTHING, honestly
  receipted. Shots both viewports >20KB; ×2 deterministic; no raw
  ids; effect inventory + stopwatch JSONs measured.
- **Out:** MCP, provider-write.

## Acceptance criteria

- [ ] Gate A proven: ≥2 useful unattended runs, zero prompts, zero duplicate effects across ticks — counted, not asserted.
- [ ] Dedup, circuit, and opt-out legs deterministic ×2; overflow zero; no raw ids.
- [ ] The walk record carries the unattended inventory (what ran alone, what it did, what it refused).

## Test plan

- **E2E:** the four legs; build-first; ×2.
