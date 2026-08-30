/**
 * HS-118-04 — @-reference autocomplete popover for the inlet.
 *
 * Triggered by `@` in the inlet text field. Filters zones by
 * case-insensitive prefix match, up to 8 results. Arrow keys
 * navigate, Enter/Tab selects, Escape dismisses.
 *
 * HS-151-06: extended generically to support any primitive kind
 * (meeting, note, artifact, decision, person) via AutocompleteItem.
 * Zone-only callers are unchanged.
 */
import { useEffect, useRef, type KeyboardEvent } from "react";
import type { Directory } from "../../lib/primitives";
import { PRIMITIVES } from "../../lib/primitives";
import type { ResolvedRef } from "../../lib/drawerResolver";
import { SurfaceRow, SurfaceRows } from "../surface/Surface";
import "./inlet-autocomplete.css";

const ZONE_ICON = PRIMITIVES.directory.icon;
const MAX_MATCHES = 8;

// ── HS-151-06: generic autocomplete item ────────────────────────────

/** A kind-tagged autocomplete row. Zones, meetings, notes, decisions,
 *  artifacts, and people all conform to this shape. */
export interface AutocompleteItem {
  id: string;
  kind: string;
  name: string;
  nameNormalized: string;
  detail?: string;
}

/** Text glyphs for each kind in the autocomplete list. */
const AC_GLYPH: Record<string, string> = {
  zone: "◰",     // ◰
  meeting: "●",  // ●
  note: "▤",     // ▤
  decision: "◈", // ◈
  artifact: "▣", // ▣
  person: "⊕",   // ⊕
};

/** Filter generic items by case-insensitive prefix match, sorted, max 8. */
export function filterItems(query: string, items: AutocompleteItem[]): AutocompleteItem[] {
  const lower = query.toLowerCase();
  const matches = items.filter((it) =>
    it.nameNormalized.startsWith(lower),
  );
  matches.sort((a, b) => a.name.localeCompare(b.name));
  return matches.slice(0, MAX_MATCHES);
}

/** Build a ResolvedRef from a generic AutocompleteItem. */
export function itemToRef(item: AutocompleteItem): ResolvedRef {
  return {
    name: item.name,
    id: item.id,
    ref: `${item.kind}:${item.id}`,
    kind: item.kind,
  };
}

/** Convert a Directory to an AutocompleteItem. */
export function directoryToItem(d: Directory): AutocompleteItem {
  return {
    id: d.id,
    kind: "zone",
    name: d.name,
    nameNormalized: d.nameNormalized,
    detail: `${d.memberIds.length} ${d.memberIds.length === 1 ? "item" : "items"}`,
  };
}

/** Boundary check: start of string, space, or punctuation. */
const BOUNDARY_CHARS = new Set([
  " ", "\t", "\n", "\r",
  ".", ",", ";", ":", "!", "?", "'", '"', "(", ")", "-",
]);

function isBoundaryChar(ch: string | undefined): boolean {
  return ch === undefined || BOUNDARY_CHARS.has(ch);
}

/**
 * Find the @ trigger position in text, returning -1 if none active.
 *
 * Fix #1: match-aware — when `zones` is provided, allow spaces after @
 * as long as the full query text is a prefix of at least one zone name.
 */
export function findAtTrigger(
  text: string,
  cursorPos: number,
  zones?: Directory[],
): number {
  // Walk backwards from cursor to find the nearest unescaped @.
  for (let i = cursorPos - 1; i >= 0; i--) {
    const ch = text[i];
    if (ch === "@") {
      // Check boundary before @.
      const before = i > 0 ? text[i - 1] : undefined;
      if (!isBoundaryChar(before)) {
        return -1;
      }

      const query = text.slice(i + 1, cursorPos);

      // Empty query: just typed @.
      if (query === "") return i;

      // If the query contains spaces, only stay open if it's a
      // prefix of at least one zone (match-aware space continuation).
      // Single-token queries always keep the popover open so that
      // "No zones match" can render for unmatched prefixes.
      if (/\s/.test(query)) {
        if (zones && zones.length > 0) {
          const lower = query.toLowerCase();
          const hasMatch = zones.some((z) =>
            z.nameNormalized.startsWith(lower),
          );
          return hasMatch ? i : -1;
        }
        return -1;
      }
      return i;
    }
  }
  return -1;
}

/** Extract the query text after @ up to cursor position. */
export function extractAtQuery(text: string, atPos: number, cursorPos: number): string {
  return text.slice(atPos + 1, cursorPos);
}

