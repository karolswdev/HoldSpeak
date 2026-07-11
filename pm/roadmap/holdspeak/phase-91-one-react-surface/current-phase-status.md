# Phase 91 — One React Surface (DeskOS craft across the Web)

**Status:** IN PROGRESS (9/10).

**Last updated:** 2026-07-10 (the one-tree Vite/React cutover, all route cohorts,
Signal grammar, hard deletion, automated parity suites, browser audit, and
public docs are complete; owner workflows and actual Swift parity evidence
remain the non-waivable close gate).

## Goal

Replace the Astro + Alpine + imperative-page-script frontend with one typed
Vite/React application whose entire Web surface feels authored by the same
product team as DeskOS. Preserve the recent Signal control improvements,
existing URLs, API contracts, privacy signals, and user-visible capabilities;
remove the parallel rendering and component systems rather than wrapping them.

## Why this phase exists

The Web currently contains 17 Astro pages (10,177 lines), 35 Astro components,
and 12,068 lines of page-oriented JavaScript beside the existing React Desk.
That split is why a runtime-rendered Activity action can miss Astro's scoped
CSS, why several pages privately redefine buttons and editors, and why visual
improvements do not automatically reach the whole product. The July 10 audit
fixed the visible baseline and established the Signal grammar; this phase makes
that grammar architectural instead of opt-in.

## Pinned architecture

- One client entry, one React 19 tree, and one browser router. Every product
  route resolves through the same Vite-built application shell.
- TypeScript for all new frontend code. Existing JavaScript is ported into
  typed API clients, hooks, reducers/stores, and React components—not imported
  as a DOM-mutating compatibility layer.
- Existing Zustand stores remain where state genuinely crosses component or
  route boundaries. Route-local state remains local. One shared runtime-bus
  provider owns the WebSocket lifecycle.
- `tokens.css` and the July 10 Signal control foundation survive. Reusable
  React components own interaction styling; route CSS owns composition and
  uses CSS modules or explicitly named feature styles. No CSS-in-JS fork.
- The React Desk is the Web craft reference. The native Swift DeskOS build is
  the cross-surface visual/behavior reference, but browser screenshots never
  count as native Swift acceptance evidence.
- Existing canonical URLs and `/api/*` wires remain stable. FastAPI serves one
  SPA shell for deep links; static assets continue to build into
  `holdspeak/static/_built/`.
- Astro and Alpine may coexist only inside this phase's route-by-route
  migration window. Phase exit deletes them, their dependencies, their
  directives, and their page-script bootstraps.

## Scope

- In: Vite + React Router application shell; typed shared API/runtime clients;
  React Signal components; DeskOS material, spacing, type, motion, navigation,
  editors, disclosures, status and empty-state grammar; migration of all 17
  Astro routes; migration of Alpine and imperative DOM scripts; deep-link and
  auth-token behavior; component gallery; route/verb parity harness; visual,
  accessibility and UAT proof; final Astro/Alpine deletion.
- Out: backend feature redesign; changing API payloads merely to make React
  easier; reimplementing native Swift DeskOS; treating a narrow desktop browser
  as iPad/iOS evidence; a second design system; a permanent dual frontend;
  unrelated product features discovered during the migration.

## Exit criteria (evidence required)

- [x] `web/src` contains zero `.astro` files, zero Alpine directives/imports,
      and zero product bootstraps that mutate DOM by selector; `astro`,
      `@astrojs/react`, and `alpinejs` are absent from `web/package.json`.
- [x] `npm run build` is a Vite/React build into
      `holdspeak/static/_built/`; every canonical route and direct deep link
      returns the React shell with no route-specific HTML reader in
      `holdspeak/web/routes/pages.py`.
- [x] All route contracts in the Phase-91 inventory pass: URLs, primary verbs,
      request payloads, success/error/empty/loading states, token forwarding,
      WebSocket behavior, focus return, and persisted local preferences.
- [x] `/design/components` is React and demonstrates every shared component in
      default, hover/focus, selected, disabled, loading, success, warning, and
      error states.
- [x] Every route passes the Web UI audit at desktop and compact-Web widths:
      200 responses, no console errors, no unnamed controls, no native-style
      fallbacks, no sub-24 px targets, and no horizontal overflow.
- [ ] DeskOS parity review is captured side by side from the actual Swift app
      and the Web for arrival, Desk, Dictation, Meetings, Settings, and one
      Studio tool; differences are either fixed or explicitly platform-native.
- [ ] React unit/component tests, backend Web integration tests, production
      build, and the owner UAT walk all pass; the migration ships with no lost
      user-visible capability and no secret/API key reaching browser storage.
