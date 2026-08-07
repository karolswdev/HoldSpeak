# HS-123-01 — Service errors and imports

- **Project:** holdspeak
- **Phase:** 123
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-123-02, HS-123-03, HS-123-04, HS-123-05, HS-123-06, HS-123-07, HS-123-08
- **Owner:** unassigned

## The thesis (the bar)

Phase 122 introduced services, but the boundary is still inverted. `PrimitiveService`
and `RecipeService` import helpers from FastAPI route modules, and the two
service-specific exceptions contain HTTP status codes and route-ready payloads.
An MCP caller can therefore reach a service that depends on the HTTP layer.

This story establishes the one-way dependency rule for the rest of Phase 123:

```text
HTTP routes / MCP / tests
          ↓
application services ──→ services.errors + services.support ──→ domain / db / kernel
```

`holdspeak.services` must never import `holdspeak.web.routes`. Services raise
stable domain errors (`code`, `detail`, `context`); each transport maps those
errors to its own response representation at its edge. The route response bytes
and status codes already observed by clients must remain unchanged.

This is a structural extraction only. It does not add an API, alter persistence,
or redesign inference, grounding, lineage, or graph execution.

## Current audit and required end state

### Error ownership

**Today**

- `holdspeak/services/primitive_service.py:20-34` defines `NotFound`,
  `ValidationError`, and `ConflictError`, despite six peer services importing
  them:
  - `recipe_service.py:11`
  - `profile_service.py:9`
  - `dictation_service.py:12`
  - `coder_service.py:9`
  - `meeting_service.py:15`
  - `workbench_service.py:11`
- Routes import the same types from `primitive_service.py` at:
  `web/routes/primitives/{chains,decisions,directories,kbs,notes,profiles,recipes,workbenches,workflows}.py`,
  `web/routes/meetings/{crud,live}.py`, and `web/routes/system/coders.py`.
- `holdspeak/services/workbench_service.py:20-27` defines
  `WorkbenchServiceError(error, status_code, detail)`.
- `holdspeak/services/recipe_service.py:20-26` defines
  `RecipeServiceError(status_code, payload)` and raises it at lines
  `132, 150, 170, 178, 188, 206, 281, 302, 317, 350`.

**After**

`holdspeak/services/errors.py` is the sole owner of these domain exception
classes:

```python
class ServiceError(Exception):
    code: str       # stable domain token, never an HTTP status
    detail: str     # human-readable failure text
    context: dict   # operation metadata; no transport envelope

class NotFound(ServiceError): ...
class ValidationError(ServiceError): ...
class ConflictError(ServiceError): ...
```

Make the base constructor explicit: `ServiceError(code, detail, *, context=None)`
normalizes `context` to a fresh dictionary and calls `Exception.__init__(detail)`.
Keep compatibility attributes needed by existing adapters while changing no route
wire shape:

- `NotFound(kind, id)` sets `code="not_found"`, `detail="Unknown {kind}: {id}"`,
  `context={"kind": kind, "id": id}`, and keeps `.kind` / `.id`.
- `ValidationError(detail, *, code="validation_error", context=None)` preserves
  existing `ValidationError("...")` call sites.
- `ConflictError(detail, *, existing_name="", code="conflict", context=None)`
  preserves `.existing_name` and includes it in context only when non-empty.

Delete `WorkbenchServiceError` and `RecipeServiceError`. Replace every raise with
`ServiceError` (or a subtype where appropriate), using a stable code plus the
former payload fields as `context`. At minimum use the following codes:

