# HSM-6-01 — The artifact-generation engine

- **Project:** holdspeak-mobile
- **Phase:** 6
- **Status:** done
- **Depends on:** none
- **Unblocks:** HSM-6-02, HSM-6-03
- **Owner:** unassigned

## Problem

Phase 5 delivers a callable `ILLMProvider`, and Phase 0 locks the contract
shapes, but nothing yet turns a transcribed meeting into structured intelligence
on mobile. The Runtime Core (Layer 2) needs an artifact-generation engine: given
a finished transcript and an `ILLMProvider`, drive the model and bind its output
to the Phase-0 contracts as structured JSON. Without this seam, every artifact
type (HSM-6-02/03) has nowhere to live.

## Scope

- **In:** the Runtime-Core engine that takes a transcript (Phase-0 `Transcript`/
  `Segment`/`Speaker`) plus an injected `ILLMProvider`, prompts the model, parses
  its response, and emits Phase-0 `Artifact` records as structured JSON. The seam
  is UI-free and provider-agnostic (works against any `ILLMProvider` — local,
  homelab, or endpoint per the charter runtime modes). The Propose→Review→
  Approve→Execute lifecycle: the engine only proposes; it never executes.
- **Out:** the specific artifact types and their prompts/parsers (HSM-6-02 for the
  five core types, HSM-6-03 for ADR Candidates + Follow-ups). The `ILLMProvider`
  implementation (Phase 5). MIR profile selection (Phase 7). Review/approve UI
  (Phases 8–9). Any executor or connector call.

## Acceptance criteria

- [x] The engine is a Runtime-Core (Layer 2) component with no SwiftUI/UIKit/
      WebView dependency (charter architecture principle: domain is independent).
      (`Sources/RuntimeCore/MeetingIntelligence/ArtifactGenerationEngine.swift`;
      layer guard green.)
- [x] It accepts an injected `ILLMProvider` and a Phase-0 `Transcript`; it does
      not construct or assume a concrete provider. (`init(provider: ILLMProvider, …)`.)
- [x] Given a real transcript + a working provider, it emits at least one Phase-0
      `Artifact` as structured JSON that validates against the Phase-0 schema with
      zero errors. (`testEmitsSchemaValidArtifact`: the emitted Artifact round-trips
      through the contract coder unchanged.)
- [x] Malformed or partial model output is handled (parse failure surfaces as a
      recoverable error, not a crash) — the engine is robust to the model
      returning prose instead of clean JSON. (`testMalformedOutputIsRecoverable` +
      `testBatchIsResilientPerType`: one bad type does not sink the batch.)
- [x] No code path in the engine executes an action, calls a connector, or
      implies autonomous behavior (charter non-goal: no agentic automation).
      (Propose-only: every artifact is `.draft`; `testNeverAutoAccepts`.)

## Test plan

- Unit: drive the engine with a fake/stub `ILLMProvider` returning a fixed
  well-formed JSON response; assert the emitted `Artifact` validates against the
  Phase-0 schema. Add a stub returning malformed output; assert a recoverable
  error, not a crash. Run the package test suite.
- Integration: run the engine against a real `ILLMProvider` (homelab/endpoint per
  charter Mode B/C) on one captured transcript; confirm a schema-valid artifact
  comes back. Judge that an artifact was produced and is well-shaped — do not
  assert exact artifact text (intel is non-deterministic).
- Manual: n/a.

## Notes / open questions

- Provider is injected, never hard-wired — this is what lets the same engine run
  Mode A (fully local), Mode B (homelab LLM), and Mode C (endpoint).
- Output is judged on shape/validity here; substance/quality is HSM-6-04's job.
- If the model reliably refuses to emit clean JSON, that's a prompt/provider
  concern to record here, not a reason to loosen schema validation.
