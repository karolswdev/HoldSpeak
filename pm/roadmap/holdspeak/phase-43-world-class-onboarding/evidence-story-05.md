# Evidence — HS-43-05 — Settings redesign

- **Shipped:** 2026-06-06
- **Commit:** this commit on branch `phase-43-world-class-onboarding`
- **Owner:** unassigned

## What shipped

The Phase-42 single-scroll **form dump** is retired. `/settings` is now a
**sectioned, searchable, progressive** surface — same `GET`/`PUT /api/settings`
contract + the same validator, just a far better shape.

### The redesign — `web/src/pages/settings.astro` + `settings-app.js`

- **Sticky left-nav** of five sections — **Appearance · Voice typing · Desktop
  presence · Meetings & intel · Cloud & advanced** — the active one shown one at a
  time (no endless scroll), the active item accent-bordered.
- **Search** — typing flattens to just the fields whose keywords match (each field
  carries a small keyword string so search finds it by more than its label); the
  section chrome hides in search mode.
- **Common / Advanced progressive disclosure** — a "Show advanced" toggle reveals
  the rarely-touched fields (retry/webhook/devices/model-paths); the everyday
  fields show by default.
- **The config-backed presence toggle (HS-43-04) lives here** — a real switch
  bound to `settings.presence.enabled` ("Save to apply live. No environment
  variable.").
- Pure **view-model** (`fieldVisible(section, tier, keywords)` / `sectionVisible`)
  so the section/search/disclosure logic is testable.

## Verification

- **Live (Playwright):** the section nav switches panels; the presence section
  shows the toggle; flipping it + **Save** → "Settings saved. Runtime
  configuration updated." with **`config.presence.enabled: True` on disk**;
  searching "webhook" flattened to **3 matching fields**.
  Screenshots: [`settings_appearance.png`](./evidence/settings_appearance.png)
  (the sectioned default), [`settings_presence_section.png`](./evidence/settings_presence_section.png)
  (the presence toggle), [`settings_search.png`](./evidence/settings_search.png).

## Tests run

```
uv run pytest -q tests/integration/test_web_settings_page.py   → 4 passed
```

- `test_settings_is_sectioned_searchable_and_progressive` — the section nav +
  search + `Show advanced` + the view-model (`fieldVisible`/`sections`/`searching`)
  + the five sections + the presence switch bound to `settings.presence.enabled`.
- The existing `test_settings_route_serves_the_settings_page` /
  `test_no_interim_settings_drawer_in_live_source` still pass (the surface stays a
  real `/settings`, no interim drawer).

Full suite: see the HS-43-05 commit message.

## Acceptance criteria

- [x] Settings is sectioned + searchable + progressive (Common/Advanced) — no
      single-scroll form dump.
- [x] The save round-trip still works (proven live: save → disk); the config-backed
      presence toggle is in Settings.
- [x] Screenshot; suite green.
