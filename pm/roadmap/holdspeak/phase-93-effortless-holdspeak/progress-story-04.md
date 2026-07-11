# HS-93-04 progress record — Power lives on the Desk

**Captured:** 2026-07-11<br>
**Baseline:** `main` at `1e6a28f3` plus the uncommitted HS-93-01 through
HS-93-03 working tree<br>
**After build:** current Phase-93 working tree; no commit identity claimed<br>
**Acceptance status:** in progress — implementation, API-backed production Web
evidence, package tests, and a flagship simulator build are green; owner and
physical-device evidence remain required.

## One composition grammar, not another engine

HS-93-04 adapts the Phase-92 primitives already present on the Desk. It does not
add a universal palette, persisted resource kind, event store, graph runtime, or
top-level destination.

The pure Web adapter in
[`contextual.ts`](../../../../web/src/desk/contextual.ts) joins existing
qualified Desk selection, capability descriptors, trust destinations, Coder
presence, inference targets, Projects, and projection Receipts. The shared Tools
surface then presents those existing things through search, contextual actions,
and a non-document inspector.

Eligibility is explicit:

- selected material must be a live Note or Artifact with non-empty text;
- a Persona, Sequence, or Workflow must declare required `input`, readiness
  `ready`, and effect `creates_artifact`;
- an Integration must be configured and exactly one compatible source selected;
- a Coder session accepts selected material only while waiting for a response;
- a model-backed run requires non-empty input and an available Runs-on target.

Selection and source return now carry qualified `kind:id` identity end to end.
A Note and Artifact with the same bare id cannot silently open or ground each
other.

## Visible subtraction and progressive power

| Surface | Before HS-93-04 | After |
|---|---|---|
| Web Persona/model access | an unbounded permanent right-edge avatar/model rail | no permanent rail; Persona objects, selection actions, search, pull-out chat, and Runs-on target inspection retain access |
| Background work | the full Mission Control conveyor opened at rest and could cover compact Desk objects | one non-overlapping `Background runs` presence chip; the full conveyor opens on request |
| Tools shelf | static deep-route list plus Desk object/Zone text search | the same shelf also discovers Projects, configured Integrations, Runs-on targets, and selection-compatible actions |
| Project | relationship chips only in the material pull-out | assign/remove plus a direct inspector, related material, search, and focused Project-context entry |
| Integration | setup route or disconnected proposal surfaces | configured identity, readiness, destination, data, authority, source preview, propose/approve/reject/retry, Receipt, and source return in one Desk inspector |
| Resting navigation | five primary destinations after HS-93-01 | unchanged; contextual power adds no destination and no resting action buttons |

Personas, Workflows, and Coder sessions remain visible as Desk objects/processes.
Models and devices appear as Runs-on targets. Activity and the collapsed
Background-runs presence retain process discovery. Studio remains the deep
authoring/configuration room.

## Project and Integration lifecycle

A Project remains independent from Zone placement and Knowledge membership. Web
material pull-outs name assign/remove actions and expose an adjacent Project
inspector. The inspector lists the Project's existing qualified relationships
and can open the exact related Desk object. Flagship Swift keeps the same
three-axis relationship panel and now adds a semantic Project-info button,
related-material inspector, and context-bearing `Use Project context` action.

For external effects, the selected source is now part of the proposal's approved
payload and idempotency identity. The hub accepts only a live Meeting, Note, or
Artifact source, resolves its canonical label rather than trusting display text,
and projects proposal/approval/failure/Receipt state back onto that source. An
older client that omits source identity preserves the prior Integration-scoped
behavior and idempotency key.

The shared Swift
[`DeskIntegrationProposalRequest`](../../../../apple/Sources/Contracts/DeskIntegrationProposal.swift)
uses the same `source_ref` / `source_label` wire. Native configured connectors
now accept Notes as well as existing Meeting/Artifact material, retain the
source through the exact send card, and give the host enough identity to attach
the resulting Receipt to the originating Desk subject.

