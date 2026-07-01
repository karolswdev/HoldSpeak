# HS-71-05 — Zones as shelves: file and dive

- **Status:** todo
- **Priority:** MED
- **Depends on:** HS-71-04
- **Evidence:** _(added at close)_

## Goal

Bring the spatial organization the iPad desk has: directories are painted
shelf-zones you drag objects onto to file them, and dive into to see their
contents. This is what makes it a place, not just a pretty scatter.

## Scope

- Render `directory` primitives as **shelf-zones** (the web port of the iPad
  `DioZoneTray`): a low-profile painted area with a tint, a label, and a member
  count, placed on the stage (its own local geometry in `localStorage`).
- **File by drag** — dropping an object onto a zone files it via the existing
  `PUT /api/directories/{id}/members/{primitive_id}` (and unfile via `DELETE`);
  the object animates into the zone. Reuse the desk-app filing calls already in
  `desk-app.js`.
- **Dive** — activating a zone enters it (a "level"): a spring/scale transition
  shows only that zone's members, with a clear **back** control to the top desk.
  Nesting follows the directory contract (identity/nesting only; geometry local).
- Empty zone + empty dive states guide (reuse the HS-70-07 empty-state idiom).

## Proof required

Playwright: drag an object onto a zone → it files (the `PUT` fires; the member
count updates); dive into the zone → only its members show + a working back
control; screenshots of a filed desk and a dived level. Filing is the real API
call, not a local-only fake.

## Done

_(filled at close)_
