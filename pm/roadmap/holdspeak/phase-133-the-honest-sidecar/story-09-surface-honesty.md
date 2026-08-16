# HS-133-09 — Surface honesty

- **Project:** holdspeak
- **Phase:** 133
- **Status:** backlog
- **Depends on:** HS-133-01
- **Unblocks:** HS-133-11
- **Owner:** unassigned

## Problem

Three honesty debts in the existing surface: unbounded list resources
(resources.py:316-338 — a large desk returns unbounded JSON), a kind gap
no client can see (the schema resource advertises 17 primitive kinds,
resources.py:31-49; the `desk.*` CRUD tools accept 6, tools.py:23), and
the one `domain.verb` naming-law violation (`pipeline_events_query`,
tools.py:301).

## Scope

### In

Per assets/surface-spec.md §2.3-2.5, verbatim:

- Pagination ruling applied: `list_workbenches`/`list_recipes`/
  `list_profiles` resource reads truncate to `[:100]` at the resource
  layer; `holdspeak://dictation/journal` passes `limit=100`;
  `pipeline://events/recent`, the board, and the snapshot stay as-is
  (bounded by design).
- The kind-gap sentences appended to the five `desk.*` CRUD tool
  descriptions, exactly as the spec words them (§2.4).
- `pipeline_events_query` → `pipeline.events`: tools.py:301,554 and all
  four references in `tests/unit/test_124_verify_round3.py`
  (:41,47,52,60) INCLUDING the two test function names (spec test-law
  item 6). No compat shim — pre-release standing rule.

### Out

- Service-layer `limit` parameters (the truncation is a resource-layer
  convenience, per the spec's ruling). Any other rename. Observer
  changes.

## Acceptance criteria

- [ ] A resource read over a >100-row table returns exactly 100 entries
  (test seeds 101 profiles or workbenches).
- [ ] All five `desk.*` descriptions carry the kind-boundary sentence;
  the catalogue test can assert the substring.
- [ ] `grep -rn pipeline_events_query` across the repo returns nothing;
  `pipeline.events` dispatches identically; renamed tests green.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_phase133.py tests/unit/test_mcp_tools.py tests/unit/test_124_verify_round3.py --tb=short`