| Current source / current lines | Domain code | Route HTTP status | Required preserved response data |
|---|---|---:|---|
| Recipe run empty input, `recipe_service.py:128-135` | `empty_input` | 400 | `error`, `invocation`, `invocation_id` |
| Recipe target not ready, `149-153`; chat target not ready, `298-303` | `target_unavailable` | 409 | existing `target_refusal()` keys plus recipe and invocation data where present |
| Recipe inference exception, `165-173`; chat exception, `314-320` | `inference_failed` | 502 | existing error, target, alternate-target, invocation fields |
| Recipe cancellation, `174-182` | `cancelled` | 409 | `operation_id` and invocation fields |
| Recipe blank output, `183-191` | `empty_output` | 502 | existing error and invocation fields |
| Recipe artifact failure, `204-209`; keep failure, `345-351` | `artifact_persist_failed` | 500 | existing error, recipe, invocation fields |
| Recipe unknown grounding, `277-282` | `grounding_not_found` | 400 | `unknown_ids` |
| Workbench mint failure, `159-161` | `artifact_persist_failed` | 500 | `{"error": "Mint failed"}` |
| Workbench resolver failures, `294-338` | existing domain names `resolver_rate_limited`, `resolver_not_configured`, `resolver_unavailable`, `resolver_refused` | respectively 429, 409, 503, 403 | the existing `error` and optional `detail` fields |

The codes are the service contract. The status lookup belongs in the routes, not
in an exception or service. Add local route functions in
`web/routes/primitives/recipes.py:19-148` and
`web/routes/primitives/workbenches.py:18-35` that translate only their relevant
codes and serialize `{"error": exc.detail, **exc.context}` (with the existing
workbench `detail` representation retained). Do not introduce FastAPI,
`JSONResponse`, `status_code`, or a route payload type into `errors.py` or a
service module.

### Inverted helper imports

**Today**

```text
PrimitiveService (primitive_service.py:465-466, 495)
  ├─ web.routes.primitives._shared.capability_descriptor
  └─ web.routes.workflow_graph.linearize

RecipeService (recipe_service.py:92-94, 157, 247-249, 306-309, 338-339, 359-360, 387-388)
  ├─ web.routes.primitives._shared.RunLifecycle, _persist_run_artifact,
  │  _render_user_prompt, canonical_source_type, capability_descriptor
  ├─ web.routes.primitives.ask._GROUNDING_EXPANDS, _GROUNDING_MAX_REFS,
  │  _hydrate_grounding, _run_egress, _context_material
  └─ skill_injection.inject_skills
```

**After**

```text
services.primitive_service ─┐
services.recipe_service ────┼──→ services.errors
                            └──→ services.support
web routes / conductor ─────────→ services.errors and services.support
```

`services.support` may import domain modules such as `holdspeak.grounding`,
`holdspeak.inference_targets`, `holdspeak.intel.providers`, `holdspeak.config`,
`holdspeak.kernel`, `holdspeak.db`, and `holdspeak.logging_config`. It must not
import `fastapi`, `holdspeak.web`, `holdspeak.web.routes`, `WebContext`, request
objects, `JSONResponse`, or `get_database()` as hidden service state.

## Exact extraction recipe

Create `holdspeak/services/support.py`. The following source ranges are current
line anchors; move their behavior with the stated dependency corrections, not
blind text copies.

