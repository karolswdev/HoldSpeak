/** PHILO-8-01 — the free default zone name (the owner's Q1 (a), 2026-09-26).
 *
 * The hub refuses a second live zone whose name is the same after its rule
 * (`holdspeak/db/primitives.py:60-68`, `normalize_zone_name`): strip, collapse
 * whitespace, NFC, casefold. New Zone used to post "New zone" every time, so
 * the second press answered `409 zone_name_taken` (FINDING S1). The store now
 * picks the first free name: "New zone", then "New zone 2", "New zone 3", …
 * The hub's rule stays; a race with another client still gets its 409. */

export const DEFAULT_ZONE_NAME = "New zone";

/** The hub's rule in full. JavaScript has no `casefold`; upper-then-lower
 * folds the cases it adds over `toLowerCase` ("ß" → "ss", "ﬁ" → "fi"). */
export function normalizeZoneName(raw: string): string {
  return String(raw ?? "")
    .trim()
    .replace(/\s+/g, " ")
    .normalize("NFC")
    .toUpperCase()
    .toLowerCase();
}

/** The first default name no zone holds. A zone's hub-normalized name
 * (`name_normalized`) counts, and so does the store's own normalization of
 * its display name. A name the owner chose is never changed: it is skipped. */
export function nextFreeZoneName(
  zones: ReadonlyArray<{ name?: string | null; nameNormalized?: string | null }>,
): string {
  const taken = new Set<string>();
  for (const zone of zones) {
    if (zone.nameNormalized) taken.add(zone.nameNormalized);
    if (zone.name) taken.add(normalizeZoneName(zone.name));
  }
  for (let n = 1; ; n += 1) {
    const candidate = n === 1 ? DEFAULT_ZONE_NAME : `${DEFAULT_ZONE_NAME} ${n}`;
    if (!taken.has(normalizeZoneName(candidate))) return candidate;
  }
}

/** PHILO-8-01 — a count of face changes (Chair / Floor, list / spatial).
 * A rename begins on the face where New Zone was pressed; when the face
 * changed while the create was still landing, the rename is not started on
 * the new face (the stale field of FINDING Finding 1). */
let faceChanges = 0;

export function noteFaceChange(): void {
  faceChanges += 1;
}

export function faceChangeCount(): number {
  return faceChanges;
}
