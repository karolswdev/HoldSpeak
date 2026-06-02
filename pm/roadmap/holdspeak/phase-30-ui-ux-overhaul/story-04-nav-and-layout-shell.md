# HS-30-04 — Navigation + layout shell

- **Project:** holdspeak
- **Phase:** 30
- **Status:** backlog
- **Depends on:** HS-30-01, HS-30-03
- **Unblocks:** HS-30-06, HS-30-07, HS-30-08
- **Owner:** unassigned

## Problem

Every route renders inside `AppLayout.astro` with `TopNav.astro` as the global
chrome. The IA spec (HS-30-01) redefines the navigation model; the foundation
(HS-30-03) gives us Signal tokens. This story rebuilds the shell so all five
routes share one confident, consistent frame before each page is redesigned.

## Scope

### In

- Rebuild `web/src/layouts/AppLayout.astro` to the IA spec: the page scaffold
  (header region, content area, side-rail slot, status/footer), responsive
  behaviour, and the dark Signal canvas.
- Rebuild `web/src/components/TopNav.astro` to the new nav model: route nav,
  active state, the brand mark (`AppMark`/`HoldMark`), runtime/connection status,
  and the local-first signal (e.g. a "local" indicator) — restyled to Signal.
- Decide the **command palette / quick-switcher** question from the IA: implement
  it if the IA calls for one, otherwise record the decision and ship standard nav.
- Ensure the shell is keyboard-navigable and the active route is unambiguous.

### Out

- Per-page content layout (HS-30-06/07/08) — this story owns only the shared frame.
- Component-internal restyle beyond nav/layout (HS-30-05).

## Acceptance criteria

- [ ] `AppLayout.astro` + `TopNav.astro` render the IA-spec shell in Signal; all
      five routes inherit it consistently (screenshots of the shell on ≥2 routes).
- [ ] Active-route state is correct and visible on every route.
- [ ] Responsive: the shell holds at small / medium / large widths (screenshots).
- [ ] The command-palette decision is recorded (implemented per IA, or deferred
      with reason).
- [ ] `npm run build` green; backend sweep green.

## Test plan

- Unit / backend: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Visual: `npm run dev`; screenshot the shell across routes + at 3 widths.
- Build: `npm run build` exit 0.

## Notes / open questions

- Keep the nav data-driven if it already is; don't fork per-page nav markup.
- If a command palette lands, it must be keyboard-first and degrade without JS
  (Alpine is the only interactivity layer).
