# Evidence — HS-26-02 — Extract Meeting / Speaker / Intel Routes

- **Shipped:** 2026-05-31
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

The largest route cluster moved off `MeetingWebServer._create_app` onto the
HS-26-01 seam: **25 routes** now served from `holdspeak/web/routes/meetings.py`
via `build_meetings_router(ctx)`, reading server state from `WebContext` instead
of closing over the server instance. Handlers were moved **verbatim** (no logic
changes); only the closure target changed (`self.` → `ctx.`).

Routes moved (paths/methods unchanged):

- Lifecycle + bookmark: `POST /api/bookmark`, `POST /api/meeting/start`,
  `POST /api/meeting/stop`, `POST /api/stop`, `PATCH /api/meeting`.
- Meeting-scoped action items: `PATCH /api/action-items/{item_id}`,
  `.../review`, `.../edit`.
- DB-backed reads: `GET /api/meetings`, `GET /api/meetings/{id}`,
  `.../export`, `.../intent-timeline`, `.../plugin-runs`, `.../artifacts`.
- Speakers: `GET /api/speakers`, `GET /api/speakers/{id}`,
  `PATCH /api/speakers/{id}`.
- Global action items: `GET /api/all-action-items`,
  `PATCH /api/all-action-items/{id}`, `.../review`, `.../edit`.
- Intel queue: `GET /api/intel/jobs`, `GET /api/intel/summary`,
  `POST /api/intel/process`, `POST /api/intel/retry/{meeting_id}`.

## Files touched

- `holdspeak/web/routes/meetings.py` — **new** (1020 lines); `build_meetings_router`.
- `holdspeak/web/context.py` — added the 11 lifecycle/action-item accessors the
  moved handlers need (each defaults to `None` so the pilot test's
  `WebContext(get_state=...)` stays valid).
- `holdspeak/web/routes/__init__.py` — exports `build_meetings_router`; docstring
  updated to note the transitional, server-agnostic helper import.
- `holdspeak/web_server.py` — removed the 25 inline handlers + the nested
  `_handle_stop_request` helper; trimmed the 12 now-unused request-model imports;
  mounts `build_meetings_router(web_ctx)` via `app.include_router`. **5658 → 4691
  lines (−967).**

## Verification artifacts

```
$ uv run pytest -q tests/ -k "web and (meeting or speaker or intel)" \
    tests/unit/test_web_routes_core.py
149 passed, 1759 deselected

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1879 passed, 13 skipped        (no regressions)

$ uv run ruff check holdspeak/web/ holdspeak/web_server.py
All checks passed!
```

**Route-inventory diff** (built app, `origin/main` baseline vs working tree,
both via `app.routes`): identical paths/methods — the only delta was the
`/_built` StaticFiles mount, which is gated on `static/_built/` existing on disk
(present locally, absent in the fresh worktree that never ran `npm build`) and is
unrelated to the refactor. 122 HTTP routes, byte-identical otherwise.

## Deviations from plan

- `routes/meetings.py` holds the whole cluster (the story allowed splitting
  speaker/intel out if it grew unwieldy). At 1020 lines it is large but cohesive
  and a single move; deferring any sub-split keeps this story a clean verbatim
  migration. Revisit at HS-26-07 if it impedes navigation.
- **`broadcast` is late-bound** (a `lambda` delegating to `self.broadcast`)
  rather than snapshotted. The prior inline handlers called `self.broadcast(...)`,
  which resolves the attribute at call time; an integration test reassigns
  `server.broadcast` post-construction to spy on it. Freezing the bound method
  broke that test; the thunk preserves the original dynamic dispatch. The `on_*`
  callbacks are passed once at construction (never reassigned), so they are
  snapshotted directly.
- `meetings.py` imports two **module-level, server-agnostic** helpers from
  `web_server` (`_meeting_callback_payload`, `_UnknownDeviceError`). This stays
  acyclic because `web_server` imports the routes lazily (inside `_create_app`);
  `WebContext` still imports no route module (test-pinned).

## Acceptance criteria — re-checked

- [x] Listed routes served from `routes/meetings.py`; none remain inline in `_create_app()`.
- [x] Existing web tests for meetings/speakers/intel pass unchanged (149 passed).
- [x] Route-inventory diff shows identical paths/methods for the moved set.

## Follow-ups

- HS-26-03 (dictation/agent-hook), 04 (activity/connector/plugin-job), 05
  (device/companion/project) continue the migration; HS-26-06 collapses the
  server's callback bag into `WebContext` (and can drop the `broadcast` thunk +
  the `web_server` helper import once those helpers move to a neutral home).
