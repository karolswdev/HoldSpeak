# Web frontend architecture

**Status:** canonical since Phase 95 (the Desk OS; supersedes the Phase 91
route world).

HoldSpeak Web is one typed Vite/React 19 application whose one surface is
the Desk (docs/internal/CONSTITUTION.md, Article I). Three routes render:
`/` (the Desk), `/welcome` (arrival), `/presence` (the theater). Every
other product path is a demoted deep link that lands on the Desk with the
matching window open. The world layer renders on a WebGL (pixi v8) scene
graph fed by the Zustand desk store; windows are DOM, composited above.

## Request and render flow

```mermaid
flowchart LR
  Browser[Browser URL] --> FastAPI[FastAPI explicit SPA route]
  FastAPI --> Shell[static/_built/index.html]
  Shell --> Router[React Router]
  Router --> Desk[The Desk surface]
  Router -- demoted path --> Redirect[SurfaceRedirect]
  Redirect -- openSurfaceWhenReady --> Windows[Desk windows]
  Desk --> GL[WebGL world stage]
  Desk --> Windows
  Windows --> API[Typed apiFetch]
  API --> Backend["/api routes"]
  Runtime[RuntimeBusProvider] --> WS["/ws"]
  WS --> Desk
```

FastAPI intentionally registers explicit browser paths instead of a global
catch-all, so an added API route can never be swallowed by the SPA. Keep
`holdspeak/web/routes/pages.py::SPA_ROUTES` aligned with `routes.tsx`
(PRODUCT_ROUTES + DEMOTED_ROUTES). Both `/history` and `/meetings` deep-link
to the Meetings window; `/desk` is a compatibility alias for the root Desk.

## Source boundaries

```text
web/src/main.tsx                    one entry and provider composition
web/src/routes.tsx                  three surfaces + the demoted deep links
web/src/components/AppShell.tsx     the one immersive frame
web/src/components/signal/          semantic shared control grammar
web/src/pages/cores/                 host-agnostic surface cores
web/src/features/                    bounded feature models and hooks
web/src/desk/                        the OS: GL stage, windows, dock, shell
web/src/desk/gl/                     the WebGL world renderer (store-fed)
web/src/desk/shell.ts                surface dispatcher + navigation seam
web/src/desk/components/SurfaceWindows.tsx  the SURFACES table (core → window)
web/src/lib/api.ts                  only direct fetch call site
web/src/lib/auth.ts                 query-token bootstrap and forwarding
web/src/runtime/RuntimeBus.tsx      only product /ws owner
web/src/styles/                      tokens, reset and named compositions
```

Mechanical locks: `tests/unit/test_desk_no_exit_guard.py` (the desk never
navigates; three rendered routes; the flat shell stays dead),
`tests/unit/test_page_cores_guard.py` (cores stay host-agnostic), the
Phase 73 desk locks (no modal roles on the desk, no browser mic in the
desk tree, byte-stable position storage), and the Phase 96 design-system
locks (`npm run tokens:check` + `tokens:gate` — generated tokens and no
raw values in component CSS; `tests/unit/test_design_system_guard.py` —
the state contract stays true). The design system itself is canon in
`docs/internal/DESIGN_SYSTEM.md`: three-layer tokens from
`web/design-tokens.json`, the generated TS mirror feeding window physics
and GL palettes, the component state matrices, and the recorded Radix
decision.

Route-local state stays in the route. State shared across a feature can move to
a feature hook/reducer. State shared across routes may use Zustand when it has a
real cross-route lifetime. Do not add a store merely to avoid passing props.

## Interaction grammar

Signal components use native browser semantics and add DeskOS hierarchy,
material, spacing and motion. A route arranges controls; it does not redefine
their target size, focus, disabled, loading or status behavior. Primary actions
are 44 px high. Dense subordinate actions are 36 px high and retain at least a
24 px effective target.

Use `Field` for associated labels, descriptions and errors; `Dialog` for modal
focus containment/return; `InlineMessage` for live success/error feedback; and
`StatusPill` for states that must not rely on color alone. Reduced-motion rules
are global. The living contract is `/design/components`.

## API, authentication and secrets

All product HTTP calls use `apiFetch`, `apiBlob`, or the low-level `apiRequest`
from `src/lib/api.ts`. A browser arriving with `?token=…` captures the token in
tab-scoped `sessionStorage`, removes it from the address bar, and forwards it as
`X-HoldSpeak-Token`. The Runtime bus includes the same credential in its
handshake URL. This is a hub access token, not a model-provider key.

Provider/API keys never reach Web state or storage. A Runtime Profile exposes
only its safe shape and whether a key must exist on the hub. Any new editor that
adds a secret field violates the architecture.

## The one runtime bus

`RuntimeBusProvider` owns one `/ws` connection for the entire React tree. It
normalizes `{type, data}` frames, exposes connection state, sends the 15-second
keepalive, backs off reconnects, and removes listeners on unmount. Live,
Presence, arrival, and the Desk Record orb subscribe to that provider. The
device-audio PSK socket is a separate hardware transport and is not a product
runtime-bus consumer.

## Testing and drift locks

`npm run check` runs the architectural census, strict typecheck, all React/Desk
tests, and the production build. The architecture guard rejects old framework
directives/dependencies, selector-owned bootstraps, runtime HTML injection, and
network calls that bypass the typed client. FastAPI integration tests assert
that every direct link returns the same shell. The Phase-91 parity ledger pins
each route's verbs, endpoints, states, storage, WebSocket use, and focus seams.

When adding a surface (see web/README.md for the full pattern):

1. Extract a host-agnostic core in `src/pages/cores/` and register a
   `SURFACES` row in `src/desk/components/SurfaceWindows.tsx`.
2. If the surface needs a deep link, add a `DEMOTED_ROUTES` row in
   `src/routes.tsx` and an explicit shell path in
   `holdspeak/web/routes/pages.py`.
3. Compose Signal primitives; add a bounded feature hook/model when behavior
   becomes non-trivial.
4. Add core/window tests; the demotion table test pins the deep link.
5. Run `npm run check` and the relevant backend API integration tests.
