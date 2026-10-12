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
  intelligence: { w: 880, h: 700 },
  // PHILO-17: a meeting is a whole window (its record, its wings, its foot).
  meeting: { w: 720, h: 680 },
  // PHILO-17 (2b): a person is a whole window (the six lenses on one row).
  people: { w: 640, h: 640 },
};
