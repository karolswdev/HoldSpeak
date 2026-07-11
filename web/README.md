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
