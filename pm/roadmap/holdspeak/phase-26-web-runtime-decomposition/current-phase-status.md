# Phase 26 — Web Runtime Decomposition

**Status: DONE (frozen 2026-06-01).** 7/7 stories shipped. See
[`final-summary.md`](./final-summary.md). `web_server.py` 5658 → 523 lines (−90.8%);
122 routes unchanged; full suite green (1879). This file is frozen — no further edits.

**Last updated:** 2026-06-01 (HS-26-07 closeout — phase complete; `final-summary.md` written).

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
| HS-26-01 | Router seam + shared web context (pilot: health/state) | done | [story-01-router-seam.md](./story-01-router-seam.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-26-02 | Extract meeting / speaker / intel routes | done | [story-02-meeting-routes.md](./story-02-meeting-routes.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-26-03 | Extract dictation / agent-hook routes | done | [story-03-dictation-routes.md](./story-03-dictation-routes.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-26-04 | Extract activity / connector / plugin-job routes | done | [story-04-activity-routes.md](./story-04-activity-routes.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-26-05 | Extract device / companion / project routes | done | [story-05-device-project-routes.md](./story-05-device-project-routes.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-26-06 | Collapse callback wiring + sync-DB-in-async audit | done | [story-06-collapse-callbacks.md](./story-06-collapse-callbacks.md) | [evidence-story-06.md](./evidence-story-06.md) · [audit](./audit-sync-db-async.md) |
| HS-26-07 | Decomposition closeout (size + regression evidence) | done | [story-07-decomposition-closeout.md](./story-07-decomposition-closeout.md) | [evidence-story-07.md](./evidence-story-07.md) · [final-summary.md](./final-summary.md) |

## Where we are

Opened 2026-05-31. Phase 25's auth/bind changes (HS-25-02) are already in the
monolith, so the refactor moves a stabilized surface.

**HS-26-01 is done:** the seam exists — `holdspeak/web/routes/` package +
`holdspeak/web/context.py` (`WebContext`), with `/health` + `/api/state` migrated
off `_create_app` via `build_core_router` + `app.include_router`. App-level auth
middleware still applies to router routes. No import cycle (test-pinned). Pattern
documented in the module docstrings.

**HS-26-02 is done:** the meeting / speaker / intel cluster — **25 routes** — now
lives in `holdspeak/web/routes/meetings.py` (`build_meetings_router`), moved
verbatim and reading from `WebContext` (grown by 11 lifecycle/action-item
accessors). `web_server.py` dropped from **5658 → 4691 lines** (−967); the 12
now-unused request-model imports were trimmed. Route-inventory diff identical;
full suite green (1879); ruff clean. `broadcast` is late-bound to preserve the
prior `self.broadcast` dynamic dispatch (a test spies via reassignment).

**HS-26-03 is done:** the dictation-pipeline cluster — **26 routes** (4 intent-
control + 22 dictation) plus all its private helpers (project detection,
block-config IO, dry-run, the per-app `project_doc_suggestions` dict, readiness)
— now lives in `holdspeak/web/routes/dictation.py` (`build_dictation_router`),
moved verbatim. `WebContext` grew 5 accessors. `web_server.py` dropped **4691 →
3133 lines** (−1558; cumulative **5658 → 3133**). Route-inventory diff identical;
full suite green (1879); ruff clean.

**HS-26-03 follow-up (post-merge cleanup, behavior-preserving):** the two
deviations called out in `evidence-story-03.md` were addressed properly rather
than left as workarounds — superseding that file's §Deviations notes:
1. **`_GLOBAL_BLOCKS_PATH` duplication removed.** `web_server.py` held a third
   copy of `~/.config/holdspeak/blocks.yaml` (also in `controller.py` and the
   canonical `plugins.dictation.assembly.DEFAULT_GLOBAL_BLOCKS_PATH`). After the
   dictation move it was dead in `web_server`, so it was deleted; `dictation.py`
   now reads the canonical `assembly.DEFAULT_GLOBAL_BLOCKS_PATH` (lazy import, so
   the monkeypatch tests still apply) — the route module no longer reaches into
   the monolith. The 3 web tests now patch `assembly.DEFAULT_GLOBAL_BLOCKS_PATH`.
   (`controller.py`'s separate copy is out of Phase 26's web scope — left as-is.)
2. **`web_ctx` → `ctx`.** The param-rename workaround was replaced by renaming the
   shadowing local (a project-context dict) `ctx` → `project`, so the WebContext
   param is the conventional `ctx`, matching `core.py` / `meetings.py`.

   Full suite still green (1879); route-inventory still identical; ruff clean.

**HS-26-04 is done:** the activity-intelligence cluster — **38 routes** (activity
status/records/rules, enrichment connectors incl. GitHub/Jira, meeting
candidates, plugin-job queue) — now lives in `holdspeak/web/routes/activity.py`
(`build_activity_router`). 6 activity-only helpers were **relocated** into it (out
of `web_server`); `_meeting_callback_payload` + `_parse_iso_datetime` stay shared
(imported). `WebContext` grew 1 accessor (`on_process_plugin_jobs`). `web_server.py`
dropped **3133 → 1817 lines** (−1316; cumulative **5658 → 1817**, −68%).
Route-inventory diff identical; full suite green (1879); ruff clean.
`/api/projects/{project_id}/briefings` left inline (it is a `/api/projects/*`
path → HS-26-05).

**HS-26-05 is done:** the last 26 inline routes moved into 3 cohesive modules —
`routes/pages.py` (7 HTML pages), `routes/system.py` (device-health, runtime +
companion status, settings, `/ws`), `routes/projects.py` (project CRUD + briefings
+ associations, 13). 6 module-level helpers relocated; `WebContext` grew its final
6 accessors. **`web_server.py` is now a thin assembler: 532 lines** (from the
original 5658, **−91%**) — only middleware, lifespan, the StaticFiles mount, the
device-audio WS registration, and `include_router` wiring; **no inline route
handlers**. A relocation path bug (page `__file__` resolution) was caught by the
full suite and fixed. Route-inventory diff identical (122 routes); full suite
green (1879); ruff clean.

**HS-26-06 is done:** `MeetingWebServer.__init__` collapsed from **~30 kwargs to
4** (`callbacks: WebRuntimeCallbacks`, `*`, host/port/auth_token) — all 69
construction sites updated via an AST codemod. The 3 cross-cutting helpers
(`_UnknownDeviceError`, `_meeting_callback_payload`, `_parse_iso_datetime`) were
re-homed to `holdspeak/web/runtime_support.py`, so **no `routes/*` module imports
`web_server`**. The sync-DB-in-async audit is recorded (`audit-sync-db-async.md`):
~174 sync SQLite calls across ~118 async handlers, none on the broadcast path →
**document, no offload** (with a documented re-visit trigger). Route-inventory diff
identical (122); full suite green (1879); ruff clean.

Next: **HS-26-07** — decomposition closeout: confirm the phase exit criteria,
record final size + route-inventory evidence, write `final-summary.md`, close the
phase.

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
