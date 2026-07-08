# HSM-26-01 — The steering + rails presence contracts

- **Status:** done
- **Shipped:** 2026-07-08 — 9 schemas + fixtures; `validate.py` ALL CHECKS PASSED; real hub responses validated in `tests/unit/test_steering_contracts_fidelity.py` (8/8). Evidence: [evidence-story-01.md](./evidence-story-01.md).
- **Depends on:** desktop phase-87 + phase-88 (shipped)
- **Unblocks:** HSM-26-02, HSM-26-03, HSM-26-04

## Problem

B4 renders the belt, steering, and rails on the diorama by
INHERITING documented wire shapes, never scraping. But Phases 87/88
shipped those shapes without writing them down as contracts — the
`contracts/schemas/` dir has every durable primitive and nothing for
the presence-class steering/rails shapes. Without the contracts, the
iPad has nothing to converge on. This story writes them down and
proves them against the REAL hub responses.

## Scope

- In: JSON-Schema contracts (`contracts/schemas/`) for the presence
  shapes the Phase-87/88 routes emit — the coder-session peek, the
  arming grant, the steer request + result, the steering audit entry,
  the rails grounding ref, the rails journal entry, and the
  remote-events envelope; conformance fixtures
  (`contracts/fixtures/steering-and-rails-sample.json`) captured from
  the real routes; the shapes wired into `validate.py` (positive +
  a negative check); the entity-catalog + serialization-contract
  entries so the surfaces have one source of truth.
- Out: any Swift code (HSM-26-02+); new hub routes; the durable-sync
  ChangeSet path (these are presence, not synced primitives).

## Acceptance criteria

- [ ] A schema exists for each presence shape, `$id` under
      `holdspeak.dev/contracts/v0/`, `additionalProperties: false`,
      the source route named in its description.
- [ ] A conformance fixture for each shape validates against its
      schema with zero errors, and the fixture MATCHES the real hub
      response (captured from the route or its test, not invented).
- [ ] `validate.py` runs the new shapes (positive) plus a negative
      check (e.g. a remote-events envelope smuggling a file body is
      rejected; a steer request missing `text` is rejected).
- [ ] The entity catalog gains a "presence: steering + rails" section;
      the serialization contract notes the presence class is read from
      the documented routes, not synced.
- [ ] `uv run --with jsonschema python …/contracts/validate.py` exits 0.

## Test plan

- Validation: the contracts validator, green, with the new shapes and
  the negative check.
- Fixture fidelity: each fixture is byte-shaped like the real route
  (cross-checked against the desktop route tests / a live call).

## Implementation direction

- **Capture, don't invent.** For each shape, read the real response:
  the peek envelope from `coder_steering_routes.api_coder_peek`, the
  grant from `coder_steering.arm`, the steer result from `deliver`,
  the audit row from `db/steering.SteeringAuditEntry.to_dict`, the
  rails ref from `grounding_rails`, the journal entry from the
  `rails/journal` route, the envelope from `push_remote_envelope`.
- **Mirror the actuator-proposal schema's shape** (the closest
  presence-ish contract): required arrays, typed enums for the status
  vocabularies (peek `status`, steer `outcome`), `format: date-time`
  on instants.
- **The steer request carries the consent + grounding**: `text`,
  `submit`, optional `grounding` (with the `rails` array from
  Phase 88). The result's `status` enum is the full deliver vocabulary
  (`delivered` + the refusals).
- **Wire into validate.py** the same way the primitives are: a
  fixture file, a per-shape validator, positive prints, one negative.
