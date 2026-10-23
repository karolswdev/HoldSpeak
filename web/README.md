# HoldSpeak Web

One typed Vite/React 19 application for every HoldSpeak browser surface. It
builds into `../holdspeak/static/_built/`; FastAPI serves the hashed assets at
`/_built/` and returns the same `index.html` shell for every product URL.

## Requirements and commands

Node.js 20.19+ or 22.12+ is needed only to build and test, matching Vite 7's
runtime requirement. The shipped runtime stays Python/FastAPI.

```bash
npm install
npm run dev                # Vite development server
npm run typecheck          # strict TypeScript
npm run test:web           # React/Vitest suite
npm run guard:architecture # no framework or selector-bootstrap residue
npm run build              # production output in holdspeak/static/_built/
npm run check              # all of the above in phase-gate order
```

Vite's development server is useful for component work. End-to-end API and
deep-link work should run against the FastAPI application after `npm run build`,
because FastAPI owns authentication and the production `/api/*` and `/ws`
contracts.

## Architecture

- `src/main.tsx` is the only shipped browser entry.
- `src/routes.tsx` is the canonical client route inventory. Heavy routes are
  lazy-loaded.
- `src/components/AppShell.tsx` owns navigation and ambient trust/connection
  state. The Desk and Presence use deliberate immersive shell modes.
- `src/components/signal/` owns accessible controls and interaction styling.
- `src/lib/api.ts` is the only direct `fetch` call site. `src/lib/auth.ts`
  captures a tokenized arrival for the tab, scrubs it from the URL, and attaches
  it to same-hub API and WebSocket traffic.
- `src/runtime/RuntimeBus.tsx` owns the single `/ws` lifecycle.
- `src/pages/` contains route compositions; shared or complex behavior belongs
  in typed feature modules and hooks.
- `src/desk/` remains the Zustand-backed spatial Desk inside the same tree.
- `design-tokens.json` is the token source of truth; `src/styles/tokens.css`
  and `src/lib/tokens.gen.ts` are generated. `styles/global.css` owns
  reset/type/shared state, while `styles/react-app.css` and feature CSS own
  composition. There is no CSS-in-JS design-system fork.

The machine-readable URL/verb/state inventory is
[`docs/WEB_REACT_PARITY_LEDGER.json`](../docs/WEB_REACT_PARITY_LEDGER.json).

## Environment preview

The Floor's eight night environments (including Rainy City and Lantern Garden)
can be reviewed without a hub at
`/_built/atmospheres.html` on the Vite development server. This review entry is
not included in the production build. The shipped picker opens from **Places**
in the dock or **Go → Change places** (⌘/Ctrl+Shift+P), with browser-local
favorites; it also remains in Settings → Wallpaper. **Settle in**
(⌘/Ctrl+Shift+F) quiets navigation while preserving work and capture controls;
Escape restores the full Desk. See [environment notes](../docs/ENVIRONMENTS.md)
for controls, scene behavior, and reproducible visual checks.

## Output and security contract

- `vite.config.ts` must keep `base: "/_built/"` and build only into
  `../holdspeak/static/_built/`.
- Browser routes and API payloads remain stable; React Router does not redefine
  backend contracts.
- API keys never enter browser storage or ordinary response bodies. Model
  profiles carry only shape and secret-state metadata; key values remain in
  owner-only hub secret custody, with per-profile environment variables as a
  headless fallback.
- `localStorage` is only for explicitly device-local preferences such as Desk
  positions, Workbench layout, chat threads, and project-root history.
- New browser network calls go through the typed API client. New live consumers
  subscribe to `RuntimeBus`; they do not open another `/ws`.

## Adding a surface (the Desk OS pattern)

Features do not own surfaces; the OS owns surfaces and features plug into
them (docs/internal/CONSTITUTION.md, Articles I–II). To add or re-home a
surface:

1. **Extract the core** into `src/pages/cores/<Name>Core.tsx`: everything
   the flat page rendered below its hero, exported as
   `function <Name>Core({ hero, scope }: CoreProps)`. Cores are
   host-agnostic — no router hooks, no page chrome classes, no
   `window.location`; scope arrives as a prop
   (`tests/unit/test_page_cores_guard.py` enforces this mechanically).
   The core owns its verbs and hands them to the optional `hero` slot so
   each host chooses the chrome.
2. **Demote the route:** there are no flat wrappers anymore.
   Add one `DEMOTED_ROUTES` row in `src/routes.tsx` mapping the legacy
   path to the surface key (plus a `subjectKind` when deep links carry a
   scope); the path then lands on the Desk with the window open.
3. **Register the window**: add the application to
   `src/desk/applications.ts` with its action, window id, label, glyph,
   route and lazy `surface` core. `SurfaceWindows.tsx` derives `SURFACES`
   from that manifest; menu and Dock entries use the same application row.
   The chrome dispatches through `desk/shell.ts`; the no-exit
   lock (`tests/unit/test_desk_no_exit_guard.py`) forbids desk navigation
   outright.