## Production Web evidence

[`phase93_context_power_evidence.py`](../../../../scripts/phase93_context_power_evidence.py)
boots a real `MeetingWebServer` against an isolated database and config, seeds a
Note, Persona, Workflow, Project relationship, configured Slack destination,
and Runs-on target, and drives ordinary pointer actions through the production
bundle. The Slack HTTP transport alone is replaced with a successful local fake;
the real proposal, approval, authority, executor, persistence, projection, and
source-return paths run. Any failed API response or visible request-error copy
aborts the capture.

The runner initially failed on compact Web because the open background conveyor
intercepted the selected Note. The accepted run is after the resting-conveyor
fix; no forced click is used.

| State | Evidence | What it establishes |
|---|---|---|
| Pre-story static Tools | [HS-93-01 Tools baseline](./evidence/hs-93-01/after-web-tools.png) | advanced routes were preserved, but no resource or selection composition appeared |
| Selected material, desktop | [contextual Tools](./evidence/hs-93-04/after-web-selection-tools.png) | ready Persona/Workflow/Slack actions plus Project, Integration, and Runs-on discovery |
| Selected material, compact | [compact contextual Tools](./evidence/hs-93-04/after-web-selection-tools-compact.png) | the same semantic path remains reachable without the conveyor covering the Desk |
| Integration inspection | [source and destination](./evidence/hs-93-04/after-web-integration-inspector.png) | configured state, boundary, data, authority, destination, exact source, and effect |
| Proposed external effect | [approval state](./evidence/hs-93-04/after-web-integration-proposal.png) | the consequential button names the Slack commitment before execution |
| Completed external effect | [source-bound Receipt](./evidence/hs-93-04/after-web-integration-receipt.png) | executed outcome, retained source, and direct source return |
| Project inspection | [related material](./evidence/hs-93-04/after-web-project-inspector.png) | Project identity and relationship remain separate from spatial filing |

These frames are production-Web implementation evidence, not owner-comprehension
or physical-device evidence.

## Verification

| Lane | Result |
|---|---|
| Contextual Vitest/component coverage | qualified-id collision, readiness/input/effect gating, configured destination, waiting Coder, dynamic discovery, Project opening, and full Integration UI lifecycle covered |
| Full Web `npm run check`, NVM Node 22.21.0 | current regression gate: architecture guard passed for 109 source files; typecheck passed; 29 files / 155 tests passed; production build passed |
| Focused/broader Hub and integration lane | 85 passed, including all three Desk Integration lifecycles, Project relationships, projections, workroom, product-copy, and arrival locks |
| API-backed production evidence runner | desktop and compact selection, Project inspector, Integration propose/approve/Receipt/source-return passed with zero failed API responses |
| Product-copy census | 3,919 candidates; 0 violations |
| Full Swift package | current regression gate: 544 passed, 9 skipped, 0 failures |
| Flagship simulator app build | generated `HoldSpeakMeetingCapture.xcodeproj`; `HoldSpeakMobile` Debug iPhoneSimulator build succeeded |
| Ruff / patch hygiene | changed production Python and evidence runner passed; `git diff --check` passed |

The app build retains existing concurrency/deprecated-API warnings in unrelated
paths. The Vite build retains its existing mixed static/dynamic `ask.ts` chunk
warning; neither is a build failure.

## Acceptance still required

HS-93-04 remains open. The owner must locate Project, Integration, Persona,
Workflow, Coder, Runs on, device, and background-work actions from the production
Desk without repository knowledge and record before/after discovery time and
irrelevant-control counts. Physical iPhone and iPad walks must exercise the
semantic Project inspector, configured connector, waiting-only Coder path,
Runs-on selection/Receipt, relaunch, and source-bound Receipt. Failure and
unavailable-destination walks must confirm the source remains findable and retry
does not duplicate the effect. Simulator compilation and scripted Web discovery
do not substitute for those observations.
