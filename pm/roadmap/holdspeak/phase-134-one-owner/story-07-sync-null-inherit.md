# HS-134-07 — Sync understands inherit

- **Project:** holdspeak
- **Phase:** 134
- **Status:** backlog
- **Depends on:** HS-134-01
- **Unblocks:** HS-134-10
- **Owner:** unassigned

## Problem

Under the settled design, a null placement on a workbench means
"inherit from the agent tier" — but the sync merge map
(`holdspeak/services/sync_service.py:75`) has no notion of it, and a
receiving device could read null as "unset → this_machine". Bounded
delegation revocation (:596-621) is keyed to `profile_id`/`recipe_id`
changes and must keep firing (audit risk 3). Field RENAMES are out
(no `capability_ref` this wave) — this story is semantics, not
vocabulary.

## Scope

### In

- The merge map distinguishes "null (inheriting)" from "absent from
  payload" for `profile_id`/`resolver_profile_id`; a pushed null lands
  as null and the receiving side resolves inheritance at execution
  (never materializing this_machine into the stored field).
- Verify + test that bounded-delegation revocation fires on placement
  changes including null↔value transitions.
- A sync round-trip test: workbench with `profile_id: null` pushed and
  pulled across two DBs inherits identically on both.

### Out

- Field renames; sync protocol/version changes; iPad client work
  (dormant track).

## Acceptance criteria

- [ ] Round-trip test proves null survives and inherits; no path
  materializes a default into the stored field.
- [ ] Revocation test covers null↔value placement transitions.
- [ ] `tests/unit/test_primitive_contract.py` sync-registry guard
  green.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_primitive_contract.py -k sync --tb=short`
  plus the new round-trip + revocation tests (file named in report).
