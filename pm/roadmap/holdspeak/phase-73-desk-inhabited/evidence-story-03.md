# Evidence — HS-73-03 — Create in-world (no modals, ever)

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-73-desk-inhabited`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **Create is instant and in-world.** The chips POST immediately (default
  title), the created object **spawns at stage center** (a persisted unit
  position — the iPad grammar: it appears in front of you and you drag it
  away), wears the HS-71-06 create beat (accent glow + 3-pulse ring + NEW
  badge, values verbatim, settling at 4.5s) plus a materialize entrance,
  and its editor opens focused.
- **The object IS the editor** (`InlineEditor`): anchored to the object's
  free side on the stage; the world dims AROUND it via a radial vignette
  centered on the object (never a flat scrim — the vignette is also the
  click-away catcher); the float settles while editing. Saves are
  **on-change** (450ms debounced PUTs through the real update routes, with
  an optimistic local merge so the world's label tracks typing) — nothing
  can be lost; Escape and click-outside close and settle to the saved
  truth.
  - Note: title + markdown body + tags.
  - KB: name.
  - Agent: the essential trio visible; **More expands in the same card**
    (template, tools, KB picker, profile picker) — expansion, not a second
    surface.
- **Zones rename in place** on the tray (click the title → input →
  Enter/blur commits via `PUT /api/directories/{id}`, Escape cancels;
  optimistic local rename).
- **Tap ≠ drag, fixed properly**: a moved gesture clears its drag state
  next-tick (the click reads it and never opens); a plain tap clears
  synchronously (the click opens the editor). The first implementation
  suppressed taps too — caught by the proof run's "tap reopens" step.

## Verification artifacts (Playwright, real hub, scratch DB)

- `+ Note` → materialize + NEW badge asserted → editor focused
  (`03-create-editor.png` — the vignetted world with the editor at the
  object's side) → typed title/body/tags → **reload** → the title renders
  AND the DB row carries `title="Closeout ritual"`, `tags=["phase",
  "ritual"]` (the real round-trip, not local state).
- Escape closed the editor; click-outside (the vignette) closed it; a tap
  on the object reopened it.
- Zone rename: click → type → Enter → the directory row's name updated in
  the DB.
- `+ Agent` → essentials editor → More expanded two pickers **in the same
  card** (`03-agent-more.png`).
- `grep -rn 'aria-modal|role="dialog"' web/src/desk` → zero (after
  rewording a comment that name-dropped the banned attribute — the
  HS-73-09 lock will match attribute syntax).
- Zero page errors across the run. Build 18 pages; vitest 9/9; pre-flight
  2 passed. Full suite: **3065 passed, 37 skipped, and exactly ONE
  failure — the HS-72-02 manifest guard catching this story's new island
  call sites** (the PUT routes gained a web consumer tag); regenerated,
  guard 5/5. The declared surface keeps earning its keep.

## Acceptance criteria — re-checked

- [x] Create is instant (POST first, then edit) — the device-gap rule.
- [x] Edit in place; the world dims around, never a scrim; no
      dialog/modal patterns in the tree.
- [x] Autosave on change; Escape/click-outside settle; nothing lost.
- [x] Agent's advanced fields expand inside the same card.
- [x] Zone rename-in-place through the real route.

## Deviations from plan

- The materialize entrance is a CSS keyframe rather than a `motion`
  spring: a one-shot entrance is exactly what CSS does best; `motion`
  remains reserved for the pull-out choreography (HS-73-04), where
  interruptible springs genuinely earn their keep.
- The KB editor edits `name` only — the KB wire shape has no body; members
  arrive by filing (HS-73-05).

## Follow-ups

- HS-73-04 reuses `InlineEditor` inside the pull-out's Edit affordance.