/** Filter zones by case-insensitive prefix match, sorted alphabetically, max 8. */
export function filterZones(query: string, zones: Directory[]): Directory[] {
  const lower = query.toLowerCase();
  const matches = zones.filter((z) =>
    z.nameNormalized.startsWith(lower),
  );
  matches.sort((a, b) => a.name.localeCompare(b.name));
  return matches.slice(0, MAX_MATCHES);
}

/** Build a ResolvedRef from a Directory. */
export function zoneToRef(zone: Directory): ResolvedRef {
  return {
    name: zone.name,
    id: zone.id,
    ref: `zone:${zone.id}`,
    kind: "zone",
  };
}

/**
 * Remove the @query span from text, collapsing whitespace at the
 * deletion seam and trimming leading/trailing space.
 *
 * Fixes #6 (double space at seam) and #7 (leading/trailing space
 * after removal at start or end of input).
 */
export function removeAtSpan(text: string, atPos: number, cursorPos: number): { text: string; cursor: number } {
  const before = text.slice(0, atPos);
  const after = text.slice(cursorPos);
  let next = before + after;

  // Collapse double space at the deletion seam.
  if (before.endsWith(" ") && after.startsWith(" ")) {
    next = before.slice(0, -1) + after;
  }

  // Trim leading/trailing whitespace left by removal at edges.
  const trimmed = next.replace(/^ +/, "").replace(/ +$/, "");
  const leadingRemoved = next.length - next.replace(/^ +/, "").length;

  return {
    text: trimmed,
    cursor: Math.max(0, Math.min(before.length - leadingRemoved, trimmed.length)),
  };
}

/** Zone icon glyph rendered as inline SVG. */
function ZoneGlyph() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={ZONE_ICON} />
    </svg>
  );
}

export interface InletAutocompleteProps {
  /** All available zones (zone-only mode, backward compat). */
  zones?: Directory[];
  /** Current filtered zone matches (zone-only mode). */
  matches?: Directory[];
  /** Currently selected index (keyboard navigation). */
  selectedIndex: number;
  /** Called when user selects a zone (zone-only mode). */
  onSelect?: (zone: Directory) => void;
  /** Called to update selected index. */
  onSelectedIndexChange: (index: number) => void;
  /** HS-151-06: generic item matches (replaces zone matches when provided). */
  allMatches?: AutocompleteItem[];
  /** HS-151-06: called when a generic item is selected. */
  onSelectItem?: (item: AutocompleteItem) => void;
  /** HS-151-06: custom empty label (default: "No zones match"). */
  emptyLabel?: string;
}

/** Kind-glyph rendered as a text span. */
function KindGlyph({ kind }: { kind: string }) {
  const ch = AC_GLYPH[kind] ?? "?";
  return (
    <span className="inlet-ac-kind-glyph" aria-hidden="true">{ch}</span>
  );
}

export function InletAutocomplete({
  zones,
  matches,
  selectedIndex,
  onSelect,
  onSelectedIndexChange,
  allMatches,
  onSelectItem,
  emptyLabel,
}: InletAutocompleteProps) {
  const listRef = useRef<HTMLDivElement>(null);

  // Scroll the selected item into view.
  useEffect(() => {
    if (!listRef.current) return;
    const sel = listRef.current.querySelector("[data-selected]");
    if (sel) {
      sel.scrollIntoView({ block: "nearest" });
    }
  }, [selectedIndex]);

  // HS-151-06: generic items mode
  if (allMatches) {
    if (allMatches.length === 0) {
      return (
        <div
          id="wb-inlet-listbox"
          className="inlet-autocomplete"
          ref={listRef}
          role="listbox"
        >
          <span className="inlet-autocomplete-empty">{emptyLabel ?? "No matches"}</span>
        </div>
      );
    }
    return (
      <div
        id="wb-inlet-listbox"
        className="inlet-autocomplete"
        ref={listRef}
        role="listbox"
      >
        <SurfaceRows>
          {allMatches.map((item, i) => (
            <SurfaceRow
              key={`${item.kind}:${item.id}`}
              id={`wb-inlet-option-${item.kind}-${item.id}`}
              role="option"
              ariaSelected={i === selectedIndex}
              glyph={item.kind === "zone" ? <ZoneGlyph /> : <KindGlyph kind={item.kind} />}
              title={item.name}
              detail={item.detail}
              selected={i === selectedIndex}
              onOpen={() => onSelectItem?.(item)}
            />
          ))}
        </SurfaceRows>
      </div>
    );
  }

  // Zone-only mode (backward compat)
  const zoneMatches = matches ?? [];
  if (zoneMatches.length === 0) {
    return (
      <div
        id="wb-inlet-listbox"
        className="inlet-autocomplete"
        ref={listRef}
        role="listbox"
      >
        <span className="inlet-autocomplete-empty">{emptyLabel ?? "No zones match"}</span>
      </div>
    );
  }

  return (
    <div
      id="wb-inlet-listbox"
      className="inlet-autocomplete"
      ref={listRef}
      role="listbox"
    >
      <SurfaceRows>
        {zoneMatches.map((zone, i) => (
          <SurfaceRow
            key={zone.id}
            id={`wb-inlet-option-${zone.id}`}
            role="option"
            ariaSelected={i === selectedIndex}
            glyph={<ZoneGlyph />}
            title={zone.name}
            detail={`${zone.memberIds.length} ${zone.memberIds.length === 1 ? "item" : "items"}`}
            selected={i === selectedIndex}
            onOpen={() => onSelect?.(zone)}
          />
        ))}
      </SurfaceRows>
    </div>
  );
}

