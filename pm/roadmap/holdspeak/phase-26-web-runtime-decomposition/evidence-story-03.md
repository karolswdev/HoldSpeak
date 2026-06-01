# Evidence — HS-26-03 — Extract Dictation / Agent-Hook / Intent Routes

- **Shipped:** 2026-05-31
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

The dictation-pipeline cluster — **26 routes** plus all their private helpers —
moved off `MeetingWebServer._create_app` into
`holdspeak/web/routes/dictation.py` (`build_dictation_router(web_ctx)`), reading
from `WebContext`. Handlers and helpers moved verbatim; only the closure target
(`self.` → `web_ctx.`) and the package-relative import depth changed.

Routes moved (paths/methods unchanged):

- Intent controls: `GET /api/intents/control`, `PUT /api/intents/profile`,
  `PUT /api/intents/override`, `POST /api/intents/preview`.
- Agent context / hooks: `GET /api/dictation/agent-context`,
  `GET /api/dictation/agent-hooks`, `POST /api/dictation/agent-context/clear`,
  `POST /api/dictation/agent-context/summarize`.
- Project context + `.hs` docs: `GET /api/dictation/project-context`,
  `GET|PUT /api/dictation/project-hs`,
  `GET /api/dictation/project-doc-suggestion`, `.../apply`, `.../dismiss`.
- Blocks: `GET /api/dictation/block-templates`, `GET /api/dictation/readiness`,
  `GET|POST /api/dictation/blocks`, `.../from-template`,
  `PUT|DELETE /api/dictation/blocks/{block_id}`.
- Project KB: `GET|PUT|DELETE /api/dictation/project-kb`, `.../starter`.
- Dry-run: `POST /api/dictation/dry-run`.

The cluster's private helpers (`_resolve_project_context`,
`_resolve_blocks_target`, the project-doc-suggestion set + the per-app
`project_doc_suggestions` dict, block-config IO, `_run_dictation_dry_run_text`,
`_runtime_readiness`, the starter-template tables) moved with the routes — they
are used by no other domain. `project_doc_suggestions` stays a single per-app
closure variable inside `build_dictation_router`, preserving its semantics.

## Files touched

- `holdspeak/web/routes/dictation.py` — **new** (1608 lines); `build_dictation_router`.
- `holdspeak/web/context.py` — added 5 accessors (`on_get_intent_controls`,
  `on_set_intent_profile`, `on_set_intent_override`, `on_route_preview`,
  `on_dictation_config_changed`), all defaulting to `None`.
- `holdspeak/web/routes/__init__.py` — exports `build_dictation_router`.
- `holdspeak/web_server.py` — removed the inline intents block + the whole
  dictation block (helpers + routes); dropped 3 now-unused intent request-model
  imports + the now-unused `os` import; mounts `build_dictation_router(web_ctx)`.
  **4691 → 3133 lines (−1558).** Cumulative across HS-26-02/03: **5658 → 3133**.

## Verification artifacts

```
$ uv run pytest -q tests/ -k "web and (dictation or intent or project_kb or blocks or readiness or dry_run or agent_hook)"
128 passed

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1879 passed, 13 skipped        (no regressions)

$ uv run ruff check holdspeak/web/ holdspeak/web_server.py
All checks passed!
```

**Route-inventory diff** (built app, `app.routes`, vs the original `origin/main`
baseline at `f77c2d9` that predates the whole phase): identical paths/methods,
122 HTTP routes (only delta the environmental `/_built` static mount).

## Deviations from plan / decisions

- **Two `_GLOBAL_BLOCKS_PATH` reads are resolved through the `web_server` module
  object** (`_self_module._GLOBAL_BLOCKS_PATH`) rather than bound at import: three
  integration tests `monkeypatch.setattr(web_server, "_GLOBAL_BLOCKS_PATH", ...)`,
  and the prior inline code resolved it the same dynamic way (one site already
  used the indirect pattern; the dry-run site used a bare module global, which
  resolves identically). Preserves behavior.
- **The WebContext parameter is named `web_ctx`, not `ctx`.** Several
  `/api/dictation/project-kb` handlers use a local `ctx = _resolve_project_context(...)`
  (a project dict) that would shadow a `ctx`-named context, so the verbatim
  `self.on_dictation_config_changed` → context access would bind to the dict. The
  full suite caught this (8 project-kb failures) before commit; renaming the
  parameter resolves it. (The narrow story `-k "web and (dictation or intent)"`
  filter under-selects — the project-KB tests live in `test_web_project_kb_api.py`,
  whose name matches neither term — so the full-suite run is the real gate here.)
- `routes/dictation.py` holds the whole cluster (1608 lines). Like
  `meetings.py`, kept whole as a single verbatim move; revisit a split at HS-26-07.
- `meetings.py` imports two server-agnostic helpers from `web_server`;
  `dictation.py` needs none (its helpers all moved with it), but it reads
  `_GLOBAL_BLOCKS_PATH` via the lazily-imported `web_server` module as above.

## Acceptance criteria — re-checked

- [x] Listed routes served from `routes/dictation.py`; none remain inline in `_create_app()`.
- [x] Existing dictation/intent web tests pass unchanged (incl. project-kb/blocks/readiness/dry-run).
- [x] Route-inventory diff shows identical paths/methods for the moved set.

## Follow-ups

- HS-26-04 (activity / connector / plugin-job), 05 (device/companion/project)
  continue the migration; HS-26-06 collapses the server's callback bag into
  `WebContext` (and can drop the `broadcast` thunk + the meetings helper import).
