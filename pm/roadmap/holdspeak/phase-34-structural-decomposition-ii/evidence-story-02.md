# Evidence — HS-34-02 (Split `web/routes/activity.py` → `routes/activity/`)

**Shipped:** 2026-06-03. The 1,319-line / 38-handler `build_activity_router(ctx)`
is now a `routes/activity/` sub-package of five domain modules, composed behind a
**stable** `build_activity_router(ctx)`. Behavior-preserving: route table
byte-identical (38 routes, same hash) and the full suite unchanged.

## What changed

`holdspeak/web/routes/activity.py` → `holdspeak/web/routes/activity/`:

| Module | Lines | Routes |
|---|---|---|
| `__init__.py` | 45 | composes the five sub-routers behind `build_activity_router(ctx)` |
| `ledger.py` | 189 | `/api/activity/status`, `records` (get/delete), `refresh`, `settings`, `domains` (post/delete) + `_activity_status_payload` |
| `rules.py` | 176 | `/api/activity/project-rules*` (CRUD + preview + apply) |
| `enrichment.py` | 614 | `/api/activity/enrichment/*`, `extension/events`, `annotations`, `briefing` |
| `candidates.py` | 228 | `/api/activity/meeting-candidates*` |
| `plugin_jobs.py` | 205 | `/api/plugin-jobs*` (list/summary/process/retry-now/cancel) |

Old: **1,319 lines, one module.** New: **1,457 lines across 6 files** (the +138 is
per-module imports/docstrings/`build_*_router` boilerplate; the largest single file
is now `enrichment.py` at 614, down from 1,319).

## How it stays behavior-preserving

- **Verbatim handler moves** — only the relative imports gained one dot
  (`...db` → `....db`, `..runtime_support` → `...runtime_support`,
  `..context` → `...context`); handler bodies + their `ctx.` usage are unchanged.
- **No shared state to thread** — unlike the dictation split, every module-level
  payload shaper here is used by *exactly one* domain group, so each travels with
  its handlers (`_activity_status_payload`→ledger, the rule/record shapers→rules,
  the connector shaper→enrichment, the candidate shaper + `_meeting_payload_id`→
  candidates). The only cross-cutting helpers (`_meeting_callback_payload`,
  `_parse_iso_datetime`, `error_500`) still come from the neutral
  `web/runtime_support` — no route module imports `web_server`.
- **Absolute paths + `include_router`** keep the full `(path, method)` set
  identical (no `{id}`-vs-literal collisions across the five groups).

## Tests ran

- **Route-table invariant** — new `tests/unit/test_activity_routes_split.py`
  asserts the exact 38-route `(path, method)` set + count. **2 passed.**
- Pre/post route-table hash compared: **`d4332051064ff059` → `d4332051064ff059`** (identical).
- `uv run pytest -q` across the activity-touching suites
  (`test_web_activity_api.py`, `test_web_server.py`) → **126 passed.**
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1956 passed, 15 skipped**
  — identical to the post-HS-34-01 baseline.
- `uv run ruff check holdspeak/web/routes/activity/` (+ `--select F821`) →
  **All checks passed!**

## Done-when

- [x] `web/routes/activity.py` → a `routes/activity/` sub-package; handlers grouped
      by domain (ledger / rules / enrichment / candidates / plugin-jobs).
- [x] `build_activity_router(ctx)` import unchanged; `routes/__init__.py` untouched.
- [x] Route table byte-identical; full suite green; package ruff-clean.

## Decisions / deviations

- **`plugin_jobs.py` kept its `/api/plugin-jobs*` paths** (not `/api/activity/*`) —
  the split is by code organization, not URL; moving the paths would break the
  route-table invariant and the API. It's its own module because it's its own
  domain (the deferred MIR plugin-run queue), as the original file already noted.
- **No shared `_helpers.py`** (unlike dictation) — there was no cross-group helper
  or shared state to extract, so adding one would be ceremony.
