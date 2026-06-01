# Evidence — HS-26-05 — Extract Device / Companion / Project Routes

- **Shipped:** 2026-05-31
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

The **last 26 inline routes** moved off `MeetingWebServer._create_app` into three
cohesive modules, leaving `web_server.py` a **thin assembler**:

- `holdspeak/web/routes/pages.py` (`build_pages_router`) — **7** static HTML page
  routes: `/`, `/history`, `/settings`, `/activity`, `/dictation`, `/companion`,
  `/docs/dictation-runtime`.
- `holdspeak/web/routes/system.py` (`build_system_router`) — **6** runtime-surface
  routes: `/api/devices/health`, `/api/runtime/status`, `/api/companion/status`,
  `GET|PUT /api/settings`, and the `/ws` broadcast socket.
- `holdspeak/web/routes/projects.py` (`build_projects_router`) — **13** project
  routes: project CRUD, meeting↔project association, per-project
  summary/action-items/artifacts, the cross-meeting `briefings` timeline, and a
  meeting's project list.

Handlers moved verbatim; only the closure target changed (`self.` → `ctx.`).

## Files touched

- `holdspeak/web/routes/{pages,system,projects}.py` — **new** (174 / 799 / 403 lines).
- `holdspeak/web/context.py` — added 6 accessors: `device_registry`,
  `project_detector`, `ws`, `on_get_status`, `on_settings_applied`,
  `current_formatted_duration` (all default `None`). **WebContext is now complete.**
- `holdspeak/web/routes/__init__.py` — exports the 3 new builders.
- `holdspeak/web_server.py` — removed all 26 inline routes + relocated 6
  module-level helpers/constants (`_DASHBOARD_HTML_PATH` → pages; the runtime-status
  normalizer trio + `_validate_cloud_base_url` + `_merge_dict` + `_HTTP_HEADER_NAME_RE`
  → system); dropped now-unused imports (`json`, `deepcopy`, `urlparse`, `re`).
  **1817 → 532 lines (−1285).** `_create_app` retains only middleware (auth gate),
  lifespan (`startup`/`shutdown`), the `/_built` StaticFiles mount, the device-audio
  WS registration, and the `include_router` wiring — **zero inline route handlers**.

## Decomposition end-state (phase exit metric)

| | original `f77c2d9` | after HS-26-05 |
|---|---|---|
| `web_server.py` | **5658** | **532** (−91%) |
| route modules (`web/routes/`) | 0 | 7 modules, 5419 lines |

## Verification artifacts

```
$ grep -n "@app\." holdspeak/web_server.py
376:        @app.middleware("http")     # auth gate (assembly)
466:        @app.on_event("startup")    # lifespan (assembly)
473:        @app.on_event("shutdown")   # lifespan (assembly)
# -> no inline @app.get/post/... route handlers remain

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1879 passed, 13 skipped        (no regressions)

$ uv run ruff check holdspeak/web/ holdspeak/web_server.py
All checks passed!
```

**Route-inventory diff** (built app, `app.routes`, vs the original `origin/main`
baseline `f77c2d9`): identical paths/methods, 122 HTTP routes.

## Decisions / notes

- **Three cohesive modules, not one grab-bag.** Pages (static serving), system
  (runtime/settings/WS), and projects are distinct concerns; splitting keeps each
  navigable.
- **Relocation bug caught + fixed.** The page handlers compute their built-HTML
  path from `Path(__file__).resolve().parent`; after the move `__file__` points at
  `holdspeak/web/routes/`, so the path broke (16 page-content tests failed on the
  full-suite run). Fixed by anchoring `_HOLDSPEAK_DIR = Path(__file__).resolve()
  .parent.parent.parent` in `pages.py`. **The full suite — not the narrow `-k` —
  was again the gate** that caught this.
- **Relocated single-domain helpers; no new monolith reach.** `_HTTP_HEADER_NAME_RE`,
  `_normalize_runtime_status_payload` (+ its `_meeting_*_from_state` deps),
  `_validate_cloud_base_url`, `_merge_dict` → `system.py`; `_DASHBOARD_HTML_PATH`
  → `pages.py`. `system.py`/`projects.py`/`pages.py` import nothing from `web_server`.
- **Device-audio WS unchanged.** `device_audio_ws.py` keeps its PSK handshake and
  stays registered in `_create_app` (per scope).

## Acceptance criteria — re-checked

- [x] All remaining domain routes served from modules; `_create_app()` has no inline route handler bodies.
- [x] Existing device/companion/project/settings/WS tests pass unchanged.
- [x] Route-inventory diff shows identical paths/methods for the moved set.

## Follow-ups

- HS-26-06: collapse the `MeetingWebServer` constructor callback bag into
  `WebContext` and re-home the two still-shared helpers (`_meeting_callback_payload`,
  `_parse_iso_datetime`) so `meetings.py` + `activity.py` stop importing from
  `web_server`. HS-26-07: closeout (size + regression evidence).
