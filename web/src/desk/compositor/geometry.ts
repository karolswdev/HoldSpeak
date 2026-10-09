/** PHILO-16 (L5) — geometry is shares plus pixels, resolved by each view.
 *
 * A value is one relative coefficient (a share of the view's span) plus one
 * pixel offset: `"50% + 10"`, `"-1/2"`, `"1/2 - 4"`, or a plain number (pixels
 * only). The plane's zero is the view's centre, so `x: "-1/2"` is the view's
 * left edge on every screen. The arrangement verbs (tile, stage, exposé,
 * gather, cascade, zoom) are written here AS SHARES and resolved against the
 * working band at draw time: the same arrangement is the same arrangement at
 * 1440 and at 1920. Pure: no DOM, no React. */
import { MARGIN } from "../components/window/windowGeometry";

export type Value = number | string;

export interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** A rect of values. x/y are measured from the view's centre. */
export interface ValueRect {
  x: Value;
  y: Value;
  w: Value;
  h: Value;
}

export interface Parsed {
  share: number;
  px: number;
}

const SHARE = /^([+-]?\d+(?:\.\d+)?)(?:\s*\/\s*(\d+(?:\.\d+)?)|(%))$/;
const PX = /^([+-]?\d+(?:\.\d+)?)(?:px)?$/;

/** Parse one value. Throws on a string it does not read (a typo in an
 * arrangement is a bug, not a silent zero). */
export function parseValue(value: Value): Parsed {
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new Error(`geometry: not a value: ${value}`);
    return { share: 0, px: value };
  }
  const text = value.replace(/\s+/g, " ").trim();
  // Split at a binary + or - (a space on both sides), keeping the sign.
  const terms = text.split(/ (?=[+-] )/).map((t) => t.replace(/^([+-]) /, "$1"));
  let share = 0;
  let px = 0;
  let seenShare = false;
  let seenPx = false;
  for (const term of terms) {
    const s = SHARE.exec(term);
    if (s) {
      if (seenShare) throw new Error(`geometry: two shares in "${value}"`);
      seenShare = true;
      const n = parseFloat(s[1]);
      share = s[3] ? n / 100 : n / parseFloat(s[2]);
      continue;
    }
    const p = PX.exec(term);
    if (p) {
      if (seenPx) throw new Error(`geometry: two pixel terms in "${value}"`);
      seenPx = true;
      px = parseFloat(p[1]);
      continue;
    }
    throw new Error(`geometry: cannot read "${value}"`);
  }
  return { share, px };
}

/** Resolve one value against a span (pixels). */
export function resolve(value: Value, span: number): number {
  const { share, px } = parseValue(value);
  return share * span + px;
}

/** Resolve a value rect against a view (the band, or the viewport): x/y
 * from the view's centre, w/h from its span. Rounded to whole pixels. */
export function resolveRect(rect: ValueRect, view: Rect): Rect {
  const cx = view.x + view.w / 2;
  const cy = view.y + view.h / 2;
  return {
    x: Math.round(cx + resolve(rect.x, view.w)),
    y: Math.round(cy + resolve(rect.y, view.h)),
    w: Math.round(resolve(rect.w, view.w)),
    h: Math.round(resolve(rect.h, view.h)),
  };
}

const fmt = (share: number, px: number): string => {
  const pct = Math.round(share * 1e6) / 1e4; // 4 decimals of a percent
  const rest = Math.round(px * 1000) / 1000;
  if (rest === 0) return `${pct}%`;
  return `${pct}% ${rest < 0 ? "-" : "+"} ${Math.abs(rest)}`;
};

/** The inverse of `resolveRect`: a pixel rect recorded as the share of the
 * view it covers plus the pixels within it (PhreshOS `recordedPosition`).
 * Each axis keeps its share rounded to 1/10000 of a percent and carries the
 * remainder in pixels, so `resolveRect(record(r, v), v)` is `r` exactly. */
