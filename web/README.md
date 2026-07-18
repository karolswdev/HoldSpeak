# HoldSpeak Web

One typed Vite/React 19 application for every HoldSpeak browser surface. It
builds into `../holdspeak/static/_built/`; FastAPI serves the hashed assets at
`/_built/` and returns the same `index.html` shell for every product URL.

## Requirements and commands

Node.js 20 or newer is needed only to build and test. The shipped runtime stays
Python/FastAPI.

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

- `src/main.tsx` is the only browser entry.
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
- `styles/tokens.css` is the Signal source of truth. `styles/global.css` owns
  reset/type/shared state, while `styles/react-app.css` and feature CSS own
  composition. There is no CSS-in-JS design-system fork.

The machine-readable URL/verb/state inventory is
[`docs/WEB_REACT_PARITY_LEDGER.json`](../docs/WEB_REACT_PARITY_LEDGER.json).

## Output and security contract

- `vite.config.ts` must keep `base: "/_built/"` and build only into
  `../holdspeak/static/_built/`.
- Browser routes and API payloads remain stable; React Router does not redefine
  backend contracts.
- API keys never enter browser storage or response bodies. Runtime profiles
  carry only shape and `requires_key`; the key remains an environment variable
  on the hub.
- `localStorage` is only for explicitly device-local preferences such as Desk
  positions, Workbench layout, chat threads, and project-root history.
- New browser network calls go through the typed API client. New live consumers
  subscribe to `RuntimeBus`; they do not open another `/ws`.

## Adding a surface (the Desk OS pattern, HS-95-04)

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
2. **Keep the flat route** as a thin wrapper: `.page-wrap` + `PageHero`
   (verbs into `hero`) around the core. Until HS-95-08 demotes routes,
   this keeps deep links pixel-identical.
3. **Register the window**: add one row to `SURFACES` in
   `src/desk/components/SurfaceWindows.tsx` (shell key, window id, title,
   glyph, lazy core). The chrome menu and the tool shelf dispatch through
   `desk/shell.ts` — a registered key opens the window in-world; an
   unregistered one falls back to the legacy route.
4. **Style seam**: window-hosted cores render inside
   `.desk-surface-body`; never reintroduce `.page-*` chrome classes in a
   core.
