# Evidence - HS-119-02

- **Story:** HS-119-02 - Integration regression sweep
- **Status:** done
- **Date:** 2026-08-05

## Regression checklist results

### 1. WebSocket connection — PASS
Auth handshake, event subscription, reconnection with exponential
backoff, ping/pong — all intact. No Phase 118 code touched the WS
endpoint (`web/routes/system/ws.py`), `WebSocketManager`, or
`RuntimeBus.tsx`. The "RECONNECTING" presence display is honest
reconnection behavior when the server is down, not a bug.

### 2. Presence detection — PASS
Presence page reads from RuntimeBus state (untouched by Phase 118).
`LampGadget` correctly shows warn/ok based on connection state.

### 3. Meeting recorder — PASS
Meeting capture durability, sync routes, meeting-related unit tests
all pass (15/15). Integration failures are Slack export (needs webhook)
and UAT on .43 (needs Intel box) — environment-dependent.

### 4. Dictation hotkey — REGRESSION FOUND, FIXED
`_maybe_run_dictation_pipeline` was refactored in HS-118-08 to call
`process_transcript` instead of `run_dictation_pipeline`, but
`test_web_runtime_method_delegates` still patched the old function.
**Fix:** updated test to patch `process_transcript` with matching
async signature. All dictation_runner unit tests pass (9/9).

### 5. Workbench conductor — PASS
Conductor ref hydration, workbench triage derivation (38 tests), audio
floor contention — all pass. The auto-mint path and triage lifecycle
work. The `WorkbenchTriageCodec` was not registered (see item 6) but
the conductor's mint path is unaffected.

### 6. Kernel operations — REGRESSION FOUND, FIXED
**WorkbenchTriageCodec not registered:** The codec file existed
(`kernel/workbench_triage.py`) but was never imported or instantiated
in `runtime.py`. Any triage operation would fail at broker lookup.
**Fix:** added import + instantiation + OperationSpec registration.
Added 6 regression tests in `test_workbench_triage_kernel.py`.

**Effect fence drift:** Two subprocess calls in `repositories.py:56`
and `roadmaps.py:46` were UNLEDGERED in the effect census.
**Fix:** added to `_MIGRATED_CALLS` as authenticated owner reads.

### 7. Seed and schema — REGRESSION FOUND, FIXED
**UAT seed route stale:** The UAT seed framework mapped profiles to
`/api/profiles` which returns HTTP 405 (read-only since HS-112-01).
**Fix:** mapped to `/api/inference-targets`. The main product seed
(`db/seed.py`) uses repository-level calls and is unaffected.

**Canon guard test stale after decomposition:** HS-117-08 decomposed
`DictationCore.tsx` into `dictation/` sub-files. The sentinel
`RUNS ON LIVES IN MODELS` moved to `DictationSections.tsx` but the
test still read only the parent file.
**Fix:** test now reads the full `dictation/` sub-tree.

Schema version (v37) and migration path are intact.

### 8. Inlet and @-references — PASS
Voice resolver (38/38 pass), frontend tests (713/713 pass) including
WorkbenchTriage, InletAutocomplete, drawerResolver tests. @-reference
and voice drawer resolution intact.

## Files changed

| File | What |
|------|------|
| `holdspeak/kernel/runtime.py` | Register WorkbenchTriageCodec |
| `tests/unit/test_workbench_triage_kernel.py` | 6 regression tests (NEW) |
| `tests/unit/test_kernel_effect_fence.py` | Add 2 unledgered subprocess sites |
| `tests/unit/test_dictation_runner.py` | Patch process_transcript, not run_dictation_pipeline |
| `tests/unit/test_interior_canon_guard.py` | Read decomposed dictation/ sub-tree |
| `uat/conductor/induction/seeds.py` | Map profiles to /api/inference-targets |

## Proof

### Captured run — 2026-08-06T02:44:50Z

- **Command:** `uv run pytest -q tests/unit/test_workbench_triage_kernel.py tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current tests/unit/test_dictation_runner.py tests/unit/test_interior_canon_guard.py::test_dictation_core_speech_settings_never_regresses --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f9ecfe73fd6db1be275fce556872cef2511be5b8

```text
.................                                                        [100%]
17 passed in 1.51s
```
