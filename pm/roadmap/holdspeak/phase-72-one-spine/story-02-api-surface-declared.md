# HS-72-02 — The API surface, declared

- **Status:** done
- **Priority:** HIGH (the map every later rename/split is proven against)
- **Depends on:** —
- **Evidence:** [evidence-story-02.md](./evidence-story-02.md)

## Goal

Make the HTTP API surface a declared, versioned artifact instead of an
emergent property of 13 routers. Today 12 of 13 routers hardcode full
`/api/...` paths per-decorator (only `cadence.py` uses a prefix), and the only
way to learn which routes the iPad consumes is to grep
`HTTPDesktopClient*.swift`. `docs/ARCHITECTURE.md` guessed — and undercounts
the iPad client by roughly half. After this story, the surface is generated
from the app, consumers are declared per route, and drift fails a test.

## Scope

- **In:** a generator that walks the assembled FastAPI app and emits a
  machine-readable manifest (path, method, router module, consumer set) +
  a committed human-readable `docs/API_SURFACE.md`; consumer extraction
  scripts (grep `web/src` for fetch/WS paths; grep
  `apple/Sources/Providers/Desktop/` for request paths); snapshot tests both
  directions (app ⊆ manifest, manifest ⊆ app, Swift calls ⊆ manifest, web
  calls ⊆ manifest); normalizing routers onto `APIRouter(prefix=...)` where
  the diff is mechanical.
- **Out:** renaming any route (HS-72-03 does the companion untangle *on top
  of* this map); OpenAPI/public-API commitments (the manifest is an internal
  contract, not a stability promise — HoldSpeak's HTTP API is not a public
  surface).

## Tasks

- [ ] Write the manifest generator (a small module + a pytest that
      regenerates and compares, the schema-snapshot pattern the repo already
      uses) emitting `docs/api-surface.json` + `docs/API_SURFACE.md`.
- [ ] Write the consumer extractors: `scripts/` helpers that pull the called
      path set from `web/src/**/*.{js,astro}` and
      `apple/Sources/Providers/Desktop/*.swift`, committed as fixtures the
      snapshot test reads.
- [ ] Tag each route with its consumers (web / ios / both / internal) in the
      manifest; unconsumed routes are listed honestly, not hidden.
- [ ] Convert routers with a uniform prefix to `APIRouter(prefix=...)` where
      it is a pure refactor (no path changes — proven by the manifest diff
      being empty).
- [ ] The guard: adding a route without regenerating the manifest fails; a
      Swift or web call to a path not in the manifest fails.

## Proof required

`docs/API_SURFACE.md` + `docs/api-surface.json` committed and readable; the
snapshot test green; a deliberate unregistered-route scratch run red (captured
output); the manifest diff for the prefix conversion empty; full suite green.

## Done

Shipped. The surface is a committed, generated artifact: 229 routes (incl.
both WebSocket routes and the static mount) with per-route consumers
extracted from the real call sites — **44 iOS-consumed, 151 web-consumed**,
the rest honestly server-only. Five snapshot tests keep it true (manifest ==
live app, markdown == manifest, clients-only-call-served-routes, non-vacuity
pins, extractor canary), and both drift directions were proven red and
reverted (an undeclared scratch route; a Swift call to an unserved path).
The generated markdown passes the full doc-drift guard; full suite 3056
passed, 38 skipped. Deviation recorded:
the cosmetic `APIRouter(prefix=...)` conversion was skipped (the manifest
makes it moot; HS-72-06 adopts the style where it rewrites anyway). See
[evidence-story-02.md](./evidence-story-02.md).
