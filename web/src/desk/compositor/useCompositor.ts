/** PHILO-16 — the compositor's DOM side: one owner of window planes, motion
 * and the arrangement grammar (§5, §6).
 *
 * - `usePlane(id)` is the ONE source of a window's `data-plane`,
 *   `data-layer`, z and the `is-front` alias: every frame renders them from
 *   it (live.ts derives them from the depths). Nothing else writes them.
 * - `transition()` is `arrange()`: every window glides from its old rect to
 *   its new one (WAAPI translate + scale, `timing("arrange")`), FLIP style,
 *   so the measured rect is always the destination.
 * - The verbs: tile, stage, exposé, gather, cascade, back (Esc).
 * - The moments: raise (lift), seat and close (a retained snapshot shrinks
 *   into its target while the live window leaves at once). */
import { useEffect, useMemo, useSyncExternalStore } from "react";
import { flushSync } from "react-dom";
import { useDesk } from "../store";
import { saveDeskWorkspace } from "../store/workspaceStorage";
import { workBand } from "../components/window/windowGeometry";
import { shellEls } from "../components/window/windowRegistry";
import {
  bandFor,
  cascade as cascadeRects,
  exposeGrid,
  gather as gatherShares,
  resolveRect,
  stage as stageShares,
  tile as tileShares,
  type Rect,
} from "./geometry";
import { timing } from "./timing";
import type { Plane } from "./planes";
import {
  computePlanes,
  departures,
  getPresentation,
  liveVersion,
  modeNow,
  mountedWindows,
  roomOf,
  setPresentation,
  subscribeLive,
  subscribePresentation,
  zOfWindow,
  type Mode,
  type PlateState,
  type SavedRect,
} from "./live";

// ---- environment ----------------------------------------------------------

function reducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

/** At 393 every window is a sheet: the arrangement grammar has nothing to
 * arrange (the sheet is unchanged). */
export function compactNow(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(max-width: 720px)").matches
  );
}

/** The working band now: below the screen bar, above the dock, inside the
 * side margins (the band `clampIntoBand` keeps every window in). */
export function bandNow(): Rect {
  const vw = typeof window === "undefined" ? 1280 : window.innerWidth || 1280;
  const vh = typeof window === "undefined" ? 800 : window.innerHeight || 800;
  return bandFor(vw, vh, workBand());
}

// ---- hooks ----------------------------------------------------------------

export interface PlaneOf {
  plane: Plane | undefined;
  z: number;
}

/** The plane and z of one window (re-renders on a depth, a minimize, or a
 * window mounting or leaving). */
export function usePlane(id: string): PlaneOf {
  const v = useSyncExternalStore(subscribeLive, liveVersion);
  const depth = useDesk((s) => s.panelDepth);
  const min = useDesk((s) => s.panelMin);
  return useMemo(() => {
    const live = computePlanes(depth, min);
    return { plane: live.planes.get(id), z: zOfWindow(id, live) };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, depth, min, v]);
}

export function usePresentation() {
  return useSyncExternalStore(subscribePresentation, getPresentation);
}

/** The plate a window is drawn as (stage, exposé), or null. */
export function usePlate(id: string): PlateState | null {
  return usePresentation().plates[id] ?? null;
}

export function useMode(): Mode {
  return usePresentation().mode;
}

// ---- the pointer ------------------------------------------------------------

/** Astra M4: a pointer is held down on the desk (a press, a drag, a resize,
 * a divider). No lift runs under a held pointer. Capture phase on the
 * document, so no handler that stops propagation can hide the press. */
let pointerHeld = false;
if (typeof document !== "undefined") {
  const up = () => {
    pointerHeld = false;
  };
  document.addEventListener("pointerdown", () => {
    pointerHeld = true;
  }, true);
  document.addEventListener("pointerup", up, true);
  document.addEventListener("pointercancel", up, true);
  if (typeof window !== "undefined") window.addEventListener("blur", up);
}

export function pointerGestureActive(): boolean {
  return pointerHeld;
}

// ---- motion ownership -----------------------------------------------------

