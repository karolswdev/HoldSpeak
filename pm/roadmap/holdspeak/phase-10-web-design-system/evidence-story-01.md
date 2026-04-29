# HS-10-01 evidence — Astro + Open Props bootstrap

## Source layout shipped

```
web/
├── .gitignore (via repo root)
├── README.md
├── astro.config.mjs        # outDir = ../holdspeak/static/_built, base = /_built
├── package.json            # astro ^4.16.18, open-props ^1.7.13
└── src/
    ├── pages/
    │   └── design/check.astro   # smoke page consuming Open Props tokens
    └── styles/
        └── global.css           # placeholder; real tokens land in HS-10-02
```

`holdspeak/static/_built/` and `web/node_modules/`, `web/dist/`,
`web/.astro/` are added to `.gitignore`.

## Build loop verified

```
$ cd web && npm install
added 330 packages, and audited 331 packages in 10s

$ npm run build
> astro build
21:09:21 [build] output: "static"
21:09:21 [build] directory: /Users/karol/dev/tools/HoldSpeak/holdspeak/static/_built/
21:09:22 ▶ src/pages/design/check.astro
21:09:22   └─ /design/check/index.html (+3ms)
21:09:22 [build] 1 page(s) built in 262ms
21:09:22 [build] Complete!
```

Output tree:

```
$ find holdspeak/static/_built -type f
holdspeak/static/_built/_astro/check.LRuJK_i5.css
holdspeak/static/_built/design/check/index.html
```

Asset URL prefix correctly carries the `/_built` base:

```
$ grep href holdspeak/static/_built/design/check/index.html
<link rel="stylesheet" href="/_built/_astro/check.LRuJK_i5.css">
```

## Legacy pages survived

```
$ ls holdspeak/static/
_built
activity.html
dashboard.html
dictation-runtime-setup.html
dictation.html
history.html
```

All five hand-authored files are byte-identical to pre-build state; the
build pipeline only writes under `_built/`.

## FastAPI wiring

`holdspeak/web_server.py` now imports `StaticFiles` and mounts the
built directory at `/_built` when it exists:

```python
_BUILT_DIR = Path(__file__).resolve().parent / "static" / "_built"
if _BUILT_DIR.is_dir():
    app.mount(
        "/_built",
        StaticFiles(directory=str(_BUILT_DIR), html=True),
        name="built",
    )
```

The mount is conditional so the runtime keeps working when the build
output is absent (fresh clones, CI without Node).

## Smoke test

`tests/integration/test_web_built_mount.py`:

```
$ uv run pytest -q tests/integration/test_web_built_mount.py
..                                                                       [100%]
2 passed in 0.43s
```

The two cases:

- `/_built/design/check/` returns 200, contains the smoke marker
  ("Design pipeline online"), and references the `/_built/_astro/`
  asset path — proving Astro → mount → browser end-to-end.
- All five legacy routes (`/`, `/activity`, `/history`, `/dictation`,
  `/docs/dictation-runtime`) still return 200 with their expected
  content markers — proving the legacy surface is untouched.

## Full regression sweep

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1180 passed, 13 skipped in 31.77s
```

Skips are pre-existing (audio fixture absences, optional llama-cpp
backend) and unrelated to HS-10-01.

## Acceptance criteria

- [x] `cd web && npm install && npm run build` produces files under
  `holdspeak/static/` (specifically `static/_built/`) without erasing
  the existing five legacy pages.
- [x] FastAPI runtime serves the new design-check route alongside the
  existing pages with no regressions.
- [x] `npm run dev` is wired (Astro's built-in dev server; documented
  in `web/README.md`). Hot-reload behavior is the standard Astro dev
  loop and was not exercised in CI; it will be exercised continuously
  during HS-10-02 onwards.
- [x] Open Props is reachable from a component — `src/styles/global.css`
  consumes `--gray-11`, `--gray-12`, `--cyan-3`, `--radius-3`,
  `--font-sans`, `--font-mono`, etc.
- [x] `web/README.md` documents the dev/build commands and the
  output-into-`holdspeak/static/_built/` contract.
- [x] No new runtime Python dependency introduced. `StaticFiles` is
  already part of FastAPI; Node is build-time only.

## Notes for next stories

- The `/_built/design/check/` smoke page should be deleted (or repurposed
  as the components gallery anchor) once HS-10-03 ships
  `/_built/_design/components/`.
- The `_BUILT_DIR.is_dir()` guard is intentional. CI environments that
  don't run `npm run build` see the runtime exactly as before.
- Astro 4.x triggered 3 npm-audit advisories (2 moderate, 1 high) at
  install time. They are transitive and build-time only; not loaded
  into the runtime. Will reassess at the next Astro minor.
