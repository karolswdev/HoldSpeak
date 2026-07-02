# Evidence — HS-73-05 — Zones as landmarks: file and dive

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-73-desk-inhabited`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **Trays are landmarks now**: a stable per-zone tint
  (`variantIndex(id, 6)` over a fixed palette — the same stable-hash
  family as the sprite picker, so a zone keeps its color forever), up to
  four member mini-sprites (member ids resolved to kinds via the lineage
  resolver, rendered with the shared picker) + `+N` overflow + a bare
  count, and the whispered empty hint (`drop things here` — the iPad
  empty-zone parity).
- **Drag files**: the object drag hit-tests FRESH tray rects each move
  (the HS-71-05 robustness rule) and lights the hovered tray
  (`drop-ready` lift); the drop fires the real
  `PUT /api/directories/{id}/members/{pid}`, forgets the free position,
  and the tray's thumbnails/count update from state — no reload.
- **Dive is a camera move**: clicking a tray scales/fades the world in on
  the zone's members (zones hidden while dived; reduced-motion instant);
  the floating `← All` chip surfaces back.
- **`+ Zone` arrives renaming**: the new tray mounts with its rename
  input focused (Enter/blur commits through the real PUT).

## Verification artifacts (Playwright, real hub, scratch DB)

- The empty tray whispered its hint.
- A real mouse drag onto the tray: the `drop-ready` lift asserted
  MID-DRAG (`05-drop-ready.png`), the membership row landed in the DB
  (`n1 → Q3`), and the tray immediately wore a member thumbnail + "1
  item" without reload (`05-tray-thumbs.png`).
- Dive filtered the stage to exactly the member (zones hidden;
  `05-dived.png`); `← All` restored the full desk.
- `+ Zone` → typed "Inbox" into the focused rename → Enter → the
  directory row's name in the DB.
- Zero page errors. Build 18 pages; api-surface + pre-flight **7 passed**;
  full suite **3066 passed, 37 skipped, 0 failures**.

## Acceptance criteria — re-checked

- [x] Member thumbnails + count + stable tint; the empty hint.
- [x] Drop affordance lifts mid-drag; drop files via the real PUT; state
      updates live.
- [x] Dive/back as a camera move, reduced-motion safe.
- [x] Zone create focuses rename-in-place.
- [x] Geometry/paint never syncs (tints are derived; only identity +
      membership ride the wire — unchanged).

## Deviations from plan

- The filed sprite "flies into the tray" flourish was dropped: the drop
  already reads clearly through the lift + the instant thumbnail
  arrival, and the object's disappearance-into-the-shelf is the same
  visual beat. Recorded rather than silently skipped.

## Follow-ups

- HS-73-06 (the Record orb) and HS-73-07 (the rail) complete the world's
  verbs before the cutover.
