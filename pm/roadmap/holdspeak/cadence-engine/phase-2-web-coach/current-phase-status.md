# Cadence Phase 2 — The web coach surface

**Status:** done (built + tested; the web bundle builds, 137 cadence/web-server tests green).
**Start here:** `../README.md` (the program chart). Builds on Phase 1 (merged).

**Last updated:** 2026-06-28 (Phase 2 shipped: the `/api/cadence/*` API + the `/cadence` coach page
with prepared next moves, evidence deep-links, lifecycle actions, and egress badges).

## Objective

Make the Phase-1 substrate visible and actionable in the local web runtime: a read API over loops +
their evidence + a prepared next action, lifecycle actions (snooze/kill/close), and a `/cadence`
coach page that shows *Now* (what's due, with the prepared move) and *Open loops* (with evidence
deep-links + an egress badge). Still **no autonomous external side effect** — lifecycle actions are
local; a "next action" that maps to an external connector remains a *draft* (executing it is the
actuator path, Phase 6/7).

## Design decisions

- **Deterministic next-action (no LLM yet).** A pure `next_action.py` maps a loop to its best
  prepared move (proposal → `approve_proposal`; owned action → `create_issue` draft; unowned →
  `assign_owner`; `needs_review` → `review_draft`). The LLM-drafted version is Phase 7.
- **Routes follow the repo seam:** `build_cadence_router(ctx) -> APIRouter`, handlers call
  `get_database()` directly (like the meetings/activity routers), registered in `web_server.py`.
- **Egress honesty:** every loop/response carries `egress: {scope, label}` (Phase 2 reads are
  `local`); the page renders it via `web/src/scripts/egress-badge.js`. **Card CSS is `<style
  is:global>`** (the Astro-scoped-CSS gotcha — scoped CSS never reaches JS-injected DOM,
  [[reference_astro_scoped_css_js_dom]]).

## Stories

| ID | Title | Status |
|----|-------|--------|
| CAD-2-01 | Deterministic next-action generator (`cadence/next_action.py`) | done |
| CAD-2-02 | `/api/cadence/*` routes (status, loops, loop detail, run-now) | done |
| CAD-2-03 | Lifecycle actions (snooze / kill / close) + audit-honest responses | done |
| CAD-2-04 | The `/cadence` coach page (Now + Open loops + Policy) with egress badges | done |
| CAD-2-05 | Tests: next-action unit, route integration, page preflight | done |

## Where we are

**Phase 2 is complete.** `cadence/next_action.py` maps each loop to its prepared move
(proposal→approve, owned action→issue draft, unowned→assign, needs_review→review). The
`build_cadence_router` (`web/routes/cadence.py`, registered in `web_server.py`) exposes
`status`/`loops`/`loops/{id}`/`run-now` + lifecycle `snooze`/`kill`/`close`, each loop carrying its
evidence, the next action, and a `local` egress badge. The `/cadence` page (`cadence.astro` +
`cadence-app.js`, served from `pages.py`) renders *Now* + *Open loops* with deep-link evidence,
egress chips, and one-tap snooze/done/kill — all loop text via `textContent` (source is data, never
markup). **Proof:** 137 tests green (`test_cadence_next_action`, `test_cadence_routes`,
`TestCadenceUiSmoke`, + the full web-server suite); the web bundle builds (15 pages); the Phase-1
no-side-effects guard still passes.

**Next: Phase 3 (agent-blocker push)** — awaiting-response coding-agent sessions → loops + a prepared
reply, delivered via the tmux/`/api/dictation/remote` path.

## Exit criteria

- `GET /api/cadence/loops` returns scored loops with evidence + a prepared next action; lifecycle
  POSTs mutate and reflect honestly; `POST /api/cadence/run-now` projects.
- `/cadence` loads, lists due + open loops with working evidence deep-links + egress badges, and the
  snooze/kill/close buttons drive the API.
- No autonomous external side effect (the Phase-1 guard still passes; the page never executes a
  connector — a next-action is a draft until the actuator path).
- `uv run pytest -q` green; the web bundle builds.
