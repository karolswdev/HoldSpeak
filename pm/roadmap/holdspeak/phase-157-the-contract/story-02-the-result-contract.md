# HS-157-02 - The result contract: envelope, typed errors, ID prefixes

- **Project:** holdspeak
- **Phase:** 157
- **Status:** done
- **Depends on:** HS-157-01
- **Unblocks:** HS-157-05
- **Owner:** unassigned

## Problem

P0's exit is "schema/API names are agreed." Every later phase (the
Room's command contract API-001..003, the MCP family MCP-001..005,
the Watch effects) returns the same envelope: `result_kind`,
`project_id`, `project_revision`, `changed_refs`, typed
warnings/errors. If P1 invents these shapes ad hoc, Web and MCP
drift apart and the graduation promise breaks. Freeze the names now,
before any of them is implemented.

## Scope

- **In:** a typed contract module (e.g.
  `holdspeak/services/project_contracts.py`): the command result
  envelope shape, the closed `result_kind` vocabulary, the typed
  error codes (stale-revision conflict, idempotency conflict,
  not-found, validation, capability), and the ID prefixes from
  SRS_DOMAIN_DRIVER §4.1 (`pitem_`, `psrc_`, `pobs_`, `pprop_`,
  `prev_`, `pupd_`, `pchg_`, `pcmd_`, `pstpol_`, `pstrun_`,
  `pststep_`) as constants with generators/validators. A P0 contract
  doc (`docs/internal/project-rooms/CONTRACTS-P0.md` or a §-addition
  the suite prefers) recording the agreed names, each traced to its
  SRS requirement ID. Tests pinning the frozen names so a later
  rename is a deliberate suite amendment, not an accident.
- **Out:** implementing any command handler, revision column, or
  endpoint that USES the envelope — that is P1. No behavior change.

## Acceptance criteria

- [ ] The envelope fields, `result_kind` values, and error codes exist as typed constants and are asserted by tests; each name traces to an SRS requirement ID in the contract doc.
- [ ] All eleven ID prefixes from §4.1 have a generator + validator, tested (deterministic-prefix rules from the table respected in the generator signatures, even where determinism itself lands later).
- [ ] The contract doc is committed alongside the module and the SRS suite needs no contradicting edit — or the suite is amended in the same commit (README precedence rule).
- [ ] Zero branch-new; no runtime path imports change behavior.

## Test plan

- **Unit:** `tests/unit/test_project_contracts.py` (frozen names, prefix generators/validators, error-code table).

## What shipped

- `holdspeak/project_contracts.py` — beside `refs.py` (domain-grammar
  modules live at the package root; services under `services/`). Pure:
  enums, frozen dataclasses, validators, ID generators. Imports
  `holdspeak.refs` for `changed_refs` validation.
- `CommandResultEnvelope` (API-003/MCP-004): `result_kind`,
  `project_id`, `project_revision`, `changed_refs`
  (tuple[QualifiedRef]), `warnings`, `errors` — plus
  `validate_envelope()`.
- `ResultKind` — 16 closed values, each traced to §11.1 tools /
  §10 events / UPD-005 / API-002 (`no_change` for idempotent replay).
- `ProjectErrorCode` — 5 closed values: `stale_revision` (API-001),
  `idempotency_conflict` (API-002), `not_found`, `validation`
  (DOM-006/DB-004), `capability` (MCP-005).
- All 11 §4.1 ID prefixes: 8 uuid4-style generators + 3 DETERMINISTIC
  ones whose signatures take the §4.1 determinism inputs
  (`generate_pobs_id(adapter, source_id, source_version, fact_key)`,
  `generate_pprop_id(project_id, review_window_key, proposal_kind,
  target_ref, normalized_patch)`, `generate_pchg_id(project_id,
  project_revision, ordinal)`) — sha256 length-prefixed, 32-hex wire
  format matching the repo's `prefix_ + uuid4().hex` convention
  (`db/front_door.py:29`). Per-prefix validators.
- CONTRACTS-P0.md HS-157-02 section completed: envelope table,
  vocabulary + traceability, error codes, generator signatures.
- Tests: `tests/unit/test_project_contracts.py` (frozen names, good/
  bad envelopes, determinism, closed tables) — `167 passed in 0.46s`
  with the refs suite, re-run by the orchestrator under isolated HOME.

## Notes / open questions

- Nothing imports the module yet — by design. P1's command handlers are its first consumers; a rename after this commit is a deliberate suite amendment, not an accident.
- The design mapped cleanly onto the SRS: 16 kinds, 5 codes, no inventions needed.