- [x] Public architecture/development docs describe one React Web frontend;
      stale Astro/Alpine instructions and diagrams are removed.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-91-01 | The React foundation and parity ledger | done | [story-01](./story-01-react-foundation-and-parity-ledger.md) | [ledger](../../../../docs/WEB_REACT_PARITY_LEDGER.json) |
| HS-91-02 | Signal React: the DeskOS component grammar | done | [story-02](./story-02-signal-react-component-grammar.md) | [gallery audit](./evidence/web-audit/report.json) |
| HS-91-03 | Arrival and configuration in React | done | [story-03](./story-03-arrival-and-configuration.md) | [automated closeout](./evidence-automated-closeout.md) |
| HS-91-04 | The Dictation cockpit in React | done | [story-04](./story-04-dictation-cockpit.md) | [automated closeout](./evidence-automated-closeout.md) |
| HS-91-05 | Activity, Commands, and Cadence in React | done | [story-05](./story-05-activity-commands-cadence.md) | [automated closeout](./evidence-automated-closeout.md) |
| HS-91-06 | The live meeting room in React | done | [story-06](./story-06-live-meeting-room.md) | [automated closeout](./evidence-automated-closeout.md) |
| HS-91-07 | The Meetings archive in React | done | [story-07](./story-07-meetings-archive.md) | [automated closeout](./evidence-automated-closeout.md) |
| HS-91-08 | Studio and support surfaces in React | done | [story-08](./story-08-studio-and-support-surfaces.md) | [automated closeout](./evidence-automated-closeout.md) |
| HS-91-09 | The hard cut: one Vite app, no Astro or Alpine | done | [story-09](./story-09-hard-cut.md) | [automated closeout](./evidence-automated-closeout.md) |
| HS-91-10 | DeskOS parity walk, UAT, docs, and close | in-progress | [story-10](./story-10-parity-uat-close.md) | [Web audit](./evidence/web-audit/report.json); owner/Swift evidence pending |

## Where we are

The Web implementation is one React 19 tree from arrival through Desk,
Dictation, Meetings, configuration, Studio, support, ambient runtime surfaces,
and the component gallery. FastAPI serves one shell for every direct link;
the old framework, island, and page-script layers are deleted. Automated Web
evidence is green across 34 desktop/compact loads and the full selected backend
contract suite. HS-91-10 remains open by design: the owner must complete the
real microphone/model workflows and the actual Swift app must supply parity
captures before the phase can be called closed.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A visually cleaner rewrite silently loses mature behavior | high | route/verb/state ledger; network-contract tests; cohort cutovers; before/after UAT | any route called “migrated” without verb and failure-state parity |
| Two frontends become permanent | medium | explicit HS-91-09 deletion gate; no new Astro/Alpine work after phase opens | a new product feature lands only in Astro after its cohort starts |
| React merely wraps imperative DOM code | high | typed hooks/components own state; census forbids selector-driven product bootstraps at exit | `innerHTML`, global query-selector mutation, or Alpine shim used as migration completion |
| DeskOS parity becomes a superficial color copy | medium | compare hierarchy, density, material, motion, focus and workflow—not just palette | route passes screenshots but still uses a second interaction grammar |
| SPA cutover breaks deep links/auth | medium | FastAPI deep-link integration tests and token bootstrap contract land in HS-91-01 | refresh on any canonical URL 404s, loops, or drops auth |
| History/Live scope explodes | high | dedicated stories with locked verb inventories; no backend feature additions | migration PR changes backend semantics unrelated to parity |

## Decisions made (this phase)

- 2026-07-10 — Phase exit is a full React/Vite shop: no Astro and no Alpine —
  direct owner decision.
- 2026-07-10 — Preserve Signal tokens and recent control improvements, then
  express them as React components — avoids discarding the just-verified UI
  baseline.
- 2026-07-10 — React Router plus a single FastAPI-served SPA shell; canonical
  paths remain unchanged — deep links are product contracts.
- 2026-07-10 — Route cohorts may migrate incrementally, but compatibility code
  has an expiry story (HS-91-09) and cannot survive phase exit.
- 2026-07-10 — Swift DeskOS requires actual native evidence; compact Web is a
  responsive-Web target only — preserves the corrected UAT protocol.

## Decisions deferred

- Server-side rendering — default: no; the hub serves a local application and
  Vite SPA output satisfies current product and packaging needs.
- A third-party data-fetching cache — default: use typed fetch hooks and the
  existing Zustand stores; revisit only when duplicated cache invalidation is
  demonstrated during a route migration.
- Native Swift component sharing — default: share design intent/tokens and wire
  contracts, not implementation code.
