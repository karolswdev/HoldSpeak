# Screenshot Index

Screenshots are captured from the local running app and stored in
[`screenshots/`](./screenshots/).

Captured: 2026-04-29 from the rebuilt Astro frontend (HS-10-13).
The capture script is `designer-handoff/capture-screenshots.py`;
it accepts a `--base-url` argument so it can target either the
running `holdspeak` web runtime or the Astro dev server (which
serves under the `/_built/` base path during development).

## Capture Matrix

| File | Route | Viewport | Review Focus |
|---|---|---|---|
| `dashboard-desktop.png` | `/` | 1440 x 1000 | Runtime hierarchy, idle/active affordances, nav clarity |
| `activity-desktop.png` | `/activity` | 1440 x 1100 | Ledger layout, candidates, rules, connector-adjacent density |
| `activity-mobile.png` | `/activity` | 390 x 1200 | Responsive stacking, button wrapping, dense list readability |
| `history-desktop.png` | `/history` | 1440 x 1100 | Meeting review layout, saved-state hierarchy |
| `dictation-desktop.png` | `/dictation` | 1440 x 1100 | Technical configuration layout, editor density |

## Notes For Review

- Screens are captured against an idle local runtime; empty
  states are intentional.
- Connector APIs for GitHub and Jira exist; first-class UI
  controls are now feasible on top of the phase-10 component
  library and are tracked under **phase 11** (Local Connector
  Ecosystem).
- These screenshots are the reference implementation of the
  phase-10 design system, not a final visual design — the system
  is the source of truth (see `style-handoff.md`).
