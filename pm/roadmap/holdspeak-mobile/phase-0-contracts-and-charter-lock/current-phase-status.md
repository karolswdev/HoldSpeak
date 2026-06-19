# Phase 0 — Contract Extraction & Charter Lock

**Status:** CLOSED ✅ (5/5) 2026-06-18 — see [`final-summary.md`](./final-summary.md).
Track A of the Council
Implementation Charter. The convergence phase: it fixes the shared
`holdspeak-contracts` schema every later phase builds on, and it reconciles the
charter's open items (the truncated Gate list, the deferred tech decisions).

**Last updated:** 2026-06-18 (**HSM-0-01 + HSM-0-02 built** — the entity catalog
([`../contracts/ENTITY-CATALOG.md`](../contracts/ENTITY-CATALOG.md)) is
cross-checked both ways against a **live** `MeetingState.to_dict()` serialization
(captured as [`../contracts/fixtures/meeting-sample.json`](../contracts/fixtures/meeting-sample.json));
seven draft-2020-12 JSON Schemas
([`../contracts/schemas/`](../contracts/schemas/)) validate that real payload with
**zero errors** and a corrupted payload fails loudly — green via
[`../contracts/validate.py`](../contracts/validate.py). Both stories are content-
complete, awaiting a commit (status "built (awaiting commit)"; flip to done + ship
`evidence-story-0{1,2}.md` in the PR). Key correction from the live payload:
`mir_profile` is NOT a serialized Meeting field, so HSM-7-03 is a contract
addition. **HSM-0-03 also built**: the serialization contract
([`../contracts/SERIALIZATION-CONTRACT.md`](../contracts/SERIALIZATION-CONTRACT.md))
locks ten cross-runtime rules + the package home. **Owner confirmations received
(HSM-0-05):** Quality Gates 3–7 confirmed (CHARTER de-flagged); instants
standardized to **UTC `Z`** (folded into the contract + fixture + a green
validator UTC-Z check). Three of five stories built; HSM-0-05 in progress (only
the program-risk-register + holdspeak cross-link remain). Next: HSM-0-04.).

## Goal

Extract all domain entities from the existing HoldSpeak implementation into a
language-neutral contract package (`holdspeak-contracts`): an Entity Catalog,
JSON Schemas, and Serialization Contracts, validated against real desktop
payloads, so the new Apple runtime can interoperate with the desktop and server
runtimes. Also lock the charter's open decisions so Phases 1–11 build on settled
ground.

## Scope

- **In:** the Entity Catalog (HSM-0-01); a JSON Schema per canonical entity
  (HSM-0-02); the serialization contract + the `holdspeak-contracts` package
  layout/home (HSM-0-03); golden conformance fixtures + a cross-runtime validator
  (HSM-0-04); the charter reconciliation + decisions/risk lock (HSM-0-05).
- **Out:** any Swift code, Xcode workspace, or SPM package (Phase 1). Any runtime
  behavior change to the desktop product (this phase reads it; it may add a
  schema-export or validation helper, but does not alter desktop behavior). The
  Runtime Core implementation (Layer 2) and Providers (Layer 3) are later phases.

## Exit criteria (evidence required)

- [ ] Every entity in the charter's Layer-1 list (`Meeting`, `Transcript`,
      `Speaker`, `Segment`, `ActionItem`, `Decision`, `Risk`, `Requirement`,
      `Artifact`, `IntelJob`) is catalogued with every field traced to a desktop
      source (file:line or a captured payload) — Track A gate "all desktop
      entities mapped" (HSM-0-01).
- [ ] A JSON Schema exists per canonical entity and validates a real desktop
      payload sample with zero errors (HSM-0-02).
- [ ] The serialization contract is written (naming, enums, optionality,
      timestamps, versioning) and the `holdspeak-contracts` package home is
      decided and recorded (HSM-0-03).
- [ ] Golden fixtures round-trip through a validator both runtimes can run
      (HSM-0-04).
- [ ] The truncated Quality Gate list is confirmed with the owner and the
      deferred decisions (Track-F tech, repo home, version scheme) are locked or
      explicitly parked with a default (HSM-0-05).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-0-01 | The entity catalog | done | [story-01](./story-01-entity-catalog.md) | [evidence-01](./evidence-story-01.md) |
| HSM-0-02 | JSON Schemas | done | [story-02](./story-02-json-schemas.md) | [evidence-02](./evidence-story-02.md) |
| HSM-0-03 | Serialization contracts + package | done | [story-03](./story-03-serialization-contracts.md) | [evidence-03](./evidence-story-03.md) |
| HSM-0-04 | Conformance fixtures | done | [story-04](./story-04-conformance-fixtures.md) | [evidence-04](./evidence-story-04.md) |
| HSM-0-05 | Charter reconciliation & decisions lock | done | [story-05](./story-05-charter-reconciliation.md) | [evidence-05](./evidence-story-05.md) |

## Where we are