export function record(rect: Rect, view: Rect): ValueRect {
  const cx = view.x + view.w / 2;
  const cy = view.y + view.h / 2;
  const axis = (offset: number, span: number): string => {
    const share = Math.round((offset / span) * 1e6) / 1e6;
    return fmt(share, offset - share * span);
  };
  return {
    x: axis(rect.x - cx, view.w),
    y: axis(rect.y - cy, view.h),
    w: axis(rect.w, view.w),
    h: axis(rect.h, view.h),
  };
}

// ---- the band -------------------------------------------------------------

/** The canvas's band edges: the screen bar (28) and the dock (80), each
 * with a 10 px margin. The live desk passes `workBand()` instead. */
export const SCREEN_BAR = 28;
export const DOCK = 80;
export const DEFAULT_EDGES = { top: SCREEN_BAR + MARGIN, bottom: DOCK + MARGIN };

/** The working band of a view: below the screen bar, above the dock, the
 * side margin off each edge (the band `clampIntoBand` keeps windows in). */
export function bandFor(
  vw: number,
  vh: number,
  edges: { top: number; bottom: number } = DEFAULT_EDGES,
): Rect {
  return {
    x: MARGIN,
    y: edges.top,
    w: Math.max(0, vw - MARGIN * 2),
    h: Math.max(0, vh - edges.top - edges.bottom),
  };
}

/** True when `r` lies whole inside `band` (1 px of rounding allowed). */
export function inside(r: Rect, band: Rect): boolean {
  return (
    r.x >= band.x - 1 &&
    r.y >= band.y - 1 &&
    r.x + r.w <= band.x + band.w + 1 &&
    r.y + r.h <= band.y + band.h + 1
  );
}

// ---- arrangements, as shares ---------------------------------------------

/** Tile left: the left half of the band. Tiles touch at the centre line, so
 * the two halves share one boundary (one steel divider, L8). */
export const tileLeft = (): ValueRect => ({ x: "-1/2", y: "-1/2", w: "1/2", h: "1/1" });
/** Tile right: the right half of the band. */
export const tileRight = (): ValueRect => ({ x: 0, y: "-1/2", w: "1/2", h: "1/1" });

/** Zoom: the window fills the band. */
export const zoom = (): ValueRect => ({ x: "-1/2", y: "-1/2", w: "1/1", h: "1/1" });

/** Tile two windows: `first` takes `side`, `second` the other half. */
export function tile(
  first: string,
  second: string | null,
  side: "left" | "right" = "left",
): Map<string, ValueRect> {
  const map = new Map<string, ValueRect>();
  map.set(first, side === "left" ? tileLeft() : tileRight());
  if (second) map.set(second, side === "left" ? tileRight() : tileLeft());
  return map;
}

export interface Plate {
  rect: ValueRect;
  /** The plate's scale (a live window drawn smaller); absent = full size. */
  k?: number;
}

const STAGE_MAIN = 0.76;
const SHELF_W = 300;
const SHELF_H = 170;
const SHELF_STEP = 190;
const SHELF_INSET = 10;

/** Stage: the front takes 76 % of the band; every other shown window waits
 * on the shelf as a live plate scaled to at most 300 x 170, stacked at 190 px
 * steps (closer when the band is short, so no plate leaves it), the nearest
 * on top. `shownIds` is back to front; `rects` gives each plate its size. */
