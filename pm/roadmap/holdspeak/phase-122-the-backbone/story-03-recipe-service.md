# HS-122-03 — Recipe service

- **Project:** holdspeak
- **Phase:** 122
- **Status:** done
- **Depends on:** HS-122-01 (primitive service — shared patterns)
- **Unblocks:** HS-122-06 (thin routes audit)
- **Owner:** unassigned

## The thesis (the bar)

The recipe route module's `api_run_recipe` is 166 lines of inline
orchestration: lifecycle bookkeeping, prompt rendering, inference
target resolution/readiness, engine call, cancellation/error/empty
handling, provenance, artifact persistence. Chat builds contextual
prompt blocks and hydrates grounding. This is the most complex
operation in the system and it's trapped in a route handler.

When this ships, a `RecipeService` class owns the run lifecycle,
chat, and CRUD. The route becomes a thin adapter.

## Scope

- `RecipeService.list(principal, query?, limit?)`
- `RecipeService.get(principal, id)`
- `RecipeService.create(principal, fields)`
- `RecipeService.update(principal, id, patch)`
- `RecipeService.delete(principal, id)`
- `RecipeService.run(principal, id, input, grounding?, target_id?)`
- `RecipeService.chat(principal, id, message, history?, grounding?)`
- `RecipeService.list_skills(principal, recipe_id?)`
- `RecipeService.update_skill(principal, skill_id, patch)`

## Acceptance criteria

- [ ] `RecipeService` class exists with all listed methods.
- [ ] Run lifecycle (166 lines) fully extracted from route.
- [ ] Chat conversation flow extracted from route.
- [ ] Prompt rendering, target resolution, inference, provenance,
      artifact persistence — all in the service.
- [ ] Route handlers are thin: deserialize, call service, serialize.
- [ ] Existing API behavior unchanged.
- [ ] Tests pass.

## Files in scope

- New: `holdspeak/services/recipe_service.py`
- `holdspeak/web/routes/primitives/recipes.py`
