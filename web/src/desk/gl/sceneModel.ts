/** HS-95-01 — the pure scene model. The store stays the single truth; this
 * module projects a store snapshot into a flat display list the GL stage
 * draws, and answers hit-tests against it. No pixi import, fully testable.
 *
 * Geometry contract (ported verbatim from the DOM world, HS-71/73 values):
 * an object is a 128px-wide column centered on its unit position — a 96×96
 * lift (sprite 88×88; 74×74 for note/artifact) over a 2-line label; zones
 * are top-center-anchored trays (min 148px, default max 260px). */
import type { UnitPos } from "../store";
import type { Items } from "../api";
import { qualifiedRef } from "../api";
import {
  objGlow,
  objMotion,
  objUnit,
  worldObjects,
  worldRows,
  worldZones,
  type WorldObject,
} from "../world";
import { resolveRef } from "../lineage";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { spriteUrl, variantIndex } from "../sprites";
import type { WorldRect } from "./coords";

/** HS-93-08 — the spatial stage's honest render bound (moved here with the
 * renderer; the chip and List view still reach everything). */
export const MAX_FLOATERS = 200;

/** Per-zone stable tints — the same stable-hash family the sprite picker
 * uses, so a zone's color never changes (World.tsx values, verbatim). */
export const ZONE_TINTS = [
  "#E0A458",
  "#56C7F5",
  "#34D399",
  "#A78BFA",
  "#FF9E64",
  "#FBBF24",
];

export const OBJ_W = 128;
export const LIFT = 96;
export const SPRITE = 88;
export const SPRITE_SMALL = 74;
export const LABEL_H = 34;
export const OBJ_H = LIFT + 2 + LABEL_H;
export const ZONE_MIN_W = 148;
export const ZONE_DEFAULT_MAX_W = 260;
export const ZONE_MAX_W = 560;
export const ZONE_H = 66;
export const ZONE_THUMBS_H = 78;
export const GRIP = 16;
/** The DOM's @use-gesture tap/drag discrimination threshold (HS-71-04). */
export const DRAG_THRESHOLD = 4;

export interface SceneObject {
  key: string;
  kind: string;
  id: string;
  /** The selection ref (`kind:id`) the lasso/rope vocabulary uses. */
  selectionRef: string;
  title: string;
  u: UnitPos;
  phase: number;
  tilt: number;
  scale: number;
  glow: string;
  sprite: string;
  small: boolean;
  selected: boolean;
  dragging: boolean;
  isNew: boolean;
  editing: boolean;
  attention: number;
}

export interface SceneZoneThumb {
  id: string;
  kind: string;
  sprite: string;
}

export interface SceneZone {
  id: string;
  title: string;
  u: UnitPos;
  /** Resolved width in px for the given world width. */
  width: number;
  height: number;
  tint: string;
  count: number;
  thumbs: SceneZoneThumb[];
  more: number;
  dropReady: boolean;
  dragging: boolean;
  renaming: boolean;
}

export interface WorldScene {
  objects: SceneObject[];
  zones: SceneZone[];
  dived: boolean;
  rows: number;
  /** Non-null when the floater cap hides objects (the honest scale chip). */
  overflow: { shown: number; total: number } | null;
}

export interface SceneInputs {
  items: Items;
  divedZone: string | null;
  positions: Record<string, UnitPos>;
  zoneWidths: Record<string, number>;
  draggingId: string | null;
  hoverZoneId: string | null;
  renamingZoneId: string | null;
  newIds: string[];
  editingId: string | null;
  selectedIds: string[];
  subjectCounts: Record<string, { needs_attention?: number } | undefined>;
  compact: boolean;
  worldWidth: number;
}

function projectionSubject(o: WorldObject): string {
  return o.kind === "coder"
    ? `coder_session:${String((o.ref as any).agent || "claude")}:${o.id}`
    : qualifiedRef(o.kind, o.id);
}

