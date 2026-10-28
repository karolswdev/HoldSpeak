/** PHILO-15 lane 12 (B24): a card's first-open size, by kind.
 *
 * A card fits its material (`fitContent`), so the placement engine seeds it
 * at whatever height its content has at first measure. A list card that
 * reads its items after it opens (Intelligence) was measured small and
 * seated low: 390 x 300 px, its tabs stacked, its items below the fold.
 * A kind named here opens at this size (clamped into the work band by
 * `placeWindow`); a saved size always wins (DeskWindow keeps `panelRects`).
 *
 * The width keeps the Intelligence tabs on one row: they stack when the
 * window body is 420 px or less (intelligence.css). */
export const PULLOUT_SIZE: Partial<Record<string, { w: number; h: number }>> = {
  // Owner 2026-10-27: a note opens as a document window, wide enough that
  // its toolbar (Done · Ask about this · Find the tasks · Project · Send) is
  // one row. The loading frame seats the note window at this size, and the
  // note window keeps that seat.
  note: { w: 760, h: 560 },
  intelligence: { w: 880, h: 700 },
  thread: { w: 740, h: 680 },
  // W1-TRUTH (atlas 2026-10-27): the decision reads on the reader grammar
  // (toolbar, the decision, a status bar); 640 px left 300 px of blank
  // under a short decision. A long one scrolls in its body. W3-A: this is the
  // first seat only; the window fits its content between 320 and 640 px
  // (Pullout fitContent, decisions.css).
  decision: { w: 680, h: 440 },
  // PHILO-17: a meeting is a whole window (its record, its wings, its foot).
  meeting: { w: 720, h: 600 },
  // PHILO-17 (2b): a person is a whole window (the six lenses on one row).
  people: { w: 640, h: 560 },
  room: { w: 760, h: 480 },
  // W2-BUILDER (atlas 2026-10-27): the builder windows on the grammar; the
  // toolbar's verbs fit one row, the material and its Run below.
  recipe: { w: 560, h: 640 },
  chain: { w: 560, h: 560 },
  workflow: { w: 560, h: 520 },
  kb: { w: 560, h: 420 },
  // W3-ZONE (atlas 2026-10-27): a zone drawer opens wide enough that its
  // list rows stay one line (Name · Kind · When).
  directory: { w: 640, h: 440 },
  // Settings is hosted by SurfaceWindows, but stays in this table so the
  // first-open matrix has one source of truth for every desk room.
  settings: { w: 1040, h: 720 },
};
