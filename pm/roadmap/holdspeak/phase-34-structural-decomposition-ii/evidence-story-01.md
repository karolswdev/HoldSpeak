# Evidence — HS-34-01 (Split `web/routes/dictation.py` → `routes/dictation/`)

**Shipped:** 2026-06-03. The 1,607-line single `build_dictation_router(ctx)` is now
a `routes/dictation/` sub-package of six domain modules + a shared helpers module,
composed behind a **stable** `build_dictation_router(ctx)`. Behavior-preserving:
the route table is byte-identical (26 routes, same hash) and the full suite is
unchanged.

## What changed

`holdspeak/web/routes/dictation.py` → `holdspeak/web/routes/dictation/`:

| Module | Lines | Routes |
|---|---|---|
| `__init__.py` | 54 | composes the six sub-routers behind `build_dictation_router(ctx)` |
| `intents.py` | 99 | `/api/intents/*` (control, profile, override, preview) |
| `agent.py` | 201 | `/api/dictation/project-context`, `agent-context*`, `agent-hooks` |
| `project_docs.py` | 134 | `/api/dictation/project-hs` (get/put), `project-doc-suggestion*` |
| `blocks.py` | 342 | `/api/dictation/block-templates`, `blocks*` CRUD + from-template |
| `kb.py` | 167 | `/api/dictation/project-kb*` |
| `pipeline.py` | 263 | `/api/dictation/readiness`, `dry-run` |
| `_helpers.py` | 594 | ctx-free shared helpers + constants + the dry-run executor |

Old: **1,607 lines, one module.** New: **1,854 lines across 8 files** (the +247 is
per-module imports/docstrings/`build_*_router` boilerplate — the largest single
file is now `_helpers.py` at 594, down from 1,607).

## How it stays behavior-preserving

- **Verbatim handler/helper moves** — only the `ctx.` closure target stays and the
  relative imports gained one dot (`...logging_config` → `....logging_config`,
  `..context` → `...context`) — these modules sit one package deeper. The
  Phase-26 rule, re-applied one level down.
- **Absolute route paths + `include_router`** — each `build_*_router(ctx)`
  registers its `/api/...` paths and `__init__` includes them with no prefix, so
  the full `(path, method)` set is unchanged (no ordering hazards: every path is
  distinct, no `{id}` vs literal collisions).
- **Shared suggestion store threaded explicitly** — the in-memory
  `project_doc_suggestions` dict (a dry-run/from-template *detects* a suggestion;
  the project-doc-suggestion GET *reads* it) was a closure variable in the old
  single factory. It's now created once in `build_dictation_router` and passed to
  the three groups that touch it (`project_docs`, `blocks`, `pipeline`) — same
  per-app lifetime, same test isolation. `_store_project_doc_suggestion(...)` and
  `_run_dictation_dry_run_text(...)` gained an explicit `suggestions` parameter.

## Tests ran

- **Route-table invariant** — new `tests/unit/test_dictation_routes_split.py`
  asserts the exact 26-route `(path, method)` set + count. **2 passed.** (The
  phase's shared gate — HS-34-02 adds its own; HS-34-05 re-verifies.)
- Pre/post route-table hash compared by hand: **`0a0b26562cf25a36` → `0a0b26562cf25a36`** (identical).
- `uv run pytest -q tests/integration/test_web_dictation_blocks_api.py
  test_web_dictation_settings_api.py test_web_dictation_readiness_api.py
  test_web_project_kb_api.py` → **93 passed.**
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1954 passed, 15 skipped**
  — identical to the pre-split baseline.
- `uv run ruff check holdspeak/web/routes/dictation/` (incl. an explicit
  `--select F821` undefined-name sweep) → **All checks passed!**

## Done-when

- [x] `web/routes/dictation.py` → a `routes/dictation/` sub-package; handlers grouped
      by domain.
- [x] `build_dictation_router(ctx)` import unchanged; `routes/__init__.py` untouched.
- [x] Route table byte-identical; full suite green; package ruff-clean.

## Decisions / deviations

- **`_helpers.py` for the shared, ctx-free helpers** rather than scattering them or
  forcing them onto a class — they're pure functions several groups call; one
  module keeps the move verbatim and the imports obvious.
- **`project-context` grouped with `agent.py`** — it's the small project-detection
  endpoint the agent-context routes lean on; it has no domain module of its own.
