# Evidence — HS-73-01 — The React foundation: the world, ported

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-73-desk-inhabited`)
- **Owner:** agent (Fable), owner-directed phase

## The stack, landed

- `@astrojs/react` (React 19) via `npx astro add react` — one build
  pipeline, still a static bundle FastAPI serves; plus `zustand`, `motion`
  (reserved for the interaction stories), `@use-gesture/react`, and
  `vitest` (dev).
- `web/src/desk/`: `DeskApp.tsx` (the island root), `store.ts` (Zustand;
  positions keep the EXACT legacy `localStorage["hs.diorama.pos"]` bare-map
  contract — no persist-middleware envelope, so hand-arranged desks survive
  the Alpine→React cutover byte-for-byte), `api.ts` (the faithful port of
  `loadAll` + every `fromWire*` normalizer, same endpoints incl.
  `/api/coders/status`), `world.ts` (bit-faithful `worldObjects` /
  `looseHome` / `objGlow` / float-phase math), `hash.ts` (the legacy `_oh`
  FNV jitter), `components/{Stage,World,DeskObject}.tsx`, `desk.css` (the
  HS-71 atmosphere/object/zone values verbatim, namespaced `.desk-next`).
- **The sprite picker is the SAME module** — the island imports
  `scripts/desk/sprites.js` directly (it was already ESM), so per-id sprite
  choice is parity by construction, not by port (a `.d.ts` types it).
- Coexistence: the island mounts at `/desk-next`
  (`<DeskApp client:only="react" />`; a `pages.py` route + pre-flight
  entry); the Alpine `/desk` is **frozen** (bugfix-only) from this merge.
- Drag: `@use-gesture` with HS-71-04's exact semantics — fresh world rect
  per move, 0.04..0.96 unit clamp, >4px tap/drag threshold, persist on
  release, drag-state cleared next-tick for the open-vs-drag
  discrimination the later stories use.

## Verification artifacts

- **Unit rig** (`npx vitest run src/desk`): **9 passed** — sprite-hash
  stability + pool spread against the shared picker, every wire
  normalizer, tombstone dropping, `looseHome` determinism + clamping +
  saved-position precedence, the legacy `_oh`.
- **Side-by-side parity** (Playwright, one seeded hub — 4 meetings, 3
  notes, 2 KBs, 2 agents, 1 directory): the island renders **11 objects +
  1 zone**, sprites served from the shared pool; screenshots
  `01-parity-alpine.png` vs `01-parity-react.png`.
- **Drag persistence**: a real mouse drag saved a unit position under the
  legacy key, it survived a full reload, and Tidy reset it to `{}` —
  asserted, plus `01-drag-persisted.png`. Zero page errors across the run.
- `npm run build`: **19 pages** (the island + the coexistence page).
- Route pre-flight (with `/desk-next` registered): **2 passed**. Full
  python suite at ship: **3066 passed, 37 skipped, 0 failures**. API
  manifest regenerated (the new page route).

## Acceptance criteria — re-checked

- [x] The island builds in the one existing pipeline.
- [x] Render parity with the Alpine desk on the same seeded data
      (side-by-side committed).
- [x] Same positions contract, same sprite picker, same layout math
      (unit-tested, not eyeballed).
- [x] The legacy desk frozen, not regressed (it stays the served `/desk`
      until the cutover).

## Deviations from plan

- The float stays on the proven CSS keyframes (verbatim values) rather
  than per-object `motion` springs: N springs for an ambient loop is
  wasted main-thread work and the CSS float IS the shipped feel. `motion`
  enters where it earns its keep — the materialize/pull-out choreography
  in the interaction stories.
- Zones render at parity (flat tray + count) but file/dive is deliberately
  NOT wired on the island yet — that is HS-73-05's scope; the story's own
  In-list ("atmosphere, sprites, float, drag-to-arrange, Tidy") is the
  parity bar and is met.

## Follow-ups

- HS-73-02 promotes the island to `/` and retires `/desk-next`.