/**
 * Hook to manage autocomplete state in the inlet.
 * Returns handlers and state for the popover.
 */
export function useInletAutocomplete(
  zones: Directory[],
  inputText: string,
  cursorPos: number,
  onAddRef: (ref: ResolvedRef) => void,
  onSetText: (text: string, cursor: number) => void,
) {
  const atPosRef = useRef(-1);
  const selectedIndexRef = useRef(0);
  const typedAtPosRef = useRef<number | null>(null);
  const prevQueryRef = useRef("");

  // Fix #2: only open autocomplete for typed @ characters.
  // Detect @ trigger only if we have a stored typed-@ position that matches.
  const rawAtPos = findAtTrigger(inputText, cursorPos, zones);
  const atPos =
    rawAtPos >= 0 && typedAtPosRef.current !== null && rawAtPos === typedAtPosRef.current
      ? rawAtPos
      : -1;
  const isOpen = atPos >= 0;
  const query = isOpen ? extractAtQuery(inputText, atPos, cursorPos) : "";
  const matches = isOpen ? filterZones(query, zones) : [];

  // Store for handlers.
  atPosRef.current = atPos;

  // Fix #5: reset selected index when query changes.
  let selectedIndex = selectedIndexRef.current;
  if (query !== prevQueryRef.current) {
    selectedIndex = 0;
    selectedIndexRef.current = 0;
    prevQueryRef.current = query;
  } else if (selectedIndex >= matches.length) {
    selectedIndex = Math.max(0, matches.length - 1);
    selectedIndexRef.current = selectedIndex;
  }

  const setSelectedIndex = (idx: number) => {
    selectedIndexRef.current = idx;
  };

  const selectZone = (zone: Directory) => {
    const ref = zoneToRef(zone);
    onAddRef(ref);

    // Remove the @query span from input (fixes #6, #7).
    const ap = atPosRef.current;
    if (ap >= 0) {
      const result = removeAtSpan(inputText, ap, cursorPos);
      onSetText(result.text, result.cursor);
    }
    selectedIndexRef.current = 0;
    typedAtPosRef.current = null;
  };

  /** Call this when the user types @ (in onKeyDown, before insertion). */
  const registerTypedAt = (pos: number) => {
    typedAtPosRef.current = pos;
  };

  /** Dismiss the autocomplete (Escape, mic arm, etc.). */
  const dismiss = () => {
    typedAtPosRef.current = null;
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>): boolean => {
    if (!isOpen) return false;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        selectedIndexRef.current = Math.min(
          selectedIndexRef.current + 1,
          matches.length - 1,
        );
        return true;

      case "ArrowUp":
        e.preventDefault();
        selectedIndexRef.current = Math.max(
          selectedIndexRef.current - 1,
          0,
        );
        return true;

      case "Enter":
        if (matches.length > 0) {
          e.preventDefault();
          selectZone(matches[selectedIndexRef.current]);
          return true;
        }
        return false;

      case "Tab":
        // Fix #4: Shift+Tab should not select.
        if (e.shiftKey) return false;
        if (matches.length > 0) {
          e.preventDefault();
          selectZone(matches[selectedIndexRef.current]);
          return true;
        }
        return false;

      case "Escape":
        e.preventDefault();
        dismiss();
        return true;

      case " ":
        // Space with no matches closes popover.
        if (matches.length === 0) {
          dismiss();
          return false; // Let the space through.
        }
        return false;

      default:
        return false;
    }
  };

  return {
    isOpen,
    matches,
    selectedIndex,
    setSelectedIndex,
    selectZone,
    handleKeyDown,
    registerTypedAt,
    dismiss,
  };
}
