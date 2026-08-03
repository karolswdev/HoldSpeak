# HS-115-08 - The cooled accent

- **Project:** holdspeak
- **Phase:** 115
- **Status:** backlog
- **Depends on:** HS-115-01
- **Unblocks:** HS-115-07
- **Owner:** unassigned

## The thesis (the bar)

The system accent cools from startup-orange (`#ff6b35`) to a
restrained tone that sits on dark beveled surfaces like patina, not
neon. The Signal Workbench chrome becomes quietly warm instead of
loudly branded. The "Done" button, focus rings, editor caret,
selection tint, traffic-light close, and every other accent surface
shift in one token change. Signal orange survives only as the brand
mark (the speech-bubble icon, the dock identity). When this ships,
the desk looks like an operating system, not a web app with a
corporate color.

**Articles served:** VIII (native-grade craft — the accent IS the
craft question).

## Ground

- `--accent: #ff6b35` — saturated warm orange, 88 consumers in
  desk.css + 20 hard-coded hex values.
- The accent does too many jobs: focus ring, primary button fill,
  editor caret, selection tint, window border, glow, traffic-light
  close button, link color, egress badge, recording indicator.
- In classic OS design (NeXTSTEP, Amiga, macOS pre-Big Sur), the
  system accent only appears on the thing you're actively touching.
  Everything else is neutral chrome.
- `--accent-cool: #5b8def` is defined but unused.

## Candidate tones

The owner's direction: "cool it down." Three candidates in the
burnt/earthy family — same hue, lower saturation, darker value:

| Name | Hex | Character |
|------|-----|-----------|
| Burnt amber | `#c47a52` | Warm leather, aged wood |
| Desert stone | `#b07454` | Sandstone, terracotta |
| Forge ember | `#a86e4a` | Cooling metal, workshop |

The owner picks one (or names another). The winner replaces
`--accent` and its derivative tokens. The gradient, glow, and
tint tokens re-derive from the new base.

## Deliverables

1. **Token swap.** Replace `--accent: #ff6b35` and all derivative
   tokens (`--accent-hover`, `--accent-press`, `--accent-tint`,
   `--accent-glow`, `--accent-gradient`) with the chosen tone.

2. **Hard-coded hex cleanup.** Replace all 20 hard-coded `#ff6b35`
   (and variant) values in desk.css with `var(--accent)` or
   derivative tokens. No hex values for accent outside tokens.css.

3. **Brand mark exception.** The dock speech-bubble icon and any
   brand-identity sprite keep signal orange if the owner wants the
   brand to remain distinct from the system accent.

4. **Contrast audit.** Verify the new accent passes WCAG AA contrast
   against `--surface-1` (window body), `--surface-2` (head bar),
   and `--bg` (desk background) for text-on-accent and accent-on-dark.

5. **Text-on-accent.** If the new accent is darker, `--text-on-accent`
   may need to shift from white to ensure button label legibility.

## Test plan

- `npx vitest run` — all frontend tests pass.
- Visual: open every surface from the walk shot list. The accent
  must read as "system color" not "brand color." Focus rings, Done
  buttons, selection highlights, and the editor caret must all use
  the new tone.
- Contrast: text on accent-filled buttons must be legible.
