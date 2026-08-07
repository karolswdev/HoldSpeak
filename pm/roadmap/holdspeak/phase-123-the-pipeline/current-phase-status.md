# Phase 123 — The Pipeline

**Status:** chartered (0/13).

**Last updated:** 2026-08-06.

## The orchestrator

Opus 4.6 implements. Terra verifies against spec. The orchestrator
makes the done call.

## What we're building

Phase 122 built the skeleton: eight transport-neutral services and an MCP
server with ten tools. The audit after that work found the boundary is still
partial. One hundred fifty-seven route handlers in thirty-five modules call
`get_database()` directly; only about thirty percent of operations travel
through a service; and ten MCP tools expose only a fraction of the desk's
essential operations.

Phase 123 completes the pipeline. Every operation reaches persistence and
domain machinery through a named service, FastAPI routes become transport
adapters, and MCP exposes the full essential desk tool surface. The service
layer itself becomes sound: it has domain errors rather than HTTP-shaped
exceptions, and it no longer imports route-layer helpers.

The result is the architecture Phase 122 promised: HTTP, MCP, tests, and
future adapters call the same application services, with the same authority,
validation, invariants, receipts, and durable state transitions.

## The architecture

```
FastAPI routes ────────┐
MCP stdio server ──────┼──→ named application services ──→ repositories / domain / kernel
Tests and future CLI ──┘        │
                                 ├── ServiceError (domain code, not HTTP status)
                                 ├── services.support (shared domain helpers)
                                 └── explicit Principal + authorization
```

Routes deserialize, obtain the request principal, invoke one named service,
and serialize the result. Services do not import `holdspeak.web.routes` or
know whether the caller is HTTP, MCP, a test, or a future CLI.

## Why this phase exists

1. **The false-boundary gap.** A service layer that only owns thirty percent
   of operations is not a system boundary. Direct route database calls let
   HTTP become a privileged alternate path and force MCP callers to duplicate
   or omit desk behavior. (Constitution Article II: primitives and their
   operations must remain programmable.)
2. **The inversion gap.** Existing services import helpers and error types
   from route modules. That reverses the dependency direction and makes the
   supposedly transport-neutral layer impossible to use independently.
3. **The programmability gap.** Ten MCP tools cannot operate workbenches,
   recipes, profiles, meetings, dictation, filing, or the other essential
   desk objects as a complete programmatic surface.
4. **The proof gap.** The only meaningful completion proof is a real MCP walk
   over the expanded surface, backed by the final structural audit and desk
   doctor.

## Method

- **Wave 1 — structural fixes (story 01).** Establish domain errors and
  shared service support, then eliminate imports from service modules back
  into route modules.
- **Wave 2 — remaining service extractions (stories 02–08).** Move every
  audited route operation into a named authority, settings, ask/decision,
  project/projection, meeting, activity, or remaining-domain service.
- **Wave 3 — MCP expansion (stories 09–11).** Expose the services as the
  complete essential tool and resource surface; MCP tools never grow a
  second business-logic path.
- **Wave 4 — proof (stories 12–13).** Audit the route boundary mechanically,
  then walk all new programmatic operations against the running desk.

## What's held

- Streamable-HTTP MCP transport and remote deployment; stdio remains the
  proven transport for this phase.
- A general-purpose scripting language, arbitrary code execution, or a new
  CLI adapter; services and MCP are the contract to prove first.
- New product features or schema redesigns not required to extract an
  existing operation faithfully.
- Refactoring repositories or kernel internals beyond seams required for
  transport-neutral service ownership.

## Dependency graph

```
01 structural fixes ──→ 02 authority ──┐
                    ──→ 03 settings  ──┤
                    ──→ 04 ask + decisions ──┤
                    ──→ 05 projects + projections ──├──→ 12 thin routes audit
                    ──→ 06 meetings + aftercare ──┤             │
                    ──→ 07 activity domain ─────┤             ├──→ 09 MCP workbench + recipe
                    ──→ 08 remaining handlers ──┘             ├──→ 10 MCP meeting + profile + dictation
                                                               ├──→ 11 MCP resources
                                                               └──→ 13 the walk
```

## Stories

### Wave 1 — Structural fixes

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 01 | Service errors and imports | Can services be truly transport-neutral and share domain support without importing routes? | backlog |