| Current owner and lines | Move to `services/support.py` | Required dependency treatment |
|---|---|---|
| `web/routes/primitives/_shared.py:36-56` | `CANONICAL_SOURCE_TYPES`, `_SOURCE_TYPE_ALIASES`, `canonical_source_type()` | Move the constants with the function so `canonical_source_type` remains the only source vocabulary normalizer. |
| `_shared.py:58-83` | `capability_descriptor()` | Pure helper; preserve its returned keys/defaults byte-for-byte. |
| `_shared.py:86-272` | `RunLifecycle` | This is a required dependent extraction even though it was absent from the first audit list: `RecipeService.run()` imports it at line 92. Keep its kernel/db behavior; give support its own UUID helper rather than importing route `_new_id`. |
| `_shared.py:282-303` | `_render_user_prompt()` | Preserve unknown-brace and malformed-template fallback behavior. |
| `_shared.py:337-372` | `_persist_run_artifact()` | Change its signature to accept `db: Database` explicitly. Generate the artifact ID locally, call `db.plugins.record_artifact`, and retain the current “log then return `None`” failure behavior. Remove its lazy `get_database()` import. Update every call with the caller's database. |
| `skill_injection.py:7-56` | `SKILL_BUDGET_BYTES`, `skills_for_recipe()`, and `inject_skills()` | Move the collaborating helper and logger with `inject_skills`; otherwise the claimed owner remains split. Pass `db` explicitly to `skills_for_recipe` / `inject_skills` (and update call sites) rather than resolving a global database. Remove `holdspeak/skill_injection.py` after every consumer moves. |
| `web/routes/primitives/ask.py:22-29, 57-82` | grounding aliases/constants and `_run_egress()` | `_hydrate_grounding` and its detailed variant already live in `holdspeak.grounding`; support must import/re-export them from there, not duplicate their implementation. Move `_GROUNDING_EXPANDS` and `_GROUNDING_MAX_REFS` as aliases of the grounding constants. Refactor egress to accept `(profile, intel, *, default_model: str)`; it may load domain config/provider helpers, but it must not accept `WebContext` or import `web.routes.sync._hub_model_name`. The route obtains its default model and passes it in. |
| `ask.py:85-113` | `_context_material()` | Move `meeting_digest` and logging dependencies to support. Keep the same tolerant per-kind lookup and empty fallback. `ask.py:_assemble_material` calls the support helper. |
| `web/routes/workflow_graph.py:42-405` | graph types, constants, and helpers | Move the complete cohesive pure graph module: `GraphNode`, `LinearPlan`, `_norm_failure_policy`, `_norm_run_target`, `_node_kind`, `parse_graph`, `_parse_exec_edges`, `linearize`, `_extract_artifact_type`, `build_node_prompt`, `apply_pure_transform`, `resolved_failure_policy`, `on_node_error`, and all `_...KINDS` constants. Delete `workflow_graph.py`; leaving a forwarding module preserves a route-owned import path and masks a regression. |

Keep route-only helpers in `_shared.py`: `_new_id`, `_json_body`, and `_run_frame`.
They depend on request or `WebContext` concerns and are not service support.

## File-by-file change list

The builder must update each listed import, not only the two imports named by the
audit. Line numbers below refer to the pre-story tree.

### New modules

- **New `holdspeak/services/errors.py`** — implement the hierarchy and
  compatibility constructors defined above.
- **New `holdspeak/services/support.py`** — own every item in the extraction
  table. Its module-level imports must be domain-only.

### Service modules

- **`holdspeak/services/primitive_service.py:11-13, 20-34, 465-466, 495`** —
  import errors from `.errors`; delete local classes; import
  `capability_descriptor` and `linearize` from `.support`.
- **`holdspeak/services/recipe_service.py:8-26, 92-94, 157-161, 247-249,
  277-282, 306-309, 322-323, 338-350, 359-367, 387-397`** — replace every
  route/skill import with `.errors` / `.support`; pass `self._db` to artifact
  persistence and skill injection; replace all HTTP-shaped exceptions using the
  mapping table; replace `egress_context: Any` with a neutral
  `default_model: str = ""` argument.
- **`holdspeak/services/workbench_service.py:8-10, 20-27, 159-161, 294-338`** —
  import the common errors, delete `WorkbenchServiceError`, and raise
  `ServiceError` with the existing domain error strings as codes and former
  detail as `detail`.
- **`holdspeak/services/{profile,dictation,coder,meeting}_service.py` at
  lines `9, 12, 9, 15` respectively** — change only the common-error import
  from `.primitive_service` to `.errors`. Confirm `kernel_service.py` has no
  error import; do not add a needless one.

### Routes and non-route consumers

- **Common errors:** change the imports in
  `web/routes/primitives/chains.py:14`, `decisions.py:10`, `directories.py:10-14`,
  `kbs.py:10`, `notes.py:10`, `profiles.py:17`, `recipes.py:10-11`,
  `workbenches.py:9-10`, `workflows.py:16`,
  `web/routes/meetings/crud.py:17`, `live.py:12`, and
  `web/routes/system/coders.py:22` to `holdspeak.services.errors`.
- **Recipe adapter:** `web/routes/primitives/recipes.py:10-15, 91-146` imports
  `ServiceError` instead of `RecipeServiceError`, uses the code-to-status mapper
  described above, and passes the route-derived default model rather than
  `WebContext` into `RecipeService.chat()`.
