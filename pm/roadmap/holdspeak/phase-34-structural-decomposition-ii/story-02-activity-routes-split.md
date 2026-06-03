# HS-34-02 — Split `web/routes/activity.py` → `routes/activity/` sub-package

- **Status:** not-started.

## Goal

`web/routes/activity.py` is 1,319 lines / **38 route handlers** across five distinct
concerns. Split it into a `routes/activity/` sub-package, behind a stable
`build_activity_router(ctx)`.

## Scope

- Create `holdspeak/web/routes/activity/` with one module per domain seam:
  - `ledger.py` — `/api/activity/status`, `records` (get/delete), `refresh`,
    `settings`, `domains` (post/delete).
  - `rules.py` — `/api/activity/project-rules*` (CRUD + preview + apply).
  - `enrichment.py` — `/api/activity/enrichment/*` (connectors, pipelines, runs,
    annotations, GitHub/Jira preview+run) + `/api/activity/extension/events`,
    `annotations`, `briefing`.
  - `candidates.py` — `/api/activity/meeting-candidates*`.
  - `plugin_jobs.py` — `/api/plugin-jobs*` (the deferred plugin/intel job queue API;
    it lives in this module today but is its own domain).
  - `__init__.py` — `build_activity_router(ctx)` composes the sub-routers and is
    re-exported so `routes/__init__.py` is unchanged.
- Same verbatim-move rules as HS-34-01 (Phase-26 `ctx` pattern; helpers travel with
  their handlers; relative imports gain one dot).

## Test plan

- **Route-table invariant** (shared with HS-34-01 / HS-34-05): full `(path, method)`
  set identical before/after.
- `ruff --select F821` on each new module.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green.
- `uv run ruff check holdspeak/web/routes/activity/` — clean.

## Done when

- [ ] `web/routes/activity.py` → a `routes/activity/` sub-package; handlers grouped
      by domain (ledger / rules / enrichment / candidates / plugin-jobs).
- [ ] `build_activity_router(ctx)` import unchanged; `routes/__init__.py` untouched.
- [ ] Route table byte-identical; full suite green; package ruff-clean.
