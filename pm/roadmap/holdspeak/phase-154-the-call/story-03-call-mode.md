# HS-154-03 - Call mode: the persisted state and the one visible chip (M9)

- **Project:** holdspeak
- **Phase:** 154
- **Status:** done
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

## What shipped

### Files

- `holdspeak/db/schema.py` -- additive `call_mode INTEGER NOT NULL DEFAULT 0` on the `threads` table; SCHEMA_VERSION 65->66 (informational).
- `holdspeak/db/threads.py` -- `Thread` dataclass gains `call_mode: int`; `_row_to_thread` reads it with a fallback for pre-change DBs; `ThreadRepository.patch` accepts `call_mode: Optional[int]`.
- `holdspeak/services/thread_service.py` -- `ThreadService.patch` validates call_mode (0/1, 400 otherwise); emits `thread_call_state` frame on ON/OFF transitions; `_thread_dict` returns `call_mode` in the GET response; `start_turn` emits THINKING at turn start and LISTENING at turn done on call_mode=1 threads.
- `holdspeak/kernel/inference_stream.py` -- `emit_thread_call_state` broadcast helper (thread_id, state).
- `holdspeak/realtime_frames.py` -- `thread_call_state` registered in `RUNTIME_FRAME_TYPES`.
- `holdspeak/web/routes/threads.py` -- PATCH route reads `call_mode` from body, passes to `ThreadService.patch`.
- `web/src/runtime/frames.ts` -- `thread_call_state` mirrored in the web frame vocabulary.
- `web/src/desk/threads.ts` -- `ThreadWire.call_mode: number`; `getThread` parses it; `patchThread` accepts it; `ThreadCallStatePayload` interface exported.
- `web/src/desk/components/CallChip.tsx` -- the ONE call-mode chip: OFF / LISTENING / THINKING / SPEAKING. Click toggles via `patchThread`; ONE click in any non-OFF state stops TTS + loop + patches call_mode=0. Keyboard reachable (tabIndex=0, Enter/Space). Desk tokens, no modal, no prose.
- `web/src/desk/pullouts/ThreadPullout.tsx` -- CallChip placed in the thread head beside the mode badge; subscribes to `thread_call_state` frame for live reload.
- `web/src/desk/pullouts/thread-pullout.css` -- `.thread-call-chip` + state variants (`--off`, `--listening`, `--thinking`, `--speaking`) with desk tokens.
- `tests/unit/test_thread_call_mode.py` -- 11 tests: reconcile (pre-change DB gains call_mode default 0, rows intact, idempotent), PATCH toggle + validate (400 on non-0/1), GET returns it, frame fires on transitions, no frame on same-value patch, real-coordinator turn emits THINKING then LISTENING, call_mode=0 turn emits no frames.
- `web/src/desk/components/__tests__/callChip.test.tsx` -- 11 vitest tests: all four visual states, click in each non-OFF state stops (tts.stop + loop.stop + PATCH 0), click OFF starts (PATCH 1), keyboard Enter/Space, hydration starts loop.
- `tests/e2e/test_hs154_call_glass.py` -- extended with `test_call_chip_glass`: chip visible in head at 1440+393, OFF by default, PATCH 1 persists on reload, click stops, zero overflow. Screenshots to story-03-shots/.

### Tests

- pytest `test_thread_call_mode.py`: 11 passed -- reconcile (3), PATCH toggle (6), real-coordinator THINKING/LISTENING transitions (2).
- pytest `test_thread_service.py`: 21 passed (unchanged).
- pytest `test_realtime_frame_registry.py`: 11 passed (thread_call_state properly registered, mirror matches, no orphans).
- pytest `test_api_surface.py`: 5 passed (fence validates -- no new routes added, only PATCH body changed).
- vitest `callChip.test.tsx`: 11 passed -- four states, stop in each, start, keyboard, hydration.
- vitest `callLoopWiring.test.ts`: 5 passed (unchanged).
- vitest `ThreadPullout.test.tsx`: 10 passed (unchanged).
- pytest `test_hs154_call_glass.py`: 4 passed (2 story-01 + 1 story-02 + 1 story-03 call-chip glass leg).
- Web baseline: zero BRANCH-NEW (1619 passed, 0 failed).

### Seams

- Schema: `threads.call_mode` is additive; the generic reconcile carries it to existing DBs (proven against the pre-change DDL).
- Server: `ThreadService.patch(call_mode=)` is the ONE mutation point. Validation (0/1) and frame emission happen here. `start_turn` / turn-done emit THINKING / LISTENING for call_mode=1 threads.
- Frame: `thread_call_state` is registered in both `realtime_frames.py` and `web/src/runtime/frames.ts`; emitted via `emit_thread_call_state` in inference_stream.py; consumed by `subscribe("thread_call_state")` in ThreadPullout.
- Client: `CallChip` derives THINKING from `isStreaming` prop, SPEAKING from `tts.onStateChange`; only ON/OFF persists to the server. `wireCallLoop` from story 02 starts/stops the mic session.

### Defects found

- None during implementation. The `_row_to_thread` fallback pattern (`if "call_mode" in row.keys() else 0`) matches the existing `draft` column pattern at threads.py:145 and prevents crashes when reading from a pre-reconcile DB connection.

### Evidence

- `pm/roadmap/holdspeak/phase-154-the-call/evidence-story-03.md` -- captured run: 48 passed (test_thread_call_mode.py 11 + test_thread_service.py 21 + test_realtime_frame_registry.py 11 + test_api_surface.py 5).
