# HSM-16-04 — The web Astro Desk (parity build)

- **Project:** holdspeak-mobile (build lands in the holdspeak web app, `web/src`)
- **Phase:** 16
- **Status:** done (2026-07-05 — the survey-corrected remaining slice: the recipe layer
  resurrected + authoring, and the Ask AI atom's full web arc; see `evidence-story-04.md`.
  The bulk of the original scope was pre-paid by the Primitive Framework + HS-73/74/78 —
  recorded in the resume survey)
- **Depends on:** HSM-16-01 (the spec), HSM-16-03 (the store/API to read), holdspeak Phase 68
  (design-pattern catalog + shared Signal tokens).
- **Unblocks:** HSM-16-05 (the surface that syncs), HSM-16-06 (proof).
- **Owner:** agent (Fable)

## The truth-up the build opened with (2026-07-05)

The survey called this story "substantially pre-paid… remaining slice = web recipe/atelier
authoring + the Ask atom's web parity". The build found the pre-paid recipe layer was
actually **dead on the web** — the Phase-17 rename half-landed there and nobody noticed:

- `api.ts` read the pre-rename `agents` response key into a nonexistent `items.agent`
  lane (the hub answers `{recipes: […]}`), so recipes never loaded;
- `world.ts` ORDER/glow, `lineage.ts` resolve order, `InlineEditor`'s and `Pullout`'s kind
  checks all still said `"agent"` (a kind that no longer exists), so nothing recipe-shaped
  could render, edit, or resolve;
- the chrome's "+ Agent" chip called `createPrimitive("agent")` — an undefined route table
  entry, a live crash;
- the desk vitest suite was ALREADY RED (`fromWireAgent is not a function`) — the rename
  broke the test file itself and no gate caught it.

All fixed in this story, with a fetch-stubbed regression lock on the exact loader keys.

## Problem

The web client has no Desk. To be a mesh, the DeskOS must exist in `web/src` (Astro) at parity with the
iPad — the same metaphor, the same objects, the same gestures — built against the real API, not a
mock.

## Scope

- **In:** the DeskOS twin in `web/src`:
  - A **canvas** of objects with weight/drag/settle (a physics-ish layer — pointer drag + inertia; the
    bar need not be SpriteKit, but it must feel like objects, not a list).
  - The **object kinds** from HSM-16-01: meetings, their **spilled** outputs, models, **directories**,
    **knowledge bases** (the crystal). Tap → open (spill / window / read), long-press/right-click →
    reshape, **lasso** → select, **bundle**, **file into** (classify).
  - A **left organization pane** (Smart / Library / Directories / Knowledge) and **floating app
    windows** on the desk (meeting detail, an output reader) — the windowing model, not page nav.
  - Built on the **shared Signal tokens** (Phase 68 catalog: accent `#FF6B35`, the surface/elevation
    ramps) so the two surfaces are visibly one product. Reads real data from `/api/meetings` + the
    HSM-16-03 organization store.
- **Out:** the live-meeting lasso (its own story), Fun Mode/CoreMotion (device-only). Sync wiring is
  16-05 — this story makes the surface; 16-05 makes it flow.

## Acceptance criteria

*(Re-read against what shipped: the desk IS the web front door since HS-73-02 — `/` mounts
`DeskApp`; the canvas/objects/windows/zones landed in HS-73; this story closed the two
genuinely-open slices.)*

- [x] A desk route renders the canvas with real objects (pre-paid: `/` via HS-73-02; `/desk`
      307-redirects there). Meetings open in-world (the pull-out drawer, HS-73-04).
- [x] Lasso → bundle works ON THE WEB now: drag the empty desk to rope objects (or
      shift/cmd-click), the bundle bar rises, Ask AI composes over the roped context.
      File-into-zone was pre-paid (drag onto a tray, HS-73-05).
- [x] Recipe authoring at parity: recipes load (the rename truth-up), float, rail, pull out,
      and edit in-world (avatar + name + role + system prompt + template + tools + KB +
      profile), autosaving through the real PUT.
- [x] The Ask AI atom's web arc: lasso → lens grid + prompt (+ mic) + RUNS-ON pick →
      `/api/ask` (the hub assembles material from the canonical store) → the card prints in
      the panel wearing the run's HONEST egress (model · host) → Keep mints the SAME
      artifact shape the iPad's Keep mints (`via_kind: "ask"`, every card + the prompt) and
      it materializes on the desk with the NEW beat; Bin stores nothing.
- [x] Uses the shared Signal tokens; six committed screenshots reviewed against the iPad
      16-09 shots.
- [x] `cd web && npm run build` green; vitest desk suite 39/39 (was red before this story);
      hub unit suite 2482 green; api-surface regenerated (240 routes).

## Test plan

- `cd web && npm run build` green; load `/desk` in headless Chromium, screenshot, compare to the iPad
  DeskOS shots for parity. Source-only commit (the built bundle is gitignored — see
  [[reference_web_bundle_gitignored]]).
