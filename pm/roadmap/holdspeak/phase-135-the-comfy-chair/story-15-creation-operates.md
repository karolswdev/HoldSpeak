# HS-135-15 — Creation operates

- **Project:** holdspeak
- **Phase:** 135
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-135-13
- **Owner:** unassigned

## Problem

The setup-flows joy audit (2026-08-17, 57 shots, session scratchpad
`setup-flows/` + `setup-flows-joy-report.md`) found one creation flow
that does not OPERATE and two honesty breaks beside it — squarely
inside the owner's magnifying-glass mandate ("these things deserve to
look and feel and OPERATE incredibly easy"):

1. **Agent setup is a dead end.** "New Agent" creates the recipe and
   drops the user on the desktop staring at an icon — the inline
   editor (`RecipeEditor` via `InlineEditor`) never opens, unlike New
   Workflow which opens its builder immediately. The user is stranded
   with no name field, no next step (audit flow 2; the Object menu
   stayed ghosted even with the object selected).
2. **Run runs nothing, enabled.** A blank workbench's Run button is
   always enabled; clicking with no agent bound silently switches tabs
   to a "No agent bound" state. The ghosted-verb-with-reason grammar
   exists (floor menu) and is not used here (audit offense 12).
3. **"No agents match" lies.** The blank workbench's AGENT section
   shows a search-failure label over an empty universe; honest is "No
   agents yet" with a create path (audit offense 2).

## Scope

### In

- New Agent behaves like New Workflow: creation opens the editor
  immediately, cursor in the name field; root-cause why the editable-
  kind auto-open fails for recipes (z-order/GL positioning/selection
  timing — the audit's hypotheses) and fix the CLASS, with a test that
  every editable kind's create verb yields an open editor.
- Workbench Run ghosts (disabled with the reason label "Bind an agent
  first") when no agent is bound — the existing ghosted-verb grammar.
- The AGENT section's empty state says "No agents yet" with a create
  affordance (honest label; the create path may open the Desk New
  Agent verb).

### Out

- The full setup-joy redesign (cadence identity/comprehensibility,
  workbench progressive disclosure, workflow run affordance, the
  Agent/Agents naming collision, template-picker cron humanization) —
  next leg's charter on the audit evidence.

## Acceptance criteria

- [ ] "New Agent" opens the editor with focus in the name field
  (test + screenshot); the editable-kind guarantee is fenced for all
  kinds.
- [ ] Run is visibly disabled with the reason when no agent is bound;
  binding enables it (tests).
- [ ] The empty AGENT section reads "No agents yet" with a working
  create path (test).

## Test plan

- `cd web && npx vitest run` — creation/editor suites + workbench
  config suites + new fence; screenshots ride HS-135-13.
