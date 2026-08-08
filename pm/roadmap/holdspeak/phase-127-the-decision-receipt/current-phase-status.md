# Phase 127 — The Decision Receipt

**Status:** done (10/10).

**Last updated:** 2026-08-07.

## The orchestrator

Opus 4.6 implements. Terra verifies against spec. The orchestrator
makes the done call.

## What we're building

A consequential choice must remain explainable after its conversation has
passed. Phase 127 gives every decision a compact, permanent receipt: the
decision, rationale, alternatives, owner, affected work, review date, and
conversation evidence that produced it. “Why did we choose Kafka?” should
return its answer in ten seconds, before a user has to excavate artifacts.

Receipts unify the existing meeting-derived `decisions` and desk-authored
`desk_decisions` without replacing either source. Their revisions and
supersessions are append-only; their source moments remain openable; their
links let work point back to the choice that shaped it. The result is a
local-first decision memory with evidence rather than a mutable ADR copy.

## The architecture

```
 decisions ───────────────┐
 desk_decisions ──────────┼──→ DecisionReceiptService
 meetings / artifacts ────┘          │
                                     ▼
                         decision_receipts (v41)
                         ├─ sources: meeting / artifact / segment
                         ├─ work: project / workbench / action / meeting
                         └─ revisions: append-only history
                                     │
                  ┌──────────────────┼──────────────────┐
                  ▼                  ▼                  ▼
             Desk editor       review queue      FTS + MCP resource
                  │                  │                  │
                  └──────────── SyncService ────────────┘
```

## Constitutional grounding

- **Article V.2:** Every consequential choice leaves a durable receipt.
- **Article VI:** Receipts retain the evidence, alternatives, revisions, and
  supersession chain; they never rewrite history into a flattering summary.
- **Article IX:** The walk proves creation, evidence resolution, review,
  supersession, retrieval, MCP delivery, and sync against stored records.

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-127-01 | Receipt canon | done | [story-01](story-01-receipt-canon.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-127-02 | Unify decision origins | done | [story-02](story-02-unify-origins.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-127-03 | Exact meeting evidence | done | [story-03](story-03-meeting-evidence.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-127-04 | Receipt editor | done | [story-04](story-04-receipt-editor.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-127-05 | Affected-work links | done | [story-05](story-05-affected-work.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-127-06 | Review queue | done | [story-06](story-06-review-queue.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-127-07 | Supersede, never erase | done | [story-07](story-07-supersede-never-erase.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-127-08 | Ten-second retrieval | done | [story-08](story-08-ten-second-retrieval.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-127-09 | MCP tools and the walk | done | [story-09](story-09-mcp-and-walk.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-127-10 | Local-first sync | done | [story-10](story-10-sync.md) | [evidence-story-10](./evidence-story-10.md) |

## Where we are

Phase complete (10/10). Every consequential choice gets a permanent receipt:
decision, rationale, alternatives, owner, affected work, review date, and
the conversation that produced it. DecisionReceiptService with create/get/
list/update/search/supersede/sync. Schema v40→v42, 5 MCP tools, 1 MCP
resource, local-first sync with LWW conflict resolution and tombstones.
"Why did we choose Kafka?" answered in ten seconds.
