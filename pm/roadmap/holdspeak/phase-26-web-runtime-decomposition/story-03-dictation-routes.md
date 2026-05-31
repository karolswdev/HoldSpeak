# HS-26-03 — Extract Dictation / Agent-Hook Routes

- **Project:** holdspeak
- **Phase:** 26
- **Status:** backlog
- **Depends on:** HS-26-01
- **Unblocks:** HS-26-07
- **Owner:** unassigned

## Problem

The dictation-pipeline config, blocks, project-context, agent-hook, and
intent-control routes (`/api/dictation/*`, `/api/intents/*`) are a self-contained
cluster ready to move behind the HS-26-01 seam.

## Scope

### In

- Move `/api/dictation/*` (config, blocks, agent-context, project KB) and
  `/api/intents/*` (profile/override/control) routes into `routes/dictation.py`.
- Read from the shared context; no behavior change.

### Out

- Other domains (HS-26-02, HS-26-04, HS-26-05).
- Callback removal beyond these routes (HS-26-06).

## Acceptance criteria

- [ ] Listed routes are served from the new module; none remain inline.
- [ ] Existing dictation/intent web tests pass unchanged.
- [ ] Route-inventory diff shows identical paths/methods for the moved set.

## Test plan

- Unit: `uv run pytest -q tests/ -k "web and (dictation or intent)"`.
- Integration: dictation config round-trip via the runtime.
- Manual: n/a.

## Notes / open questions

- Confirm whether intent-control routes belong with dictation or meetings; keep
  with dictation unless tests suggest otherwise.