const owned = new WeakMap<Element, Set<Animation>>();

function own(el: Element, anim: Animation) {
  const set = owned.get(el) ?? new Set<Animation>();
  set.add(anim);
  owned.set(el, set);
  const drop = () => set.delete(anim);
  anim.addEventListener?.("finish", drop);
  anim.addEventListener?.("cancel", drop);
}

/** A press or a drag on this window: every compositor motion on it stops
 * at its end state, so nothing animates under the pointer. */
export function stillUnderPointer(el: Element | null): void {
  if (!el) return;
  const set = owned.get(el);
  if (!set) return;
  for (const a of Array.from(set)) a.finish?.();
}

/** §6 moment 1 — the window lifts (scale 1 → 1.012 → 1). The `scale`
 * property composes with any transform already running. */
export function liftOnRaise(el: HTMLElement | null): void {
  // The lift is for a raise the person watches (a key, a menu, a cycle),
  // never one under his pointer (a press, a drag, a resize): Astra M4.
  if (!el || typeof el.animate !== "function" || pointerHeld) return;
  const t = timing("raise", { reducedMotion: reducedMotion() });
  if (!t.duration) return;
  own(
    el,
    el.animate([{ scale: "1" }, { scale: "1.012", offset: 0.5 }, { scale: "1" }], {
      duration: t.duration,
      easing: t.easing,
    }),
  );
}

function visible(r: DOMRect | Rect): Rect {
  const d = r as DOMRect;
  return "width" in d ? { x: d.left, y: d.top, w: d.width, h: d.height } : (r as Rect);
}

function offScreen(r: Rect): boolean {
  const vw = window.innerWidth || 1280;
  const vh = window.innerHeight || 800;
  return r.x + r.w <= 0 || r.y + r.h <= 0 || r.x >= vw || r.y >= vh;
}

/** `arrange()` (§6 moment 4): run `mutate` (store writes, a presentation
 * change), commit it now, then glide each window from where it was to where
 * it is. Translate + scale from the old visual rect; a window that ends out
 * of sight is simply there. */
export function transition(ids: readonly string[], mutate: () => void): void {
  const before = new Map<string, Rect>();
  for (const id of ids) {
    const el = shellEls.get(id);
    if (!el) continue;
    const r = el.getBoundingClientRect();
    if (r.width && r.height) before.set(id, visible(r));
    stillUnderPointer(el);
  }
  flushSync(mutate);
  const reduce = reducedMotion();
  for (const [id, from] of before) {
    const el = shellEls.get(id);
    if (!el || typeof el.animate !== "function") continue;
    const to = visible(el.getBoundingClientRect());
    if (!to.w || !to.h) continue;
    const k = getPresentation().plates[id]?.k ?? 1;
    const distance = Math.hypot(from.x + from.w / 2 - (to.x + to.w / 2), from.y + from.h / 2 - (to.y + to.h / 2));
    const t = timing("arrange", { distance, leaving: offScreen(to), reducedMotion: reduce });
    if (!t.duration) continue;
    if (Math.abs(from.x - to.x) < 0.5 && Math.abs(from.y - to.y) < 0.5 && Math.abs(from.w - to.w) < 0.5 && Math.abs(from.h - to.h) < 0.5)
      continue;
    const tx = (from.x - to.x) / k;
    const ty = (from.y - to.y) / k;
    const sx = from.w / to.w;
    const sy = from.h / to.h;
    own(
      el,
      el.animate(
        [
          { transform: `translate(${tx}px, ${ty}px) scale(${sx}, ${sy})`, transformOrigin: "0 0" },
          { transform: "none", transformOrigin: "0 0" },
        ],
        { duration: t.duration, easing: t.easing },
      ),
    );
  }
}

/** §6 moment 3 — seat and close. The live window leaves the collection at
 * once (the caller does that right after); a retained snapshot (L7) shrinks
 * along a curve into `target` (its dock seat, or the object it opened from)
 * and is removed when the motion reports done. Returns false when there is
 * no motion (reduced motion, no WAAPI): the caller just closes. */
