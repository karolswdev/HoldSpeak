# Evidence - HSU-1-04

- **Story:** HSU-1-04 - The guided site
- **Status:** done
- **Date:** 2026-07-09

## What shipped

`uat/web/` (a React+Vite SPA, dark Signal-grade) + `uat/conductor/sittings.py`
+ sitting routes:

- **The site** — home (pack coverage pills + past sittings + resume), staging
  panel (each recipe verified live, or the failure with the product's own log
  tail + retry/abort — never a spinner), the beat-by-beat walkthrough (do /
  expect, an "Open the product" deep-link to the run's product URL at `where`,
  **one verdict slot per applicable surface** — web/iPad/iPhone, each
  pass/fail/partial/skip + note + screenshot), an `n/a` surface rendered with
  its reason and excluded from the completion math, mid-run conductor actions
  (the mesh kill) firing between steps, and a sitting-end tally.
- **The backend** — a `sittings` table + `SittingManager`: create (boots an
  isolated run), stage a scenario (applies its recipes), cast a verdict (written
  to the run DB the moment cast, keyed (scenario, step, surface)), upload a
  screenshot, run a step's after-actions, resume (first unanswered slot), finish.
- **Build posture** — commit-built: `uat/web/dist` is committed so
  `uv run python -m uat.conductor` serves the site with no npm step for the owner.

## Playwright drive (labelled harness self-test)

`scripts/uat_site_walk.py` drives the real site with chromium and captures:

- `assets/site-01-home.png` — the pack chooser with per-surface coverage pills.
- `assets/site-02-walkthrough.png` — a staged step with three surface verdict cards.
- `assets/site-03-verdict-cast.png` — a `pass` cast on web (green, "cast: pass").
- `assets/site-04-phone-home.png` — the layout at iPhone width (390px).

The verdicts cast here are harness self-tests, **not a sitting**. The live
device-over-LAN cross-view (a verdict from a real iPad/iPhone) is owner-gated
and rides HSU-1-06.

## Store tests (`npm test` in `uat/web/`)

```text
✓ src/store.test.js (5 tests)
Test Files  1 passed (1)
     Tests  5 passed (5)
```

## Proof

### Captured run — 2026-07-09T07:44:07Z

- **Command:** `uv run pytest -q tests/uat/ --ignore=tests/uat/test_induction_integration_43.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 020f357e3c72b43252eb10003a3d71082f1caea3

```text
........................................................................ [100%]
72 passed in 16.64s
```
