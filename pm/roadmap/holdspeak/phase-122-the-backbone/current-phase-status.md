# Phase 122 — The Backbone

**Status:** done (12/12).

**Last updated:** 2026-08-07.

## The orchestrator

Opus 4.6 implements. Terra verifies against spec. The orchestrator
makes the done call.

## What we're building

Phase 121 made the desk feel like one OS. Phase 122 makes the desk
*programmable* — extractable from inside, drivable from outside.

Today the desk's only adapter is FastAPI routes. Some are thin
controllers (kernel, meetings); some are fat controllers with business
logic, orchestration, and direct repository calls inline (workbenches
at 161 lines, recipes at 166 lines). An MCP server, a CLI, a test
harness, or a cron job cannot call the desk's operations without going
through HTTP or duplicating logic.

This phase extracts a **service layer** — transport-neutral application
services that own every operation in the system. Then it plugs two
adapters into them: the existing FastAPI routes (thinned) and a new
MCP server (the desk's first programmatic API). Every operation in the
system — create, delete, run, capture, resolve — flows through one
pipeline regardless of who called it.

The result: DeskOS becomes an MCP server. Any MCP client — Claude Code,
another agent, a CI pipeline, a mobile companion — can drive the desk
with the same authority model, the same validation, the same receipts.

## The architecture

```
MCP adapter (stdio JSON-RPC) ────┐
                                  ├──→ PrimitiveService
FastAPI routes (thinned) ─────────┤    WorkbenchService
                                  ├──→ RecipeService
Future CLI ───────────────────────┤    MeetingService
                                  ├──→ KernelService (already exists as Broker)
Test fixtures ────────────────────┘    DictationService
                                       CoderService
                                       ProfileService
                                            │
                                       Repositories / Domain / Kernel
```

Services take a `Principal`, enforce authorization, validate
invariants, call repositories, return typed results. They don't know
who called them.

## Why this phase exists

1. **The programmability gap.** The desk has 45 verbs, 17 primitive
   kinds, and ~400 HTTP routes, but no transport-neutral API. An
   agent cannot create a workbench, run it, and read results without
   HTTP. A test cannot seed the desk without browser automation. A
   cron job cannot trigger a morning brief without curl.
   (Article II — everything is a primitive; primitives should be
   programmable.)

2. **The fat controller gap.** Workbench and recipe routes contain
   orchestration, business rules, and multi-repository calls inline.
   This logic cannot be reused by a second adapter without
   duplication. Extracting services is not refactoring for purity —
   it's the prerequisite for programmability.

3. **The walk gap.** Phase 121's walk (story 12) needs automated
   proof. A programmatic walk harness needs to seed state, drive
   actions, and capture results. Services + MCP + Playwright gives
   each layer its job: MCP drives state, Playwright verifies the
   rendered result, services are the single source of truth.

## Method

- **Extract first (stories 01-05).** Move business logic from route
  handlers into named service classes. Routes become three-line
  adapters: deserialize, call service, serialize. This is the
  foundation everything else stands on.
- **Thin the routes (story 06).** Verify every route is a thin
  adapter. The extraction stories do the work; this story is the
  audit that proves it.
- **Build the MCP server (stories 07-08).** 10 day-one tools + MCP
  resources. Python stdio sidecar following the DW MCP pattern.
- **Build the walk harness (story 09).** Python Playwright page
  objects, isolated hub fixture, screenshot manifest.
- **Desk doctor (story 10).** CLI health check: hub, runtime,
  WebSocket, desk bootstrap.
- **The walk (story 11).** Automated + manual proof.
- **Phase 121 story 12 closeout (story 12).** The keyboard-first
  walk that was deferred.

## What's held

- **Second-wave MCP tools** (filing, duplication, capability
  execution, coder interaction) — Phase 123+.
- **Agent-driven self-walking desk** — after MCP + walk harness
  prove separately.
- **Streamable-HTTP MCP transport** — after stdio proves the schemas.
- **CLI adapter** — after services prove stable through two adapters.

## Dependency graph

```
01 primitive service    ──┐
02 workbench service    ──┤
03 recipe service       ──┤
04 meeting service      ──├──→ 06 thin routes audit
05 remaining services   ──┘         │
                                    ├──→ 07 MCP server (10 tools)
                                    ├──→ 08 MCP resources
                                    ├──→ 09 walk harness
                                    └──→ 10 desk doctor
                                              │
                              07, 08, 09, 10 ──→ 11 the walk
                                               ──→ 12 phase 121 closeout
```

## Stories

### The extraction

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 01 | Primitive service | Why can't a non-HTTP caller create a note? | backlog |
| 02 | Workbench service | Why is workbench orchestration trapped in a route handler? | backlog |
| 03 | Recipe service | Why is the run lifecycle trapped in a 166-line handler? | backlog |
| 04 | Meeting service | Why can't MCP start a capture without HTTP? | backlog |
| 05 | Remaining services | Why do dictation, coders, and profiles still require HTTP? | backlog |

### The proof

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 06 | Thin routes audit | Is every route now a three-line adapter? | backlog |

### The MCP server

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 07 | MCP server — 10 tools | Can an MCP client drive the desk? | backlog |
| 08 | MCP resources | Can an MCP client discover the desk's schema and state? | backlog |

### The walk harness

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 09 | Walk harness | Can a script walk and screenshot the desk? | backlog |
| 10 | Desk doctor | Can we check desk health from the command line? | backlog |

### The proof

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 11 | The walk | Does the MCP server drive real state through real services? | backlog |
| 12 | Phase 121 closeout | Can a power user drive the desk without the mouse? | backlog |

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-122-01 | Primitive service | done | [story-01](story-01-primitive-service.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-122-02 | Workbench service | done | [story-02](story-02-workbench-service.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-122-03 | Recipe service | done | [story-03](story-03-recipe-service.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-122-04 | Meeting service | done | [story-04](story-04-meeting-service.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-122-05 | Remaining services | done | [story-05](story-05-remaining-services.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-122-06 | Thin routes audit | done | [story-06](story-06-thin-routes-audit.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-122-07 | MCP server — 10 tools | done | [story-07](story-07-mcp-server.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-122-08 | MCP resources | done | [story-08](story-08-mcp-resources.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-122-09 | Walk harness | done | [story-09](story-09-walk-harness.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-122-10 | Desk doctor | done | [story-10](story-10-desk-doctor.md) | [evidence-story-10](./evidence-story-10.md) |
| HS-122-11 | The walk | done | [story-11](story-11-the-walk.md) | [evidence-story-11](./evidence-story-11.md) |
| HS-122-12 | Phase 121 closeout | done | [story-12](story-12-phase-121-closeout.md) | [evidence-story-12](./evidence-story-12.md) |

## Where we are

12/12 DONE. DeskOS is programmable. Eight transport-neutral services
(~2000 lines) own every desk operation. All CRUD route handlers are
thin adapters. The MCP server advertises 10 tools + 7 resources over
stdio JSON-RPC. The walk harness captures screenshots at 1440px +
393px with an isolated hub fixture. Desk doctor runs 8 health checks.
The integration walk proved MCP tools drive real state through real
services. The keyboard-first walk proved palette, ARIA, and
object lifecycle all complete without a mouse. The CLOSED claim
awaits the owner sitting.
