# Evidence — HSM-0-03 — Serialization contracts + the `holdspeak-contracts` package

- **Shipped:** 2026-06-18
- **Commit:** initial Phase-0 contracts bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `contracts/SERIALIZATION-CONTRACT.md` — ten locked cross-runtime rules
  (wire = desktop snake_case; UTC-`Z` instants + float offsets; string IDs;
  null-vs-absent; closed enums + open `structured_json`; `mir_profile` ≠
  `target_profile`; thin `Transcript` + `Speaker` roster; reserved `egress`;
  `contract_version 0.1.0` independent of DB version; the package home) + the
  worked Meeting→Swift example.

## Verification artifacts

- The contract was authored consistent with the HSM-0-02 schemas; the validator
  (`validate.py`) passing proves no schema violates the contract it encodes,
  including the UTC-`Z` instant rule (§2):
  `PASS utc-z: all instants are UTC Z-terminated`.
- The worked example walks `Meeting` end to end (wire → schema → rule → predicted
  Swift `Codable`) with no residual ambiguity.

## Acceptance criteria — re-checked

- [x] Naming/optionality/enum/timestamp/null rules written and consistent with
  every HSM-0-02 schema — §§1–8; validator green.
- [x] `contract_version` defined (`0.1.0`), independent of DB `SCHEMA_VERSION`,
  unknown-newer-field policy specified (ignore-on-decode) — §9.
- [x] `holdspeak-contracts` layout documented + home decided (in-repo `contracts/`
  tree; extract-to-standalone trigger recorded) — §10.
- [x] A reader can predict the Swift `Codable` from any schema + the contract —
  the worked Meeting table.

## Deviations from plan

Timestamp rule landed as UTC-`Z` (owner decision, HSM-0-05) rather than the
draft's "preserve bare-local" — folded in, with the desktop normalization boundary
documented.

## Follow-ups

`egress` is reserved but unpopulated (v0); per-`artifact_type` sub-schemas remain
open and additive.
