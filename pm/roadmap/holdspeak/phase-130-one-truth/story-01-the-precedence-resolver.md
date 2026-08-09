# HS-130-01 — The precedence resolver: one placement authority

- **Project:** holdspeak
- **Phase:** 130
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-130-03, HS-130-04, HS-130-05
- **Owner:** unassigned

## The thesis (the bar)

"Where does this run?" has nine possible answers today, and the empty value
has three contradictory readings: the backend picks `this_machine`
(`workbench_conductor.py:453` — `wb.profile_id or "this_machine"`), RecipeEditor
labels `""` "Default runs on" and writes `""` (`RecipeEditor.tsx:107`), and
InfoWindow labels the same `""` "This device" and writes `null`
(`infoContract.ts:80,90`). This is the single change the owner will experience
as *simpler*. One resolver owns placement; `null`/unset means **inherit**,
never silently "this device."

### What changes

1. One resolver — `resolve_placement(scope) -> {effective_target_id, source}`
   where `source ∈ {invocation, workbench, agent, global}` — is the ONLY code
   that turns a stored placement pointer into an effective target. Precedence:
   invocation override → Workbench override → Agent/capability default →
   global default. `None` at every level inherits down; the global default is
   the one terminal fallback and it is named, not `"this_machine"` by accident.
2. `workbench_conductor.py:447-465` and `workbench_service.py:132` stop
   computing `wb.profile_id or "this_machine"` and call the resolver; the
   Agent default (`recipes.profile_id`, schema.py:958), currently skipped, is
   consulted as the tier between Workbench and global.
3. The four scoped labels replace the one overloaded "Runs on": **Default runs
   on** (global/Agent default), **Workbench runs on** (Workbench override),
   **Run this on** (invocation), **Retry on** (recovery — transient, see
   HS-130-07). RecipeEditor and InfoWindow render the same label vocabulary
   and the same empty-value meaning (inherit, with the inherited source shown).
4. A grep/AST guard forbids new `or "this_machine"` / inline placement
   fallbacks outside the resolver (the mechanism that keeps owner #9 from
   growing back — rides in this story, per Sol: guards land with the invariant
   they protect).

## Acceptance criteria

1. Exactly one function resolves a placement pointer to an effective target;
   Workbench and Agent runs both call it, and an Agent configured for a
   private endpoint is honored by its Workbench when the Workbench override is
   unset (today it is silently ignored — audit-2 claim 3).
2. Every placement API response carries `{effective_target_id, source}`; unset
   at a level reports the source it inherited from, never a bare target with
   no provenance.
3. `null`/unset never resolves to `this_machine` by fallback; the terminal
   global default is an explicit, named setting.
4. RecipeEditor and InfoWindow show one label vocabulary and one empty-value
   meaning; a value set in one is reflected as effective (with source) in the
   other.
5. The inline-fallback guard fails on a reintroduced `or "this_machine"`
   outside the resolver.

## Test plan

- Backend: unit tests for each precedence tier and each inherit-down path;
  a test that Workbench-unset + Agent-set resolves to the Agent target with
  `source: "agent"`; the guard test.
- Web: RecipeEditor/InfoWindow render tests for the four labels and the
  inherited-source line; typecheck.
- Full backend suite + `npm --prefix web run test:web -- run` read from file
  before flip.

## Out of scope

- Kernel admission of the resolved target (Phase 131).
- Deployment revisions / immutability (Phase 131).
- Meeting-specific placement policy (HS-130-05 consumes this resolver).