export function departInto(
  id: string,
  el: HTMLElement | null,
  plane: Plane | undefined,
  target: { x: number; y: number } | null,
): boolean {
  if (!el || typeof el.animate !== "function" || !el.parentElement) return false;
  const t = timing("seat", { reducedMotion: reducedMotion() });
  if (!t.duration) return false;
  const r = el.getBoundingClientRect();
  if (!r.width || !r.height) return false;
  const snap = departures.retainSnapshot(id, visible(r), plane ?? "front");
  const clone = el.cloneNode(true) as HTMLElement;
  clone.removeAttribute("id");
  clone.removeAttribute("role");
  clone.removeAttribute("aria-label");
  clone.setAttribute("aria-hidden", "true");
  clone.setAttribute("inert", "");
  // The snapshot is no window: it never reads as a front (one front, by
  // construction) and no query for windows finds it.
  clone.classList.remove("is-front");
  clone.removeAttribute("data-plane");
  clone.removeAttribute("data-layer");
  clone.classList.add("desk-window-departing");
  clone.setAttribute("data-departing", "");
  Object.assign(clone.style, {
    left: `${r.left}px`,
    top: `${r.top}px`,
    width: `${r.width}px`,
    height: `${r.height}px`,
    right: "auto",
    bottom: "auto",
    maxHeight: "none",
    transform: "none",
    pointerEvents: "none",
  });
  el.parentElement.appendChild(clone);
  const frames: Keyframe[] = target
    ? (() => {
        const tx = target.x - (r.left + r.width / 2);
        const ty = target.y - (r.top + r.height / 2);
        return [
          { transform: "none", opacity: 1, transformOrigin: "50% 50%" },
          { transform: `translate(${tx * 0.5}px, ${ty * 0.5 - 40}px) scale(.5)`, opacity: 1, offset: 0.6, transformOrigin: "50% 50%" },
          { transform: `translate(${tx}px, ${ty}px) scale(.06)`, opacity: 0, transformOrigin: "50% 50%" },
        ];
      })()
    : [
        { transform: "scale(1)", opacity: 1 },
        { transform: "scale(.96)", opacity: 0 },
      ];
  const anim = clone.animate(frames, { duration: t.duration, easing: t.easing, fill: "forwards" });
  const done = () => {
    clone.remove();
    departures.release(id, snap.key);
  };
  anim.onfinish = done;
  anim.oncancel = done;
  return true;
}

// ---- the arrangement verbs ------------------------------------------------

function savedNow(ids: readonly string[]): Record<string, SavedRect> {
  const s = useDesk.getState();
  const out: Record<string, SavedRect> = {};
  for (const id of ids)
    out[id] = {
      rect: s.panelRects[id] ?? null,
      arranged: s.panelSaved.includes(id),
      max: s.panelMax.includes(id),
      zoom: s.panelZoom?.[id] ?? null,
    };
  return out;
}

/** Remember the free arrangement once, when an arrangement begins. */
function remember(ids: readonly string[]) {
  const p = getPresentation();
  if (p.mode !== "free") return p.saved;
  return savedNow(ids);
}

/** A window's own full-size rect (the size a plate scales from). */
function layoutRect(id: string): Rect {
  const s = useDesk.getState();
  const el = shellEls.get(id);
  const r = el?.getBoundingClientRect();
  const k = getPresentation().plates[id]?.k ?? 1;
  if (r && r.width && r.height) return { x: r.left, y: r.top, w: r.width / k, h: r.height / k };
  return s.panelRects[id] ?? { x: 0, y: 0, w: 480, h: 360 };
}

/** Write rects as the user's arrangement (persisted), leaving zoom. */
function writeRects(map: ReadonlyMap<string, Rect>) {
  const s = useDesk.getState();
  const panelMax = s.panelMax.filter((id) => !map.has(id));
  const panelRects = { ...s.panelRects };
  const panelSaved = [...s.panelSaved];
  for (const [id, r] of map) {
    panelRects[id] = { x: r.x, y: r.y, w: r.w, h: r.h };
    if (!panelSaved.includes(id)) panelSaved.push(id);
  }
  useDesk.setState({ panelRects, panelSaved, panelMax });
  saveDeskWorkspace(useDesk.getState());
}

