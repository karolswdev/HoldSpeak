/** PHILO-14 B1 — IconGrid: a drawer's (or the Floor's) objects as icons.
 *
 *  The A-1/A-2 spacing: 112 px columns that fill the window, 6 px rows,
 *  4 px gutters; four columns at the narrow container. The grid owns NO
 *  selection: the caller passes `selected` to each DeskIcon and gets the
 *  rubber band through `onMarquee` (a rectangle in grid coordinates while
 *  the pointer drags over empty glass, null when it ends) and the ids under
 *  it through `iconsInRect`. A press on empty glass calls `onClear`.
 *
 *  Keyboard: one Tab stop; Left/Right move within the visual row, Up/Down
 *  by the rendered column count, Home/End to the ends (useRovingGrid).
 */
import { useRef, type PointerEvent, type ReactNode } from "react";
import { useRovingGrid } from "../roving";
import "./objects.css";

export interface GridRect {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** The ids (data-object-id) of the icons in `grid` that meet `rect`
 *  (grid coordinates, as `onMarquee` gives them). */
export function iconsInRect(grid: HTMLElement, rect: GridRect): string[] {
  const box = grid.getBoundingClientRect();
  const left = box.left + rect.x - grid.scrollLeft;
  const top = box.top + rect.y - grid.scrollTop;
  const ids: string[] = [];
  grid.querySelectorAll<HTMLElement>("[data-object-id]").forEach((icon) => {
    const r = icon.getBoundingClientRect();
    const meets = r.right >= left && r.left <= left + rect.w && r.bottom >= top && r.top <= top + rect.h;
    if (meets && icon.dataset.objectId) ids.push(icon.dataset.objectId);
  });
  return ids;
}

export interface IconGridProps {
  /** The grid's accessible name (e.g. the drawer's name). */
  label: string;
  children: ReactNode;
  /** The rubber band to draw (the caller's state). */
  marquee?: GridRect | null;
  /** Called while the pointer drags over empty glass, and with null at the end. */
  onMarquee?(rect: GridRect | null, grid: HTMLElement): void;
  /** A press on empty glass (clear the selection). */
  onClear?(): void;
  className?: string;
  /** Phase 16 (the interior kit, §11 "IconGrid"): the objects INSIDE a
   *  window sit in a sunken paper well, five across at 900 px and wider,
   *  the icon at 40 px over a two-line sans name. The Floor's grid (the
   *  glass itself) has no well. */
  well?: boolean;
  "data-testid"?: string;
}

export function IconGrid({ label, children, marquee, onMarquee, onClear, className, well, "data-testid": testId }: IconGridProps) {
  const ref = useRef<HTMLDivElement>(null);
  const origin = useRef<{ x: number; y: number } | null>(null);
  useRovingGrid(ref, { selector: ".desk-icon" });

  const point = (event: PointerEvent<HTMLDivElement>) => {
    const grid = ref.current!;
    const box = grid.getBoundingClientRect();
    return { x: event.clientX - box.left + grid.scrollLeft, y: event.clientY - box.top + grid.scrollTop };
  };
  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    if (event.target !== ref.current || event.button !== 0) return;
    onClear?.();
    if (!onMarquee) return;
    origin.current = point(event);
    ref.current?.setPointerCapture?.(event.pointerId);
  };
  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    const start = origin.current;
    if (!start || !ref.current) return;
    const at = point(event);
    onMarquee?.(
      { x: Math.min(start.x, at.x), y: Math.min(start.y, at.y), w: Math.abs(at.x - start.x), h: Math.abs(at.y - start.y) },
      ref.current,
    );
  };
  const onPointerUp = () => {
    if (!origin.current || !ref.current) return;
    origin.current = null;
    onMarquee?.(null, ref.current);
  };

  return (
    <div
      ref={ref}
      className={`desk-icon-grid${className ? ` ${className}` : ""}`}
      role="group"
      aria-label={label}
      data-well={well || undefined}
      data-testid={testId}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
    >
      {children}
      {marquee && marquee.w + marquee.h > 0 ? (
        <span
          className="desk-icon-marquee"
          aria-hidden="true"
          style={{ left: marquee.x, top: marquee.y, width: marquee.w, height: marquee.h }}
        />
      ) : null}
    </div>
  );
}
