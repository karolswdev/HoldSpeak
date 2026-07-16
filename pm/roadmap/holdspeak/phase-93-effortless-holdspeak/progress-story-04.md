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

## UI consistency + desk-window remediation slice — 2026-07-15

Direct owner finding: the Phase 92/93 deliverables introduced visible
inconsistency with the general UI layout and per-component rules, and the
floating desk areas were glued in place — not movable, not resizable — which
contradicts the Desk OS window grammar this phase promised. Four independent
review passes produced [ui-consistency-inventory.md](./ui-consistency-inventory.md)
(46 findings, each with the convention it breaks); this slice remediates them
across Web and flagship Swift.

What shipped:

- **The desk-window contract.** `web/src/desk/components/DeskWindow.tsx` gives
  every floating panel drag (by its head), a corner resize grip, focus-to-front
  ordering, and a persisted per-panel rect (`hs.desk.panels`, beside the object
  layout), reusing the exact `@use-gesture` + localStorage machinery desk
  objects already trust. Adopters: object Pullout, Ask composer, Persona chat,
  Session pullout, Tool inspector, Desk memory drawer. Windows coexist
  (focus-not-destroy replaced the destroy-on-open exclusivity), a stray desk
  click no longer wipes a roped Ask context or closes a live Session peek, a
  window dragged toward an edge shrinks to keep its grip reachable, and two
  default-corner windows cascade instead of stacking pixel-for-pixel.
- **One panel chrome.** The undefined `--surface-0` token (four panels rendered
  with no background fill — a real bug), divergent radii/offsets/blur/shadows,
  unscoped `.desk-first-*` rules, the invented `--ink` token, hardcoded hex and
  off-grid values, and per-panel close-button reinventions all converge on the
  established pullout chrome, shared part classes, and a documented z ladder.
- **One Record verb.** The chrome Record chip now drives the same hub recorder
  as the orb and mirrors its state (Stop while recording) instead of navigating
  off-desk to /live; recording state lives in the desk store.
- **Pages and language.** Dead `.notice`/`button secondary` classes replaced
  with real components; raw wire values (`control_posture`, `effect_class`,
  proposal statuses) render product labels everywhere including the Desk
  memory drawer and Tool inspector; one shared `PostureNote`; recovery-card CSS
  deduplicated onto the canonical warning tint; Settings policy internals moved
  behind a disclosure; copy-contract rewrites (no anthropomorphism, no
  documentation prose in permanent chrome, on Web and in the relationship
  pull-outs).
- **Flagship Swift parity.** The Desk-memory detail sheet rebuilt from stock
  `List`/`LabeledContent` to the Signal grammar; `DioProjectInspector` adopts
  the sibling Dio sheet anatomy; recovery actions use the capsule grammar with
  commitment verbs; hand-rolled egress badges replaced by `EgressBadge`; one
  shared `PostureBadge` (Settings keeps its selector); relationship prose and
  invariant enumerations removed from permanent chrome; the 8.5pt destination
  line and fixed HUD height made Dynamic-Type-sane; naming drift fixed.

Verification for this slice (fresh, on the final tree):

| Lane | Result |
|---|---|
| Full Web gate (`npm --prefix web run check`) | architecture guard 115 sources; typecheck; 32 files / 173 tests; production build — all green |
| Desk-window production walk (`scripts/phase93_desk_windows_evidence.py`) | coexist → drag+persist → resize → focus-raise → reload-restore → Desk memory window; zero failed API responses; captures in [evidence/ui-remediation](./evidence/ui-remediation/) |
| Flagship simulator app build | generated project rebuilt from the remediated App sources; Debug iPhoneSimulator BUILD SUCCEEDED |
| Canonical Python suite | captured at commit time; see "Captured runs" below |

HS-93-04's owner and physical-device acceptance gates are unchanged by this
slice and remain open.

### Captured runs (2026-07-15, `dw evidence capture`, this slice's final tree)

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — captured
  2026-07-16T02:59:04Z, exit 0: `3798 passed, 42 skipped in 463.56s`.
  Two prior captures the same evening are recorded honestly: the first
  (02:41Z, exit 1) caught the stale `Button("Retry")` source lock in
  `test_native_first_words_contract.py`, updated to the copy-contract
  commitment verbs this slice ships; the second (02:50Z, exit 1) was
  `test_device_recording_tick.py::test_sender_exception_does_not_kill_thread`,
  a thread-timing test on a file this slice does not touch, which passes in
  isolation and on the rerun.
- `npm --prefix web run check` — captured 2026-07-16T03:06:53Z, exit 0:
  architecture guard (115 sources), typecheck, `32 passed (32)` test files /
  173 tests, production build.

The raw captures were taken via the evidence tool and folded here because an
`evidence-story-04.md` file is a done-claim in `dw check` and this story
remains in progress.