export function stage(
  frontId: string,
  shownIds: readonly string[],
  shelf: "left" | "right",
  rects: Readonly<Record<string, Rect>>,
  band: Rect,
): Map<string, Plate> {
  const map = new Map<string, Plate>();
  const left = shelf === "left";
  // Main: right-aligned when the shelf is on the left.
  map.set(frontId, {
    rect: { x: left ? `${50 - STAGE_MAIN * 100}%` : "-1/2", y: "-1/2", w: `${STAGE_MAIN * 100}%`, h: "1/1" },
  });
  const rest = shownIds.filter((id) => id !== frontId).reverse(); // nearest first
  // A short band (Astra MAY, 1440 x 280) shrinks the plates to fit it.
  const shelfH = Math.max(1, Math.min(SHELF_H, band.h - SHELF_INSET * 2));
  const room = band.h - SHELF_INSET * 2 - shelfH;
  const step = rest.length > 1 ? Math.max(0, Math.min(SHELF_STEP, room / (rest.length - 1))) : SHELF_STEP;
  rest.forEach((id, i) => {
    const r = rects[id] ?? { x: 0, y: 0, w: SHELF_W, h: SHELF_H };
    const k = Math.min(1, SHELF_W / r.w, shelfH / r.h);
    map.set(id, {
      rect: {
        x: left ? `-1/2 + ${SHELF_INSET}` : `1/2 - ${SHELF_W + SHELF_INSET}`,
        y: `-1/2 + ${Math.round(SHELF_INSET + i * step)}`,
        // The plate's layout box is the window's own size; k draws it smaller.
        w: r.w,
        h: r.h,
      },
      k,
    });
  });
  return map;
}

/** Exposé: every shown window as a live plate in a grid of cells inside the
 * band, scaled (never reflowed) to fit its cell with a 20 px air. */
export function exposeGrid(
  ids: readonly string[],
  rects: Readonly<Record<string, Rect>>,
  band: Rect,
): Map<string, Plate> {
  const map = new Map<string, Plate>();
  const n = ids.length;
  if (!n) return map;
  const cols = Math.ceil(Math.sqrt(n));
  const rows = Math.ceil(n / cols);
  const cw = (band.w - 40) / cols;
  const ch = (band.h - 40) / rows;
  ids.forEach((id, i) => {
    const r = rects[id] ?? { x: 0, y: 0, w: cw, h: ch };
    const k = Math.min(1, (cw - 40) / r.w, (ch - 40) / r.h);
    const w = r.w * k;
    const h = r.h * k;
    const px = 20 + (i % cols) * cw + (cw - w) / 2;
    const py = 20 + Math.floor(i / cols) * ch + (ch - h) / 2;
    map.set(id, {
      rect: { x: `-1/2 + ${Math.round(px)}`, y: `-1/2 + ${Math.round(py)}`, w: r.w, h: r.h },
      k,
    });
  });
  return map;
}

const GATHER_GUTTER = 8;

/** Gather: the windows tile the band in equal columns with 8 px gutters. */
export function gather(ids: readonly string[]): Map<string, ValueRect> {
  const map = new Map<string, ValueRect>();
  const n = ids.length;
  ids.forEach((id, i) => {
    // x_i = -W/2 + i*W/n + 8i/n ; w = W/n - 8(n-1)/n
    const xPx = Math.round(((GATHER_GUTTER * i) / n) * 1000) / 1000;
    const wPx = Math.round(((GATHER_GUTTER * (n - 1)) / n) * 1000) / 1000;
    map.set(id, {
      x: `${2 * i - n}/${2 * n}${xPx ? ` + ${xPx}` : ""}`,
      y: "-1/2",
      w: `1/${n}${wPx ? ` - ${wPx}` : ""}`,
      h: "1/1",
    });
  });
  return map;
}

/** Cascade: every window re-seated from the band's top-left in `step` px
 * steps, its size kept (clamped to the band). */
export function cascade(
  ids: readonly string[],
  rects: Readonly<Record<string, Rect>>,
  band: Rect,
  step = 26,
): Map<string, Rect> {
  const map = new Map<string, Rect>();
  ids.forEach((id, i) => {
    const r = rects[id] ?? { x: 0, y: 0, w: 480, h: 360 };
    const w = Math.min(r.w, band.w);
    const h = Math.min(r.h, band.h);
    const x = Math.min(band.x + 4 + i * step, band.x + band.w - w);
    const y = Math.min(band.y + 4 + i * step, band.y + band.h - h);
    map.set(id, { x, y, w, h });
  });
  return map;
}

/** The visual rect of a plate: its layout box drawn at scale k from the
 * top-left corner. */
export function plateVisual(r: Rect, k = 1): Rect {
  return { x: r.x, y: r.y, w: r.w * k, h: r.h * k };
}
