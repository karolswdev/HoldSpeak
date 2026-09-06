# Evidence - HS-176-03

- **Story:** HS-176-03 - The journal as a stream (live feed, filterable, searchable; the voice-typing act visible)
- **Status:** done
- **Date:** 2026-09-06

## Proof

### Captured run — 2026-09-06T15:07:43Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); HOME=$T PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs176_journal_glass.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_hs176_routes.py -p no:cacheprovider 2>&1 | tail -1; cd web && npx vitest run src/pages/cores/dictation src/desk/surface 2>&1 | grep -E 'Tests ' ; node scripts/validate-tokens.cjs 2>&1 | tail -1; node scripts/guard-architecture.mjs 2>&1 | tail -1; cd ..; ls pm/roadmap/holdspeak/phase-176-the-speak-loop/assets/story-03-shots/ | tr '\n' ' '; echo`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4503fcd397d31e8a97cb19d915427cd8743a1730

```text
41 passed in 70.56s (0:01:10)
      Tests  337 passed (337)
token gate: clean (11 allow-listed exceptions, all in use)
React architecture guard passed (719 source files; zero framework residue).
filtered-1440.png filtered-393.png quiet-1440.png quiet-393.png row-open-1440.png row-open-393.png stream-1440.png stream-393.png 
```
