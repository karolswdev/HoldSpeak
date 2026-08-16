# HS-134-08 — The routing profile stands alone

- **Project:** holdspeak
- **Phase:** 134
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-134-10
- **Owner:** unassigned

## Problem

Phase 130 converged `mir_profile`/`plugin_profile` into
`routing_profile` at the accessor (`effective_routing_profile`,
`holdspeak/config/meeting.py:269-289`) but the legacy pair survives in
the schema (:77, :90), validation (:171-179), the one-time migration
(`config/core.py:177-206, :298`), and runtime instance vars
(`web_runtime.py:183` `self.mir_profile`, `runtime/activity.py:106`,
`runtime/routing_glue.py:45,323`). Pre-release: delete, don't deprecate.

## Scope

### In

- Delete both legacy fields from `MeetingConfig`, their validation,
  and their `__post_init__` participation; `effective_routing_profile`
  reads one field.
- The migration shrinks to a tolerant-load guard (unknown legacy keys
  in existing config files are dropped silently on load — owner's real
  config must not error).
- Runtime rename: `self.mir_profile` → `self.routing_profile`
  propagated to activity payloads and routing glue;
  `intel_queue.py:149,308` call sites verified.

### Out

- Any behavior change to routing itself; profile *values* semantics.

## Acceptance criteria

- [ ] `grep -rn "mir_profile\|plugin_profile" holdspeak/ web/src/ tests/`
  → zero hits outside historical roadmap docs.
- [ ] A config file containing the legacy keys loads clean (test).
- [ ] Focused guards green: `test_intel_profile_resolution.py`,
  `test_one_dial.py`.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_intel_profile_resolution.py tests/unit/test_one_dial.py --tb=short`
  + the legacy-key-load test.
