# Evidence - HS-176-02

- **Story:** HS-176-02 - The first correction (teach, persist, apply to the next match; learning digest > 0)
- **Status:** done
- **Date:** 2026-09-06

## Proof

### Captured run — 2026-09-06T15:05:37Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); HOME=$T PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/unit/test_hs176_text_correction.py tests/unit/test_hs176_routes.py tests/unit/test_dictation_correction_store.py tests/unit/test_dictation_pipeline.py tests/unit/test_db_dictation_journal.py tests/integration/test_web_dictation_correction_ritual.py tests/integration/test_web_dictation_corrections_api.py tests/integration/test_dictation_moment_of_truth.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_db.py -k 'not (test_db and not (schema or snapshot))' -p no:cacheprovider 2>&1 | tail -1; HOME=$T PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs176_speak_glass.py -p no:cacheprovider 2>&1 | tail -1; cd web && npx vitest run src/pages/cores/dictation 2>&1 | grep -E 'Tests ' ; cd ..; ls pm/roadmap/holdspeak/phase-176-the-speak-loop/assets/story-02-shots/ | tr '\n' ' '; echo`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d4bfb9e82706d39571743b789311d194b7dde6d6

```text
133 passed, 83 deselected in 39.76s
3 passed in 18.87s
      Tests  57 passed (57)
applied-1440.png applied-393.png refused-1440.png refused-393.png taught-1440.png taught-393.png wrong-1440.png wrong-393.png wrong-route-1440.png wrong-route-393.png 
```