export function buildScene(input: SceneInputs): WorldScene {
  const allWorld = worldObjects(input.items, input.divedZone);
  const capped =
    allWorld.length > MAX_FLOATERS ? allWorld.slice(0, MAX_FLOATERS) : allWorld;
  const n = capped.length;

  const objects: SceneObject[] = capped.map((o, i) => {
    const u = objUnit(o, i, n, input.positions);
    const m = objMotion(o);
    const selectionRef = qualifiedRef(o.kind, o.id);
    const counts = input.subjectCounts[projectionSubject(o)];
    return {
      key: `${o.kind}:${o.id}`,
      kind: o.kind,
      id: o.id,
      selectionRef,
      title: o.title,
      u,
      phase: m.phase,
      tilt: m.tilt,
      scale: m.scale,
      glow: objGlow(o.kind),
      sprite: spriteUrl(o.kind, o.id),
      small: o.kind === "note" || o.kind === "artifact",
      selected:
        input.selectedIds.includes(selectionRef) ||
        input.selectedIds.includes(o.id),
      dragging: input.draggingId === o.id,
      isNew: input.newIds.includes(o.id),
      editing: input.editingId === o.id,
      attention: counts?.needs_attention || 0,
    };
  });

  const zoneList = worldZones(input.items, input.divedZone);
  const cols = Math.max(
    1,
    Math.min(input.compact ? 2 : 4, zoneList.length || 1),
  );
  const wPct = Math.min(input.compact ? 42 : 30, 84 / cols);
  const zones: SceneZone[] = zoneList.map((z, i) => {
    const zoneKey = `zone:${z.id}`;
    const saved = input.positions[zoneKey];
    const u: UnitPos =
      saved && typeof saved.x === "number"
        ? saved
        : {
            x: ((i % cols) + 0.5) / cols,
            y:
              (input.compact ? 0.2 : 0.13) +
              (Math.floor(i / cols) * 12) / 100,
          };
    const savedWidth = input.zoneWidths[z.id];
    const width = savedWidth
      ? Math.min(ZONE_MAX_W, Math.max(ZONE_MIN_W, savedWidth))
      : Math.min(
          ZONE_DEFAULT_MAX_W,
          Math.max(ZONE_MIN_W, (wPct / 100) * input.worldWidth),
        );
    const memberIds = (((z.ref as any).memberIds as string[]) || []).slice();
    const thumbs: SceneZoneThumb[] = memberIds.slice(0, 4).map((mid) => {
      const r = resolveRef(input.items, mid);
      const kind = r.kind || "note";
      return { id: mid, kind, sprite: spriteUrl(kind, mid) };
    });
    return {
      id: z.id,
      title: z.title,
      u,
      width,
      height: thumbs.length > 0 ? ZONE_THUMBS_H : ZONE_H,
      tint: ZONE_TINTS[variantIndex(z.id, ZONE_TINTS.length)],
      count: memberIds.length,
      thumbs,
      more: Math.max(0, memberIds.length - 4),
      dropReady: input.hoverZoneId === z.id,
      dragging: input.draggingId === zoneKey,
      renaming: input.renamingZoneId === z.id,
    };
  });

  return {
    objects,
    zones,
    dived: Boolean(input.divedZone),
    rows: worldRows(objects.length),
    overflow:
      allWorld.length > objects.length
        ? { shown: objects.length, total: allWorld.length }
        : null,
  };
}

/** An object's hit rectangle in canvas-local px (the DOM column's box). */
export function objectRect(o: SceneObject, rect: WorldRect) {
  const cx = o.u.x * rect.width;
  const cy = o.u.y * rect.height;
  const w = OBJ_W * o.scale;
  const h = OBJ_H * o.scale;
  return { left: cx - w / 2, top: cy - h / 2, width: w, height: h, cx, cy };
}

/** A zone's panel rectangle in canvas-local px (top-center anchored). */
export function zoneRect(z: SceneZone, rect: WorldRect) {
  const cx = z.u.x * rect.width;
  const top = z.u.y * rect.height;
  return {
    left: cx - z.width / 2,
    top,
    width: z.width,
    height: z.height,
    cx,
    cy: top + z.height / 2,
  };
}