HSM-0-01 and HSM-0-02 are built (content-complete, awaiting a commit). The entity
catalog ([`../contracts/ENTITY-CATALOG.md`](../contracts/ENTITY-CATALOG.md)) maps
all ten charter Layer-1 entities to shipped `holdspeak/` source and is cross-checked
both ways against a live serialization. Seven draft-2020-12 schemas
([`../contracts/schemas/`](../contracts/schemas/): meeting, segment, bookmark,
intel-snapshot, action-item, artifact, intel-job) validate a real desktop payload
with zero errors and reject a corrupted one — [`../contracts/validate.py`](../contracts/validate.py)
is green (3 entities + negative). The findings that shape the rest of the phase:
`Artifact` is a tagged union; "profile" is two distinct concepts (the MIR one is
Phase 7's); `mir_profile` is not a serialized Meeting field (HSM-7-03 is a contract
addition); and timestamps/IDs are mixed in one payload. HSM-0-03 is now also built:
[`../contracts/SERIALIZATION-CONTRACT.md`](../contracts/SERIALIZATION-CONTRACT.md)
locks ten cross-runtime rules (wire = desktop snake_case; ISO instants + float
offsets; string ids; closed enums + open `structured_json`; reserved `egress`;
`contract_version 0.1.0` independent of DB version; the package home) with a
worked Meeting→Swift example — Phase 1 is unblocked. The owner's two HSM-0-05
calls are now in: **Quality Gates 3–7 confirmed** (CHARTER de-flagged) and
**instants standardized to UTC `Z`** (folded into the contract §2, the fixture,
and a green `validate.py` UTC-Z check — so the standard is tested, not just
written). **Phase 0 is CLOSED ✅ (5/5)** — HSM-0-04 broadened the fixtures (9
schemas total, actuator + balanced/architect intent windows, a round-trip +
MIR-profile + UTC-Z sweep, validator green across 10 checks) and HSM-0-05 closed
the reconciliation (program risk register `../PROGRAM-RISKS.md`, `holdspeak`
HANDOVER cross-link). See [`final-summary.md`](./final-summary.md). Phase 1
(Mobile Foundation) is the current phase.
Next authorable step: HSM-0-04 (broaden the fixtures — add the parked entities,
multiple MIR profiles, and a parse→re-serialize round-trip assertion on top of the
existing green validator).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The desktop domain has more entities/fields than the charter's 10 | high | Catalog from code, not from the charter list; treat the 10 as the floor | The catalog can't close because entities keep appearing — timebox and ship the core 10, park the long tail |
| Python↔Swift impedance (casing, optionality, dates) leaks into every schema | medium | Resolve it once in the serialization contract (HSM-0-03) before writing Swift types in Phase 1 | A schema needs a Swift-specific shape — escalate to the contract, don't fork it |
| ~~The truncated charter Gate list hides a real acceptance bar~~ — **RETIRED 2026-06-18** | — | Owner confirmed Gates 3–7 as-reconstructed; CHARTER is the gate list of record | — |
| Contract version coupled to SQLite `SCHEMA_VERSION` by accident | low | Decide the version scheme explicitly in HSM-0-03 | A schema change forces a DB migration with no behavior change |

## Decisions made (this phase)

- 2026-06-18 — The mobile runtime is a separate roadmap project
  (`holdspeak-mobile`, prefix `HSM`), not a continuation of the `holdspeak`
  phase line — distinct language, workspace, and deliverables — owner-directed
  charter scaffold.
- 2026-06-18 (HSM-0-03) — Wire format = the desktop's `to_dict()` snake_case
  shape, adopted as-is (no desktop churn); Swift maps via a key strategy.
- 2026-06-18 (HSM-0-03) — `contract_version = "0.1.0"` (semver), **independent**
  of any DB `SCHEMA_VERSION`, additive-only within a major, ignore-unknown-fields
  on decode, carried in the sync envelope (not per-entity).
- 2026-06-18 (HSM-0-03) — `holdspeak-contracts` is a versioned in-repo
  `contracts/` tree; extract to a standalone repo only when a second independent
  consumer appears.
- 2026-06-18 (HSM-0-03) — IDs are strings on the wire; instants are ISO-8601
  strings, intra-meeting offsets are float seconds; `mir_profile` ≠
  `target_profile` (never a bare `profile`).
- 2026-06-18 (HSM-0-05, **owner**) — Quality Gates 3–7 confirmed as-reconstructed;
  `CHARTER.md` is the gate list of record (caveats removed).
- 2026-06-18 (HSM-0-05, **owner**) — Instants standardize on **UTC `Z`**; folded
  into the serialization contract §2, the fixture, and a green `validate.py`
  UTC-Z check. Desktop bare-local normalizes at the contract boundary.

## Decisions deferred

- Track-F local-inference engine (MLC-LLM vs llama.cpp vs CoreML-native) —
  trigger: Phase 5 open — default: evaluate all three in Phase 5, do not pre-pick
  here. **Owner's inference brief received 2026-06-18**
  ([`../research/inference-on-apple.md`](../research/inference-on-apple.md)):
  candidate set narrowed to **Core ML / llama.cpp+GGUF / MLC-LLM** (Ollama/vLLM
  are Mode-B/C companions, not in-app); 4-bit PTQ default; charter per-device
  model tiers confirmed. **RESOLVED 2026-06-19 (HSM-5-01): the engine is
  `llama.cpp` + GGUF** — a banked decision from the canon (no bake-off, per the
  owner's no-spikes directive), reversible behind `ILLMProvider`, MLX as the
  fallback. See `../phase-5-local-inference/evidence-story-01.md`.

(The Quality-Gate-list and timestamp questions that were deferred here are now
resolved — see "Decisions made" above.)
