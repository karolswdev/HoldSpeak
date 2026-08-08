# HS-127-09 — MCP tools and the walk

- **Project:** holdspeak
- **Phase:** 127
- **Status:** backlog
- **Depends on:** HS-127-08
- **Unblocks:** HS-127-10
- **Owner:** unassigned

## The thesis (the bar)

Receipts are a desk capability, not a UI-only feature. MCP must expose the
same receipt lifecycle, and an end-to-end walk must prove it against durable
local records.

### What changes

1. Add receipt create, get, edit, link, review, supersede, and search tools.
2. Publish `holdspeak://decision-receipts/{id}` with sources, work, revisions,
   lifecycle, and lineage.
3. Keep tool validation and errors aligned with `DecisionReceiptService`.
4. Add a walk covering the full receipt lifecycle and exact evidence opening.

## Acceptance criteria

1. MCP can create and retrieve a receipt from both supported origins.
2. The resource exposes current facts plus source, work, revision, and lineage.
3. Invalid tool requests fail by name without partial receipt mutation.
4. The walk proves create, edit, link, review, supersede, retrieval, and proof.

## Test plan

- MCP: exercise every receipt tool and resource serialization path.
- Contract: compare MCP results with service results for one receipt lifecycle.
- Walk: run the recorded end-to-end scenario against a fresh local archive.
