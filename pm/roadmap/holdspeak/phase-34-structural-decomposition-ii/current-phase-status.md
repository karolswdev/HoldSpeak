# Phase 34 — Structural Decomposition II

**Status:** in-progress (opened 2026-06-03). 2/5 stories shipped.

**Last updated:** 2026-06-03 (HS-34-02 shipped — `web/routes/activity.py` → a
`routes/activity/` sub-package; route table byte-identical, suite green 1956/15).

## Goal

Finish the decomposition lineage (Phases 26 / 31 / 32) by sub-splitting the four
files that now dominate the tree — **5,373 lines combined** — into navigable,
single-responsibility packages, **behavior-preserving**. This is the finer route
split Phase 26 explicitly deferred to "later", plus the two biggest non-route
modules. No new features; every import path and every HTTP route stays identical.

## Scope

### In

- **`web/routes/dictation.py` (HS-34-01).** Split the 1,607-line single
  `build_dictation_router(ctx)` into a `routes/dictation/` sub-package by domain —
  intents (`/api/intents/*`), agent context + hooks, the `.hs`/project-doc-suggestion
  routes, block-config CRUD, project-KB, and dry-run — each a `build_*_router(ctx)`
  the package `__init__` composes behind a **stable `build_dictation_router(ctx)`**.
- **`web/routes/activity.py` (HS-34-02).** Split the 1,319-line / 38-handler module
  into a `routes/activity/` sub-package: ledger core, project-rules, connector
  enrichment (incl. GitHub/Jira), meeting candidates, and the plugin-job queue API —
  behind a stable `build_activity_router(ctx)`.
- **`agent_context.py` (HS-34-03).** Decompose the 1,381-line / 46-function module
  into an `agent_context/` package — models (`AgentSession`/`RepoRoot`), the
  session registry, the `.hs` project-context loader, and hook/tmux helpers — with a
  **full re-export `__init__`** so `from holdspeak.agent_context import X` is
  unchanged.
- **`intel.py` (HS-34-04).** Decompose the 1,066-line module into an `intel/`
  package — models (`ActionItem`/`IntelResult`), provider resolution + egress
  posture, JSON parsing/coercion, and the `MeetingIntel` engine — full re-export.
- **Phase closeout (HS-34-05).** Re-verify the route-table invariant + the full
  suite, ruff-clean, write `final-summary.md`.

### Out

- **New behavior / features / API changes.** Routes keep their path + method;
  modules keep their public symbols. The only deletions are dead intra-file
  duplication exposed by the split.
- **`meetings.py` / `system.py` / `db/activity.py`.** Already repository-shaped
  (db) or below the pain threshold; not selected for this phase.
- **The PMO corpus + frozen history.** Untouched.

## Exit criteria (evidence required)

- [x] `web/routes/dictation.py` is a `routes/dictation/` sub-package; the route
      table is byte-identical (same paths/methods); `build_dictation_router` import
      unchanged. (HS-34-01) ✅
- [x] `web/routes/activity.py` is a `routes/activity/` sub-package; route table
      identical; `build_activity_router` import unchanged. (HS-34-02) ✅
- [ ] `agent_context.py` is an `agent_context/` package with a full re-export
      `__init__`; no caller import changed. (HS-34-03)
