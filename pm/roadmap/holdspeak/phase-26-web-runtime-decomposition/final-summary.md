# Phase 26 — Web Runtime Decomposition — Final Summary

**Closed:** 2026-06-01. **Outcome:** delivered. **Stories:** 7/7 done.

## What the phase set out to do

Break the 5,620-line `holdspeak/web_server.py` monolith (≈125 routes inline in one
`_create_app`, ~30 constructor callbacks) into cohesive route modules behind a
shared runtime context, **behavior-preserving at every step**, and collapse the
constructor callback bag.

## What shipped

| Story | Result |
|---|---|
| HS-26-01 | Seam: `holdspeak/web/routes/` package + `WebContext`; pilot `/health` + `/api/state` |
| HS-26-02 | `routes/meetings.py` — meeting/speaker/intel (25 routes) |
| HS-26-03 | `routes/dictation.py` — dictation/agent-hook/intent (26) + follow-up (drop duplicate `_GLOBAL_BLOCKS_PATH`, restore `ctx` naming) |
| HS-26-04 | `routes/activity.py` — activity/connector/plugin-job (38) |
| HS-26-05 | `routes/{pages,system,projects}.py` — the last 26 routes; `web_server.py` becomes a thin assembler |
| HS-26-06 | Constructor 30→4 params (`WebRuntimeCallbacks`); routes fully decoupled from `web_server`; sync-DB-in-async audit |
| HS-26-07 | This closeout |

## End-state metrics

- **`web_server.py`: 5658 → 523 lines (−90.8%).** It now holds only: the
  `WebSocketManager`, `BroadcastMessage`, `WebRuntimeCallbacks`, the
  `MeetingWebServer` class (lifecycle/`broadcast`/`start`/`stop`/`_create_app`
  assembler), and `_create_app` = middleware (auth gate) + lifespan + `/_built`
  StaticFiles mount + device-audio WS registration + `include_router` wiring.
  **No inline route handlers.**
- **`holdspeak/web/` package: ~5552 lines** across:
  `context.py` (WebContext, 70), `runtime_support.py` (shared helpers, 62), and
  `routes/`: `core.py` (2 routes), `meetings.py` (25), `dictation.py` (26),
  `activity.py` (38), `pages.py` (7), `system.py` (6), `projects.py` (13).
- **`MeetingWebServer.__init__`: ~30 kwargs → 4** (`callbacks: WebRuntimeCallbacks`,
  `*`, `host`, `port`, `auth_token`).
- **No `routes/*` module imports `web_server`** — cross-cutting helpers live in
  `web/runtime_support`.

## Exit criteria — re-checked

- [x] `web_server.py` reduced to a thin app-assembler; handlers live in `routes/`
      (line-count before/after recorded above). — HS-26-05, HS-26-07
- [x] Full HTTP/WebSocket API surface unchanged — existing web tests pass +
      route-inventory diff shows **identical 122 paths/methods** vs the pre-phase
      `origin/main` baseline (`f77c2d9`), at every story boundary. — all stories
- [x] `MeetingWebServer`'s callback count materially reduced via a shared context
      object; wiring documented. — HS-26-06 (`WebRuntimeCallbacks` + `WebContext`)
- [x] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout —
      **1879 passed, 13 skipped** at closeout (and at every story).

## Verification at closeout

```
$ git show f77c2d9:holdspeak/web_server.py | wc -l   # 5658
$ wc -l holdspeak/web_server.py                       # 523
$ uv run pytest -q --ignore=tests/e2e/test_metal.py   # 1879 passed, 13 skipped
$ diff <baseline app.routes> <current app.routes>     # identical, 122 routes
$ uv run ruff check holdspeak/web/ holdspeak/web_server.py   # All checks passed!
```

(One pre-existing `current_time` F841 in `meeting_session.py:1277` is unrelated to
this phase and predates it.)

## Conventions established (carried forward)

- Route modules read all server state from `WebContext` (param named `ctx`);
  shadowing locals are named `project`, never `ctx`.
- Single-domain helpers are relocated into their route module; only genuinely
  cross-cutting, server-agnostic helpers live in `web/runtime_support`.
- After moving a module, re-anchor any `Path(__file__)` to the package dir.
- The **full** test suite (not a narrow `-k`) is the gate — it caught a broadcast
  late-binding regression (HS-26-02), a `ctx` shadow bug (HS-26-03), and a page
  `__file__` path bug (HS-26-05).

## Decisions of record

- 2026-05-31 — Split from Phase 25 as a separate fast-follow (different blast
  radius from the security work) — user.
- 2026-05-31 — `routes/meetings.py`/`dictation.py`/`activity.py` kept as single
  modules despite size; a finer split was deferred (not needed for navigability).
- 2026-06-01 — Full constructor collapse (vs. documenting the bag) — user choice;
  all 69 construction sites updated via AST codemod.
- 2026-06-01 — Sync DB calls in async handlers: **documented, not offloaded** (none
  stalls the broadcast loop); see `audit-sync-db-async.md` for the re-visit trigger.

## Follow-ups beyond this phase

- The three large route modules (`activity`/`dictation`/`meetings`) could be
  sub-split if they impede navigation later — optional, not required.
- Resume the paused phases now that the web runtime is navigable: Phase 24 (AI PI
  companion productization) and Phase 16 (first real plugin). Phase 15
  (out-and-about) remains auth-unblocked by HS-25-02.
