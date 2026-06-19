# Phase 0 — Final Summary

- **Phase opened:** 2026-06-18
- **Phase closed:** 2026-06-18
- **Chunks shipped:** 5 stories (2 commits on `main`)

## Goal — was it met?

> Extract all domain entities from the existing HoldSpeak implementation into a
> language-neutral contract package (`holdspeak-contracts`): an Entity Catalog,
> JSON Schemas, and Serialization Contracts, validated against real desktop
> payloads … Also lock the charter's open decisions.

**Yes.** The contract layer (charter Layer 1) exists, is grounded in shipped
`holdspeak/` code, and is mechanically validated against real serializations. The
charter's open decisions are locked.

## Exit criteria — final state

- [x] Every charter Layer-1 entity catalogued + traced to source — [evidence-01](./evidence-story-01.md).
- [x] A JSON Schema per entity validates a real payload with zero errors —
  [evidence-02](./evidence-story-02.md) (9 schemas; validator green).
- [x] Serialization contract written + `holdspeak-contracts` home decided —
  [evidence-03](./evidence-story-03.md).
- [x] Golden fixtures round-trip through a validator both runtimes can run —
  [evidence-04](./evidence-story-04.md).
- [x] Truncated Gate list confirmed + deferred decisions locked —
  [evidence-05](./evidence-story-05.md).

## Stories shipped

| ID | Title | Commit | Date |
|---|---|---|---|
| HSM-0-01 | The entity catalog | 28d14ea | 2026-06-18 |
| HSM-0-02 | JSON Schemas | 28d14ea | 2026-06-18 |
| HSM-0-03 | Serialization contracts + package | 28d14ea | 2026-06-18 |
| HSM-0-04 | Conformance fixtures | (close bundle) | 2026-06-18 |
| HSM-0-05 | Charter reconciliation & decisions lock | (close bundle) | 2026-06-18 |

## Stories cut or deferred

| ID | Title | Reason | Re-targeted to |
|---|---|---|---|
| — | dictation-journal fixture/schema | "keep-lightweight" entity; lower contract priority | follow-up (additive) |

## Surprises and lessons

- **`Artifact` is a tagged union**, not ten classes — the single biggest shape
  decision; HSM-0-02 models one discriminated type with an open `structured_json`.
- **`mir_profile` is not a serialized Meeting field** — it lives in config and on
  `IntentWindowSummary.profile`. So HSM-7-03 ("profile on the Meeting") is a
  genuine *contract addition*, recorded for Phase 7.
- **Two distinct "profile" vocabularies** (MIR meeting profile vs dictation target
  profile) — the contract forbids a bare `profile` to prevent conflation.
- **Mixed timestamps/IDs in one real payload** — resolved once in the contract:
  string IDs, UTC-`Z` instants (owner decision), float intra-meeting offsets.
- Reverse-engineering from a **live `to_dict()`** (not the prose catalog) caught
  the nested `intel_status` shape and the derived `duration` keys.

## Handoff to phase 1

- **Now available:** `contracts/` — the entity catalog, 9 JSON schemas, the
  serialization contract (10 locked rules + the worked Meeting→Swift example), two
  golden fixtures, and a green `validate.py`. Phase 1 writes the Swift `Codable`
  types against these and round-trips the fixtures (HSM-1-02).
- **Contract changed/canon:** `contract_version = "0.1.0"`, independent of DB
  version; wire = desktop snake_case; UTC-`Z` instants; string IDs;
  `holdspeak-contracts` is the in-repo `contracts/` tree.
- **Read first:** `contracts/SERIALIZATION-CONTRACT.md`, then `ENTITY-CATALOG.md`.
- **Carried dependency:** if Phase 5 picks Core ML, its `MLState` KV cache sets an
  iOS-18+ floor — reconcile with Phase 1's minimum-deployment-target decision
  (P6 in `../PROGRAM-RISKS.md`).

## Final asset / test posture

- 9 JSON schemas, 2 golden fixtures, 1 validator (`validate.py`) — **10 checks
  green** (6 entity validations + UTC-Z + round-trip + MIR-profile + negative).
- Program risk register seeded (`../PROGRAM-RISKS.md`, P1–P7).
- Charter Quality Gates confirmed as the list of record.
