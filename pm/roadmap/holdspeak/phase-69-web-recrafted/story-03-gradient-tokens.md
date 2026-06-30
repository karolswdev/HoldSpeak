# HS-69-03 — Gradient + hairline tokens

- **Status:** done
- **Priority:** HIGH (unblocks 02/04)
- **Depends on:** —
- **Catalog pattern(s):** §1 depth
- **Evidence:** [evidence-story-03.md](./evidence-story-03.md)

## Goal

`--accent-gradient` + `--bg-gradient` (the iPad values) added to the token layer,
consumed by the glyph chip + the signal-card top-lit hairline.

## Done

Shipped in the substrate wave: `web/src/styles/tokens.css` carries
`--accent-gradient` (amber→ember diagonal) + `--bg-gradient` (cinematic vertical
wash). `.glyph-chip` fills with `--accent-gradient`; the `.signal-card::before`
hairline is the directional `white .12 → .035` gradient. See the evidence file.
