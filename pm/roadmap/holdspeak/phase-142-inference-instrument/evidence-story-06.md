# Evidence - HSEGHS001HS104-142-06

- **Story:** HSEGHS001HS104-142-06 - Task-First Model Picker
- **Status:** done
- **Date:** 2026-08-21

## Proof

# Evidence — HSEGHS001HS104-142-06

## Outcome

Replaced the three-step model setup wizard with one compact task-first master/detail picker. The first useful viewport now contains source filters, model rows, selected truth, and the sole action. Full names wrap; setup issues and per-job routing are disclosed.

## Verification

- Focused Vitest: 2 files, 32 tests passed.
- Production Vite build passed.
- Isolated-HOME Playwright glass: 1440×900 and 393×900, 2 tests passed.
- `git diff --check` passed.

## Visual evidence

- `/tmp/holdspeak-inference-setup-1440.png`
- `/tmp/holdspeak-inference-setup-393.png`
- `/tmp/holdspeak-inference-setup-hammer-1440.png`
- `/tmp/holdspeak-inference-setup-hammer-393.png`
