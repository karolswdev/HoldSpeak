# Evidence — HS-54-04: The density guard

**Date:** 2026-06-11
**Branch:** `phase-54-dictation-frontend`

## 1. The guard

`tests/unit/test_frontend_density_guard.py` (the doc-drift-guard pattern: plain
unit test, default suite, no marker gymnastics) locks the shipped shape:

| Surface | Budget | Shipped |
|---|---|---|
| `web/src/pages/dictation.astro` | ≤ 300 | 252 |
| `web/src/scripts/dictation-app.js` (entry) | ≤ 50 | 19 |
| `web/src/components/dictation/*.astro` | ≤ 600 each | largest 499 (`MemorySection`) |
| `web/src/scripts/dictation/*.js` | ≤ 600 each | largest 576 (`knowledge.js`) |

Each failure message says what to do (**carve, don't bump** — a new partial /
module along the same seams) and points at the architecture doc. A sanity test
asserts the guard scans the real tree so a green run is never vacuous.

## 2. Proven both ways (violation not committed)

```
$ uv run pytest -q tests/unit/test_frontend_density_guard.py
5 passed in 0.02s

# temporarily pad core.js with 500 comment lines →
E  AssertionError: Dictation behavior modules over the 600-line budget — split
   by concern (a new module + registerSection/loadSection for cross-module
   reloads) rather than growing one module:
     core.js: 711 lines

# revert →
5 passed in 0.02s
```

## 3. Before / after — the paydown, measured

| | Before (scaffold) | After (HS-54-01..04) |
|---|---|---|
| Files | 2 | 27 (1 page + 14 components + 1 entry + 12 modules… counting the guard's surfaces) |
| Total lines | 6,101 | 3,259 (markup/styles) + 3,197 (behavior) = 6,456 |
| Largest file | 3,134 (`dictation.astro`) | 576 (`knowledge.js`) |
| Page | 3,134 | 252 |
| Script blob | 2,967 | 19-line entry |

(The ~350-line total growth is the cost of imports/exports, component
frontmatter, and module headers — the price of navigability; the largest unit
shrank 5.4×.)

## 4. Full suite

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2545 passed, 17 skipped in 75.53s (0:01:15)
```

(2540 → 2545: the five new guard tests.)
