# HS-26-01 — Router Seam + Shared Web Context (Pilot: health/state)

- **Project:** holdspeak
- **Phase:** 26
- **Status:** backlog
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

- [ ] A `routes/` package + shared context exist; `/health` and `/api/state` are
      served from the new router.
- [ ] Behavior is identical: existing web tests pass; paths/methods/payloads
      unchanged.
- [ ] No import cycle (routers import the context; the context imports no router).
- [ ] The pattern is documented for HS-26-02..05 to follow.

## Test plan

- Unit: `uv run pytest -q tests/ -k web` — existing web tests stay green;
  `/health` + `/api/state` covered.
- Integration: local web client boots and reaches `/api/state`.
- Manual: n/a.

## Notes / open questions

- Settle the package location here (default `holdspeak/web/routes/`).
- Sequence after Phase 25 closes so the auth gate is already in the monolith.
