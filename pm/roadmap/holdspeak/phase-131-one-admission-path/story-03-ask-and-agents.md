# HS-131-03 — Ask and Agents take the same door

- **Project:** holdspeak
- **Phase:** 131
- **Status:** done
- **Depends on:** HS-131-01, HS-131-02
- **Unblocks:** HS-131-04, HS-131-05
- **Owner:** unassigned

## Problem

Recipe run is the best existing inference lifecycle, but Recipe chat bypasses it,
and Ask has no invocation record at all. Ask also lacks a saved definition and
revision, which makes blindly reusing the current recipe codec dishonest. These
single-call paths must establish the runner's first real product contract before
fan-out callers migrate.

## Scope

### In

- Route `AskService.ask` in `holdspeak/services/ask_service.py:63-120` through
  the HS-131-02 runner using a versioned Ask service-contract origin and the
  immutable request payload hash.
- Route Recipe run and Recipe chat in
  `holdspeak/services/recipe_service.py:66-299` through the same runner. A saved
  Agent uses its real definition reference and persisted revision.
- Keep Phase 130 placement behavior unchanged: target ID selects placement,
  model names cannot retarget, and execution consumes the admitted deployment
  revision.
- Preserve native Ask/Agent records as projections that reference the kernel
  invocation and terminal receipt. They may not perform their own model
  execution or invent a second lifecycle.
- Propagate authenticated principal, cancellation, typed refusal, egress facts,
  and domain result references through the existing service and route
  boundaries.
- Render new synchronous admission/claim refusals through the existing in-flow
  error contract; do not add a modal or overlapping banner.
- *Added 2026-08-09 (HS-131-02 amendment; Sol counsel; owner may overrule at
  the sitting):* establish the **shared projection-staging primitive** — one
  durable protocol closing the crash window between a caller's domain write
  and the runner's terminal receipt — before Ask/Recipe become the first
  production migrations. It becomes the required publication path for every
  later domain migration story (HS-131-04 through HS-131-09). Crash-recovery
  tests are mandatory: stage-before-terminal, crash-after-stage-before-
  receipt, cancellation-after-stage, interrupted finalization, idempotent
  recovery without duplicate domain objects.

### Out

- Sequence, Workflow, or Workbench fan-out.
- Ask or Agent UI redesign.
- New placement controls or persistent writers.

## Acceptance criteria

- [ ] Ask, Recipe run, and Recipe chat each dispatch only through the one runner.
- [ ] Ask admissions cite a truthful versioned service contract and immutable
  request hash; no fake saved definition is created.
- [ ] Agent admissions cite the saved Agent definition and exact revision used.
- [ ] One successful call yields one admitted invocation and one terminal
  receipt referenced by the native domain result.
- [ ] Refusal, provider failure, cancellation, and indeterminate outcome appear
  once in the kernel and as the same typed outcome in the service response.
- [ ] Changing the target after admission cannot change execution or the receipt.
- [ ] A model mismatch remains a named refusal and cannot select another target.
- [ ] Admission or claim failure is visible in-flow on Ask and Agent chat and
  leaves no model output record.

## Test plan

- Unit: `uv run pytest -q tests/unit/test_web_routes_ask.py tests/unit/test_web_routes_recipe_chat.py tests/unit/test_inference_kernel.py` plus focused Recipe service tests.
- Integration: one real Ask and one real Agent call against the LAN target with
  operation/receipt queries; one cancellation and one target-mutation race.
- Web: focused Ask and Agent refusal-render tests; `npm --prefix web run test:web -- run` only if web code changes.
- Manual / device: Ask and Agent run from the Desk, inspect the same deployment
  identity and openable receipt.

## Notes / open questions

This story is a migration, not a new policy layer. The runner derives authority;
Ask and Recipe services retain their domain contracts and no longer own model
execution.