function shown(): string[] {
  return computePlanes().shown;
}

function nothing(): boolean {
  return compactNow() || shown().length === 0;
}

/** Tile (⌘⌥← / ⌘⌥→): the front window takes `side`, the near window the
 * other half; they touch, so one steel divider sits between them. */
/** A window's real minimum: the larger of its frame's minW / minH and its
 * rendered CSS min-width / min-height (Astra M2: a surface window is 420 px,
 * Settings wider). */
export function minOf(id: string): { w: number; h: number } {
  const info = mountedWindows().get(id);
  const el = shellEls.get(id);
  const cs = el && typeof getComputedStyle === "function" ? getComputedStyle(el) : null;
  const css = (v: string | undefined) => {
    const n = v ? parseFloat(v) : NaN;
    return Number.isFinite(n) ? n : 0;
  };
  return {
    w: Math.max(info?.minW ?? 0, css(cs?.minWidth)),
    h: Math.max(info?.minH ?? 0, css(cs?.minHeight)),
  };
}

/** Every rect at least its window's minimum and whole inside the band: a
 * window that would render wider than its rect (and so cover its
 * neighbour, or leave the band) is given its real size, pulled back in. */
function fitMinimums(map: Map<string, Rect>, band: Rect): Map<string, Rect> {
  const out = new Map<string, Rect>();
  for (const [id, r] of map) {
    const min = minOf(id);
    const w = Math.min(band.w, Math.max(r.w, min.w));
    const h = Math.min(band.h, Math.max(r.h, min.h));
    out.set(id, {
      x: Math.max(band.x, Math.min(r.x, band.x + band.w - w)),
      y: Math.max(band.y, Math.min(r.y, band.y + band.h - h)),
      w,
      h,
    });
  }
  return out;
}

/** Tile two windows so they share the band at one seam, each at least its
 * minimum. When their minimums do not fit side by side, each keeps its
 * minimum inside the band (they overlap; no divider, the seam is not one). */
function tilePair(left: string, right: string, band: Rect): Map<string, Rect> {
  const minL = minOf(left).w;
  const minR = minOf(right).w;
  let split = Math.round(band.w / 2);
  split = Math.max(split, minL);
  split = Math.min(split, band.w - minR);
  if (split < minL) split = minL;
  return fitMinimums(
    new Map([
      [left, { x: band.x, y: band.y, w: split, h: band.h }],
      [right, { x: band.x + split, y: band.y, w: band.w - split, h: band.h }],
    ]),
    band,
  );
}

export function tileFront(side: "left" | "right"): void {
  if (nothing()) return;
  const ids = shown();
  const front = ids[ids.length - 1];
  const near = ids.length > 1 ? ids[ids.length - 2] : null;
  const band = bandNow();
  const saved = remember(ids);
  const shares = tileShares(front, near, side);
  let map = new Map<string, Rect>();
  for (const [id, v] of shares) map.set(id, resolveRect(v, band));
  // The shares give halves; the windows' real minimums decide the seam.
  map = near
    ? side === "left"
      ? tilePair(front, near, band)
      : tilePair(near, front, band)
    : fitMinimums(map, band);
  transition(ids, () => {
    setPresentation({ mode: "tile", plates: {}, staged: null, saved });
    writeRects(map);
  });
}

/** Stage (⌘⏎, a toggle): the front takes the centre, the rest wait on the
 * shelf as scaled live plates, the nearest on top. */
export function toggleStage(): void {
  if (modeNow() === "stage") {
    back();
    return;
  }
  stageOn(null);
}

