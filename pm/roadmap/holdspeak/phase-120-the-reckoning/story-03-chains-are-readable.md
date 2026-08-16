# HS-120-03 — Chains are readable

- **Project:** holdspeak
- **Phase:** 120
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-120-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

The ChainPullout renders step IDs as raw UUIDs. There is no Edit verb
in the footer, and no empty state when a chain has zero steps. A chain
is a central composition primitive — it must be intelligible.

When this ships:

1. Step IDs are resolved to agent/recipe names via the store's recipe
   items. Unresolvable IDs fall back to a truncated ID with a "?"
   indicator.
2. An Edit verb appears in the footer (matching recipe/workflow
   pullouts).
3. Empty chains show `SurfaceState empty` with "No steps" and an
   "Add step" affordance.

## Acceptance criteria

- [ ] Chain steps display resolved agent/recipe names, not UUIDs.
- [ ] Footer has an Edit verb.
- [ ] Empty chain shows `SurfaceState empty`.

## Test plan

- Open a chain with steps; verify names render.
- Open an empty chain; verify empty state.
- Click Edit; verify editor opens.

## Files in scope

- `web/src/desk/pullouts/ChainPullout.tsx`
