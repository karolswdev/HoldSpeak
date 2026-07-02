# HS-73-05 — Zones as landmarks: file and dive

- **Status:** todo
- **Priority:** MED (zones are the desk's geography; flat trays make a flat world)
- **Depends on:** HS-73-01

## Goal

Zones stop being labeled rectangles ("Q3 release · 0 items") and become the
painted, inhabited trays the iPad draws (`ZoneRec`,
`DeskDioramaStage.swift:~305`): member sprite thumbnails, a count, a
per-zone tint, a lift-on-drag-over affordance, an inline hint when empty —
and dive/back becomes a camera move.

## Scope

- **In:** the `ZoneTray` restyle; membership thumbnails; drop affordance;
  file-on-drop; dive/back transition; the empty hint; zone rename-in-place
  (with HS-73-03's editor).
- **Out:** zone geometry sync (layout NEVER syncs — identity + membership
  only, which the `PUT` already honors); nested zones; an authored zone
  paint editor (tint is derived from the stable hash, not authored).

## Tasks

- [ ] `ZoneTray`: a shallow painted tray (gradient face + hairline rim from
      the Signal tokens), tinted per zone via the djb2 hash from
      `sprites.ts` (stable forever per id); up to ~4 member mini-sprites
      (membership from the `directoriesFor`/`memberOf` maps,
      `desk-app.js:691/752`, rendered at thumbnail size) + a bare count,
      `+N` overflow.
- [ ] File on drop: the drag hit-tests fresh tray rects at release (the
      HS-71-05 mid-drag-layout lesson); on drop, fire
      `PUT /api/directories/{id}/members/{pid}` and fly the sprite into
      the tray (a `motion` spring); the tray count/thumbnails update from
      state, no reload.
- [ ] Drag-over affordance: the tray lifts + brightens while a dragged
      object is above it.
- [ ] Dive as a camera move: `diveInto` scales/fades the world toward the
      tray; the zone's members settle into the full stage; a floating
      `← All` chip surfaces back. Reduced-motion: instant swap.
- [ ] Empty tray: one whispered inline hint on the tray (`drop things
      here`) — iPad empty-zone parity (PR #191), never a paragraph.
- [ ] `+ Zone` chip (HS-73-03) drops a new tray with rename-in-place
      focused.

## Proof required

Screenshots: populated trays (thumbnails + tints), the drag-over lift, the
empty hint, mid-dive and dived states. Playwright: drop → the `PUT` fires →
tray updates without reload; dive → back restores positions.
Reduced-motion verified. Route pre-flight + full suite + `npm run build`
green.