export function stageOn(frontArg: string | null): void {
  if (nothing()) return;
  const ids = shown();
  if (ids.length < 2) return;
  const front = frontArg ?? ids[ids.length - 1];
  const band = bandNow();
  const rects: Record<string, Rect> = {};
  for (const id of ids) rects[id] = layoutRect(id);
  const saved = remember(ids);
  const plates: Record<string, PlateState> = {};
  for (const [id, p] of stageShares(front, ids, useDesk.getState().stageShelf, rects, band))
    plates[id] = { rect: resolveRect(p.rect, band), ...(p.k !== undefined ? { k: p.k } : {}) };
  transition(ids, () => setPresentation({ mode: "stage", plates, saved, staged: front }));
}

/** A press on a shelf plate swaps it onto the stage. */
export function stageSwap(id: string): void {
  useDesk.getState().focusPanel(id);
  stageOn(id);
}

/** Exposé (⌘⇧E, ⌃↑): every shown window scales into a grid of live plates. */
export function toggleExposeMode(force?: boolean): void {
  const on = modeNow() === "expose";
  const want = force ?? !on;
  if (want === on) return;
  if (!want) {
    back();
    return;
  }
  if (nothing()) return;
  if (modeNow() === "stage") back();
  const order = Array.from(mountedWindows().keys());
  const ids = shown().sort((a, b) => order.indexOf(a) - order.indexOf(b));
  const band = bandNow();
  const rects: Record<string, Rect> = {};
  for (const id of ids) rects[id] = layoutRect(id);
  const saved = remember(ids);
  const plates: Record<string, PlateState> = {};
  for (const [id, p] of exposeGrid(ids, rects, band))
    plates[id] = { rect: resolveRect(p.rect, band), ...(p.k !== undefined ? { k: p.k } : {}) };
  transition(ids, () => setPresentation({ mode: "expose", plates, saved, staged: null }));
}

/** Pick a plate in exposé: back to the remembered rects, that window in front. */
export function exposePick(id: string): void {
  back();
  const s = useDesk.getState();
  if (s.panelMin.includes(id)) s.restorePanel(id);
  else s.focusPanel(id);
}

/** The Room of the front window, when another shown window shares it. */
export function gatherRoom(): string | null {
  const ids = shown();
  const front = ids[ids.length - 1];
  const room = front ? roomOf(front) : undefined;
  if (!room) return null;
  return ids.filter((id) => roomOf(id) === room).length >= 2 ? room : null;
}

/** Gather (⌘G): the windows of the front window's Room tile the band in
 * equal columns, in one move. */
export function gatherFront(): void {
  if (compactNow()) return;
  const room = gatherRoom();
  if (!room) return;
  const ids = shown();
  const group = ids.filter((id) => roomOf(id) === room);
  const band = bandNow();
  const saved = remember(ids);
  let map = new Map<string, Rect>();
  for (const [id, v] of gatherShares(group)) map.set(id, resolveRect(v, band));
  map = fitMinimums(map, band);
  transition(group, () => {
    setPresentation({ mode: "tile", plates: {}, staged: null, saved });
    writeRects(map);
    // The group comes forward together; the front stays in front.
    for (const id of group) useDesk.getState().focusPanel(id);
  });
}

/** Cascade: every shown window re-seated from the band's top-left in 26 px
 * steps, back to front. Ends any arrangement first. */
export function cascadeAll(): void {
  if (nothing()) return;
  if (modeNow() !== "free") back();
  const ids = shown();
  const rects: Record<string, Rect> = {};
  for (const id of ids) rects[id] = layoutRect(id);
  const map = cascadeRects(ids, rects, bandNow());
  transition(ids, () => writeRects(map));
}

