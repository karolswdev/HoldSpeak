# HS-73-05 — Zones as landmarks

- **Status:** todo
- **Priority:** MED (zones are the desk's geography; flat trays make a flat world)
- **Depends on:** HS-73-01

## Goal

Zones stop being labeled rectangles ("Q3 release · 0 items") and become the
painted, inhabited trays the iPad draws (`ZoneRec`,
`DeskDioramaStage.swift:~305`): member sprite thumbnails, a count, a
per-zone tint, a hover/drop affordance, an inline hint when empty, and a
dive/back that feels like a camera move instead of a filter toggling.

## Scope

- **In:** the tray restyle; member thumbnails; tint; drop affordance; the
  empty hint; the dive/back transition; the zone rename-in-place (from
  HS-73-02).
- **Out:** zone geometry sync (layout NEVER syncs — the Primitive Framework
  rule; identity + membership only, which `fileIntoDir`'s
  `PUT /api/directories/{id}/members/{pid}` already honors); nested zones;
  the iPad's zone-paint editor (tint here is derived, not authored).

## Tasks

- [ ] Restyle `zoneStyle` / the `.desk-zone` markup (`desk-app.js:355`,
      `components/desk/DeskWorld.astro`): a shallow painted tray (gradient
      face + hairline rim from the Signal tokens), tinted per zone via the
      djb2 stable hash (`window.__deskSprites` exposes the hash; same
      family the sprite picker uses so a zone keeps its color forever).
- [ ] Member thumbnails: up to ~4 mini-sprites of the zone's members
      (resolve via the membership map behind `memberOf`/`directoriesFor`,
      `desk-app.js:752/691`, rendered with `objSprite` at thumbnail size)
      + a bare count. Overflow shows `+N`.
- [ ] Drop affordance: while an object drag is live and the pointer is over
      a tray (the drag handler already hit-tests fresh `.desk-zone` rects —
      HS-71-05's fix), the tray lifts + brightens; on drop, the filed
      object's sprite flies into the tray (the `hs-materialize` motion
      reversed or a simple transform — cheap, CSS-only).
- [ ] Empty zone: the inline hint ON the tray (`drop things here`, one
      whisper, iPad's empty-zone parity from PR #191) — not a paragraph.
- [ ] Dive/back as a camera move: `diveInto`/`surface`
      (`desk-app.js:375/379`) get a transition — the world scales/fades
      toward the tray, the zone's members settle into the full stage, the
      breadcrumb becomes a floating back chip (`← All`). Reduced-motion:
      instant swap, no scale.
- [ ] Zone create (`+ Zone` chip from HS-73-02) drops a new empty tray with
      rename-in-place focused.

## Proof required

Screenshots: populated trays with thumbnails + tints; the drag-over lift;
an empty tray's hint; mid-dive and dived states. Playwright: drop → the
`PUT` fires → the tray count/thumbnails update without reload; dive → back
restores positions. Reduced-motion verified. Route pre-flight + full suite
+ `npm run build` green.
