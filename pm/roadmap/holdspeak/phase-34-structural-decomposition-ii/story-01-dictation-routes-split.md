# HS-34-01 — Split `web/routes/dictation.py` → `routes/dictation/` sub-package

- **Status:** not-started.

## Goal

The 1,607-line `web/routes/dictation.py` is one `build_dictation_router(ctx)`
factory holding ~26 handlers across six unrelated concerns. Split it into a
`routes/dictation/` sub-package by domain, behind a **stable**
`build_dictation_router(ctx)` so nothing upstream changes.

## Scope

- Create `holdspeak/web/routes/dictation/` with one module per domain seam (the
  route-path prefixes):
  - `intents.py` — `/api/intents/*` (control, profile, override, preview).
  - `agent.py` — `/api/dictation/agent-context*`, `agent-hooks`, `project-context`.
  - `project_docs.py` — `/api/dictation/project-hs`, `project-doc-suggestion*`.
  - `blocks.py` — `/api/dictation/block-templates`, `blocks*` CRUD.
  - `kb.py` — `/api/dictation/project-kb*`.
  - `pipeline.py` — `/api/dictation/readiness`, `/api/dictation/dry-run`.
  - `__init__.py` — `build_dictation_router(ctx)` composes the sub-routers via
    `include_router` (or merges them onto one `APIRouter`) and is re-exported so
    `from holdspeak.web.routes.dictation import build_dictation_router` and
    `routes/__init__.py` are unchanged.
- Handlers + their private helpers move **verbatim** (Phase-26 rule: only `ctx.`
  closure target stays; package-relative imports gain one dot — these modules sit
  one level deeper). Single-domain helpers travel with their handlers; any genuinely
  shared helper goes to the sub-package `__init__` or `web/runtime_support`.

## Test plan

- **Route-table invariant:** the app's full `(path, method)` set is identical
  before/after (capture once, assert; this is the phase's shared gate — see
  HS-34-05).
- `ruff --select F821` on each new module (undefined-name sweep — Phase-31 lesson).
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green
  (`-k` filters miss late-binding/`ctx`-shadow bugs).
- `uv run ruff check holdspeak/web/routes/dictation/` — clean.

## Done when

- [ ] `web/routes/dictation.py` → a `routes/dictation/` sub-package; handlers grouped
      by domain.
- [ ] `build_dictation_router(ctx)` import unchanged; `routes/__init__.py` untouched.
- [ ] Route table byte-identical; full suite green; package ruff-clean.
