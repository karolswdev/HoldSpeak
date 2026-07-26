# HS-105-02 - Drop-onto — composition by direct manipulation

- **Project:** holdspeak
- **Phase:** 105
- **Status:** done
- **Depends on:** HS-105-01
- **Unblocks:** HS-105-07
- **Owner:** unassigned

## The thesis (the bar)

On Workbench you dropped a file on a tool and the tool ran on it.
This is the single missing atom that turns the desk's objects from
decorations into machines: the moment a note dropped onto an agent
RUNS that agent with the note as grounding, the lamp is no longer a
mascot — it is a tool on a bench. The entire grounding wire already
exists (`buildGrounding` and the Phase-87/88 hydration spine); today
it is reachable only through composers. This story makes the world
itself the composer.

## Problem

Dragging an object over another object today means nothing. Objects
cannot act on each other by direct manipulation, so every
composition routes through a panel — the opposite of an operating
surface.

## Recipe

1. **The drop matrix is contract data.** Extend the Desk Primitive
   contract with per-kind declarations: what this kind ACCEPTS
   (dropped-onto) and what dropping produces — a named verb, never
   generic "interact." First matrix, deliberately small and fully
   honest:
   - note / meeting / kb → **agent-recipe**: run the recipe with the
     dropped object as grounding (the exact `buildGrounding` wire
     the ask/steer composers use — byte-identical grounding, the
     Phase-88 parity rule).
   - note / meeting → **kb**: propose ingestion (the propose-approve
     shape; the KB never silently mutates — Article V).
   - any primitive → **zone**: file it (this exists as placement;
     it joins the matrix as its formal case).
   - any groundable → **the orb**: open Speak with the object held
     as context (the HSM-16-04 held-selection carve-out reused).
   Everything else refuses BY NAME.
2. **The physics of intent.** In the engine (`gl/engine.ts`): while
   dragging, a viable target under the cursor lights its selected
   state (the HS-105-01 image — one grammar, reused) plus a verb
   tag naming what release does ("Run with this", "File", "Add to
   KB"); a non-target stays inert — never a hover state that lies.
   Release over a viable target fires the verb; release elsewhere is
   a move, exactly as today. Touch: drag already arms on hold; the
   same lighting applies.
3. **The act lands where acts land.** A drop that runs a recipe
   produces the SAME run/artifact objects a composer-launched run
   produces (run-born artifacts, Phase 74 lineage naming the drop
   source); a drop that proposes ingestion raises the standard
   proposal card. No new result surfaces — the drop is an entrance,
   not a new system.
4. **Refusal is visible and quiet.** Dropping the unacceptable
   snaps the object back with a brief shake-and-return (Reduce
   Motion: no shake, position return only) — no toast prose, no
   modal (the no-modals rule).
5. **The undo half-step.** A drop that only files or grounds is
   inherently reversible; a drop that RUNS is not — so the verb tag
   is the consent moment. Keep the matrix honest: no destructive
   verb ever rides a drop in this phase.

## Out of scope

- Multi-object drops (drop a selection of three — after the sitting
  proves the single-object grammar); drops that write outside the
  desk (actuator territory); any new composer UI.

## Acceptance

- Every matrix row proven live on a staged hub: note→agent runs on
  real metal (the .43 endpoint) and the artifact's lineage names the
  drop; note→kb raises the proposal; groundable→orb opens Speak
  holding context; a refused pair shakes back, named in the test.
- Target lighting appears only over viable targets, with the verb
  tag, both viewports + touch context.
- Grounding parity pinned: the drop path and the composer path
  produce byte-identical grounding for the same object.
- The matrix lives in the contract and the UI derives from it — a
  census forbids hardcoded kind-pairs in components.

## Test plan

- **Unit:** matrix resolution (accepts/verb/refuse) for every kind
  pair; grounding parity.
- **Integration:** the run entrance producing the same wire payload
  as the composer entrance.
- **Live (evidence):** the headed walk above with real pointer
  sequences (the 101 round-9 method), screenshots read.

## Chef's notes

- The verb tag under the cursor is the consent surface. If the
  tester cannot predict from the tag alone exactly what release
  does, rewrite the tag before touching code.
- Resist growing the matrix during build. Four honest rows that
  always work beat twelve that mostly work; the matrix is contract
  data precisely so later phases can add rows cheaply.
- Watch the drag-vs-select arm thresholds from the 101 tap work
  (`lastTap` 400ms/8px) — the drop grammar must not regress
  tap-to-open on touch.
