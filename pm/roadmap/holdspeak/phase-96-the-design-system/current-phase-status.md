# Phase 96 — The Design System

**Status:** IN PROGRESS (1/7; HS-96-01 done 2026-07-18).

**Last updated:** 2026-07-18 (HS-96-01, the token architecture, done).

## Why this phase exists

Phase 95 built the OS: the WebGL world, one window chrome, the dock, every
surface in-world. What it inherited is the styling under that OS — a
3,400-line `desk.css` full of hand-tuned hex values, ad-hoc radii and
shadows, a `tokens.css` that mixes primitive and semantic values in one
flat layer, surface windows that grew their own background/border recipe
beside the pull-out grammar, and interaction states (focus-visible,
active, busy) present where someone remembered and absent where they
didn't. The owner directed this phase by name: apply the vendored
**design-system** skill (three-layer token architecture, generated CSS,
a hardcoded-value validator, component state specs) and the **ui-styling**
skill (interaction-state discipline, accessibility patterns, hierarchy
and spacing craft) to the Desk OS.

This phase executes Constitution Articles VII (the interface serves — one
quiet grammar) and VIII (native-grade craft); Article X governs the one
open design decision it must record (the Radix question, HS-96-05).

## The method (from the skills, adapted honestly)

The design-system skill's core transfers directly: a
`design-tokens.json` source of truth generating CSS in three layers
(primitive → semantic → component), a validator that fails the build on
raw values in component styles, and per-component state matrices
(default / hover / focus-visible / active / disabled / busy). The
ui-styling skill's shadcn/Tailwind stack does NOT transfer wholesale —
HoldSpeak's web is the hand-rolled Signal grammar over plain CSS by
standing decision — but its disciplines do: mobile-first responsiveness,
dark-mode-consistent theming through the semantic layer, Radix-grade
accessibility patterns, and "every detail matters" interaction craft.
Where a skill rule fights repo canon, canon wins and the deviation is
recorded (Article X.3).

## Scope

### In

- `design-tokens.json` + a generator producing the three-layer
  `tokens.css` with today's computed values preserved (screenshot-stable);
- the token validator wired into `npm run check` and CI; the hardcoded
  values in `desk.css`/`react-app.css` burned down to component tokens
  (the z ladder, the glow palette, radii, elevation, motion, chrome
  dimensions);
- component state specs for the Signal grammar and the OS chrome
  (windows, dock, chips, verbs, badges, shelf), with the missing states
  implemented;
- one material grammar: surface windows, the trust window, the menu, and
  the pull-outs on the same elevation/radius/motion tokens;
- the accessibility pass: window focus management, keyboard reachability,
  ARIA on the shell furniture, reduced-motion completeness, and the
  recorded Radix decision;
- docs (the design-system chapter), the validator as a mechanical lock,
  and a closeout with the screenshot walk, a storm re-run, and the owner
  rider on the UAT rig.

### Out

- Adopting Tailwind or shadcn/ui wholesale (the Signal grammar is
  standing canon; HS-96-05 may adopt individual Radix primitives under
  Signal skins if the evidence says so);
- new surfaces or OS behavior (Phase 95's contracts are the floor);
- the GL world's generated textures beyond retinting through tokens;
- Swift Desk parity (the HSM belt consumes the token JSON later).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-96-01 | The token architecture | done | [story-01-token-architecture](./story-01-token-architecture.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-96-02 | The validator gate and the burn-down | backlog | [story-02-validator-burndown](./story-02-validator-burndown.md) | — |
| HS-96-03 | Component state specs | backlog | [story-03-component-specs](./story-03-component-specs.md) | — |
| HS-96-04 | One material grammar | backlog | [story-04-material-grammar](./story-04-material-grammar.md) | — |
| HS-96-05 | The accessibility pass | backlog | [story-05-accessibility](./story-05-accessibility.md) | — |
| HS-96-06 | Docs and the mechanical lock | backlog | [story-06-docs-lock](./story-06-docs-lock.md) | — |
| HS-96-07 | Closeout: walks, storm, owner rider | backlog | [story-07-closeout](./story-07-closeout.md) | — |

## Where we are

**HS-96-01 done (2026-07-18): the tokens have one source of truth.**
`web/design-tokens.json` carries three layers; the adapted generator
(`web/scripts/generate-tokens.cjs`, skill-style `{ref}` syntax with a
purpose-built plain-CSS emitter and a `--check` drift gate wired first
into `npm run check`) emits `tokens.css`. Fidelity proven mechanically:
all 117 pre-existing custom properties preserved with identical computed
values, 61 added — the primitive layer (ink/paper/orange/status ramps,
the glow pool, the zone tints, the type faces) and the Desk OS component
layer (the z ladder 0/25/30/42/80/81, window margins/grab/cascade, snap
clearances, per-kind glows). Deterministic double-run, `npm run check`
green end to end, and the production desk renders identically (shots in
`assets/`).

Next: HS-96-02 wires the validator and burns the desk.css literals down
onto these tokens.
