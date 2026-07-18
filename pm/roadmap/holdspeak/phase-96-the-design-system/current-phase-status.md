# Phase 96 — The Design System

**Status:** CLOSED (7/7, 2026-07-18 — scaffolded and shipped the same
day by owner directive) at machine-verifiable scope under the standing
close directive; the owner's design-polish verdict rides UAT Campaign 13
with the Desk OS sitting. See [final-summary](./final-summary.md).

**Last updated:** 2026-07-18 (HS-96-07 done; phase CLOSED 7/7).

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
| HS-96-02 | The validator gate and the burn-down | done | [story-02-validator-burndown](./story-02-validator-burndown.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-96-03 | Component state specs | done | [story-03-component-specs](./story-03-component-specs.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-96-04 | One material grammar | done | [story-04-material-grammar](./story-04-material-grammar.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-96-05 | The accessibility pass | done | [story-05-accessibility](./story-05-accessibility.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-96-06 | Docs and the mechanical lock | done | [story-06-docs-lock](./story-06-docs-lock.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-96-07 | Closeout: walks, storm, owner rider | done | [story-07-closeout](./story-07-closeout.md) | [evidence-story-07](./evidence-story-07.md) |

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

**HS-96-02 done (2026-07-18): the gate is live and the debt is paid.**
The adapted validator (`web/scripts/validate-tokens.cjs`: hex/rgb colors,
z-index literals, ms durations in component CSS, with var() bodies
masked) runs in `npm run check` beside the drift gate; the evidence shows
it firing on a planted raw value and failing on stale allow-list entries.
86 literals burned down: the recurring values became NAMED tokens
(--desk-glass, --desk-window-fill, --shadow-ink-1..6, --wash-1/2,
--accent-cool, --accent-glow-strong, and the z ladder including
--desk-z-stage/-dock-under/-popover); the 70 that remain are allow-listed
with reasons (DioPal atmosphere art, local stacking contexts, one-off
shades for HS-96-04's fold). The TS mirror is generated
(`src/lib/tokens.gen.ts`): DeskWindow physics, snap clearances, the glow
pool, and zone tints now come from the SAME source as the CSS — drift is
structurally impossible. Build pixel-identical (shots in assets/);
suite 256/256.

**HS-96-03 done (2026-07-18): the state contract is written and true.**
`docs/internal/DESIGN_SYSTEM.md` carries the architecture, the locks, and
per-component state matrices (Button, chips, window verbs, dock, orb,
window frame, inputs, Switch/Tabs/StatusPill/InlineMessage, and the GL
world states) in token vocabulary only (a guard forbids raw values in the
doc). The mechanical gaps closed: one pressed grammar (a 1px settle,
compositor-only) across `.btn` and eleven chrome families, the orb
pressing inward; focus-visible was already global (audited, adopted as
the spec's grammar). `tests/unit/test_design_system_guard.py` locks the
doc's coverage and the CSS grammars; the keyboard walk shows 14/14 tab
stops wearing the accent ring (`assets/focus-ring-1440.png`). Suite
256/256; token gates clean.

**HS-96-04 done (2026-07-18): one window material.** A single
`:where(.desk-pullout, .desk-surface-window, .desk-trust-window)` rule
carries the family (fill `--desk-window-fill`, radius
`--desk-window-radius` 18, elevation `--desk-window-shadow`, the glass
`--desk-window-blur`); the pull-out keeps only its per-kind tinted border
as a spec'd override; the menu adopts the transient tokens; window body
padding rides `--desk-window-pad-*`. Named normalizations: surface/trust
fills 0.96 → the R2-06 0.985, radius 16 → 18, elevation unified, glass
family-wide. The allow-list SHRANK (70 → 69). Storm with the glass on the
assembled build: median 8.3ms, p95 9.8ms — no regression. Suite 256/256;
`assets/material-1440.png` shows both families side by side.

**HS-96-05 done (2026-07-18): the OS answers the keyboard.** Windows
manage focus (open moves in, close returns to the opener, Escape closes,
tabIndex=-1 shell — NO trap, windows stay regions); the menu carries the
full Radix keyboard pattern hand-rolled (arrows, Home/End, Escape with
focus return); keyboard travel through the GL world is VISIBLE — a
focused sr-only world button surfaces as a chip above the dock band (the
walk shows 'My Nuts' surfacing). axe sweeps run in the suite at the
serious/critical gate, zero violations. The Radix decision is RECORDED in
the story: Signal stays; the patterns come, the primitives do not (the
desk's no-modal law and the dark-only grammar would fight Radix's grain;
the patterns cost ~30 lines). Suite 259/259; the focus walk verifies all
three behaviors live.

**HS-96-06 done (2026-07-18): the system is documented where builders
look.** `docs/internal/DESIGN_SYSTEM.md` (authored across 03-05) is
referenced from web/README's add-a-surface path (a fifth step names the
styling rules and the gate) and from the frontend architecture doc's
locks list (now including the Phase 96 token gates and the state-contract
guard). Doc guards 22/22; `npm run check` green end to end.

**HS-96-07 done (2026-07-18): closed against the production bundle.**
The assembled eight-walk chain green on the restyled bundle with zero
failed API responses; the storm within the Phase 95 envelope (median
8.3ms, p95 10.0ms, one layout event); every guard green (no-exit, cores,
desk locks, design-system, doc drift, UAT packs); `npm run check` end to
end; the full python sweep 4110 passed / 0 failed. Campaign 13 carries
the `desk-os-design-polish` scenario so one sitting casts both verdicts.
final-summary.md names the deferrals (the sitting itself, the keyboard
zone-rename path, the 69 shrinking allow-list entries, busy-state
stragglers) and hands the token JSON to the Swift belt.
