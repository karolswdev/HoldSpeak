# HS-73-01 — The React foundation: the world, ported

- **Status:** done
- **Priority:** HIGH (everything else in the phase stands on it)
- **Depends on:** —
- **Evidence:** [evidence-story-01.md](./evidence-story-01.md)

## Goal

Stand up the React island and bring the existing world to **render parity**:
the atmosphere, sprites, float, drag-to-arrange, and Tidy — everything the
Alpine desk's world layer does today, in React + TypeScript with real
components, typed state, and spring motion. No new verbs in this story;
parity is the deliverable, because parity is provable.

## Scope

- **In:** the `@astrojs/react` integration; the `web/src/desk/` app; the
  typed API layer; the store; the world at parity; the legacy coexistence
  arrangement.
- **Out:** chrome/IA changes (HS-73-02); any inhabitation verb (03–07);
  deleting the Alpine desk (HS-73-08 — it stays live and frozen at `/desk`
  until then).

## Tasks

- [ ] Integration: `cd web && npx astro add react` (adds `@astrojs/react`
      + react/react-dom + TS config). Add `zustand`, `motion`,
      `@use-gesture/react`. Verify `npm run build` still emits the one
      static bundle FastAPI serves (no SSR artifacts).
- [ ] App skeleton under `web/src/desk/`: `DeskApp.tsx` (root),
      `store.ts` (Zustand: `items`, `positions`, `divedZone`, plus slots
      the later stories fill), `api.ts` (typed fetchers importing
      `web/src/lib/primitives.ts` — do not fork the shapes),
      `sprites.ts` (port `sprites.js`'s djb2 `stableHash` **with the
      BigInt 64-bit two's-complement wrap** — a JS Number loses precision
      and breaks per-object sprite stability; HS-71-02's lesson),
      `useRuntimeBus.ts` (subscribe to the `hs-*` DOM events
      `runtime-bus.js` dispatches on `window`; never open a socket here).
- [ ] Data layer: port `loadAll()` (`desk-app.js:464`) and the per-kind
      `fromWire*` normalizers (:556/:582/:648/:676/:782/:806) into
      `api.ts` — same endpoints (`/api/meetings`, `/api/sync/pull`,
      `/api/notes`, `/api/agents`, `/api/kbs`, `/api/directories`,
      `/api/chains`, `/api/workflows`, `/api/profiles`,
      `/api/companion/status`), same normalized `{kind, id, title, …}`
      result.
- [ ] The world at parity, as components: `Stage` (the HS-71-01 atmosphere:
      gradient + spotlight + motes — motes stay one cheap canvas),
      `World`, `DeskObject` (sprite via `sprites.ts`, per-kind glow pool,
      detached ground shadow, float via `motion` springs with per-object
      phase — match the Alpine desk's feel, don't invent), `ZoneTray`
      (parity-level: the current flat tray; HS-73-05 makes it a landmark).
      Layout: port `looseHome` density auto-layout + `objStyle` jitter.
- [ ] Placement: port `positions` (same `localStorage["hs.diorama.pos"]`
      key — local-only, never synced), drag via `@use-gesture` with the
      unit-space clamp (0.04..0.96) and the >4px tap/drag threshold
      (`startObjDrag`, :296), `tidyDesk`. Reduced-motion: floats rest.
- [ ] Coexistence: mount the island on a new page (e.g. `/desk-next`) for
      this story only; the Alpine `/desk` is **frozen** (bugfix-only) from
      this story's merge. HS-73-02 promotes the island and re-homes the
      legacy page.
- [ ] Basic island test rig: a vitest (or equivalent) unit run for
      `sprites.ts` stability (same ids → same sprites, matching the JS
      picker's output on a fixture set) and the wire normalizers.

## Proof required

Side-by-side screenshots: the Alpine `/desk` world vs the island on the
same seeded data — same sprites per id (hash parity asserted in a test),
same layout class, floats alive. Drag persists across reload
(Playwright, same localStorage key). `npm run build` green; route
pre-flight green (the temporary page registered); full suite green.

## Done

Shipped. The Desk island stands: React 19 via `@astrojs/react` in the one
existing build (still a static bundle), `web/src/desk/` with a Zustand
store keeping the EXACT legacy positions contract, a faithful typed port of
`loadAll` + every normalizer, bit-faithful `looseHome`/glow/float math, the
HS-71 CSS values verbatim, and the SAME sprite-picker module imported
directly (parity by construction). Drag replicates HS-71-04's semantics via
`@use-gesture` (fresh rect per move, clamp, >4px threshold). Mounted at the
coexistence route `/desk-next`; the Alpine `/desk` is frozen. Proofs:
vitest 9/9 (hash parity, normalizers, layout math); the side-by-side on one
seeded hub — 11 objects + 1 zone, screenshots committed; a real drag
persisted across reload under the legacy key and Tidy cleared it; zero page
errors; 19 pages built; pre-flight 2 passed; full suite 3066 passed, 37
skipped. Deviations
recorded (CSS float kept over N motion springs; zones parity-only until
05). See [evidence-story-01.md](./evidence-story-01.md).
