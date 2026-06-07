# Evidence — HS-47-02: In-app explainer + inviting empty states

**Date:** 2026-06-07. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-47-project-kb-legibility`.

## What shipped

Both project-knowledge surfaces went from a bare lede + grid/textarea to a
teaching surface: a what/why/worked-example explainer on each, and an inviting
empty state with a one-click starter. Presentation only; the pipeline is
untouched.

### The explainers (static markup, scoped CSS)

Each surface (`view-kb`, `view-hs` in `web/src/pages/dictation.astro`) carries a
`.kn-explainer` card with a Signal eyebrow ("Project knowledge · Facts" /
"Project knowledge · Context"), a one-line what, a why paragraph that names the
companion part, and a `.kn-example` panel that shows the mechanism concretely:

- **Facts:** `stack = Rails 7 + Postgres 16` + template `Follow our stack:
  {project.kb.stack}` → typed `Follow our stack: Rails 7 + Postgres 16`. Shows the
  verbatim, no-LLM substitution.
- **Context:** `.hs/terms.md` ("product is Holdr; British spelling") + "you say:
  color picker is done" → rewrite "the Holdr colour picker is complete." Shows
  guidance shaping a rewrite, not substitution.

These are static, so the scoped `<style>` applies directly (no injection trap).
The literal `{project.kb.stack}` is written as a JS-string expression
(`{`...`}`) so Astro renders the braces instead of evaluating them.

### The empty states (static markup, toggled by JS)

To dodge the Astro scoped-CSS-on-injected-DOM trap, the empty states are static
markup whose `hidden` attribute is toggled by `dictation-app.js` (never
re-rendered via `innerHTML`):

- `#kb-empty` ("No facts yet") shows when a project is detected and has no facts.
  `renderKBRows()` toggles it and clears the rows host. Actions: "Use starter
  facts" (existing `createStarterKB`) and "Add one manually" (`kbAdd`).
- `#hs-empty` ("No project context yet") shows when a project is detected and
  `.hs/` does not exist yet. `renderHSFileList()` toggles it. Action: "Start with
  an example" (`hsLoadExample`) loads an example `instructions.md` into the editor
  **unsaved** — the user reviews and clicks Save, honoring the
  never-write-without-approval rule. No new write primitive, no endpoint.

Scoped CSS for `.kn-explainer`, `.kn-example`, and `.kn-empty` was added to the
page `<style>` (all static or static-toggled markup, so it applies).

### Focus-safe

`hsLoadExample` uses `scrollIntoView` (honoring `prefers-reduced-motion`) but does
**not** call `.focus()` — the dictation flow is sacred, enforced by
`test_moment_affordance_present_and_focus_safe` (the dictation bundle must contain
zero `.focus()`). An initial version called `.focus()`; the guard caught it and it
was removed. Bundle now has 0 `.focus()`.

## Tests run

- New page-content tests (in `tests/integration/test_web_dictation_cockpit.py`):
  `test_dictation_surfaces_carry_the_knowledge_explainer` and
  `test_dictation_surfaces_have_teaching_empty_states` assert the explainer
  markers, the worked-example, both empty states + their one-click actions, and
  the `.kn-empty` scoped-CSS guard.
- Targeted: `uv run pytest -q -k "dictation or doc_drift or link"`
  → **369 passed, 5 skipped**.
- Full-suite gate: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → **2367 passed, 17 skipped** (exit 0).
- Build: `(cd web && npm run build)` clean; **0** `_built/` tracked.

### Screenshot-verify (the trap guard)

Booted a real server over a temp DB (no mic, no LLM) and captured both surfaces
with Playwright. Both render correctly with the scoped CSS applied: the explainer
cards with their worked-example panels (the `{project.kb.stack}` literal renders),
and the teaching empty states with the icon, copy, example chip, and one-click
actions. Confirmed the toggled DOM is styled, not just present in the bundle.

## Acceptance criteria

- [x] Each surface has a what/why/example explainer consistent with the HS-47-01
      model and accurate per the Phase-46 facts.
- [x] Each surface has an inviting, teaching empty state with a one-click starter;
      no bare grid/textarea on first visit.
- [x] Premium UX bar met; reduced-motion safe; nothing steals focus (0 `.focus()`).
- [x] Behavior unchanged; page-content tests assert the markers; build clean; 0
      `_built/` tracked.