- [ ] `intel.py` is an `intel/` package with a full re-export `__init__`; no caller
      import changed. (HS-34-04)
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout; the
      app route table is asserted unchanged; every touched tree ruff-clean.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-34-01 | Split `web/routes/dictation.py` → `routes/dictation/` | done | [story-01-dictation-routes-split.md](./story-01-dictation-routes-split.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-34-02 | Split `web/routes/activity.py` → `routes/activity/` | done | [story-02-activity-routes-split.md](./story-02-activity-routes-split.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-34-03 | Decompose `agent_context.py` → package | not-started | [story-03-agent-context-package.md](./story-03-agent-context-package.md) | — |
| HS-34-04 | Decompose `intel.py` → package | not-started | [story-04-intel-package.md](./story-04-intel-package.md) | — |
| HS-34-05 | Phase closeout + final-summary | not-started | [story-05-closeout.md](./story-05-closeout.md) | — |

## Where we are

Opened 2026-06-03 right after Phase 33 closed + merged (PR #9). The 2026-06-02
engineering review (which drove 31/32) is fully closed; this phase is the
*self-initiated* continuation of the decomposition lineage, discharging Phase 26's
named follow-up ("the three large route modules could be sub-split if they impede
navigation later") and taking the two biggest non-route modules with it. All
non-hardware-gated.

## Pickup order

1. HS-34-01 — `routes/dictation/` split. **✅ done (2026-06-03).**
2. HS-34-02 — `routes/activity/` split (same pattern; bigger handler count). **✅ done (2026-06-03).**
3. HS-34-03 — `agent_context/` package (proven Phase-31 re-export pattern). **◀ next.**
4. HS-34-04 — `intel/` package (same pattern).
5. HS-34-05 — closeout + final-summary.

The two route splits share a **route-table invariant** check (the app's full route
list, paths+methods, must be identical before/after); the two module-package splits
share the Phase-31 re-export + monkeypatch-target lessons.

**HS-34-01 shipped** (2026-06-03): `web/routes/dictation.py` (1,607L) → a
`routes/dictation/` sub-package (intents / agent / project_docs / blocks / kb /
pipeline + a ctx-free `_helpers.py`), composed behind a stable
`build_dictation_router(ctx)` via `include_router`. The shared in-memory
project-doc-suggestion store is threaded explicitly to the three groups that touch
it. Route table byte-identical (26 routes, hash unchanged); committed
`test_dictation_routes_split.py` locks it (the phase's shared invariant). Suite
green 1954/15; package ruff + F821 clean.

**HS-34-02 shipped** (2026-06-03): `web/routes/activity.py` (1,319L / 38 handlers)
→ a `routes/activity/` sub-package (ledger / rules / enrichment / candidates /
plugin_jobs), composed behind a stable `build_activity_router(ctx)`. Simpler than
the dictation split — every payload shaper is single-group, so no shared state to
thread. Route table byte-identical (38 routes, hash `d4332051064ff059` unchanged);
committed `test_activity_routes_split.py` locks it. Suite green 1956/15; package
ruff + F821 clean.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A moved handler/helper drops a relative import or a late-bound `ctx`/symbol | Medium | Run `ruff --select F821` on each new module; the **full** suite is the gate (it caught Phase 26's late-binding + `ctx`-shadow bugs) | A route 500s, or an import error in the suite |
| Route table silently changes (a handler lost in the move) | Medium | Assert the app's full `(path, method)` route set is identical before/after (a committed test or a documented diff) | The route-count/diff check fails |
| A test monkeypatches a symbol by its old module path | Medium | Phase-31 lesson — monkeypatch targets follow the symbol; grep tests for the moved module name + re-export from `__init__` | `monkeypatch.setattr` AttributeError |
| Over-splitting hurts navigability instead of helping | Low | Split by *domain seam* (the route-path prefixes / the docstring clusters), not by line count; stop at the natural groups | A module with one tiny function and no cohesion |

## Decisions made (this phase)

- 2026-06-03 — **Phase scope = the 4 user-named targets** (dictation routes,
  activity routes, `agent_context`, `intel`) + closeout; `meetings.py`/`system.py`
  left as-is — user (chose "Structural Decomposition II" from the next-phase menu).
- 2026-06-03 — **Package + full re-export** (not a façade module) for
  `agent_context`/`intel`, mirroring the Phase-31 db split — so import paths are
  unchanged and the package is the unit of navigation.

## Decisions deferred

- Whether `agent_context` becomes a *state class* vs. a *function package* —
  trigger: HS-34-03 — default: a **package** of domain modules with a re-export
  `__init__` (the helpers — `.hs` loading, hook templates — aren't session state, so
  a single class would be a false grouping).
- Whether to also sub-split `meetings.py`/`system.py` — trigger: post-phase —
  default: no (below the pain threshold; revisit only if navigation suffers).
