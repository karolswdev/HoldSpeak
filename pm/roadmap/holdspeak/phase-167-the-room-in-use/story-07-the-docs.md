# HS-167-07 - The docs: the Rooms guide re-shot, the library contract, the sidecar counts guarded

- **Project:** holdspeak
- **Phase:** 167
- **Status:** backlog
- **Depends on:** HS-167-05, HS-167-06
- **Unblocks:** HS-167-08
- **Owner:** unassigned

## Problem

The public Project Rooms guide (166-06) shows the old faces; the
library contract does not yet name 03's species; docs/MCP_SIDECAR.md
carries stale per-family counts (desk: 47 vs ~63; 18 of 33 families
listed) with no guard — the 166 ledger's D4.

## Scope

- **In:** the Rooms guide's shots re-taken on the recomposed faces
  and its walk re-told as the Tuesday walk (what the owner did, in
  order, no promotion); the setup prerequisites unchanged and
  re-verified; contract.md sections for every 03 species;
  docs/MCP_SIDECAR.md regenerated from the registry with a doc
  drift guard test that fails on any stale count or missing family
  (the resources.py precedent: generate from the one source); the
  new route + tool (02's trigger, the cadence field) documented; the
  roadmap-vocabulary guard and the doc drift guard run and read.
- **Out:** canon edits (none needed — the SRS is unchanged).

## Acceptance criteria

- [ ] The guide's every shot is of a recomposed face; its walk matches the walk script step for step.
- [ ] MCP_SIDECAR.md counts equal the registry's, proven by the guard; zero drift-guard failures.
- [ ] contract.md names every species in the barrel.

## Test plan

- **Docs:** tests/unit/test_docs_*guard* (the existing drift + vocabulary guards) + the new sidecar-counts guard.
