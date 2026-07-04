# HSM-23-05 — Docs + the walk rider (schema safety joins the entry points)

- **Project:** holdspeak-mobile
- **Phase:** 23
- **Status:** todo
- **Depends on:** 23-01..04 (the features it documents).
- **Unblocks:** phase closeout; the standing rule that every phase carries its own
  documentation story ([[feedback_dedicated_docs_story]]), entry points included
  (the Phase-64 lesson).
- **Owner:** unassigned

## Problem

The iPad now refuses newer stores, backs up before migrating, reports its own health,
and renders the hub's doctor — and no entry-point doc says so. The desktop schema
matrix is documented (Phase 50, RELEASING/ARCHITECTURE); the iPad half is not.

## The design

1. **Entry points:** the README iPad/companion section + the web `/companion`
   explainer gain the schema-safety + readiness lines (labels, canon voice, no
   reassurance prose — the badge rule applies to docs copy about trust).
2. **ARCHITECTURE.md:** the trust-boundary/device-path diagrams' prose mentions the
   iPad refuse-newer mirror where the desktop matrix is described.
3. **The walk rider (`HSM-23-WALK-RIDER.md`):** R1–R2, ~2 minutes riding the staged
   couch session — R1: Settings → Readiness on the real iPad shows Store ok + the
   hub's sections against the live hub; R2: the owner's call on the refused-newer
   render (optional, seeded file).

## Scope

- **In:** the doc touches above + the staged rider.
- **Out:** any new behavior; desktop doc rewrites beyond the mirror mention.

## Test plan

- `uv run pytest -q tests/unit/test_doc_drift_guard.py` (voice + banned-copy green
  over the new prose).
- The rider is the owner's; staging it is this story's deliverable.
