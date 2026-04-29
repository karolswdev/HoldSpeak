# Screenshot Index

Screenshots are captured from the local running app and stored in
[`screenshots/`](./screenshots/).

Captured: 2026-04-28 from `http://127.0.0.1:64524`.

## Capture Matrix

| File | Route | Viewport | Review Focus |
|---|---|---|---|
| `dashboard-desktop.png` | `/` | 1440 x 1000 | Runtime hierarchy, idle/active affordances, nav clarity |
| `activity-desktop.png` | `/activity` | 1440 x 1100 | Ledger layout, candidates, rules, connector-adjacent density |
| `activity-mobile.png` | `/activity` | 390 x 1200 | Responsive stacking, button wrapping, dense list readability |
| `history-desktop.png` | `/history` | 1440 x 1100 | Meeting review layout, saved-state hierarchy |
| `dictation-desktop.png` | `/dictation` | 1440 x 1100 | Technical configuration layout, editor density |

## Notes For Review

- Screens may show empty states because the app uses local machine data.
- Connector APIs for GitHub and Jira exist, but connector controls are not yet
  first-class UI controls on `/activity`; that is the next design-critical gap.
- Treat these screenshots as implementation references, not final visual design.
