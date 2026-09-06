# HS-190-11 — Bounded shadow adoption: Ask, Thread, Recipe, Coder

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-190-03, HS-190-04, HS-190-05, HS-190-07, HS-190-08, HS-190-10
- **Unblocks:** HS-190-13, HS-190-14
- **Owner:** unassigned

## Problem

Contracts that never touch real consumers can be internally elegant and still
fail at the ecosystem seam. CF-0 needs representative end-to-end integrations
without changing a single model input or overstating universal adoption.

## Scope

- **In:** adapters at Ask, Thread, Recipe, and Coder admission boundaries;
  frozen capability/operation/destination/scope mapping; construction and
  validation of `purpose=shadow` plans; sanitized comparison receipts; feature
  flags; explicit deprecation seam for relationship-aware `include_memory`;
  compatibility characterization for Workflow, Workbench, HTTP, and MCP.
- **Out:** plan injection, prompt changes, ranking-quality comparison, enabling
  any adapter by default, or universal rollout.

## Acceptance criteria

- [ ] Each representative adapter maps its real invocation to a registered
  capability/operation, actor, destination, assignment/route, scope, and budget
  without synthesizing missing authority.
- [ ] The same transaction/release diff that installs all four adapters changes
  their generated runtime-adoption state from `planned_shadow` to `shadow`;
  partial adapter/state rollout fails the census and cannot merge.
- [ ] With the CF-0 shadow flag on, it constructs one deterministic plan and
  receipt; the bytes passed to the existing inference path remain byte-equal to
  the flag-off path.
- [ ] With flags off, Ask, Thread, Recipe, Workflow, Workbench, Coder, HTTP, and
  MCP behavior and result contracts remain unchanged.
- [ ] Private, stale, barred, wrong-scope, unknown-capability, and cloud-denied
  inputs fail closed inside shadow planning without blocking the legacy call;
  only sanitized status is recorded.
- [ ] Existing relationship-aware memory remains authoritative until a later
  migration story; the seam is documented and no dual injection can occur.
- [ ] Static/runtime fences fail if CF-0 plan content reaches a model request.

## Test plan

- **Golden:** one fixed fixture per Ask, Thread, Recipe, and Coder adapter,
  proving common ref/revision rendering and capability-specific plan fields.
- **Differential:** exact legacy request/result comparison with flags off/on.
- **Fault/privacy:** unavailable planner, stale revision, removed lineage,
  denied fallback, duplicate request, timeout; receipt leakage scan.
- **Regression:** focused relationship-aware suite plus named consumer, HTTP,
  and MCP contracts.

## Notes / open questions

- CF-0 story map 09, INV-010/011, and §16 are normative.
- “Shadow” means the plan is built and validated but has zero authority to
  affect context, model route, tool permissions, result, or owner-visible copy.
