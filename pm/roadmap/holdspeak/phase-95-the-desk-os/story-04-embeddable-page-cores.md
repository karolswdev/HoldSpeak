# HS-95-04 — Embeddable page cores

- **Project:** holdspeak
- **Phase:** 95
- **Status:** backlog
- **Depends on:** HS-95-02
- **Unblocks:** HS-95-05, HS-95-06, HS-95-07, HS-95-08

## Problem

The flat pages fetch their own data through the shared `lib/api.ts` client
and `useResource`, so their cores are portable — but their chrome is not.
`PageHero`/`WorkroomBar` assume a flat page (they read routing state and
render document chrome), and `styles/react-app.css` page styling collides
with `desk.css` inside a window. Without a clean extraction pattern, each
re-homing story would improvise its own, and the desk would inherit sixteen
inconsistent embeddings.

## Scope

- In:
  - the pattern: each page splits into a chrome-free core component
    (props-driven, no `useLocation`, no `PageHero`/`WorkroomBar`, no
    `.page-wrap` classes) and a thin flat-route wrapper that keeps today's
    page working;
  - the style seam: core styles that render correctly under both shells —
    scoped classes (or the desk-window scope) so `react-app.css` document
    chrome never leaks into windows;
  - the workroom-context bridge inverted: cores accept an optional context
    prop; the desk passes it directly instead of encoding `?room=` into a
    URL; flat wrappers keep decoding it for deep links;
  - the pattern proven end to end on two pages of different weight:
    ActivityPage (read-mostly) and CommandsPage (form-bearing), each
    rendering in a desk window and on its flat route from one core;
  - a short authoring note in `web/README.md`: how to extract a core, the
    style rules, the context prop.
- Out:
  - the remaining pages (their stories re-home them);
  - deleting flat routes (HS-95-08 decides their end state);
  - visual redesign of page content beyond what the seam requires.

## Acceptance criteria

- [ ] The core/wrapper pattern exists with a typed contract (context prop,
      no router coupling in cores) and is written down in `web/README.md`.
- [ ] ActivityPage and CommandsPage each render from one core in both
      hosts; the flat routes are pixel-equivalent to before (screenshot
      diff) and the desk windows carry no document chrome.
- [ ] No `react-app.css` page-chrome selector applies inside a desk window
      (verified by a style-leak test or targeted assertion).
- [ ] Cores never read `useLocation`; grep-level guard or lint rule
      enforces it for `web/src/pages/cores/` (or the chosen home).
- [ ] Data behavior is unchanged: same requests, same `useResource`
      semantics, proven by existing page tests passing against the wrappers.
- [ ] A window hosting a core unmounts cleanly on close and on
      minimize-with-unmount (the HS-95-02 slot API) with no leaked
      subscriptions (RuntimeBus listeners released).

## Test plan

- `npm --prefix web test` — new core-mount tests (both hosts) for the two
  proof pages; existing page suites green.
- Playwright: open each proof page as a window and as a flat route;
  screenshot both; drive one interaction in each host.
- A style-leak assertion: mount a core in a window and assert the computed
  style of a marker element matches the desk scope.

## Implementation direction

- Prefer moving files: `pages/XPage.tsx` becomes a 20-line wrapper around
  `pages/cores/X.tsx` (naming per the survey; adjust to repo taste once).
- The context prop mirrors `workrooms/context.ts` types — reuse the codec,
  do not fork it.
- Do not migrate state into `useDesk` in this story; cores keep
  `useResource`. Coordination moves store-ward only where a later story
  needs it (e.g. dictation subject handoff).
- Resist improving pages while extracting; mechanical extraction keeps the
  screenshot-equivalence criterion honest.

## Evidence required

- captured web test run;
- side-by-side screenshots (flat vs window) for both proof pages at 1440;
- the `web/README.md` authoring note in the diff;
- the style-leak assertion output.
