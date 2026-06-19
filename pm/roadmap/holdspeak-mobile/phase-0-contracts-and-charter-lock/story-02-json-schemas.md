# HSM-0-02 — JSON Schemas

- **Project:** holdspeak-mobile
- **Phase:** 0
- **Status:** done
- **Depends on:** HSM-0-01
- **Unblocks:** HSM-0-03, HSM-0-04
- **Owner:** unassigned

## Problem

The entity catalog (HSM-0-01) is prose. Interop needs machine-checkable schemas
both runtimes can validate against, so "compatible" is provable rather than
asserted.

## Scope

- **In:** one JSON Schema (draft 2020-12) per canonical entity from the catalog,
  under the contracts package home (e.g. `contracts/schemas/*.json`). Schemas
  reference each other where entities nest (Meeting embeds/refs Segments,
  Speakers, Artifacts). A small validation script that loads a real desktop
  payload and validates it against the schema set.
- **Out:** the human-facing serialization rules (HSM-0-03 — naming/version/enum
  policy lives there; the schemas encode it). Swift `Codable` types (Phase 1).

## Acceptance criteria

- [ ] A schema file exists for every entity catalogued in HSM-0-01's core set.
- [ ] Each schema validates at least one real desktop payload sample with zero
      errors (paste the validator output into evidence).
- [ ] Enum fields are constrained to the catalogued vocabulary; unknown values
      fail validation.
- [ ] Optional vs. required is explicit on every field and matches desktop
      behavior (a field desktop sometimes omits is `not required`).
- [ ] Cross-entity references resolve (the schema set validates a full nested
      Meeting payload, not just leaf entities).

## Test plan

- Unit: the validation script run against captured desktop payloads → 0 errors;
  and against a deliberately corrupted payload (bad enum, missing required) → it
  fails loudly. Both pasted into evidence.
- Manual: n/a.

## Notes / open questions

- Pick one schema dialect and state it (draft 2020-12 unless HSM-0-03 decides
  otherwise) so the Swift side (Phase 1) and the desktop side use the same one.
- Timestamps: decide ISO-8601 string vs. epoch here in line with HSM-0-03; the
  schema must pin exactly one.
