# HS-133-05 — Cadence over the wire

- **Project:** holdspeak
- **Phase:** 133
- **Status:** done
- **Depends on:** HS-133-01
- **Unblocks:** HS-133-11
- **Owner:** unassigned

## Problem

The cadence engine has no programmable surface. `CadenceService` carries
a full read + safe-write API and an admitted model path
(`get_loop` :177 → `_draft_child` :254 → `InferenceRunner.invoke` via
`_as_principal` :272-276), all web-only today.

## Scope

### In

Per assets/surface-spec.md §1D, verbatim (counsel-amended revision):
`holdspeak/mcp/families/cadence.py` implementing the eleven tools —
`cadence.status`, `cadence.loops`, `cadence.get_loop` (R/W conditional,
description names the MAY-INVOKE-MODEL behavior), `cadence.brief`,
`cadence.closeout`, `cadence.history`, `cadence.audit`,
`cadence.snooze`, `cadence.set_status`, `cadence.run_now`,
`cadence.apply_closeout` — with the spec's schemas and anchors.
Constructor per spec: `config=Config.load().cadence`, `kernel=None`
(lazy broker at :220). Plus the phase's one new resource:
`holdspeak://cadence/status` registered in `resources.py`, following the
existing static-resource pattern (unobserved, per spec Invariant 4).

### Out

- `cadence.reply` (counsel Q2 — requires tmux delivery; absence named in
  the `cadence.set_status` description). Any CadenceService change. Any
  change to the resource observer pattern.

## Acceptance criteria

- [ ] All eleven tools in the catalogue with closed schemas, dispatching
  to the anchored methods; `cadence.get_loop` is async-wrapped via
  `_run()` and its test monkeypatches the service.
- [ ] `holdspeak://cadence/status` answers `resources/read` through
  `handle_message` with a test (spec test-law item 5).
- [ ] `cadence.set_status` rejects a status outside the enum;
  `cadence.snooze` on an unknown loop returns `isError: true`.
- [ ] REQUIRED_TOOLS extended with the eleven names.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_phase133.py tests/unit/test_mcp_tools.py --tb=short`
