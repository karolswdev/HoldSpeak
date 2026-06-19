# HSM-1-02 — Contracts Swift Codable types

- **Project:** holdspeak-mobile
- **Phase:** 1
- **Status:** done
- **Depends on:** HSM-1-01, HSM-0-04
- **Unblocks:** HSM-1-04 (and every later Runtime Core / Providers phase)
- **Owner:** unassigned

## Problem

The mobile runtime is only "compatible with desktop" if its Swift domain types
serialize to the same wire format the desktop product emits. Phase 0 produced the
JSON Schemas (HSM-0-02) and the golden conformance fixtures (HSM-0-04). This story
lands the Swift `Codable` types that mirror those schemas and proves they
round-trip the fixtures, so interop is tested rather than asserted.

## Scope

- **In:** Swift `Codable` types in the `Contracts` target for the canonical
  entities the Phase-0 schemas define (`Meeting`, `Transcript`, `Speaker`,
  `Segment`, `ActionItem`, `Decision`, `Risk`, `Requirement`, `Artifact`,
  `IntelJob`, plus any sibling Phase 0 catalogued and kept). The `CodingKeys` /
  decoding strategy needed to match the HSM-0-03 wire format (casing, optionality,
  enums, timestamps). A round-trip test that decodes every HSM-0-04 fixture and
  re-encodes to a semantically-equal payload.
- **Out:** the schemas/fixtures themselves (Phase 0 owns them — consume, do not
  redefine). Any Runtime Core behavior (engine/persistence/sync) — these are pure
  data types. UI bindings. Anything in `RuntimeCore`/`Providers`/`Hosts` beyond
  what's needed to compile the types in `Contracts`.

## Acceptance criteria

- [ ] A `Codable` Swift type exists per canonical entity in the Phase-0 schema
      set, in the `Contracts` target.
- [ ] Enum-valued fields (statuses, MIR profile, egress scope, artifact type) are
      modeled as Swift enums whose raw values match the desktop vocabulary
      verbatim, with a defined behavior for an unknown value (do not crash on a
      future enum case).
- [ ] Every HSM-0-04 golden fixture decodes into the Swift types without error.
- [ ] Each decoded fixture re-encodes to a payload semantically equal to the
      original (schema-valid + field-equal; key order/whitespace ignored) — a
      passing round-trip test in evidence.
- [ ] A deliberately contract-violating payload fails to decode (negative case in
      the test), proving the types reject malformed input.

## Test plan

- Unit: `swift test` runs a round-trip suite over `contracts/fixtures/*.json`
  (the HSM-0-04 set) — all decode and re-encode semantically-equal; one mutated
  fixture fails to decode. Green log + the negative case both in evidence.
- Integration: n/a (the cross-runtime validator is HSM-0-04's; this story is the
  Swift side of the same fixtures).
- Manual / device: n/a.

## Notes / open questions

- Casing/optionality/date impedance is resolved at the contract level (HSM-0-03),
  not per-type here. If a fixture won't round-trip, escalate to the serialization
  contract rather than special-casing one struct — record any such escalation.
- Unknown-enum handling matters for forward compatibility (desktop may add a new
  artifact type before mobile knows it); pick a documented strategy and test it.
- These types are the foundation every later mobile phase builds on — keep them
  pure (no UIKit/SwiftUI), consistent with HSM-1-01's layer rule.
