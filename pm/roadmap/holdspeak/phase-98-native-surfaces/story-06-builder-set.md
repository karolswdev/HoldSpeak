# HS-98-06 — The builder set

- **Project:** holdspeak
- **Phase:** 98
- **Status:** backlog
- **Depends on:** HS-98-01
- **Unblocks:** HS-98-09

## Problem

Workbench (448), Studio (60), and Components (184) are the maker
surfaces. Workbench already owns a canvas idiom (node graph) but its
chrome (palette, inspector) is page-grammar; Studio and Components are
thin page shells.

## Scope

- In:
  - `WorkbenchCore`: canvas untouched; palette and inspector become
    surface sections/rows that collapse by container width;
  - `StudioCore` + `ComponentsCore` re-composed in the kit;
  - all three off the guard allowlist.
- Out:
  - workbench graph semantics, blueprint features.

## Acceptance criteria

- [ ] Three cores off the allowlist; guard green.
- [ ] Workbench save/load behavior unchanged (existing tests green).
- [ ] Reflow shots; `npm run check` + python suite green.

## Test plan

- Existing vitest; reflow shots; `npm run check`.

## Evidence required

- Before/after shots, guard output, suite output.
