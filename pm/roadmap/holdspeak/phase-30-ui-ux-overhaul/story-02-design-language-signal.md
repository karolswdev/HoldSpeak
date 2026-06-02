# HS-30-02 — "Signal" design language + skill-derived system + sign-off

- **Project:** holdspeak
- **Phase:** 30
- **Status:** backlog
- **Depends on:** HS-30-01
- **Unblocks:** HS-30-03
- **Owner:** unassigned

## Problem

The redesign needs one written, signed-off visual language before a single token
is changed — otherwise the per-page work drifts. The direction is locked (bold,
distinctive, dark-first), but the exact palette ramps, type scale, depth, radius,
and motion grammar must be derived properly (via the `ui-ux-pro-max` skill) and
approved, so HS-30-03 onward is mechanical application, not invention.

## Scope

### In

- Run the `ui-ux-pro-max` skill (`--design-system` + `style` / `color` /
  `typography` domains) for the bold-dark productivity direction; capture the
  output as the system's grounding.
- A **design-language doc** `evidence/design-language-signal.md` defining the
  **"Signal"** system:
  - **Palette**, as named ramps with hex + intended role + AA contrast notes:
    near-black canvas family (seed `#0E0F13`), raised surfaces (seed `#1A1C22`),
    off-white text (seed `#F2F3F5`) + a muted text step, the signature **orange
    accent** (seed `#FF6B35`) + an accent-glow, hairline border, and status
    ramps (success / warn / danger / info) tuned for dark.
  - **Typography**: Space Grotesk (display), Inter (UI/body), JetBrains Mono
    (data) with a concrete size / weight / line-height / tracking scale.
  - **Depth**: real elevation (shadow + accent glow on primary), replacing the
    current all-`none` elevation.
  - **Shape**: a real corner-radius scale, replacing the current all-`0` radius.
  - **Motion**: easing (seed `cubic-bezier(0.16, 1, 0.3, 1)`) + duration scale,
    and the `prefers-reduced-motion` stance.
  - **Density**: spacing rhythm and the default vs dense surface intent.
- A token-name plan that maps Signal → the variables HS-30-03 will write (so the
  component tree keeps reading from `tokens.css`).
- **Sign-off gate:** Karol approves the doc before HS-30-03 starts.

### Out

- Editing `tokens.css` / `global.css` / any component (HS-30-03+).
- Light theme (deferred — but author ramps so a light variant is additive later).

## Acceptance criteria

- [ ] `evidence/design-language-signal.md` exists and specifies palette,
      typography, depth, shape, motion, and density as concrete, buildable values.
- [ ] The system is **skill-derived**: the `ui-ux-pro-max` output it's based on is
      captured in evidence (not just asserted).
- [ ] Every text/affordance colour pairing lists its intended AA contrast target
      (verified for real in HS-30-09).
- [ ] A token-name map is included so HS-30-03 is a mechanical translation.
- [ ] **Signed off by Karol** (record the sign-off in the doc) before HS-30-03.

## Test plan

- Unit / backend: n/a — design doc.
- Visual: optional — a single static mock (HTML or image) of one surface in
  Signal to make the sign-off concrete.
- Build: n/a.

## Notes / open questions

- The `ui-ux-pro-max` "Modern Dark" style is the closest match (best-for: pro
  productivity / dev tools / AI interfaces) and already recommends the chosen font
  trio — use it as the spine, adapt the accent to HoldSpeak's orange.
- Keep `#000000`-pure backgrounds out (OLED smear / harshness); use the near-black
  family.
- This is the hard **gate**: no token work ships until this is approved.
