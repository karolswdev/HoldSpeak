# HS-30-03 — Foundation: tokens + global CSS + fonts + design galleries

- **Project:** holdspeak
- **Phase:** 30
- **Status:** backlog
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

- [ ] `tokens.css` + `global.css` contain the Signal system; **zero** `--wb-*`
      tokens, zero `VT323`/`Sora` references remain in either file.
- [ ] `web/package.json` adds Space Grotesk + Inter, removes VT323 + Sora;
      `npm install` clean.
- [ ] `npm run build` is green; `/design/check` + `/design/components` render in
      Signal (screenshots in evidence).
- [ ] `grep -rE "wb-|VT323|Sora" web/src` returns only references explicitly
      deferred to HS-30-05 (listed in evidence) — ideally none.
- [ ] Backend sweep `uv run pytest -q --ignore=tests/e2e/test_metal.py` green
      (UI change must not break the served runtime).

## Test plan

- Unit / backend: `uv run pytest -q --ignore=tests/e2e/test_metal.py` (no
  regression from the rebuilt static output).
- Visual: `cd web && npm run build` then serve / `npm run dev`; screenshot
  `/design/check` and `/design/components`.
- Build: `npm run build` must exit 0 and emit to `../holdspeak/static/_built/`.

## Notes / open questions

- Greenfield: delete Workbench tokens outright — no aliasing old `--wb-*` names to
  new ones (the product is not yet released; no external CSS contract).
- The static output ships under `/_built`; confirm the FastAPI runtime still
  serves the rebuilt assets (smoke the running app, not just the build).
