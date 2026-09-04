# HS-167-07 - The docs: the Rooms guide re-shot, the library contract, the sidecar counts guarded

- **Project:** holdspeak
- **Phase:** 167
- **Status:** done
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

- [x] The guide's every shot is of a recomposed face; its walk matches the walk script step for step.
- [x] MCP_SIDECAR.md counts equal the registry's, proven by the guard; zero drift-guard failures.
- [x] contract.md names every species in the barrel.

## Landed (2026-09-03)

docs/MCP_SIDECAR.md is now GENERATED from the registry
(scripts/gen_mcp_sidecar_doc.py, the gen_api_surface precedent) with a
drift guard (tests/unit/test_mcp_sidecar_doc_drift.py) that fails on
any stale count or missing family — the corrections it forced: 186 →
187 tools, desk 47 → 52 (scheduled_recording/zone/kb/decision.supersede
/dictation were uncounted), project 34 → 35, people 14 → 16, the
project palette 44 → 45; docs/README.md follows. The new surface
documented where 166 documented Jira: project.steward.trigger (desk-
wide, typed 503 `scheduler_not_wired`, never route-level dedup),
project.setup.clarify_jira_scope, evaluation_cadence_minutes (1..10080)
on the policy PUT + set_rules, the cross-process acli file lock +
HOLDSPEAK_ACLI_LOCK_TIMEOUT. docs/PROJECT_ROOMS.md (166-06's guide had
NO images and no walk) now carries fourteen shots of the recomposed
faces (docs/assets/project-rooms/) and the walk re-told in the
Tuesday order, no promotion. contract.md was completed by 03. Guards
read by the orchestrator: the sidecar drift guard + the doc drift guard
+ the vocabulary guard green; the generator idempotent. Note: the
product-copy guard's failures on this branch all pre-exist on main
(verified by git grep) — baseline.

## Test plan

- **Docs:** tests/unit/test_docs_*guard* (the existing drift + vocabulary guards) + the new sidecar-counts guard.
