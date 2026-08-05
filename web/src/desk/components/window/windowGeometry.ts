// Window geometry — pure functions with zero React or module-state
// dependencies. Extracted from DeskWindow.tsx (HS-117-04).
import type { PanelRect } from "../../store";
import { DESK_WINDOW } from "../../../lib/tokens.gen";

/** Viewport margin windows are clamped inside. */
export const MARGIN = DESK_WINDOW.margin;
/** Cascade step when several default-corner windows are open at once. */
const CASCADE = DESK_WINDOW.cascade;

/** The window head strip considered for title-bar occlusion (px). */
const HEAD = 44;

/** The usable desktop is one contract: below the system bar, above the dock.
 * CSS owns the dimensions so shell changes cannot make window physics drift. */
export function workBand() {
  const fallback = {
    top: DESK_WINDOW.snapTop,
    bottom: DESK_WINDOW.snapBottom,
  };
  if (typeof window === "undefined" || typeof document === "undefined")
    return fallback;
  const style = getComputedStyle(document.documentElement);
  const top = parseFloat(style.getPropertyValue("--desk-work-top"));
  const bottom = parseFloat(style.getPropertyValue("--desk-work-bottom"));
  return {
    top: Number.isFinite(top) ? top : fallback.top,
    bottom: Number.isFinite(bottom) ? bottom : fallback.bottom,
  };
}

/** HS-97-02 — the open-placement engine. A window opening without a
 * persisted rect lands FULLY inside the working band (below the chrome,
 * clear of the dock), seeded at its CSS default home but moved off other
 * windows' title bars by a min-overlap scan (head occlusion dominates,
 * then overlap area, then distance from home). Pure, pinned by test. */
export function placeWindow(
  seed: PanelRect,
  existing: PanelRect[],
  vw: number,
  vh: number,
  minW = 320,
  minH = 220,
): PanelRect {
  const { top, bottom } = workBand();
  const w = Math.max(minW, Math.min(seed.w, vw - MARGIN * 2));
  const h = Math.max(minH, Math.min(seed.h, Math.max(minH, vh - top - bottom)));
  const maxX = Math.max(MARGIN, vw - MARGIN - w);
  const maxY = Math.max(top, vh - bottom - h);
  const sx = Math.min(Math.max(seed.x, MARGIN), maxX);
  const sy = Math.min(Math.max(seed.y, top), maxY);
  const overlap = (
    ax: number,
    ay: number,
    aw: number,
    ah: number,
    b: PanelRect,
    bh: number,
  ) => {
    const ox = Math.max(0, Math.min(ax + aw, b.x + b.w) - Math.max(ax, b.x));
    const oy = Math.max(0, Math.min(ay + ah, b.y + bh) - Math.max(ay, b.y));
    return ox * oy;
  };
  const score = (x: number, y: number) => {
    let heads = 0;
    let area = 0;
    for (const r of existing) {
      area += overlap(x, y, w, h, r, r.h);
      if (overlap(x, y, w, HEAD, r, HEAD) > 0) heads++;
    }
    return heads * 1e9 + area * 10 + Math.hypot(x - sx, y - sy);
  };
  let best = { x: sx, y: sy, s: score(sx, sy) };
  const STEP = 32;
  for (let y = top; y <= maxY; y += STEP) {
    for (let x = MARGIN; x <= maxX; x += STEP) {
      const s = score(x, y);
      if (s < best.s - 0.5) best = { x, y, s };
    }
  }
  if (best.s >= 1e9) {
    // Saturated: every position occludes a title bar somewhere. The
    // cascade survives exactly here — step down-right off the home seat.
    const step = CASCADE * Math.min(existing.length, 8);
    return {
      x: Math.min(Math.max(sx + step, MARGIN), maxX),
      y: Math.min(Math.max(sy + step, top), maxY),
      w,
      h,
    };
  }
  return { x: best.x, y: best.y, w, h };
}

/** HS-97-02 — clamp-on-open: a persisted rect (possibly from a larger
 * viewport) lands whole inside the working band; the arrangement is
 * otherwise untouched. */
export function clampIntoBand(
  r: PanelRect,
  vw: number,
  vh: number,
  minW = 320,
  minH = 220,
): PanelRect {
  const { top, bottom } = workBand();
  const w = Math.max(minW, Math.min(r.w, vw - MARGIN * 2));
  const h = Math.max(minH, Math.min(r.h, Math.max(minH, vh - top - bottom)));
  const x = Math.min(Math.max(r.x, MARGIN), Math.max(MARGIN, vw - MARGIN - w));
  const y = Math.min(Math.max(r.y, top), Math.max(top, vh - bottom - h));
  return { x, y, w, h };
}

