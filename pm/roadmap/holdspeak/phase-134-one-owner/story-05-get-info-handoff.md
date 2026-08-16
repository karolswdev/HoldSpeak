# HS-134-05 — Get Info hands off

- **Project:** holdspeak
- **Phase:** 134
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-134-10
- **Owner:** unassigned

## Problem

Two editors write `recipe.profile_id`: RecipeEditor
(`web/src/desk/pullouts/editors/RecipeEditor.tsx:118`, canonical) and
Get Info (`web/src/desk/infoContract.ts:97`, via
`InfoWindow.tsx:200-219`). Issue #450's ruling verbatim: "Agent Edit
owns this decision. Get Info should summarize and hand off." No guard
exists against dual-editor writes (audit risk 4).

## Scope

### In

- `infoContract.ts` stops writing `profile_id`; Get Info renders the
  placement summary (effective target + source once HS-134-04 lands;
  static summary until then) with an "Edit in Agent" hand-off that
  opens the RecipeEditor.
- A writer-guard test on the `settingsWriters.test.ts` pattern: recipe
  `profile_id` writes originate only from RecipeEditor.

### Out

- Any RecipeEditor redesign. Other Get Info fields.

## Acceptance criteria

- [x] `grep -n profile_id web/src/desk/infoContract.ts` shows no write
  path; the Info window shows summary + hand-off (screenshot in
  evidence).
- [x] The writer-guard test exists and fails if a second writer
  appears.
- [x] Focused vitest green.

## Test plan

- `cd web && npx vitest run` scoped to the info/recipe suites + the new
  guard; a live screenshot of the Info window rides evidence (walk
  covers both widths).
