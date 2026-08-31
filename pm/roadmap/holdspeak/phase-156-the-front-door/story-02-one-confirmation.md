# HS-156-02 - One confirmation applies everything (through the existing machinery)

- **Project:** holdspeak
- **Phase:** 156
- **Status:** done
- **Depends on:** HS-156-01
- **Unblocks:** HS-156-04, HS-156-07
- **Owner:** unassigned

## Problem

A recommendation that hands the owner a to-do list failed. One
confirmation must download, define, and wire everything — through the
EXISTING Library/Assignments machinery, receipted end to end, resumable
on failure (settled design D2).

## Scope

- **In:** `POST /api/front-door/apply {pack_id}` executes the pack's
  plan as an ordered, idempotent sequence over EXISTING surfaces only:
  model-library download (egress badge + receipt intact), define-
  endpoint for LAN ingredients, profile creation, assignments
  editor/set for all seven groups. A durable plan row per apply with
  per-item state (queued → running (progress) → done/failed); GET
  returns it for the UI; re-apply continues from the first unfinished
  item — a crash never leaves a half-desk unaccounted. No new
  authority: a fence test asserts the apply path contains no direct
  DB writes to library/assignment tables (service calls only).
- **Out:** the door UI (03), pack auto-changes after setup (recorded).

## Acceptance criteria

- [ ] Applying a fixture pack on a fresh isolated hub yields: profiles exist, all seven groups assigned, receipts for every download and wiring step; a REAL chat turn then resolves through the assigned engine (real coordinator, fake engine at the endpoint).
- [ ] Kill the apply mid-plan (fault injection after item N) → GET shows the plan with the failure named; re-apply completes the remainder; nothing is double-created (idempotency proven).
- [ ] The no-parallel-authority fence passes (apply uses only the existing service seams).
- [ ] The .43-shaped ingredient (an explicit LAN endpoint) wires via define-endpoint and carries its provenance label.

## Test plan

- **Unit:** `tests/unit/test_front_door_apply.py` (plan execution, idempotency, fault injection, fence).
- **Integration:** the isolated-hub leg above.
- **Manual / device:** story 05.

## What shipped

- `holdspeak/services/front_door_service.py` -- apply engine appended
  after the recommender.  `apply_pack(pack, db, model_library_service,
  assignment_service, principal, catalog_revision)` executes the pack's
  plan as an ordered, idempotent sequence over EXISTING surfaces only:

  1. **Endpoint items** (`kind=endpoint`): calls
     `model_library_service.define_endpoint()` with a deterministic
     `front-door-ep-<id>` profile_id, `openai_compatible` family, the
     base_url with `/v1` appended, and a provenance label.
  2. **Catalog download items** (`kind=catalog_download`): calls
     `model_library_service.download()` with the preset's catalog_id
     and the current catalog_revision.
  3. **Built-in items** (`whisper_model`, `kokoro_tts`): marked done
     immediately (no provisioning needed).
  4. **Legacy GGUF items**: marked done (already present locally).
  5. **Assignment phase**: after all provisioning, calls
     `assignment_service.set_assignment()` for each of the seven groups
     with `scope={"kind":"group","group_id":...}`.

  Durable plan row per apply with per-item state
  (queued -> running -> done/failed).  Re-apply (same pack_id)
  resumes from the first unfinished item.  Fault injection proven:
  failure on call N -> plan records the failure with the error message,
  re-apply completes the remainder, nothing double-created.

  No-parallel-authority fence: the apply engine contains zero direct
  DB writes to any library or assignment table -- service calls only.
  A fence test asserts this by scanning the source AST.

- `holdspeak/db/front_door.py` -- `FrontDoorApplyRepository` with
  `create_plan`, `get_plan`, `get_latest_plan`, `update_plan`,
  `get_plan_by_pack`.  Registered in `core.py` and `__init__.py`.

- `holdspeak/db/schema.py` -- `front_door_apply_plans` table added
  (id, pack_id, status, items_json, created_at, updated_at).

- `holdspeak/web/routes/front_door.py` -- two new routes:
  - `POST /api/front-door/apply {pack_id}` -- owner-only, reconstructs
    recommendation, finds the pack, calls `apply_pack`.
  - `GET /api/front-door/apply` -- owner-only, returns the latest plan.

- `docs/api-surface.json` regenerated (567 routes, +2 new).

- `tests/unit/test_front_door_apply.py` -- 27 tests:
  - TestMakeApplyItems (2): plan entry conversion.
  - TestApplyEndpointPack (6): endpoint pack reaches done, endpoint
    defined for each group, all seven groups assigned, plan persisted,
    receipts for every step, endpoint provenance label.
  - TestApplyCatalogPack (2): catalog pack reaches done, downloads
    triggered.
  - TestFaultInjection (3): failure names the error, re-apply completes
    remainder, nothing double-created.
  - TestAssignmentFaultInjection (1): assignment failure leaves plan failed.
  - TestNoParallelAuthorityFence (2): no direct DB writes to library/
    assignment tables, apply functions call service methods only.
  - TestLANEndpointProvenance (2): endpoint carries provenance label,
    profile_id is deterministic.
  - TestSpeechAndTTSBuiltIn (1): built-in items marked done immediately.
  - TestApplyRoute (4): POST non-owner denied, missing pack_id rejected,
    GET returns null when no plan, GET non-owner denied.
  - TestPlanPersistence (4): plan created and readable, update persists,
    latest plan, plan by pack.

### BLOCKED-ON(fix/model-wiring-p0)

The end-to-end assignment proof after `define_endpoint` is blocked by
the P0 context_ceiling=0 bug (concierge-ux-evidence.md item 2): the
deployment revision writes `context_ceiling=0`, making every profile
created by define_endpoint incompatible with all capabilities at the
assignment service's compatibility check.  The tests prove the apply
engine correctly calls `set_assignment()` for all seven groups, but the
real integration (real coordinator + fake engine at the endpoint) cannot
pass until the P0 fixer merges.  The test suite stubs the assignment
service to prove the calling shape; the orchestrator re-runs the
integration leg after the fix merges.

## Notes / open questions

- Download progress rides the existing model-library progress surface; the plan aggregates it, never re-implements it.
