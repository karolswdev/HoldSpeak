# Qlippy — vendored mascot assets

Qlippy is the HoldSpeak mascot: a warm-orange bent-paperclip helper (a Clippy
homage) rendered by the presence layer's mascot mode (`presence.mascot`).

**Provenance:** PixelLab object `44c0b009-520d-4662-b60b-303627a5a39d`
(1-direction, 80×80 native, v3 animations). Vendored from the working asset
pack (`qlippy-concepts/final/`); regenerate there, then re-copy.

## Layout

- `qlippy.png` / `qlippy@4x.png` — canonical static avatar (idle frame).
- `sprites/<state>.png` — **80×80 horizontal sprite strips, 9 frames
  left→right** (`background-size: 720px 80px`, animate with `steps(9)`,
  `image-rendering: pixelated`). States: idle, listening, thinking,
  questioning, alert, approve, decline, learned, present-note, celebrate,
  error, surprised, wave-hello, sleeping.
- `glyphs/` — crisp Signal-palette status glyphs the UI composites above
  Qlippy's head at runtime: `check.png` (#34D399), `x.png` (#F87171),
  `lightbulb.png` / `bang.png` (#FBBF24).

## The design rule

A paperclip has no hands, and at 80×80 the generator cannot render small
symbols legibly — so **the sprite does the body emotion and the UI composites
the glyph**. Only large props that render well (the note, the Zzz) are baked
into strips. Do not bake glyphs into new states.

Served under the web bundle's `/_built` base (e.g.
`/_built/qlippy/sprites/idle.png`); local only, in-bundle, never fetched from
a network.
