# HS-54-01 — The module seam (decide + prove on one cluster)

- **Project:** holdspeak
- **Phase:** 54
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-54-02, HS-54-03, HS-54-04, HS-54-05, HS-54-06
- **Owner:** unassigned

## Problem
Every page loads its app script as one blob via a `?raw` import executed with
`new Function()` (`dictation.astro:791-814`). No page uses ES module imports for its
behavior today, so there is no proven way to split `dictation-app.js` into modules.
Carving 2,900 lines onto an unproven seam is how a refactor phase dies; the seam must
be decided and proven on a small slice first.

## Scope
- **In:**
  - Investigate **why** the `?raw` + `new Function()` loader exists (git history, Astro
    script-processing behavior, hoisting). Record the answer with evidence.
  - Decide the seam: either replace the loader for the dictation page with a bundled
    module entry (an Astro-processed `<script>` with imports), or keep the loader and
    define how source modules compose under it. The decision and its rationale go in
    the evidence file and feed HS-54-05.
  - Prove it: extract **one small cluster** — suggested: the discovery nudge (cluster
    13, `dictation-app.js:2541-2594`, five functions, two localStorage keys) — into
    `web/src/scripts/dictation/` as a real module with identical behavior.
- **Out:** carving any other cluster (HS-54-02); markup/styles (HS-54-03); touching
  other pages' loaders.

## Acceptance criteria
- [ ] The loader question is answered with evidence (why it exists; what breaks
      without it, if anything).
- [ ] The chosen seam is implemented for the dictation page and one cluster runs
      through it with identical behavior (nudge shows/dismisses/persists exactly as
      before; same localStorage keys).
- [ ] Existing page-content + dictation integration tests pass **unmodified**.
- [ ] `npm run build` clean; 0 `_built/` tracked; the page works in a live runtime.

## Test plan
- Full relevant slice: `uv run pytest -q tests/integration -k "dictation"` then the
  full suite (`uv run pytest -q --ignore=tests/e2e/test_metal.py`).
- Manual: load `/dictation`, verify the discovery nudge behavior (show conditions,
  dismiss-per-root, global disable) is unchanged; screenshot.

## Notes / open questions
- If the answer is "the loader must stay", the module split still happens — the
  evidence must show how modules compose under it (build-time composition is fine);
  what is forbidden is 2,900 lines staying in one file because the seam was hard.
