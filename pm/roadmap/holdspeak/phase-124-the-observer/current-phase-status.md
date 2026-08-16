# Phase 124 — The Observer

**Status:** done (10/10, PR #442, merged 4898465e). (Record corrected
2026-08-15 by HS-132-13: the header said chartered (0/10) while commit
416f0828 shipped the whole phase; per-story evidence is reconstructed as
commit pointers — see the evidence files.)

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

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-124-01 | PipelineObserver protocol and event schema | done | [story-01](./story-01-pipeline-observer-protocol.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-124-02 | The `pipeline_events` table | done | [story-02](./story-02-pipeline-events-table.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-124-03 | The `@observed` decorator | done | [story-03](./story-03-observed-decorator.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-124-04 | SQLiteObserver — the day-one backend | done | [story-04](./story-04-sqlite-observer.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-124-05 | Wire observer to all 33 services | done | [story-05](./story-05-wire-observer-to-services.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-124-06 | Event query service | done | [story-06](./story-06-event-query-service.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-124-07 | MCP resource: pipeline events | done | [story-07](./story-07-mcp-resource-pipeline-events.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-124-08 | Desk doctor: observer health check | done | [story-08](./story-08-desk-doctor-observer.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-124-09 | Docs story | done | [story-09](./story-09-docs.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-124-10 | The walk | done | [story-10](./story-10-the-walk.md) | [evidence-story-10](./evidence-story-10.md) |

## Where we are

Chartered. No work started. The service layer (Phase 123) is the
prerequisite and it shipped as PR #441.
