# Evidence - HS-139-03

- **Story:** HS-139-03 - Config goes home
- **Status:** done
- **Date:** 2026-08-17

## Proof

### Captured run — 2026-08-18T02:03:11Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -x tests/ -k "settings" -q 2>&1 && cd web && npx vitest run src/pages/cores/__tests__/settingsModels.test.tsx src/pages/cores/history/__tests__/meetingsConfig.test.tsx --reporter=verbose 2>&1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 53dd9a4eb1c7d91d7a251d308da3d746180a6047

```text
........................................................................ [ 56%]
........................................................                 [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_workbench_walk.py:46: no hub listening at http://localhost:8778
128 passed, 3 skipped, 5942 deselected in 36.38s

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web

 ✓ src/pages/cores/history/__tests__/meetingsConfig.test.tsx > MeetingsConfig (HS-139-03) > renders capture + export controls from /api/settings 25ms
 ✓ src/pages/cores/history/__tests__/meetingsConfig.test.tsx > MeetingsConfig (HS-139-03) > does NOT render intel or companion controls (those moved elsewhere) 7ms
 ✓ src/pages/cores/history/__tests__/meetingsConfig.test.tsx > MeetingsConfig (HS-139-03) > fetches settings on mount 5ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > lists the profile-backed targets with key + readiness lamps 50ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > offers HUB DEFAULT plus every target on all three RUNS ON rows 24ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > writes a pointer pick through the settings updater with the one sentinel 24ms
stderr | src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > edits a target through the one write path (/api/inference-targets)
An update to ModelsModule inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://react.dev/link/wrap-tests-with-act
An update to ModelsModule inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://react.dev/link/wrap-tests-with-act

stderr | src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > edits a target through the one write path (/api/inference-targets)
An update to ModelsModule inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://react.dev/link/wrap-tests-with-act

 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > tests each destination and offers its discovered models 135ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > edits a target through the one write path (/api/inference-targets) 69ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > renders the meetings placement rule where the placement is set 18ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > ModelsModule (HS-112-01) > never touches a legacy endpoint field 15ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > names the local placement and leaves the provider fallback live 20ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > names the cloud placement 18ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > disables the provider fallback and names the override when a destination is adopted 18ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > names a dropped destination pointer and keeps the provider live 16ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > names a placement that cannot run 18ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > marks exactly one row as the deciding control, in every state 31ms
 ✓ src/pages/cores/__tests__/settingsModels.test.tsx > meetings placement dial (HS-132-10) > writes the provider fallback through the settings updater 16ms

 Test Files  2 passed (2)
      Tests  17 passed (17)
   Start at  20:03:49
   Duration  1.24s (transform 334ms, setup 136ms, import 569ms, tests 511ms, environment 591ms)
```
