# HS-156-02 - One confirmation applies everything (through the existing machinery)

- **Project:** holdspeak
- **Phase:** 156
- **Status:** backlog
- **Depends on:** HS-156-01
- **Unblocks:** HS-156-04, HS-156-07
- **Owner:** unassigned

## Problem

A recommendation that hands the owner a to-do list failed. One
confirmation must download, define, and wire everything — through the
EXISTING Library/Assignments machinery, receipted end to end, resumable
on failure (settled design D2).

## Scope

- **In:** `POST /api/front-door/apply {pack_id}` executes the pack's
  plan as an ordered, idempotent sequence over EXISTING surfaces only:
  model-library download (egress badge + receipt intact), define-
  endpoint for LAN ingredients, profile creation, assignments
  editor/set for all seven groups. A durable plan row per apply with
  per-item state (queued → running (progress) → done/failed); GET
  returns it for the UI; re-apply continues from the first unfinished
  item — a crash never leaves a half-desk unaccounted. No new
  authority: a fence test asserts the apply path contains no direct
  DB writes to library/assignment tables (service calls only).
- **Out:** the door UI (03), pack auto-changes after setup (recorded).

## Acceptance criteria

- [ ] Applying a fixture pack on a fresh isolated hub yields: profiles exist, all seven groups assigned, receipts for every download and wiring step; a REAL chat turn then resolves through the assigned engine (real coordinator, fake engine at the endpoint).
- [ ] Kill the apply mid-plan (fault injection after item N) → GET shows the plan with the failure named; re-apply completes the remainder; nothing is double-created (idempotency proven).
- [ ] The no-parallel-authority fence passes (apply uses only the existing service seams).
- [ ] The .43-shaped ingredient (an explicit LAN endpoint) wires via define-endpoint and carries its provenance label.

## Test plan

- **Unit:** `tests/unit/test_front_door_apply.py` (plan execution, idempotency, fault injection, fence).
- **Integration:** the isolated-hub leg above.
- **Manual / device:** story 05.

## Notes / open questions

- Download progress rides the existing model-library progress surface; the plan aggregates it, never re-implements it.
