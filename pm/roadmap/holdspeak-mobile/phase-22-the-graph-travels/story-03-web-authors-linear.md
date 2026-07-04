# HSM-22-03 — Web authors a linear graph (or honest scope)

- **Project:** holdspeak-mobile
- **Phase:** 22
- **Status:** todo
- **Depends on:** HSM-22-01 (the canonical authored shape to match).
- **Unblocks:** 22-04's any-surface leg.
- **Owner:** unassigned

## Problem

Survey-corrected: the remembered Wave-2 "web authors a linear graph" claim is **not
backed by code**. Today:

- No web surface emits `nodes`/`exec_edges` (grep-clean across `web/src`);
  `useDesk.createPrimitive` (`web/src/desk/store.ts:60`) has no workflow case.
- `web/src/pages/workbench.astro` + `scripts/workbench/model.js` build the ENGINE
  workflow shape and persist to localStorage only — never `/api/workflows`.
- `web/src/lib/primitives.ts:153` still types `graphJson?: string` against the object
  wire (the desk path routes around it via `fromWireWorkflow`).
- The desk run UI renders `steps` but drops the hub's `warning` (a refused graph runs
  linear silently for the web reader).

## The design

1. **The type fix:** `primitives.ts` `graphJson` becomes the object wire type.
2. **A minimal linear builder on the web desk:** author an ordered chain of the
   faithful-subset kinds (entry → llm/extract/summarize/rewrite/keepIf), emitted in
   the exact tagged-union + `exec_edges`/`data_edges` shape `linearize()` and the
   iPad speak, POSTed to the real `/api/workflows`. Linear only, honestly: control
   flow stays "graphed on iPad".
3. **The run UI renders the hub's `warning`** beside the steps trail.

## Scope

- **In:** the three items above + web build + a desk test locking the emitted shape
  against the same golden expectations 22-01 pins.
- **Out:** a full node-graph canvas on web (the iPad owns Blueprint authoring);
  executing control flow.

## Test plan

- `cd web && npm run build` + the desk vitest suite.
- `uv run pytest -q tests/unit/test_web_routes_primitives.py` (the web-emitted shape
  runs through the real route in a test).
