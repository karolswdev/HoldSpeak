# HS-79-03 — `routes/primitives.py` becomes the primitives package

- **Project:** holdspeak
- **Phase:** 79
- **Status:** todo
- **Depends on:** nothing (parallel to 01/02).
- **Unblocks:** HS-79-04.

## Problem

`holdspeak/web/routes/primitives.py` is 1,294 lines: 41 routes over seven
primitive CRUD families (notes, agents, profiles, kbs, chains, workflows,
directories + membership) plus the shared run-persist logic the agent/chain/
workflow run endpoints ride (the Phase-74 run-born artifact tail).

## The design

`holdspeak/web/routes/primitives/` with one module per family and `_shared.py`
for the JSON-body/serializer/run-persist helpers, composed by
`build_primitives_router` in `__init__.py`. Bodies verbatim; the manifest
regenerates in the same commit; the run-persist helper stays ONE function
(both run endpoints call it — do not fork it during the move).

## Test plan

Full unit + integration suites green (the run-born artifact tests cover the
moved tail); `test_api_surface.py` green; patch-target edits listed.
