# HS-121-03 — The door must open

- **Project:** holdspeak
- **Phase:** 121
- **Status:** backlog
- **Depends on:** HS-121-01 (SurfaceState action slot)
- **Unblocks:** HS-121-12 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

Seven primitive kinds in the pullout registry resolve to `null`. The
SurfaceState action slot (story 01) enables empty states to guide
users. This story wires both together.

When this ships:

1. Every kind in the pullout registry resolves to a component.
   Kinds without a custom view render FallbackPullout.
2. Workbench kind opens WorkbenchWindow (not a pullout).
3. At least 8 high-value empty states use the new action slot:
   workbench items ("Add an item"), workbench runs ("Run now"),
   directory members ("Drop items here"), chain steps ("Add a step"),
   note body ("Start typing or speak"), zone window ("Move objects
   here"), commands ("Add a voice command"), cadence loops ("What's
   on your mind?").

## Acceptance criteria

- [ ] Zero null entries in the pullout registry.
- [ ] 8+ empty states have `onAction` + `actionLabel`.
- [ ] Action buttons function (clicking them does the thing).

## Files in scope

- `web/src/desk/pullouts/registry.ts`
- 8+ pullout/window consumers of SurfaceState
