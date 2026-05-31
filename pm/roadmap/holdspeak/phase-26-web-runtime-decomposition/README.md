# Phase 26 — Web Runtime Decomposition

**Status:** planning (scaffolded 2026-05-31 as the Phase 25 fast-follow; not started; all stories backlog).

Phase 26 breaks the `web_server.py` monolith (5,620 lines, ~125 routes inline in
one `_create_app()`, 40+ constructor callbacks) into cohesive route modules and
a shared runtime context — behavior-preserving at every step. It runs after
Phase 25 so the auth/bind hardening lands in the monolith once and the refactor
then moves a stabilized surface.

## Where to look first

- `current-phase-status.md` — goal, scope, exit criteria, story table, risks.
- `../phase-25-trust-and-hardening/` — the prerequisite phase (esp. HS-25-02 web auth).
- `../../../holdspeak/web_server.py` — the monolith being decomposed.
- `../../../holdspeak/web_runtime.py`, `../../../holdspeak/web_requests.py` — runtime orchestration + request DTOs.

## Phase boundaries

This phase owns the structure of the web runtime only: route modularization and
callback-wiring cleanup, with the existing web test suite as the regression
gate. It does **not** change the API surface, add endpoints, alter auth behavior
(inherited from Phase 25), or touch the Astro frontend, menubar, or TUI beyond
their calls into the runtime.
