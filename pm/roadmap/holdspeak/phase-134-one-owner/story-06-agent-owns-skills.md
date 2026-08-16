# HS-134-06 — Skills belong to the Agent

- **Project:** holdspeak
- **Phase:** 134
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-134-10
- **Owner:** unassigned

## Problem

WorkbenchWindow mutates Agent-owned skill bindings globally:
`updateSkillBinding/attachSkill/detachSkill` at
`web/src/desk/components/WorkbenchWindow.tsx:1166-1190` (plus
`approveSkill` :1192-1197) write `skill.recipe_ids` and skill status
while rendering skills as the Workbench's own configuration
(:231-249). Issue #450's ruling verbatim: "Agent Edit owns Agent
skills. A Workbench may display inherited skills." No guard exists
(audit risk 5).

## Scope

### In

- Delete the four mutation paths from WorkbenchWindow; skills render
  read-only as INHERITED (from the bound agent), with an "Edit in
  Agent" hand-off.
- A guard test that WorkbenchWindow performs no `updateSkill` calls.
- Honest empty/disabled states per the kit grammar (no dead-looking
  controls — states say why).

### Out

- Workbench-level skill overrides (`workbench_skill_overrides`) — #450
  says display-only suffices; backlog if ever wanted. Agent editor
  changes.

## Acceptance criteria

- [ ] `grep -n "updateSkill\|attachSkill\|detachSkill\|approveSkill" web/src/desk/components/WorkbenchWindow.tsx`
  → zero mutation paths; read-only inherited display + hand-off render
  (screenshot in evidence).
- [ ] Guard test in place and meaningful.
- [ ] Focused vitest green; no orphaned handlers/dead imports.

## Test plan

- `cd web && npx vitest run` scoped to workbench suites + the new
  guard; both-widths rendering rides HS-134-10.