/** Esc — every arrangement returns to the remembered free rects. */
export function back(): boolean {
  const p = getPresentation();
  if (p.mode === "free") return false;
  const saved = p.saved;
  const ids = Array.from(mountedWindows().keys());
  transition(ids, () => {
    setPresentation({ mode: "free", plates: {}, saved: {}, staged: null });
    const s = useDesk.getState();
    const panelRects = { ...s.panelRects };
    const panelZoom = { ...(s.panelZoom ?? {}) };
    let panelSaved = [...s.panelSaved];
    let panelMax = [...s.panelMax];
    let touched = false;
    // Astra M1: BOTH remembered rects (free and zoom) and the zoom flag come
    // back exactly.
    for (const [id, was] of Object.entries(saved)) {
      if (!mountedWindows().has(id)) continue;
      touched = true;
      if (was.rect) panelRects[id] = was.rect;
      else delete panelRects[id];
      if (was.zoom) panelZoom[id] = was.zoom;
      else delete panelZoom[id];
      // Membership only: an id already in place keeps its place.
      if (!was.arranged) panelSaved = panelSaved.filter((x) => x !== id);
      else if (!panelSaved.includes(id)) panelSaved.push(id);
      if (!was.max) panelMax = panelMax.filter((x) => x !== id);
      else if (!panelMax.includes(id)) panelMax.push(id);
    }
    if (touched) {
      useDesk.setState({ panelRects, panelSaved, panelMax, panelZoom });
      saveDeskWorkspace(useDesk.getState());
    }
  });
  return true;
}

/** Stage and Exposé draw plates; the stored geometry is not theirs. */
export function presenting(): boolean {
  const mode = modeNow();
  return mode === "stage" || mode === "expose";
}

/** The plate a window is drawn as now, or null. */
export function plateOf(id: string): PlateState | null {
  return getPresentation().plates[id] ?? null;
}

/** Astra M1: a resize of the staged front writes the STAGE rect only (the
 * plate), never the free or the zoom rect. A scaled plate (the shelf, an
 * exposé plate) is not resized at all. */
export function resizePlate(id: string, rect: Rect): void {
  const p = getPresentation();
  const plate = p.plates[id];
  if (!plate || plate.k !== undefined) return;
  setPresentation({ plates: { ...p.plates, [id]: { ...plate, rect } } });
}

/** The user moved or sized a window by hand: a tiled arrangement is now his
 * own (the user's arrangement is sacred; Esc no longer undoes it). */
export function userArranged(): void {
  if (modeNow() === "tile") setPresentation({ mode: "free", saved: {} });
}

// ---- the desk-level hook ---------------------------------------------------

function typing(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null;
  return Boolean(
    el &&
      (el.tagName === "INPUT" ||
        el.tagName === "TEXTAREA" ||
        el.tagName === "SELECT" ||
        el.isContentEditable ||
        el.closest?.("[contenteditable='true']")),
  );
}

/** Mounted once by the desk: Esc returns any arrangement (before a window's
 * own Escape can close it); stage follows the front window; a window that
 * opens or closes during an arrangement re-arranges it. */
export function useCompositor(): void {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape" || e.isComposing || e.defaultPrevented) return;
      const mode = modeNow();
      if (mode === "free") return;
      // A field keeps its Escape while tiled; an open menu closes first.
      if (mode === "tile" && (typing(e.target) || document.querySelector("[role='menu']"))) return;
      e.preventDefault();
      e.stopImmediatePropagation();
      back();
    };
    document.addEventListener("keydown", onKey, true);
    // Stage follows the front: a raise by any path re-stages (deferred, so
    // the store write that raised is committed first).
    let queued = false;
    const restage = () => {
      if (queued) return;
      queued = true;
      queueMicrotask(() => {
        queued = false;
        const p = getPresentation();
        if (p.mode === "stage") {
          const live = computePlanes();
          if (live.shown.length < 2) back();
          else if (live.front !== p.staged || live.shown.some((id) => !p.plates[id])) stageOn(live.front);
        } else if (p.mode === "expose") {
          const live = computePlanes();
          if (live.shown.some((id) => !p.plates[id]) || Object.keys(p.plates).some((id) => !live.shown.includes(id)))
            back();
        }
      });
    };
    const offDesk = useDesk.subscribe((s, prev) => {
      if (s.panelDepth !== prev.panelDepth || s.panelMin !== prev.panelMin) restage();
    });
    const offLive = subscribeLive(restage);
    const onResize = () => {
      if (modeNow() === "stage" || modeNow() === "expose") back();
    };
    window.addEventListener("resize", onResize);
    return () => {
      document.removeEventListener("keydown", onKey, true);
      offDesk();
      offLive();
      window.removeEventListener("resize", onResize);
    };
  }, []);
}
