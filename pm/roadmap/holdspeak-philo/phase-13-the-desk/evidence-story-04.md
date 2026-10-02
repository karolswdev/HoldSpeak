# Evidence - PHILO-13-04

- **Story:** PHILO-13-04 - A3 — Faces that do not lie
- **Status:** done
- **Date:** 2026-10-02

## Proof

### Captured run — 2026-10-02T20:07:04Z

- **Command:** `bash -c set -eo pipefail; H=$(mktemp -d); trap "rm -rf \"$H\"" EXIT INT TERM; cd web; npx vitest run src/desk/__tests__/philo13FacesDoNotLie.test.tsx src/desk/store/__tests__/recordingSlice.test.ts src/pages/cores/__tests__/settingsSummaryName202.test.tsx src/desk/components/MicButton.test.tsx src/features/project-room/update/__tests__/retryKeepsNewerWords.test.tsx src/pages/cores/history 2>&1 | tail -4; npx tsc --noEmit -p .; echo TYPECHECK-OK; cd ..; HOME=$H HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_philo13_04_faces_glass.py tests/unit/test_philo13_a3h_meeting_summary.py tests/unit/test_philo13_muaddib_atlas.py tests/unit/test_product_copy.py --basetemp=$H/bt -p no:cacheprovider 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9b185e77766807d6ba2c005789a3097861431cf7

```text
      Tests  94 passed (94)
   Start at  14:07:04
   Duration  2.09s (transform 3.60s, setup 1.55s, import 7.44s, tests 2.59s, environment 6.06s)

TYPECHECK-OK
....................................................                     [100%]
52 passed in 127.53s (0:02:07)
```
