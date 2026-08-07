# Phase 124 — The Observer

**Status:** chartered (0/10).

**Last updated:** 2026-08-06.

## The orchestrator

Opus 4.6 implements. Terra verifies against spec. The orchestrator
makes the done call.

## What we're building

Phase 123 completed the service pipeline: 33 services own every
operation in DeskOS, and 41 MCP tools provide the full programmatic
surface. But the pipeline is blind — calls execute and return, and
nothing records what happened. The handover planted the seed: the
pipeline is one observer away from being observable.

Phase 124 adds the observer. Every public service method call is
recorded — who called it, what they asked for, what came back, how long
it took, and when. The entire system becomes a stream of structured
events stored in a local append-only SQLite table. No telemetry leaves
the machine (Article III.3). The observer satisfies Article V.2 ("every
attempt leaves a receipt") at the application layer, complementing the
kernel journal's operation-level receipts from Phase 106.

The result: the desk knows what it did. An MCP resource answers "what
happened?", a desk doctor check validates the observer is wired, and a
walk proves every service is observed.

## The architecture

```
FastAPI routes ────────┐
MCP stdio server ──────┼──→ named application services ──→ repositories
Tests and future CLI ──┘        │
                                 ├── @observed decorator
                                 │       │
                                 │       ▼
                                 │   PipelineObserver protocol
                                 │       │
                                 │       ▼
                                 │   pipeline_events (SQLite)
                                 │       │
                                 │       ▼
                                 │   MCP resource: pipeline://events
                                 │   Desk doctor: observer health
                                 │
                                 ├── ServiceError (domain code)
                                 ├── services.support (shared helpers)
                                 └── explicit Principal + authorization
```

## Why this phase exists

1. **The blindness gap.** 33 services process every desk operation, but
   nothing records what flows through them. The desk cannot answer "what
   did I do today?" or "which services are hot?" (Constitution Article
   V.2: every attempt leaves a receipt — who, what, where, outcome.)

2. **The replay gap.** Without structured event history, there is no
   foundation for replay, correlation, analytics, or briefing generation.
   The kernel journal records consequential operations (Article XI), but
   the application layer — CRUDs, queries, voice resolutions, ledger
   refreshes — is invisible.

3. **The proof gap.** Observability that isn't walked is a claim. The
   MCP resource, the doctor check, and the walk prove the observer is
   real and complete.

## Constitutional grounding

- **Article V.2:** "Every attempt leaves a receipt: who, what, where,
  outcome. The audit is part of the act, not an accessory." The observer
  makes this true at the application layer.
- **Article III.3:** "No telemetry, no silent cloud dependency. Ever."
  Events are local-only SQLite. Nothing leaves the machine.
- **Article XI.5:** "Reads owe the kernel no admission and no receipt."
  The observer records reads as well — but as application-layer events,
  not kernel admissions. The distinction is preserved.
- **Article IX:** "Proof over claim." The walk proves it.

## Story status

| ID | Title | Status | Trace |
|----|-------|--------|-------|
| HS-124-01 | PipelineObserver protocol and event schema | backlog | — |
| HS-124-02 | The `pipeline_events` table | backlog | — |
| HS-124-03 | The `@observed` decorator | backlog | — |
| HS-124-04 | SQLiteObserver — the day-one backend | backlog | — |
| HS-124-05 | Wire observer to all 33 services | backlog | — |
| HS-124-06 | Event query service | backlog | — |
| HS-124-07 | MCP resource: pipeline events | backlog | — |
| HS-124-08 | Desk doctor: observer health check | backlog | — |
| HS-124-09 | Docs story | backlog | — |
| HS-124-10 | The walk | backlog | — |

## Where we are

Chartered. No work started. The service layer (Phase 123) is the
prerequisite and it shipped as PR #441.