4. **Compose the surface kit:** a core builds its interior
   from `src/desk/surface/` — `SurfaceVerbs` (one sticky verb bar),
   `SurfaceSection` (hairline + quiet label, never a nested card),
   `SurfaceRows`/`SurfaceRow` (dense honest rows, revealed verbs),
   `SurfaceState` (the one loading/empty/error treatment),
   `SurfaceColumns`/`SurfaceSplit` (@container reflow — the WINDOW is
   the viewport; `.desk-surface-body` is the `surface` container),
   `ConfirmVerb` (destructive verbs are inline two-steps, never
   modals), and the honest formatters (`humanTime`/`deSnake`/
   `presentValue` — unknowns are omitted, not printed). The page
   grammar (`page-grid`, `span-*`, `Panel`, `data-list`/`data-row`,
   `button-row`, `Dialog`, …) is forbidden in cores —
   `tests/unit/test_native_surfaces_guard.py` enforces it and its
   ledger is closed.
5. **Styling rules** (`docs/internal/DESIGN_SYSTEM.md` is the canon):
   component tokens only — `npm run tokens:gate` fails raw colors,
   z-index, and ms literals in component CSS; new recurring values become
   tokens in `design-tokens.json` (then `npm run tokens`), not allow-list
   entries; the focus and pressed state grammars are inherited — never
   hand-roll them; the window material is ONE `:where()` rule — no
   per-window recipes.
6. **The chrome ladder** (see the chrome ladder chapter in
   `DESIGN_SYSTEM.md` is the contract): interiors layer by tone
   (head/rail/well around the body fill), with shared fine rules and quiet
   grouping where needed. Popovers
   render through `DeskMenuList`/`DeskMenuItem` (`src/desk/components/
   DeskMenu.tsx`) — never a hand-rolled menu. Bare `select`/`input`/
   `textarea` elements inside the desk shell inherit the Signal
   control foundation mechanically; never opt a control out of it.
   Scrollbars are the drawn pill — verify HEADED (the headless shell
   suppresses them).
7. **Window grammar** (see the physics floors chapter in
   `DESIGN_SYSTEM.md` is the contract): windows are placed by the OS —
   never hand-position a surface window; its CSS default is only the
   placement seed. A Dock application uses the `dock` metadata in
   `src/desk/applications.ts` (the Dock is the one shelf; floating pills
   are forbidden). The eyebrow prop is
   demoted — window identity is icon + title.


## Design author map

Read the [Constitution](../docs/internal/CONSTITUTION.md) and
[UX Canon](../docs/internal/UX-CANON.md) for owner principles and face rules.
The [Design System](../docs/internal/DESIGN_SYSTEM.md) owns current material
and geometry; `design-tokens.json` owns values. Generate its CSS/TS mirrors
with `npm run tokens`.

Use the public `src/desk/surface/index.ts` barrel and
[surface contract](src/desk/surface/contract.md) for component APIs.
Open `/design/components` for executable examples. With **Builder tools**
on, the menu entry is **Go → Builder → Components**.
Patterns demonstrate forms, reading, lists, conversation and progress;
Controls retains the component catalogue. Local specimen state is labelled;
a reference example is not proof that a production journey uses it.
The separate root `gallery/` site is a product gallery, not this library.

The window frame and compositor own the operating shell:

| Responsibility | Implementation home |
| --- | --- |
| Frame, title, wings, feedback, drag/resize, compact frame | `src/desk/components/DeskWindow.tsx` |
| Active application inventory and lazy cores | `src/desk/applications.ts` |
| Core hosting, frame publication, surface scroll custody | `src/desk/components/SurfaceWindows.tsx` |
| Mounted planes/front authority and motion/arrangement | `src/desk/compositor/live.ts`, `useCompositor.ts` |
| Remote window synchronization | `src/desk/compositor/hubWindows.ts` |
| Current geometry and persistence | `src/desk/store/compositorSlice.ts`, `workspaceStorage.ts` |
| Shared compact viewport rule | `src/desk/useCompactViewport.ts` |
| Interior components, container reflow, task composition | `src/desk/surface/` and the feature core |

The 720px compact frame policy and 560px interior reflow serve different
responsibilities. Interior layouts respond to the named `surface` container.
A canvas, terminal or editor can retain a bounded internal scroller; ordinary
window content has one primary scroller. Do not move user arrangement or
workspace authority into a feature to achieve a visual layout.

`computePlanes().front` is the mounted front-window authority. The frame,
Dock, screen title and keyboard target consume it through their shared
helpers/hooks; an announced remote row cannot substitute for a mounted
frame. Reuse `COMPACT_VIEWPORT_QUERY` for the compact policy in JavaScript.
Do not duplicate the query or infer a second front from an open-row list.

Update docs with the implementation: semantic material changes update the
Design System; public component changes update the surface contract and
matching reference example; host/authority changes update this map. Record
which real consumers adopted a pattern. A local spacing fix needs no canon
rewrite. Label superseded material as history and keep old owner rulings.
The active modernization inventory and observations live in
[the implementation record](../docs/internal/betterment/MODERNIZATION-IMPLEMENTATION-2026-10-22.md).