/** HS-95-03 — edge snap: releasing a window drag at a screen edge tiles
 * it. Corners take quarters, the left/right flanks take halves; anywhere
 * else returns null (a free park). Pure, pinned by test. */
export function snapForPointer(
  px: number,
  py: number,
  vw: number,
  vh: number,
): PanelRect | null {
  const EDGE = 26;
  const CORNER = 150;
  const { top, bottom } = workBand(); // below chrome, clear of dock
  const halfW = Math.floor((vw - MARGIN * 3) / 2);
  const halfH = Math.floor((vh - top - bottom - MARGIN) / 2);
  const left = px <= CORNER;
  const right = px >= vw - CORNER;
  const high = py <= CORNER + top;
  const low = py >= vh - CORNER;
  if (left && high) return { x: MARGIN, y: top, w: halfW, h: halfH };
  if (right && high)
    return { x: vw - MARGIN - halfW, y: top, w: halfW, h: halfH };
  if (left && low)
    return { x: MARGIN, y: top + halfH + MARGIN, w: halfW, h: halfH };
  if (right && low)
    return {
      x: vw - MARGIN - halfW,
      y: top + halfH + MARGIN,
      w: halfW,
      h: halfH,
    };
  if (px <= EDGE)
    return { x: MARGIN, y: top, w: halfW, h: vh - top - bottom };
  if (px >= vw - EDGE)
    return { x: vw - MARGIN - halfW, y: top, w: halfW, h: vh - top - bottom };
  return null;
}

/** HS-97-05 — edge resize math: which edges move with the pointer.
 * Modes: "r" | "b" | "br" | "l" | "bl"; the left edge keeps the right
 * edge fixed when the minimum bites. Pure, pinned by test. */
export function resizeEdge(
  mode: string,
  base: PanelRect,
  mx: number,
  my: number,
  minW: number,
  minH: number,
): PanelRect {
  let { x, y, w, h } = base;
  if (mode.includes("r")) w = base.w + mx;
  if (mode.includes("l")) {
    w = base.w - mx;
    x = base.x + mx;
    if (w < minW) {
      x = base.x + base.w - minW;
      w = minW;
    }
  }
  if (mode.includes("b")) h = base.h + my;
  return clampRect({ x, y, w, h }, minW, minH);
}

export function clampRect(r: PanelRect, minW: number, minH: number): PanelRect {
  const vw = window.innerWidth || 1280;
  const vh = window.innerHeight || 800;
  const { top, bottom } = workBand();
  const w = Math.max(minW, Math.min(r.w, vw - MARGIN * 2));
  const h = Math.max(minH, Math.min(r.h, Math.max(minH, vh - top - bottom)));
  const x = Math.min(Math.max(r.x, MARGIN), Math.max(MARGIN, vw - MARGIN - w));
  const y = Math.min(Math.max(r.y, top), Math.max(top, vh - bottom - h));
  return { x, y, w, h };
}

/** HS-97-06 — the expose grid: N non-overlapping cells inside the
 * working band, last row centered. Pure, pinned by test. */
export function exposeLayout(
  count: number,
  vw: number,
  vh: number,
): PanelRect[] {
  const band = workBand();
  const top = band.top + 8;
  const bottom = band.bottom + 8;
  const GAP = 18;
  const cols = Math.max(1, Math.ceil(Math.sqrt(count)));
  const rows = Math.max(1, Math.ceil(count / cols));
  const bandW = vw - MARGIN * 2;
  const bandH = vh - top - bottom;
  const w = Math.floor((bandW - GAP * (cols - 1)) / cols);
  const h = Math.floor((bandH - GAP * (rows - 1)) / rows);
  const cells: PanelRect[] = [];
  for (let i = 0; i < count; i++) {
    const r = Math.floor(i / cols);
    const inRow = r === rows - 1 ? count - r * cols : cols;
    const rowW = inRow * w + (inRow - 1) * GAP;
    const x0 = MARGIN + Math.floor((bandW - rowW) / 2);
    cells.push({
      x: x0 + (i - r * cols) * (w + GAP),
      y: top + r * (h + GAP),
      w,
      h,
    });
  }
  return cells;
}

/** MRU order over the currently-open windows (front last, like the z
 * band). Windows never focused yet sort first. */
export function mruOrder(ids: string[], order: string[]): string[] {
  return [...ids].sort((a, b) => order.indexOf(a) - order.indexOf(b));
}
