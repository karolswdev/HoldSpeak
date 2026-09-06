# Evidence - HS-200-02

- **Story:** HS-200-02 - Expose loaded runtime identity and prove restore
- **Status:** done
- **Date:** 2026-09-06

## Proof

### Captured run — 2026-09-06T18:28:49Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); HOME=$T uv run pytest -q tests/unit/test_phase200_runtime_identity.py tests/integration/test_phase200_runtime_identity.py tests/unit/test_web_runtime.py tests/unit/test_api_surface.py tests/unit/test_setup_status_doctor_drift.py tests/integration/test_web_setup_status_api.py tests/unit/test_backup_restore_cli.py tests/integration/test_web_trust_chip.py tests/unit/test_db_schema_policy.py tests/unit/test_ux_canon_ratchet.py -p no:cacheprovider 2>&1 | tail -1; HOME=$T PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs200_runtime_identity_glass.py -p no:cacheprovider 2>&1 | tail -1; cd web && npx vitest run src/pages/cores/__tests__/runtimeIdentity.test.tsx src/pages/cores/__tests__ 2>&1 | grep -E 'Tests '; npm run guard:architecture 2>&1 | tail -1; cd ..; echo 'web baseline (the worker''s run, read): 2354 passed, zero branch-new'; ls pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-02-shots/ | tr '\n' ' '; echo; grep -c system/identity docs/api-surface.json | sed 's/^/identity route in api surface: /'`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cf1bbb717d8d08276659edb51313fa96c3ece4cc

```text
77 passed in 20.43s
4 passed in 16.03s
      Tests  241 passed (241)
React architecture guard passed (726 source files; zero framework residue).
web baseline (the workers run, read): 2354 passed, zero branch-new
runtime-identity-healthy-desktop.png runtime-identity-healthy-phone.png runtime-identity-stale-desktop.png runtime-identity-stale-phone.png 
identity route in api surface: 1
```
