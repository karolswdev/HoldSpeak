# Evidence — HS-26-01 — Router Seam + Shared Web Context (Pilot: health/state)

- **Shipped:** 2026-05-31
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

The seam every other Phase 26 migration will follow: a `holdspeak/web/routes/`
package whose `build_*_router(ctx)` factories read from a shared
`holdspeak.web.context.WebContext` instead of closing over the `MeetingWebServer`
instance. `/health` and `/api/state` are migrated as the pilot, behavior identical.

## Files touched

- `holdspeak/web/__init__.py` — **new** package doc.
- `holdspeak/web/context.py` — **new** `WebContext` dataclass (pilot field:
  `get_state`). Imports no route module (no cycle).
- `holdspeak/web/routes/__init__.py` — **new**; exports `build_core_router`.
- `holdspeak/web/routes/core.py` — **new**; `build_core_router(ctx)` → `/health`
  + `/api/state` (with the prior fail-soft on `get_state` error).
- `holdspeak/web_server.py` — removed the two inline handlers; mounts
  `build_core_router(WebContext(get_state=self.get_state))` via
  `app.include_router` in `_create_app`.
- `tests/unit/test_web_routes_core.py` — **new**, 4 cases.

## Verification artifacts

```
$ uv run pytest -q tests/unit/test_web_routes_core.py
4 passed
  - /health -> {"status":"ok"}; /api/state -> get_state payload;
    fail-soft -> {} (not 500); no context->routes import cycle.

$ uv run pytest -q tests/integration/test_web_server.py tests/unit/test_web_auth.py \
    tests/integration/test_web_auth_gate.py
91 passed
  (auth middleware still applies to router routes: /health exempt,
   /api/state gated off-loopback)

$ uv run ruff check holdspeak/web/ holdspeak/web_server.py tests/unit/test_web_routes_core.py
All checks passed!

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1875 passed, 13 skipped   (no regressions; same green baseline)
```

## Acceptance criteria — re-checked

- [x] `routes/` package + `WebContext` exist; `/health` + `/api/state` via the router.
- [x] Behavior identical (full suite green; auth gate unchanged; fail-soft preserved).
- [x] No import cycle (test-pinned).
- [x] Pattern documented in module docstrings for HS-26-02..05.

## Deviations from plan

None. Package location `holdspeak/web/routes/` (the deferred default) chosen.

## Follow-ups

- HS-26-02..05 migrate the remaining domains onto this seam; HS-26-06 collapses
  the server's callback bag into `WebContext`.
