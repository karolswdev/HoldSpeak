/**
 * HS-118-04 — @-reference tokenizer: pure resolver functions.
 *
 * Resolves zone names from text (typed @-references or voice transcripts).
 * No React dependencies, no side effects — fully unit-testable.
 *
 * The resolver never recomputes normalization in JavaScript; it compares
 * the query's lowercased form against the stored `nameNormalized` values
 * from the API (computed by Python per HS-118-01).
 */
import type { Directory } from "./primitives";

/** A resolved zone reference — the grounding tray's unit. */
export interface ResolvedRef {
  /** Matched zone name (display form). */
  name: string;
  /** Zone id (dir_...). */
  id: string;
  /** Qualified ref (zone:dir_...). */
  ref: string;
  /** Primitive kind ("zone" for now). */
  kind: string;
}

/**
 * Case-insensitive exact match of `query` against zone `nameNormalized`
 * values. Returns the first match or null. Since zone names are globally
 * unique (HS-118-01), there is at most one match.
 */
export function resolveDrawerName(
  query: string,
  zones: Directory[],
): ResolvedRef | null {
  const normalized = query.toLowerCase();
  for (const zone of zones) {
    if (zone.nameNormalized === normalized) {
      return {
        name: zone.name,
        id: zone.id,
        ref: `zone:${zone.id}`,
        kind: "zone",
      };
    }
  }
  return null;
}

// Boundary characters for word-boundary matching.
// Do NOT use regex \b — inconsistent Unicode behavior across engines.
const BOUNDARY_CHARS = new Set([
  " ", "\t", "\n", "\r",
  ".", ",", ";", ":", "!", "?", "'", '"', "(", ")", "-",
]);

function isBoundary(ch: string | undefined): boolean {
  return ch === undefined || BOUNDARY_CHARS.has(ch);
}

/**
 * Scans `text` for zone names as complete phrases at word boundaries.
 * Longest-match-first. Case-insensitive via stored `nameNormalized`.
 * Deduplicates. Returns resolved refs and the text with matches removed.
 */
export function resolveDrawerNames(
  text: string,
  zones: Directory[],
): { refs: ResolvedRef[]; cleanText: string } {
  if (!text || zones.length === 0) {
    return { refs: [], cleanText: text };
  }

  // Sort zones by name length DESC (longest-match-first).
  const sorted = [...zones].sort((a, b) => b.name.length - a.name.length);

  const lowerText = text.toLowerCase();
  const refs: ResolvedRef[] = [];
  const seenIds = new Set<string>();

  // Track which character positions have been consumed by a match.
  const consumed = new Array<boolean>(text.length).fill(false);

  for (const zone of sorted) {
    const normalized = zone.nameNormalized;
    if (!normalized) continue;

    // Scan for all occurrences of this zone name in the lowered text.
    let searchFrom = 0;
    while (searchFrom <= lowerText.length - normalized.length) {
      const idx = lowerText.indexOf(normalized, searchFrom);
      if (idx === -1) break;

      const endIdx = idx + normalized.length;

      // Check that this span hasn't been consumed by a longer match.
      let overlap = false;
      for (let i = idx; i < endIdx; i++) {
        if (consumed[i]) {
          overlap = true;
          break;
        }
      }

      if (!overlap) {
        // Check word boundaries.
        const charBefore = idx > 0 ? lowerText[idx - 1] : undefined;
        const charAfter = endIdx < lowerText.length ? lowerText[endIdx] : undefined;

        if (isBoundary(charBefore) && isBoundary(charAfter)) {
          // Mark consumed.
          for (let i = idx; i < endIdx; i++) {
            consumed[i] = true;
          }

          // Deduplicate.
          if (!seenIds.has(zone.id)) {
            seenIds.add(zone.id);
            refs.push({
              name: zone.name,
              id: zone.id,
              ref: `zone:${zone.id}`,
              kind: "zone",
            });
          }
        }
      }

      searchFrom = idx + 1;
    }
  }

  // Build cleanText: remove consumed spans and collapse whitespace.
  let clean = "";
  for (let i = 0; i < text.length; i++) {
    if (!consumed[i]) {
      clean += text[i];
    }
  }
  // Collapse multiple spaces into one and trim.
  clean = clean.replace(/\s+/g, " ").trim();

  return { refs, cleanText: clean };
}
