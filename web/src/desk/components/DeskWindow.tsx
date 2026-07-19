// The desk-window contract (Phase 93 UI remediation; HS-95-02 makes it an
// OS): floating desk panels are windows, not fixtures. The `useDeskWindow`
// hook below carries the physics — drag (by the head), resize (corner
// grip), focus-to-front, persisted rect — and `DeskWindowFrame` is the ONE
// container every window renders through: one chrome (icon · title ·
// actions · minimize/maximize/close), a children content slot, lifecycle
// state in the store (`panelMin`/`panelMax`, persisted in the same
// `hs.desk.panels` slot as the rects), and the phone's bottom-sheet form.
// The hook is module-private on purpose: windows do not hand-wire physics.
import {
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { motion, useReducedMotion } from "motion/react";
import { useDrag } from "@use-gesture/react";
import { useDesk, type PanelRect } from "../store";
import { DeskMenuItem, DeskMenuList } from "./DeskMenu";
// The physics constants mirror the CSS component tokens — one generated
// source (design-tokens.json), no drift possible (HS-96-02).
import { DESK_WINDOW, DESK_Z } from "../../lib/tokens.gen";

/** Viewport margin windows are clamped inside. */
const MARGIN = DESK_WINDOW.margin;
/** Minimum visible head strip so a window can always be grabbed back. */
const GRAB = DESK_WINDOW.grab;
/** The desk-window z band (see the ladder note in desk.css). */
const Z_BASE = DESK_Z.windowBase;
/** Cascade step when several default-corner windows are open at once. */
const CASCADE = DESK_WINDOW.cascade;

/** The window head strip considered for title-bar occlusion (px). */
const HEAD = 44;

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
  const top = DESK_WINDOW.snapTop;
  const bottom = DESK_WINDOW.snapBottom;
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
  const top = DESK_WINDOW.snapTop;
  const bottom = DESK_WINDOW.snapBottom;
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
  const top = DESK_WINDOW.snapTop; // below the chrome band
  const bottom = DESK_WINDOW.snapBottom; // clear of the dock band
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

/** HS-97-05 — the snap ghost: while a head drag hovers a snap region,
 * the landing tile renders as a translucent preview. Module-level
 * publisher so the one ghost lives outside any window. */
let ghostRect: PanelRect | null = null;
const ghostListeners = new Set<() => void>();
function publishGhost(r: PanelRect | null) {
  const same =
    (r === null && ghostRect === null) ||
    (r !== null &&
      ghostRect !== null &&
      r.x === ghostRect.x &&
      r.y === ghostRect.y &&
      r.w === ghostRect.w &&
      r.h === ghostRect.h);
  if (same) return;
  ghostRect = r;
  for (const l of ghostListeners) l();
}

export function SnapGhost() {
  const rect = useSyncExternalStore(
    (cb) => {
      ghostListeners.add(cb);
      return () => ghostListeners.delete(cb);
    },
    () => ghostRect,
  );
  if (!rect) return null;
  return (
    <div
      className="desk-snap-ghost"
      style={{ top: rect.y, left: rect.x, width: rect.w, height: rect.h }}
      aria-hidden="true"
    />
  );
}

/** HS-97-06 — the exposé grid: N non-overlapping cells inside the
 * working band, last row centered. Pure, pinned by test. */
export function exposeLayout(
  count: number,
  vw: number,
  vh: number,
): PanelRect[] {
  const top = DESK_WINDOW.snapTop + 8;
  const bottom = DESK_WINDOW.snapBottom + 8;
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

function clampRect(r: PanelRect, minW: number, minH: number): PanelRect {
  const vw = window.innerWidth || 1280;
  const vh = window.innerHeight || 800;
  let w = Math.min(Math.max(r.w, minW), vw - MARGIN * 2);
  let h = Math.min(Math.max(r.h, minH), vh - MARGIN * 2);
  const x = Math.min(Math.max(r.x, MARGIN - w + GRAB), vw - GRAB);
  const y = Math.min(Math.max(r.y, MARGIN), vh - 48);
  // Keep the resize grip reachable: a window dragged toward an edge
  // shrinks to fit the viewport (floored at its minimum) rather than
  // sliding its bottom-right corner off-screen.
  w = Math.max(minW, Math.min(w, vw - MARGIN - x));
  h = Math.max(minH, Math.min(h, vh - MARGIN - y));
  return { x, y, w, h };
}

export interface DeskWindowOptions {
  minW?: number;
  minH?: number;
  /** Pass false while the panel renders nothing (launcher-only mounts). */
  open?: boolean;
}

/** The desk-window physics (Phase 93). Module-private since HS-95-02:
 * every window adopts it through `DeskWindowFrame`, never by hand. */
function useDeskWindow(id: string, opts: DeskWindowOptions = {}) {
  const minW = opts.minW ?? 320;
  const minH = opts.minH ?? 220;
  const open = opts.open ?? true;
  const rect = useDesk((s) => s.panelRects[id]);
  const orderIndex = useDesk((s) => s.panelOrder.indexOf(id));
  const elRef = useRef<HTMLElement | null>(null);

  const measure = (): PanelRect => {
    const cur = useDesk.getState().panelRects[id];
    if (cur) return cur;
    const el = elRef.current;
    const r = el?.getBoundingClientRect();
    if (!el || !r || !r.width) return { x: MARGIN, y: 64, w: 400, h: 480 };
    // The entrance spring translates the panel; strip the live transform so
    // a mid-animation measure still yields the settled rect.
    let tx = 0;
    let ty = 0;
    try {
      const t = getComputedStyle(el).transform;
      if (t && t !== "none") {
        const m = new DOMMatrixReadOnly(t);
        tx = m.m41;
        ty = m.m42;
      }
    } catch {
      /* environments without DOMMatrix just measure as-is */
    }
    return { x: r.left - tx, y: r.top - ty, w: r.width, h: r.height };
  };

  // HS-97-02 — a window lands well. Opening places the window through
  // the engine (seeded at its CSS default home, moved off other title
  // bars, always whole inside the working band); a persisted rect is
  // clamped into the band and otherwise untouched (the arrangement is
  // sacred). Sheets (compact viewports) own their own form.
  useEffect(() => {
    if (!open) return;
    // Present, don't blindly raise: a window rehydrating on reload keeps
    // its remembered plane in the stacking order (HS-97-03).
    useDesk.getState().presentPanel(id);
    if (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(max-width: 720px)").matches
    )
      return;
    const s = useDesk.getState();
    const vw = window.innerWidth || 1280;
    const vh = window.innerHeight || 800;
    const cur = s.panelRects[id];
    if (cur) {
      const kept = clampIntoBand(cur, vw, vh, minW, minH);
      if (
        kept.x !== cur.x ||
        kept.y !== cur.y ||
        kept.w !== cur.w ||
        kept.h !== cur.h
      )
        s.setPanelRect(id, kept, s.panelSaved.includes(id));
    } else {
      const others = registrySnapshot
        .filter((w) => w.id !== id && !s.panelMin.includes(w.id))
        .map((w) => s.panelRects[w.id])
        .filter((r): r is PanelRect => Boolean(r));
      const seed = measure();
      // Lazy cores may still be a Suspense fallback at measure time; a
      // window's geometry comes from its CSS constraint (max-height),
      // never from the transient content height. The default seat is
      // capped below the full band so title bars can stagger — a
      // full-band window is a choice (resize/maximize), not a default
      // (HS-97-09).
      const el = elRef.current;
      if (el) {
        const mh = parseFloat(getComputedStyle(el).maxHeight);
        const cap = Math.max(
          minH,
          Math.round(
            ((vh - DESK_WINDOW.snapTop - DESK_WINDOW.snapBottom) * 78) / 100,
          ),
        );
        if (Number.isFinite(mh) && mh > seed.h)
          seed.h = Math.min(mh, cap);
      }
      s.setPanelRect(id, placeWindow(seed, others, vw, vh, minW, minH));
    }
    return () => {
      // An unarranged (never persisted) rect is ephemeral: forget it so
      // the panel is re-placed from its default home next time. Closing
      // also leaves the stacking order, so a reopen presents on top.
      const st = useDesk.getState();
      if (!st.panelSaved.includes(id) && st.panelRects[id])
        st.resetPanelRect(id);
      st.retirePanel(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, open]);

  const dragBind = useDrag(
    ({ event, first, last, movement: [mx, my], memo }) => {
      // Buttons and inputs inside the head keep their own gestures.
      if (first) {
        const t = event?.target as HTMLElement | null;
        if (t?.closest("button, a, input, textarea, select, [role='button']"))
          return { skip: true };
      }
      if (memo?.skip) return memo;
      const base: PanelRect = memo?.base ?? measure();
      if (Math.abs(mx) + Math.abs(my) > 3) {
        // A snap region shows its landing tile as a live ghost while
        // dragging (HS-97-05); releasing inside it lands exactly there
        // (HS-95-03); anywhere else parks the dragged rect as before.
        const ev = event as PointerEvent | undefined;
        const tile =
          ev && typeof ev.clientX === "number"
            ? snapForPointer(
                ev.clientX,
                ev.clientY,
                window.innerWidth || 1280,
                window.innerHeight || 800,
              )
            : null;
        publishGhost(last ? null : tile);
        useDesk
          .getState()
          .setPanelRect(
            id,
            (last ? tile : null) ??
              clampRect(
                { ...base, x: base.x + mx, y: base.y + my },
                minW,
                minH,
              ),
            last,
          );
      } else if (last) {
        publishGhost(null);
      }
      return { base, skip: false };
    },
    { pointer: { buttons: 1 } },
  );

  const resizeBind = useDrag(
    ({ movement: [mx, my], last, memo }) => {
      const base: PanelRect = memo?.base ?? measure();
      useDesk
        .getState()
        .setPanelRect(
          id,
          clampRect({ ...base, w: base.w + mx, h: base.h + my }, minW, minH),
          last,
        );
      return { base };
    },
    { pointer: { buttons: 1 } },
  );

  // HS-97-05 — the frame resizes from its edges, not one corner.
  const edgeBind = useDrag(
    ({ args, movement: [mx, my], last, memo }) => {
      const mode = String(args?.[0] ?? "br");
      const base: PanelRect = memo?.base ?? measure();
      useDesk
        .getState()
        .setPanelRect(id, resizeEdge(mode, base, mx, my, minW, minH), last);
      return { base };
    },
    { pointer: { buttons: 1 } },
  );
  const edgeStyle = { touchAction: "none" } as React.CSSProperties;
  const edges = (
    <>
      <span
        className="desk-window-edge desk-window-edge-l"
        {...edgeBind("l")}
        style={edgeStyle}
        aria-hidden="true"
      />
      <span
        className="desk-window-edge desk-window-edge-r"
        {...edgeBind("r")}
        style={edgeStyle}
        aria-hidden="true"
      />
      <span
        className="desk-window-edge desk-window-edge-b"
        {...edgeBind("b")}
        style={edgeStyle}
        aria-hidden="true"
      />
      <span
        className="desk-window-corner desk-window-corner-bl"
        {...edgeBind("bl")}
        style={edgeStyle}
        aria-hidden="true"
      />
    </>
  );

  const style: React.CSSProperties = rect
    ? {
        top: rect.y,
        left: rect.x,
        width: rect.w,
        height: rect.h,
        right: "auto",
        bottom: "auto",
        maxHeight: "none",
        zIndex: Z_BASE + Math.max(orderIndex, 0),
      }
    : { zIndex: Z_BASE + Math.max(orderIndex, 0) };

  return {
    /** True when the user (or the cascade) gave this window its own rect. */
    floating: Boolean(rect),
    style,
    setEl: (el: HTMLElement | null) => {
      elRef.current = el;
    },
    focus: () => useDesk.getState().focusPanel(id),
    handleProps: {
      ...dragBind(),
      style: { touchAction: "none" } as React.CSSProperties,
    },
    grip: (
      <span className="desk-window-grip" {...resizeBind()} aria-hidden="true" />
    ),
    edges,
  };
}

/** Dock chip elements by window id — the minimize/restore motion's
 * target (HS-97-04). Populated by the Dock's ref callbacks. */
const chipEls = new Map<string, HTMLElement>();

/** Window shell elements by id — the exposé's fan targets (HS-97-06). */
const shellEls = new Map<string, HTMLElement>();

/** HS-97-06 — exposé state (module-level so the dock verb and the
 * keyboard share one truth). */
let exposeActive = false;
const exposeListeners = new Set<() => void>();
export function toggleExpose(force?: boolean) {
  const next = force ?? !exposeActive;
  if (next === exposeActive) return;
  exposeActive = next;
  for (const l of exposeListeners) l();
}

/** HS-97-06 — the transient switcher strip's state. */
let switcherState: {
  items: { id: string; label: string; glyph: string }[];
  target: string;
} | null = null;
let switcherTimer: ReturnType<typeof setTimeout> | undefined;
const switcherListeners = new Set<() => void>();
function flashSwitcher(target: string) {
  switcherState = {
    items: registrySnapshot.map((w) => ({
      id: w.id,
      label: w.label,
      glyph: w.glyph,
    })),
    target,
  };
  for (const l of switcherListeners) l();
  clearTimeout(switcherTimer);
  switcherTimer = setTimeout(() => {
    switcherState = null;
    for (const l of switcherListeners) l();
  }, 900);
}

/** The visible MRU switcher (HS-97-06): while Ctrl+` cycles, a strip
 * names every open window with the landing target highlighted, fading
 * once the cycle settles. */
export function Switcher() {
  const st = useSyncExternalStore(
    (cb) => {
      switcherListeners.add(cb);
      return () => switcherListeners.delete(cb);
    },
    () => switcherState,
  );
  if (!st) return null;
  return (
    <div className="desk-switcher" role="status">
      {st.items.map((w) => (
        <span
          key={w.id}
          className={
            "desk-switcher-chip" + (w.id === st.target ? " is-target" : "")
          }
        >
          <span aria-hidden="true">{w.glyph}</span> {w.label}
        </span>
      ))}
    </div>
  );
}

/** The exposé (HS-97-06): fans every open window into a pick grid —
 * live shells scale into their cells (compositor transforms), minimized
 * windows join as dimmed cards; click or Enter focuses, Escape cancels. */
export function Expose() {
  const active = useSyncExternalStore(
    (cb) => {
      exposeListeners.add(cb);
      return () => exposeListeners.delete(cb);
    },
    () => exposeActive,
  );
  const windows = useOpenWindows();
  const panelMin = useDesk((s) => s.panelMin);
  const reducedMotion = useReducedMotion();
  const firstBtnRef = useRef<HTMLButtonElement | null>(null);
  const fannedRef = useRef<
    { el: HTMLElement; anim: Animation }[]
  >([]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "ArrowUp") {
        e.preventDefault();
        toggleExpose();
      } else if (e.key === "Escape" && exposeActive) {
        e.preventDefault();
        toggleExpose(false);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const entries = windows.map((w) => ({
    ...w,
    minimized: panelMin.includes(w.id),
  }));
  const vw = typeof window === "undefined" ? 1280 : window.innerWidth || 1280;
  const vh = typeof window === "undefined" ? 800 : window.innerHeight || 800;
  const cells = exposeLayout(Math.max(entries.length, 1), vw, vh);

  useEffect(() => {
    if (!active) return;
    const fanned: { el: HTMLElement; anim: Animation }[] = [];
    entries.forEach((en, i) => {
      if (en.minimized) return;
      const el = shellEls.get(en.id);
      if (!el || typeof el.animate !== "function") return;
      const r = el.getBoundingClientRect();
      if (!r.width) return;
      const cell = cells[i];
      const s = Math.min(cell.w / r.width, cell.h / r.height, 1);
      const dx = cell.x + cell.w / 2 - (r.x + r.width / 2);
      const dy = cell.y + cell.h / 2 - (r.y + r.height / 2);
      const anim = el.animate(
        [
          { transform: "translate(0, 0) scale(1)" },
          { transform: `translate(${dx}px, ${dy}px) scale(${s})` },
        ],
        {
          duration: reducedMotion ? 0 : 220,
          easing: "cubic-bezier(.2, .8, .2, 1)",
          fill: "forwards",
        },
      );
      fanned.push({ el, anim });
    });
    fannedRef.current = fanned;
    firstBtnRef.current?.focus();
    return () => {
      for (const { el, anim } of fannedRef.current) {
        try {
          const current = getComputedStyle(el).transform;
          anim.cancel();
          if (!reducedMotion && current && current !== "none")
            el.animate(
              [{ transform: current }, { transform: "none" }],
              { duration: 180, easing: "cubic-bezier(.2, .8, .2, 1)" },
            );
        } catch {
          /* jsdom or torn-down element: nothing to unwind */
        }
      }
      fannedRef.current = [];
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  if (!active || entries.length === 0) return null;
  return (
    <>
      <div className="desk-expose-scrim" aria-hidden="true" />
      <div
        className="desk-expose"
        // A region, not a dialog: the desk's no-modal law holds — no
        // trap, Escape and the backdrop dismiss (Phase 73 lock).
        role="group"
        aria-label="Window overview"
        onClick={(e) => {
          if (e.target === e.currentTarget) toggleExpose(false);
        }}
      >
        {entries.map((en, i) => (
          <button
            key={en.id}
            type="button"
            ref={i === 0 ? firstBtnRef : undefined}
            className={"desk-expose-cell" + (en.minimized ? " is-min" : "")}
            style={{
              top: cells[i].y,
              left: cells[i].x,
              width: cells[i].w,
              height: cells[i].h,
            }}
            aria-label={`Focus ${en.label}`}
            onClick={() => {
              toggleExpose(false);
              const s = useDesk.getState();
              if (s.panelMin.includes(en.id)) s.restorePanel(en.id);
              else s.focusPanel(en.id);
            }}
          >
            <span className="desk-expose-name">
              <span aria-hidden="true">{en.glyph}</span> {en.label}
            </span>
          </button>
        ))}
      </div>
    </>
  );
}

/** HS-97-07 — dock launchers: fixed shelf verbs (Desk memory, Delivery,
 * Panes) announce themselves so ONE dock carries launch and running
 * state; the floating pills are gone. */
export interface DockLauncher {
  id: string;
  label: string;
  glyph: string;
  open: boolean;
  badge?: number;
  activate: () => void;
}
const LAUNCHER_SEAT: Record<string, number> = {
  attention: 0,
  "delivery-board": 1,
  panes: 2,
};
const launcherRegistry = new Map<string, DockLauncher>();
let launcherSnapshot: DockLauncher[] = [];
const launcherListeners = new Set<() => void>();
function publishLaunchers() {
  launcherSnapshot = Array.from(launcherRegistry.values()).sort(
    (a, b) => (LAUNCHER_SEAT[a.id] ?? 9) - (LAUNCHER_SEAT[b.id] ?? 9),
  );
  for (const l of launcherListeners) l();
}
export function announceLauncher(l: DockLauncher) {
  launcherRegistry.set(l.id, l);
  publishLaunchers();
}
export function retractLauncher(id: string) {
  launcherRegistry.delete(id);
  publishLaunchers();
}
function useLaunchers() {
  return useSyncExternalStore(
    (cb) => {
      launcherListeners.add(cb);
      return () => launcherListeners.delete(cb);
    },
    () => launcherSnapshot,
  );
}

/** Open windows announce themselves (title/icon/close) so the dock can
 * name and drive them without a parallel registry. */
const windowRegistry = new Map<
  string,
  { label: string; glyph: string; close: () => void }
>();
const registryListeners = new Set<() => void>();
let registrySnapshot: {
  id: string;
  label: string;
  glyph: string;
  close: () => void;
}[] = [];

function announceWindow(
  id: string,
  label: string,
  glyph: string,
  close: () => void,
) {
  windowRegistry.set(id, { label, glyph, close });
  publishRegistry();
}

function retractWindow(id: string) {
  windowRegistry.delete(id);
  publishRegistry();
}

function publishRegistry() {
  registrySnapshot = Array.from(windowRegistry.entries()).map(
    ([id, v]) => ({ id, ...v }),
  );
  for (const l of registryListeners) l();
}

export function useOpenWindows() {
  return useSyncExternalStore(
    (cb) => {
      registryListeners.add(cb);
      return () => registryListeners.delete(cb);
    },
    () => registrySnapshot,
  );
}

function useCompactViewport(): boolean {
  return useSyncExternalStore(
    (cb) => {
      if (typeof window.matchMedia !== "function") return () => {};
      const mq = window.matchMedia("(max-width: 720px)");
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    },
    () =>
      typeof window.matchMedia === "function"
        ? window.matchMedia("(max-width: 720px)").matches
        : false,
  );
}

export interface DeskWindowFrameProps {
  id: string;
  /** The head title (any node). Pass `label` when it isn't plain text. */
  title: ReactNode;
  /** Plain-text name for the tray/dock and aria labels. */
  label?: string;
  /** A small leading glyph/avatar node (the window's face). */
  icon?: ReactNode;
  /** One-character dock face when `icon` is a node (default ▢). */
  glyph?: string;
  /** Content before the icon (e.g. a back chip). */
  leading?: ReactNode;
  /** One-word kind eyebrow — DEMOTED from the head (HS-97-07, Article
   * VII.1); accepted for compatibility, no longer rendered. */
  eyebrow?: string;
  /** Extra head content (badges, panel-specific verbs), left of the window verbs. */
  actions?: ReactNode;
  /** HS-100-07 — the application's wing segments, centered in the head
   * (the thesis's posture rule: faces live in the head, never as a tab
   * wall in the body). */
  wings?: ReactNode;
  /** Root classes — keep the panel's legacy class so its content CSS holds. */
  className?: string;
  minW?: number;
  minH?: number;
  open: boolean;
  onClose: () => void;
  /** Heavy content may unmount while minimized (default: stays mounted). */
  unmountOnMinimize?: boolean;
  /** Entrance spring (the Phase 93 slide-in). Default true. */
  entrance?: boolean;
  /** Inline style merged under the window geometry (e.g. CSS vars). */
  rootStyle?: React.CSSProperties;
  children?: ReactNode;
}

/** THE window. One chrome, one lifecycle, one physics contract — content
 * plugs in as children (Constitution, Article I: features do not own
 * surfaces). */
/** HS-99-02 — the window verb glyphs: crisp inline SVG strokes that
 * inherit currentColor (text glyphs read as characters, not chrome). */
function VerbGlyph({ kind }: { kind: string }) {
  const paths: Record<string, string> = {
    minimize: "M3 7h8",
    maximize: "M3.5 3.5h7v7h-7Z",
    restore: "M3 5.2h5.8V11H3Z M5.2 5.2V3H11v5.8H8.8",
    close: "M3.5 3.5l7 7M10.5 3.5l-7 7",
    "light-close": "M3.6 3.6l6.8 6.8M10.4 3.6l-6.8 6.8",
    "light-min": "M3 7h8",
    "light-max": "M7 3v8M3 7h8",
    "light-restore": "M4 7h6M7 4l-3 3 3 3M7 4l3 3-3 3",
  };
  return (
    <svg
      viewBox="0 0 14 14"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.3"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[kind]} />
    </svg>
  );
}

export function DeskWindowFrame(props: DeskWindowFrameProps) {
  const {
    id,
    title,
    label,
    icon,
    glyph: glyphProp,
    leading,
    actions,
    wings,
    className,
    minW,
    minH,
    open,
    onClose,
    unmountOnMinimize,
    entrance = true,
    rootStyle,
    children,
  } = props;
  const minimized = useDesk((s) => s.panelMin.includes(id));
  const maximized = useDesk((s) => s.panelMax.includes(id));
  // HS-97-04 — the front window is the last id in the stacking order
  // that is open (announced) and not minimized; it alone wears depth.
  const isFront = useDesk((s) => {
    for (let i = s.panelOrder.length - 1; i >= 0; i--) {
      const oid = s.panelOrder[i];
      if (s.panelMin.includes(oid)) continue;
      if (!windowRegistry.has(oid)) continue;
      return oid === id;
    }
    return false;
  });
  const compact = useCompactViewport();
  const reducedMotion = useReducedMotion();
  const win = useDeskWindow(id, { minW, minH, open: open && !minimized });
  const glyph = glyphProp ?? (typeof icon === "string" ? icon : "▢");
  const name = label ?? (typeof title === "string" ? title : id);

  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  // HS-99-02 — the head's right-click menu (chrome ladder rule 2).
  const [headMenu, setHeadMenu] = useState<{ x: number; y: number } | null>(
    null,
  );
  useEffect(() => {
    if (!headMenu) return;
    const close = () => setHeadMenu(null);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("pointerdown", close);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("pointerdown", close);
      window.removeEventListener("keydown", onKey);
    };
  }, [headMenu]);

  // HS-97-04 — motion tells the story: close animates out; minimize
  // contracts toward the window's dock chip and restore returns from
  // it. WAAPI (compositor-only transform/opacity), skipped under
  // reduced motion or where unavailable (jsdom).
  const shellRef = useRef<HTMLDivElement | null>(null);
  const leavingRef = useRef(false);
  const dockChip = () => chipEls.get(id) ?? null;
  const flyToChip = (el: HTMLElement, chip: Element, reverse: boolean) => {
    const c = chip.getBoundingClientRect();
    const r = el.getBoundingClientRect();
    const dx = c.x + c.width / 2 - (r.x + r.width / 2);
    const dy = c.y + c.height / 2 - (r.y + r.height / 2);
    const away = { transform: `translate(${dx}px, ${dy}px) scale(0.06)`, opacity: 0 };
    const home = { transform: "translate(0, 0) scale(1)", opacity: 1 };
    return el.animate(reverse ? [away, home] : [home, away], {
      duration: 220,
      easing: "cubic-bezier(.2, .8, .2, 1)",
      fill: "forwards",
    });
  };
  const requestClose = () => {
    const el = shellRef.current;
    if (leavingRef.current) return;
    if (!el || typeof el.animate !== "function" || reducedMotion) {
      closeRef.current();
      return;
    }
    leavingRef.current = true;
    const anim = el.animate(
      [
        { opacity: 1, transform: "scale(1)" },
        { opacity: 0, transform: "scale(0.96)" },
      ],
      { duration: 140, easing: "ease-in", fill: "forwards" },
    );
    anim.onfinish = () => {
      leavingRef.current = false;
      closeRef.current();
    };
  };
  const requestMinimize = () => {
    const el = shellRef.current;
    const chip = dockChip();
    const done = () => useDesk.getState().minimizePanel(id);
    if (!el || typeof el.animate !== "function" || reducedMotion || !chip) {
      done();
      return;
    }
    const anim = flyToChip(el, chip, false);
    anim.onfinish = () => {
      anim.cancel(); // release the forwards fill before display:none
      done();
    };
  };
  const prevMinRef = useRef(false);
  useEffect(() => {
    const was = prevMinRef.current;
    prevMinRef.current = minimized;
    if (!was || minimized) return;
    // Restore: the window returns from its dock chip.
    const el = shellRef.current;
    const chip = dockChip();
    if (el && typeof el.animate === "function" && !reducedMotion && chip)
      flyToChip(el, chip, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [minimized]);

  useEffect(() => {
    if (!open) return;
    announceWindow(id, name, glyph, () => requestClose());
    return () => retractWindow(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, id, name, glyph]);

  // HS-96-05 — window focus management (the ui-styling a11y pattern,
  // WITHOUT a modal trap: windows coexest is the law). Opening moves
  // focus into the window; closing returns it to the opener; Escape
  // anywhere inside closes this window.
  const openerRef = useRef<HTMLElement | null>(null);
  useEffect(() => {
    if (!open) return;
    openerRef.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    shellRef.current?.focus({ preventScroll: true });
    return () => {
      const opener = openerRef.current;
      if (opener && document.contains(opener))
        opener.focus({ preventScroll: true });
    };
  }, [open, id]);

  // Opening always PRESENTS the window. A stale in-session minimize
  // (window closed while parked, reopened later) would otherwise open it
  // invisibly parked — a stranded surface. Minimize is session-scoped by
  // design and never persisted (HS-97-03); rects/order/maximize persist.
  useEffect(() => {
    if (open && useDesk.getState().panelMin.includes(id))
      useDesk.getState().restorePanel(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, id]);

  if (!open) return null;
  if (minimized && unmountOnMinimize) return null;

  const maxed = maximized && !compact;
  const style: React.CSSProperties = {
    ...rootStyle,
    ...(compact
      ? { zIndex: (win.style.zIndex as number) ?? 42 }
      : maxed
        ? {
            top: 54,
            left: 10,
            right: 10,
            bottom: 10,
            width: "auto",
            height: "auto",
            maxHeight: "none",
            zIndex: win.style.zIndex,
          }
        : win.style),
    ...(minimized ? { display: "none" } : null),
  };

  return (
    <motion.div
      ref={(el: HTMLDivElement | null) => {
        win.setEl(el);
        shellRef.current = el;
        if (el) shellEls.set(id, el);
        else shellEls.delete(id);
      }}
      tabIndex={-1}
      onKeyDown={(e) => {
        if (e.key === "Escape" && !e.defaultPrevented) {
          e.stopPropagation();
          // HS-99-02 — an open head menu absorbs the first Escape; the
          // window only closes on the next one.
          if (headMenu) {
            setHeadMenu(null);
            return;
          }
          requestClose();
        }
      }}
      className={
        (className ? className + " " : "") +
        "desk-window desk-window-shell" +
        (win.floating ? " is-floating" : "") +
        (compact ? " is-sheet" : "") +
        (maxed ? " is-max" : "") +
        (isFront ? " is-front" : "")
      }
      style={style}
      initial={reducedMotion || !entrance ? false : { x: 60, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 30 }}
      onPointerDown={(e) => {
        win.focus();
        e.stopPropagation();
      }}
      role="region"
      aria-label={name}
    >
      <header
        className={`desk-pullout-head desk-window-handle${wings ? " has-wings" : ""}`}
        {...(compact || maxed ? {} : win.handleProps)}
        onDoubleClick={(e) => {
          // HS-97-05 — double-click the head toggles maximize (buttons
          // inside the head keep their own clicks).
          if (compact) return;
          const t = e.target as HTMLElement | null;
          if (t?.closest("button, a, input, textarea, select")) return;
          useDesk.getState().toggleMaximizePanel(id);
        }}
        onContextMenu={(e) => {
          // HS-99-02 — the bar owns its window verbs on right-click.
          const t = e.target as HTMLElement | null;
          if (t?.closest("button, a, input, textarea, select")) return;
          e.preventDefault();
          setHeadMenu({ x: e.clientX, y: e.clientY });
        }}
      >
        {/* Materials spike — traffic lights on the LEFT (the strongest
            native cue there is): red close, yellow minimize, green
            maximize; grey when the window is not front; glyphs reveal
            on cluster hover. */}
        <span className="desk-traffic">
          <button
            type="button"
            className="desk-light desk-light-close"
            aria-label={`Close ${name}`}
            onClick={requestClose}
          >
            <VerbGlyph kind="light-close" />
          </button>
          <button
            type="button"
            className="desk-light desk-light-min"
            aria-label={`Minimize ${name}`}
            onClick={requestMinimize}
          >
            <VerbGlyph kind="light-min" />
          </button>
          {!compact ? (
            <button
              type="button"
              className="desk-light desk-light-max"
              aria-label={maximized ? `Restore ${name}` : `Maximize ${name}`}
              onClick={() => useDesk.getState().toggleMaximizePanel(id)}
            >
              <VerbGlyph kind={maximized ? "light-restore" : "light-max"} />
            </button>
          ) : (
            <span aria-hidden="true" />
          )}
        </span>
        {leading}
        {icon}
        {/* HS-97-07 — the eyebrow is demoted: window identity is icon +
            title (Article VII.1); the prop survives for callers/AT. */}
        <span className="desk-pullout-title desk-window-title">{title}</span>
        {wings}
        {actions}
      </header>
      {headMenu ? (
        <DeskMenuList
          className="desk-head-menu"
          label={`${name} window menu`}
          anchor="below"
          style={{
            left: Math.min(headMenu.x, window.innerWidth - 184),
            top: Math.min(headMenu.y, window.innerHeight - 132),
          }}
          onClose={() => setHeadMenu(null)}
        >
          <DeskMenuItem
            glyph={<VerbGlyph kind="minimize" />}
            onSelect={() => {
              setHeadMenu(null);
              requestMinimize();
            }}
          >
            Minimize
          </DeskMenuItem>
          {!compact && (
            <DeskMenuItem
              glyph={<VerbGlyph kind={maximized ? "restore" : "maximize"} />}
              onSelect={() => {
                setHeadMenu(null);
                useDesk.getState().toggleMaximizePanel(id);
              }}
            >
              {maximized ? "Restore" : "Maximize"}
            </DeskMenuItem>
          )}
          <DeskMenuItem
            glyph={<VerbGlyph kind="close" />}
            onSelect={() => {
              setHeadMenu(null);
              requestClose();
            }}
          >
            Close
          </DeskMenuItem>
        </DeskMenuList>
      ) : null}
      {children}
      {!maxed && !compact ? win.grip : null}
      {!maxed && !compact ? win.edges : null}
    </motion.div>
  );
}

/** MRU order over the currently-open windows (front last, like the z
 * band). Windows never focused yet sort first. */
function mruOrder(ids: string[], order: string[]): string[] {
  return [...ids].sort((a, b) => order.indexOf(a) - order.indexOf(b));
}

/** The dock (HS-95-03): every open window as a chip — tap focuses (or
 * restores a parked one), ✕ closes, ⟲ resets the layout. Ctrl+` cycles
 * focus in MRU order, restoring as it lands. Shell furniture: it rides
 * above the window band, and it is invisible while nothing is open. */
export function Dock({ center }: { center?: ReactNode } = {}) {
  const panelMin = useDesk((s) => s.panelMin);
  const panelOrder = useDesk((s) => s.panelOrder);
  const windows = useOpenWindows();
  const launchers = useLaunchers();
  // HS-99-04 — the dock chip menu (one menu vocabulary).
  const [chipMenu, setChipMenu] = useState<{
    id: string;
    label: string;
    x: number;
    y: number;
    minimized: boolean;
    close: () => void;
  } | null>(null);
  useEffect(() => {
    if (!chipMenu) return;
    const close = () => setChipMenu(null);
    window.addEventListener("pointerdown", close);
    return () => window.removeEventListener("pointerdown", close);
  }, [chipMenu]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "`" || !e.ctrlKey) return;
      const ids = mruOrder(
        registrySnapshot.map((w) => w.id),
        useDesk.getState().panelOrder,
      );
      if (ids.length < 1) return;
      e.preventDefault();
      // The front window is last; cycling brings the least-recent forward.
      const next = ids[0];
      const s = useDesk.getState();
      if (s.panelMin.includes(next)) s.restorePanel(next);
      else s.focusPanel(next);
      // The cycle is visible (HS-97-06): the strip names the landing.
      flashSwitcher(next);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  if (!center && windows.length === 0 && launchers.length === 0) return null;
  // The front chip mirrors the shell's is-front rule: the last id in
  // the order that is open here and not minimized (HS-97-04).
  let front: string | undefined;
  for (let i = panelOrder.length - 1; i >= 0; i--) {
    const oid = panelOrder[i];
    if (panelMin.includes(oid)) continue;
    if (!windows.some((w) => w.id === oid)) continue;
    front = oid;
    break;
  }
  // A launcher whose surface is already a window folds into that chip;
  // it only renders as a launcher while its surface is closed.
  const shown = launchers.filter((l) => !windows.some((w) => w.id === l.id));
  return (
    <div
      className="desk-dock"
      role="toolbar"
      aria-label="Dock"
      onMouseMove={(e) => {
        // Materials round 2 — magnification: a distance falloff swells
        // chips near the pointer (macos-web curve, simplified; the CSS
        // transition supplies the spring feel). Skipped under reduced
        // motion.
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches)
          return;
        const buttons = e.currentTarget.querySelectorAll<HTMLElement>(
          ".desk-dock-main, .desk-dock-launch, .desk-dock-reset",
        );
        for (const el of buttons) {
          const r = el.getBoundingClientRect();
          const d = Math.abs(e.clientX - (r.x + r.width / 2));
          const t = Math.max(0, 1 - d / 170);
          const curve = t * t;
          el.style.transform = curve > 0.01
            ? `translateY(${(-5 * curve).toFixed(1)}px) scale(${(1 + 0.18 * curve).toFixed(3)})`
            : "";
        }
      }}
      onMouseLeave={(e) => {
        for (const el of e.currentTarget.querySelectorAll<HTMLElement>(
          ".desk-dock-main, .desk-dock-launch, .desk-dock-reset",
        ))
          el.style.transform = "";
      }}
    >
      {shown.map((l) => (
        <button
          key={l.id}
          type="button"
          className={"desk-dock-launch" + (l.open ? " is-run" : "")}
          onClick={() => l.activate()}
        >
          <span aria-hidden="true">{l.glyph}</span>
          <span className="desk-dock-label">{l.label}</span>
          {l.badge ? (
            <strong aria-label={`${l.badge} need attention`}>{l.badge}</strong>
          ) : null}
        </button>
      ))}
      {center}
      {shown.length > 0 && windows.length > 0 ? (
        <span className="desk-dock-sep" aria-hidden="true" />
      ) : null}
      {windows.map((c) => {
        const minimized = panelMin.includes(c.id);
        return (
          <span
            key={c.id}
            className={
              "desk-dock-chip" +
              (minimized ? " is-min" : "") +
              (c.id === front && !minimized ? " is-front" : "")
            }
          >
            <button
              type="button"
              className="desk-dock-main"
              ref={(el) => {
                if (el) chipEls.set(c.id, el);
                else chipEls.delete(c.id);
              }}
              aria-label={minimized ? `Restore ${c.label}` : `Focus ${c.label}`}
              onClick={() => {
                const s = useDesk.getState();
                if (minimized) s.restorePanel(c.id);
                else s.focusPanel(c.id);
              }}
              onContextMenu={(e) => {
                e.preventDefault();
                setChipMenu({
                  id: c.id,
                  label: c.label,
                  x: e.clientX,
                  y: e.clientY,
                  minimized,
                  close: c.close,
                });
              }}
            >
              <span aria-hidden="true">{c.glyph}</span>
              <span className="desk-dock-label">{c.label}</span>
            </button>
            <button
              type="button"
              className="desk-dock-x"
              aria-label={`Close ${c.label}`}
              onClick={c.close}
            >
              ✕
            </button>
          </span>
        );
      })}
      {windows.length > 0 ? (
        <>
          <button
            type="button"
            className="desk-dock-reset"
            aria-label="Overview"
            title="Overview"
            onClick={() => toggleExpose(true)}
          >
            ⊞
          </button>
          <button
            type="button"
            className="desk-dock-reset"
            aria-label="Reset layout"
            title="Reset layout"
            onClick={() => useDesk.getState().resetLayout()}
          >
            ⟲
          </button>
        </>
      ) : null}
      {chipMenu ? (
        <DeskMenuList
          className="desk-dock-menu"
          label={`${chipMenu.label} dock menu`}
          anchor="above"
          style={{
            left: Math.min(chipMenu.x, window.innerWidth - 184),
            top: Math.max(8, chipMenu.y - 104),
          }}
          onClose={() => setChipMenu(null)}
        >
          <DeskMenuItem
            onSelect={() => {
              const s = useDesk.getState();
              if (chipMenu.minimized) s.restorePanel(chipMenu.id);
              else s.minimizePanel(chipMenu.id);
              setChipMenu(null);
            }}
          >
            {chipMenu.minimized ? "Restore" : "Minimize"}
          </DeskMenuItem>
          <DeskMenuItem
            onSelect={() => {
              chipMenu.close();
              setChipMenu(null);
            }}
          >
            Close
          </DeskMenuItem>
        </DeskMenuList>
      ) : null}
    </div>
  );
}
