# Phase 4 — The Owner Functional Pass

**Last updated:** 2026-07-09 (protocol v2 target/form-factor correction applied;
React Desk and Swift Desk are separate evidence legs)
**Status:** in-progress (1/3)

## Goal

Turn the broad authored corpus into a protocol the owner can actually execute:
ordered by daily user journey, explicit about time and prerequisites, and
deterministically bootstrapped wherever the behavior does not inherently
require a person, microphone, physical device, live model, or external service.

This phase prioritizes usability and functional progress for the early MVP.
Infrastructure hardening—including drift/schema attacks, no-telemetry capture,
and token-gate attack work—is outside this phase by owner decision.

## Exit criteria

- [x] Seven ordered campaign sittings are selectable in the guided site, with
      human titles, purpose, time, preflight, bootstrap split, and move-on gate.
- [x] UI-mechanics tests use exact product-route fixtures for their meeting,
      action, and proposal state; live inference remains where intelligence is
      the capability under test.
- [x] The owner protocol covers the core daily loops: foundation/Desk, voice,
      meetings, agents, and the exact flagship native app; connected and
      secondary-build work is separately labeled.
- [x] Protocol v2 names implementation targets separately from form factors;
      Campaign 1 earns `web_react:desktop` only, while Campaign 5 separately
      exercises `ios_flagship_swift` Desk/native behavior on physical glass.
- [ ] Campaign 1 is completed by the owner and its findings are triaged before
      campaign 2 begins.
- [ ] Core campaigns 1–5 have direct owner verdicts and no untriaged finding.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSU-4-01 | Executable functional protocol + exact bootstrap | done | [story-01](./story-01-functional-protocol-bootstrap.md) | [evidence-story-01](./evidence-story-01.md) |
| HSU-4-02 | Core owner sittings (campaigns 1–5) | ready | [story-02](./story-02-core-owner-sittings.md) | — |
| HSU-4-03 | Connected + secondary target sittings | backlog | [story-03](./story-03-connected-secondary-sittings.md) | — |

## Where we are

The raw protocol already contains 109 scenarios, but it is organized around
historical packs and mixes functional journeys with hardening assertions. The
owner asked for a powerful functional pass with per-test bootstrap and an
explicit usability priority. HSU-4-01 builds that execution layer without
duplicating canonical scenario YAML.

HSU-4-01 originally arranged 85 functional scenarios / 484 legacy surface
observations. The 2026-07-09 protocol audit found that this count conflated
React, viewport shape, and Swift roots. Protocol v2 preserves that historical
fact while replacing the executable denominator with 90 scenarios / 327
target-qualified slots. Exact aftercare/proposal/Qlippy worlds remain live and
idempotent. Campaign 1 is the React desktop sitting; Campaign 5 is the separate
flagship Swift Desk/native sitting. The harness never supplies owner verdicts.

## Decisions made

| Date | Decision | Reason | Authority |
|---|---|---|---|
| 2026-07-09 | Organize the pass by user journey, not implementation phase or feature-ledger domain | The owner needs to use the product coherently and find usability defects, not audit roadmap taxonomy | owner |
| 2026-07-09 | Use deterministic sync-staged meetings/actions/proposals for interface mechanics; keep `.43` for generated-intelligence judgments | Exact fixtures remove irrelevant nondeterminism without faking AI capability | owner + implementation evidence |
| 2026-07-09 | Drift/schema/network-hardening work is not scheduled in this phase | Explicit owner priority: early single-user MVP usability and function first | owner |
| 2026-07-09 | Supersede “three surfaces, one script” with implementation target × form factor | A resized React browser and a Swift app are different products under test; parity requires independent evidence | owner direction + protocol audit |

## Active risks

| Risk | Mitigation | Stop signal |
|---|---|---|
| A long pass becomes another document nobody executes | Seven resumable sittings with honest durations; campaign 1 is fully local and 45 minutes | No completed owner sitting after protocol handoff |
| Fixture state accidentally earns an intelligence verdict | Fixture campaigns judge mechanics only; model-generation scenarios retain live `.43` control/treatment | A generated-output claim passes without a live model run |
| Companion/classic results are credited to flagship | Separate campaign and explicit execution targets/build notes | A non-flagship build recorded as flagship evidence |
| React viewport evidence is credited to Swift Desk | Separate Campaign 1 (`web_react:desktop`) from Campaign 5 (`ios_flagship_swift:ipad/iphone`); native slots require matching device attestation | Any Swift verdict without exact target/form-factor/bundle/build/pairing provenance |
