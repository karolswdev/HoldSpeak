# Parked vitest files

Vitest files retired by the test diet, push 2 (2026-10-12). Each one read
source text (`readFileSync`, `?raw`) to pin markup, class names, CSS or copy,
instead of rendering. The pull request that parked a file names its
successor (a rendered test, the desk sweep, or none and why).

Vitest does not collect this folder (`web/vite.config.ts`, `exclude`), and
`tsc` does not check it (`web/tsconfig.json`). The paths below `_parked/`
are the original paths below `web/src/`. Never delete: park.
