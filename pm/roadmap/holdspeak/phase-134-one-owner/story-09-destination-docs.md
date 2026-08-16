# HS-134-09 — The docs speak destination

- **Project:** holdspeak
- **Phase:** 134
- **Status:** backlog
- **Depends on:** HS-134-03
- **Unblocks:** HS-134-10
- **Owner:** unassigned

## Problem

After the rename, the entry-point docs lie: `docs/MCP_SIDECAR.md`
documents the `profile.*` family and `holdspeak://profiles` resources
(shipped in Phase 133); the README's sidecar section links it. House
rule: docs stories touch ENTRY points.

## Scope

### In

- `docs/MCP_SIDECAR.md`: the destination family, renamed resources,
  and a one-line note that placement answers carry
  `{effective_target_id, source}` (HS-134-04).
- README: any profile-vocabulary in the public surface swept to
  destination.
- Doc drift guards (the 19-test suite HS-133-10 used) green.

### Out

- Marketing/positioning rewrites; web UI copy (separate surfaces own
  their labels — swept only where the renamed API forces it).

## Acceptance criteria

- [ ] `grep -n "profile\." docs/MCP_SIDECAR.md` shows no stale tool
  names; resources section matches the live catalogue.
- [ ] Doc drift guard tests green.

## Test plan

- The docs drift-guard suite (as in evidence-story-10 of Phase 133) +
  link check.
