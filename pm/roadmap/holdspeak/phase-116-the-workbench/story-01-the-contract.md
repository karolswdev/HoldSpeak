# HS-116-01 — The contract

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-116-02, HS-116-03, HS-116-06, HS-116-07
- **Owner:** unassigned

## The thesis (the bar)

A Workbench is a new DeskPrimitive. It has an identity, an agent
(recipe), an inference target, a schedule, and a list of items. The
backend CRUD exists, the kernel admits workbench runs as bounded
children of the owning recipe's authority, and the API contract is
typed and documented. When this ships, the system knows what a
workbench *is* — even if no surface renders it yet.

**Articles served:** II (everything is a primitive), III (honest
egress — the target carries the boundary), V (consent spine — runs
produce proposals, not actions), XI (kernel admission — workbench
runs are admitted, receipted, bounded).

## Deliverables

1. **WorkbenchRecord DB model.** SQLite table: `id`, `name`,
   `recipe_id` (FK → recipes), `profile_id` (FK → inference
   targets), `schedule` (cron expression or null for manual),
   `schedule_enabled` (bool), `item_order` (JSON array of item IDs),
   `created_at`, `updated_at`. Synced between devices.

2. **WorkbenchItemRecord DB model.** SQLite table: `id`,
   `workbench_id` (FK), `title`, `body` (markdown), `priority`
   (int), `status` (pending/claimed/done/dismissed), `grounding`
   (JSON — meetings, artifacts, resources, same shape as chat
   grounding), `context` (JSON — attached constitutional + ad-hoc
   context), `result` (markdown — agent output), `result_egress`
   (JSON — placement receipt), `claimed_at`, `completed_at`,
   `created_at`, `updated_at`.

3. **CRUD API routes.** Under `/api/workbenches`:
   - `GET /` — list all workbenches
   - `POST /` — create (name, recipe_id, profile_id, schedule)
   - `GET /{id}` — single workbench with items
   - `PUT /{id}` — update config
   - `DELETE /{id}` — delete (refuses if items are claimed/running)
   - `POST /{id}/items` — add item
   - `PUT /{id}/items/{item_id}` — update item
   - `DELETE /{id}/items/{item_id}` — remove item
   - `POST /{id}/items/{item_id}/reorder` — move item in priority
   - `POST /{id}/run` — trigger a manual run (kernel-admitted)

4. **Kernel admission.** A workbench run is admitted through the
   kernel as `workbench_run` effect kind. The principal is the
   owner. The authority basis is the recipe's system prompt +
   constitutional context + the item's grounding. The target is
   the workbench's `profile_id`. The receipt records: items
   attempted, items completed, items failed, egress boundary,
   model used, tokens consumed.

5. **Workbench item kind in desk API.** The desk `api.ts` gains
   `workbench` as an item kind so workbenches appear as objects
   on the Desk.

6. **Contract doc.** `docs/workbenches.json` — the versioned
   contract (schema version, field semantics, kernel effect kind,
   receipt shape).

## Test plan

- `uv run pytest -q` — schema migration, CRUD round-trip, kernel
  admission for workbench_run, receipt generation, deletion refusal
  for active items.
- API probe: create a workbench with a recipe and target, add items,
  trigger a manual run, verify the receipt includes egress and token
  count.
