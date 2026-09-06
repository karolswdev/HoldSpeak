# Evidence - HS-175-08

- **Story:** HS-175-08 - The docs (the calendar in the architecture; the week brief in the guide)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T23:48:37Z

- **Command:** `bash -c HOME=$(mktemp -d) npm_config_cache=/Users/karol/.npm PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_mermaid_renders.py -p no:cacheprovider -rs 2>&1 | tail -6; grep -c 'verify at build' README.md docs/USER_GUIDE.md docs/ARCHITECTURE.md docs/SECURITY.md docs/MCP_SIDECAR.md docs/internal/POSITIONING.md`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 5e119ee0f6c07be5b98f421606a81c0ca3a85c1d

```text
.s                                                                       [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_mermaid_renders.py:101: mermaid renderer unavailable in this env: core/lib/esm/puppeteer/node/BrowserLauncher.js:55:28)
    at async run (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:862:19)
    at async cli (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:374:3)
1 passed, 1 skipped in 1.52s
README.md:0
docs/USER_GUIDE.md:0
docs/ARCHITECTURE.md:0
docs/SECURITY.md:0
docs/MCP_SIDECAR.md:0
docs/internal/POSITIONING.md:0
```

### Captured run — 2026-09-05T23:49:07Z

- **Command:** `bash -c HOME=$(mktemp -d) npm_config_cache=/Users/karol/.npm PUPPETEER_CACHE_DIR=/Users/karol/.cache/puppeteer PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_mermaid_renders.py -p no:cacheprovider -rs 2>&1 | tail -4 && echo 'verify-at-build markers remaining:' && test $(cat README.md docs/USER_GUIDE.md docs/ARCHITECTURE.md docs/SECURITY.md docs/MCP_SIDECAR.md docs/internal/POSITIONING.md | grep -c 'verify at build') -eq 0 && echo 0`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5e119ee0f6c07be5b98f421606a81c0ca3a85c1d

```text
E       assert not ['docs/ARCHITECTURE.md block #7:     at async CdpPage.$eval (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modul...rmaid-cli-intercept.invalid/Users/karol/.npm/_npx/668c188756b835f3/node_modules/mermaid/dist/mermaid.esm.mjs:1221:17)']

tests/e2e/test_mermaid_renders.py:117: AssertionError
1 failed, 1 passed in 37.61s
verify-at-build markers remaining:
0
```

**Reading order.** The two captures above this line are SUPERSEDED and
not proof: the first (23:48:37Z) exited 1 only because `grep -c` returns 1
on a zero count; the second (23:49:07Z) recorded exit 0 while its output
shows `1 failed` — the pipe into `tail` masked pytest's exit, and the
failure was real: ARCHITECTURE.md's Steward drafter diagram (block index
7, a 173-era block) used the participant alias `PAR`, which mermaid reads
as the `par` keyword. Renamed to `PRS` in this commit. The capture below
runs with `set -o pipefail` and is the proof: the render guard 2 passed,
zero `verify at build` markers left in the six docs.

### Captured run — 2026-09-05T23:51:20Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) npm_config_cache=/Users/karol/.npm PUPPETEER_CACHE_DIR=/Users/karol/.cache/puppeteer uv run pytest -q tests/e2e/test_mermaid_renders.py -p no:cacheprovider 2>&1 | tail -3 && echo 'verify-at-build markers remaining:' && test $(cat README.md docs/USER_GUIDE.md docs/ARCHITECTURE.md docs/SECURITY.md docs/MCP_SIDECAR.md docs/internal/POSITIONING.md | grep -c 'verify at build') -eq 0 && echo 0`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5e119ee0f6c07be5b98f421606a81c0ca3a85c1d

```text
..                                                                       [100%]
2 passed in 39.23s
verify-at-build markers remaining:
0
```
