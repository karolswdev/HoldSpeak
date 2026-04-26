# HS-2-11 — Step 10: Full regression gate + DoD

- **Project:** holdspeak
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HS-2-02..HS-2-10 (whichever ship)
- **Unblocks:** phase exit
- **Owner:** unassigned

## Problem

Spec §9.11 + §11 — final phase-exit sweep: run the full requirement
matrix from spec §7.2, generate the evidence bundle per §8.2 at
`docs/evidence/phase-mir-01/<YYYYMMDD-HHMM>/`, write the phase
summary with known gaps + deferred work, confirm web UI surfaces the
controls end-to-end, and flip phase status to `done`. Mirrors HS-1-11
in DIR-01.

## Scope

- **In:** Per `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` §9.11 + §11.
- **Out:** Any new feature work (would be a separate story).

## Acceptance criteria

- [ ] _TBD when story is picked up; cross-check spec §11 DoD list._

## Test plan

- _TBD when story is picked up; expect `uv run pytest -q tests/` clean (modulo documented pre-existing hardware-only Whisper-loader failure carried since HS-1-03)._

## Notes / open questions

- Pre-existing `tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads` failure is the documented baseline; phase exit doesn't have to fix it.
