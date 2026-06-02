# HS-30-03 — Foundation: tokens + global CSS + fonts + design galleries

- **Project:** holdspeak
- **Phase:** 30
- **Status:** done
- **Depends on:** HS-30-02
- **Unblocks:** HS-30-04, HS-30-05, HS-30-06, HS-30-07, HS-30-08
- **Owner:** unassigned

## Problem

`web/src/styles/tokens.css` (276 lines) is the single source of truth — every
component reads its variables. Rewriting it to "Signal" flips the entire product
to the new look in one move. This story lands that foundation: the token layer,
the global stylesheet, and the fonts, proven by the design galleries.

## Scope

### In

- Rewrite `web/src/styles/tokens.css` to the Signal system from HS-30-02:
  - Replace the Workbench anchors (`--wb-blue/white/black/orange` + families)
    with the Signal palette (near-black canvas, raised surfaces, off-white +
    muted text, signature orange accent + glow, hairline border, dark-tuned
    status ramps).
  - Real `--radius-*` (no longer all `0`) and real `--elevation-*` /
    shadow + accent-glow tokens (no longer all `none`).
  - Typography stacks → Space Grotesk (display), Inter (UI), JetBrains Mono
    (data); size / line-height / tracking scale per the design language.
  - Motion tokens (easing + durations) per Signal.
- Rewrite `web/src/styles/global.css`: dark canvas + off-white default text,
  updated font `@import`s, the live-status pulse retuned, reduced-motion baseline.
- Swap fonts in `web/package.json`: add `@fontsource/space-grotesk` +
  `@fontsource/inter`, keep `@fontsource/jetbrains-mono`, drop `@fontsource/vt323`
  and `@fontsource/sora` (no longer referenced).
- Update `/design/check.astro` + `/design/components.astro` so the galleries
  render the new foundation (they are the visual contract for later stories).
- **Repo-wide sweep:** no remaining `--wb-*` token, no `VT323`, no `Sora`
  reference left live anywhere under `web/` (component scoped CSS included — any
  found are migrated or flagged for HS-30-05).

### Out

- Restyling component internals beyond what the token swap propagates (HS-30-05).
- Page-layout changes (HS-30-04/06/07/08).

## Acceptance criteria

- [x] `tokens.css` + `global.css` contain the Signal system; `global.css` has
      **zero** `--wb-*`/`VT323`/`Sora`. `tokens.css`'s **only** `--wb-*` is the
      clearly-marked temporary compat shim (§3), scheduled for deletion in
      HS-30-05. *(Scope note: a discovery during the rewrite — 108 component refs
      hardcode `--wb-*` with context-dependent meaning, so the foundation flips
      them via a shim now and HS-30-05 migrates the refs + deletes §3, rather than
      a single un-shippable mega-commit. Recorded in current-phase-status.)*
- [x] `web/package.json` adds Space Grotesk + Inter, removes VT323 + Sora;
      `npm install` clean.
- [x] `npm run build` is green; `/design/check` + `/design/components` render in
      Signal (screenshots in `evidence/after-hs03/`).
- [x] `grep -rE "VT323|Sora" web/src` returns only **comment** mentions in
      not-yet-migrated component files (flagged for HS-30-05); the 89 remaining
      `--wb-*` component refs flip correctly via the shim and are inventoried in
      evidence.
- [x] Backend sweep `uv run pytest -q --ignore=tests/e2e/test_metal.py` green
      (2062 passed, 14 skipped — no regression from the rebuilt static output).

## Test plan

- Unit / backend: `uv run pytest -q --ignore=tests/e2e/test_metal.py` (no
  regression from the rebuilt static output).
- Visual: `cd web && npm run build` then serve / `npm run dev`; screenshot
  `/design/check` and `/design/components`.
- Build: `npm run build` must exit 0 and emit to `../holdspeak/static/_built/`.

## Notes / open questions

- **Reality check on "delete `--wb-*` outright":** the original plan assumed the
  token swap would flip everything cleanly. It can't — 108 component refs hardcode
  `--wb-*`, and `--wb-white`/`--wb-black` are used context-dependently (bg *and*
  text *and* border), so no single global remap is correct for all. The honest
  resolution: a **temporary** `--wb-*`→Signal shim (still greenfield — it's a
  two-story transition aid deleted in HS-30-05, not backwards-compat for shipped
  users). The one bounded fix made now: the 16 `--wb-white` backgrounds + 2
  hardcoded `#f5f5f5` footers were retargeted to `--surface-2` so the swap yields
  a clean **dark** product, not light boxes.
- **Status of the dark flip:** the whole product reads as dark Signal after this
  (verified: `evidence/after-hs03/`). The deep per-component restyle (uppercase
  eyebrows, primary glow, depth refinement) + structural IA redesigns are the
  shell/component/page stories (HS-30-04/05/06+).
- Confirmed the FastAPI `/_built` mount still serves the rebuilt assets (preview
  200 + screenshots of live routes, not just the build).
