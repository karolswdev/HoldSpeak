# HS-26-01 — Router Seam + Shared Web Context (Pilot: health/state)

- **Project:** holdspeak
- **Phase:** 26
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-26-02, HS-26-03, HS-26-04, HS-26-05, HS-26-06
- **Owner:** unassigned

## Problem

All ~125 routes are defined inline in `MeetingWebServer._create_app()`
(`web_server.py`), wired through 40+ constructor callbacks. There is no seam to
move routes through. This story establishes the pattern — a `routes/` package
using `APIRouter` and a shared web-context object — and proves it on a low-risk
pilot (the `/health` and `/api/state` routes) without changing behavior.

## Scope

### In

- Create the route-module package (default `holdspeak/web/routes/`).
- Introduce a shared web-context object that exposes the runtime state/services
  the routes need (the thing that replaces the callback bag).
- Migrate `/health` and `/api/state` to a pilot router as the reference pattern.
- Keep the app assembled by `MeetingWebServer`; only these two routes move.

### Out

- Moving any other routes (HS-26-02..05).
- Removing callbacks wholesale (HS-26-06) — only what the two pilot routes need.

## Acceptance criteria

- [x] `holdspeak/web/routes/` package + `holdspeak/web/context.py` (`WebContext`)
      exist; `/health` and `/api/state` are served from `build_core_router`
      (`web/routes/core.py`), mounted via `app.include_router` in `_create_app`.
- [x] Behavior identical: the existing web suite passes (91 web tests; full suite
      1875 passed); paths/methods/payloads unchanged, incl. the fail-soft
      empty-object on `get_state` error.
- [x] No import cycle — `WebContext` imports no route module; pinned by
      `test_web_routes_core.py::test_context_module_has_no_route_import_cycle`.
- [x] Pattern documented (module docstrings in `web/__init__.py`,
      `web/context.py`, `web/routes/__init__.py`, `web/routes/core.py`) for
      HS-26-02..05 to follow.

## Test plan

- Unit: `uv run pytest -q tests/ -k web` — existing web tests stay green;
  `/health` + `/api/state` covered.
- Integration: local web client boots and reaches `/api/state`.
- Manual: n/a.

## Notes / open questions

- Settle the package location here (default `holdspeak/web/routes/`).
- Sequence after Phase 25 closes so the auth gate is already in the monolith.

## Closeout

Shipped 2026-05-31. See [evidence-story-01.md](./evidence-story-01.md).

Package location decided: **`holdspeak/web/routes/`** (the deferred decision),
with `holdspeak/web/context.py` for `WebContext`. Coexists fine with the
`holdspeak/web_server.py` module. The HS-25-02 auth middleware is app-level, so it
still applies to router-mounted routes (`/health` exempt, `/api/state` gated
off-loopback) — verified by the auth-gate suite passing unchanged.