export type SceneHit =
  | { type: "object"; object: SceneObject }
  | { type: "zone"; zone: SceneZone }
  | { type: "zone-grip"; zone: SceneZone }
  | { type: "zone-title"; zone: SceneZone }
  | { type: "background" };

/** Hit-test canvas-local coordinates against the scene. Zones sit above
 * resting objects (DOM stacking parity: .desk-zone carried z-index 2); a
 * dragged object never hits itself. Later-drawn things win per layer, so
 * iterate each in reverse. */
export function hitTest(
  scene: WorldScene,
  rect: WorldRect,
  localX: number,
  localY: number,
  opts: { ignoreObjectId?: string | null } = {},
): SceneHit {
  for (let i = scene.zones.length - 1; i >= 0; i--) {
    const z = scene.zones[i];
    const r = zoneRect(z, rect);
    const inside =
      localX >= r.left &&
      localX <= r.left + r.width &&
      localY >= r.top &&
      localY <= r.top + r.height;
    if (!inside) continue;
    const gripPad = 6;
    if (
      localX >= r.left + r.width - GRIP - gripPad &&
      localY >= r.top + r.height - GRIP - gripPad
    ) {
      return { type: "zone-grip", zone: z };
    }
    // The title row: tapping it starts rename (DOM parity — the title span
    // stopped propagation and opened the rename input).
    if (localY <= r.top + 30) return { type: "zone-title", zone: z };
    return { type: "zone", zone: z };
  }
  for (let i = scene.objects.length - 1; i >= 0; i--) {
    const o = scene.objects[i];
    if (opts.ignoreObjectId && o.id === opts.ignoreObjectId) continue;
    const r = objectRect(o, rect);
    if (
      localX >= r.left &&
      localX <= r.left + r.width &&
      localY >= r.top &&
      localY <= r.top + r.height
    ) {
      return { type: "object", object: o };
    }
  }
  return { type: "background" };
}

/** The lasso's roping rule, ported: an object is roped when its rendered
 * center falls inside the client-space rectangle. */
export function ropeObjects(
  scene: WorldScene,
  rect: WorldRect,
  box: { left: number; top: number; right: number; bottom: number },
): string[] {
  const roped: string[] = [];
  for (const o of scene.objects) {
    const cx = rect.left + o.u.x * rect.width;
    const cy = rect.top + o.u.y * rect.height;
    if (cx >= box.left && cx <= box.right && cy >= box.top && cy <= box.bottom)
      roped.push(o.selectionRef);
  }
  return roped;
}

/** Clamp a label to two centered lines with an ellipsis (the DOM's
 * -webkit-line-clamp: 2 contract, done by measure). Greedy word wrap; any
 * text that doesn't fit two lines ends the second line with `…`. */
export function clampLabel(
  title: string,
  measure: (s: string) => number,
  maxWidth: number,
): string {
  const words = String(title || "").split(/\s+/).filter(Boolean);
  if (words.length === 0) return "";
  const lines: string[] = [];
  let line = "";
  let consumed = 0;
  for (const w of words) {
    const probe = line ? `${line} ${w}` : w;
    if (measure(probe) <= maxWidth || !line) {
      line = probe;
      consumed++;
      continue;
    }
    lines.push(line);
    line = w;
    consumed++;
    if (lines.length === 2) {
      consumed--; // the word that opened line 3 was not consumed
      line = "";
      break;
    }
  }
  if (line && lines.length < 2) lines.push(line);
  const truncated = consumed < words.length;
  if ((truncated || measure(lines[lines.length - 1]) > maxWidth) && lines.length) {
    let cut = lines[lines.length - 1];
    while (cut.length > 1 && measure(`${cut}…`) > maxWidth)
      cut = cut.slice(0, -1);
    lines[lines.length - 1] = `${cut}…`;
  }
  return lines.join("\n");
}
