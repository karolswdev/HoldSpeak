# Evidence — HS-71-05: Zones as shelves — file and dive

**Date:** 2026-07-01
**Verdict:** done. Directories are painted shelf-zones you drag objects onto to
file (a real API write) and dive into to see their contents, with a way back.
The desk is a place to organize now, not just a pretty scatter.

## What shipped

- **`web/src/scripts/desk-app.js`**:
  - `worldObjects()` now **excludes directories** (they are zones) and, when
    dived, filters to that zone's members.
  - `worldZones()` returns directories as shelf-zones (hidden while dived);
    `zoneStyle` lays them across the top of the stage.
  - `fileIntoDir(pid, dirId)` — an add-only **`PUT /api/directories/{id}/
    members/{pid}`** with an optimistic `memberIds` update (the real filing API,
    the same one the iPad uses).
  - `diveInto(zoneId)` / `surface()` / `divedZoneName()` — the "level" state.
  - The drag handler (HS-71-04) now **files on drop**: at pointerup it hit-tests
    the live `.desk-zone` rects; a drop on a zone files the object there (and
    drops its free position) instead of leaving it loose.
  - Robustness fix found on the way: the object now tracks the pointer using a
    **fresh world rect each move** (a mid-drag layout shift — the "Tidy" button
    appearing — used to desync the delta math and the drop hit-test).
- **`web/src/pages/desk.astro`**:
  - zones render inside the world (`.desk-zone`, a tinted painted shelf with a
    folder glyph + label + member count; `data-zone-id` for the hit-test),
  - a dive breadcrumb ("← All primitives · <zone>") + an empty-dive guide,
  - all `<style is:global>` (Alpine-injected).

## Proof

- **File-by-drag (Playwright, real API):** dragging an object onto the "Q3
  release" zone fired the `PUT` and the zone read **"1 item"**; diving in showed
  exactly that **1 member** with the "← All primitives" back control
  (`dived objects: 1, dive bar: True`). Filing is the real write, not a local
  fake.
- **`screenshots/05-zones.png`** — the "Q3 release" shelf-zone among the
  floating objects. **`screenshots/05-dived.png`** — dived in: the breadcrumb +
  only the filed member.
- **Tests:** route pre-flight **2 passed** (zero page errors on `/desk`); full
  suite **3045 passed, 37 skipped**; build green.
