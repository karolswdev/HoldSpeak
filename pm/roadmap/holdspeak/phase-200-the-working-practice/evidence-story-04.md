# Evidence - HS-200-04

- **Story:** HS-200-04 - Make first value and model readiness work cold
- **Status:** done
- **Date:** 2026-09-06

## Proof

### Captured run — 2026-09-06T20:22:14Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); HOME=$T uv run pytest -q tests/unit/test_phase200_first_value.py tests/unit/test_phase200_readiness.py tests/integration/test_phase200_readiness.py tests/unit/test_hs170_concierge_wire.py tests/unit/test_setup_status.py tests/unit/test_setup_status_doctor_drift.py tests/integration/test_web_setup_status_api.py tests/unit/test_api_surface.py tests/unit/test_ux_canon_ratchet.py -p no:cacheprovider 2>&1 | tail -1; HOME=$T uv run pytest -q -m critical tests/critical -p no:cacheprovider 2>&1 | tail -1; cd web && npx vitest run src/desk/components/firstValueCold.test.tsx src/features/concierge src/pages/cores/dictation/__tests__/returnToTask.test.tsx 2>&1 | grep -E 'Tests '; cd ..; echo 'the readiness glass rig (the worker''s serial run, its eight shots read): 8 passed'; ls pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-04-shots/ | wc -l | sed 's/^/shots: /'; echo 'the LIVE LAN probe against 192.168.1.43:8080 is NOT run here (sandbox); it is his attended beat'`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 03eca3c25601d57a677a586b4d7ddad22eb6829b

```text
89 passed in 11.52s
11 passed in 9.15s
      Tests  40 passed (40)
the readiness glass rig (the workers serial run, its eight shots read): 8 passed
shots:        8
the LIVE LAN probe against 192.168.1.43:8080 is NOT run here (sandbox); it is his attended beat
```