### Wave 2 — Remaining service extractions

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 02 | Authority and credentials | Can authority and secrets be managed without route-owned persistence logic? | backlog |
| 03 | Settings service | Can configuration be read, validated, redacted, and reconfigured outside HTTP? | backlog |
| 04 | Ask and decisions | Can ask orchestration and decision lifecycle run through services? | backlog |
| 05 | Projects and projections | Can projects and desk presentation be fully programmatic? | backlog |
| 06 | Meeting intel, aftercare, and friends | Can every meeting intelligence and recovery operation leave route handlers? | backlog |
| 07 | Activity domain | Can the activity ledger, rules, jobs, enrichment, and nudges share named services? | backlog |
| 08 | Remaining handlers | Can every remaining audited route operation cross a named service boundary? | backlog |

### Wave 3 — MCP expansion

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 09 | MCP tools: workbench and recipe | Can an MCP client operate workbenches, recipes, zones, and knowledge membership? | backlog |
| 10 | MCP tools: meeting, profile, dictation, desk | Can an MCP client operate capture, profiles, dictation, desk state, and decision supersession? | backlog |
| 11 | MCP resources expansion | Can an MCP client discover essential desk state through stable resources? | backlog |

### Wave 4 — Proof

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 12 | Thin routes audit | Does every route handler now delegate through a named service? | backlog |
| 13 | The walk | Does MCP drive the expanded service surface through a real running desk? | backlog |

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-123-01 | Service errors and imports | backlog | [story-01](story-01-service-errors-and-imports.md) | — |
| HS-123-02 | Authority and credentials | backlog | [story-02](story-02-authority-and-credentials.md) | — |
| HS-123-03 | Settings service | backlog | [story-03](story-03-settings-service.md) | — |
| HS-123-04 | Ask and decisions | backlog | [story-04](story-04-ask-and-decisions.md) | — |
| HS-123-05 | Projects and projections | backlog | [story-05](story-05-projects-and-projections.md) | — |
| HS-123-06 | Meeting intel, aftercare, and friends | backlog | [story-06](story-06-meeting-intel-aftercare-and-friends.md) | — |
| HS-123-07 | Activity domain | backlog | [story-07](story-07-activity-domain.md) | — |
| HS-123-08 | Remaining handlers | backlog | [story-08](story-08-remaining-handlers.md) | — |
| HS-123-09 | MCP tools: workbench and recipe | backlog | [story-09](story-09-mcp-tools-workbench-and-recipe.md) | — |
| HS-123-10 | MCP tools: meeting, profile, dictation, desk | backlog | [story-10](story-10-mcp-tools-meeting-profile-dictation-and-desk.md) | — |
| HS-123-11 | MCP resources expansion | backlog | [story-11](story-11-mcp-resources-expansion.md) | — |
| HS-123-12 | Thin routes audit | backlog | [story-12](story-12-thin-routes-audit.md) | — |
| HS-123-13 | The walk | backlog | [story-13](story-13-the-walk.md) | — |

## Where we are

Phase 123 is chartered. Start with HS-123-01: all later extraction work
requires a transport-neutral error vocabulary and support helpers that no
longer live in `holdspeak.web.routes`. After the eight extraction stories,
HS-123-12 is the structural boundary gate; the MCP expansion and live walk
then prove the public programmatic surface. No evidence exists yet.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Extraction changes established HTTP semantics | medium | Preserve route response mapping at the adapter edge and regression-test each migrated domain | Existing route contract tests change unexpectedly without a deliberate API decision |
| Service imports retain hidden route dependencies | high | Add static import and `get_database()` census checks before the final audit | A service still imports `holdspeak.web.routes` or needs FastAPI to import |
| MCP expands schemas but duplicates business logic | medium | MCP handlers call only named services; exercise routes and MCP against shared fixtures | An MCP tool calls a repository or reproduces a service algorithm |
| Sweeping 157 handlers obscures omissions | high | Use an ownership inventory per route module and make the final grep a release gate | `get_database()` remains in a handler without a documented exception |

## Decisions made (this phase)

- 2026-08-06 — Service errors carry a domain `code`, never an HTTP status — routes translate domain errors at the transport edge.
- 2026-08-06 — Shared helper ownership moves from `holdspeak.web.routes.primitives._shared` to `holdspeak.services.support` — services must not depend on routes.
- 2026-08-06 — MCP expansion is service-first — a tool is an adapter, not a parallel application layer.

## Decisions deferred

- Streamable-HTTP MCP transport — revisit after the complete stdio tool and resource surface has passed the walk.
- A CLI adapter — revisit after service contracts are stable across FastAPI and MCP.
