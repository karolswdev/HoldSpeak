# Phase 26 — Web Runtime Decomposition

**Last updated:** 2026-05-31 (phase scaffolded as Phase 25 fast-follow; all stories backlog).

## Goal

Break the 5,620-line `web_server.py` monolith into cohesive route modules and
collapse the 40+ constructor-callback wiring into a shared runtime context, with
**zero behavior change** at each step. The web runtime is the structural
keystone that will rot first and is hardest to test or extend while it is one
file; this phase makes it navigable and safely modifiable — including for the
auth and bind work that lands in Phase 25.

## Scope

### In

- Introduce a route-module structure (`APIRouter` package) and migrate routes
  out of the single `_create_app()` factory, domain by domain.
- Replace the 40+ callbacks passed into `MeetingWebServer` with a shared
  runtime-context object the route modules read from.
- Preserve the API surface exactly (same paths, methods, payloads, status
  codes) at every story boundary.
- End with `web_server.py` as a thin assembler.

### Out

- Auth / bind-guard behavior (that is Phase 25 HS-25-02; this phase keeps
  whatever auth exists working, unchanged).
- New endpoints or response-shape changes.
- The Astro frontend, menubar, and TUI (untouched except where they call the
  runtime).
- Making sync DB calls async beyond the targeted audit story (HS-26-06).

## Exit criteria (evidence required)

- [ ] `web_server.py` is reduced to a thin app-assembler; route handlers live in
      a `routes/` (or equivalent) package, with line-count before/after recorded.
- [ ] The full HTTP/WebSocket API surface is unchanged — proven by the existing
      web tests passing plus a route-inventory diff showing identical paths.
- [ ] `MeetingWebServer`'s callback count is materially reduced via a shared
      context object; the new wiring is documented.
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` is green throughout.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-26-01 | Router seam + shared web context (pilot: health/state) | backlog | [story-01-router-seam.md](./story-01-router-seam.md) | — |
| HS-26-02 | Extract meeting / speaker / intel routes | backlog | [story-02-meeting-routes.md](./story-02-meeting-routes.md) | — |
| HS-26-03 | Extract dictation / agent-hook routes | backlog | [story-03-dictation-routes.md](./story-03-dictation-routes.md) | — |
| HS-26-04 | Extract activity / connector / plugin-job routes | backlog | [story-04-activity-routes.md](./story-04-activity-routes.md) | — |
| HS-26-05 | Extract device / companion / project routes | backlog | [story-05-device-project-routes.md](./story-05-device-project-routes.md) | — |
| HS-26-06 | Collapse callback wiring + sync-DB-in-async audit | backlog | [story-06-collapse-callbacks.md](./story-06-collapse-callbacks.md) | — |
| HS-26-07 | Decomposition closeout (size + regression evidence) | backlog | [story-07-decomposition-closeout.md](./story-07-decomposition-closeout.md) | — |

## Where we are

Scaffolded 2026-05-31 as the explicit fast-follow to Phase 25. Not started; runs
after Phase 25 closes so the auth/bind changes (HS-25-02) land in the monolith
once and the refactor moves the stabilized surface. Each story is a
behavior-preserving migration with the web test suite as the regression gate.

## Pickup order

1. HS-26-01 — establish the router + shared-context pattern on a low-risk pair
   of routes; everything else follows it.
2. HS-26-02..05 — migrate one domain per story (one PR each).
3. HS-26-06 — collapse the callback wiring now that routes are modular; audit
   sync DB calls made from async handlers.
4. HS-26-07 — size/regression evidence + closeout.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A route changes behavior subtly during a move | Medium | Move verbatim; rely on the existing web test suite + a route-inventory diff per story | Any web test fails or a path/method/payload differs from the inventory baseline |
| Shared-context refactor creates import cycles | Medium | Context is a plain data/accessor object with no route imports; routers import it, not vice versa | A circular import appears when wiring a router |
| Phase 25 auth work and this refactor collide | Medium | Sequence after Phase 25 closes; rebase the refactor onto the auth-bearing monolith | Auth gate has to be reimplemented per-router instead of inherited |
| Sync DB calls in async handlers surface latent event-loop stalls when moved | Low | Limit the async audit to HS-26-06; document rather than over-refactor | Moving a handler reveals a blocking call that already harms the WS broadcast cadence |

## Decisions made (this phase)

- 2026-05-31 — Split out from Phase 25 as a separate fast-follow — keep a large
  refactor in a different blast radius from the security work — user.

## Decisions deferred

- Whether to move sync DB access onto a thread pool/async wrapper — trigger:
  HS-26-06 audit findings — default: document the blocking calls and offload
  only those that demonstrably stall the WebSocket broadcast loop.
- Package name/location for the route modules (`holdspeak/web/routes/` vs.
  `holdspeak/routes/`) — trigger: HS-26-01 — default: `holdspeak/web/routes/`.
