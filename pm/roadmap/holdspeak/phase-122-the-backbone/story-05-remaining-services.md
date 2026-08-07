# HS-122-05 — Remaining services

- **Project:** holdspeak
- **Phase:** 122
- **Status:** done
- **Depends on:** HS-122-01 (primitive service — shared patterns)
- **Unblocks:** HS-122-06 (thin routes audit)
- **Owner:** unassigned

## The thesis (the bar)

Every operation in the system must flow through the service pipeline.
Stories 01-04 extracted the high-value services. This story wraps the
remaining domain areas so no route handler calls repositories directly.

## Scope

### DictationService
- `list_journal(principal, limit?, cursor?)`
- `get_entry(principal, id)`
- `export_journal(principal, format)`
- `clear_journal(principal)`
- `submit_dictation(principal, text, aim?, source?)`

### CoderService
- `list_sessions(principal)`
- `get_session(principal, session_id)`
- `select_session(principal, session_id)`
- `reply(principal, session_id, text)`

### ProfileService
- `list_profiles(principal)`
- `get_profile(principal, id)`
- `create_profile(principal, fields)`
- `update_profile(principal, id, patch)`
- `delete_profile(principal, id)`
- `list_inference_targets(principal)`

### DeskService
- `seed(principal)`
- `reset(principal)`
- `snapshot(principal) → DeskSnapshot` (aggregated desk state)
- `health() → HealthStatus` (no principal needed)

### KernelService
Already exists as `Broker` with `read/submit/decide/events`. This
story verifies it conforms to the service contract and adds any
missing convenience wrappers.

## Acceptance criteria

- [ ] All five service classes exist.
- [ ] Every route handler that was still calling `get_database()`
      now delegates to a service.
- [ ] Services are importable without FastAPI.
- [ ] Tests pass.

## Files in scope

- New: `holdspeak/services/dictation_service.py`
- New: `holdspeak/services/coder_service.py`
- New: `holdspeak/services/profile_service.py`
- New: `holdspeak/services/desk_service.py`
- Various route modules under `holdspeak/web/routes/`
- `holdspeak/kernel/broker.py` (verify contract)
