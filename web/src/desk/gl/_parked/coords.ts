/** HS-95-01 — the one coordinate contract shared by the GPU world and the
 * DOM overlays above it. Object/zone positions are unit-space fractions
 * (0..1) of the world box, exactly as the DOM world stored them
 * (`hs.diorama.pos` stays byte-compatible); these helpers are the only
 * translation between unit space, canvas-local pixels, and client pixels,
 * so a DOM window can anchor to a GL object through pan and resize. */
import type { UnitPos } from "../store";

export interface WorldRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

/** Unit → canvas-local px (the GL scene's own coordinate space). */
export function unitToLocal(u: UnitPos, rect: WorldRect): {
  x: number;
  y: number;
} {
  return { x: u.x * rect.width, y: u.y * rect.height };
}

/** Unit → client px (for DOM overlays anchored to world things). */
export function unitToClient(u: UnitPos, rect: WorldRect): {
  x: number;
  y: number;
} {
  return { x: rect.left + u.x * rect.width, y: rect.top + u.y * rect.height };
}

/** Client px → unit, with the world's drag clamps (objects clamp to
 * 0.04..0.96 both axes; zones allow a slightly higher park, HS-71-05). */
export function clientToUnit(
  clientX: number,
  clientY: number,
  rect: WorldRect,
  clamp: { xMin: number; xMax: number; yMin: number; yMax: number } = OBJECT_CLAMP,
): UnitPos {
  const x = rect.width > 0 ? (clientX - rect.left) / rect.width : 0;
  const y = rect.height > 0 ? (clientY - rect.top) / rect.height : 0;
  return {
    x: Math.min(clamp.xMax, Math.max(clamp.xMin, x)),
    y: Math.min(clamp.yMax, Math.max(clamp.yMin, y)),
  };
}

export const OBJECT_CLAMP = { xMin: 0.04, xMax: 0.96, yMin: 0.04, yMax: 0.96 };
export const ZONE_CLAMP = { xMin: 0.04, xMax: 0.96, yMin: 0.03, yMax: 0.94 };

export function worldRectOf(el: Element): WorldRect {
  const r = el.getBoundingClientRect();
  return { left: r.left, top: r.top, width: r.width, height: r.height };
}

/** HS-110-01 — grid pitch in pixels: icon cell + gutter. */
export const GRID_CELL_W = 120;
export const GRID_CELL_H = 128;

/** Snap a unit-space position to the nearest grid cell center. */
export function snapToGrid(
  u: UnitPos,
  rect: WorldRect,
  clamp: { xMin: number; xMax: number; yMin: number; yMax: number } = OBJECT_CLAMP,
): UnitPos {
  if (rect.width <= 0 || rect.height <= 0) return u;
  const px = u.x * rect.width;
  const py = u.y * rect.height;
  const halfW = GRID_CELL_W / 2;
  const halfH = GRID_CELL_H / 2;
  const snappedX = Math.round((px - halfW) / GRID_CELL_W) * GRID_CELL_W + halfW;
  const snappedY = Math.round((py - halfH) / GRID_CELL_H) * GRID_CELL_H + halfH;
  return {
    x: Math.min(clamp.xMax, Math.max(clamp.xMin, snappedX / rect.width)),
    y: Math.min(clamp.yMax, Math.max(clamp.yMin, snappedY / rect.height)),
  };
}
