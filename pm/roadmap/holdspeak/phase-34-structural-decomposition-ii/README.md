# Phase 34 — Structural Decomposition II

**Status:** in-progress (opened 2026-06-03; runs after Phase 33).

The twin of Phases 26 (web-server), 31 (db), and 32 (web-runtime). Those phases
tamed the biggest god-objects; this one finishes the **explicitly-deferred** finer
split Phase 26 named in its own follow-ups ("the three large route modules could be
sub-split if they impede navigation later") plus the two largest remaining
non-route modules. Four files now dominate the tree at **5,373 lines combined**:

1. `web/routes/dictation.py` — **1,607 lines, ~26 route handlers** in one
   `build_dictation_router(ctx)` factory: intent controls, agent-context/hooks, the
   `.hs`/project-doc-suggestion routes, block-config CRUD, project-KB, and dry-run.
2. `web/routes/activity.py` — **1,319 lines, 38 route handlers**: the activity
   ledger, project-rules, connector enrichment (incl. GitHub/Jira), meeting
   candidates, and the plugin-job queue API.
3. `agent_context.py` — **1,381 lines, 46 module-level functions**: the agent-session
   registry, the `.hs` project-context loader, and hook/tmux helpers, all flat.
4. `intel.py` — **1,066 lines**: provider resolution + egress posture, JSON
   coercion/parsing helpers, and the `MeetingIntel` engine in one module.

## Where to look first

- `current-phase-status.md` — goal, scope, exit criteria, story table, risks.
- `../phase-26-web-runtime-decomposition/final-summary.md` — the proven route-module
  pattern (`build_*_router(ctx)` + the route-table invariant) and its named
  follow-up that this phase discharges.
- `../phase-31-database-decomposition/` — the proven module→package + full
  re-export pattern (and its decomposition lessons: dropped relative imports,
  monkeypatch targets following the symbol).

## Phase boundaries

**Behavior-preserving structural refactor only — no new features, no API surface
changes.** Every public import path stays valid (packages re-export their full
surface), every HTTP route stays at the same path/method, and the full route table
is asserted identical. The gate is the **whole** suite (`-k` filters miss the
late-binding / shadow bugs this kind of move surfaces — see Phase 26's lessons),
plus ruff-clean on every touched tree. No hardware needed.
