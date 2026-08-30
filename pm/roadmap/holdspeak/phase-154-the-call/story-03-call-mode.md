# HS-154-03 - Call mode: the persisted state and the one visible chip (M9)

- **Project:** holdspeak
- **Phase:** 154
- **Status:** backlog
- **Depends on:** HS-154-01, HS-154-02
- **Unblocks:** HS-154-04, HS-154-05
- **Owner:** unassigned

## Problem

A call the owner cannot see or stop is a bug. One visible state on the
thread head — OFF / LISTENING / THINKING / SPEAKING — persisted so a
refresh keeps the call ON (counsel M9; settled design D3).

## Scope

- **In:** additive `threads.call_mode INTEGER NOT NULL DEFAULT 0`
  (schema + the generic reconcile; prove against the pre-change DDL —
  the 153 pattern). PATCH `{call_mode}` on the thread route;
  `thread_call_state` frame (frames module + web mirror + registry
  fence test). The head chip: OFF→LISTENING→THINKING→SPEAKING→LISTENING
  driven by the loop (02), turn streaming, and TTS (01); ONE click
  stops everything (TTS stop, mic closed, call_mode=0). Never a
  default: new threads are OFF. Reload with call_mode=1 resumes
  LISTENING. The egress badge stays per turn, untouched.
- **Out:** auto-speak (04).

## Acceptance criteria

- [ ] Reconcile: a pre-change-DDL DB gains `call_mode` default 0, rows intact.
- [ ] PATCH toggles and GET returns it; the frame fires on every state change (unit; real coordinator where a turn drives THINKING).
- [ ] vitest: the chip renders all four states; click in any state → OFF, mic closed, TTS stopped.
- [ ] Glass 1440 + 393: the chip in the thread head in all states (stub the loop), zero overflow; reload keeps ON.

## Test plan

- **Unit:** `tests/unit/test_thread_call_mode.py`; vitest `callChip.test.tsx`.
- **Integration:** glass leg `call-chip`.
- **Manual / device:** story 05.

## Notes / open questions

- THINKING is derived (a turn is streaming), not stored; only ON/OFF persists.
