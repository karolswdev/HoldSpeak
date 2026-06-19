# HSM-0-03 — Serialization contracts + the `holdspeak-contracts` package

- **Project:** holdspeak-mobile
- **Phase:** 0
- **Status:** done
- **Depends on:** HSM-0-02
- **Unblocks:** HSM-0-04, all of Phase 1
- **Owner:** unassigned

## Problem

JSON Schemas describe shape, but cross-runtime interop also needs settled
*policy*: how Python and Swift agree on field casing, optionality, enum spelling,
timestamps, and versioning. Without one written contract, each runtime makes its
own `Codable`/Pydantic choices and they drift. The charter also names a
deliverable — `holdspeak-contracts` — whose home and layout must be decided.

## Scope

- **In:** `contracts/SERIALIZATION-CONTRACT.md` covering field naming convention
  (and any Python↔Swift casing map), optionality rules, the canonical enum
  vocabulary, timestamp format, null vs. absent semantics, and the
  `contract_version` scheme + compatibility policy (what a consumer does with an
  unknown newer field). Plus the `holdspeak-contracts` package layout decision
  (directory structure + home: this repo vs. standalone) recorded with rationale.
- **Out:** the schemas themselves (HSM-0-02). Generated Swift/Python types
  (Phase 1 generates Swift; desktop wiring is follow-on).

## Acceptance criteria

- [ ] The naming, optionality, enum, timestamp, and null rules are written and
      each is consistent with every HSM-0-02 schema (no schema violates its own
      contract).
- [ ] `contract_version` is defined, its relationship to DB `SCHEMA_VERSION`
      stated (independent unless argued otherwise), and the unknown-newer-field
      policy is specified.
- [ ] The `holdspeak-contracts` package layout is documented and its home is
      decided (defaulting to a versioned directory in this repo per the phase
      decision register) with the trigger that would move it standalone.
- [ ] A reader can take any HSM-0-02 schema and the contract and predict the
      exact Swift `Codable` declaration Phase 1 will write.

## Test plan

- Manual: walk one entity (e.g. `Meeting`) end to end — catalog → schema →
  contract → the predicted Swift type — and confirm no ambiguity remains.
- Unit: n/a (the validator in HSM-0-04 enforces the contract mechanically).

## Notes / open questions

- This is the single place to absorb Python↔Swift impedance. Resist
  per-entity special cases; a special case is a contract clause, not a one-off.
- Decide the dialect/version once and make HSM-0-02 conform to it (may require a
  small back-edit of the schemas — acceptable, they ship in Phase 0).
