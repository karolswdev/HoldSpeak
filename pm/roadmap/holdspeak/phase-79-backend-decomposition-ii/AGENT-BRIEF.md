# Phase 79 — Agent Brief (read this first)

**Phase 79 — Backend Decomposition II** for HoldSpeak. The desk-era handover's
candidate 2, picked by the owner on 2026-07-03 ("Let's do the backend decomp").
The successor of [Phase 63](../phase-63-backend-decomposition/): the same
disease, the same cure, the same proof standard.

## 0. Mission

The handover named `db/activity.py` (1,596) and `routes/meetings.py` (1,525);
the 2026-07-03 survey corrects the second — Phase 72 already split the meetings
routes into a package. Today's three worst backend monoliths:

- **`holdspeak/db/activity.py` — 1,596 lines.** One `ActivityRepository` class,
  ~45 methods across eight distinct concerns (the ledger, import checkpoints,
  privacy, nudge dismissals, domain rules, project rules, enrichment connectors
  + runs, annotations, meeting candidates).
- **`holdspeak/web/routes/system.py` — 1,299 lines.** One
  `build_system_router` holding five unrelated route families (runtime/device
  health, the coder board, settings GET/PUT, the voice lane
  wake/transcribe/preview/commands-test, the `/ws` socket).
- **`holdspeak/web/routes/primitives.py` — 1,294 lines.** 41 routes over seven
  primitive CRUD families plus the shared run-persist helpers.

Carve all three, **behavior-preserving** (bodies move verbatim; assertions
byte-identical), and extend the Phase-63 backend density guard so the new
shapes cannot regrow. `db/core.py` (1,266) is deliberately OUT: it is the
schema DDL + migration matrix, pinned by the snapshot test — a different
budget conversation, kept as a named watch item.

## 1. The one thing you must not get wrong

**This is a refactor, not a rewrite.** Method bodies move verbatim. The only
permitted test edits are monkeypatch TARGET module paths where a module-level
name moved with its code (each one listed in evidence); every assertion stays
byte-identical. If a move makes you want to improve a body, stop —
improvements are out of scope.

## 2. Traps carried from Phase 63 and 72

- **Patch targets move with the code.** After a carve, `web.routes.system.X`
  patches do nothing if `X` lives in a submodule. Grep the tests for every
  moved module-level name before flipping a story.
- **The API-surface manifest records `module` per route.** Splitting a route
  file changes those fields; regenerate with
  `uv run python scripts/gen_api_surface.py` in the same commit (the accepted
  diff class is module fields only — any path/method diff is a bug).
- **Public constructors stay put.** `from ..routes import build_system_router`
  and `from holdspeak.db.activity import ActivityRepository` keep working: the
  package `__init__` composes and re-exports.
- **The schema snapshot regenerates with the test's literal `r'\\s+'`
  normalizer** if any DB-adjacent move touches it (it should not).

## 3. Rules (the standing set)

PMO gate per commit; evidence file with every done-flip; one PR on branch
`phase-79-backend-decomposition-ii`, merged on conclusion-checked green;
tests via `uv run pytest -q` (full: `--ignore=tests/e2e/test_metal.py`);
cadence per shipping commit (story header + status row + the project README
"Last updated" line).

## 4. The stories

1. **HS-79-01** — `db/activity.py` → the `holdspeak/db/activity/` package
   (concern mixins composing `ActivityRepository`).
2. **HS-79-02** — `routes/system.py` → the `system/` package (five routers
   composed under one `build_system_router`).
3. **HS-79-03** — `routes/primitives.py` → the `primitives/` package (per
   primitive family + the shared run helpers).
4. **HS-79-04** — the density guard extension (lock all three new shapes;
   name `db/core.py` as the watch item).
5. **HS-79-05** — the docs story (ARCHITECTURE_BACKEND_RUNTIME.md + the map).
6. **HS-79-06** — closeout (full suite + manifest + final-summary).
