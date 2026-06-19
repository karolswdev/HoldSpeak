# Phase 0 — Agent Brief (read this first)

**Phase 0 — Contract Extraction & Charter Lock** for the HoldSpeak Mobile
Runtime (`holdspeak-mobile`). This is Track A of the Council Implementation
Charter ([`../CHARTER.md`](../CHARTER.md)) and the convergence phase for the
whole program: nothing above it is safe to build until the shared contracts are
fixed.

## 0. Mission

Produce `holdspeak-contracts` — the language-neutral schema that lets the new
Apple runtime and the existing Python/web runtime exchange Meetings,
Transcripts, Artifacts, Actions, MIR routing, and Intelligence Jobs without
either side depending on the other's implementation. Extract it from what the
desktop product *already does*, not from what we wish it did.

## 1. The one thing you must not get wrong

**The contracts are reverse-engineered from shipped behavior, not invented.**
The desktop product has been live since v0.3.0. Every entity, field, enum value,
and status string in the catalog must be traceable to real desktop code or a
real serialized payload. If the mobile runtime needs a field the desktop does
not emit, that is a charter-level addition recorded as a decision, not a silent
new field. Canon (the charter + the shipped code) wins over convenience.

## 2. Rules (the standing set)

- PMO gate: every shipping commit needs a fresh `.tmp/CONTRACT.md`; flip the
  story header + this phase's `current-phase-status.md` row + "Where we are" +
  the roadmap README "Last updated" in the same commit.
- Evidence is a real artifact: a generated schema file, a passing round-trip
  validation run, a diff of a desktop payload against the schema. Not a summary.
- One story = one PR. Each `done` ships its `evidence-story-{n}.md`.
- `pm/roadmap/**` is out of scope for the docs/voice guards, so prose dashes and
  HS-style IDs are fine in these files.

## 3. Ground truth to verify before writing schemas

- The shipped entities live in the Python codebase (meeting session models, the
  artifact/plugin outputs, the actuator proposal/decision records, the dictation
  journal). `docs/ARCHITECTURE.md` is the orienting map; the
  `holdspeak/meeting/` package models and the route response shapes are the
  literal field source.
- The DB is `SCHEMA_VERSION = 1` and additive (Phase 50). The contract version
  is its own thing — do not couple the wire-contract version to the SQLite
  schema version; record the mapping if one exists.
- MIR profiles are Balanced / Architect / Delivery / Product / Incident
  (`PLAN_PHASE_MULTI_INTENT_ROUTING.md`). The contract must carry the profile
  identity and the per-profile artifact emphasis, not bake one profile in.
- Egress scope is a first-class concept on the desktop side (the `egress` badge,
  Phase 62). A contract for Artifacts/Actions should be able to carry it.

## 4. Stories

- **HSM-0-01 — The entity catalog.** A single document cataloguing every domain
  entity the desktop emits (`Meeting`, `Transcript`, `Speaker`, `Segment`,
  `ActionItem`, `Decision`, `Risk`, `Requirement`, `Artifact`, `IntelJob`, plus
  any sibling the extraction surfaces), each field traced to its desktop source.
- **HSM-0-02 — JSON Schemas.** A JSON Schema per canonical entity, validated
  against real desktop payloads.
- **HSM-0-03 — Serialization contracts + the package.** The cross-runtime rules
  (field naming, enum vocab, optionality, timestamps, versioning) and the
  `holdspeak-contracts` package layout/home decision.
- **HSM-0-04 — Conformance fixtures.** Golden serialized examples both runtimes
  must round-trip, plus a validator both sides can run.
- **HSM-0-05 — Charter reconciliation & decisions lock.** Confirm the truncated
  Quality Gate list with the owner; lock the deferred decisions (Track-F
  inference tech, contracts repo home, version scheme); seed the program risk
  register.

## 5. Gotchas

- The desktop side is Python with Pydantic-ish shapes; field casing and optional
  handling differ from Swift `Codable` defaults. The serialization contract
  (HSM-0-03) is where that impedance is resolved once, explicitly.
- Intel output is non-deterministic; the contract describes the *shape* of an
  artifact, never asserts its content. Keep content judgments out of conformance.
- Do not start Swift package work here — that is Phase 1. Phase 0's deliverable
  is schema + rules + fixtures, language-neutral, plus (optionally) generated
  desktop-side validators. The Swift `Codable` types land in Phase 1 against
  these schemas.
