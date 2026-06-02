# HS-30-02 Evidence — "Signal" design language + sign-off

**Date:** 2026-06-01.
**Story:** [story-02-design-language-signal.md](./story-02-design-language-signal.md).

## Implementation Evidence

The signed-off visual language for Phase 30. Two artifacts under `evidence/`:

- `evidence/design-language-signal.md` — the **"Signal"** system as concrete,
  buildable values: a neutral near-black surface ramp (`--bg #0E0F13` →
  `--surface-1/2/3`), off-white text ramp, the signature orange accent
  (`--accent #FF6B35`, reserved for primary/live/focus), dark-tuned status
  colours, the Space Grotesk / Inter / JetBrains Mono type scale (with an
  uppercase-tracked eyebrow replacing the VT323 title-strip), real depth (shadow +
  accent glow), a radius scale, a motion grammar (one brand pulse), density, an
  **AA contrast table** (§10), and a **token-name map** (§9) that makes HS-30-03 a
  mechanical translation. Hard rule captured: never white-on-orange (≈2.5:1) — the
  orange fill always carries dark ink (≈6.8:1).
- `evidence/signal-preview.html` + `evidence/signal-preview.png` — a static mock
  embodying **every** token (grouped nav, hero, transcript panel, intel rail,
  buttons incl. focus ring + disabled, status pills, fields, palette swatches),
  rendered at 1440×2 with puppeteer. This is the artifact the sign-off was made
  against; compare to `evidence/before/before-runtime.png`.

### Skill-derived (captured)

The system is grounded in `ui-ux-pro-max`, not invented: its `--design-system`
output recommended **Dark Mode (OLED)** style (WCAG AAA; best-for coding
platforms / dev tools), a **Real-Time / Operations** pattern (dark, status
colours, data-dense but scannable), and the **Space Grotesk + Inter + JetBrains
Mono** tri-stack (headings 600–700, body Inter 400–600, data Mono 500) — exactly
the chosen trio. We kept its structural palette ramp and swapped the cool-slate
base for Karol's neutral near-black and the green accent for the signature orange.

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py \
  "bold distinctive dark developer productivity tool, near-black, orange accent, confident, real-time monitor" \
  --design-system -p "HoldSpeak Signal" -f markdown
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<...>" --domain typography
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<...>" --domain color
```

## Sign-off

> 2026-06-01 — **Approved by Karol** ("yea dude this looks a lot better") against
> `evidence/signal-preview.png`. Recorded in `design-language-signal.md` §Sign-off.

This is the hard gate for the phase: with sign-off recorded, HS-30-03 may write
tokens.

## Tests

Design/docs chunk — no unit suite applies. The mock was rendered through the real
browser pipeline (puppeteer via the transitive Chromium):

```text
rendered evidence/signal-preview.png   # 1440×1100 @2x, fullPage
```

No Python touched; the backend sweep is the exit gate on HS-30-03 (where served
output first changes).

## Result

"Signal" is approved and fully specified. **Next: HS-30-03** — rewrite
`tokens.css` + `global.css` to the §9 token map, swap fonts (add Space Grotesk +
Inter, drop VT323 + Sora), update the design galleries, sweep out every `--wb-*` /
VT323 / Sora reference, and rebuild green.