- **Workbench adapter:** `web/routes/primitives/workbenches.py:9-14, 31-35`
  imports `ServiceError`, maps its four resolver codes plus
  `artifact_persist_failed`, and produces precisely the former response body and
  status.
- **Support consumers:** move imports in
  `web/routes/primitives/chains.py:17-20`,
  `web/routes/primitives/workflows.py:19-25, 152-160`,
  `web/routes/primitives/ask.py:22-35, 57-132`,
  `web/routes/primitives/__init__.py:16`,
  `web/routes/decisions.py:281`, and
  `web/routes/delivery_prs.py:246, 317` to `holdspeak.services.support`.
  Route-only `_json_body`, `_new_id`, and `_run_frame` imports stay in
  `_shared.py`.
- **`holdspeak/workbench_conductor.py:19, 166-171, 219, 460, 477`** — replace
  its route helper and skill imports with support imports. Keep only route
  concerns in routes.
- **Delete `holdspeak/web/routes/workflow_graph.py`** after all imports move.
  **Delete `holdspeak/skill_injection.py`** after `RecipeService` and
  `workbench_conductor` use support. Do not retain compatibility wrappers that
  reintroduce service-to-route reachability.
- **`holdspeak/web/routes/primitives/_shared.py:36-83, 86-272, 282-303,
  337-372`** — remove the moved definitions and their now-unused imports.
  Its remaining code must not import support merely to re-export service-owned
  functions.

### Tests to update or add

- Update imports in `tests/unit/test_workflow_graph.py:9`,
  `tests/unit/test_blueprint_graph_conformance.py:18`,
  `tests/unit/test_doctor_runtime_profiles.py:109`, and
  `tests/unit/test_mesh_relay_provider.py:322` to import support directly.
  Adapt egress test calls to supply `default_model` rather than a route context.
- Preserve and run existing response coverage in
  `tests/unit/test_web_routes_recipe_chat.py`,
  `test_web_routes_primitives.py`, `test_web_routes_sync_primitives.py`,
  `test_recipe_pinned_context.py`, `test_workbench_triage.py`, and
  `test_workbench_triage_kernel.py`.
- Add focused service tests (new test file is acceptable) that instantiate each
  common error and assert `code`, `detail`, `context`, `str(exc)`, plus
  `NotFound.kind/id` and `ConflictError.existing_name` compatibility.
- Add route tests for every row in the error mapping table. Assert both status
  and JSON body, especially `empty_output` remaining HTTP 502 and
  `target_unavailable` remaining HTTP 409.

## Implementation order

1. **Inventory before moving.** Run the verification greps below and record the
   current import/consumer set. Read the route tests before modifying mappings;
   response preservation is a hard constraint.
2. **Create the error foundation.** Add `errors.py`, migrate the three common
   exceptions first, and switch all service and route imports. Run focused
   primitive/meeting/profile/dictation/coder tests before touching specialized
   errors.
3. **Remove HTTP-shaped service errors.** Replace `WorkbenchServiceError` and
   `RecipeServiceError` raises with code/detail/context. Implement route-local
   translators and prove the old response shapes with route tests.
4. **Build support bottom-up.** Move pure source vocabulary, capability,
   rendering, graph, and context helpers; re-export grounding from its actual
   domain owner. Then move lifecycle/artifact persistence and skill injection,
   making database/default-model dependencies explicit.
5. **Switch consumers in one pass.** Update both services first, then route,
   conductor, and test imports. Delete the two obsolete owner modules only after
   `rg` shows no remaining consumer.
6. **Run the structural gate before broad tests.** Confirm services have no
   route import and support has no transport import. Then run targeted tests and
   the full suite. Read each output before claiming the story complete.

## Verification

Run these from the repository root after implementation. The first four are
structural acceptance checks and must produce no matches (exit 1 is expected for
those `rg` commands):

