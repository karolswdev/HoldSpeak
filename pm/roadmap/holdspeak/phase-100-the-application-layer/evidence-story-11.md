# Evidence - HS-100-11

- **Story:** HS-100-11 - B7: one launcher
- **Status:** done
- **Date:** 2026-07-19

## Proof

### Captured run — 2026-07-19T15:19:54Z

- **Command:** `sh -c HS_WALK_BASE=http://localhost:8792 HS_WALK_TOKEN=YZi6W-PzL8bfY4UbMgxThqUdUUKQcGj8 uv run python scripts/desk_gl_walk.py chrome 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4fbb94d6bd3e23112af461f7cbbf1382411a4fd9

```text
one-launcher: dock carries the four apps; search reaches every app and tool; the bar is system truth
chrome walk: the bar (two-tone, square verbs, red close), head menu, skinned selects, drawn scrollbar (headed), square maximize corners, dock underline — all present; shots at 1440 and 393
```

## Summary of proof

- **The dock IS the launcher**: the four applications (Speak ⌁,
  Meetings ▣, Agents ◉, Settings ⚙) ride it always with running/front
  marks; an app's window folds into its chip (focus/restore/context
  menu); the record orb stays center; the drawer chips left it.
- **The system bar is system truth**: HoldSpeak menu (the four apps +
  the desk, plus the desk verbs List/Arrange/Refresh it absorbed),
  trust badge, the attention BELL (the approve-queue badge moved out
  of the dock), Search ⌘K, the clock. The daily-start chips left the
  bar — they live on the arrival and the dock.
- **The shelf is the ⌘K search palette**: trigger renamed, prose line
  deleted, the four applications joined its reach, and the dockless
  drawers (Delivery board, Panes) surface as a searchable Drawers
  section over the same launcher registry.
- **Pinned live** (captured, HEADED): the chrome leg extended — the
  dock carries exactly the four apps, `.desk-start-actions` is absent
  from the bar, and the search palette reaches every application and
  tool by name; the traffic-light and head-menu asserts retargeted to
  the owner-approved spike chrome. speakflow (4 interactions) and the
  full meetings leg re-ran green on the new launcher (dock chip + orb).
  vitest 296/296 (three pins retargeted); chrome/desk pytest clusters
  green. Screenshots: assets/hs-100-11-launcher-*.png + search shelf.
