# Evidence — HS-42-02 — Global settings completion

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-42-first-run-delight`
- **Owner:** unassigned

## What shipped

The interim Settings drawer is **retired** and the "History → Settings" move is
**complete** — a real, shell-level `/settings` route the gear opens on every page.

### The real surface — `web/src/pages/settings.astro` + `settings-app.js`

A Signal-styled global settings page (the content lifted out of the History
"Settings" tab): grouped cards (**Appearance & UI · Core · Cloud intel**) with
accent-edged headers, a "Local · 127.0.0.1" chip, two-column responsive field
grids, inline validation, and a **sticky save bar** with a saved/error message.
Backed by `GET`/`PUT /api/settings` via a dedicated `settingsApp()` Alpine
factory (the load + the full validator ported verbatim from the old tab).

### The shell — interim drawer deleted

- `AppLayout.astro`: the entire `.settings-overlay` drawer + its
  "consolidating / The full move from History → Settings lands in HS-30-08 /
  Open History → Settings" interim copy + the drawer open/close script + the
  drawer CSS are **deleted**. The legacy `#settings` deep link is preserved by
  redirecting it to `/settings`.
- `TopNav.astro`: the gear is now an `<a href="/settings">` (was the
  `data-settings-open` drawer button).
- `holdspeak/web/routes/pages.py`: the server `/settings` route (which aliased
  to the history page) now serves the built `_built/settings/index.html`, with a
  graceful "not built" fallback.

### History page — settings tab removed

`history.astro`: the "Settings" tab button + its ~220-line `tab === 'settings'`
template are removed. `history-app.js` keeps a **read-only** `loadSettings()`
(the intel-queue alert-threshold getters read `settings.meeting.*`); the
tab-only editing logic (`saveSettings`, `validateSettingsPayload`,
`savingSettings`, `settingsValidationErrors`, `loadingSettings`, the `setTab`
settings branch) is removed.

## Verification

- **Save round-trip proven live** (Playwright against the real server):
  set History lines = 37 in the UI → **Save** → "Settings saved. Runtime
  configuration updated." → **reload** → the field shows 37 **and**
  `config.json` on disk is `ui.history_lines: 37`. `ROUND-TRIP OK`.
- Screenshot: [`evidence/settings_page.png`](./evidence/settings_page.png) —
  the three Signal cards, the local chip, and the sticky save bar, with live
  config loaded from `/api/settings`.
- `npm run build` clean (`/settings/index.html` generated).

## Tests run

```
uv run pytest -q tests/integration/test_web_settings_page.py
→ 3 passed
```

- `test_settings_route_serves_the_settings_page` — `GET /settings` 200,
  build-agnostic (the real page when built, the fallback otherwise).
- `test_no_interim_settings_drawer_in_live_source` — the drawer's signature
  markers (`consolidating` / `settings-interim` / `data-settings-open` /
  `data-settings-overlay`) are gone from live `web/src`.
- `test_topnav_gear_links_to_settings_route` — the gear links to `/settings`.

Full suite: see the HS-42-02 commit message.

## Acceptance criteria

- [x] A real global-settings surface exists, reachable from the shell gear on
      every route; page-local settings (the `/dictation` cockpit) unchanged.
- [x] **No live product copy** says "consolidating" / "History → Settings" /
      the interim drawer markers — guarded by a test.
- [x] The `#settings` deep link still resolves (redirects to `/settings`).
- [x] Bundle rebuilt; only `web/src` committed (no `_built/`); a Playwright
      round-trip confirms save→reload→disk; screenshot captured.
- [x] Default suite green; existing settings round-trips unchanged
      (same `/api/settings` contract).
