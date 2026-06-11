# HS-54-02 — Behavior modules (carve dictation-app.js)

- **Project:** holdspeak
- **Phase:** 54
- **Status:** backlog
- **Depends on:** HS-54-01
- **Unblocks:** HS-54-03, HS-54-04, HS-54-06
- **Owner:** unassigned

## Problem
`web/src/scripts/dictation-app.js` is 2,967 lines: ~73 top-level functions in 15
clusters (blocks, readiness, KB, `.hs/` + guided setup, runtime knobs, memory +
learning, journal + replay, dry-run + moment-of-truth, agent context/hooks, project
root, two nudge systems, init) sharing mutable state objects and ~300+ DOM queries.
Every dictation feature lands in this one file; navigation and review cost grows with
each phase.

## Scope
- **In:**
  - Carve the remaining clusters into single-concern ES modules under
    `web/src/scripts/dictation/` on the HS-54-01 seam. Suggested map (merge/split with
    evidence if the natural seams differ): `core.js` (shared state, `api`, escape/clone
    utils, `activateSection` tab switching), `blocks.js`, `readiness.js`,
    `knowledge.js` (KB + `.hs/` + guided setup + doc suggestion), `runtime.js`,
    `memory.js` (corrections + learning digest), `journal.js` (incl. replay + latency
    strip), `dryrun.js` (incl. moment-of-truth ritual), `agent.js` (agent context +
    hooks + project-root override + recent roots), `nudges.js` (discovery + activity
    pre-briefing), `init.js` (event wiring, loaders, the 10s agent-context poll).
  - Explicit imports/exports replace implicit global reference. Shared state lives in
    **one** module (`core.js`); no duplication.
  - Identical behavior: same endpoints, same localStorage keys
    (`holdspeak.projectRootOverride`, `.recentProjectRoots`, `.knNudgeDisabled`,
    `.knNudgeDismissed`, `.anPin`), same DOM queries, same init order, same poll.
  - No module over ~600 lines.
- **Out:** renaming DOM ids/classes; changing any fetch shape; markup/styles
  (HS-54-03); behavior "fixes" of any kind.

## Acceptance criteria
- [ ] `dictation-app.js` is gone (or reduced to a thin entry) and the behavior lives in
      single-concern modules, none over ~600 lines.
- [ ] Init order and the 10s `loadAgentContext` interval are preserved exactly.
- [ ] All dictation integration + e2e tests pass **unmodified**; full suite green.
- [ ] `npm run build` clean; 0 `_built/` tracked.

## Test plan
- `uv run pytest -q tests/integration -k "dictation"`, the dictation e2e files, then
  the full suite (`uv run pytest -q --ignore=tests/e2e/test_metal.py`).
- Manual live-runtime pass across tabs whose JS moved (blocks CRUD, KB save, `.hs/`
  guided setup, runtime save, correction add/delete, journal filter + replay, dry-run +
  moment-of-truth, agent hooks render, project-root override, both nudges).

## Notes / open questions
- The hidden `CommandPreview` copy-delegator and `wireCopyCommandButtons` document
  delegation must keep working for JS-rendered copy buttons — they are easy to orphan
  in a module split.
