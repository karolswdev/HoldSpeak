# HS-122-02 — Workbench service

- **Project:** holdspeak
- **Phase:** 122
- **Status:** done
- **Depends on:** HS-122-01 (primitive service — shared patterns)
- **Unblocks:** HS-122-06 (thin routes audit)
- **Owner:** unassigned

## The thesis (the bar)

The workbench route module is a 161-line fat controller. Template
instantiation creates a recipe, workbench, starter items, and binds
skills in loops. Voice resolution builds a catalog, performs kernel
admission, and processes receipts. Retry mint resolves multiple
dependencies. These operations are trapped in HTTP handlers.

When this ships, a `WorkbenchService` class owns all workbench
orchestration. The route module becomes a thin adapter.

## Scope

- `WorkbenchService.list(principal, query?, limit?)`
- `WorkbenchService.get(principal, id) → WorkbenchDetail`
- `WorkbenchService.create(principal, fields)`
- `WorkbenchService.update(principal, id, patch)`
- `WorkbenchService.delete(principal, id)`
- `WorkbenchService.instantiate_template(principal, template_id, profile_id?)`
- `WorkbenchService.add_item(principal, wb_id, item)`
- `WorkbenchService.update_item(principal, wb_id, item_id, patch)`
- `WorkbenchService.delete_item(principal, wb_id, item_id)`
- `WorkbenchService.run(principal, wb_id)` — delegates to conductor
- `WorkbenchService.list_runs(principal, wb_id)`
- `WorkbenchService.list_memory(principal, wb_id)`
- `WorkbenchService.clear_memory(principal, wb_id)`
- `WorkbenchService.promote_memory(principal, wb_id, index)`
- `WorkbenchService.resolve_voice(principal, wb_id, text, request_id)`
- `WorkbenchService.retry_mint(principal, wb_id, item_id)`

## Acceptance criteria

- [ ] `WorkbenchService` class exists with all listed methods.
- [ ] Each method takes an explicit `Principal`.
- [ ] Route handlers delegate entirely — no `get_database()` in routes.
- [ ] Template instantiation logic moved from route to service.
- [ ] Voice resolution logic moved from route to service.
- [ ] Existing API behavior unchanged.
- [ ] Tests pass.

## Files in scope

- New: `holdspeak/services/workbench_service.py`
- `holdspeak/web/routes/primitives/workbenches.py`
