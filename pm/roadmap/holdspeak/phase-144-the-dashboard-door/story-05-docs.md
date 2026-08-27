# HS-144-05 — Docs

- **Project:** holdspeak
- **Phase:** 144
- **Status:** backlog
- **Depends on:** HS-144-04
- **Unblocks:** HS-144-06
- **Owner:** unassigned

## Problem

The Door changes what the owner sees first and adds a calendar
ingest with an egress surface. The entry-point docs must tell the
new truth before the phase closes (house law: a dedicated docs story
after features, before closeout — touching ENTRY points).

## Scope

### In

- **README** (public surface): the front-door description matches the
  Door — the one-sentence open, then the board + upcoming rail.
- **USER_GUIDE / owner-facing docs**: the kanban (what the columns
  mean, that card moves are real verbs with receipts), the upcoming
  rail, the ICS subscription (file and URL, the egress truth, the
  14-day horizon), Chair-level schedule create.
- **SECURITY / egress docs**: the ICS URL fetch row — what is
  fetched, when, what never leaves.
- **MCP_SIDECAR**: the `door.get` (and any calendar) tool entries;
  the inventory count updated truthfully (the Phase 143 lesson — the
  count edit is cheaper than the ledger note).
- **Retired-vocabulary check**: if HS-144-03 removed lane components
  or names, the doc guard must not find them referenced (the 143
  guard precedent).
- Positioning voice rules apply (`docs/internal/POSITIONING.md`);
  no privacy novels — one badge, named once.

### Out

- New canon documents; ARCHITECTURE_* rewrites (the Door composes
  existing services — a paragraph where one already fits, not a new
  doc).
- Roadmap files (the orchestrator authors those directly).

## Acceptance criteria

- [ ] Every entry point above tells the Door truth; a cold reader
  finds board, rail, and ICS subscription without internal lore.
- [ ] Doc guards / mermaid renderers / MCP inventory checks pass
  (`uv run --python 3.13.11 pytest -q tests/ -k doc` under isolated
  HOME — the generators-open-DBs law applies).
- [ ] No retired vocabulary survives in docs (guard or grep in
  evidence).

## Test plan

- `HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q tests/ -k
  "doc or mcp_inventory"` (exact selector confirmed in the plan).
