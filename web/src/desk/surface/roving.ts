// HS-111-08 — roving focus is kit law (audit §3.1, doctrine P0 F3):
// ONE hook, applied INSIDE SurfaceLedger and GadgetTable — never in
// consumers. ARIA roving-tabindex over the container's REAL controls:
// one Tab stop per composite, ArrowUp/Down walk rows, Home/End jump,
// PageUp/Down move ±10, printable keys type-ahead (500ms buffer).
// No wrap — Home/End exist and wrap surprises in 100-row archives.
// The hook re-queries the DOM per keypress (correct under any children
// shape, no context plumbing) and re-anchors on focusin so mouse
// clicks move the rover.
import { useEffect, useRef, type RefObject } from "react";

const EDITOR_GUARD = "input, textarea, select";
const TYPEAHEAD_MS = 500;

/** Group the stops by their row element (document order). Without a
 * rowSelector every stop is its own row (the ledger's shape). */
function groupRows(
  root: HTMLElement,
  stops: HTMLElement[],
  rowSelector?: string,
): HTMLElement[][] {
  if (!rowSelector) return stops.map((stop) => [stop]);
  const rows = new Map<Element, HTMLElement[]>();
  for (const stop of stops) {
    const row = stop.closest(rowSelector);
    if (!row || !root.contains(row)) continue;
    const bucket = rows.get(row);
    if (bucket) bucket.push(stop);
    else rows.set(row, [stop]);
  }
  return [...rows.values()];
}

export function useRovingRows(
  ref: RefObject<HTMLElement | null>,
  {
    selector,
    rowSelector,
  }: {
    /** The focusable stops (real buttons/inputs — the tree stays honest). */
    selector: string;
    /** Groups stops into rows: Up/Down walk rows, Left/Right walk the
     * row's own controls (the GadgetTable shape). */
    rowSelector?: string;
  },
) {
  const current = useRef(0);

  // Re-stamp the roving tabindex after EVERY render: rows come and go
  // with the caller's children, so the hook re-queries, never plumbs.
  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const stops = Array.from(root.querySelectorAll<HTMLElement>(selector));
    if (!stops.length) return;
    if (current.current >= stops.length) current.current = stops.length - 1;
    stops.forEach((stop, index) => {
      stop.tabIndex = index === current.current ? 0 : -1;
    });
  });

  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const query = () =>
      Array.from(root.querySelectorAll<HTMLElement>(selector));
    const anchor = (stops: HTMLElement[], index: number) => {
      current.current = index;
      stops.forEach((stop, i) => {
        stop.tabIndex = i === index ? 0 : -1;
      });
    };
    // Mouse clicks (and Tab-in) re-anchor the rover.
    const onFocusIn = (event: FocusEvent) => {
      const stops = query();
      const hit = stops.indexOf(event.target as HTMLElement);
      if (hit >= 0) anchor(stops, hit);
    };

    let buffer = "";
    let bufferAt = 0;
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      // Typing in an open row's editor is untouched.
      if (target.matches?.(EDITOR_GUARD) || target.isContentEditable) return;
      const stops = query();
      if (!stops.length) return;
      const from = Math.min(current.current, stops.length - 1);
      const rows = groupRows(root, stops, rowSelector);
      const rowOf = (stop: HTMLElement) =>
        rows.findIndex((row) => row.includes(stop));
      const fromRow = Math.max(0, rowOf(stops[from]));
      const fromCol = Math.max(0, rows[fromRow]?.indexOf(stops[from]) ?? 0);
      const toRow = (rowIndex: number) => {
        const row = rows[Math.max(0, Math.min(rowIndex, rows.length - 1))];
        return row[Math.min(fromCol, row.length - 1)];
      };
      let next: HTMLElement | undefined;
      switch (event.key) {
        case "ArrowDown":
          next = toRow(fromRow + 1);
          break;
        case "ArrowUp":
          next = toRow(fromRow - 1);
          break;
        case "ArrowRight":
          if (!rowSelector) return;
          next = rows[fromRow]?.[fromCol + 1];
          if (!next) return;
          break;
        case "ArrowLeft":
          if (!rowSelector) return;
          next = rows[fromRow]?.[fromCol - 1];
          if (!next) return;
          break;
        case "PageDown":
          next = toRow(fromRow + 10);
          break;
        case "PageUp":
          next = toRow(fromRow - 10);
          break;
        case "Home":
          next = rows[0]?.[0];
          break;
        case "End":
          next = rows[rows.length - 1]?.[0];
          break;
        default: {
          // First-letter type-ahead over the ROW's text (doctrine F3).
          // Space stays a row verb; modifiers stay shortcuts.
          if (
            event.key.length !== 1 ||
            event.key === " " ||
            event.ctrlKey ||
            event.metaKey ||
            event.altKey
          )
            return;
          const now = Date.now();
          buffer =
            (now - bufferAt < TYPEAHEAD_MS ? buffer : "") +
            event.key.toLowerCase();
          bufferAt = now;
          for (let step = 1; step <= rows.length; step += 1) {
            const row = rows[(fromRow + step) % rows.length];
            const text = (
              (rowSelector
                ? row[0].closest(rowSelector)?.textContent
                : row[0].textContent) || ""
            )
              .trim()
              .toLowerCase();
            if (text.startsWith(buffer)) {
              next = row[0];
              break;
            }
          }
          if (!next) return;
        }
      }
      if (!next) return;
      event.preventDefault();
      anchor(stops, stops.indexOf(next));
      next.focus();
    };

    root.addEventListener("focusin", onFocusIn);
    root.addEventListener("keydown", onKeyDown);
    return () => {
      root.removeEventListener("focusin", onFocusIn);
      root.removeEventListener("keydown", onKeyDown);
    };
  }, [ref, selector, rowSelector]);
}
