# HS-147-05 — Snapshot polish riders (the 146 ledger pair)

- **Project:** holdspeak
- **Phase:** 147
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-147-07
- **Owner:** unassigned

## Problem

The two Phase 146 close-counsel ledger items, folded in by the
owner's pick: (1) the IMPORT SCREENSHOT button swallows 422 upload
refusals behind a bare catch (the desk-drop path is honest; the
button path is not); (2) the snapshot direct-dispatch fallback does
not pre-filter vision-capable profiles — failure is a named refusal
plus wasted inference, never bad data, but it burns a real model
call to learn what the profile list already knows.

## Scope

### In

- Surface 422 (and kin) upload refusals from the IMPORT SCREENSHOT
  button path in-flow beside the button — named, fewest words,
  matching the drop path's existing honesty; kill the bare catch.
- Pre-filter the direct-dispatch fallback to vision-capable
  profiles; when none qualify, the existing NAMED refusal
  `no_vision_model_assigned` fires WITHOUT dispatching an inference
  call.

### Out

- The real-vision-model probe (stays a named backlog moment — a
  control-vs-treatment sitting when `.43` grows a vision model or a
  cloud one is assigned); any router/assignment changes.

## Acceptance criteria

1. A refused upload (oversized/wrong-type → 422) shows its named
   refusal at the button, in-flow, both widths — shot-proven.
2. With zero vision-capable profiles, the fallback refuses by name
   with ZERO inference dispatches (assert call count).
3. The happy screenshot path is regression-free (the story-07
   anchored review flow untouched).

## Test plan

Web component test for the button refusal path + live shot;
snapshot service unit tests (pre-filter selection, zero-dispatch
refusal, happy path); focused `tests/` snapshot suite green.