```bash
# No service may reach into the route layer.
rg -n --glob '*.py' '(^|[.])web\.routes|holdspeak\.web' holdspeak/services

# The former owners and HTTP-shaped exception classes are gone.
rg -n --glob '*.py' 'class (RecipeServiceError|WorkbenchServiceError)|status_code' \
  holdspeak/services
rg -n --glob '*.py' 'from .*primitive_service import .*\b(NotFound|ValidationError|ConflictError)\b' \
  holdspeak/services holdspeak/web
rg -n --glob '*.py' 'web\.routes\.(workflow_graph|primitives\.(ask|_shared))' \
  holdspeak/services

# Support is transport-neutral, and all intended public modules import alone.
rg -n --glob '*.py' 'fastapi|holdspeak\.web|\.\.web|WebContext|Request|JSONResponse' \
  holdspeak/services/support.py
uv run python -c 'from holdspeak.services.errors import ServiceError, NotFound, ValidationError, ConflictError; from holdspeak.services import support; assert NotFound("note", "n1").context == {"kind": "note", "id": "n1"}; assert ValidationError("bad").code == "validation_error"'
uv run python -c 'import holdspeak.services.primitive_service; import holdspeak.services.recipe_service; import holdspeak.services.workbench_service'

# Focused behavior, then the required suite.
uv run pytest -q tests/unit/test_workflow_graph.py tests/unit/test_blueprint_graph_conformance.py tests/unit/test_doctor_runtime_profiles.py tests/unit/test_mesh_relay_provider.py tests/unit/test_web_routes_recipe_chat.py tests/unit/test_workbench_triage.py tests/unit/test_workbench_triage_kernel.py
uv run pytest -q
```

If a structural grep finds an import in a service, move the dependency down to
`services.support` or inject it as an explicit service argument. Do not silence
the check with a local lazy import: the current inversion is predominantly lazy
imports, and they are still imports.

## Acceptance criteria

- [ ] `holdspeak/services/errors.py` owns `ServiceError`, `NotFound`,
      `ValidationError`, and `ConflictError`; all expose the required domain
      fields, while existing `kind`, `id`, and `existing_name` adapter use
      remains valid.
- [ ] No service exception has `status_code` or a route response `payload`.
      `WorkbenchServiceError` and `RecipeServiceError` no longer exist.
- [ ] Every former specialized failure has a stable code, and the recipes and
      workbenches HTTP adapters map it to the exact prior status/body. Target
      unavailable is 409; empty output is 502.
- [ ] `holdspeak/services/support.py` owns every helper named in the extraction
      table, including the necessary `RunLifecycle`, graph collaborators, and
      skill-injection collaborators. It has no FastAPI or route dependency.
- [ ] `PrimitiveService`, `RecipeService`, and every other module under
      `holdspeak/services/` pass the no-route-import grep. Lazy imports count
      as imports and are not exempt.
- [ ] Artifact persistence and skill injection receive database state
      explicitly; egress receives a neutral default model explicitly. No moved
      helper reaches back into a route module or a route-global database.
- [ ] `workflow_graph.py` and `skill_injection.py` are deleted only after all
      consumers move, and no compatibility wrapper preserves the old owner.
- [ ] The focused tests and `uv run pytest -q` pass, with the structural greps
      and direct import smoke tests recorded as story evidence.

## Files in scope

- New: `holdspeak/services/errors.py`
- New: `holdspeak/services/support.py`
- Delete: `holdspeak/skill_injection.py`
- Delete: `holdspeak/web/routes/workflow_graph.py`
- `holdspeak/services/primitive_service.py`
- `holdspeak/services/workbench_service.py`
- `holdspeak/services/recipe_service.py`
- `holdspeak/services/meeting_service.py`
- `holdspeak/services/dictation_service.py`
- `holdspeak/services/coder_service.py`
- `holdspeak/services/profile_service.py`
- `holdspeak/web/routes/primitives/_shared.py`
- `holdspeak/web/routes/primitives/{__init__,ask,chains,decisions,recipes,workbenches,workflows}.py`
- `holdspeak/web/routes/delivery_prs.py`
- `holdspeak/workbench_conductor.py`
- Route modules that import common errors, named in the file-by-file list
- Affected unit/route/service tests named above
