# Evidence — HS-44-02 — Dictation cockpit polish

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-44-daily-surface-polish`

## What shipped
A behavior-preserving premium pass on the **dictation cockpit (`/dictation`)** —
the second daily-driver surface lifted to the Phase-43 wizard's bar. The page
previously opened as a bare tab-row dump on the canvas; it now reads as a
designed cockpit. All changes are presentation; the Alpine-free
`dictation-app.js` and every API call are untouched.

- **Cockpit hero** (`web/src/pages/dictation.astro`): an eyebrow (`Dictation`) +
  a display title (`Dictation cockpit`) + a one-line lede, the same
  eyebrow/headline grammar as the wizard's steps. Heads `<main>` above the
  section nav.
- **Ambient accent glow** (`.dictation::before` radial gradient) — the same
  top-of-page glow as the dashboard home (HS-44-01) and the wizard.
- **Premium section nav** — the `[role="tablist"]` section row is now a
  contained, elevated pill bar (`.cockpit-tabs`: surface tint + border +
  `--elev-1` + `backdrop-filter` blur) instead of loose buttons on the canvas.
  The **active** section reads as a punchy **solid accent** (specificity-scoped
  to `.scope-row.cockpit-tabs` so the in-panel block-scope row keeps its lighter
  outline — the two tab tiers are now visually distinct).
- **Depth + motion** — readiness cards lift on hover (`translateY(-2px)` +
  `--elev-1`); block-list cards gain a hover accent left-edge. Both
  reduced-motion-safe.

## Behavior preservation
The JS binds by attribute/id (`.scope-row button[data-section]`,
`[data-scope]`, `getElementById`), never by DOM position — the hero header
inserted above the nav is inert. Every `data-section`, `data-scope`, and control
id is intact (asserted in the test). Default suite green; `_built/` stays
gitignored (source-only commit).

## Verification
- **Live (Playwright):** the cockpit renders the hero, the contained pill nav
  with a solid-accent active tab, and the elevated panels. Screenshot:
  [`dictation_cockpit.png`](./evidence/dictation_cockpit.png).
- `tests/integration/test_web_dictation_cockpit.py` — the hero, the glow +
  contained nav + reduced-motion, and the preserved DOM contract (section tabs,
  block-scope row, key control ids).
- Full suite: **2325 passed, 16 skipped**
  (`uv run pytest -q --ignore=tests/e2e/test_metal.py`).

## Acceptance criteria
- [x] The dictation cockpit is visibly elevated to the wizard's bar (hero +
      glow + premium contained nav + card depth/motion); behavior unchanged
      (same app + APIs, DOM contract preserved); reduced-motion + a11y; suite
      green; 0 `_built/`.
