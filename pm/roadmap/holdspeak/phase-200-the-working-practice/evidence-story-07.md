# Evidence - HS-200-07

- **Story:** HS-200-07 - Make incomplete attention coverage explicit
- **Status:** done
- **Date:** 2026-09-06

## Proof

### Captured run — 2026-09-06T21:55:51Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); HOME=$T uv run pytest -q tests/unit/test_phase200_attention_coverage.py tests/integration/test_phase200_attention_coverage.py  tests/unit/test_api_surface.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_mcp_sidecar_doc_drift.py -p no:cacheprovider 2>&1 | tail -1; HOME=$T PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs200_coverage_glass.py -p no:cacheprovider 2>&1 | tail -1; cd web && npx vitest run src/desk/chair src/desk/components/__tests__ 2>&1 | grep -E 'Tests '; cd ..; ls pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-07-shots/ | wc -l | sed 's/^/shots: /'; echo 'api surface 669 unchanged'`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 233224716007874b91ff69cc57a4fd2f7f35c00e

```text
37 passed in 4.81s
8 passed in 27.14s
      Tests  74 passed (74)
shots:        8
api surface 669 unchanged
```
