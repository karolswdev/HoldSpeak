# HS-30-03 Evidence — Foundation: tokens + global CSS + fonts + galleries

**Date:** 2026-06-01.
**Story:** [story-03-foundation-tokens.md](./story-03-foundation-tokens.md).

## Implementation Evidence

The Signal foundation is live: the whole web front-end now renders dark Signal
(verified on the running build, not just compiled).

**`web/src/styles/tokens.css`** — full rewrite to the design-language §9 map:
- §1 Signal canonical tokens: `--bg #0E0F13`, `--surface-1/2/3`, `--text/-muted/
  -faint/-on-accent`, `--accent #FF6B35` (+ hover/press/tint/glow), status
  (`--ok/--warn-signal/--danger-signal/--danger-fill/--info`), `--border-subtle/
  border/strong`, the three font stacks.
- §2 legacy semantic aliases (`--canvas`, `--line`, `--text`, `--accent`, status,
  `--field-*`, `--selected-*`, `--radius-1..5`, `--elev-0..4`, motion, focus)
  **repointed** to Signal — so existing component CSS flips to dark with no edits.
- §3 a **clearly-marked TEMPORARY `--wb-*`→Signal shim** (deleted by HS-30-05).
- §4 real `--radius-*` (was all `0`) + real `--elev-*` (was all `none`) + the
  Signal motion grammar + `--focus-ring` (orange-on-dark).
- `color-scheme: dark`.

**`web/src/styles/global.css`** — body → `--bg` canvas + `--text` off-white;
font `@import`s swapped to Inter + Space Grotesk + JetBrains Mono (VT323 + Sora
gone); pulse retuned to `--ease-standard`. Zero `--wb-*`/`VT323`/`Sora`.

**`web/package.json`** — added `@fontsource/inter` + `@fontsource/space-grotesk`,
removed `@fontsource/sora` + `@fontsource/vt323`; `npm install` clean (font dirs:
`inter`, `space-grotesk`, `jetbrains-mono`).

**Bounded component fix (so the swap is clean, not light boxes):** the 16
`--wb-white`-as-background sites + 2 hardcoded `#f5f5f5` footers were retargeted to
`--surface-2` (CommandPreview, ConfirmDialog, activity, dictation, history, Panel,
index). Everything else flips via the shim: `--wb-white`→off-white text,
`--wb-black`→subtle light border, `--wb-blue`→dark surface, oranges→accent,
grays→neutral ramp, status→Signal.

### The `--wb-*` discovery (why a shim)

The plan assumed a token swap flips everything at once. It can't: **108 component
refs hardcode `--wb-*`**, and `--wb-white` (25 text / 16 bg) and `--wb-black`
(37 border / 1 text) are context-dependent, so no single remap is correct for all.
Resolution: flip them via a temporary shim now; **HS-30-05 migrates the 89
remaining refs to canonical Signal names and deletes shim §3.** This keeps the
chunk shippable and the app readable, instead of one un-reviewable mega-commit.

## Tests

```bash
cd web && npm run build
# 23:41:31 [build] ✓ Completed in 4.12s — 8 page(s) built. (green)

npm run preview && curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:4321/_built/
# 200  (FastAPI /_built mount serves the rebuilt Signal assets)

uv run pytest -q --ignore=tests/e2e/test_metal.py
# 2062 passed, 14 skipped in 62.66s  (no regression; matches Phase-29 baseline)
```

### Sweep

```text
global.css        : --wb-* / VT323 / Sora  = 0
tokens.css        : --wb-* only inside the marked §3 shim
web/src VT323/Sora : 10 hits — all COMMENT mentions in not-yet-migrated component
                     files (flagged for HS-30-05; no font usage)
web/src --wb-* refs (outside tokens.css): 89 — flipped via shim, migrate in HS-30-05
```

## Live evidence (screenshots)

`evidence/after-hs03/after-{runtime,history,components,dictation}.png` — captured
from the running build via headless Chrome at 1440 wide. The runtime dashboard and
the `/design/components` gallery both read as clean dark Signal: near-black canvas,
dark panels with subtle borders + off-white titles in Space Grotesk/Inter (no pixel
font), orange `#FF6B35` primary, dark-tuned status pills, info-cyan local-only
pill, readable throughout — no broken/invisible text. Compare to
`evidence/before/before-*.png`.

## Result

The Signal foundation is in place and the product is dark end-to-end. **Next:
HS-30-04** — rebuild the nav + layout shell (`AppLayout`/`TopNav`) to the IA spec
(grouped nav Live/Review/Configure, global status cluster, Settings drawer),
beginning the structural redesign on top of this foundation.
