# HS-99-01 — The study and the tokens

- **Project:** holdspeak
- **Phase:** 99
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-99-02..06

## Problem

The ProzillaOS study identified the chrome techniques we lack, but
none of them have a home in the token system: no surface depth
ladder, no easing family, no tint formulas, no scrollbar/control
tokens, no compositional shadow primitives. Building chrome before
the tokens exist would scatter raw values the gate then has to chase.

## Scope

- In:
  - `docs/internal/PROZILLAOS_STUDY.md` — the borrow/embrace/skip
    inventory with MIT attribution, each technique tied to the story
    that lands it;
  - token additions in `web/design-tokens.json` (component layer):
    the five-step window surface ladder (`--os-surface-0..4` family
    mapped onto our ink ramp), `--os-head-fill`/`--os-well-fill`,
    easing tokens (`--ease-quart/--ease-expo/--ease-back`), tint
    formulas (`--tint-hover`/`--tint-selected` via color-mix),
    `--os-scrollbar-thumb`, control tokens (chevron color, control
    heights), and compositional shadow primitives
    (size/opacity/spread → the existing `--desk-window-shadow`
    family, values preserved);
  - generator + TS mirror untouched in behavior; gates green with no
    new allow-list entries;
  - DESIGN_SYSTEM.md gains "The chrome ladder (HS-99)" spec BEFORE
    the chrome stories consume it.
- Out:
  - any component CSS change (stories 02..06).

## Acceptance criteria

- [ ] Study doc committed with attribution; every borrowed technique
      names its landing story.
- [ ] Tokens generated, `tokens:check`/`tokens:gate` green, no new
      allow-list entries; spec section lands first.
- [ ] `npm run check` + guard subset green.

## Test plan

- tokens:check/gate; design-system guards; `npm run check`.

## Evidence required

- Study doc, token diff, gate output, suite output.
